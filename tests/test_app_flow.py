"""End-to-end checks that drive the real Streamlit app. No internet or key needed."""
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
pytest.importorskip("streamlit.testing.v1")
from streamlit.testing.v1 import AppTest   # noqa: E402

import ai_tools   # noqa: E402

pytestmark = pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract not installed")


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(ai_tools, "translate_free", lambda t, target="en": "FREE english")
    monkeypatch.setattr(ai_tools, "_free_per_line", lambda lines: ["x"] * len(lines))
    ai_tools._CACHE.clear()


def new_app():
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=180).run()


def read_sample(at):
    """One tap on the sample: it is read straight away, with no Convert button."""
    [b for b in at.button if b.key == "s_sample"][0].click(); at.run()


def in_workspace(at):
    return any(b.label == "Save" for b in at.button)


def test_sample_page_reaches_the_workspace():
    at = new_app(); read_sample(at)
    assert not at.exception and in_workspace(at)
    assert any("FREE english" in m.value for m in at.markdown)       # English shown without a click


def test_a_translation_crash_never_blocks_reading(monkeypatch):
    def boom(text): raise AttributeError("no attribute 'understand'")   # e.g. a stale file on the server
    monkeypatch.setattr(ai_tools, "understand", boom)
    at = new_app(); read_sample(at)
    assert not at.exception and in_workspace(at)


def test_camera_is_an_equal_choice():
    at = new_app()
    assert at.session_state["source"] == "Upload a file"
    at.session_state["source"] = "Take a photo"; at.run()
    assert not at.exception and len(at.get("camera_input")) == 1


def test_menu_pages_open_without_errors():
    at = new_app()
    for page in ("My Library", "About"):
        at.sidebar.radio[0].set_value(page).run()
        assert not at.exception and at.session_state["page"] == page


def test_new_page_returns_to_the_start():
    at = new_app(); read_sample(at)
    [b for b in at.button if b.label == "New page"][0].click(); at.run()
    assert not at.exception and any(b.key == "s_sample" for b in at.button)


def test_library_page_offers_backup_and_restore():
    at = new_app()
    at.sidebar.radio[0].set_value("My Library").run()
    assert not at.exception
    assert any("Back up" in e.label for e in at.expander)


def test_there_is_no_convert_button_to_press():
    at = new_app()
    assert not any("Convert" in b.label for b in at.button)
    assert sum(1 for b in at.button if b.key and b.key.startswith("s_")) == 1      # exactly one sample


def test_a_failed_read_explains_itself_and_offers_a_retry(monkeypatch):
    import ocr_pipeline
    def boom(*a, **k): raise RuntimeError("tesseract exploded")
    monkeypatch.setattr(ocr_pipeline, "read_document", boom)
    at = new_app(); read_sample(at)
    assert not at.exception and not in_workspace(at)
    assert any("could not be read" in e.value for e in at.error)       # message stays on screen
    assert any("RuntimeError" in c.value for c in at.code)                 # technical details shown
    assert any(b.label == "Try reading again" for b in at.button)


def test_half_uploaded_update_is_named_not_mysterious(monkeypatch):
    import ocr_pipeline
    monkeypatch.setattr(ocr_pipeline, "MODULE_VERSION", 1)                  # pretend the server has an old file
    at = new_app()
    assert not at.exception and any("out of date" in e.value for e in at.error)
    assert any("ocr_pipeline.py" in m.value for m in at.markdown)
    assert not any(b.key == "s_sample" for b in at.button)                  # the app stopped safely


def test_system_check_reports_real_results():
    at = new_app()
    at.sidebar.radio[0].set_value("About").run()
    [b for b in at.button if b.label == "Run system check"][0].click(); at.run()
    assert not at.exception
    text = " ".join(m.value for m in at.markdown)
    assert "App files up to date" in text and "Kannada reading model" in text and "✅" in text
