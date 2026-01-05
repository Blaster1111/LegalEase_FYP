# qa_router.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from models import QARequest, QAResponse, QAChat
from auth import get_current_user
from utils import retrieve_chunks_for_doc, generate_with_openrouter
from db import chats_col
from datetime import datetime
from bson import ObjectId
import json


router = APIRouter(prefix="/qa", tags=["qa"])




@router.get("/history/{document_id}", response_model=List[QAChat])
def get_document_chats(document_id: str, user: dict = Depends(get_current_user)):
    """
    Get all Q&A chats for a specific document belonging to the current user.
    """
    try:
        doc_obj_id = ObjectId(document_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid document ID")

    # Fetch chats for this user and document
    chats = list(chats_col.find({"user_id": ObjectId(user["id"]), "document_id": doc_obj_id}).sort("created_at", -1))

    return [
        QAChat(
            question=chat["question"],
            answer=chat["answer"],
            contexts=chat.get("contexts", []),
            timestamp=chat.get("created_at", datetime.utcnow())
        )
        for chat in chats
    ]

@router.post("/ask", response_model=QAResponse)
def ask_question(req: QARequest, user: dict = Depends(get_current_user)):
    # check document exists & processed
    from db import documents_col
    doc = documents_col.find_one({"_id": ObjectId(req.document_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # accept both 'READY' and 'processed' statuses
    if doc.get("status") not in ["READY", "processed"]:
        raise HTTPException(status_code=400, detail="Document not yet processed")

    # retrieve top-k relevant chunks
    contexts, scores = retrieve_chunks_for_doc(req.document_id, req.question, k=req.top_k, fetch_k=20)
    context_text = "\n\n---\n\n".join(
        [f"Context {i+1} (relevance: {score:.2f}): {ctx}" for i, (ctx, score) in enumerate(zip(contexts, scores))]
    )

    prompt = f"""<|system|>
You are a precise legal assistant. Answer questions based ONLY on the provided contract excerpts.
Be concise, cite relevant sections if possible, and if information is missing, say: "The document does not specify this."
<|end|>

<|user|>
Contract excerpts:
{context_text}

Question: {req.question}
<|end|>

<|assistant|>
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

