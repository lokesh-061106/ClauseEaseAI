import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.preprocessing import preprocess_contract
from src.simplifier import simplify_clause
from src.preservation import check_preservation
from src.classifier import predict_category

def test_pipeline():
    print("Testing Pipeline...\n")
    
    # 5. Test a clause where meaning is preserved
    test_1 = "The Supplier shall deliver the goods within 15 days."
    print("TEST 1: Meaning Preserved")
    run_test(test_1, "The Supplier must deliver the goods within 15 days.")
    
    # 6. Test a clause where modality changes
    test_2 = "The Supplier shall deliver the goods within 15 days."
    print("TEST 2: Modality Changed")
    run_test(test_2, "The Supplier may deliver the goods within 15 days.")
    
    # 7. Test a clause where numbers change
    test_3 = "The Purchaser shall pay $10,000 within 15 days."
    print("TEST 3: Numbers Changed")
    run_test(test_3, "The Purchaser shall pay $10,000 within 30 days.")
    
    # 8. Test a clause where an exception disappears
    test_4 = "The Supplier shall deliver the goods, unless it rains."
    print("TEST 4: Exception Disappears")
    run_test(test_4, "The Supplier must deliver the goods.")

def run_test(original, simplified):
    print(f"Original: {original}")
    print(f"Simplified: {simplified}")
    
    cat = predict_category(original)
    print(f"Predicted Category: {cat}")
    
    report = check_preservation(original, simplified)
    print(f"Risk Level: {report['risk_level']}")
    print(f"Reason: {report['reason']}")
    print("-" * 50)

if __name__ == "__main__":
    test_pipeline()
