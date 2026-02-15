from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import re
from typing import List

MODEL_NAME = "nsi319/legal-pegasus"

device = "cuda" if torch.cuda.is_available() else "cpu"

print("Loading summarization model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(device)
model.eval()
print(f"Model loaded on {device}.")


# -------- text cleaning --------
def clean_text(text: str) -> str:
    # Remove page numbers like "Page 1 of 6"
    text = re.sub(r'Page\s*\d+\s*of\s*\d+', '', text, flags=re.IGNORECASE)

    # Remove common template headers/footers (Lawyered.in etc.)
    text = re.sub(r'This template is authored by.*?Lawyered\.in\.', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'In case of any queries.*?expert advisors\.', '', text, flags=re.DOTALL | re.IGNORECASE)

    # Remove placeholders like [Please fill in ...] and <<...>> and <...>
    text = re.sub(r'\[Please fill in.*?\]', '', text, flags=re.DOTALL)
    text = re.sub(r'<<.*?>>', '', text)
    text = re.sub(r'<.*?>', '', text)

    # Remove obvious signature blocks (best-effort)
    text = re.sub(r'Signature\s*\d+.*?Date', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'Désignations.*?Date', '', text, flags=re.DOTALL | re.IGNORECASE)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


# -------- chunking with overlap --------
def chunk_text(text: str, max_tokens: int = 400, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks measured in tokenizer tokens.
    """
    if not text:
        return []

    # Encode without adding special tokens so counts match generation limits
    tokens = tokenizer.encode(text, add_special_tokens=False)
    chunks: List[str] = []
    start = 0
    total = len(tokens)

    while start < total:
        end = min(start + max_tokens, total)
        chunk_tokens = tokens[start:end]
        chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True, clean_up_tokenization_spaces=True)
        chunk_text = chunk_text.strip()
        if chunk_text:
            chunks.append(chunk_text)
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
def summarize_text(text: str, max_length: int = 150, min_length: int = 50, final_sentence_limit: int = 8) -> str:
    """
    Summarize legal text by:
      1. Cleaning the text
      2. Chunking with overlap
      3. Summarizing each chunk
      4. Deduplicating and limiting final summary length
    """
    if not text or not text.strip():
        return ""

    text = clean_text(text)

    # If the text is already short, return cleaned text (or optionally run a single-pass summarize)
    if len(text.split()) < 40:
        return text

    chunks = chunk_text(text, max_tokens=400, overlap=50)
    if not chunks:
        return ""

    summaries = []
    for chunk in chunks:
        if len(chunk.split()) < 10:
            continue

        inputs = tokenizer(
            chunk,
            return_tensors="pt",
            truncation=True,
            max_length=512,  # safe guard
            padding=False
        ).to(device)

        with torch.no_grad():
            summary_ids = model.generate(
                **inputs,
                max_length=max_length,
                min_length=min_length,
                num_beams=4,
                length_penalty=2.0,
                early_stopping=True,
                no_repeat_ngram_size=3
            )

        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)
        if summary:
            summaries.append(summary.strip())

    if not summaries:
        return ""

    # Join chunk summaries, dedupe sentences, and limit length
    full_summary = " ".join(summaries)
    full_summary = remove_duplicate_sentences(full_summary)

    # Limit final output to N sentences for consistent size/UX
    sentences = re.split(r'(?<=[.!?])\s+', full_summary)
    final_sentences = [s.strip() for s in sentences if s.strip()][:final_sentence_limit]
    final_summary = " ".join(final_sentences).strip()

    return final_summary
