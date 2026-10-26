"""Generate synthetic Kannada test images (clean, noisy, tilted) so you can test
the pipeline before collecting real scans. Ground-truth text goes in samples/*.txt"""
import random
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT = Path(__file__).parent / "fonts" / "NotoSansKannada.ttf"
OUT = Path(__file__).parent / "samples"
OUT.mkdir(exist_ok=True)

TEXTS = {
 "notice": "ಕರ್ನಾಟಕ ಸರ್ಕಾರದ ಸೂಚನೆ\nಎಲ್ಲಾ ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ತಿಳಿಸುವುದೇನೆಂದರೆ ಪರೀಕ್ಷೆಯು ನವೆಂಬರ್ ತಿಂಗಳಲ್ಲಿ ನಡೆಯಲಿದೆ.\nದಯವಿಟ್ಟು ಸಮಯಕ್ಕೆ ಸರಿಯಾಗಿ ಹಾಜರಾಗಿ.",
 "textbook": "ಕನ್ನಡ ನಾಡು ಸುಂದರವಾದ ಪ್ರಕೃತಿಯ ತವರೂರು.\nಇಲ್ಲಿ ಕಾವೇರಿ ನದಿ ಹರಿಯುತ್ತದೆ.\nಮೈಸೂರು ಅರಮನೆ ಬಹಳ ಪ್ರಸಿದ್ಧವಾಗಿದೆ.",
 "letter": "ಪ್ರೀತಿಯ ಅಮ್ಮನಿಗೆ ನಮಸ್ಕಾರ.\nನಾನು ಇಲ್ಲಿ ಚೆನ್ನಾಗಿದ್ದೇನೆ.\nನೀವು ಆರೋಗ್ಯವಾಗಿರಿ ಎಂದು ಆಶಿಸುತ್ತೇನೆ.",
}

def render(text, size=44):
    f = ImageFont.truetype(str(FONT), size)
    lines = text.split("\n")
    w, h = 1500, 140 * len(lines) + 120
    img = Image.new("RGB", (w, h), "white")
    d = ImageDraw.Draw(img)
    for i, l in enumerate(lines):
        d.text((60, 60 + i * 110), l, font=f, fill=(20, 20, 20), layout_engine=ImageFont.Layout.RAQM)
    return img

def degrade(img, angle=0, noise=0, blur=0):
    img = img.rotate(angle, expand=True, fillcolor="white", resample=Image.BICUBIC)
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(blur))
    a = np.array(img).astype(np.int16)
    if noise:
        a += np.random.normal(0, noise, a.shape).astype(np.int16)
    # uneven lighting
    grad = np.linspace(0, 40, a.shape[1])[None, :, None]
    a = a - grad.astype(np.int16)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

if __name__ == "__main__":
    random.seed(1); np.random.seed(1)
    for name, text in TEXTS.items():
        base = render(text)
        (OUT / f"{name}_clean.txt").write_text(text, encoding="utf-8")
        base.save(OUT / f"{name}_clean.png")
        for tag, kw in {"tilted": dict(angle=3, noise=8), "noisy": dict(angle=0, noise=25, blur=1.2)}.items():
            degrade(base, **kw).save(OUT / f"{name}_{tag}.png")
            (OUT / f"{name}_{tag}.txt").write_text(text, encoding="utf-8")
    print("samples created:", len(list(OUT.glob('*.png'))))
