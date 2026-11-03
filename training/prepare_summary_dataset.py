import pandas as pd
import numpy as np
import os
import nltk
from datasets import load_dataset
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

def extract_features(sentence, position, total_sentences):
    # Base features
    length = len(sentence.split())
    rel_position = position / max(1, total_sentences)
    
    # Keyword sets
    obligations = r'\b(shall|must|required to|is obligated to)\b'
    permissions = r'\b(may|permitted to|allowed to)\b'
    prohibitions = r'\b(shall not|must not|prohibited from|may not)\b'
    conditions = r'\b(if|unless|provided that|subject to|except)\b'
    
    # Counts
    obl_count = len(re.findall(obligations, sentence.lower()))
    per_count = len(re.findall(permissions, sentence.lower()))
    pro_count = len(re.findall(prohibitions, sentence.lower()))
    cond_count = len(re.findall(conditions, sentence.lower()))
    
    has_number = 1 if re.search(r'\b\d+\b', sentence) else 0
    has_date = 1 if re.search(r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b', sentence.lower()) else 0
    has_money = 1 if re.search(r'[\$£€₹]\d+', sentence) else 0
    
    return {
        'sentence_length': length,
        'sentence_position': rel_position,
        'has_obligation': obl_count,
        'has_permission': per_count,
        'has_prohibition': pro_count,
        'has_condition': cond_count,
        'has_number': has_number,
        'has_date': has_date,
        'has_money': has_money
    }

def prepare_dataset():
    print("Fetching BillSum dataset from Hugging Face...")
    try:
        # Load a small subset for speed
        dataset = load_dataset("billsum", split="train[:500]", trust_remote_code=True)
        df = dataset.to_pandas()
        print(f"Successfully loaded {len(df)} records from BillSum.")
    except Exception as e:
        print(f"Failed to load BillSum (Error: {e}). Generating synthetic legislative/contract data for training...")
        # Synthetic fallback mimicking structure
        df = pd.DataFrame({
            'text': [
                "The Supplier shall deliver the goods within 15 days. The Purchaser may reject defective goods. If rejected, the Supplier must refund the payment. The total amount is $10,000.",
                "This agreement is governed by the laws of New York. Arbitration shall be held in Manhattan. Neither party shall be liable for indirect damages.",
                "The tenant must pay rent on the 1st of every month. A late fee of $50 applies after 5 days. The landlord may evict the tenant for non-payment."
            ] * 100,
            'summary': [
                "Supplier must deliver goods in 15 days or refund $10,000 for defects.",
                "New York law governs. No liability for indirect damages.",
                "Tenant pays rent on the 1st or faces a $50 fee and possible eviction."
            ] * 100
        })

    dataset_rows = []
    vectorizer = TfidfVectorizer(stop_words='english')
    
    print("Processing sentences and generating ML labels (No LLMs used)...")
    for idx, row in df.iterrows():
        doc_text = row['text']
        sum_text = row['summary']
        
        doc_sents = nltk.sent_tokenize(doc_text)
        sum_sents = nltk.sent_tokenize(sum_text)
        
        if not doc_sents or not sum_sents: continue
        
        try:
            # Calculate similarity matrix between document sentences and summary sentences
            # If a document sentence is highly similar to ANY summary sentence, it is "important" (label 1)
            tfidf_matrix = vectorizer.fit_transform(doc_sents + sum_sents)
            doc_vecs = tfidf_matrix[:len(doc_sents)]
            sum_vecs = tfidf_matrix[len(doc_sents):]
            
            sim_matrix = cosine_similarity(doc_vecs, sum_vecs)
            
            for s_idx, doc_sent in enumerate(doc_sents):
                # Max similarity to any summary sentence
                max_sim = np.max(sim_matrix[s_idx]) if sim_matrix.size > 0 else 0
                
                # Threshold for importance
                label = 1 if max_sim > 0.3 else 0
                
                features = extract_features(doc_sent, s_idx, len(doc_sents))
                features['document_id'] = idx
                features['sentence'] = doc_sent
                features['label'] = label
                
                dataset_rows.append(features)
        except ValueError:
            # Handles empty vocab errors
            pass

    final_df = pd.DataFrame(dataset_rows)
    os.makedirs('data/processed', exist_ok=True)
    final_df.to_csv('data/processed/sentence_importance_dataset.csv', index=False)
    
    print(f"Dataset generated! Total sentences: {len(final_df)}. Positive labels: {final_df['label'].sum()}")

if __name__ == "__main__":
    prepare_dataset()
