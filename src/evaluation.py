import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def evaluate_system():
    """
    Evaluates the system by comparing pure Cosine Similarity vs ClauseGuard Risk Score.
    """
    from src.preservation_checker import check_preservation, calculate_similarity
    
    test_cases = [
        {
            "original": "The Supplier shall pay $10,000.",
            "simplified": "The Supplier may pay $10,000.",
            "expected_risk": "HIGH",
            "reason": "Modality changed from Obligation to Permission."
        },
        {
            "original": "The Supplier shall deliver the goods within 15 days.",
            "simplified": "The Supplier must deliver the goods within 15 days.",
            "expected_risk": "LOW",
            "reason": "Modality 'shall' to 'must' preserves obligation."
        },
        {
            "original": "The Purchaser shall pay $10,000 within 15 days.",
            "simplified": "The Purchaser shall pay $10,000 within 30 days.",
            "expected_risk": "HIGH",
            "reason": "Duration changed from 15 to 30 days."
        }
    ]
    
    print("=== System Evaluation: Baseline vs Proposed ===")
    
    for i, tc in enumerate(test_cases):
        orig = tc['original']
        simp = tc['simplified']
        
        sim_score = calculate_similarity(orig, simp)
        report = check_preservation(orig, simp)
        
        print(f"\nTest Case {i+1}:")
        print(f"Original:   {orig}")
        print(f"Simplified: {simp}")
        
        print(f"\nBaseline (Similarity Only): {sim_score}")
        if sim_score > 0.8:
            print("Baseline would likely classify this as 'Preserved' (High Similarity).")
        
        print(f"\nProposed (ClauseGuard Risk Score): {report['risk_level']}")
        print(f"Reasoning: {report['reason']}")
        
        if report['risk_level'] == tc['expected_risk']:
            print("=> TEST PASSED")
        else:
            print(f"=> TEST FAILED (Expected {tc['expected_risk']})")

if __name__ == "__main__":
    evaluate_system()
