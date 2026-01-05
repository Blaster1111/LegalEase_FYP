# # docs_router.py
# import os
# from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException
# from db import documents_col
# from config import settings
# from utils import extract_text_from_file, chunk_text, embed_chunks, build_faiss_index, save_index, save_chunks
# from bson import ObjectId
# import shutil
# from auth import get_current_user

# router = APIRouter(prefix="/documents", tags=["documents"])

# def process_document_sync(document_id: str, file_path: str):
#     # Extract text
#     text = extract_text_from_file(file_path)
#     # Chunk
#     chunks = chunk_text(text)
#     # embed
#     embeddings = embed_chunks(chunks)
#     # build index + save
#     index = build_faiss_index(embeddings)
#     save_index(index, document_id)
#     save_chunks(document_id, chunks)
#     # update mongo doc
#     documents_col.update_one({"_id": ObjectId(document_id)}, {"$set": {"status": "processed", "chunks_count": len(chunks)}})

# @router.post("/upload", response_model=dict)
# def upload_document(background_tasks: BackgroundTasks, file: UploadFile = File(...), user: dict = Depends(get_current_user)):
#     ext = os.path.splitext(file.filename)[1].lower()
#     if ext not in (".pdf", ".txt", ".docx"):
#         raise HTTPException(status_code=400, detail="Unsupported file type")
#     # save file
#     doc = {"filename": file.filename, "user_id": user["id"], "status": "uploaded"}
#     res = documents_col.insert_one(doc)
#     doc_id = str(res.inserted_id)
#     dest_path = os.path.join(settings.UPLOAD_DIR, f"{doc_id}{ext}")
#     with open(dest_path, "wb") as f:
#         shutil.copyfileobj(file.file, f)
#     # schedule background processing
#     background_tasks.add_task(process_document_sync, doc_id, dest_path)
#     # update doc with path
#     documents_col.update_one({"_id": res.inserted_id}, {"$set": {"file_path": dest_path}})
#     return {"document_id": doc_id, "filename": file.filename, "status": "processing"}


# docs_router.py
import os
import shutil
from datetime import datetime
from bson.errors import InvalidId
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, Depends, HTTPException
from bson import ObjectId

from db import documents_col
from config import settings
from auth import get_current_user
from utils import (
    extract_text_from_file,
    chunk_text,
    embed_chunks,
    build_faiss_index,
    save_index,
    save_chunks,
)

router = APIRouter(prefix="/documents", tags=["documents"])


# -----------------------------
# Background processing logic
# -----------------------------
def process_document(document_id: str, file_path: str):
    try:
        # mark as PROCESSING
        documents_col.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {"status": "PROCESSING", "updated_at": datetime.utcnow()}}
        )

        # 1. extract text
        text = extract_text_from_file(file_path)

        # 2. chunk
        chunks = chunk_text(text)

        # 3. embed
        embeddings = embed_chunks(chunks)

        # 4. build + save FAISS index
        index = build_faiss_index(embeddings)
        save_index(index, document_id)
        save_chunks(document_id, chunks)

        # mark as READY
        documents_col.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {
                "status": "READY",
                "chunks_count": len(chunks),
                "updated_at": datetime.utcnow()
            }}
        )

    except Exception as e:
        documents_col.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {
                "status": "FAILED",
                "error": str(e),
                "updated_at": datetime.utcnow()
            }}
        )


# -----------------------------
# Upload document
# -----------------------------
@router.post("/upload")
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".pdf", ".txt", ".docx"):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    # create db record immediately
    doc = {
        "filename": file.filename,
        "user_id": user["id"], 
        "status": "PROCESSING",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    res = documents_col.insert_one(doc)
    document_id = str(res.inserted_id)

    # save file
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    dest_path = os.path.join(settings.UPLOAD_DIR, f"{document_id}{ext}")

    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    documents_col.update_one(
        {"_id": res.inserted_id},
        {"$set": {"file_path": dest_path}}
    )

    # background task
    background_tasks.add_task(process_document, document_id, dest_path)

    return {
        "document_id": document_id,
        "filename": file.filename,
        "status": "PROCESSING",
    }


# -----------------------------
# Poll document status
# -----------------------------
@router.get("/status/{document_id}")
def get_document_status(
    document_id: str,
    user: dict = Depends(get_current_user),
):
    try:
        obj_id = ObjectId(document_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid document ID")

    doc = documents_col.find_one(
        {
            "_id": obj_id,
            "user_id": user["id"],   # security check
        }
    )

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return {
        "document_id": document_id,
        "status": doc["status"],
        "chunks_count": doc.get("chunks_count", 0),
    }

@router.get("/list")
def list_documents(user: dict = Depends(get_current_user)):
    docs = documents_col.find(
        {"user_id": user["id"]},
        {"file_path": 0}
    )

    return [
        {
            "document_id": str(doc["_id"]),
            "filename": doc["filename"],
            "status": doc["status"],
        }
        for doc in docs
    ]