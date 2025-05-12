#!/bin/bash
# filepath: /Users/mac/VulnAI/utils/test_model.sh

# Load environment variables
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo "Testing fine-tuned model: ft:gpt-4o-2024-08-06:personal::BWAukKEO"
echo "================================================="

# Test examples
examples=(
  "SQL Injection in Login Form"
  "Cross-Site Scripting (XSS) in Search Bar"
  "Buffer Overflow in File Upload Module"
  "CSRF (Cross-Site Request Forgery) in User Profile"
  "Misconfigured AWS S3 Bucket Permissions"
)

for example in "${examples[@]}"; do
  echo -e "\nExample: $example"
  echo "------------------------------------------------"
  
  # Call the OpenAI API using the CLI
  openai api chat_completions.create -m ft:gpt-4o-2024-08-06:personal::BWAukKEO \
    -g system "You are a cybersecurity expert analyzing vulnerabilities." \
    -g user "$example"
  
  echo "------------------------------------------------"
done

echo -e "\nTesting completed!"
