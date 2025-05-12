#!/usr/bin/env python3
# filepath: /Users/mac/VulnAI/utils/test_current_tool_knowledge.py
"""
This script tests the current model's understanding of security tools
without fine-tuning, to establish a baseline for comparison.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any
from openai import OpenAI

# Add the app directory to the path so we can import from it
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
from utils.logger import log_info, log_error

# Add the current directory to the path so we can import the metrics tracker
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from track_training_metrics import TrainingMetricsTracker


def load_tools_metadata(file_path: str) -> Dict[str, Any]:
    """Load the tools metadata from the JSON file."""
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception as e:
        log_error(f"Failed to load tools metadata: {str(e)}")
        return {}


def generate_test_questions(tools_metadata: Dict[str, Any]) -> List[Dict[str, str]]:
    """Generate test questions for a sample of tools."""
    test_questions = []
    
    # Sample of different types of tools to test
    sample_tools = ["nuclei", "nmap", "katana", "gau", "naabu"]
    
    for tool_id in sample_tools:
        if tool_id in tools_metadata:
            tool_info = tools_metadata[tool_id]
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
    
    return test_questions


def ask_model(client: OpenAI, model_id: str, question: str) -> str:
    """Ask a question to the specified model."""
    try:
        response = client.chat.completions.create(
            model=model_id,
            messages=[
                {"role": "system", "content": "You are a cybersecurity expert that can run security tools to analyze systems and applications."},
                {"role": "user", "content": question}
            ]
        )
        
        return response.choices[0].message.content
    except Exception as e:
        log_error(f"Error asking question to model: {str(e)}")
        return f"Error: {str(e)}"


def evaluate_response(question: Dict[str, str], response: str, tools_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate the model's response to a question."""
    tool_id = question["tool_id"]
    tool_info = tools_metadata.get(tool_id, {})
    
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
    
def run_test(model_id: str, tools_metadata_path: str) -> None:
    """Run a test on the model's understanding of security tools."""
    # Initialize OpenAI client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        log_error("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")
        return
        
    client = OpenAI(api_key=api_key)
    
    # Initialize metrics tracker
    metrics_tracker = TrainingMetricsTracker()
    
    # Load tools metadata
    tools_metadata = load_tools_metadata(tools_metadata_path)
    if not tools_metadata:
        log_error("Failed to load tools metadata.")
        return
        
    # Generate test questions
    test_questions = generate_test_questions(tools_metadata)
    
    # Run the test
    log_info(f"Testing model {model_id} on {len(test_questions)} questions about security tools...")
    
    results = []
    total_score = 0
    
    for i, question_data in enumerate(test_questions):
        question = question_data["question"]
        tool_id = question_data["tool_id"]
        category = question_data["category"]
        
        log_info(f"[{i+1}/{len(test_questions)}] Testing question: {question}")
        response = ask_model(client, model_id, question)
        
        # Evaluate the response
        evaluation = evaluate_response(question_data, response, tools_metadata)
        results.append(evaluation)
        total_score += evaluation["score"]
        
        # Record metrics
        metrics_tracker.record_model_test(
            model_id=model_id,
            tool_id=tool_id,
            category=category,
            question=question,
            response=response,
            score=evaluation["score"]
        )
    
    # Calculate average score
    average_score = total_score / len(results) if results else 0
    
    # Save the results
    output_file = f"data/model_test_results_{model_id.replace(':', '_')}.json"
    try:
        with open(output_file, "w") as f:
            json.dump({
                "model_id": model_id,
                "results": results,
                "average_score": average_score
            }, f, indent=2)
        log_info(f"Results saved to {output_file}")
    except Exception as e:
        log_error(f"Failed to save results: {str(e)}")
    
    # Print a summary
    log_info("\n===== TEST SUMMARY =====")
    log_info(f"Model: {model_id}")
    log_info(f"Questions tested: {len(test_questions)}")
    log_info(f"Average score: {average_score:.2f}%")
    
    # Group results by category
    category_scores = {}
    for result in results:
        category = result["category"]
        if category not in category_scores:
            category_scores[category] = []
        category_scores[category].append(result["score"])
    
    log_info("\nCategory scores:")
    for category, scores in category_scores.items():
        avg_score = sum(scores) / len(scores) if scores else 0
        log_info(f"  {category}: {avg_score:.2f}%")
    
    log_info("\nTool scores:")
    tool_scores = {}
    for result in results:
        tool_id = result["tool_id"]
        if tool_id not in tool_scores:
            tool_scores[tool_id] = []
        tool_scores[tool_id].append(result["score"])
    
    for tool_id, scores in tool_scores.items():
        avg_score = sum(scores) / len(scores) if scores else 0
        log_info(f"  {tool_id}: {avg_score:.2f}%")


def main():
    parser = argparse.ArgumentParser(description="Test a model's knowledge of security tools")
    parser.add_argument("--model", type=str, default="gpt-4o",
                        help="ID of the model to test (default: gpt-4o)")
    parser.add_argument("--tools-metadata", type=str, default="tools/tools_metadata.json",
                        help="Path to the tools metadata JSON file")
    
    args = parser.parse_args()
    
    run_test(args.model, args.tools_metadata)


if __name__ == "__main__":
    main()
