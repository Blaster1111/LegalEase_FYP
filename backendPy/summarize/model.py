from transformers import PegasusTokenizer, AutoModelForSeq2SeqLM
import torch
import re
from typing import List
import time

MODEL_NAME = "nsi319/legal-pegasus"
device = "cuda" if torch.cuda.is_available() else "cpu"


# ---------------- LOAD MODEL ONCE ----------------
def load_summarizer():
    print("Loading summarization model...")

    # ✅ FORCE PEGASUS TOKENIZER (SentencePiece)
    tokenizer = PegasusTokenizer.from_pretrained(MODEL_NAME)

    model = AutoModelForSeq2SeqLM.from_pretrained(
        MODEL_NAME
    ).to(device)

    model.eval()
    print("Model loaded.")

    return tokenizer, model


# ---------------- TEXT CLEANING ----------------
def clean_text(text: str) -> str:
    text = re.sub(r'Page\s*\d+\s*of\s*\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'This template is authored by.*?Lawyered\.in\.', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'In case of any queries.*?expert advisors\.', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<<.*?>>', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'Signature\s*\d+.*?Date', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'Désignations.*?Date', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\[.*?\]', '', text, flags=re.DOTALL)
    text = re.sub(r'\(hereinafter.*?\)', '', text, flags=re.DOTALL)
    text = re.sub(r'IN WITNESS WHEREOF.*', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'WHEREAS\b.*?(?=\d+\.)', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# ---------------- CLAUSE EXTRACTION ----------------
def extract_key_clauses(text: str) -> str:
    lines = text.split('.')
    result = []
    for line in lines:
        line = line.strip()
        if len(line.split()) >= 8:
            result.append(line + '.')
    return ' '.join(result)


# ---------------- TOKEN CHUNKING ----------------
def chunk_text_tokens(text: str, tokenizer, max_tokens: int = 900) -> List[str]:
    tokens = tokenizer.encode(text)
    chunks = []
    for i in range(0, len(tokens), max_tokens):
        chunk = tokenizer.decode(tokens[i:i + max_tokens], skip_special_tokens=True)
        chunks.append(chunk)
    return chunks


# ---------------- SANITY CHECK ----------------
def is_valid_chunk(text: str) -> bool:
    words = text.split()
    if len(words) < 30:
        return False
    avg_word_len = sum(len(w) for w in words) / len(words)
    if avg_word_len < 3:
        return False
    alpha_ratio = sum(1 for w in words if w.isalpha()) / len(words)
    if alpha_ratio < 0.4:
        return False
    return True


# ---------------- MAIN SUMMARIZER ----------------
def summarize_text(text: str, tokenizer, model) -> str:
    if not text or not text.strip():
        return ""

    print("Cleaning text...")
    text = clean_text(text)

    print("Extracting key clauses...")
    text = extract_key_clauses(text)

    word_count = len(text.split())

    # -------- SHORT DOC --------
    if word_count < 250:
        print("Short document detected")

        text = "summarize: " + text

        inputs = tokenizer(
            text,
            return_tensors="pt",
            max_length=1024,
            truncation=True,
            padding="longest"
        ).to(device)

        with torch.no_grad():
            outputs = model.generate(
                inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                max_length=80,
                min_length=20,
                num_beams=4,
                length_penalty=2.0,
                no_repeat_ngram_size=3,
                early_stopping=True
            )

        return tokenizer.decode(outputs[0], skip_special_tokens=True)

    # -------- LONG DOC --------
    print("Chunking text...")
    chunks = chunk_text_tokens(text, tokenizer)

    summaries = []

    for i, chunk in enumerate(chunks):
        if not is_valid_chunk(chunk):
            continue

        print(f"Summarizing chunk {i+1}/{len(chunks)}...")
        start = time.time()

        chunk = "summarize: " + chunk

        inputs = tokenizer(
            chunk,
            return_tensors="pt",
            max_length=1024,
            truncation=True,
            padding="longest"
        ).to(device)

        with torch.no_grad():
            outputs = model.generate(
                inputs["input_ids"],
                attention_mask=inputs["attention_mask"],
                max_length=180,
                min_length=40,
                num_beams=5,
                length_penalty=2.0,
                no_repeat_ngram_size=3,
                early_stopping=True
            )

        summary = tokenizer.decode(outputs[0], skip_special_tokens=True)

        if summary:
            summaries.append(summary)

        print(f"Chunk time: {time.time()-start:.2f}s")

    return " ".join(summaries)