"""ಕನ್ನಡ ಡಿಜಿಟೈಸರ್ - Kannada Digitizer (Streamlit app).

Run:  streamlit run app.py

Two states:  start (pick a page)  ->  workspace (read it, in English and Kannada).
"""
import logging
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Kannada Digitizer · ಕನ್ನಡ ಡಿಜಿಟೈಸರ್", page_icon="📜", layout="wide")

# ---- start-up guard: a half-uploaded update (new app.py + old helper file) is named, not mysterious
APP_VERSION = 7
REQUIRED = {"ocr_pipeline": APP_VERSION, "ai_tools": APP_VERSION, "llm": APP_VERSION,
            "storage": APP_VERSION, "exports": APP_VERSION, "theme": APP_VERSION}
try:
    import diagnostics
    _diag_ok = getattr(diagnostics, "MODULE_VERSION", 0) == APP_VERSION
except ImportError:
    diagnostics, _diag_ok = None, False

if not _diag_ok:
    st.error("Some files on the server are out of date, so the app cannot start safely.")
    st.markdown("**diagnostics.py** is missing or old. Upload the newest copy of **all** the files from "
                "the latest zip (after extracting it) next to app.py, commit, then open Streamlit's "
                "**Manage app → ⋮ → Reboot app**.")
    st.stop()

_stale = diagnostics.stale_modules(REQUIRED)
if _stale:
    diagnostics.try_reload(REQUIRED)              # self-heal when only the in-memory copy is old
    _stale = diagnostics.stale_modules(REQUIRED)
if _stale:
    st.error("Some files on the server are out of date, so the app cannot start safely.")
    st.markdown(diagnostics.explain(_stale, REQUIRED))
    st.stop()

import ai_tools   # noqa: E402
import exports    # noqa: E402
import llm        # noqa: E402
import ocr_pipeline as ocr   # noqa: E402
import storage    # noqa: E402
import theme      # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
log = logging.getLogger("kannada.app")

storage.init_db()
theme.inject()

# ------------------------------------------------------------------ navigation
PAGES = ["Photo to Text", "My Library", "About"]
PAGE_HINTS = ["Turn a page into text", "Your saved pages", "Why and how it works"]
ss = st.session_state
if "page" not in ss:
    ss.page = "Photo to Text"
ss.setdefault("nav_side", ss.page)
ss.setdefault("nav_top", ss.page)


def _go(src):
    """Keep the sidebar menu and the phone menu in step."""
    if ss.get(src):                       # a segmented control can be un-selected: ignore that
        ss.page = ss[src]
    ss.nav_side = ss.page
    ss.nav_top = ss.page


theme.sidebar_brand()
st.sidebar.radio("Go to", PAGES, key="nav_side", on_change=_go, args=("nav_side",),
                 captions=PAGE_HINTS, label_visibility="collapsed")
st.sidebar.divider()
theme.sidebar_status(llm.label() if llm.available() else None)
if hasattr(st, "segmented_control"):
    with st.container(key="mobilenav"):          # shown only on narrow screens (see theme.py)
        st.segmented_control("Menu", PAGES, key="nav_top", on_change=_go, args=("nav_top",),
                             label_visibility="collapsed")
page = ss.page

SAMPLE_DIR = Path(__file__).parent / "samples"
SOURCES = ["Upload a file", "Take a photo"]
SAMPLE_FILE = "notice_tilted.png"
VIEWS = ["English", "Side by side", "Kannada"]
NEEDS_KEY = "Add a free GEMINI_API_KEY in the app's Secrets to turn this on."
WORK_KEYS = ("images", "results", "title", "text", "und", "und_text", "summary", "facts",
             "answer", "audio", "pdf", "saved_id")


def run_ai(fn, *args, spinner="Thinking…"):
    """Run an AI call; show a plain-language message instead of a crash if it fails."""
    try:
        with st.spinner(spinner):
            return fn(*args)
    except llm.AIError as e:
        st.error(str(e))
    except Exception as e:                      # never show a raw traceback to visitors
        st.error(f"Something went wrong ({type(e).__name__}). Please try again.")
    return None


def safe_understand(text: str) -> dict:
    """Translation must never stop a page from being read: any failure becomes 'no English'."""
    try:
        return ai_tools.understand(text)
    except Exception:
        return {"lines": [], "english": "", "corrected": None, "source": "none"}


def is_phone() -> bool:
    try:
        ua = st.context.headers.get("User-Agent", "")
    except Exception:
        return False
    return any(k in ua for k in ("Mobi", "Android", "iPhone", "iPad"))


def rear_camera_hint():
    """Ask the phone to open its BACK camera (sharp, full resolution) from the file picker."""
    components.html("""<script>
      const fix=()=>{try{window.parent.document.querySelectorAll('input[type=file]').forEach(i=>{
        i.setAttribute('capture','environment');i.setAttribute('accept','image/*');});}catch(e){}};
      fix();let n=0;const t=setInterval(()=>{fix();if(++n>25)clearInterval(t);},300);
    </script>""", height=0)


def understanding():
    """The English/line-by-line result for the current text, or None if there is none."""
    u = ss.get("und")
    return u if u and u.get("source") != "none" else None


def translation_is_stale() -> bool:
    return bool(understanding()) and ss.get("und_text") != ss.get("text")


def refresh_understanding():
    with st.spinner("Translating so it reads in English…"):
        ss.und = safe_understand(ss.text)
        ss.und_text = ss.text


def best_text() -> str:
    """The AI-corrected Kannada if we have it (fewer reading mistakes), else what was read."""
    u = understanding()
    return "\n".join(u["corrected"]) if u and u.get("corrected") else ss.text


def reset_work():
    for k in WORK_KEYS:
        ss.pop(k, None)
    ss.nonce = ss.get("nonce", 0) + 1          # fresh, empty upload and camera widgets


# ================================================================== START
def start_page():
    """Scan-and-go: the moment a file arrives or a photo is taken, it is read. No button to press."""
    theme.hero()

    if "source" not in ss:
        ss.source = SOURCES[1] if is_phone() else SOURCES[0]       # phones start with the camera
    seg = getattr(st, "segmented_control", None)
    if seg:
        source = seg("How do you want to add it?", SOURCES, key="source", label_visibility="collapsed")
    else:
        source = st.radio("How do you want to add it?", SOURCES, key="source", horizontal=True,
                          label_visibility="collapsed")
    source = source or ss.get("last_source") or SOURCES[0]
    ss.last_source = source
    n = ss.get("nonce", 0)

    files, photo = [], None
    if source == SOURCES[0]:
        files = st.file_uploader("Drop a photo, scan or PDF here, or browse",
                                 type=["png", "jpg", "jpeg", "webp", "pdf"],
                                 accept_multiple_files=True, key=f"up{n}")
        st.caption("It starts reading the moment your file arrives. Nothing else to press.")
    elif is_phone():
        with st.container(key="camwrap"):
            photo = st.file_uploader("Tap to open your camera and photograph the page",
                                     type=["png", "jpg", "jpeg", "webp"], key=f"cam{n}")
        rear_camera_hint()
        st.caption("Uses your phone's own camera. Fill the frame with the page and hold steady. "
                   "It reads the moment you take the photo.")
    else:
        photo = st.camera_input("Point the camera at the page and press Take photo", key=f"webcam{n}")

    # ---- one sample, one tap
    sample_path = SAMPLE_DIR / SAMPLE_FILE
    sample_go = False
    if sample_path.exists() and not files and photo is None:
        with st.container(key="samplecard"):
            c1, c2 = st.columns([1, 2], vertical_alignment="center", gap="large")
            c1.image(str(sample_path), width="stretch")
            with c2:
                st.markdown("**No page handy?**")
                st.caption("Try a sample notice and watch it turn into English in a few seconds.")
                sample_go = st.button("Try the sample page", key="s_sample", type="primary")

    ai_on = ocr.vision_available()
    with st.expander("Reading options"):
        c1, c2, c3 = st.columns(3)
        use_pre = c1.checkbox("Clean the image first", True,
                              help="Straightens the page, flips light-on-dark text, removes glare.")
        allow_v = c2.checkbox("Let the AI reader help on hard pages", True, disabled=not ai_on,
                              help="" if ai_on else NEEDS_KEY)
        force_v = c3.checkbox("Handwriting mode (AI reader always)", False, disabled=not ai_on,
                              help="" if ai_on else NEEDS_KEY)

    # ---- when to start: a new file, a new photo, the sample, or 'try again' after a failure
    file_ids = (tuple(getattr(f, "file_id", None) or (f.name, f.size) for f in files)
                if files else None)
    photo_id = None
    if photo is not None:
        photo_id = getattr(photo, "file_id", None) or (photo.name, photo.size)
    fresh_files = bool(files) and ss.get("done_files") != file_ids
    fresh_photo = photo is not None and ss.get("done_photo") != photo_id
    retry = False
    if ss.get("read_error"):
        msg, tech, can_retry = ss.read_error
        st.error(msg)
        if tech:
            with st.expander("Technical details (send these if it keeps happening)"):
                st.code(tech, language=None)
                st.caption("Tip: About, then System check, tests this server and shows what is wrong.")
        if can_retry:
            retry = st.button("Try reading again", type="primary")
    if not (fresh_files or fresh_photo or sample_go or retry):
        return
    ss.pop("read_error", None)
    if fresh_files:
        ss.done_files = file_ids
    if fresh_photo:
        ss.done_photo = photo_id

    # ---- read the page(s)
    sources = [(f.getvalue(), f.name, f.name) for f in (files or [])]
    if photo is not None:
        sources.append((photo.getvalue(), photo.name or "camera.jpg", "camera photo"))
    if not sources and sample_go:
        sources.append((sample_path.read_bytes(), sample_path.name, sample_path.name))

    images, results, names = [], [], []
    with st.status("Reading your page…", expanded=True) as status:
        try:
            for data, fname, label in sources:
                im, rs, hit = ocr.read_document(data, fname, use_pre, allow_v, force_v,
                                                on_step=st.write)
                if hit:
                    st.write("Read this page before, so it is ready instantly")
                images += im
                results += rs
                names.append(label)
        except ocr.UnreadableFile as e:
            ss.read_error = (str(e), None, False)
        except Exception as e:
            log.exception("reading failed")
            ss.read_error = ("This page could not be read. Try a clearer, well-lit photo with the "
                             "page filling the frame, or try again.",
                             f"{type(e).__name__}: {str(e)[:400]}", True)
        text = "\n\n".join(r.text for r in results) if results else ""
        letters = sum(ch.isalpha() or "\u0c80" <= ch <= "\u0cff" for ch in text)
        if not ss.get("read_error") and letters < 4:         # nothing readable: say so, do not show an empty page
            ss.read_error = ("No text was found in this photo. Hold the page flat, fill the frame with it, "
                             "use good light, and take the photo again.", None, False)
        if not ss.get("read_error"):
            st.write("Translating so it reads in English")
            und = safe_understand(text)
            status.update(label="Ready", state="complete", expanded=False)
        else:
            status.update(label="Could not read this page", state="error")
    if ss.get("read_error"):
        st.rerun()                      # redraw the start page with the message and the retry button

    reset_work()
    ss.images, ss.results = images, results
    ss.title = exports.safe_filename(names[0].rsplit(".", 1)[0]) if names else "document"
    ss.text, ss.und, ss.und_text = text, und, text
    ss.saved_id = None
    ss.flash = "Page read. You can read it in English, side by side, or in Kannada."
    st.rerun()


# ============================================================== WORKSPACE
def save_to_library(engines, avg, pages):
    u = understanding()
    tr = u["english"] if u else ""
    if not tr:
        tr = ai_tools.translate(ss.text)
        tr = tr if ai_tools.translation_ok(tr) else ""
    if ss.get("saved_id"):
        storage.update_document(ss.saved_id, text=ss.text, translation=tr)
    else:
        ss.saved_id = storage.add_document(ss.title, ss.text, engines, avg, pages, tr)
    st.toast("Saved to your library." if tr else
             "Saved. No English was available, so search works in Kannada only.", icon="📚")


def workspace_page():
    results, images = ss.results, ss.images
    avg = sum(r.avg_conf for r in results) / len(results)
    engines = ", ".join(sorted({r.engine for r in results}))
    flash = ss.pop("flash", None)
    if flash:
        st.toast(flash, icon="✅")

    # ---- one compact bar: status, name, save, download, new page
    with st.container(key="topbar"):
        b1, b2, b3, b4, b5 = st.columns([4.4, 2.6, 1.1, 1.5, 1.3], vertical_alignment="center")
    with b1:
        theme.result_bar(avg, len(images), engines, results[0].variant)
    ss.title = b2.text_input("Document name", ss.title, label_visibility="collapsed",
                             placeholder="Document name")
    if b3.button("Save", type="primary", width="stretch"):
        save_to_library(engines, avg, len(images))
    with b4.popover("Download", width="stretch"):
        u = understanding()
        st.download_button("Word document (.docx)",
                           exports.to_docx(ss.title, ss.text, u["english"] if u else "",
                                           u["lines"] if u else None),
                           f"{exports.safe_filename(ss.title)}.docx", width="stretch")
        st.download_button("Kannada text (.txt)", exports.to_txt(ss.text), f"{exports.safe_filename(ss.title)}-kannada.txt",
                           width="stretch")
        if u:
            st.download_button("English text (.txt)", exports.to_txt(u["english"]),
                               f"{exports.safe_filename(ss.title)}-english.txt", width="stretch")
        if st.button("Prepare searchable PDF", width="stretch"):
            with st.spinner("Building the PDF…"):
                ss.pdf = exports.to_searchable_pdf(images)
        if ss.get("pdf"):
            st.download_button("Searchable PDF", ss.pdf, f"{exports.safe_filename(ss.title)}.pdf", width="stretch")
    if b5.button("New page", width="stretch"):
        reset_work()
        st.rerun()

    # ---- photo (left) and text (right)
    left, right = st.columns([5, 7], gap="large")
    idx = 0
    with left:
        theme.plate_title("Your page")
        if len(images) > 1:
            idx = st.number_input("Page", 1, len(images), 1) - 1
        st.image(images[idx], width="stretch")
        with st.expander("What the reader saw"):
            st.caption(f"Cleanup chosen automatically: {results[idx].variant}")
            st.image(results[idx].preprocessed, width="stretch")

    with right:
        seg = getattr(st, "segmented_control", None)
        if seg:
            view = seg("View", VIEWS, default="English", key="view", label_visibility="collapsed")
        else:
            view = st.radio("View", VIEWS, horizontal=True, key="view", label_visibility="collapsed")
        view = view or "English"
        u = understanding()

        if view in ("English", "Side by side"):
            if not u:
                st.info("English isn't available right now (the translation service did not answer).")
                if st.button("Try translating again"):
                    refresh_understanding()
                    st.rerun()
            else:
                if translation_is_stale():
                    st.warning("You edited the Kannada after this translation was made.")
                    if st.button("Update the English"):
                        refresh_understanding()
                        st.rerun()
                if view == "English":
                    note = ("Meaning-aware translation by the AI helper, with reading mistakes fixed."
                            if u["source"] == "ai" else
                            "Free word-by-word translation. A free Gemini key makes it read naturally.")
                    theme.english_plate(u["english"], note)
                    with st.expander("Copy the English text"):
                        st.code(u["english"], language=None, wrap_lines=True)
                else:
                    theme.pairs_view(u["lines"])
        else:
            t_edit, t_doubt = st.tabs(["Edit", "Doubtful words"])
            with t_edit:
                ss.text = st.text_area("Kannada text", ss.text, height=380,
                                       label_visibility="collapsed")
                if u and u.get("corrected") and "\n".join(u["corrected"]) != "\n".join(
                        l.strip() for l in ss.text.splitlines() if l.strip()):
                    if st.button("Use the AI-corrected Kannada"):
                        ss.text = "\n".join(u["corrected"])
                        ss.und_text = ss.text
                        st.rerun()
            with t_doubt:
                if results[idx].words:
                    st.caption("Words the reader was unsure about are marked in yellow.")
                    theme.kannada_plate(ocr.highlight_html(results[idx].words))
                else:
                    st.info("No word-by-word confidence is available for this page.")

    # ---- tools
    theme.plate_title("Do more with it")
    t_sum, t_facts, t_ask, t_listen = st.tabs(["Summary", "Key facts", "Ask a question", "Listen"])
    with t_sum:
        if not llm.available():
            st.info(NEEDS_KEY)
        elif st.button("Summarize this page"):
            res = run_ai(ai_tools.summarize, best_text(), spinner="Summarizing…")
            if res:
                ss.summary = res
        if ss.get("summary"):
            st.write(ss.summary)
    with t_facts:
        if not llm.available():
            st.info(NEEDS_KEY)
        elif st.button("Find dates, names and actions"):
            res = run_ai(ai_tools.key_facts, best_text(), spinner="Reading carefully…")
            if res:
                ss.facts = res
        if ss.get("facts"):
            st.write(ss.facts)
    with t_ask:
        if not llm.available():
            st.info(NEEDS_KEY)
        else:
            q = st.text_input("Ask about this page, in English or Kannada",
                              placeholder="For example: What is the last date mentioned?")
            if st.button("Ask") and q:
                res = run_ai(ai_tools.ask, best_text(), q, spinner="Looking through the page…")
                if res:
                    ss.answer = res
            if ss.get("answer"):
                st.write(ss.answer)
    with t_listen:
        c1, c2 = st.columns(2)
        want = None
        if c1.button("Hear it in Kannada", width="stretch"):
            want = ("kn", ss.text)
        if understanding() and c2.button("Hear it in English", width="stretch"):
            want = ("en", understanding()["english"])
        if want:
            try:
                with st.spinner("Preparing the audio…"):
                    ss.audio = ai_tools.speak(want[1], want[0])
            except Exception:
                st.error("Audio could not be created. It needs an internet connection; try again.")
        if ss.get("audio"):
            st.audio(ss.audio, format="audio/mp3")


def digitize_page():
    if "results" in ss:
        workspace_page()
    else:
        start_page()


# ================================================================ LIBRARY
def library_page():
    theme.page_head("Library", "Everything you saved. Search in Kannada or English.")
    q = st.text_input("Search your documents", placeholder="Try ಪರೀಕ್ಷೆ or exam")
    if q:
        hits = storage.search(q)
        st.caption(f"{len(hits)} result{'s' if len(hits) != 1 else ''}")
        for h in hits:
            with st.container(border=True):
                st.markdown(f"**{h['title']}**  matched in {h['matched']}")
                st.write(h["snippet"])
    with st.expander("Back up or restore your library"):
        st.caption("Free hosting forgets saved pages when the app restarts. "
                   "Download a backup now and then, and restore it here any time.")
        st.download_button("Download backup", storage.export_json(), "kannada-library-backup.json",
                           mime="application/json")
        up = st.file_uploader("Restore from a backup file", type=["json"], key="restore")
        if up is not None and st.button("Restore these documents"):
            try:
                added, skipped = storage.import_json(up.getvalue())
                st.toast(f"Restored {added} document(s); {skipped} already there.", icon="📚")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
    docs = storage.list_documents()
    if not docs:
        st.info("Nothing saved yet. Convert a page and press Save. "
                "It will appear here, searchable in Kannada and English.")
    for d in docs:
        with st.expander(f"{d['title']}: {d['pages']} page(s), {d['avg_conf']:.0f}% confidence, "
                         f"{d['created'][:10]}"):
            full = storage.get_document(d["id"])
            if full["translation"]:
                st.markdown("**English**")
                st.write(full["translation"])
            st.markdown("**Kannada**")
            st.text_area("Text", full["text"], height=200, key=f"t{d['id']}",
                         label_visibility="collapsed")
            c1, c2 = st.columns(2)
            if c1.button("Save edits", key=f"s{d['id']}"):
                storage.update_document(d["id"], text=ss[f"t{d['id']}"])
                st.toast("Changes saved.", icon="✅")
            if c2.button("Delete", key=f"x{d['id']}"):
                storage.delete_document(d["id"])
                st.rerun()


# ================================================================== ABOUT
def about_page():
    theme.page_head("About this project", "Why it exists, how it works, and how well it works.")
    theme.about_legend([
        ("The problem", "Karnataka's knowledge sits on paper: notices, textbooks, newspapers and "
                        "handwritten records. It cannot be searched, copied, translated or read aloud."),
        ("What this does", "It turns photos, scans and PDFs into editable, searchable Kannada text, "
                           "and puts the English meaning right beside it for anyone who does not read Kannada."),
        ("Who it helps", "Students, elders who struggle with small print, people learning Kannada, "
                         "newcomers to Karnataka, researchers, and offices digitizing records."),
    ])
    theme.plate_title("How it works")
    st.graphviz_chart("""
digraph G {
  rankdir=LR; bgcolor="transparent"; nodesep=0.35; ranksep=0.45;
  node [shape=box, style="rounded,filled", fillcolor="#EFE7B8", fontname="Helvetica", fontsize=15, color="#BDB27A", margin="0.18,0.12"];
  edge [color="#2B3A33", fontname="Helvetica", fontsize=12];
  A [label="Photo, scan\\nor PDF"];
  B [label="Clean-up\\nflip colours,\\nstraighten,\\nremove glare"];
  C [label="Tesseract\\nKannada reader"];
  D [label="Find the text,\\ncrop and\\nread again"];
  E [label="AI reader\\nfor handwriting", fillcolor="#13201B", fontcolor="white", color="#13201B"];
  F [label="Kannada\\ntext"];
  H [label="English\\nmeaning"];
  G [label="Search, export,\\nsummary, key facts,\\nlisten, ask", fillcolor="#E8A317", color="#B97F00"];
  A -> B -> C -> D -> F -> H -> G;
  C -> E [style=dashed, label=" low\\n confidence"];
  E -> F [style=dashed];
}
""")
    theme.plate_title("Measured accuracy")
    st.caption("Character error rate on 15 test images. Lower is better.")
    theme.accuracy_bars([
        ("All 15 images, average", [("Plain Tesseract", 37.3, False), ("This pipeline", 0.3, True)]),
        ("The 6 hardest, phone-style photos (white text on dark, tilted, glare)",
         [("Plain Tesseract", 70.2, False), ("This pipeline", 0.3, True)]),
    ])
    theme.plate_title("System check")
    st.caption("If something does not work, press this. It tests this server and shows the real reason.")
    if st.button("Run system check"):
        with st.spinner("Checking…"):
            ss.syscheck = diagnostics.run_checks(REQUIRED)
    for name, ok, detail in ss.get("syscheck", []):
        st.markdown(f"{'✅' if ok else '❌'} **{name}**: {detail}")
    if llm.available() and st.button("Test the AI helper (uses a little quota)"):
        ok, detail = diagnostics.test_ai()
        st.markdown(f"{'✅' if ok else '❌'} **AI helper**: {detail}")
    st.markdown(
        "**Read this honestly.** The test images are synthetic: computer-made Kannada, then degraded "
        "to look like phone photos. Real photos are harder. On two real, low-resolution phone-screen "
        "photos the pipeline recovered about 79% of the words, with small spelling slips. "
        "Handwriting depends on the AI reader.")


{"Photo to Text": digitize_page, "My Library": library_page, "About": about_page}[page]()
