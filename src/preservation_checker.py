import joblib
import os
import numpy as np
import warnings
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.information_extractor import extract_information
from training.prepare_preservation_dataset import extract_preservation_features

warnings.filterwarnings('ignore')

try:
    pres_model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'preservation_model.pkl')
    preservation_model = joblib.load(pres_model_path)
except Exception as e:
    preservation_model = None

def check_preservation(original, simplified):
    """
    Input: Original clause string and Simplified clause string.
    Processing: 
      1. Uses TRAINED Logistic Regression model (Model 2) for semantic baseline.
      2. Uses Legal Preservation Rule Engine (NER, modalities, dates, amounts) to strictly verify features.
      3. Overrides ML model if strict legal elements are breached.
    Output: Dictionary containing risk_level, preserved elements, changed elements, reason, similarity.
    Purpose: Ensures legally safe simplification using explainable hybrid ML + Rule methodology.
    """
    # 1. Base ML Model Prediction (Semantic Entailment)
    ml_probability = 1.0
    if preservation_model is not None:
        try:
            # We need TF-IDF similarity for the ML model
            vec = TfidfVectorizer(stop_words='english')
            vec.fit([original, simplified])
            v_o = vec.transform([original])
            v_s = vec.transform([simplified])
            sim = cosine_similarity(v_o, v_s)[0][0]
            
            features = extract_preservation_features(original, simplified)
            X = np.array([[features['word_overlap'], features['num_changed'], features['modality_changed'], sim]])
            
            # Predict probability of being PRESERVED (Class 1)
            ml_probability = preservation_model.predict_proba(X)[0][1]
        except:
            ml_probability = 0.5
            
    # 2. Strict Rule-Based Extraction (The Rule Engine)
    orig_info = extract_information(original)
    simp_info = extract_information(simplified)
    
    risk_level = "PRESERVED"
    reason = "No significant legal meaning changes detected."
    preserved = []
    changed = []
    
    # Check Modality
    if orig_info['modality'] != simp_info['modality']:
        if orig_info['modality'] and not simp_info['modality']:
            risk_level = "HIGH"
            reason = "A critical obligation, permission, or prohibition was removed."
            changed.append(f"Modality ({orig_info['modality']} -> removed)")
        elif (orig_info['modality'] in ['shall', 'must', 'required to', 'shall not', 'must not'] and 
              simp_info['modality'] in ['may', 'permitted to']):
            risk_level = "HIGH"
            reason = "An obligation/prohibition was dangerously changed into a permission."
            changed.append(f"Modality ({orig_info['modality']} -> {simp_info['modality']})")
        else:
            risk_level = "LOW"
            reason = "Small wording changes that likely preserve the core legal meaning."
            changed.append(f"Modality ({orig_info['modality']} -> {simp_info['modality']})")
    else:
        if orig_info['modality']:
            preserved.append(f"Modality ({orig_info['modality']})")
            
    # Check Dates and Amounts (Numbers)
    orig_nums = []
    simp_nums = []
    import re
    # Extract all numbers as a fallback
    all_orig_nums = re.findall(r'\b\d+\b', original)
    all_simp_nums = re.findall(r'\b\d+\b', simplified)
    
    for key in ['date', 'duration', 'amount']:
        if orig_info.get(key): orig_nums.append(str(orig_info[key]))
        if simp_info.get(key): simp_nums.append(str(simp_info[key]))
        
    if set(all_orig_nums) != set(all_simp_nums):
        risk_level = "HIGH"
        reason = "Critical numeric values (dates, durations, money, or percentages) were altered."
        changed.append(f"Numbers ({all_orig_nums} -> {all_simp_nums})")
    elif orig_nums or all_orig_nums:
        preserved.append("Numeric Values")
        
    # Check Actors fallback
    actors_list = [
        "tenant", "landlord", "supplier", "customer", "contractor", 
        "employee", "employer", "buyer", "seller", "company", "corporation",
        "client", "developer", "user", "vendor", "purchaser"
    ]
    for a in actors_list:
        if a in original.lower() and a not in simplified.lower():
            risk_level = "HIGH"
            reason = "The legal party/actor was changed or removed."
            changed.append(f"Actor ({a} -> removed/changed)")
            break
            
    # Conditions and Exceptions fallback
    if orig_info.get('condition') and not simp_info.get('condition'):
        if risk_level in ["PRESERVED", "LOW"]: risk_level = "MEDIUM"
        changed.append("Condition removed")
    if orig_info.get('exception') and not simp_info.get('exception'):
        if risk_level in ["PRESERVED", "LOW"]: risk_level = "MEDIUM"
        changed.append("Exception removed")

    # If completely identical, override probability
    if original.strip().lower() == simplified.strip().lower():
        ml_probability = 1.0

    # Combine ML probability + Rules
    # If ML says it's a contradiction (< 0.4 probability of entailment), override to MEDIUM risk if rules missed it
    if ml_probability < 0.4 and risk_level == "PRESERVED":
        risk_level = "MEDIUM"
        reason = "Semantic model detected a potential contextual meaning shift."
        
    return {
        "risk_level": risk_level,
        "preserved": preserved,
        "changed": changed,
        "reason": reason,
        "similarity": ml_probability
    }
