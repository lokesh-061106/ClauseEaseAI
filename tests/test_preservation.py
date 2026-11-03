import sys
import os
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.preservation_checker import check_preservation

class TestPreservationChecker(unittest.TestCase):
    
    def test_shall_to_must(self):
        orig = "The Supplier shall deliver the goods."
        simp = "The Supplier must deliver the goods."
        res = check_preservation(orig, simp)
        self.assertIn(res['risk_level'], ["LOW", "PRESERVED"])
        
    def test_shall_to_may(self):
        orig = "The Supplier shall deliver the goods."
        simp = "The Supplier may deliver the goods."
        res = check_preservation(orig, simp)
        self.assertEqual(res['risk_level'], "HIGH")
        
    def test_shall_not_to_may(self):
        orig = "The Supplier shall not deliver the goods."
        simp = "The Supplier may deliver the goods."
        res = check_preservation(orig, simp)
        # Assuming the rule engine flags modality shift or ML drops entailment
        # We need to make sure the rule engine catches 'shall not'.
        # Since our basic information extractor might just see 'shall' and 'may',
        # let's trust the integration or ML.
        self.assertIn(res['risk_level'], ["MEDIUM", "HIGH"])
        
    def test_number_change_days(self):
        orig = "Payment within 15 days."
        simp = "Payment within 30 days."
        res = check_preservation(orig, simp)
        self.assertEqual(res['risk_level'], "HIGH")
        
    def test_number_change_currency(self):
        orig = "The penalty is ₹50,000."
        simp = "The penalty is ₹60,000."
        res = check_preservation(orig, simp)
        self.assertEqual(res['risk_level'], "HIGH")
        
    def test_actor_change(self):
        orig = "The supplier shall pay the tax."
        simp = "The customer must pay the tax."
        res = check_preservation(orig, simp)
        self.assertEqual(res['risk_level'], "HIGH")
        
    def test_condition_removed(self):
        orig = "Supplier shall deliver the goods, provided that payment is received."
        simp = "Supplier must deliver the goods."
        # ML model should flag this as a potential contradiction or information loss
        res = check_preservation(orig, simp)
        self.assertIn(res['risk_level'], ["MEDIUM", "HIGH"])
        
    def test_exception_removed(self):
        orig = "The Tenant shall pay rent, unless the building is destroyed."
        simp = "The Tenant must pay rent."
        res = check_preservation(orig, simp)
        self.assertIn(res['risk_level'], ["MEDIUM", "HIGH"])
        
    def test_harmless_synonym(self):
        orig = "The automobile shall be parked outside."
        simp = "The car must be parked outside."
        res = check_preservation(orig, simp)
        self.assertIn(res['risk_level'], ["LOW", "PRESERVED"])
        
    def test_identical_sentence(self):
        orig = "The Supplier shall deliver the goods."
        simp = "The Supplier shall deliver the goods."
        res = check_preservation(orig, simp)
        self.assertEqual(res['risk_level'], "PRESERVED")
        self.assertGreater(res['similarity'], 0.95)

if __name__ == "__main__":
    unittest.main()
