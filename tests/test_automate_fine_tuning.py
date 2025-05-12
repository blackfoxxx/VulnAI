#!/usr/bin/env python3
# filepath: /Users/mac/VulnAI/tests/test_automate_fine_tuning.py

import os
import tempfile
import json
import asyncio
import unittest
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the module to test
from utils.automate_fine_tuning import validate_jsonl_file, upload_training_file, create_fine_tune_job, monitor_fine_tune_job, prepare_training_data, update_ai_integration

class TestAutomateFineTuning(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create a valid JSONL file for testing
        self.valid_jsonl_path = os.path.join(self.temp_dir.name, "valid.jsonl")
        with open(self.valid_jsonl_path, "w", encoding="utf-8") as f:
            valid_entry = {
                "messages": [
                    {"role": "system", "content": "You are a cybersecurity expert analyzing vulnerabilities."},
                    {"role": "user", "content": "Analyze this vulnerability:\nTitle: SQL Injection\nDescription: Test description"},
                    {"role": "assistant", "content": "Based on my analysis, this is a High severity vulnerability."}
                ]
            }
            f.write(json.dumps(valid_entry) + "\n")
        
        # Create an invalid JSONL file (missing role)
        self.invalid_jsonl_path = os.path.join(self.temp_dir.name, "invalid.jsonl")
        with open(self.invalid_jsonl_path, "w", encoding="utf-8") as f:
            invalid_entry = {
                "messages": [
                    {"role": "system", "content": "You are a cybersecurity expert analyzing vulnerabilities."},
                    {"content": "Missing role field"},
                    {"role": "assistant", "content": "Based on my analysis, this is a High severity vulnerability."}
                ]
            }
            f.write(json.dumps(invalid_entry) + "\n")
        
        # Create a non-JSON file
        self.non_json_path = os.path.join(self.temp_dir.name, "non_json.txt")
        with open(self.non_json_path, "w", encoding="utf-8") as f:
            f.write("This is not a JSON file.")
        
        # Create a mock AI integration file
        self.integration_file = os.path.join(self.temp_dir.name, "ai_integration.py")
        with open(self.integration_file, "w", encoding="utf-8") as f:
            f.write('model="old-model-id"  # Use the fine-tuned model')
    
    def tearDown(self):
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    @pytest.mark.asyncio
    async def test_validate_jsonl_file_valid(self):
        # Test validating a valid JSONL file
        result = await validate_jsonl_file(self.valid_jsonl_path)
        self.assertTrue(result)
    
    @pytest.mark.asyncio
    async def test_validate_jsonl_file_invalid(self):
        # Test validating an invalid JSONL file
        result = await validate_jsonl_file(self.invalid_jsonl_path)
        self.assertFalse(result)
    
    @pytest.mark.asyncio
    async def test_validate_jsonl_file_non_json(self):
        # Test validating a non-JSON file
        result = await validate_jsonl_file(self.non_json_path)
        self.assertFalse(result)
    
    @pytest.mark.asyncio
    async def test_validate_jsonl_file_not_found(self):
        # Test validating a file that doesn't exist
        with self.assertRaises(FileNotFoundError):
            await validate_jsonl_file("nonexistent_file.jsonl")
    
    @pytest.mark.asyncio
    @patch('utils.automate_fine_tuning.validate_jsonl_file', return_value=True)
    @patch('openai.File.acreate')
    async def test_upload_training_file(self, mock_acreate, mock_validate):
        # Mock the openai.File.acreate response
        mock_response = {"id": "file-123456"}
        mock_acreate.return_value = mock_response
        
        # Call the function
        file_id = await upload_training_file(self.valid_jsonl_path)
        
        # Assert the result
        self.assertEqual(file_id, "file-123456")
        
        # Verify the function was called with the right parameters
        mock_validate.assert_called_once_with(self.valid_jsonl_path)
        mock_acreate.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('openai.FineTuningJob.acreate')
    async def test_create_fine_tune_job(self, mock_acreate):
        # Mock the openai.FineTuningJob.acreate response
        mock_response = {"id": "job-123456"}
        mock_acreate.return_value = mock_response
        
        # Call the function
        job_id = await create_fine_tune_job("file-123456", model="gpt-4o-2024-08-06")
        
        # Assert the result
        self.assertEqual(job_id, "job-123456")
        
        # Verify the function was called with the right parameters
        mock_acreate.assert_called_once_with(
            training_file="file-123456",
            model="gpt-4o-2024-08-06"
        )
    
    @pytest.mark.asyncio
    @patch('openai.FineTuningJob.aretrieve')
    @patch('asyncio.sleep')
    async def test_monitor_fine_tune_job_success(self, mock_sleep, mock_aretrieve):
        # Mock the openai.FineTuningJob.aretrieve responses
        mock_responses = [
            {"status": "queued"},
            {"status": "running", "training_metrics": {"training_loss": 0.5}},
            {"status": "succeeded", "fine_tuned_model": "model-123456"}
        ]
        mock_aretrieve.side_effect = mock_responses
        
        # Patch the open function for writing model info
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            # Call the function
            model_id = await monitor_fine_tune_job("job-123456")
            
            # Assert the result
            self.assertEqual(model_id, "model-123456")
            
            # Verify the function called aretrieve the right number of times
            self.assertEqual(mock_aretrieve.call_count, 3)
            
            # Verify sleep was called
            self.assertEqual(mock_sleep.call_count, 2)
    
    @pytest.mark.asyncio
    @patch('utils.automate_fine_tuning.validate_jsonl_file', return_value=True)
    @patch('utils.text_extractor.TextExtractor')
    async def test_prepare_training_data(self, mock_text_extractor, mock_validate):
        # Mock the TextExtractor
        mock_extractor_instance = MagicMock()
        mock_extractor_instance.process_directory.return_value = 2
        mock_text_extractor.return_value = mock_extractor_instance
        
        # Create test files and directories
        input_file = os.path.join(self.temp_dir.name, "input.jsonl")
        with open(input_file, "w") as f:
            f.write("{}\n")
        
        text_dir = os.path.join(self.temp_dir.name, "text_files")
        os.makedirs(text_dir, exist_ok=True)
        
        output_file = os.path.join(self.temp_dir.name, "output.jsonl")
        
        # Call the function
        result = await prepare_training_data(
            input_files=[input_file],
            text_dirs=[text_dir],
            output_file=output_file
        )
        
        # Assert the result
        self.assertEqual(result, output_file)
        
        # Verify the validate function was called
        mock_validate.assert_called()
        
        # Verify TextExtractor.process_directory was called
        mock_extractor_instance.process_directory.assert_called_with(text_dir, output_file)
    
    @pytest.mark.asyncio
    async def test_update_ai_integration(self):
        # Patch the open function
        with patch('builtins.open', unittest.mock.mock_open(read_data='model="old-model-id"  # Use the fine-tuned model')) as mock_file:
            # Call the function
            result = await update_ai_integration("new-model-id")
            
            # Assert the result
            self.assertTrue(result)
            
            # Verify the open function was called
            self.assertEqual(mock_file.call_count, 2)  # Once for read and once for write
            
            # Get the written content
            written_content = ''.join([call.args[0] for call in mock_file().write.call_args_list])
            self.assertIn('model="new-model-id"', written_content)

if __name__ == "__main__":
    pytest.main(["-v", "test_automate_fine_tuning.py"])
