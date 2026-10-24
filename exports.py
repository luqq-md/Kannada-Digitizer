"""Export helpers: TXT, DOCX and searchable PDF."""
import io

import pytesseract
from docx import Document
from docx.oxml.ns import qn
from docx.shared import Pt
from PIL import Image

from ocr_pipeline import TESSDATA_DIR


def to_txt(text: str) -> bytes:
    return text.encode("utf-8")


def to_docx(title: str, text: str) -> bytes:
    doc = Document()
    doc.add_heading(title, level=1)
    for line in text.split("\n"):
        p = doc.add_paragraph()
        run = p.add_run(line)
        run.font.size = Pt(12)
        run.font.name = "Noto Sans Kannada"
        # make Word use the Kannada font for complex-script text too
        run._element.rPr.rFonts.set(qn("w:cs"), "Noto Sans Kannada")
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def to_searchable_pdf(images: list) -> bytes:
    """PDF that looks like the original scan but has an invisible text layer."""
    from pypdf import PdfWriter, PdfReader
    writer = PdfWriter()
    for img in images:
        pdf_bytes = pytesseract.image_to_pdf_or_hocr(
            img.convert("RGB"), lang="kan+eng", extension="pdf",
            config="--psm 6")
        for page in PdfReader(io.BytesIO(pdf_bytes)).pages:
            writer.add_page(page)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()
