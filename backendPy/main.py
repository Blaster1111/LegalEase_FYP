from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

from auth import router as auth_router
from docs_router import router as docs_router
from qa_router import router as qa_router
from config import settings

# Summarization imports
from summarize.model import summarize_text
from summarize.pdf_utils import extract_text_from_pdf
from summarize.doc_utils import extract_text_from_docx
from summarize.text_utils import extract_text_from_txt

# Simplification import (USLT)
from simplification.model import simplify_text

app = FastAPI(title="Legal RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(docs_router)
app.include_router(qa_router)


@app.get("/")
def root():
    return {"status": "ok", "service": "Legal RAG API"}


# ---------------------------
# SUMMARIZE ENDPOINT
# ---------------------------
@app.post("/summarize")
async def summarize_file(
    file: UploadFile = File(...),
    max_length: int = Form(150),
    min_length: int = Form(50)
):
    filename = file.filename.lower()

    # Read file
    file_bytes = await file.read()

    # Detect file type
    if filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes)

    elif filename.endswith(".docx"):
        text = extract_text_from_docx(file_bytes)

    elif filename.endswith(".txt"):
        text = extract_text_from_txt(file_bytes)

    else:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX, and TXT files are supported"
        )

    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="No text found in file")

    # Summarize with improved parameters
    summary = summarize_text(text, max_length=max_length, min_length=min_length)

    return {
        "filename": file.filename,
        "summary": summary
    }


# ---------------------------
# SIMPLIFY ENDPOINT (USLT)
# Accepts: file OR raw text
# ---------------------------
@app.post("/simplify")
async def simplify_endpoint(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None)
):
    # Case 1: raw text provided (from summary)
    if text:
        simplified = simplify_text(text)
        return {
            "simplified_text": simplified
        }

    # Case 2: file provided
    if file:
        filename = file.filename.lower()
        file_bytes = await file.read()

        if filename.endswith(".pdf"):
            text = extract_text_from_pdf(file_bytes)

        elif filename.endswith(".docx"):
            text = extract_text_from_docx(file_bytes)

        elif filename.endswith(".txt"):
            text = extract_text_from_txt(file_bytes)

        else:
            raise HTTPException(
                status_code=400,
                detail="Only PDF, DOCX, and TXT files are supported"
            )

        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="No text found in file")

        simplified = simplify_text(text)

        return {
            "filename": file.filename,
            "simplified_text": simplified
        }

    # Nothing provided
    raise HTTPException(status_code=400, detail="Provide file or text")