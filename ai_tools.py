"""'Understand it' features: translate, summarize, ask questions, read aloud.

Translation and read-aloud work WITHOUT any API key (free Google services).
Summary, Q&A and meaning-aware translation need an AI key (free Gemini or Claude).
"""
import io
import os
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
    """Kannada -> English. With an API key: meaning-aware (fixes OCR mistakes).
    Without: Google, then MyMemory (free)."""
    errors = []
    if ai_available():
        try:
            return smart_translate(text)[1]
        except Exception as e:
            errors.append(f"Claude: {e}")
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


def translation_ok(t: str) -> bool:
    return bool(t) and not t.startswith("Translation failed")


def summarize(text: str) -> str:
    if not ai_available():
        return "Add a GEMINI_API_KEY (free) or ANTHROPIC_API_KEY to enable summaries."
    return _claude("Summarize this Kannada document in simple English in 4-6 bullet "
                   "points, then give the same summary in simple Kannada. "
                   "If it is a notice/letter, mention key dates, names and actions.\n\n"
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
