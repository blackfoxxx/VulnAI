#!/usr/bin/env python3
# filepath: /Users/mac/VulnAI/tests/test_expand_training_data.py

import os
import tempfile
import unittest
import json
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.expand_training_data import TrainingDataExpander, VULNERABILITY_TEMPLATES, APPLICATIONS

class TestTrainingDataExpander(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Path for output JSONL
        self.output_jsonl = os.path.join(self.temp_dir.name, "output_training.jsonl")
        
        # Create the expander instance
        self.expander = TrainingDataExpander(self.output_jsonl)
        
        # Create a test JSONL file for augmentation
        self.input_jsonl = os.path.join(self.temp_dir.name, "input_training.jsonl")
        with open(self.input_jsonl, "w", encoding="utf-8") as f:
            example = {
                "messages": [
                    {"role": "system", "content": "You are a cybersecurity expert analyzing vulnerabilities."},
                    {"role": "user", "content": "Analyze this vulnerability:\nTitle: SQL Injection in Login Form\nDescription: The login form doesn't properly sanitize user inputs, allowing attackers to inject SQL queries."},
                    {"role": "assistant", "content": "Based on my analysis, this is a High severity vulnerability. To remediate SQL injection vulnerabilities, implement parameterized queries or prepared statements instead of dynamic SQL."}
                ]
            }
            f.write(json.dumps(example) + "\n")
    
    def tearDown(self):
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_generate_synthetic_examples(self):
        # Test generating synthetic examples
        examples = self.expander.generate_synthetic_examples(count=5)
        
        # Assert we got the expected number of examples
        self.assertEqual(len(examples), 5)
        
        # Check the structure of each example
        for example in examples:
            self.assertIn("messages", example)
            self.assertEqual(len(example["messages"]), 3)
            self.assertEqual(example["messages"][0]["role"], "system")
            self.assertEqual(example["messages"][1]["role"], "user")
            self.assertEqual(example["messages"][2]["role"], "assistant")
            
            # Check that the user message contains Title and Description
            user_content = example["messages"][1]["content"]
            self.assertIn("Title:", user_content)
            self.assertIn("Description:", user_content)
    
    def test_generate_from_template(self):
        # Test generating a vulnerability from a template
        template = VULNERABILITY_TEMPLATES[0]  # SQL Injection template
        application = APPLICATIONS[0]  # E-commerce Platform
        
        vuln = self.expander._generate_from_template(template, application)
        
        # Assert the result has the expected keys
        self.assertIn("title", vuln)
        self.assertIn("description", vuln)
        self.assertIn("severity", vuln)
        self.assertIn("source", vuln)
        self.assertIn("timestamp", vuln)
        
        # Assert the title and severity are as expected
        self.assertIn("SQL Injection", vuln["title"])
        self.assertIn(vuln["severity"], ["Critical", "High"])
        self.assertEqual(vuln["source"], "synthetic")
    
    def test_convert_to_training_format(self):
        # Create a test vulnerability
        vuln = {
            "title": "SQL Injection in E-commerce Platform",
            "description": "A SQL injection vulnerability was found in the login form of E-commerce Platform.",
            "severity": "Critical",
            "source": "synthetic",
            "timestamp": "2023-01-01T12:00:00"
        }
        
        # Convert to training format
        training_example = self.expander._convert_to_training_format(vuln)
        
        # Assert the result has the expected structure
        self.assertIn("messages", training_example)
        self.assertEqual(len(training_example["messages"]), 3)
        self.assertEqual(training_example["messages"][0]["role"], "system")
        self.assertEqual(training_example["messages"][1]["role"], "user")
        self.assertEqual(training_example["messages"][2]["role"], "assistant")
        
        # Check content
        user_content = training_example["messages"][1]["content"]
        self.assertIn(vuln["title"], user_content)
        self.assertIn(vuln["description"], user_content)
        
        assistant_content = training_example["messages"][2]["content"]
        self.assertIn(vuln["severity"], assistant_content)
    
    def test_generate_remediation_advice(self):
        # Test generating remediation advice for different vulnerabilities
        
        # SQL Injection
        vuln_sql = {"title": "SQL Injection in Login Form"}
        advice_sql = self.expander._generate_remediation_advice(vuln_sql)
        self.assertIn("parameterized queries", advice_sql)
        
        # XSS
        vuln_xss = {"title": "Cross-Site Scripting in Comments"}
        advice_xss = self.expander._generate_remediation_advice(vuln_xss)
        self.assertIn("Content Security Policy", advice_xss)
        
        # Authentication Bypass
        vuln_auth = {"title": "Authentication Bypass in Login System"}
        advice_auth = self.expander._generate_remediation_advice(vuln_auth)
        self.assertIn("multi-factor authentication", advice_auth)
        
        # Generic
        vuln_generic = {"title": "Unknown Vulnerability"}
        advice_generic = self.expander._generate_remediation_advice(vuln_generic)
        self.assertIn("security best practices", advice_generic)
    
    def test_save_to_jsonl(self):
        # Generate examples
        examples = self.expander.generate_synthetic_examples(count=3)
        
        # Save to JSONL
        self.expander.save_to_jsonl(examples)
        
        # Assert the file exists
        self.assertTrue(os.path.exists(self.output_jsonl))
        
        # Read the file and check its content
        with open(self.output_jsonl, "r", encoding="utf-8") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 3)
            
            # Parse each line as JSON
            for line in lines:
                data = json.loads(line)
                self.assertIn("messages", data)
    
    def test_load_existing_jsonl(self):
        # Load existing examples
        examples = self.expander.load_existing_jsonl(self.input_jsonl)
        
        # Assert we loaded one example
        self.assertEqual(len(examples), 1)
        
        # Check the content
        example = examples[0]
        self.assertIn("messages", example)
        self.assertEqual(len(example["messages"]), 3)
        user_content = example["messages"][1]["content"]
        self.assertIn("SQL Injection in Login Form", user_content)
    
    def test_augment_existing_examples(self):
        # Load existing examples
        examples = self.expander.load_existing_jsonl(self.input_jsonl)
        
        # Augment examples
        augmented = self.expander.augment_existing_examples(examples, augmentation_factor=3)
        
        # Assert we got 3 augmented examples (1 original * 3 factor)
        self.assertEqual(len(augmented), 3)
        
        # Check that each augmented example has the expected structure
        for example in augmented:
            self.assertIn("messages", example)
            self.assertEqual(len(example["messages"]), 3)
            
            # Check that the content includes SQL Injection (from the original)
            user_content = example["messages"][1]["content"]
            self.assertIn("SQL Injection", user_content)
    
    def test_create_title_variation(self):
        # Test creating title variations
        original_title = "SQL Injection in Login Form"
        variation = self.expander._create_title_variation(original_title)
        
        # Assert the variation contains the original content
        self.assertIn("SQL Injection", variation)
    
    def test_create_description_variation(self):
        # Test creating description variations
        original_desc = "This is a critical vulnerability. It allows attackers to inject SQL queries."
        variation = self.expander._create_description_variation(original_desc)
        
        # Assert the variation has content
        self.assertTrue(variation)
        
        # Should contain key phrases from the original
        self.assertIn("vulnerability", variation)
        self.assertIn("sql", variation.lower())

if __name__ == "__main__":
    unittest.main()
