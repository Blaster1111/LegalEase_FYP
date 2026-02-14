from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from auth import router as auth_router
from docs_router import router as docs_router
from qa_router import router as qa_router
from config import settings

# Summarization imports
from summarize.model import summarize_text
from summarize.pdf_utils import extract_text_from_pdf
from summarize.doc_utils import extract_text_from_docx
from summarize.text_utils import extract_text_from_txt

app = FastAPI(title="Legal RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      
    allow_credentials=True,
    allow_methods=["*"],      
    allow_headers=["*"],      
)

app.include_router(auth_router)
app.include_router(docs_router)
app.include_router(qa_router)


@app.get("/")
def root():
    return {"status": "ok", "service": "Legal RAG API"}


@app.post("/summarize")
async def summarize_file(file: UploadFile = File(...)):
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

    if not text:
        raise HTTPException(status_code=400, detail="No text found in file")

    # Summarize
    summary = summarize_text(text)

    return {
        "filename": file.filename,
        "summary": summary
    }
