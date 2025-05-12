#!/usr/bin/env python3
# filepath: /Users/mac/VulnAI/utils/test_fine_tuned.py

import os
import sys
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client with API key
openai.api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key loaded: {'Yes' if openai.api_key else 'No'}")
print(f"OpenAI version: {openai.__version__}")

# Test examples - using just one for now to simplify testing
test_examples = [
    "SQL Injection in Login Form"
]

def test_fine_tuned_model():
    """Test the fine-tuned model with example prompts"""
    model_id = "ft:gpt-4o-2024-08-06:personal::BWAukKEO"
    print(f"Testing fine-tuned model: {model_id}\n")
    
    for example in test_examples:
        print(f"Example: {example}")
        print("-" * 80)
        
        try:
            print("Sending request to OpenAI API...")
            sys.stdout.flush()  # Force output to display immediately
            
            # Using openai library v0.28.0 format
            response = openai.ChatCompletion.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": "You are a cybersecurity expert analyzing vulnerabilities."},
                    {"role": "user", "content": example}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            print("Response received")
            print(f"Response object: {response}")
            sys.stdout.flush()
            
            result = response['choices'][0]['message']['content']
            print(f"Response:\n{result}\n")
            print("-" * 80)
            
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("Testing completed!")

# Run the test
if __name__ == "__main__":
    test_fine_tuned_model()
        
        try:
            print("Sending request to OpenAI API...")
            
            # Using openai library v0.28.0 format
            response = openai.ChatCompletion.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": "You are a cybersecurity expert analyzing vulnerabilities."},
                    {"role": "user", "content": example}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            print("Response received")
            result = response['choices'][0]['message']['content']
            print(f"Response:\n{result}\n")
            print("-" * 80)
            
        except Exception as e:
            print(f"Error: {str(e)}")
    
    print("Testing completed!")

# Run the test
if __name__ == "__main__":
    test_fine_tuned_model()
