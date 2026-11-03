import re
try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
except Exception:
    # If not found or if there is a C-extension error (like blis.cy), we rely purely on regex fallback
    nlp = None

# Keyword lists for modality, conditions, and exceptions
MODALITIES = {
    "shall": "shall",
    "must": "must",
    "may": "may",
    "will": "will",
    "should": "should",
    "required to": "must",
    "is obligated to": "must",
    "agrees to": "must",
    "permitted to": "may",
    "allowed to": "may",
    "shall not": "shall not",
    "must not": "must not",
    "prohibited from": "must not",
    "not permitted to": "must not",
    "is forbidden to": "must not"
}

CONDITIONS = ["if", "when", "provided that", "subject to", "in the event"]
EXCEPTIONS = ["unless", "except", "notwithstanding", "other than"]

def extract_modality(text):
    """
    Extracts the legal modality (shall, must, may, etc.) from the text.
    Input: Clause text
    Output: Modality string or None
    """
    text_lower = text.lower()
    for mod in sorted(MODALITIES.keys(), key=len, reverse=True):
        if re.search(r'\b' + re.escape(mod) + r'\b', text_lower):
            return MODALITIES[mod]
    return None

def extract_condition_exception(text):
    """
    Extracts conditions and exceptions based on predefined keywords.
    Input: Clause text
    Output: Tuple of (condition string, exception string)
    """
    text_lower = text.lower()
    
    found_condition = None
    for cond in CONDITIONS:
        if cond in text_lower:
            found_condition = cond
            break
            
    found_exception = None
    for exc in EXCEPTIONS:
        if exc in text_lower:
            found_exception = exc
            break
            
    return found_condition, found_exception

def extract_entities_regex(text):
    """
    Fallback regex-based entity extraction for numbers, dates, and currency.
    """
    # Simple regex for amounts (e.g., $10,000, 50%)
    amounts = re.findall(r'(\$\s*\d+(?:,\d+)*(?:\.\d+)?|\d+(?:,\d+)*(?:\.\d+)?\s*%)', text)
    
    # Simple regex for durations (e.g., 15 days, 3 months)
    durations = re.findall(r'\b(\d+\s+(?:days?|months?|years?|weeks?))\b', text, re.IGNORECASE)
    
    return {
        "amounts": amounts if amounts else [],
        "durations": durations if durations else []
    }

def extract_information(text):
    """
    Main function to extract structured legal information from a clause.
    Input: Clause string
    Output: Dictionary of extracted elements
    """
    extracted = {
        "actor": None,
        "action": None,
        "modality": extract_modality(text),
        "date": None,
        "duration": None,
        "amount": None,
        "condition": None,
        "exception": None
    }
    
    cond, exc = extract_condition_exception(text)
    extracted["condition"] = cond
    extracted["exception"] = exc
    
    # Try using spaCy for NLP-based extraction
    if nlp is not None:
        doc = nlp(text)
        
        # Extract actor (usually the subject before the modality)
        for token in doc:
            if token.dep_ == "nsubj":
                extracted["actor"] = token.text
                break
                
        # Extract action (usually the main verb)
        for token in doc:
            if token.pos_ == "VERB":
                extracted["action"] = token.text
                break
                
        # Extract specific entities
        dates = []
        amounts = []
        for ent in doc.ents:
            if ent.label_ == "DATE":
                dates.append(ent.text)
            elif ent.label_ == "MONEY":
                amounts.append(ent.text)
                
        if dates:
            # We assume durations often contain "days", "months", "years"
            durations = [d for d in dates if any(w in d.lower() for w in ["day", "month", "year", "week"])]
            other_dates = [d for d in dates if d not in durations]
            
            if durations: extracted["duration"] = durations[0]
            if other_dates: extracted["date"] = other_dates[0]
            
        if amounts:
            extracted["amount"] = amounts[0]
            
    # Fallback to regex if spaCy missed things
    regex_ents = extract_entities_regex(text)
    if not extracted["amount"] and regex_ents["amounts"]:
        extracted["amount"] = regex_ents["amounts"][0]
    if not extracted["duration"] and regex_ents["durations"]:
        extracted["duration"] = regex_ents["durations"][0]
        
    return extracted

if __name__ == "__main__":
    sample = "The Supplier shall deliver the goods within 15 days."
    print(extract_information(sample))
