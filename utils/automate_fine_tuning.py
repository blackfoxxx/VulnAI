import os
import openai
import asyncio
import argparse
import json
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get API key from environment variable
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

openai.api_key = api_key

# Default file path to the prepared JSONL file
DEFAULT_TRAINING_FILE_PATH = "data/extended_messages.jsonl"

async def validate_jsonl_file(file_path):
    """Validates that the JSONL file is properly formatted."""
    logger.info(f"Validating JSONL file: {file_path}")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Training file not found: {file_path}")
    
    with open(file_path, "r", encoding="utf-8") as file:
        line_num = 0
        for line in file:
            line_num += 1
            try:
                # Parse JSON
                data = json.loads(line)
                
                # Check if it follows the message format
                if "messages" not in data:
                    logger.error(f"Line {line_num}: Missing 'messages' key")
                    return False
                
                messages = data["messages"]
                if not isinstance(messages, list) or len(messages) < 2:
                    logger.error(f"Line {line_num}: 'messages' should be a list with at least 2 messages")
                    return False
                
                # Check each message
                for msg in messages:
                    if "role" not in msg or "content" not in msg:
                        logger.error(f"Line {line_num}: Message missing 'role' or 'content'")
                        return False
                    
                    if msg["role"] not in ["system", "user", "assistant"]:
                        logger.error(f"Line {line_num}: Invalid role: {msg['role']}")
                        return False
            
            except json.JSONDecodeError:
                logger.error(f"Line {line_num}: Invalid JSON")
                return False
    
    logger.info(f"JSONL file validated successfully: {file_path}")
    return True

async def upload_training_file(file_path):
    """Uploads the training file to OpenAI and returns the file ID."""
    logger.info("Uploading training file...")
    
    # Validate the file before uploading
    if not await validate_jsonl_file(file_path):
        raise ValueError("Training file validation failed. Please check the format.")
    
    try:
        with open(file_path, "rb") as file:  # Use a synchronous context manager
            response = await openai.File.acreate(
                file=file,
                purpose="fine-tune"
            )
        file_id = response["id"]
        logger.info(f"File uploaded successfully. File ID: {file_id}")
        return file_id
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise

async def create_fine_tune_job(file_id, model="gpt-4o-2024-08-06", n_epochs=None, batch_size=None, learning_rate_multiplier=None):
    """Creates a fine-tuning job using the uploaded file ID."""
    logger.info("Creating fine-tuning job...")
    
    # Prepare parameters
    params = {
        "training_file": file_id,
        "model": model
    }
    
    # Add optional parameters if provided
    if n_epochs is not None:
        params["n_epochs"] = n_epochs
    if batch_size is not None:
        params["batch_size"] = batch_size
    if learning_rate_multiplier is not None:
        params["learning_rate_multiplier"] = learning_rate_multiplier
    
    try:
        response = await openai.FineTuningJob.acreate(**params)
        job_id = response["id"]
        logger.info(f"Fine-tuning job created successfully. Job ID: {job_id}")
        return job_id
    except Exception as e:
        logger.error(f"Error creating fine-tuning job: {str(e)}")
        raise

async def monitor_fine_tune_job(job_id):
    """Monitors the fine-tuning job until it is complete."""
    logger.info("Monitoring fine-tuning job...")
    try:
        while True:
            response = await openai.FineTuningJob.aretrieve(id=job_id)
            status = response["status"]
            logger.info(f"Job status: {status}")
            
            # If we have training_metrics, log them
            if "training_metrics" in response and response["training_metrics"]:
                metrics = response["training_metrics"]
                logger.info(f"Training loss: {metrics.get('training_loss', 'N/A')}")
                logger.info(f"Training accuracy: {metrics.get('training_accuracy', 'N/A')}")
            
            if status in ["succeeded", "failed", "cancelled"]:
                break
            
            await asyncio.sleep(30)  # Wait for 30 seconds before checking again

        if status == "succeeded":
            logger.info("Fine-tuning job completed successfully!")
            logger.info(f"Fine-tuned model ID: {response['fine_tuned_model']}")
            
            # Save model info to a file for future reference
            model_info = {
                "job_id": job_id,
                "model_id": response['fine_tuned_model'],
                "base_model": response.get('model', 'unknown'),
                "created_at": response.get('created_at', 'unknown'),
                "finished_at": response.get('finished_at', 'unknown'),
                "training_file": response.get('training_file', 'unknown'),
                "validation_file": response.get('validation_file', 'unknown')
            }
            
            os.makedirs("data/model-info", exist_ok=True)
            with open(f"data/model-info/model_{job_id}.json", "w") as f:
                json.dump(model_info, f, indent=2)
            
            return response['fine_tuned_model']
        else:
            logger.error("Fine-tuning job failed.")
            if 'error' in response:
                logger.error(f"Error: {response['error']}")
            return None
    except Exception as e:
        logger.error(f"Error monitoring fine-tuning job: {str(e)}")
        raise

async def prepare_training_data(input_files=None, text_dirs=None, output_file=None):
    """
    Prepare and consolidate training data from various sources.
    
    Args:
        input_files: List of JSONL files to include
        text_dirs: List of directories containing text files to process
        output_file: Path to save the consolidated training data
    
    Returns:
        Path to the prepared training file
    """
    if output_file is None:
        # Generate a timestamped output file
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        output_file = f"data/training_data_{timestamp}.jsonl"
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Create an empty output file
    with open(output_file, "w") as f:
        pass
    
    # Process JSONL files
    if input_files:
        for file in input_files:
            if os.path.exists(file) and file.endswith('.jsonl'):
                logger.info(f"Processing input file: {file}")
                # Load and validate the file
                if await validate_jsonl_file(file):
                    # Append the file content to the output file
                    with open(file, "r") as src, open(output_file, "a") as dst:
                        dst.write(src.read())
                    logger.info(f"Added content from {file} to {output_file}")
                else:
                    logger.warning(f"Skipping invalid file: {file}")
    
    # Process text directories
    if text_dirs:
        from utils.text_extractor import TextExtractor
        extractor = TextExtractor()
        
        for directory in text_dirs:
            if os.path.isdir(directory):
                logger.info(f"Processing text files from directory: {directory}")
                processed = extractor.process_directory(directory, output_file)
                logger.info(f"Processed {processed} files from {directory}")
    
    # Validate the final output file
    if not await validate_jsonl_file(output_file):
        logger.error(f"Final output file is invalid: {output_file}")
        raise ValueError("Generated training file is invalid")
    
    return output_file

async def update_ai_integration(model_id):
    """Update the AI integration module to use the new model."""
    integration_file = "app/ml/ai_integration.py"
    
    if not os.path.exists(integration_file):
        logger.error(f"Integration file not found: {integration_file}")
        return False
    
    logger.info(f"Updating AI integration to use model: {model_id}")
    
    try:
        # Read the file
        with open(integration_file, "r") as file:
            content = file.read()
        
        # Replace the model ID - look for model="..." patterns in _analyze_with_openai method
        import re
        pattern = r'(model=")([^"]+)(".*# Use the fine-tuned model)'
        updated_content = re.sub(pattern, f'\\1{model_id}\\3', content)
        
        # Write the updated content
        with open(integration_file, "w") as file:
            file.write(updated_content)
        
        logger.info(f"Successfully updated {integration_file} to use model {model_id}")
        return True
    
    except Exception as e:
        logger.error(f"Error updating AI integration: {str(e)}")
        return False

async def main(args=None):
    """Main function to orchestrate the fine-tuning process."""
    if args is None:
        # For backward compatibility, use default values
        training_file_path = DEFAULT_TRAINING_FILE_PATH
        file_id = await upload_training_file(training_file_path)
        job_id = await create_fine_tune_job(file_id)
        await monitor_fine_tune_job(job_id)
        return
        
    try:
        # Prepare training data if sources are provided
        if args.input_files or args.text_dirs:
            training_file_path = await prepare_training_data(
                input_files=args.input_files,
                text_dirs=args.text_dirs,
                output_file=args.output_file
            )
        else:
            training_file_path = args.training_file
        
        logger.info(f"Using training file: {training_file_path}")
        
        # Upload the training file
        file_id = await upload_training_file(training_file_path)
        
        # Create the fine-tuning job
        job_id = await create_fine_tune_job(
            file_id=file_id,
            model=args.model,
            n_epochs=args.n_epochs,
            batch_size=args.batch_size,
            learning_rate_multiplier=args.learning_rate_multiplier
        )
        
        # Monitor the job
        model_id = await monitor_fine_tune_job(job_id)
        
        if model_id:
            logger.info(f"Fine-tuning process completed successfully. Model ID: {model_id}")
            
            # Update the AI integration to use the new model
            if args.update_integration:
                await update_ai_integration(model_id)
            
            return model_id
        else:
            logger.error("Fine-tuning process failed")
            return None
    
    except Exception as e:
        logger.error(f"Error in fine-tuning process: {str(e)}")
        raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Automate fine-tuning process for VulnLearnAI.')
    
    # Input data sources
    parser.add_argument('--training-file', default=DEFAULT_TRAINING_FILE_PATH, help='Path to the main training JSONL file')
    parser.add_argument('--input-files', nargs='+', help='Additional JSONL files to include in training')
    parser.add_argument('--text-dirs', nargs='+', help='Directories containing text files to process')
    parser.add_argument('--output-file', help='Path to save the consolidated training data')
    
    # Fine-tuning parameters
    parser.add_argument('--model', default="gpt-4o-2024-08-06", help='Base model to fine-tune')
    parser.add_argument('--n-epochs', type=int, help='Number of epochs')
    parser.add_argument('--batch-size', type=int, help='Batch size')
    parser.add_argument('--learning-rate-multiplier', type=float, help='Learning rate multiplier')
    
    # Additional options
    parser.add_argument('--update-integration', action='store_true', help='Update AI integration with the new model')
    
    args = parser.parse_args()
    
    # Run the async main function
    asyncio.run(main(args))
