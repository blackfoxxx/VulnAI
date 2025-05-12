#!/bin/bash
# filepath: /Users/mac/VulnAI/utils/train_tools_pipeline.sh

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

# Configuration
BASE_MODEL="gpt-4o"
TOOLS_METADATA="tools/tools_metadata.json"
TRAINING_DATA="data/tools_training_data.jsonl"
METRICS_DIR="data/metrics"
REPORT_FILE="data/metrics/training_report.md"

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}= VulnLearnAI Security Tools Training and Comparison =${NC}"
echo -e "${BLUE}======================================================${NC}"

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd $SCRIPT_DIR/..

# Create necessary directories
mkdir -p data/metrics

# Ensure we have the OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}Error: OPENAI_API_KEY environment variable is not set.${NC}"
    echo "Please set it using: export OPENAI_API_KEY=your_api_key"
    exit 1
fi

# 1. Test the current model's knowledge
echo -e "${GREEN}Step 1: Testing current model's knowledge of security tools...${NC}"
python utils/test_current_tool_knowledge.py --model $BASE_MODEL --tools-metadata $TOOLS_METADATA
echo "Baseline testing complete!"
echo ""

# 2. Generate training data
echo -e "${GREEN}Step 2: Generating training data from tool documentation...${NC}"
python utils/train_tools_documentation.py --output $TRAINING_DATA
echo "Training data generation complete!"
echo "Created training data at $TRAINING_DATA"
echo ""

# 3. Fine-tune a new model
echo -e "${GREEN}Step 3: Fine-tuning a new model with the training data...${NC}"
echo "Would you like to proceed with model fine-tuning? This will incur OpenAI API costs. (y/n)"
read -p "Proceed with fine-tuning? " choice
if [[ "$choice" =~ ^[Yy]$ ]]; then
    FINETUNED_MODEL=$(python utils/finetune_tools_model.py --training-data $TRAINING_DATA)
    if [ -z "$FINETUNED_MODEL" ]; then
        echo -e "${RED}Error: Fine-tuning failed or model ID was not returned.${NC}"
        exit 1
    fi
    echo "Model fine-tuning complete!"
    echo "New model ID: $FINETUNED_MODEL"
    
    # 4. Test the fine-tuned model
    echo -e "${GREEN}Step 4: Testing fine-tuned model knowledge...${NC}"
    python utils/test_current_tool_knowledge.py --model $FINETUNED_MODEL --tools-metadata $TOOLS_METADATA
    echo "Fine-tuned model testing complete!"
    echo ""

    # 5. Compare models and generate visualization
    echo -e "${GREEN}Step 5: Comparing models and generating report...${NC}"
    python utils/track_training_metrics.py --base-model $BASE_MODEL --finetuned-model $FINETUNED_MODEL --output "$METRICS_DIR/model_comparison.png"
    echo "Comparison complete!"
    echo ""

    # Generate a markdown report
    echo "## VulnLearnAI Security Tools Training Report" > $REPORT_FILE
    echo "**Date:** $(date)" >> $REPORT_FILE
    echo "" >> $REPORT_FILE
    echo "### Models Compared" >> $REPORT_FILE
    echo "- Base Model: $BASE_MODEL" >> $REPORT_FILE
    echo "- Fine-tuned Model: $FINETUNED_MODEL" >> $REPORT_FILE
    echo "" >> $REPORT_FILE
    echo "### Training Summary" >> $REPORT_FILE
    echo "- Number of training examples: $(wc -l < $TRAINING_DATA)" >> $REPORT_FILE
    echo "- Tools covered: katana, naabu, gau, nuclei, nmap" >> $REPORT_FILE
    echo "" >> $REPORT_FILE
    echo "### Results" >> $REPORT_FILE
    echo "![Model Comparison](model_comparison.png)" >> $REPORT_FILE
    echo "" >> $REPORT_FILE
    echo "### Next Steps" >> $REPORT_FILE
    echo "1. Update the domain_models.json configuration to use the new fine-tuned model" >> $REPORT_FILE
    echo "2. Test the model's performance in real-world scenarios" >> $REPORT_FILE
    echo "3. Consider expanding the training to include additional tools" >> $REPORT_FILE

    echo -e "${BLUE}======================================================${NC}"
    echo -e "${BLUE}=               Training Process Completed            =${NC}"
    echo -e "${BLUE}======================================================${NC}"
    echo ""
    echo "Report generated at $REPORT_FILE"
    echo ""
    echo "To update the application to use the new model, run:"
    echo "python utils/train_security_tools_ai.py --existing-model $FINETUNED_MODEL --update-config"
else
    echo "Fine-tuning skipped. You can run it later with:"
    echo "python utils/finetune_tools_model.py --training-data $TRAINING_DATA"
    echo ""
    echo -e "${BLUE}======================================================${NC}"
    echo -e "${BLUE}=               Partial Process Completed             =${NC}"
    echo -e "${BLUE}======================================================${NC}"
    echo ""
    echo "The training data has been generated and the baseline model has been tested."
    echo "When you're ready to continue, run this script again and choose to proceed with fine-tuning."
fi
