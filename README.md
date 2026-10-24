# 📜 Kannada Digitizer
Turn Kannada text in photos, scans, PDFs and handwriting into **editable, searchable digital text**,
then translate it, summarize it, listen to it, and ask questions about it.

Built for the Kannada Digital Innovation Hackathon 2026 (Problem 5: Kannada Text Digitization).

## Features
- Upload images / scanned PDFs / camera photos
- OpenCV cleanup: upscale, denoise, deskew, binarize
- Kannada OCR with Tesseract; automatic **vision-model fallback** for handwriting and low-confidence pages
- Side-by-side original vs. editable text, low-confidence words highlighted
- Document library with Kannada **full-text search**
- Export: TXT, DOCX, searchable PDF
- Understand: English translation, summary, read-aloud (Kannada), document Q&A

## Quick start
1. Install **Python 3.10+**, **Tesseract OCR**, and **Poppler** (for PDFs).
   - Windows: Tesseract (UB Mannheim installer) + Poppler (add its `bin` folder to PATH).
     If Tesseract isn't found, set its path in `ocr_pipeline.py` (line marked "On Windows").
   - Mac: `brew install tesseract poppler`
   - Linux: `sudo apt install tesseract-ocr poppler-utils`
2. In this folder:
   ```
   pip install -r requirements.txt
   streamlit run app.py
   ```
3. Open the link it prints (http://localhost:8501).

The Kannada model is already included in `tessdata/`, so no extra language install is needed.

### Optional: enable AI features (handwriting, summary, Q&A)
Set an Anthropic API key before running:
- Windows (PowerShell): `$env:ANTHROPIC_API_KEY="your-key"`
- Mac/Linux: `export ANTHROPIC_API_KEY="your-key"`

Without a key everything else still works (OCR, search, export, translation, read-aloud).

## Test it
```
python make_samples.py     # creates synthetic Kannada test images in samples/
python evaluate.py         # prints Character Error Rate table -> accuracy_report.md
```
Replace/add your own real scans in `samples/` with a matching `.txt` holding the correct text.

## Project layout
| File | Purpose |
|---|---|
| `app.py` | Streamlit web app (UI) |
| `ocr_pipeline.py` | Preprocessing + Tesseract + vision fallback |
| `storage.py` | SQLite + full-text search |
| `exports.py` | TXT / DOCX / searchable PDF |
| `ai_tools.py` | Translate / summarize / Q&A / text-to-speech |
| `evaluate.py` | Accuracy (CER) measurement |
| `Dockerfile` | Deployment |

## Known limitations (be honest in the submission)
- Tesseract is strong on clean printed Kannada, weaker on handwriting and very old scripts; handwriting relies on the vision model.
- Copy-paste from the searchable PDF's hidden text layer may not preserve Kannada conjunct order; the TXT/DOCX exports are the reliable text.
- Translation and read-aloud need an internet connection.

## Deploying free (Streamlit Community Cloud)
1. Put this folder in a **public GitHub repository** (never include your API key).
2. Go to share.streamlit.io, sign in with GitHub, click **Create app**, pick the repo,
   branch `main`, main file `app.py`.
3. Open **Advanced settings**: choose Python 3.12 and paste your key in **Secrets**:
   ```
   GEMINI_API_KEY = "your-key-here"
   ```
4. Deploy. `requirements.txt` installs the Python libraries and `packages.txt`
   installs Tesseract and Poppler.

Notes: free apps sleep when idle (open the link before a demo), saved library documents are
not permanent on free hosting, and Tesseract on the cloud may be an older version than on your PC.
