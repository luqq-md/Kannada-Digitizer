"""SQLite storage + full-text search (Kannada text AND its English translation).

FTS5 'trigram' tokenizer: matches any 3+ character substring (good for Kannada,
case-insensitive for English). Shorter queries fall back to a plain LIKE search.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "documents.db"


def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def init_db():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS documents(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT, text TEXT, engine TEXT, avg_conf REAL, pages INTEGER,
            created TEXT DEFAULT CURRENT_TIMESTAMP, translation TEXT DEFAULT '')""")
        cols = [r["name"] for r in c.execute("PRAGMA table_info(documents)")]
        migrated = False
        if "translation" not in cols:            # upgrade an older database
            c.execute("ALTER TABLE documents ADD COLUMN translation TEXT DEFAULT ''")
            migrated = True
        fts_cols = [r["name"] for r in c.execute("PRAGMA table_info(docs_fts)")]
        if migrated or (fts_cols and "translation" not in fts_cols):
            c.execute("DROP TABLE IF EXISTS docs_fts")
            migrated = True
        c.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts
            USING fts5(title, text, translation, content='documents',
                       content_rowid='id', tokenize='trigram')""")
        if migrated:
            c.execute("INSERT INTO docs_fts(docs_fts) VALUES('rebuild')")


def _fts_add(c, i, title, text, tr):
    c.execute("INSERT INTO docs_fts(rowid,title,text,translation) VALUES(?,?,?,?)",
              (i, title, text, tr or ""))


def _fts_remove(c, row):
    c.execute("INSERT INTO docs_fts(docs_fts,rowid,title,text,translation) "
              "VALUES('delete',?,?,?,?)",
              (row["id"], row["title"], row["text"], row["translation"] or ""))


def add_document(title, text, engine, avg_conf, pages, translation="") -> int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO documents(title,text,engine,avg_conf,pages,translation) "
            "VALUES(?,?,?,?,?,?)", (title, text, engine, avg_conf, pages, translation or ""))
        _fts_add(c, cur.lastrowid, title, text, translation)
        return cur.lastrowid


def update_document(doc_id, text=None, translation=None):
    with _conn() as c:
        old = c.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
        if not old:
            return
        new_text = old["text"] if text is None else text
        new_tr = (old["translation"] or "") if translation is None else translation
        _fts_remove(c, old)
        c.execute("UPDATE documents SET text=?, translation=? WHERE id=?",
                  (new_text, new_tr, doc_id))
        _fts_add(c, doc_id, old["title"], new_text, new_tr)


def update_text(doc_id, text):
    update_document(doc_id, text=text)


def delete_document(doc_id):
    with _conn() as c:
        old = c.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
        if old:
            _fts_remove(c, old)
            c.execute("DELETE FROM documents WHERE id=?", (doc_id,))


def list_documents():
    with _conn() as c:
        return c.execute("SELECT id,title,engine,avg_conf,pages,created "
                         "FROM documents ORDER BY id DESC").fetchall()


def get_document(doc_id):
    with _conn() as c:
        return c.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()


def _snippet(text: str, q: str, width=60):
    """Return a snippet around the match, or None if q isn't in text."""
    i = (text or "").lower().find(q.lower())
    if i < 0:
        return None
    a, b = max(0, i - width), min(len(text), i + len(q) + width)
    return ("…" if a else "") + text[a:b].replace("\n", " ") + ("…" if b < len(text) else "")


def search(query: str):
    q = query.strip()
    if not q:
        return []
    with _conn() as c:
        if len(q) >= 3:
            safe = '"' + q.replace('"', '""') + '"'
            rows = c.execute(
                "SELECT d.id,d.title,d.text,d.translation FROM docs_fts f "
                "JOIN documents d ON d.id=f.rowid WHERE docs_fts MATCH ? ORDER BY rank",
                (safe,)).fetchall()
        else:
            like = f"%{q}%"
            rows = c.execute("SELECT id,title,text,translation FROM documents "
                             "WHERE text LIKE ? OR translation LIKE ? OR title LIKE ?",
                             (like, like, like)).fetchall()
    hits = []
    for r in rows:
        snip = _snippet(r["text"], q)
        lang = "Kannada"
        if snip is None:
            snip = _snippet(r["translation"] or "", q)
            lang = "English translation"
        if snip is None:
            snip, lang = (r["text"] or "")[:120], "title"
        hits.append({"id": r["id"], "title": r["title"], "snippet": snip, "matched": lang})
    return hits
