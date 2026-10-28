"""'Understand it' features: translate, summarize, ask questions, read aloud.

Translation and read-aloud work WITHOUT any API key (free Google services).
Summary, Q&A and meaning-aware translation need an AI key (free Gemini or Claude).
"""
MODULE_VERSION = 7   # bumped on every release; app.py checks it to spot half-uploaded updates

import hashlib
import io
import json
import os
import re
import textwrap

import llm


def ai_available() -> bool:
    return llm.available()


def _claude(prompt: str, max_tokens=1200) -> str:     # name kept; works with any provider
    return llm.complete(prompt, max_tokens)


SMART_PROMPT = """You are translating Kannada text that was extracted from a photo by OCR.
The OCR can make mistakes: wrong or missing letters, broken words, stray symbols,
and lines split in the middle of a sentence.

1. Use the context to work out what the original Kannada most likely said, and fix
   the OCR mistakes.
2. Translate it into natural, fluent English that carries the real meaning. Be
   idiomatic (how a person would actually say it), not word-for-word.

Reply in EXACTLY this format and nothing else:
CORRECTED KANNADA:
<the corrected Kannada text>

ENGLISH:
<the natural English translation>"""


def _parse_smart(raw: str):
    i = raw.find("ENGLISH:")
    if i < 0:
        return "", raw.strip()
    kn = raw[:i].replace("CORRECTED KANNADA:", "").strip()
    return kn, raw[i + len("ENGLISH:"):].strip()


def smart_translate(text: str):
    """Meaning-aware translation (needs API key). Returns (corrected_kannada, english)."""
    return _parse_smart(_claude(SMART_PROMPT + "\n\nOCR TEXT:\n" + text, 2500))


def _translate_paragraphs(text, translate_fn, size):
    """OCR line breaks are just layout, not sentence ends: join the lines of each
    paragraph so the translator sees whole sentences, then translate."""
    out = []
    for para in text.split("\n\n"):
        flat = " ".join(para.split())
        if not flat:
            continue
        out.append(" ".join(translate_fn(p) for p in textwrap.wrap(flat, size)))
    return "\n\n".join(out)


def translate(text: str, target="en") -> str:
    """Kannada -> English. With an AI key: meaning-aware (fixes OCR mistakes).
    Without (or if the AI is unavailable): free word-by-word translation."""
    if ai_available():
        try:
            return smart_translate(text)[1]
        except Exception:
            pass
    return translate_free(text, target)


def translate_free(text: str, target="en") -> str:
    """Google Translate, then MyMemory (both free, no key). Cannot fix OCR mistakes."""
    errors = []
    try:
        from deep_translator import GoogleTranslator
        g = GoogleTranslator(source="kn", target=target)
        return _translate_paragraphs(text, g.translate, 4000)
    except Exception as e:
        errors.append(f"Google: {e}")
    try:
        from deep_translator import MyMemoryTranslator
        m = MyMemoryTranslator(source="kannada", target="english")
        return _translate_paragraphs(text, m.translate, 150)
    except Exception as e:
        errors.append(f"MyMemory: {e}")
    return "Translation failed. " + " | ".join(errors)


# ---------------------------------------------------------------- understand
# One AI call that gives a non-Kannada reader everything at once.
UNDERSTAND_PROMPT = """You are helping a reader who may not know Kannada. The Kannada text below was read
from a photo by OCR, so it can contain mistakes: wrong or missing letters, broken words, stray symbols.

Using the context, produce JSON with exactly these keys:
  "corrected": the Kannada lines with obvious OCR mistakes fixed. SAME number of lines, same order.
  "pairs":     for each corrected line, a short natural English rendering of that line's meaning.
               SAME number of items, same order. Read together they must flow like normal English.
  "english":   the whole text as fluent, natural English, the way a person would say it (paragraphs ok).

Reply with ONLY the JSON object, no explanations, no code fences. Both arrays must have exactly {n} items.

LINES:
{lines}"""

_CACHE: dict = {}


def _lines_of(text: str) -> list:
    return [l.strip() for l in text.splitlines() if l.strip()]


def _parse_understanding(raw: str, n: int):
    """Pull the JSON out of the AI reply and check it. Returns a dict or None."""
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
        corrected, pairs, english = d["corrected"], d["pairs"], d["english"]
    except Exception:
        return None
    if not (isinstance(corrected, list) and isinstance(pairs, list) and isinstance(english, str)):
        return None
    if len(corrected) != n or len(pairs) != n:
        return None
    return {"corrected": [str(x) for x in corrected], "pairs": [str(x) for x in pairs],
            "english": english.strip()}


def understand(text: str) -> dict:
    """Everything an English reader needs, from the Kannada text.

    Returns {"lines": [(kannada, english), ...], "english": str, "corrected": [str] | None,
             "source": "ai" | "free" | "none"}. Never raises; results are cached by text.
    """
    lines = _lines_of(text)
    empty = {"lines": [], "english": "", "corrected": None, "source": "none"}
    if not lines:
        return empty
    key = hashlib.sha1(text.encode("utf-8")).hexdigest()
    if key in _CACHE:
        return _CACHE[key]

    result = None
    if ai_available():
        prompt = UNDERSTAND_PROMPT.format(
            n=len(lines), lines="\n".join(f"{i}. {l}" for i, l in enumerate(lines, 1)))
        try:
            d = _parse_understanding(_claude(prompt, 4000), len(lines))
            if d:
                result = {"lines": list(zip(d["corrected"], d["pairs"])), "english": d["english"],
                          "corrected": d["corrected"], "source": "ai"}
        except Exception:
            result = None

    if result is None:                      # free, word-by-word fallback
        english = translate_free(text)
        if not translation_ok(english):
            return {**empty, "source": "none"}      # not cached: try again next time
        per_line = _free_per_line(lines)
        result = {"lines": list(zip(lines, per_line)), "english": english,
                  "corrected": None, "source": "free"}

    if len(_CACHE) > 64:
        _CACHE.clear()
    _CACHE[key] = result
    return result


def _free_per_line(lines: list) -> list:
    try:
        from deep_translator import GoogleTranslator
        out = GoogleTranslator(source="kn", target="en").translate_batch(lines)
        if out and len(out) == len(lines):
            return [o or "" for o in out]
    except Exception:
        pass
    return [""] * len(lines)


def translation_ok(t: str) -> bool:
    return bool(t) and not t.startswith("Translation failed")


def summarize(text: str) -> str:
    if not ai_available():
        return "Add a GEMINI_API_KEY (free) or ANTHROPIC_API_KEY to enable summaries."
    return _claude("Summarize this Kannada document in simple English in 4-6 bullet "
                   "points, then give the same summary in simple Kannada. "
                   "If it is a notice/letter, mention key dates, names and actions.\n\n"
                   + text)


def key_facts(text: str) -> str:
    if not ai_available():
        return "Add a GEMINI_API_KEY (free) or ANTHROPIC_API_KEY to enable key facts."
    return _claude(
        "Read this Kannada document (extracted by OCR, so it may contain small mistakes). "
        "List its key facts in English as short bullets, grouped under these headings and "
        "skipping any heading with nothing to report: Who / Dates and deadlines / Places / "
        "Amounts / What the reader must do. Write names in Kannada script followed by an "
        "English spelling in brackets. Do not invent anything that is not in the document.\n\n"
        + text)


def ask(text: str, question: str) -> str:
    if not ai_available():
        return "Add a GEMINI_API_KEY (free) or ANTHROPIC_API_KEY to enable document Q&A."
    return _claude("Answer the question using ONLY this document. If the answer is not "
                   "in it, say so. Answer in the same language as the question.\n\n"
                   f"DOCUMENT:\n{text}\n\nQUESTION: {question}")


def speak(text: str, lang="kn") -> bytes:
    """Return MP3 bytes of the text read aloud (needs internet)."""
    from gtts import gTTS
    buf = io.BytesIO()
    gTTS(text=text[:3000], lang=lang).write_to_fp(buf)
    return buf.getvalue()
