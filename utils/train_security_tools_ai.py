#!/usr/bin/env python3
# filepath: /Users/mac/VulnAI/utils/train_security_tools_ai.py
"""
Main script to train the AI module on security tools documentation.
This script coordinates:
1. Generating training data from tool documentation
2. Fine-tuning the model with the training data
3. Testing the fine-tuned model's understanding of the tools
"""

import os
import argparse
import sys
import json
from datetime import datetime
import time
import subprocess

# Add the app directory to the path so we can import from it
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
from utils.logger import log_info, log_error

# Import the other scripts
from train_tools_documentation import ToolDocumentationTrainer
from finetune_tools_model import ToolModelFinetuner
from test_tools_knowledge import ToolKnowledgeTester


def update_config_file(model_id: str) -> None:
    """Update the configuration file with the new model ID."""
    config_file = "config/domain_models.json"
    
    try:
        # Ensure the config directory exists
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        # Load existing config if available
        config = {}
        if os.path.exists(config_file):
            with open(config_file, "r") as f:
                config = json.load(f)
                
        # Update the tools model
        config["tools_model"] = model_id
        config["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Save the updated config
        with open(config_file, "w") as f:
            json.dump(config, f, indent=4)
            
        log_info(f"Updated config file with new model ID: {model_id}")
    except Exception as e:
        log_error(f"Failed to update config file: {str(e)}")


def wait_for_fine_tuning(job_id: str, check_interval: int = 300) -> str:
    """Wait for the fine-tuning job to complete and return the model ID."""
    if not job_id:
        log_error("No job ID provided. Cannot check status.")
        return ""
        
    log_info(f"Waiting for fine-tuning job {job_id} to complete. Checking every {check_interval} seconds.")
    
    while True:
        try:
            result = subprocess.run(
                ["openai", "api", "fine_tuning.jobs.get", "-i", job_id],
                capture_output=True, text=True, check=True
            )
            
            if result.stdout:
                job_data = json.loads(result.stdout)
                status = job_data.get("status", "")
                
                log_info(f"Job status: {status}")
                
                if status == "succeeded":
                    model_id = job_data.get("fine_tuned_model", "")
                    log_info(f"Fine-tuning completed successfully! Model ID: {model_id}")
                    return model_id
                elif status in ["failed", "cancelled"]:
                    log_error(f"Fine-tuning job failed or was cancelled.")
                    return ""
                    
            # Wait before checking again
            time.sleep(check_interval)
        except subprocess.CalledProcessError as e:
            log_error(f"Error checking job status: {e.stderr}")
            return ""
        except Exception as e:
            log_error(f"Unexpected error while checking job status: {str(e)}")
            return ""


def main():
    parser = argparse.ArgumentParser(description="Train the AI module on security tools documentation")
    parser.add_argument("--tools-metadata", type=str, default="tools/tools_metadata.json",
                        help="Path to the tools metadata JSON file")
    parser.add_argument("--training-data", type=str, default="data/tools_training_data.jsonl",
                        help="Path to save the training data JSONL file")
    parser.add_argument("--base-model", type=str, default="gpt-4o",
                        help="Base model to use for fine-tuning")
    parser.add_argument("--model-suffix", type=str, default="tools-knowledge",
                        help="Suffix for the fine-tuned model name")
    parser.add_argument("--wait-for-completion", action="store_true",
                        help="Wait for the fine-tuning job to complete")
    parser.add_argument("--check-interval", type=int, default=300,
                        help="Interval in seconds to check fine-tuning status")
    parser.add_argument("--test-model", action="store_true",
                        help="Test the model after fine-tuning")
    parser.add_argument("--existing-model", type=str, default="",
                        help="Use an existing model ID instead of fine-tuning a new one")
    parser.add_argument("--update-config", action="store_true",
                        help="Update the configuration file with the new model ID")
    
    args = parser.parse_args()
    
    log_info("Starting the security tools AI training process...")
    
    model_id = args.existing_model
    
    if not model_id:
        # Step 1: Generate training data
        log_info("Step 1: Generating training data from tool documentation...")
        trainer = ToolDocumentationTrainer(args.tools_metadata, args.training_data)
        trainer.run()
        
        # Step 2: Fine-tune the model
        log_info("Step 2: Fine-tuning the model with the generated training data...")
        finetuner = ToolModelFinetuner(args.training_data, args.base_model, args.model_suffix)
        job_id = finetuner.run()
        
        # Wait for fine-tuning to complete if requested
        if args.wait_for_completion and job_id:
            model_id = wait_for_fine_tuning(job_id, args.check_interval)
    else:
        log_info(f"Using existing model: {model_id}")
    
    # Step 3: Test the model if requested and available
    if args.test_model and model_id:
        log_info(f"Step 3: Testing the fine-tuned model {model_id}...")
        tester = ToolKnowledgeTester(model_id, args.tools_metadata)
        tester.run()
    elif args.test_model:
        log_info("Testing skipped because no model ID is available.")
        
    # Update the configuration file if requested
    if args.update_config and model_id:
        log_info("Updating configuration with the new model ID...")
        update_config_file(model_id)
        
    log_info("Security tools AI training process completed!")
    
    
if __name__ == "__main__":
    main()
