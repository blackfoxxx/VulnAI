#!/usr/bin/env python3
# filepath: /Users/mac/VulnAI/tests/test_text_extractor.py

import os
import tempfile
import unittest
import json
from unittest.mock import patch, mock_open
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.text_extractor import TextExtractor

class TestTextExtractor(unittest.TestCase):
    def setUp(self):
        self.extractor = TextExtractor()
        self.test_txt_content = "Test vulnerability description.\nSeverity: Critical\nImpact: High"
        
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a test txt file
        self.test_txt_path = os.path.join(self.temp_dir.name, "test_vuln.txt")
        with open(self.test_txt_path, "w", encoding="utf-8") as f:
            f.write(self.test_txt_content)
            
        # Path for output JSONL
        self.output_jsonl = os.path.join(self.temp_dir.name, "output.jsonl")
    
    def tearDown(self):
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_is_supported_file(self):
        # Test supported extensions
        self.assertTrue(self.extractor.is_supported_file("test.txt"))
        self.assertTrue(self.extractor.is_supported_file("test.pdf"))
        self.assertTrue(self.extractor.is_supported_file("test.docx"))
        
        # Test unsupported extensions
        self.assertFalse(self.extractor.is_supported_file("test.jpg"))
        self.assertFalse(self.extractor.is_supported_file("test.csv"))
    
    def test_extract_from_txt(self):
        # Test extracting text from TXT file
        text = self.extractor._extract_from_txt(self.test_txt_path)
        self.assertEqual(text, self.test_txt_content)
    
    @patch('PyPDF2.PdfReader')
    def test_extract_from_pdf(self, mock_pdf_reader):
        # Mock PdfReader
        mock_page = unittest.mock.MagicMock()
        mock_page.extract_text.return_value = "Test PDF content"
        mock_pdf_reader.return_value.pages = [mock_page]
        
        # Create a test file path
        test_pdf_path = "test.pdf"
        
        # Mock open function
        with patch("builtins.open", mock_open()) as mock_file:
            # Call the method
            text = self.extractor._extract_from_pdf(test_pdf_path)
            
            # Assert the result
            self.assertEqual(text, "Test PDF content\n")
            mock_file.assert_called_once_with(test_pdf_path, 'rb')
    
    @patch('docx.Document')
    def test_extract_from_docx(self, mock_document):
        # Mock Document class
        mock_para1 = unittest.mock.MagicMock()
        mock_para1.text = "Paragraph 1"
        mock_para2 = unittest.mock.MagicMock()
        mock_para2.text = "Paragraph 2"
        
        mock_document.return_value.paragraphs = [mock_para1, mock_para2]
        
        # Call the method
        text = self.extractor._extract_from_docx("test.docx")
        
        # Assert the result
        self.assertEqual(text, "Paragraph 1\nParagraph 2")
    
    def test_parse_vulnerability_from_text(self):
        # Test parsing vulnerability from text
        text = "Critical Vulnerability\nThis is a critical security issue.\nIt allows remote code execution."
        file_name = "test_vuln.txt"
        
        result = self.extractor.parse_vulnerability_from_text(text, file_name)
        
        # Assert the result has the expected keys and values
        self.assertEqual(result["title"], "Critical Vulnerability")
        self.assertEqual(result["description"], text)
        self.assertEqual(result["severity"], "Critical")
        self.assertEqual(result["source"], f"File: {file_name}")
        self.assertIn("timestamp", result)
    
    def test_extract_severity(self):
        # Test extracting severity
        self.assertEqual(self.extractor._extract_severity("This is a critical issue"), "Critical")
        self.assertEqual(self.extractor._extract_severity("High severity vulnerability"), "High")
        self.assertEqual(self.extractor._extract_severity("Medium risk issue"), "Medium")
        self.assertEqual(self.extractor._extract_severity("Low impact"), "Low")
        self.assertEqual(self.extractor._extract_severity("Unknown severity"), "Unknown")
    
    def test_process_file_to_jsonl(self):
        # Test processing a file to JSONL
        result = self.extractor.process_file_to_jsonl(self.test_txt_path, self.output_jsonl)
        
        # Assert the result is True (success)
        self.assertTrue(result)
        
        # Assert the output file exists and has content
        self.assertTrue(os.path.exists(self.output_jsonl))
        
        # Read the content of the output file
        with open(self.output_jsonl, "r", encoding="utf-8") as f:
            line = f.readline()
            data = json.loads(line)
            
            # Assert the content has the expected format
            self.assertIn("messages", data)
            self.assertEqual(len(data["messages"]), 3)
            self.assertEqual(data["messages"][0]["role"], "system")
            self.assertEqual(data["messages"][1]["role"], "user")
            self.assertEqual(data["messages"][2]["role"], "assistant")
            
            # Check if vulnerability title is in the user message
            user_content = data["messages"][1]["content"]
            self.assertIn("Title:", user_content)
            self.assertIn("Description:", user_content)
    
    def test_process_directory(self):
        # Create another test file
        test_txt_path2 = os.path.join(self.temp_dir.name, "test_vuln2.txt")
        with open(test_txt_path2, "w", encoding="utf-8") as f:
            f.write("Another test vulnerability.\nSeverity: High")
            
        # Test processing a directory
        count = self.extractor.process_directory(self.temp_dir.name, self.output_jsonl)
        
        # Assert two files were processed
        self.assertEqual(count, 2)
        
        # Check the output file content
        with open(self.output_jsonl, "r", encoding="utf-8") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 2)

if __name__ == "__main__":
    unittest.main()
