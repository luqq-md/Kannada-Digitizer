"""Core OCR pipeline for Kannada Text Digitization.

Flow:  load image/PDF  ->  preprocess (OpenCV)  ->  Tesseract (kan)
       -> if confidence is low and an API key exists -> vision model fallback
       -> clean up text + mark uncertain words
"""
import base64
import io
import os
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np
import pytesseract
from PIL import Image

# Use the Kannada model that ships inside this project folder
TESSDATA_DIR = str(Path(__file__).parent / "tessdata")
os.environ["TESSDATA_PREFIX"] = TESSDATA_DIR

# On Windows, uncomment and fix this path if Tesseract is not found:
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

LOW_CONF_WORD = 60      # words below this confidence get highlighted
FALLBACK_BELOW = 70     # page average below this -> try the vision model


@dataclass
class PageResult:
    text: str
    avg_conf: float
    engine: str                      # "tesseract" or "vision"
    words: list = field(default_factory=list)   # [(word, conf), ...]
    preprocessed: "Image.Image | None" = None
    score: float = 0.0
    variant: str = "standard"
    boxes: list = field(default_factory=list)   # [(word, conf, left, top, w, h)]


# ---------------------------------------------------------------- loading
def load_pages(data: bytes, filename: str) -> list:
    """Return a list of PIL images (one per page)."""
    if filename.lower().endswith(".pdf"):
        from pdf2image import convert_from_bytes
        return convert_from_bytes(data, dpi=250)
    return [Image.open(io.BytesIO(data)).convert("RGB")]


# ---------------------------------------------------------- preprocessing
EARLY_STOP_CONF = 92    # a clean page needs only one attempt


def _gray(img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2GRAY)


def _upscale(arr: np.ndarray, target: int = 1800, max_side: int = 2600) -> np.ndarray:
    """Kannada letters are detailed: make small images bigger, and shrink huge
    phone photos (faster, and keeps the text at a size Tesseract likes)."""
    h, w = arr.shape
    if max(h, w) < target:
        scale = target / max(h, w)
        arr = cv2.resize(arr, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    elif max(h, w) > max_side:
        scale = max_side / max(h, w)
        arr = cv2.resize(arr, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return arr


def _rotate(arr: np.ndarray, angle: float, fill: int = 255) -> np.ndarray:
    """Rotate by `angle` degrees, enlarging the canvas so nothing is cut off."""
    if abs(angle) < 0.3:
        return arr
    h, w = arr.shape
    m = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
    cos, sin = abs(m[0, 0]), abs(m[0, 1])
    nw, nh = int(h * sin + w * cos), int(h * cos + w * sin)
    m[0, 2] += nw / 2 - w / 2
    m[1, 2] += nh / 2 - h / 2
    return cv2.warpAffine(arr, m, (nw, nh), flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=fill)


def _small(mask: np.ndarray, side: int) -> np.ndarray:
    h, w = mask.shape
    s = side / max(h, w)
    return cv2.resize(mask, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)


def _skew_blob(text_mask: np.ndarray) -> float:
    """Tilt of the text lines: join letters into line-shaped blobs, take the
    area-weighted median blob angle. text_mask: text = 255."""
    m = _small(text_mask, 1800)
    blobs = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_RECT, (35, 5)))
    cnts, _ = cv2.findContours(blobs, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    angs = []
    for c in cnts:
        if cv2.contourArea(c) < 800:
            continue
        (_, _), (w, h), a = cv2.minAreaRect(c)
        if w < h:
            a += 90
        while a > 45:
            a -= 90
        while a < -45:
            a += 90
        angs.append((a, w * h))
    if not angs:
        return 0.0
    arr = np.array(angs)
    order = np.argsort(arr[:, 0])
    cs = np.cumsum(arr[order, 1])
    return float(arr[order][np.searchsorted(cs, cs[-1] / 2), 0])


def _skew_projection(text_mask: np.ndarray, limit: int = 25) -> float:
    """Pick the rotation where text lines are sharpest in a horizontal projection."""
    m = _small(text_mask, 600)

    def sharp(a):
        p = _rotate(m, a, 0).sum(axis=1).astype(float)
        return float(np.sum(np.diff(p) ** 2))

    best_a = max(np.arange(-limit, limit + 1, 1.0), key=sharp)
    return float(max(np.arange(best_a - 1, best_a + 1.01, 0.25), key=sharp))


def _standard(gray: np.ndarray) -> Image.Image:
    """Good for clean, dark-on-light pages: denoise, light deskew, Otsu."""
    arr = _upscale(gray)
    arr = cv2.fastNlMeansDenoising(arr, None, h=12, templateWindowSize=7, searchWindowSize=21)
    inv = cv2.bitwise_not(arr)
    mask = cv2.threshold(inv, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    ang = _skew_blob(mask)
    if 0.3 < abs(ang) < 15:
        arr = _rotate(arr, ang, 255)
    arr = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    return Image.fromarray(arr)


def _adaptive(gray: np.ndarray, invert: bool, skew_fn) -> Image.Image:
    """Good for photos: local thresholding copes with glare/shadows; `invert`
    handles light text on a dark background (phone screens, signboards)."""
    arr = _upscale(gray)
    arr = cv2.fastNlMeansDenoising(arr, None, h=10)
    if invert:
        arr = cv2.bitwise_not(arr)
    b = cv2.adaptiveThreshold(arr, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                              cv2.THRESH_BINARY, 51, 15)
    ang = skew_fn(cv2.bitwise_not(b))
    b = _rotate(b, ang, 255)
    b = cv2.copyMakeBorder(b, 30, 30, 30, 30, cv2.BORDER_CONSTANT, value=255)
    return Image.fromarray(b)


def candidate_images(img: Image.Image):
    """Yield (name, image) versions to try, most likely best first."""
    gray = _gray(img)
    dark = float(np.median(gray)) < 120          # dark background -> light text
    std = ("standard", lambda: _standard(gray))
    if dark:
        order = [("inverted-lines", lambda: _adaptive(gray, True, _skew_blob)),
                 ("inverted-projection", lambda: _adaptive(gray, True, _skew_projection)),
                 std]
    else:
        order = [std,
                 ("photo-lines", lambda: _adaptive(gray, False, _skew_blob)),
                 ("photo-projection", lambda: _adaptive(gray, False, _skew_projection))]
    order.append(("original", lambda: img.convert("RGB")))
    for name, make in order:
        yield name, make()


def preprocess(img: Image.Image, enabled: bool = True) -> Image.Image:
    """Single best-guess cleanup (kept for simple use)."""
    if not enabled:
        return img
    return next(candidate_images(img))[1]


# ------------------------------------------------------------- tesseract
def _is_kan(ch: str) -> bool:
    return "\u0c80" <= ch <= "\u0cff"


def _letters(w: str) -> int:
    return sum(_is_kan(ch) or ch.isalpha() for ch in w)


def _noise_token(w: str, c: float) -> bool:
    """Stray marks like '[', '1-', '|', '—'. Real numbers (all digits) are kept."""
    return _letters(w) == 0 and not (w.isdigit() and c >= 60)


def _good_line(items) -> bool:
    """A line we trust: it has a solidly-read word, or is long and fairly confident."""
    if any(c >= 75 and _letters(w) >= 3 for w, c, *_ in items):
        return True
    mean = float(np.mean([c for _, c, *_ in items]))
    return mean >= 60 and sum(_letters(w) for w, *_ in items) >= 8


def _filter_lines(lines):
    """Remove junk (glare, edges of other objects, stray marks) from a photo's lines.
    Only when the page has clear good lines; a weak page (e.g. rough handwriting)
    keeps everything except pure garbage, so real content is never thrown away."""
    cleaned = []
    for l in lines:
        l = [it for it in l if not _noise_token(it[0], it[1])]
        if l:
            cleaned.append(l)
    good = [l for l in cleaned if _good_line(l)]
    if len(good) >= 2:
        return good
    return [l for l in cleaned
            if not (sum(_letters(w) for w, c, *_ in l if c >= 50) < 3
                    and np.mean([c for _, c, *_ in l]) < 40)]


def run_tesseract(img: Image.Image, lang: str = "kan+eng") -> PageResult:
    data = pytesseract.image_to_data(img, lang=lang, config="--psm 6",
                                     output_type=pytesseract.Output.DICT)
    lines, cur, cur_key = [], [], None
    for i, word in enumerate(data["text"]):
        word = word.strip()
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        if cur_key is not None and key != cur_key and cur:
            lines.append(cur)
            cur = []
        cur_key = key
        if word and float(data["conf"][i]) >= 0:
            cur.append((word, float(data["conf"][i]), data["left"][i], data["top"][i],
                        data["width"][i], data["height"][i]))
    if cur:
        lines.append(cur)

    lines = _filter_lines(lines)                              # drop junk
    boxes = [it for l in lines for it in l]
    words = [(w, c) for w, c, *_ in boxes]
    confs = [c for _, c in words]
    avg = float(np.mean(confs)) if confs else 0.0
    # Unsupervised quality score = confidently-read letters (Kannada first; any
    # letters if the page has no Kannada). Used to pick the best image version.
    kan = sum(sum(_is_kan(ch) for ch in w) * c / 100 for w, c in words if c >= 50)
    score = kan or sum(sum(ch.isalpha() for ch in w) * c / 100 for w, c in words if c >= 50)
    text = clean_text("\n".join(" ".join(w for w, *_ in l) for l in lines))
    return PageResult(text, avg, "tesseract", words, score=score, boxes=boxes)


def locate_text_crop(img: Image.Image, boxes, min_conf: float = 60, pad: float = 0.10):
    """Crop to the area holding the confidently-read Kannada words, so clutter around
    the text (walls, hands, phone frame...) is thrown away. Returns None if not sure."""
    pts = [(l, t, l + w, t + h) for wd, c, l, t, w, h in boxes
           if c >= min_conf and any(_is_kan(ch) for ch in wd)]
    if len(pts) < 3:
        return None
    a = np.array(pts, float)
    cx, cy = (a[:, 0] + a[:, 2]) / 2, (a[:, 1] + a[:, 3]) / 2
    mx, my = np.median(cx), np.median(cy)          # ignore stray far-away words
    sx = max(np.median(np.abs(cx - mx)) * 4 + 50, img.width * 0.35)
    sy = max(np.median(np.abs(cy - my)) * 4 + 50, img.height * 0.35)
    a = a[(np.abs(cx - mx) <= sx) & (np.abs(cy - my) <= sy)]
    if len(a) < 3:
        return None
    x0, y0, x1, y1 = a[:, 0].min(), a[:, 1].min(), a[:, 2].max(), a[:, 3].max()
    px, py = (x1 - x0) * pad + 20, (y1 - y0) * pad + 20
    box = (int(max(0, x0 - px)), int(max(0, y0 - py)),
           int(min(img.width, x1 + px)), int(min(img.height, y1 + py)))
    if (box[2] - box[0]) * (box[3] - box[1]) > 0.92 * img.width * img.height:
        return None                                 # nothing to crop away
    return img.crop(box)


# ---------------------------------------------------------------- vision
def vision_available() -> bool:
    import llm
    return llm.available()


def run_vision(img: Image.Image) -> PageResult:
    """Fallback for handwriting / messy scans using an AI vision model."""
    import llm
    text = llm.complete(
        "Transcribe ALL the text in this image exactly as written, "
        "keeping the original language (mostly Kannada) and line breaks. "
        "Do not translate, summarize or add comments. "
        "Output only the transcription.", 4000, image=img)
    return PageResult(clean_text(text), 100.0, "vision", [])


# ------------------------------------------------------------ post-process
def clean_text(text: str) -> str:
    """Normalize Unicode (important for Kannada) and tidy whitespace."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u200b", "").replace("\ufeff", "")
    lines = [" ".join(l.split()) for l in text.splitlines()]
    return "\n".join(l for l in lines if l).strip()


# --------------------------------------------------------------- main API
CROP_BELOW = 88   # pages already read this well don't need the crop-and-reread pass


def process_page(img: Image.Image, use_preprocess: bool = True,
                 allow_vision: bool = True, force_vision: bool = False) -> PageResult:
    if force_vision and vision_available():
        res = run_vision(img)
        res.preprocessed = preprocess(img, use_preprocess)
        return res

    if not use_preprocess:
        res = run_tesseract(img)
        res.preprocessed, res.variant = img, "original"
    else:
        # Pass 1: try several cleaned-up versions of the whole image
        tried = []
        for name, cand in candidate_images(img):
            r = run_tesseract(cand)
            r.preprocessed, r.variant = cand, name
            tried.append(r)
            if r.avg_conf >= EARLY_STOP_CONF:        # clean page: no need to try more
                break
        res = max(tried, key=lambda r: r.score)

        # Pass 2 (hard photos): crop to where the text is, throw the rest away, re-read
        if res.avg_conf < CROP_BELOW:
            for r in sorted(tried, key=lambda r: r.score, reverse=True)[:3]:
                crop = locate_text_crop(r.preprocessed, r.boxes)
                if crop is None:
                    continue
                r2 = run_tesseract(crop)
                r2.preprocessed, r2.variant = crop, r.variant + "+crop"
                if r2.score > res.score:
                    res = r2

    if allow_vision and vision_available() and res.avg_conf < FALLBACK_BELOW:
        try:
            v = run_vision(img)
            if v.text:
                v.preprocessed, v.variant = res.preprocessed, "vision"
                return v
        except Exception as e:           # keep Tesseract result if API fails
            print("Vision fallback failed:", e)
    return res


def highlight_html(words: list) -> str:
    """HTML where low-confidence words are highlighted."""
    out = []
    for w, c in words:
        w = w.replace("&", "&amp;").replace("<", "&lt;")
        if c < LOW_CONF_WORD:
            out.append(f'<mark title="confidence {c:.0f}%">{w}</mark>')
        else:
            out.append(w)
    return " ".join(out)
