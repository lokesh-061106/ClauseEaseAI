import re
from src.legal_terms import LEGAL_DICT

def simplify_clause(text, level="Beginner"):
    """
    Input: Original clause string and education level (Beginner, Intermediate, Advanced).
    Processing: Replaces complex archaic legal terms with plain English equivalents based on the level.
      - Beginner: Aggressive replacement, including modalities (shall -> must).
      - Intermediate: Moderate replacement, avoids changing strict legal modalities.
      - Advanced: Minimal replacement, preserves most legal nuance.
    Output: Simplified clause string.
    Purpose: Provides education-level-based explanation as requested.
    """
    replacements = {}
    
    if level == "Beginner":
        # Full dictionary replacement
        replacements = {k: v.split('(')[0].strip() for k, v in LEGAL_DICT.items()}
    elif level == "Intermediate":
        # Keep strict legal modalities intact to preserve exact meaning
        for k, v in LEGAL_DICT.items():
            if k not in ["shall", "indemnify", "force majeure"]:
                replacements[k] = v.split('(')[0].strip()
    elif level == "Advanced":
        # Only replace extremely archaic conjunctions
        for k, v in LEGAL_DICT.items():
            if k in ["hereinafter", "aforementioned", "mutatis mutandis", "inter alia"]:
                replacements[k] = v.split('(')[0].strip()

    for word, simple in replacements.items():
        # Use regex to match whole words/phrases, ignoring case
        text = re.sub(rf"\b{word}\b", simple, text, flags=re.IGNORECASE)

    return text
