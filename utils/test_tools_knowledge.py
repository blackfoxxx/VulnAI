#!/usr/bin/env python3
# filepath: /Users/mac/VulnAI/utils/test_tools_knowledge.py
"""
This script tests the fine-tuned model's understanding of security tools
by asking a series of questions about different tools and analyzing the responses.
"""

import os
import json
import sys
import argparse
from typing import Dict, List, Any
import openai

# Add the app directory to the path so we can import from it
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
from utils.logger import log_info, log_error


class ToolKnowledgeTester:
    def __init__(self, model_id: str, tools_metadata_path: str):
        self.model_id = model_id
        self.tools_metadata_path = tools_metadata_path
        self.tools_metadata = self._load_tools_metadata()
        
        # Initialize OpenAI client
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            log_error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
            sys.exit(1)
            
        self.client = openai.OpenAI()
        
    def _load_tools_metadata(self) -> Dict[str, Any]:
        """Load the tools metadata from the JSON file."""
        try:
            with open(self.tools_metadata_path, "r") as f:
                return json.load(f)
        except Exception as e:
            log_error(f"Failed to load tools metadata: {str(e)}")
            return {}
            
    def generate_test_questions(self) -> List[Dict[str, str]]:
        """Generate test questions for each tool."""
        test_questions = []
        
        for tool_id, tool_info in self.tools_metadata.items():
            tool_name = tool_info.get("name", tool_id)
            
            # Add questions about tool purpose
            test_questions.append({
                "question": f"What is {tool_name} used for?",
                "tool_id": tool_id,
                "category": "purpose"
            })
            
            # Add questions about how to use the tool
            test_questions.append({
                "question": f"How do I use {tool_name} to scan a website?",
                "tool_id": tool_id,
                "category": "usage"
            })
            
            # For specific tools, add more targeted questions
            if tool_id in ["nuclei", "nmap", "sqlmap"]:
                test_questions.append({
                    "question": f"What kinds of vulnerabilities can {tool_name} detect?",
                    "tool_id": tool_id,
                    "category": "capabilities"
                })
                
        return test_questions
        
    def ask_question(self, question: str) -> str:
        """Ask a question to the fine-tuned model."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": "You are a cybersecurity expert that can run security tools to analyze systems and applications."},
                    {"role": "user", "content": question}
                ]
            )
            
            return response.choices[0].message.content
        except Exception as e:
            log_error(f"Error asking question to model: {str(e)}")
            return f"Error: {str(e)}"
            
    def evaluate_response(self, question: Dict[str, str], response: str) -> Dict[str, Any]:
        """Evaluate the model's response to a question."""
        tool_id = question["tool_id"]
        tool_info = self.tools_metadata.get(tool_id, {})
        
        # Extract key information from the tool metadata
        tool_name = tool_info.get("name", tool_id)
        description = tool_info.get("description", "")
        
        # Check if the response contains key information
        mentions_tool = tool_name.lower() in response.lower()
        mentions_purpose = any(keyword in response.lower() for keyword in description.lower().split()[:5])
        
        score = 0
        if mentions_tool:
            score += 1
        if mentions_purpose:
            score += 1
            
        # For usage questions, check if it mentions command structure
        if question["category"] == "usage" and "command" in tool_info:
            command_parts = tool_info["command"].split()
            if any(part in response.lower() for part in command_parts[:2]):
                score += 1
                
        # Normalize score to a percentage
        max_score = 3 if question["category"] == "usage" else 2
        normalized_score = (score / max_score) * 100
        
        return {
            "question": question["question"],
            "tool_id": tool_id,
            "category": question["category"],
            "score": normalized_score,
            "response": response
        }
        
    def run_tests(self) -> List[Dict[str, Any]]:
        """Run all tests and return the results."""
        log_info(f"Starting tool knowledge tests with model {self.model_id}...")
        
        test_questions = self.generate_test_questions()
        test_results = []
        
        for i, question in enumerate(test_questions):
            log_info(f"Running test {i+1}/{len(test_questions)}: {question['question']}")
            
            response = self.ask_question(question["question"])
            evaluation = self.evaluate_response(question, response)
            test_results.append(evaluation)
            
        return test_results
        
    def run(self) -> None:
        """Run the testing process and print results."""
        log_info("Starting tool knowledge testing...")
        
        test_results = self.run_tests()
        
        # Calculate overall statistics
        total_score = sum(result["score"] for result in test_results)
        average_score = total_score / len(test_results) if test_results else 0
        
        # Group results by category
        category_scores = {}
        for result in test_results:
            category = result["category"]
            if category not in category_scores:
                category_scores[category] = []
            category_scores[category].append(result["score"])
            
        # Print summary
        log_info("\n===== TOOL KNOWLEDGE TEST RESULTS =====")
        log_info(f"Model: {self.model_id}")
        log_info(f"Total questions: {len(test_results)}")
        log_info(f"Overall average score: {average_score:.2f}%")
        log_info("\nCategory scores:")
        
        for category, scores in category_scores.items():
            avg_score = sum(scores) / len(scores)
            log_info(f"  {category.capitalize()}: {avg_score:.2f}%")
            
        # Print detailed results
        log_info("\nDetailed results:")
        for result in test_results:
            log_info(f"\nQuestion: {result['question']}")
            log_info(f"Tool: {result['tool_id']}")
            log_info(f"Category: {result['category']}")
            log_info(f"Score: {result['score']:.2f}%")
            log_info(f"Response: {result['response'][:200]}...")
            
        log_info("\nTesting complete.")
        

def main():
    parser = argparse.ArgumentParser(description="Test a fine-tuned model's knowledge of security tools")
    parser.add_argument("--model", type=str, required=True,
                        help="ID of the fine-tuned model to test")
    parser.add_argument("--tools-metadata", type=str, default="tools/tools_metadata.json",
                        help="Path to the tools metadata JSON file")
    
    args = parser.parse_args()
    
    tester = ToolKnowledgeTester(args.model, args.tools_metadata)
    tester.run()
    
    
if __name__ == "__main__":
    main()
