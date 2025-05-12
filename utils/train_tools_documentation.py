#!/usr/bin/env python3
# filepath: /Users/mac/VulnAI/utils/train_tools_documentation.py
"""
This script extracts documentation for security tools from their sources
and generates training data for the AI model to better understand their usage.
"""

import os
import json
import sys
import requests
import time
from typing import Dict, List, Any
import random
import argparse

# Add the app directory to the path so we can import from it
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
from utils.logger import log_info, log_error


class ToolDocumentationTrainer:
    def __init__(self, tools_metadata_path: str, training_output_path: str):
        self.tools_metadata_path = tools_metadata_path
        self.training_output_path = training_output_path
        self.tools_metadata = self._load_tools_metadata()
        
    def _load_tools_metadata(self) -> Dict[str, Any]:
        """Load the tools metadata from the JSON file."""
        try:
            with open(self.tools_metadata_path, "r") as f:
                return json.load(f)
        except Exception as e:
            log_error(f"Failed to load tools metadata: {str(e)}")
            return {}
            
    def fetch_github_documentation(self, repo_url: str) -> str:
        """Fetch documentation from a GitHub repository README."""
        try:
            # Convert github.com URL to raw.githubusercontent.com URL for the README
            if not repo_url.endswith(".git"):
                repo_url = repo_url + ".git"
                
            parts = repo_url.replace("https://github.com/", "").replace(".git", "").split("/")
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
                readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
                
                # Try to fetch the README
                response = requests.get(readme_url)
                if response.status_code == 200:
                    return response.text
                
                # If main branch doesn't work, try master
                readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
                response = requests.get(readme_url)
                if response.status_code == 200:
                    return response.text
                    
            return "No documentation available."
        except Exception as e:
            log_error(f"Failed to fetch GitHub documentation: {str(e)}")
            return "Error fetching documentation."
            
    def generate_usage_examples(self, tool_info: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate usage examples for the tool based on its metadata."""
        examples = []
        
        # Basic information
        tool_name = tool_info.get("name", "Unknown Tool")
        description = tool_info.get("description", "")
        command = tool_info.get("command", "")
        
        # Extract the default parameter and its template value
        default_param = tool_info.get("default_param", "")
        param_value = "example.com"
        if default_param and "parameter_template" in tool_info:
            param_value = tool_info["parameter_template"].get(default_param, "example.com")
            
        # Generate examples using natural language patterns if available
        if "natural_language_patterns" in tool_info:
            for pattern in tool_info["natural_language_patterns"]:
                # Create user message
                user_message = pattern.capitalize()
                if "{url}" in user_message:
                    user_message = user_message.replace("{url}", param_value)
                elif "{target}" in user_message:
                    user_message = user_message.replace("{target}", param_value)
                elif "{domain}" in user_message:
                    user_message = user_message.replace("{domain}", param_value)
                else:
                    user_message = f"{user_message} on {param_value}"
                    
                # Create assistant response
                assistant_response = (
                    f"I'll help you {pattern} on {param_value} using the {tool_name} tool. "
                    f"This tool {description.lower()}. "
                    f"I'll run it with the appropriate parameters and analyze the results for you."
                )
                
                examples.append({
                    "role": "user",
                    "content": user_message
                })
                
                examples.append({
                    "role": "assistant",
                    "content": assistant_response
                })
        else:
            # Create generic example
            user_message = f"Can you use {tool_name} to analyze {param_value}?"
            assistant_response = (
                f"I'll use {tool_name} to analyze {param_value}. "
                f"This tool {description.lower()}. "
                f"I'll run it with the appropriate parameters and analyze the results for you."
            )
            
            examples.append({
                "role": "user",
                "content": user_message
            })
            
            examples.append({
                "role": "assistant",
                "content": assistant_response
            })
            
        return examples
    
    def generate_tool_explanation_examples(self, tool_info: Dict[str, Any], documentation: str = None) -> List[Dict[str, str]]:
        """Generate examples where the user asks about a tool and the assistant explains it."""
        examples = []
        
        # Basic information
        tool_name = tool_info.get("name", "Unknown Tool")
        description = tool_info.get("description", "")
        
        # Different ways to ask about a tool
        questions = [
            f"What is {tool_name}?",
            f"How does {tool_name} work?",
            f"What can I do with {tool_name}?",
            f"Tell me about {tool_name}",
            f"What's the purpose of {tool_name}?"
        ]
        
        # Extract key information from documentation
        doc_summary = "No additional documentation available."
        if documentation:
            # Extract a few sentences from the documentation
            sentences = documentation.replace("\n", " ").split(". ")
            relevant_sentences = []
            
            # Look for sentences that mention the tool name
            for sentence in sentences:
                if tool_name.lower() in sentence.lower():
                    relevant_sentences.append(sentence)
                    
            # Limit to a few sentences
            if relevant_sentences:
                doc_summary = ". ".join(relevant_sentences[:3]) + "."
            else:
                doc_summary = ". ".join(sentences[:3]) + "."
        
        # Create an explanation response
        for question in questions:
            examples.append({
                "role": "user",
                "content": question
            })
            
            explanation = (
                f"{tool_name} is a security tool that {description.lower()}. "
                f"{doc_summary} "
                f"You can use it in this environment by asking me to run it on a specific target."
            )
            
            examples.append({
                "role": "assistant",
                "content": explanation
            })
            
        return examples
        
    def generate_training_data(self) -> List[Dict[str, Any]]:
        """Generate training data for all tools in the metadata."""
        training_data = []
        
        for tool_id, tool_info in self.tools_metadata.items():
            log_info(f"Generating training data for {tool_id}...")
            
            # Fetch documentation if available
            documentation = None
            if "git_repo_url" in tool_info:
                documentation = self.fetch_github_documentation(tool_info["git_repo_url"])
                time.sleep(1)  # To avoid hitting rate limits
                
            # Generate usage examples
            usage_examples = self.generate_usage_examples(tool_info)
            training_data.extend(usage_examples)
            
            # Generate explanation examples
            explanation_examples = self.generate_tool_explanation_examples(tool_info, documentation)
            training_data.extend(explanation_examples)
            
        return training_data
        
    def save_training_data(self, data: List[Dict[str, Any]]) -> None:
        """Save the training data to a JSONL file."""
        try:
            # Convert to list of messages format
            formatted_data = []
            
            i = 0
            while i < len(data):
                if data[i]["role"] == "user" and i + 1 < len(data) and data[i + 1]["role"] == "assistant":
                    entry = {
                        "messages": [
                            {"role": "system", "content": "You are a cybersecurity expert that can run security tools to analyze systems and applications."},
                            data[i],
                            data[i + 1]
                        ]
                    }
                    formatted_data.append(entry)
                    i += 2
                else:
                    i += 1
            
            # Shuffle the data
            random.shuffle(formatted_data)
            
            # Save to JSONL file
            with open(self.training_output_path, "w") as f:
                for entry in formatted_data:
                    f.write(json.dumps(entry) + "\n")
                    
            log_info(f"Successfully saved {len(formatted_data)} training examples to {self.training_output_path}")
        except Exception as e:
            log_error(f"Failed to save training data: {str(e)}")
            
    def run(self) -> None:
        """Run the training data generation process."""
        log_info("Starting tool documentation training data generation...")
        
        training_data = self.generate_training_data()
        self.save_training_data(training_data)
        
        log_info("Finished generating tool documentation training data.")
        

def main():
    parser = argparse.ArgumentParser(description="Generate training data from tool documentation")
    parser.add_argument("--tools-metadata", type=str, default="tools/tools_metadata.json",
                        help="Path to the tools metadata JSON file")
    parser.add_argument("--output", type=str, default="data/tools_training_data.jsonl",
                        help="Path to save the training data JSONL file")
    
    args = parser.parse_args()
    
    trainer = ToolDocumentationTrainer(args.tools_metadata, args.output)
    trainer.run()
    
    
if __name__ == "__main__":
    main()
