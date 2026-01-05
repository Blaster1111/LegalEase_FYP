# docs_router.py
import os
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException
from db import documents_col
from config import settings
from utils import extract_text_from_file, chunk_text, embed_chunks, build_faiss_index, save_index, save_chunks
from bson import ObjectId
import shutil
from auth import get_current_user

router = APIRouter(prefix="/documents", tags=["documents"])

def process_document_sync(document_id: str, file_path: str):
    # Extract text
    text = extract_text_from_file(file_path)
    # Chunk
    chunks = chunk_text(text)
    # embed
    embeddings = embed_chunks(chunks)
    # build index + save
    index = build_faiss_index(embeddings)
    save_index(index, document_id)
    save_chunks(document_id, chunks)
    # update mongo doc
    documents_col.update_one({"_id": ObjectId(document_id)}, {"$set": {"status": "processed", "chunks_count": len(chunks)}})

@router.post("/upload", response_model=dict)
def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...), user: dict = Depends(get_current_user)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".pdf", ".txt", ".docx"):
        raise HTTPException(status_code=400, detail="Unsupported file type")
    # save file
    doc = {"filename": file.filename, "user_id": user["id"], "status": "uploaded"}
    res = documents_col.insert_one(doc)
    doc_id = str(res.inserted_id)
    dest_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}{ext}")
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    # schedule background processing
    background_tasks.add_task(process_document_sync, doc_id, dest_path)
    # update doc with path
    documents_col.update_one({"_id": res.inserted_id}, {"$set": {"file_path": dest_path}})
    return {"document_id": doc_id, "filename": file.filename, "status": "processing"}
