# utils.py
import os, io, json, pickle
from config import settings
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
import pdfplumber
from docx import Document
import faiss
import numpy as np
import requests

# Load embedder once
EMBED_MODEL = "intfloat/e5-large-v2"
embedder = SentenceTransformer(EMBED_MODEL)

# chunker
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800, chunk_overlap=150,
    separators=["\n\n","\n","Clause ","Section ","Article ","Paragraph ","."," "], keep_separator=True
)

ALLOWED = (".pdf", ".txt", ".docx")

def extract_text_from_file(file_path: str):
    text = ""
    if file_path.lower().endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            for p in pdf.pages:
                t = p.extract_text()
                if t:
                    text += t + "\n"
    elif file_path.lower().endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
    elif file_path.lower().endswith(".docx"):
        doc = Document(file_path)
        text = "\n".join([p.text for p in doc.paragraphs])
    else:
        raise ValueError("Unsupported file type")
    return text.strip()

def chunk_text(text: str):
    return splitter.split_text(text)

def embed_chunks(chunks: list, batch_size=32):
    emb = embedder.encode(chunks, batch_size=batch_size, convert_to_numpy=True, show_progress_bar=False, normalize_embeddings=True)
    return emb.astype("float32")

def build_faiss_index(embeddings: np.ndarray):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    return index

def save_index(index, doc_id: str):
    path = os.path.join(settings.INDEX_DIR, f"{doc_id}.index")
    faiss.write_index(index, path)
    return path

def load_index(doc_id: str):
    path = os.path.join(settings.INDEX_DIR, f"{doc_id}.index")
    if not os.path.exists(path):
        return None
    return faiss.read_index(path)

def save_chunks(doc_id: str, chunks: list):
    path = os.path.join(settings.CHUNKS_DIR, f"{doc_id}.pkl")
    with open(path, "wb") as f:
        pickle.dump(chunks, f)
    return path

def load_chunks(doc_id: str):
    path = os.path.join(settings.CHUNKS_DIR, f"{doc_id}.pkl")
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return pickle.load(f)

# OpenRouter LLM call
def generate_with_openrouter(prompt: str, max_tokens=300, temperature=0.1):
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "You are a legal assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    resp = requests.post(settings.OPENROUTER_BASE_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"].strip()

# retrieval helper (simple top-k using faiss index and chunks)
def retrieve_chunks_for_doc(doc_id: str, query: str, k=3, fetch_k=10):
    index = load_index(doc_id)
    if index is None:
        return [], []
    q_emb = embedder.encode([query], normalize_embeddings=True)
    scores, indices = index.search(q_emb.astype("float32"), fetch_k)
    # load chunks and select top k
    chunks = load_chunks(doc_id)
    if chunks is None:
        return [], []
    candidate_chunks = [chunks[i] for i in indices[0] if i < len(chunks)]
    return candidate_chunks[:k], (scores[0][:k].tolist() if len(scores)>0 else [])
