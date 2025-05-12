import asyncio
import unittest
from app.ml.training_engine import engine, VulnLearnAIEngine

async def test_classification():
    title = "SQL Injection in Login Form"
    description = ("A critical SQL injection vulnerability was discovered in the application's login form. "
                   "The username field is vulnerable to SQL injection attacks, allowing attackers to bypass authentication "
                   "and potentially extract sensitive data from the database.")
    cves = ["CVE-2023-12345"]

    result = await engine.classify_vulnerability(title, description, cves)
    print("Classification Result:")
    print(result)

class TestTrainingEngine(unittest.TestCase):
    def setUp(self):
        self.engine = VulnLearnAIEngine()

    def test_preprocess_data(self):
        entries = [
            {
                "title": "SQL Injection",
                "description": "Critical SQL injection vulnerability.",
                "cves": ["CVE-2023-12345"],
            },
            {
                "title": "XSS Attack",
                "description": "Cross-site scripting vulnerability.",
                "cves": [],
            },
        ]
        texts, labels = self.engine.preprocess_data(entries)
        self.assertEqual(len(texts), 2)
        self.assertEqual(len(labels), 2)
        self.assertEqual(labels[0], 1)  # High severity
        self.assertEqual(labels[1], 0)  # Low severity

    def test_train_model_no_data(self):
        # Mock the training data loading to simulate no data
        self.engine.load_training_data = lambda: []
        with self.assertRaises(ValueError):
            self.engine.train_model()

    def test_train_model_with_data(self):
        entries = [
            {
                "title": "SQL Injection",
                "description": "Critical SQL injection vulnerability.",
                "cves": ["CVE-2023-12345"],
            },
            {
                "title": "XSS Attack",
                "description": "Cross-site scripting vulnerability.",
                "cves": [],
            },
        ]
        # Mock the training data loading
        self.engine.load_training_data = lambda: entries
        result = self.engine.train_model()
        self.assertIn("validation_accuracy", result)
        self.assertGreaterEqual(result["validation_accuracy"], 0.0)
        self.assertLessEqual(result["validation_accuracy"], 1.0)

if __name__ == "__main__":
    asyncio.run(test_classification())
    unittest.main()
