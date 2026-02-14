from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

MODEL_NAME = "nsi319/legal-pegasus"

device = "cuda" if torch.cuda.is_available() else "cpu"

print("Loading summarization model...")

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(device)
model.eval()

print("Model loaded.")


def summarize_text(text: str, max_length: int = 120) -> str:
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True
    ).to(device)

    with torch.no_grad():
        summary_ids = model.generate(
            **inputs,
            max_length=max_length,
            num_beams=4,
            early_stopping=True
        )

    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary
