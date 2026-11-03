import pandas as pd
import os
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

def train_classifier(data_path="data/raw/dataset.csv", model_path="models/classifier.pkl", vectorizer_path="models/vectorizer.pkl"):
    """
    Trains a simple TF-IDF + Logistic Regression classifier for contract clauses.
    Input: Path to the dataset CSV
    Output: Saves the trained model and vectorizer to disk, returns evaluation metrics.
    """
    if not os.path.exists(data_path):
        print(f"Dataset not found at {data_path}")
        return None

    df = pd.read_csv(data_path)
    
    # Check if required columns exist
    if 'text' not in df.columns or 'category' not in df.columns:
        print("Dataset missing 'text' or 'category' columns.")
        return None
        
    df = df.dropna(subset=['text', 'category'])
    
    X = df['text']
    y = df['category']
    
    # Split dataset: 80% training, 20% testing
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Feature extraction using TF-IDF
    # We use TF-IDF because it highlights important words while downplaying common stop words
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    X_train_vec = vectorizer.fit_transform(X_train)
    X_test_vec = vectorizer.transform(X_test)
    
    # Train Logistic Regression model
    # Logistic Regression is simple, explainable, and works well for text classification baseline
    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_train_vec, y_train)
    
    # Predict on test set
    y_pred = model.predict(X_test_vec)
    
    # Calculate metrics
    metrics = {
        "Accuracy": accuracy_score(y_test, y_pred),
        "Precision": precision_score(y_test, y_pred, average='weighted', zero_division=0),
        "Recall": recall_score(y_test, y_pred, average='weighted', zero_division=0),
        "F1-Score": f1_score(y_test, y_pred, average='weighted', zero_division=0),
        "Confusion Matrix": confusion_matrix(y_test, y_pred).tolist(),
        "Labels": sorted(list(set(y_test) | set(y_pred)))
    }
    
    # Save the model and vectorizer
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    with open(vectorizer_path, 'wb') as f:
        pickle.dump(vectorizer, f)
        
    return metrics

def predict_category(text, model_path="models/classifier.pkl", vectorizer_path="models/vectorizer.pkl"):
    """
    Predicts the category of a given clause using the trained model.
    """
    if not os.path.exists(model_path) or not os.path.exists(vectorizer_path):
        return "Unknown"
        
    with open(model_path, 'rb') as f:
        model = pickle.load(f)
    with open(vectorizer_path, 'rb') as f:
        vectorizer = pickle.load(f)
        
    vec = vectorizer.transform([text])
    pred = model.predict(vec)
    return pred[0]

if __name__ == "__main__":
    metrics = train_classifier()
    if metrics:
        print("Model trained successfully.")
        for k, v in metrics.items():
            if k not in ["Confusion Matrix", "Labels"]:
                print(f"{k}: {v:.4f}")
            else:
                print(f"{k}:\n{v}")
