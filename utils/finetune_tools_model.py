#!/usr/bin/env python3
# filepath: /Users/mac/VulnAI/utils/finetune_tools_model.py
"""
This script uses the generated tool documentation training data to fine-tune
the existing GPT-4o model with additional tool knowledge.
"""

import os
import json
import sys
import argparse
import subprocess
from typing import Dict, List, Any
from datetime import datetime

# Add the app directory to the path so we can import from it
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
from utils.logger import log_info, log_error


class ToolModelFinetuner:
    def __init__(self, training_data_path: str, model_name: str, suffix: str):
        self.training_data_path = training_data_path
        self.base_model = model_name
        self.suffix = suffix
        
    def validate_training_data(self) -> bool:
        """Validate that the training data is in the correct format."""
        try:
            with open(self.training_data_path, "r") as f:
                # Count valid examples
                valid_examples = 0
                for line in f:
                    try:
                        data = json.loads(line)
                        if "messages" in data and len(data["messages"]) >= 3:
                            if all(msg.get("role") and msg.get("content") for msg in data["messages"]):
                                valid_examples += 1
                    except json.JSONDecodeError:
                        continue
                        
            log_info(f"Found {valid_examples} valid training examples")
            return valid_examples > 0
        except Exception as e:
            log_error(f"Failed to validate training data: {str(e)}")
            return False
            
    def _run_openai_cli_command(self, command: List[str]) -> Dict[str, Any]:
        """Run an OpenAI CLI command and return the parsed output."""
        try:
            result = subprocess.run(["openai"] + command, capture_output=True, text=True, check=True)
            if result.stdout:
                return json.loads(result.stdout)
            return {}
        except subprocess.CalledProcessError as e:
            log_error(f"OpenAI CLI command failed: {e.stderr}")
            return {"error": e.stderr}
        except Exception as e:
            log_error(f"Error running OpenAI CLI command: {str(e)}")
            return {"error": str(e)}
            
    def start_fine_tuning(self) -> str:
        """Start the fine-tuning process and return the job ID."""
        try:
            # Validate the training data first
            if not self.validate_training_data():
                log_error("Training data validation failed. Aborting fine-tuning.")
                return ""
                
            # Upload the training file
            log_info("Uploading training data to OpenAI...")
            upload_command = [
                "api", "files.create", 
                "--file", self.training_data_path,
                "--purpose", "fine-tune"
            ]
            
            upload_result = self._run_openai_cli_command(upload_command)
            
            if "error" in upload_result:
                log_error(f"Failed to upload training data: {upload_result['error']}")
                return ""
                
            file_id = upload_result.get("id", "")
            if not file_id:
                log_error("Failed to get file ID from upload response")
                return ""
                
            log_info(f"Training data uploaded. File ID: {file_id}")
            
            # Start fine-tuning job
            log_info(f"Starting fine-tuning job with base model {self.base_model}...")
            current_date = datetime.now().strftime("%Y%m%d")
            suffix = f"{self.suffix}-{current_date}"
            
            finetune_command = [
                "api", "fine_tuning.jobs.create",
                "--training_file", file_id,
                "--model", self.base_model,
                "--suffix", suffix
            ]
            
            finetune_result = self._run_openai_cli_command(finetune_command)
            
            if "error" in finetune_result:
                log_error(f"Failed to start fine-tuning: {finetune_result['error']}")
                return ""
                
            job_id = finetune_result.get("id", "")
            if job_id:
                log_info(f"Fine-tuning job started. Job ID: {job_id}")
            else:
                log_error("Failed to get job ID from fine-tuning response")
                
            return job_id
        except Exception as e:
            log_error(f"Error starting fine-tuning job: {str(e)}")
            return ""
            
    def run(self) -> str:
        """Run the fine-tuning process and return the job ID."""
        log_info("Starting tool model fine-tuning process...")
        
        job_id = self.start_fine_tuning()
        
        if job_id:
            log_info(f"Fine-tuning process initiated successfully. Job ID: {job_id}")
            log_info("Monitor progress using: openai api fine_tuning.jobs.get -i " + job_id)
        else:
            log_error("Fine-tuning process failed to start.")
            
        return job_id
        

def main():
    parser = argparse.ArgumentParser(description="Fine-tune a model with tool documentation")
    parser.add_argument("--training-data", type=str, default="data/tools_training_data.jsonl",
                        help="Path to the training data JSONL file")
    parser.add_argument("--model", type=str, default="gpt-4o",
                        help="Base model to use for fine-tuning")
    parser.add_argument("--suffix", type=str, default="tools-knowledge",
                        help="Suffix for the fine-tuned model name")
    
    args = parser.parse_args()
    
    finetuner = ToolModelFinetuner(args.training_data, args.model, args.suffix)
    finetuner.run()
    
    
if __name__ == "__main__":
    main()
