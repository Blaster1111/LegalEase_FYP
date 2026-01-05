# main.py
from fastapi import FastAPI
from auth import router as auth_router
from docs_router import router as docs_router
from qa_router import router as qa_router
from config import settings

app = FastAPI(title="Legal RAG API")

app.include_router(auth_router)
app.include_router(docs_router)
app.include_router(qa_router)

@app.get("/")
def root():
    return {"status": "ok", "service": "Legal RAG API"}
