#!/usr/bin/env python3

import os
import openai
from dotenv import load_dotenv
import sys

# Load environment variables
load_dotenv()

# Set OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")
openai.api_key = api_key

print(f"API Key available: {api_key is not None}")
print(f"API Key length: {len(api_key) if api_key else 'N/A'}")
print(f"OpenAI version: {openai.__version__}")
sys.stdout.flush()

try:
    # Simple call to OpenAI API to test connectivity
    response = openai.Completion.create(
        model="gpt-3.5-turbo-instruct",
        prompt="Say hello to the VulnLearnAI team",
        max_tokens=15
    )
    
    print("Response received:")
    print(response)
    print(f"Generated text: {response.choices[0].text.strip()}")
    
except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
