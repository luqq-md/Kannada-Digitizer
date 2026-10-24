"""One place that talks to the AI service, so the rest of the app doesn't care which.

  - GEMINI_API_KEY    -> Google Gemini (has a FREE tier: aistudio.google.com/apikey)
  - ANTHROPIC_API_KEY -> Anthropic Claude (paid, prepaid credits)

If both are set, Anthropic is used. If neither is set, AI features switch off and
the app still works (OCR, search, export, free translation, read-aloud).
"""
import base64
import io
import os
import time

ANTHROPIC_MODEL = os.getenv("TEXT_MODEL", "claude-sonnet-5-5")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")   # override: set GEMINI_MODEL


_SECRET_NAMES = ("GEMINI_API_KEY", "GOOGLE_API_KEY", "ANTHROPIC_API_KEY",
                 "GEMINI_MODEL", "TEXT_MODEL")


def _load_streamlit_secrets():
    """On Streamlit Community Cloud the key lives in the app's 'Secrets' box (st.secrets).
    Copy it into environment variables so the rest of the code works the same everywhere."""
    try:
        import streamlit as st
        for name in _SECRET_NAMES:
            if not os.getenv(name) and name in st.secrets:
                os.environ[name] = str(st.secrets[name])
    except Exception:          # no secrets configured (e.g. running locally) - fine
        pass


def _gemini_key():
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def provider():
    _load_streamlit_secrets()
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if _gemini_key():
        return "gemini"
    return None


def available() -> bool:
    return provider() is not None


def label() -> str:
    return {"anthropic": "Claude", "gemini": "Gemini (free tier)"}.get(provider(), "")


def _jpeg(img) -> bytes:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def _anthropic(prompt, max_tokens, image):
    import anthropic
    content = []
    if image is not None:
        content.append({"type": "image", "source": {
            "type": "base64", "media_type": "image/jpeg",
            "data": base64.standard_b64encode(_jpeg(image)).decode()}})
    content.append({"type": "text", "text": prompt})
    msg = anthropic.Anthropic().messages.create(
        model=os.getenv("TEXT_MODEL", ANTHROPIC_MODEL), max_tokens=max_tokens,
        messages=[{"role": "user", "content": content}])
    return "".join(b.text for b in msg.content if b.type == "text")


def _gemini(prompt, image):
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=_gemini_key())
    contents = []
    if image is not None:
        contents.append(types.Part.from_bytes(data=_jpeg(image), mime_type="image/jpeg"))
    contents.append(prompt)
    last = None
    for attempt in range(3):               # free tier is rate-limited: wait and retry
        try:
            return client.models.generate_content(model=os.getenv("GEMINI_MODEL", GEMINI_MODEL), contents=contents).text or ""
        except Exception as e:
            last = e
            if any(k in str(e) for k in ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE")):
                time.sleep(6 * (attempt + 1))
                continue
            raise
    raise last


def complete(prompt: str, max_tokens: int = 1200, image=None) -> str:
    """Send a prompt (and optionally a PIL image) to whichever AI service is set up."""
    p = provider()
    if p == "anthropic":
        return _anthropic(prompt, max_tokens, image)
    if p == "gemini":
        return _gemini(prompt, image)
    raise RuntimeError("No AI key set (GEMINI_API_KEY or ANTHROPIC_API_KEY).")
