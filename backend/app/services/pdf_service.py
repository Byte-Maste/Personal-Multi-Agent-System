import io
from typing import Optional
from dataclasses import dataclass

import pypdf
import pdfplumber
from PIL import Image


@dataclass
class OcrTextBlock:
    text: str
    x0: float
    y0: float
    x1: float
    y1: float


def decrypt_pdf(file_bytes: bytes, password: str) -> bytes:
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    if reader.is_encrypted:
        reader.decrypt(password)
    writer = pypdf.PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return buf.getvalue()


def extract_text_pypdf(file_bytes: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    text_parts = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def extract_text_pdfplumber(file_bytes: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def extract_tables_pdfplumber(file_bytes: bytes) -> list[list[list[str]]]:
    all_tables = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            all_tables.extend(tables)
    return all_tables


def sort_text_blocks_spatially(blocks: list[OcrTextBlock]) -> list[OcrTextBlock]:
    return sorted(blocks, key=lambda b: (round(b.y0, 1), b.x0))


def blocks_to_text(blocks: list[OcrTextBlock]) -> str:
    sorted_blocks = sort_text_blocks_spatially(blocks)
    lines = []
    current_y = None
    line_texts = []
    for b in sorted_blocks:
        y_rounded = round(b.y0, 1)
        if current_y is None:
            current_y = y_rounded
        if abs(y_rounded - current_y) > 5.0:
            lines.append(" ".join(line_texts))
            line_texts = []
            current_y = y_rounded
        line_texts.append(b.text)
    if line_texts:
        lines.append(" ".join(line_texts))
    return "\n".join(lines)


def extract_text_ocr(file_bytes: bytes) -> str:
    try:
        import pytesseract
        from PIL import Image
        import pdf2image
        images = pdf2image.convert_from_bytes(file_bytes)
        blocks = []
        for img in images:
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            n_boxes = len(data["text"])
            for i in range(n_boxes):
                text = data["text"][i].strip()
                if not text:
                    continue
                blocks.append(OcrTextBlock(
                    text=text,
                    x0=data["left"][i],
                    y0=data["top"][i],
                    x1=data["left"][i] + data["width"][i],
                    y1=data["top"][i] + data["height"][i],
                ))
        return blocks_to_text(blocks)
    except ImportError:
        pass
    try:
        import easyocr
        import pdf2image
        reader = easyocr.Reader(["en"])
        images = pdf2image.convert_from_bytes(file_bytes)
        blocks = []
        for img in images:
            results = reader.readtext(img)
            for bbox, text, _ in results:
                (x0, y0), (x1, y1) = bbox[0], bbox[2]
                blocks.append(OcrTextBlock(
                    text=text.strip(),
                    x0=x0, y0=y0, x1=x1, y1=y1,
                ))
        return blocks_to_text(blocks)
    except ImportError:
        return ""


def extract_text(file_bytes: bytes, password: Optional[str] = None) -> str:
    if password:
        try:
            file_bytes = decrypt_pdf(file_bytes, password)
        except Exception:
            raise ValueError("Invalid PDF password")
    text = extract_text_pdfplumber(file_bytes)
    if text and len(text.strip()) > 50:
        return text
    text = extract_text_pypdf(file_bytes)
    if text and len(text.strip()) > 50:
        return text
    ocr_text = extract_text_ocr(file_bytes)
    return ocr_text
