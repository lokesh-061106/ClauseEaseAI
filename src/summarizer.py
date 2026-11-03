import nltk
import joblib
import os
import numpy as np
from scipy.sparse import hstack
import warnings

# Suppress warnings from scikit-learn version mismatches if any
warnings.filterwarnings('ignore')

try:
    model_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'sentence_importance_model.pkl')
    vec_path = os.path.join(os.path.dirname(__file__), '..', 'models', 'sentence_vectorizer.pkl')
    importance_model = joblib.load(model_path)
    importance_vectorizer = joblib.load(vec_path)
except Exception as e:
    importance_model = None
    importance_vectorizer = None
    print(f"Warning: Summarization models not found. Run training scripts first. {e}")

def summarize_text_extractive(text, num_sentences=3):
    """
    Input: Raw text string, number of sentences to extract.
    Processing: 
      1. Splits text into sentences.
      2. Extracts traditional ML features (length, position, keywords).
      3. Uses TRAINED Logistic Regression model (Model 1) to predict importance probability.
      4. Selects the top N highest-scoring sentences based on ML confidence.
    Output: A string containing the selected summary sentences.
    Purpose: Provides an explainable, non-generative, supervised ML extractive summary.
    """
    try:
        sentences = nltk.sent_tokenize(text)
    except:
        sentences = text.split('.')
        
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    if len(sentences) <= num_sentences:
        return " ".join(sentences)
        
    if importance_model is None or importance_vectorizer is None:
        return " ".join(sentences[:num_sentences])
        
    # Feature extraction exactly as in training
    from training.prepare_summary_dataset import extract_features
    
    features_list = []
    for idx, sent in enumerate(sentences):
        feats = extract_features(sent, idx, len(sentences))
        features_list.append([
            feats['sentence_length'], feats['sentence_position'], feats['has_obligation'], 
            feats['has_permission'], feats['has_prohibition'], feats['has_condition'], 
            feats['has_number'], feats['has_date'], feats['has_money']
        ])
        
    X_numeric = np.array(features_list)
    X_text = importance_vectorizer.transform(sentences)
    X = hstack([X_text, X_numeric])
    
    # Get probability of being 'important' (Class 1)
    probabilities = importance_model.predict_proba(X)[:, 1]
    
    # Get the indices of the top N scoring sentences
    top_indices = probabilities.argsort()[-num_sentences:][::-1]
    
    # Sort indices to maintain chronological order in output
    top_indices.sort()
    
    summary = " ".join([sentences[i] for i in top_indices])
    return summary
