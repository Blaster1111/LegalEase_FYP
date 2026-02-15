from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, AutoConfig
import torch
import re

MODEL_NAME = "nsi319/legal-pegasus"

device = "cuda" if torch.cuda.is_available() else "cpu"

print("Loading summarization model...")

# Load config and disable tied embeddings to suppress warnings
config = AutoConfig.from_pretrained(MODEL_NAME)
config.tie_word_embeddings = False

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME, config=config).to(device)
model.eval()

print(f"Model loaded on {device}.")


# -------- text cleaning --------
def clean_text(text: str) -> str:
    # Remove page numbers
    text = re.sub(r'Page \d+ of \d+', '', text)

    # Remove template headers and footers
    text = re.sub(r'This template is authored by.*?Lawyered\.in\.', '', text, flags=re.DOTALL)
    text = re.sub(r'In case of any queries.*?expert advisors\.', '', text, flags=re.DOTALL)

    # Remove placeholders
    text = re.sub(r'\[Please fill in.*?\]', '', text)
    text = re.sub(r'<<.*?>>', '', text)
    text = re.sub(r'<.*?>', '', text)

    # Remove signature blocks
    text = re.sub(r'Signature \d+.*?Date', '', text, flags=re.DOTALL)
    text = re.sub(r'Désignations.*?Date', '', text, flags=re.DOTALL)

    # Normalize spaces
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


# -------- chunking with overlap --------
def chunk_text(text: str, max_tokens: int = 400, overlap: int = 50):
    """
    Split text into overlapping chunks for better context preservation.
    Max 400 tokens per chunk to stay within model limits.
    """
    # Encode without special tokens for accurate count
    tokens = tokenizer.encode(text, add_special_tokens=False)
    chunks = []

    start = 0
    while start < len(tokens):
        end = start + max_tokens
        chunk_tokens = tokens[start:end]
        
        chunk_text = tokenizer.decode(chunk_tokens, skip_special_tokens=True)
        chunks.append(chunk_text)
        
        if end >= len(tokens):
            break
        start = end - overlap

    return chunks


# -------- remove duplicate sentences --------
def remove_duplicate_sentences(text: str) -> str:
    """Remove duplicate sentences from summary."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    seen = set()
    unique_sentences = []
    
    for sentence in sentences:
        normalized = sentence.lower().strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique_sentences.append(sentence)
    
    return " ".join(unique_sentences)


# -------- summarization --------
def summarize_text(text: str, max_length: int = 150, min_length: int = 50) -> str:
    """
    Summarize legal text with improved parameters.
    """
    if not text or not text.strip():
        return ""
    
    text = clean_text(text)
    
    # If text is very short, return as-is
    if len(text.split()) < 30:
        return text
    
    chunks = chunk_text(text, max_tokens=400, overlap=50)
    
    if not chunks:
        return ""
    
    summaries = []

    for chunk in chunks:
        # Skip very short chunks
        if len(chunk.split()) < 10:
            continue
        
        # Tokenize with strict truncation to prevent length errors
        inputs = tokenizer(
            chunk,
            return_tensors="pt",
            truncation=True,
            max_length=512,  # Match the model's actual max input length
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

        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
        summaries.append(summary)

    # Join and deduplicate
    full_summary = " ".join(summaries)
    full_summary = remove_duplicate_sentences(full_summary)
    
    return full_summary.strip()