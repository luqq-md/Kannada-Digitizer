"""Accuracy test. For every samples/NAME.(png|jpg) with a samples/NAME.txt holding the
correct text, compute Character Error Rate (CER, lower = better) for:
  A) plain Tesseract on the raw image
  B) our pipeline (cleanup + Tesseract)
Run:  python evaluate.py        -> prints a table and writes accuracy_report.md
"""
from pathlib import Path
from PIL import Image
import ocr_pipeline as ocr

SAMPLES = Path(__file__).parent / "samples"

def cer(ref: str, hyp: str) -> float:
    ref, hyp = "".join(ref.split()), "".join(hyp.split())
    if not ref:
        return 0.0
    prev = list(range(len(hyp) + 1))
    for i, rc in enumerate(ref, 1):
        cur = [i]
        for j, hc in enumerate(hyp, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (rc != hc)))
        prev = cur
    return min(1.0, prev[-1] / len(ref))   # cap at 100%

def main():
    rows = []
    for img_path in sorted(list(SAMPLES.glob("*.png")) + list(SAMPLES.glob("*.jpg"))):
        gt_path = img_path.with_suffix(".txt")
        if not gt_path.exists():
            continue
        truth = ocr.clean_text(gt_path.read_text(encoding="utf-8"))
        img = Image.open(img_path).convert("RGB")
        a = ocr.run_tesseract(img)                              # raw
        b = ocr.process_page(img, True, allow_vision=False)     # pipeline
        rows.append((img_path.stem, cer(truth, a.text), cer(truth, b.text), b.avg_conf))
    lines = ["| Sample | Raw Tesseract CER | Our pipeline CER | Confidence |",
             "|---|---|---|---|"]
    for n, ca, cb, conf in rows:
        lines.append(f"| {n} | {ca*100:.1f}% | {cb*100:.1f}% | {conf:.0f}% |")
    if rows:
        ma = sum(r[1] for r in rows) / len(rows) * 100
        mb = sum(r[2] for r in rows) / len(rows) * 100
        lines.append(f"| **Average** | **{ma:.1f}%** | **{mb:.1f}%** | |")
    report = "\n".join(lines)
    print(report)
    Path("accuracy_report.md").write_text(report, encoding="utf-8")

if __name__ == "__main__":
    main()
