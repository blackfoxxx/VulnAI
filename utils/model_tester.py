#!/usr/bin/env python3
# filepath: /Users/mac/VulnAI/utils/model_tester.py

import os
import openai
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize OpenAI client with API key
openai.api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key loaded: {'Yes' if openai.api_key else 'No'}")
print(f"OpenAI version: {openai.__version__}")
sys.stdout.flush()

# Test examples
test_examples = [
    "SQL Injection in Login Form",
    "Cross-Site Scripting (XSS) in Search Bar", 
    "Buffer Overflow in File Upload Module",
    "CSRF (Cross-Site Request Forgery) in User Profile",
    "Misconfigured AWS S3 Bucket Permissions"
]

def test_fine_tuned_model():
    """Test the fine-tuned model with example prompts"""
    model_id = "ft:gpt-4o-2024-08-06:personal::BWAukKEO"
    print(f"Testing fine-tuned model: {model_id}\n")
    sys.stdout.flush()
    
    for example in test_examples:
        print(f"Example: {example}")
        print("-" * 80)
        sys.stdout.flush()
        
        try:
            print("Sending request to OpenAI API...")
            sys.stdout.flush()
            
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
            sys.stdout.flush()
            
            if 'choices' in response and len(response['choices']) > 0:
                if 'message' in response['choices'][0] and 'content' in response['choices'][0]['message']:
                    result = response['choices'][0]['message']['content']
                    print(f"Response:\n{result}\n")
                else:
                    print("Error: Unexpected response format - 'message' or 'content' field missing")
            else:
                print("Error: Unexpected response format - 'choices' field missing or empty")
            
            print("-" * 80)
            sys.stdout.flush()
            
        except Exception as e:
            print(f"Error: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
    
    print("Testing completed!")
    sys.stdout.flush()

# Run the test
if __name__ == "__main__":
    test_fine_tuned_model()
