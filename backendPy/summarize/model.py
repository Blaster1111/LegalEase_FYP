from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoConfig
import torch
import re
from typing import List
import time

MODEL_NAME = "nsi319/legal-pegasus"

device = "cuda" if torch.cuda.is_available() else "cpu"
print("CUDA available:", torch.cuda.is_available())
print("Using device:", device)

print("Loading summarization model...")

# Fix tied weights warning
config = AutoConfig.from_pretrained(MODEL_NAME)
config.tie_word_embeddings = False

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(
    MODEL_NAME,
    config=config,
    torch_dtype=torch.float16 if device == "cuda" else torch.float32
).to(device)

model.eval()
print("Model loaded.")


# -------- text cleaning --------
def clean_text(text: str) -> str:
    text = re.sub(r'Page\s*\d+\s*of\s*\d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'This template is authored by.*?Lawyered\.in\.', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'In case of any queries.*?expert advisors\.', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\[Please fill in.*?\]', '', text, flags=re.DOTALL)
    text = re.sub(r'<<.*?>>', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'Signature\s*\d+.*?Date', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'Désignations.*?Date', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# -------- chunking with overlap --------
def chunk_text(text: str, max_tokens: int = 800, overlap: int = 80) -> List[str]:
    if not text:
        return []

    tokens = tokenizer.encode(text, add_special_tokens=False)
    chunks = []
    start = 0
    total = len(tokens)

    while start < total:
        end = min(start + max_tokens, total)
        chunk_tokens = tokens[start:end]
        chunk = tokenizer.decode(
            chunk_tokens,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True
        ).strip()

        if chunk:
            chunks.append(chunk)

        if end == total:
            break

        start = max(0, end - overlap)

    return chunks


# -------- remove duplicate sentences --------
def remove_duplicate_sentences(text: str) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    seen = set()
    uniq = []

    for s in sentences:
        norm = s.strip().lower()
        if not norm:
            continue
        if norm in seen:
            continue
        seen.add(norm)
        uniq.append(s.strip())

    return " ".join(uniq)


# -------- summarization --------
def summarize_text(
    text: str,
    max_length: int = 150,
    min_length: int = 50,
    final_sentence_limit: int = 8
) -> str:
    if not text or not text.strip():
        return ""

    print("cleaning")
    text = clean_text(text)

    if len(text.split()) < 40:
        return text
    
    print("chunking")

    chunks = chunk_text(text, max_tokens=800, overlap=80)
    if not chunks:
        return ""
    
    print("Summarizing")

    summaries = []

    for i, chunk in enumerate(chunks):
        if len(chunk.split()) < 10:
            continue

        print(f"Summarizing chunk {i+1}/{len(chunks)}...")
        start_time = time.time()

        inputs = tokenizer(
            chunk,
            return_tensors="pt",
            truncation=True,
            max_length=1024
        ).to(device)

        with torch.no_grad():
            summary_ids = model.generate(
                **inputs,
                max_new_tokens=max_length,
                do_sample=False,
                num_beams=1,
                no_repeat_ngram_size=2
            )

        summary = tokenizer.decode(
            summary_ids[0],
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True
        )

        if summary:
            summaries.append(summary.strip())

        print(f"Chunk done in {time.time() - start_time:.2f}s")

    if not summaries:
        return ""

    full_summary = " ".join(summaries)
    full_summary = remove_duplicate_sentences(full_summary)

    sentences = re.split(r'(?<=[.!?])\s+', full_summary)
    final_sentences = [s.strip() for s in sentences if s.strip()][:final_sentence_limit]

    return " ".join(final_sentences).strip()
