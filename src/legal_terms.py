import json
import os
import re

def load_dictionary():
    """
    Input: None.
    Processing: Reads the legal dictionary from the JSON file.
    Output: A dictionary mapping complex terms to simple explanations.
    Purpose: Loads the knowledge base for legal terminology explanation.
    """
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'dictionary', 'legal_dict.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

LEGAL_DICT = load_dictionary()

def detect_legal_terms(text):
    """
    Input: Raw text string.
    Processing: Scans text against the LEGAL_DICT keys using regex to find matching archaic terms.
    Output: A list of dictionaries containing the detected 'term' and its 'explanation'.
    Purpose: Identifies difficult legal words so the UI can explain them to the user.
    """
    detected = []
    text_lower = text.lower()
    for term, explanation in LEGAL_DICT.items():
        if re.search(r'\b' + re.escape(term) + r'\b', text_lower):
            detected.append({"term": term, "explanation": explanation})
    return detected
