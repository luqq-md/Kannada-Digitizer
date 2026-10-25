"""One place that talks to the AI service, so the rest of the app doesn't care which.

  - GEMINI_API_KEY    -> Google Gemini (has a FREE tier: aistudio.google.com/apikey)
  - ANTHROPIC_API_KEY -> Anthropic Claude (paid, prepaid credits)

If both are set, Anthropic is used. If neither is set, AI features switch off and
the app still works (OCR, search, export, free translation, read-aloud).

Google retires Gemini model names often, so we never rely on one name: we ask the API
which models this key can use, try the best ones in order, and remember what worked.
"""
import base64
import io
import os
import re

ANTHROPIC_MODEL = os.getenv("TEXT_MODEL", "claude-sonnet-5-5")

# Aliases that Google keeps pointing at the newest model, then plain fallbacks.
GEMINI_ALIASES = ["gemini-flash-latest", "gemini-flash-lite-latest"]
GEMINI_STATIC = ["gemini-3.1-flash-lite", "gemini-2.5-flash-lite", "gemini-2.5-flash"]
_SKIP = ("image", "tts", "live", "audio", "embedding", "robotics", "native",
         "computer", "veo", "imagen", "lyria", "gemma", "pro")
MAX_MODEL_TRIES = 6

_state = {"models": None, "good": None}


class AIError(RuntimeError):
    """An AI call failed. str(e) is a short, plain-language explanation for the user."""


# ------------------------------------------------------------------ secrets
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


# ------------------------------------------------------------------- helpers
def _jpeg(img) -> bytes:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def _clean(msg: str) -> str:
    """Never show a key; keep messages short."""
    msg = str(msg)
    for k in (_gemini_key(), os.getenv("ANTHROPIC_API_KEY")):
        if k:
            msg = msg.replace(k, "***")
    return re.sub(r"\s+", " ", msg).strip()[:260]


def _code(e) -> int:
    c = getattr(e, "code", None)
    if isinstance(c, int):
        return c
    m = re.search(r"\b(4\d\d|5\d\d)\b", str(e))
    return int(m.group(1)) if m else 0


def _kind(e) -> str:
    """Classify a failure: 'key' (stop), 'next' (try another model), 'other'."""
    text = str(e).upper()
    code = _code(e)
    if "API_KEY_INVALID" in text or "API KEY NOT VALID" in text or code in (401, 403):
        return "key"
    if code in (404, 429, 500, 502, 503, 504) or any(
            k in text for k in ("NOT_FOUND", "RESOURCE_EXHAUSTED", "UNAVAILABLE", "OVERLOADED", "NO LONGER AVAILABLE")):
        return "next"
    return "other"


def _version(name: str) -> float:
    m = re.search(r"gemini-(\d+(?:\.\d+)?)", name)
    return float(m.group(1)) if m else 0.0


def _discover(client):
    """Ask the API which text models this key can use (cached)."""
    if _state["models"] is not None:
        return _state["models"]
    found = []
    try:
        for m in client.models.list():
            name = (getattr(m, "name", "") or "").replace("models/", "")
            actions = getattr(m, "supported_actions", None) or []
            if not name.startswith("gemini") or "flash" not in name:
                continue
            if any(t in name for t in _SKIP):
                continue
            if actions and "generateContent" not in actions:
                continue
            found.append(name)
    except Exception:
        pass
    # stable before preview, full flash before lite, newest first
    found.sort(key=lambda n: ("preview" in n or "exp" in n, "lite" in n, -_version(n)))
    _state["models"] = found
    return found


def _candidates(client):
    order = []
    for n in [os.getenv("GEMINI_MODEL"), _state["good"], *GEMINI_ALIASES,
              *_discover(client), *GEMINI_STATIC]:
        if n and n not in order:
            order.append(n)
    return order[:MAX_MODEL_TRIES]


# ----------------------------------------------------------------- providers
def _anthropic(prompt, max_tokens, image):
    import anthropic
    content = []
    if image is not None:
        content.append({"type": "image", "source": {
            "type": "base64", "media_type": "image/jpeg",
            "data": base64.standard_b64encode(_jpeg(image)).decode()}})
    content.append({"type": "text", "text": prompt})
    try:
        msg = anthropic.Anthropic().messages.create(
            model=os.getenv("TEXT_MODEL", ANTHROPIC_MODEL), max_tokens=max_tokens,
            messages=[{"role": "user", "content": content}])
    except Exception as e:
        raise AIError(f"The Claude service could not answer ({_clean(e)}). "
                      "Check your key and credit in the Anthropic Console.") from e
    return "".join(b.text for b in msg.content if b.type == "text")


def _gemini(prompt, image):
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=_gemini_key())
    contents = []
    if image is not None:
        contents.append(types.Part.from_bytes(data=_jpeg(image), mime_type="image/jpeg"))
    contents.append(prompt)

    tried, last = [], None
    for model in _candidates(client):
        try:
            text = client.models.generate_content(model=model, contents=contents).text or ""
            _state["good"] = model
            return text
        except Exception as e:
            last = e
            tried.append(model)
            if _state["good"] == model:
                _state["good"] = None
            kind = _kind(e)
            if kind == "key":
                raise AIError("Google rejected the API key. Create a new key at "
                              "aistudio.google.com/apikey and paste it into the app's "
                              "Secrets.") from e
            if kind == "other":
                raise AIError(f"The AI helper could not process this request "
                              f"({_clean(e)}).") from e
    quota = last is not None and _code(last) == 429
    why = ("The free AI quota is used up for the moment. Wait a minute and try again."
           if quota else "No Gemini model answered right now. Try again in a minute.")
    raise AIError(f"{why} (tried {', '.join(tried)}; last error: {_clean(last)})") from last


def complete(prompt: str, max_tokens: int = 1200, image=None) -> str:
    """Send a prompt (and optionally a PIL image) to whichever AI service is set up."""
    p = provider()
    if p == "anthropic":
        return _anthropic(prompt, max_tokens, image)
    if p == "gemini":
        return _gemini(prompt, image)
    raise AIError("No AI key is set. Add GEMINI_API_KEY (free) in the app's Secrets.")
