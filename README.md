# Kannada Digitizer

A simple web application for converting Kannada documents into digital text.

Kannada Digitizer helps users extract Kannada text from photos, scanned documents, and PDFs without having to type everything manually. Once the text is extracted, users can edit it, read an English translation, save documents for later, and download the results in different formats.

**Live Demo:** https://kannada-digitizer.streamlit.app/

## Why I built this

A lot of Kannada content exists in printed notices, old documents, books, and scanned pages. Working with this content digitally can be difficult when the text is only available as an image or scan.

I built Kannada Digitizer to make that process easier. The idea is to take a document, extract its text, and make the content easier to read, edit, search, and reuse.

This project was built for the Kannada Digital Innovation Hackathon 2026 under the *Kannada Text Digitization* problem statement.

## Features

- **Image and PDF input:** Upload images, scanned PDFs, or take a photo directly from your device.
- **Kannada text recognition:** Extract printed Kannada text using Tesseract OCR.
- **Image preprocessing:** Uses OpenCV to improve readability by adjusting images, reducing noise, straightening pages, and handling certain lighting issues.
- **Automatic reading:** The application starts processing a document as soon as it is uploaded.
- **English translation:** Read the extracted content in English, Kannada, or a side-by-side view.
- **Editable text:** Review and correct the extracted Kannada text before saving or exporting it.
- **AI-assisted reading:** Optional AI support for difficult pages, handwriting, text correction, summaries, key facts, and questions about a document.
- **Document library:** Save documents and search their Kannada and English text later.
- **Export options:** Download Kannada text, English text, Word documents, and searchable PDFs.
- **Text-to-speech:** Listen to the content in Kannada or English.
- **Sample document:** Try the application with a sample page if you do not have a document ready.

## How it works

1. Upload a photograph, image, or scanned PDF, or take a picture of a document.
2. The application preprocesses the image when enabled.
3. Tesseract OCR extracts the Kannada text. Optional AI-assisted recognition can help with difficult pages.
4. Review the extracted text and switch between Kannada, English, and side-by-side views.
5. Edit the text, save it to the library, search saved documents, or export it.

## Tech stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| Streamlit | Web interface |
| Tesseract OCR | Kannada text recognition |
| OpenCV | Image preprocessing |
| Pillow | Image handling |
| pdf2image and Poppler | PDF page conversion |
| SQLite | Local document storage and text search |
| python-docx | Word document generation |
| gTTS | Text-to-speech |
| deep-translator | Basic translation |
| Google Gemini / Anthropic Claude | Optional AI-assisted features |

## Run locally

### Prerequisites

- Python 3.10 or later
- Git
- Tesseract OCR
- Poppler for PDF processing

Install the required system dependencies first.

**Windows:** Install Tesseract using the [UB Mannheim installer](https://github.com/UB-Mannheim/tesseract/wiki) and install Poppler. Add their executable directories to your system `PATH` if necessary.

**Linux:**

```bash
sudo apt update
sudo apt install tesseract-ocr poppler-utils
```

**macOS:**

```bash
brew install tesseract poppler
```

### Installation

Clone the repository:

```bash
git clone https://github.com/luqq-md/Kannada-Digitizer.git
cd Kannada-Digitizer
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows:

```powershell
.venv\Scripts\activate
```

On Linux or macOS:

```bash
source .venv/bin/activate
```

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Start the application:

```bash
streamlit run app.py
```

Open the local URL shown in your terminal, usually `http://localhost:8501`.

## Optional AI features

The basic OCR workflow, document search, exports, and basic translation can work without an AI API key. AI-assisted features require a supported provider and a valid API key.

For Google Gemini, set:

```powershell
$env:GEMINI_API_KEY="your-api-key"
```

For Anthropic Claude, set:

```powershell
$env:ANTHROPIC_API_KEY="your-api-key"
```

These commands are for the current PowerShell session. For Streamlit Community Cloud, configure the appropriate key in the application's **Secrets** settings instead.

Never commit API keys or other credentials to the repository.

## Testing

The project includes automated tests and tools for checking OCR output.

Run the tests with:

```bash
pip install pytest
pytest
```

To generate sample Kannada images and evaluate text recognition:

```bash
python make_samples.py
python evaluate.py
```

The evaluation script reports Character Error Rate (CER), which helps measure how much the extracted text differs from the expected text. Lower CER indicates better recognition.

For a meaningful evaluation, use real Kannada documents with verified reference text in addition to generated samples.

## Limitations

- OCR results depend on image quality, lighting, font style, and document condition.
- Clean printed Kannada generally works better than handwriting or heavily damaged documents.
- AI-assisted handwriting recognition and text correction can make mistakes, so important content should be reviewed manually.
- Translation may not preserve every nuance of the original Kannada text.
- Translation and text-to-speech require an internet connection.
- The searchable PDF export may not preserve the order of all complex Kannada characters when its text layer is copied. The TXT and DOCX exports are preferable when you need to reuse the extracted text.

## Future improvements

Some areas I would like to improve are:

- Better recognition of handwritten and older Kannada documents.
- Improved OCR accuracy on low-quality scans and photographs.
- More thorough testing with real-world Kannada documents.
- Better handling of multi-page documents and complex layouts.
- More options for organizing and exporting digitized documents.

## License

No license has been specified yet. If you intend to make the project open source, add a suitable `LICENSE` file and update this section.

---

**Kannada Digitizer** — built to make Kannada documents easier to work with digitally.