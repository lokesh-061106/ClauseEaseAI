import pandas as pd
import os

def check_dataset_health():
    filepath = "data/raw/dataset.csv"
    if not os.path.exists(filepath):
        print(f"Error: Dataset not found at {filepath}")
        return

    df = pd.DataFrame(pd.read_csv(filepath))
    print("=== Dataset Health Report ===")
    
    num_samples = len(df)
    missing_values = df.isnull().sum().to_dict()
    duplicates = df.duplicated(subset=['text']).sum()
    
    df['text_length'] = df['text'].astype(str).apply(len)
    
    avg_len = df['text_length'].mean()
    min_len = df['text_length'].min()
    max_len = df['text_length'].max()
    
    class_dist = df['category'].value_counts().to_dict() if 'category' in df.columns else "N/A"
    
    print(f"Number of samples: {num_samples}")
    print(f"Missing values: {missing_values}")
    print(f"Duplicates: {duplicates}")
    print(f"Average text length: {avg_len:.2f} characters")
    print(f"Minimum text length: {min_len} characters")
    print(f"Maximum text length: {max_len} characters")
    print(f"Class distribution: {class_dist}")

    # Write a simple text report
    os.makedirs("results", exist_ok=True)
    with open("results/dataset_health_report.txt", "w") as f:
        f.write("=== Dataset Health Report ===\n")
        f.write(f"Number of samples: {num_samples}\n")
        f.write(f"Missing values: {missing_values}\n")
        f.write(f"Duplicates: {duplicates}\n")
        f.write(f"Average text length: {avg_len:.2f} characters\n")
        f.write(f"Minimum text length: {min_len} characters\n")
        f.write(f"Maximum text length: {max_len} characters\n")
        f.write(f"Class distribution: {class_dist}\n")
        
    print("\nReport saved to results/dataset_health_report.txt")

if __name__ == "__main__":
    check_dataset_health()
