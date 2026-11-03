import pandas as pd
import numpy as np
import os
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import hstack

def train_model():
    print("Loading prepared dataset...")
    df = pd.read_csv('data/processed/sentence_importance_dataset.csv')
    
    # Text features
    print("Vectorizing text features (TF-IDF)...")
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    X_text = vectorizer.fit_transform(df['sentence'].fillna(''))
    
    # Numeric features
    X_numeric = df[['sentence_length', 'sentence_position', 'has_obligation', 
                    'has_permission', 'has_prohibition', 'has_condition', 
                    'has_number', 'has_date', 'has_money']].values
                    
    X = hstack([X_text, X_numeric])
    y = df['label'].values
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training Logistic Regression model...")
    model = LogisticRegression(class_weight='balanced', max_iter=1000)
    model.fit(X_train, y_train)
    
    print("Evaluating Model...")
    y_pred = model.predict(X_test)
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    cm = confusion_matrix(y_test, y_pred)
    
    print("=== MODEL 1 EVALUATION (Sentence Importance) ===")
    print(f"Accuracy:  {acc:.4f}")
    print(f"Precision: {prec:.4f}")
    print(f"Recall:    {rec:.4f}")
    print(f"F1 Score:  {f1:.4f}")
    print(f"Confusion Matrix:\n{cm}")
    
    os.makedirs('models', exist_ok=True)
    joblib.dump(model, 'models/sentence_importance_model.pkl')
    joblib.dump(vectorizer, 'models/sentence_vectorizer.pkl')
    
    # Save experiment metrics
    os.makedirs('experiments', exist_ok=True)
    with open('experiments/model_1_results.txt', 'w') as f:
        f.write(f"Accuracy: {acc}\nPrecision: {prec}\nRecall: {rec}\nF1: {f1}\n")
        
    print("Model and vectorizer saved to models/")

if __name__ == "__main__":
    train_model()
