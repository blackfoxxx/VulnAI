# Training VulnLearnAI on Security Tool Documentation

This document explains how to train the VulnLearnAI system on security tool documentation to improve its understanding and usage of security tools through natural language commands.

## Overview

The training process consists of several steps:

1. **Generating Training Data**: Extract information about tools from their documentation and create examples of natural language interactions.
2. **Fine-tuning the Model**: Using the generated data to fine-tune a GPT-4o model specifically for tool understanding.
3. **Testing the Model**: Evaluating the fine-tuned model's ability to understand and use security tools correctly.
4. **Deploying the Model**: Updating the system configuration to use the fine-tuned model for tool-related queries.

## Available Tools

VulnLearnAI currently includes the following security tools:

### Web Security Tools
- **SQLMap**: Automatic SQL injection and database takeover tool
- **FFUF**: Fast web fuzzer for discovering hidden files and directories
- **Dirsearch**: Web path scanner to find hidden files and directories
- **WhatWeb**: Identify website technologies, CMS, plugins, and other details
- **URL Scanner**: Scans URLs for vulnerabilities and returns detailed reports
- **httpx**: Fast and multi-purpose HTTP toolkit for probing web servers
- **Katana**: A fast crawler designed to execute JavaScript and DOM rendering
- **Gau**: GetAllUrls tool that fetches known URLs from various sources

### Network Security Tools
- **Nmap**: Network scanning and host discovery tool
- **Log Analyzer**: Analyzes server logs to detect suspicious activities
- **Naabu**: Fast port scanner with a focus on reliability and simplicity

### Reconnaissance Tools
- **Subfinder**: Subdomain discovery tool for finding valid subdomains
- **Nuclei**: Vulnerability scanner that uses templates to find security issues

## Training Data Generation

Training data is generated from tool documentation and metadata to help the AI model understand:

1. The purpose and capabilities of each tool
2. How to interpret user requests to use a specific tool
3. How to properly analyze and explain the output from each tool

The training data includes examples like:
- Natural language queries about security tools
- Tool usage requests 
- Detailed explanations of tool purposes and outputs

## Step-by-Step Guide

### 1. Generate Training Data

```bash
# Run the training data generation script
python utils/train_tools_documentation.py --tools-metadata tools/tools_metadata.json --output data/tools_training_data.jsonl
```

This script:
- Extracts information from the tools_metadata.json file
- Fetches additional documentation from GitHub repositories
- Generates natural language examples for each tool
- Creates a JSONL file with training examples in the OpenAI format

### 2. Fine-tune the Model

```bash
# Fine-tune a model with the generated training data
python utils/finetune_tools_model.py --training-data data/tools_training_data.jsonl --model gpt-4o --suffix tools-knowledge
```

This script:
- Validates the training data format
- Uploads the training data to OpenAI
- Starts a fine-tuning job with the specified base model
- Returns a job ID for monitoring the fine-tuning process

### 3. Test the Fine-tuned Model

```bash
# Test the fine-tuned model's understanding of tools
python utils/test_tools_knowledge.py --model ft:gpt-4o:personal:tools-knowledge-20250512 --tools-metadata tools/tools_metadata.json
```

This script:
- Generates test questions for each tool
- Sends the questions to the fine-tuned model
- Evaluates the model's responses for accuracy
- Produces a report with scores for different categories of understanding

### 4. Evaluating and Comparing Models

```bash
# Compare the baseline and fine-tuned models
python utils/track_training_metrics.py --base-model gpt-4o --finetuned-model ft:gpt-4o:personal:tools-knowledge-20250512 --output data/metrics/model_comparison.png
```

This script:
- Loads metrics from both model test runs
- Calculates improvement percentages by category and tool
- Generates visualizations comparing the models
- Creates a detailed report for analysis

The metrics tracked include:
- Tool recognition accuracy
- Command syntax accuracy
- Use case understanding
- Overall improvement score

![Model Comparison Example](../assets/model_comparison_example.png)

### 5. All-in-One Training Process

```bash
# Run the entire training pipeline
python utils/train_security_tools_ai.py --wait-for-completion --test-model --update-config
```

This script:
- Runs all of the above steps in sequence
- Waits for the fine-tuning job to complete
- Tests the model after fine-tuning
- Updates the configuration file with the new model ID

## How to Add a New Tool

When adding a new security tool to VulnLearnAI, you can now use the automated tool manager:

### Using the Automated Tool Manager

The system can automatically detect the programming language of a tool, install it correctly, and update training data:

```bash
# Add a new tool
./tools/auto_install_tools.sh add katana https://github.com/projectdiscovery/katana.git

# Update an existing tool
./tools/auto_install_tools.sh update nuclei

# Remove a tool
./tools/auto_install_tools.sh remove oldscannertools

# List all tools
./tools/auto_install_tools.sh list
```

For each new tool, the system will:
1. Detect the programming language from the repository
2. Generate appropriate metadata and installation commands
3. Install the tool automatically
4. Update the training data with examples for the new tool
5. Offer to fine-tune the model with the updated training data

### Manual Method

If you prefer to add tools manually:

1. Add the tool's metadata to `tools/tools_metadata.json`
2. Include the Git repository URL for documentation extraction
3. Define natural language patterns for tool detection
4. Run the training data generation script
5. Fine-tune the model with the updated training data

## Best Practices

- Always include a diverse set of natural language patterns for each tool
- Provide clear descriptions and expected outputs in the tool metadata
- Re-train the model whenever significant changes are made to the tool collection
- Test the model with a variety of queries before deployment

## Appendix: Understanding the Configuration

The `config/domain_models.json` file contains the model IDs for different security domains. The `tools_model` entry specifies which model to use for tool-related queries. If not specified, the system falls back to the default model.

```json
{
  "web_vulnerabilities": "ft:gpt-4o-2024-08-06:personal::BWAukKEO",
  "network_security": "ft:gpt-4o-2024-08-06:personal::BWAukKEO",
  "tools_model": "ft:gpt-4o-2024-08-06:personal::BWAukKEO",
  "default": "ft:gpt-4o-2024-08-06:personal::BWAukKEO"
}
```

When the AI needs to understand or use a tool, it will first try to use the `tools_model`, and if that's not available, it will use the `default` model.

## Appendix: Automated Tool Management

### Overview

The VulnLearnAI system includes an automated tool management system that can:

1. Detect the programming language of security tools
2. Automatically install tools based on their language
3. Generate metadata and training examples for new tools
4. Update the AI model to understand the new tools

### Key Components

The system consists of the following components:

1. **`auto_tool_manager.py`**: A Python script that handles:
   - Language detection using repository analysis
   - Tool installation based on detected language
   - Metadata generation for new tools
   - Training data generation for new tools

2. **`auto_install_tools.sh`**: A bash script that provides a user-friendly interface to:
   - Add new tools
   - Update existing tools
   - Remove tools
   - List all available tools

### Supported Languages

The system automatically detects and supports tools written in:

- Go
- Python
- JavaScript/Node.js
- Ruby
- Rust
- C/C++

### Adding New Languages

To add support for a new programming language:

1. Update the `LANGUAGE_MARKERS` dictionary in `ToolLanguageDetector` class
2. Add an installation method in the `ToolInstaller` class
3. Update the language detection logic if necessary

### Future Improvements

Planned improvements for the automated tool management system:

1. Support for containerized tools
2. Automatic version detection and updates
3. Integration with tool marketplaces
4. Dependency management for complex tools
5. Cross-platform installation support
