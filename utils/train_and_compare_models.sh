#!/bin/bash
# filepath: /Users/mac/VulnAI/utils/train_and_compare_models.sh

# This script performs a full training and comparison cycle:
# 1. Tests the current model's knowledge of security tools
# 2. Generates training data from tool documentation
# 3. Fine-tunes a new model with the training data
# 4. Tests the fine-tuned model's knowledge
# 5. Compares the results of the two models

# Set environment variables
export PATH=$PATH:$HOME/.local/bin:/usr/local/bin

# Set colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}= VulnLearnAI Security Tools Training and Comparison =${NC}"
echo -e "${BLUE}======================================================${NC}"

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd $SCRIPT_DIR/..

# Create necessary directories
mkdir -p data

# Ensure we have the OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}Error: OPENAI_API_KEY environment variable is not set.${NC}"
    echo "Please set it using: export OPENAI_API_KEY=your_api_key"
    exit 1
fi

# 1. Test the current model's knowledge
echo -e "${GREEN}Step 1: Testing current model's knowledge of security tools...${NC}"
python utils/test_current_tool_knowledge.py --model gpt-4o

# 2. Generate training data
echo -e "${GREEN}Step 2: Generating training data from tool documentation...${NC}"
python utils/train_tools_documentation.py

# 3. Fine-tune a new model (this step is commented out as it requires OpenAI credits)
echo -e "${GREEN}Step 3: Fine-tuning a new model with the training data...${NC}"
echo "Note: This step is commented out in the script because it requires OpenAI credits."
echo "To actually run the fine-tuning, uncomment the following line in the script:"
echo "python utils/finetune_tools_model.py --training-data data/tools_training_data.jsonl --model gpt-4o --suffix tools-knowledge"

# Uncomment to actually run the fine-tuning
# python utils/finetune_tools_model.py --training-data data/tools_training_data.jsonl --model gpt-4o --suffix tools-knowledge

# 4. Test the fine-tuned model (assuming we have one)
echo -e "${GREEN}Step 4: When you have a fine-tuned model, test it with:${NC}"
echo "python utils/test_tools_knowledge.py --model your_finetuned_model_id --tools-metadata tools/tools_metadata.json"

# 5. Update the configuration
echo -e "${GREEN}Step 5: When ready, update the configuration file with:${NC}"
echo "python utils/train_security_tools_ai.py --existing-model your_finetuned_model_id --update-config"

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}=               Training Process Completed            =${NC}"
echo -e "${BLUE}======================================================${NC}"
echo ""
echo "The training data has been generated and is ready for fine-tuning."
echo "To complete the process, follow the instructions above for steps 3, 4, and 5."
