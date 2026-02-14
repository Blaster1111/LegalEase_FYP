from docx import Document
import io

def extract_text_from_docx(file_bytes: bytes) -> str:
    doc = Document(io.BytesIO(file_bytes))
    text = ""

    for para in doc.paragraphs:
        text += para.text + "\n"

    return text.strip()
