"""System check: tells you, in plain words, what works on THIS server and what does not.

Used by the 'System check' button on the About page, and by the start-up guard in app.py that
spots a half-uploaded update (new app.py with an old helper file).
"""
import importlib
import os
import re
import sys
import shutil
import subprocess
import time
import traceback
from pathlib import Path

MODULE_VERSION = 7

HERE = Path(__file__).parent


def disk_version(name: str):
    """(version written in the file ON DISK, size in bytes), or (None, None) if the file is not there.
    Reading the file itself tells apart 'not uploaded' from 'uploaded but the app has not restarted'."""
    path = HERE / f"{name}.py"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None, None
    m = re.search(r"^MODULE_VERSION\s*=\s*(\d+)", text, re.M)
    return (int(m.group(1)) if m else 0), path.stat().st_size


def stale_modules(required: dict) -> list:
    """[(file, version loaded in memory, needed), ...] for every helper file that is out of date or missing."""
    out = []
    for name, need in required.items():
        try:
            mod = importlib.import_module(name)
        except Exception:
            out.append((f"{name}.py", None, need))
            continue
        found = getattr(mod, "MODULE_VERSION", 0)
        if found != need:
            out.append((f"{name}.py", found, need))
    return out


def try_reload(required: dict) -> list:
    """Self-heal: a helper file whose copy on disk is right but whose copy in memory is old (the app
    was updated without a restart) is reloaded in place. Returns the names that were reloaded."""
    done = []
    for name, need in required.items():
        disk, _ = disk_version(name)
        mod = sys.modules.get(name)
        if mod is not None and disk == need and getattr(mod, "MODULE_VERSION", 0) != need:
            try:
                importlib.reload(mod)
                done.append(name)
            except Exception:
                pass
    return done


def explain(stale: list, required: dict) -> str:
    """Plain-language report for the screen that appears when files are out of date."""
    lines, on_disk_old = [], False
    for f, mem, need in stale:
        name = f[:-3]
        disk, size = disk_version(name)
        if disk is None:
            lines.append(f"- **{f}**: not found on the server at all")
            on_disk_old = True
        elif disk != need:
            lines.append(f"- **{f}**: the file on the server is the OLD one (version {disk}, "
                         f"{size // 1024} KB); this app needs version {need}")
            on_disk_old = True
        else:
            lines.append(f"- **{f}**: the new file is on the server, but the app is still running the "
                         f"old copy (version {mem}). Rebooting the app fixes this")
    try:
        entries = sorted(os.listdir(HERE))
    except OSError:
        entries = []
    shown = [e for e in entries if not e.startswith((".", "__"))]
    folders = [e for e in shown if (HERE / e).is_dir()]
    zips = [e for e in shown if e.lower().endswith(".zip")]
    hints = []
    if zips:
        hints.append(f"**A .zip file is in your repository ({', '.join(zips)}).** A zip must be "
                     "extracted first; GitHub cannot use the files inside it. Delete it and upload the "
                     "extracted files.")
    odd = [f for f in folders if f not in ("tessdata", "samples", "tests", ".streamlit")]
    if odd:
        hints.append(f"**There is an extra folder ({', '.join(odd)}).** Files placed inside a folder are not "
                     "used. The helper files must sit next to app.py, not in a subfolder.")
    fix = ("Upload the newest copy of each file listed above next to app.py (**Add file → Upload files**), "
           "choose **Commit changes**, then open Streamlit's **Manage app → ⋮ → Reboot app**."
           if on_disk_old else
           "Open Streamlit's **Manage app → ⋮ → Reboot app**, wait a minute, and refresh this page.")
    body = "\n".join(lines) + "\n\n**How to fix it:** " + fix
    if hints:
        body += "\n\n" + "\n\n".join(hints)
    body += f"\n\n*Files next to app.py on the server: {', '.join(shown) or 'none found'}*"
    return body


def _tesseract_version() -> str:
    import pytesseract
    return str(pytesseract.get_tesseract_version())


def _languages() -> list:
    env = dict(os.environ, TESSDATA_PREFIX=str(HERE / "tessdata"))
    res = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True, env=env, timeout=30)
    return [l.strip() for l in res.stdout.splitlines()[1:] if l.strip()]


def run_checks(required: dict, with_sample: bool = True) -> list:
    """Return [(check name, ok, detail), ...]. Never raises."""
    rows = []

    def add(name, fn):
        try:
            ok, detail = fn()
        except Exception as e:                              # report, never crash
            tail = " | ".join(traceback.format_exc().strip().splitlines()[-3:])
            ok, detail = False, f"{type(e).__name__}: {e}  [{tail[:300]}]"
        rows.append((name, bool(ok), detail))

    def files():
        st = stale_modules(required)
        return (not st, "all helper files are the newest version" if not st else
                "OUT OF DATE, upload these again:\n" + describe_stale(st))
    add("App files up to date", files)

    add("Tesseract installed", lambda: (True, "version " + _tesseract_version()))

    def kn():
        langs = _languages()
        size = (HERE / "tessdata" / "kan.traineddata").stat().st_size // 1024
        return ("kan" in langs, f"Kannada model found ({size} KB); languages: {', '.join(langs)}")
    add("Kannada reading model", kn)

    add("PDF support (Poppler)", lambda: (shutil.which("pdftoppm") is not None,
                                          shutil.which("pdftoppm") or "pdftoppm not found; PDFs will not open"))

    def sample():
        import ocr_pipeline as ocr
        p = HERE / "samples" / "notice_tilted.png"
        if not p.exists():
            return True, "no sample file uploaded, skipped"
        t0 = time.time()
        res = ocr.process_page(ocr.load_pages(p.read_bytes(), p.name)[0], True, False)
        kan = sum("\u0c80" <= c <= "\u0cff" for c in res.text)
        return (kan > 20, f"read {kan} Kannada letters, confidence {res.avg_conf:.0f}%, "
                          f"cleanup '{res.variant}', {time.time() - t0:.1f}s")
    if with_sample:
        add("Reading a sample page", sample)

    def db():
        import storage
        n = len(storage.list_documents())
        return True, f"library database works ({n} saved document{'s' if n != 1 else ''})"
    add("Library database", db)

    def ai():
        import llm
        return True, (f"{llm.label()} is set up" if llm.available() else
                      "no AI key set (basic mode: reading, search and export still work)")
    add("AI helper", ai)

    return rows


def test_ai() -> tuple:
    """One tiny real AI call (uses a little quota). Returns (ok, detail)."""
    import llm
    if not llm.available():
        return False, "no AI key is set"
    try:
        t0 = time.time()
        text = llm.complete("Reply with exactly one word: ready", 20)
        return True, f"answered in {time.time() - t0:.1f}s: {text.strip()[:40]}"
    except llm.AIError as e:
        return False, str(e)
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
