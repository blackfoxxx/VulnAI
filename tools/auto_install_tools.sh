#!/bin/bash
# filepath: /Users/mac/VulnAI/tools/auto_install_tools.sh

# This script detects and installs security tools based on their programming language
# It's a wrapper around the auto_tool_manager.py utility

# Set colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd $SCRIPT_DIR/..

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed. Please install Python 3 to use this script.${NC}"
    exit 1
fi

# Ensure auto_tool_manager.py exists
if [ ! -f "utils/auto_tool_manager.py" ]; then
    echo -e "${RED}Error: utils/auto_tool_manager.py not found.${NC}"
    exit 1
fi

# Make sure auto_tool_manager.py is executable
chmod +x utils/auto_tool_manager.py

# Function to display help
show_help() {
    echo -e "${BLUE}VulnLearnAI Auto Tool Installer${NC}"
    echo ""
    echo "This script automates the installation of security tools based on their programming language."
    echo ""
    echo "Usage:"
    echo "  ./auto_install_tools.sh [command] [options]"
    echo ""
    echo "Commands:"
    echo "  add <tool_id> <repo_url>  - Add a new security tool"
    echo "  update <tool_id>          - Update an existing security tool"
    echo "  remove <tool_id>          - Remove a security tool"
    echo "  list                     - List all security tools"
    echo ""
    echo "Options:"
    echo "  --no-install              - Don't install the tool (for add and update commands)"
    echo "  --no-training             - Don't update training data (for add and update commands)"
    echo ""
    echo "Examples:"
    echo "  ./auto_install_tools.sh add nuclei https://github.com/projectdiscovery/nuclei.git"
    echo "  ./auto_install_tools.sh update nuclei"
    echo "  ./auto_install_tools.sh list"
}

# Parse arguments
if [ $# -eq 0 ]; then
    show_help
    exit 0
fi

COMMAND=$1
shift

case $COMMAND in
    add)
        if [ $# -lt 2 ]; then
            echo -e "${RED}Error: add command requires tool_id and repo_url.${NC}"
            echo "Usage: ./auto_install_tools.sh add <tool_id> <repo_url> [--no-install] [--no-training]"
            exit 1
        fi
        
        TOOL_ID=$1
        REPO_URL=$2
        shift 2
        
        OPTIONS=""
        for arg in "$@"; do
            if [ "$arg" == "--no-install" ]; then
                OPTIONS="$OPTIONS --no-install"
            elif [ "$arg" == "--no-training" ]; then
                OPTIONS="$OPTIONS --no-training"
            fi
        done
        
        echo -e "${GREEN}Adding new tool: $TOOL_ID${NC}"
        python3 utils/auto_tool_manager.py add $TOOL_ID $REPO_URL $OPTIONS
        
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 0 ]; then
            echo -e "${GREEN}Tool $TOOL_ID was added successfully.${NC}"
            
            # Ask to update the training model
            if [[ ! "$OPTIONS" == *"--no-training"* ]]; then
                echo ""
                echo -e "${YELLOW}Would you like to fine-tune the model with the updated training data? (y/n)${NC}"
                read -p "Fine-tune model? " choice
                if [[ "$choice" =~ ^[Yy]$ ]]; then
                    echo -e "${GREEN}Running training pipeline...${NC}"
                    ./utils/train_tools_pipeline.sh
                else
                    echo "You can run the training pipeline later using ./utils/train_tools_pipeline.sh"
                fi
            fi
        else
            echo -e "${RED}Failed to add tool $TOOL_ID.${NC}"
        fi
        ;;
        
    update)
        if [ $# -lt 1 ]; then
            echo -e "${RED}Error: update command requires tool_id.${NC}"
            echo "Usage: ./auto_install_tools.sh update <tool_id> [--no-install] [--no-training]"
            exit 1
        fi
        
        TOOL_ID=$1
        shift
        
        OPTIONS=""
        for arg in "$@"; do
            if [ "$arg" == "--no-install" ]; then
                OPTIONS="$OPTIONS --no-install"
            elif [ "$arg" == "--no-training" ]; then
                OPTIONS="$OPTIONS --no-training"
            fi
        done
        
        echo -e "${GREEN}Updating tool: $TOOL_ID${NC}"
        python3 utils/auto_tool_manager.py update $TOOL_ID $OPTIONS
        
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 0 ]; then
            echo -e "${GREEN}Tool $TOOL_ID was updated successfully.${NC}"
            
            # Ask to update the training model
            if [[ ! "$OPTIONS" == *"--no-training"* ]]; then
                echo ""
                echo -e "${YELLOW}Would you like to fine-tune the model with the updated training data? (y/n)${NC}"
                read -p "Fine-tune model? " choice
                if [[ "$choice" =~ ^[Yy]$ ]]; then
                    echo -e "${GREEN}Running training pipeline...${NC}"
                    ./utils/train_tools_pipeline.sh
                else
                    echo "You can run the training pipeline later using ./utils/train_tools_pipeline.sh"
                fi
            fi
        else
            echo -e "${RED}Failed to update tool $TOOL_ID.${NC}"
        fi
        ;;
        
    remove)
        if [ $# -lt 1 ]; then
            echo -e "${RED}Error: remove command requires tool_id.${NC}"
            echo "Usage: ./auto_install_tools.sh remove <tool_id>"
            exit 1
        fi
        
        TOOL_ID=$1
        
        echo -e "${YELLOW}Are you sure you want to remove tool $TOOL_ID? (y/n)${NC}"
        read -p "Remove tool? " choice
        if [[ "$choice" =~ ^[Yy]$ ]]; then
            echo -e "${GREEN}Removing tool: $TOOL_ID${NC}"
            python3 utils/auto_tool_manager.py remove $TOOL_ID
            
            EXIT_CODE=$?
            if [ $EXIT_CODE -eq 0 ]; then
                echo -e "${GREEN}Tool $TOOL_ID was removed successfully.${NC}"
                
                # Ask to update the training model
                echo ""
                echo -e "${YELLOW}Would you like to fine-tune the model with the updated training data? (y/n)${NC}"
                read -p "Fine-tune model? " choice
                if [[ "$choice" =~ ^[Yy]$ ]]; then
                    echo -e "${GREEN}Running training pipeline...${NC}"
                    ./utils/train_tools_pipeline.sh
                else
                    echo "You can run the training pipeline later using ./utils/train_tools_pipeline.sh"
                fi
            else
                echo -e "${RED}Failed to remove tool $TOOL_ID.${NC}"
            fi
        else
            echo "Tool removal cancelled."
        fi
        ;;
        
    list)
        echo -e "${GREEN}Listing security tools...${NC}"
        python3 utils/auto_tool_manager.py list
        ;;
        
    help)
        show_help
        ;;
        
    *)
        echo -e "${RED}Error: Unknown command $COMMAND.${NC}"
        show_help
        exit 1
        ;;
esac

exit 0
