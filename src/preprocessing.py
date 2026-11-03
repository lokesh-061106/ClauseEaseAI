import re
import unicodedata
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize

# We only download if not present, but our install script handles this
try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    pass # Will be downloaded by the main setup

LEGAL_KEYWORDS_TO_PRESERVE = {
    "shall", "must", "may", "not", "unless", "except", 
    "within", "before", "after", "subject to", "provided that"
}

def clean_text(text):
    """
    1 & 2 & 4: Convert text to standard format and normalize Unicode
    """
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize("NFKD", text)
    # 3: Remove unnecessary whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def split_sentences(text):
    """
    5: Split into sentences using NLTK
    """
    try:
        sentences = sent_tokenize(text)
    except:
        # Fallback if punkt is not available
        sentences = re.split(r'(?<=[.!?]) +', text)
    return [s.strip() for s in sentences if s.strip()]

def split_into_clauses(sentence):
    """
    6: Split sentences into clauses using simple punctuation rules
    For legal texts, semicolons and commas often denote separate clauses.
    """
    # Simple rule: split by semicolon or specific coordinating conjunctions
    clauses = re.split(r';\s*|\b(and|or|but)\b\s+', sentence)
    # Filter out the separators that got captured
    clauses = [c.strip() for c in clauses if c and c.strip() not in ['and', 'or', 'but']]
    return clauses

def tokenize_and_preserve(text):
    """
    7: Tokenize text but ensure important legal keywords are preserved as single tokens if possible.
    (This is basic tokenization. 'provided that' and 'subject to' might be split by word_tokenize, 
    but we will reconstruct them or handle them in extraction).
    """
    try:
        tokens = word_tokenize(text)
    except:
        tokens = text.split()
    return tokens

def preprocess_contract(text):
    """
    Full pipeline for preprocessing a contract.
    Input: Raw contract text
    Output: List of cleaned, split clauses
    """
    cleaned = clean_text(text)
    sentences = split_sentences(cleaned)
    
    all_clauses = []
    for sent in sentences:
        clauses = split_into_clauses(sent)
        all_clauses.extend(clauses)
        
    return all_clauses
