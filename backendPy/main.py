from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from contextlib import asynccontextmanager

from auth import router as auth_router
from docs_router import router as docs_router
from qa_router import router as qa_router
from config import settings

# Summarization
from summarize.model import summarize_text, load_summarizer
from summarize.pdf_utils import extract_text_from_pdf
from summarize.doc_utils import extract_text_from_docx
from summarize.text_utils import extract_text_from_txt

# Simplification
from simplification.model import simplify_text


# ---------------------------
# LOAD MODEL ON STARTUP
# ---------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading Legal Pegasus once on startup...")
    
    tokenizer, model = load_summarizer()

    app.state.tokenizer = tokenizer
    app.state.summarizer_model = model

    yield

    print("Shutting down Legal Pegasus...")


app = FastAPI(title="Legal RAG API", lifespan=lifespan)


# ---------------------------
# CORS
# ---------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------
# ROUTERS
# ---------------------------
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

    # Debug preview
    print("\n========== EXTRACTED TEXT PREVIEW ==========")
    print(text[:1000])
    print("===========================================\n")

    # Use loaded model from app.state
    summary = summarize_text(
        text,
        app.state.tokenizer,
        app.state.summarizer_model
    )

    print("\n========== SUMMARY ==========")
    print(summary)
    print("===========================================\n")

    return {
        "filename": file.filename,
        "summary": summary
    }


# ---------------------------
# SIMPLIFY ENDPOINT
# ---------------------------
@app.post("/simplify")
async def simplify_endpoint(
    file: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None)
):
    # Case 1: raw text provided
    if text:
        simplified = simplify_text(text)
        return {"simplified_text": simplified}

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

    raise HTTPException(status_code=400, detail="Provide file or text")