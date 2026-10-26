"""System check: tells you, in plain words, what works on THIS server and what does not.

Used by the 'System check' button on the About page, and by the start-up guard in app.py that
spots a half-uploaded update (new app.py with an old helper file).
"""
import importlib
import os
import shutil
import subprocess
import time
import traceback
from pathlib import Path

MODULE_VERSION = 6

HERE = Path(__file__).parent


def stale_modules(required: dict) -> list:
    """[(file, found_version, needed_version), ...] for every helper file that is out of date or missing."""
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


def describe_stale(stale: list) -> str:
    lines = []
    for f, found, need in stale:
        lines.append(f"- {f}: " + ("missing" if found is None else
                                   f"the server has version {found}, this app needs version {need}"))
    return "\n".join(lines)


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
