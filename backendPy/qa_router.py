# qa_router.py
from fastapi import APIRouter, Depends, HTTPException
from models import QARequest, QAResponse
from auth import get_current_user
from utils import retrieve_chunks_for_doc, generate_with_openrouter
from db import chats_col
from datetime import datetime
from bson import ObjectId
import json

router = APIRouter(prefix="/qa", tags=["qa"])

@router.post("/ask", response_model=QAResponse)
def ask_question(req: QARequest, user: dict = Depends(get_current_user)):
    # check document exists & processed
    from db import documents_col
    doc = documents_col.find_one({"_id": ObjectId(req.document_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.get("status") != "processed":
        raise HTTPException(status_code=400, detail="Document not yet processed")

    contexts, scores = retrieve_chunks_for_doc(req.document_id, req.question, k=req.top_k, fetch_k=20)
    context_text = "\n\n---\n\n".join([f"Context {i+1} (relevance: {score:.2f}): {ctx}" for i, (ctx, score) in enumerate(zip(contexts, scores))])

    prompt = f"""You are a precise legal assistant. Answer questions based ONLY on the provided contract excerpts.
Be concise, cite relevant sections if possible, and if information is missing, say: "The document does not specify this."

Contract excerpts:
{context_text}

Question: {req.question}
"""
    answer = generate_with_openrouter(prompt, max_tokens=300, temperature=0.0)

    # save chat
    chat_doc = {
        "user_id": ObjectId(user["id"]),
        "document_id": ObjectId(req.document_id),
        "question": req.question,
        "answer": answer,
        "contexts": contexts,
        "created_at": datetime.utcnow()
    }
    chats_col.insert_one(chat_doc)

    return QAResponse(answer=answer, contexts=contexts)
