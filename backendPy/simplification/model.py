import re
from .uslt_rules import LEGAL_SIMPLIFICATION_RULES

def apply_rules(text: str) -> str:
    for k in sorted(LEGAL_SIMPLIFICATION_RULES, key=len, reverse=True):
        v = LEGAL_SIMPLIFICATION_RULES[k]
        text = re.sub(rf"\b{k}\b", v, text, flags=re.IGNORECASE)
    return text

def simplify_text(text: str) -> str:
    text = apply_rules(text)
    sentences = re.split(r'[.!?]+', text)

    simplified = []
    for s in sentences:
        words = s.strip().split()
        if 5 <= len(words) <= 25:
            simplified.append(s.strip())

    return ". ".join(simplified[:10]) + "."
