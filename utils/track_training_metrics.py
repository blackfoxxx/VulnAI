#!/usr/bin/env python3
# filepath: /Users/mac/VulnAI/utils/track_training_metrics.py
"""
This script tracks and visualizes metrics related to the AI's understanding of security tools 
before and after training. It helps measure the effectiveness of the fine-tuning process.
"""

import os
import json
import sys
import argparse
import datetime
import matplotlib.pyplot as plt
import numpy as np
from typing import Dict, List, Any

# Add the app directory to the path so we can import from it
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app"))
from utils.logger import log_info, log_error


class TrainingMetricsTracker:
    """Tracks and visualizes metrics about tool knowledge training."""
    
    def __init__(self, metrics_dir="data/metrics"):
        self.metrics_dir = metrics_dir
        os.makedirs(metrics_dir, exist_ok=True)
        
    def record_model_test(self, model_id: str, tool_id: str, category: str, 
                          question: str, response: str, score: float) -> None:
        """
        Record metrics from a model test.
        
        Args:
            model_id: ID of the model tested
            tool_id: ID of the tool tested
            category: Category of the test (purpose, usage, etc.)
            question: The question asked
            response: The model's response
            score: The score assigned to the response (0-100)
        """
        metrics_file = os.path.join(self.metrics_dir, f"tool_tests_{model_id.replace(':', '_')}.jsonl")
        
        # Create a timestamped record
        record = {
            "timestamp": datetime.datetime.now().isoformat(),
            "model_id": model_id,
            "tool_id": tool_id,
            "category": category,
            "question": question,
            "response_snippet": response[:200] + "..." if len(response) > 200 else response,
            "score": score
        }
        
        # Append the record to the metrics file
        try:
            with open(metrics_file, "a") as f:
                f.write(json.dumps(record) + "\n")
                
            log_info(f"Recorded metrics for model {model_id}, tool {tool_id}, category {category}")
        except Exception as e:
            log_error(f"Failed to record metrics: {str(e)}")
    
    def load_metrics(self, model_id: str) -> List[Dict[str, Any]]:
        """Load metrics for a specific model."""
        metrics_file = os.path.join(self.metrics_dir, f"tool_tests_{model_id.replace(':', '_')}.jsonl")
        
        metrics = []
        try:
            if os.path.exists(metrics_file):
                with open(metrics_file, "r") as f:
                    for line in f:
                        try:
                            metrics.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            log_error(f"Failed to load metrics: {str(e)}")
            
        return metrics
        
    def calculate_category_scores(self, metrics: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate average scores by category."""
        category_scores = {}
        
        for record in metrics:
            category = record.get("category")
            score = record.get("score")
            
            if category and score is not None:
                if category not in category_scores:
                    category_scores[category] = []
                category_scores[category].append(score)
                
        # Calculate averages
        averages = {}
        for category, scores in category_scores.items():
            averages[category] = sum(scores) / len(scores) if scores else 0
            
        return averages
        
    def calculate_tool_scores(self, metrics: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate average scores by tool."""
        tool_scores = {}
        
        for record in metrics:
            tool_id = record.get("tool_id")
            score = record.get("score")
            
            if tool_id and score is not None:
                if tool_id not in tool_scores:
                    tool_scores[tool_id] = []
                tool_scores[tool_id].append(score)
                
        # Calculate averages
        averages = {}
        for tool_id, scores in tool_scores.items():
            averages[tool_id] = sum(scores) / len(scores) if scores else 0
            
        return averages
        
    def compare_models(self, base_model_id: str, finetuned_model_id: str) -> Dict[str, Any]:
        """
        Compare metrics between a base model and a fine-tuned model.
        
        Args:
            base_model_id: The ID of the base model
            finetuned_model_id: The ID of the fine-tuned model
            
        Returns:
            Dictionary with comparison results
        """
        base_metrics = self.load_metrics(base_model_id)
        finetuned_metrics = self.load_metrics(finetuned_model_id)
        
        if not base_metrics or not finetuned_metrics:
            log_error("Not enough metrics data to compare models")
            return {}
            
        # Calculate category scores
        base_category_scores = self.calculate_category_scores(base_metrics)
        finetuned_category_scores = self.calculate_category_scores(finetuned_metrics)
        
        # Calculate tool scores
        base_tool_scores = self.calculate_tool_scores(base_metrics)
        finetuned_tool_scores = self.calculate_tool_scores(finetuned_metrics)
        
        # Calculate overall scores
        base_overall = sum(s for scores in base_tool_scores.values() for s in scores) / len(base_metrics) if base_metrics else 0
        finetuned_overall = sum(s for scores in finetuned_tool_scores.values() for s in scores) / len(finetuned_metrics) if finetuned_metrics else 0
        
        # Calculate improvement percentages
        category_improvements = {}
        for category in set(base_category_scores.keys()) | set(finetuned_category_scores.keys()):
            base_score = base_category_scores.get(category, 0)
            finetuned_score = finetuned_category_scores.get(category, 0)
            
            if base_score > 0:
                improvement = ((finetuned_score - base_score) / base_score) * 100
            else:
                improvement = 100 if finetuned_score > 0 else 0
                
            category_improvements[category] = improvement
            
        tool_improvements = {}
        for tool_id in set(base_tool_scores.keys()) | set(finetuned_tool_scores.keys()):
            base_score = base_tool_scores.get(tool_id, 0)
            finetuned_score = finetuned_tool_scores.get(tool_id, 0)
            
            if base_score > 0:
                improvement = ((finetuned_score - base_score) / base_score) * 100
            else:
                improvement = 100 if finetuned_score > 0 else 0
                
            tool_improvements[tool_id] = improvement
            
        # Overall improvement
        overall_improvement = ((finetuned_overall - base_overall) / base_overall) * 100 if base_overall > 0 else 0
        
        return {
            "base_model": base_model_id,
            "finetuned_model": finetuned_model_id,
            "base_category_scores": base_category_scores,
            "finetuned_category_scores": finetuned_category_scores,
            "base_tool_scores": base_tool_scores,
            "finetuned_tool_scores": finetuned_tool_scores,
            "base_overall": base_overall,
            "finetuned_overall": finetuned_overall,
            "category_improvements": category_improvements,
            "tool_improvements": tool_improvements,
            "overall_improvement": overall_improvement
        }
        
    def visualize_comparison(self, comparison_data: Dict[str, Any], output_file: str = None) -> None:
        """
        Visualize the comparison between models.
        
        Args:
            comparison_data: The comparison data returned by compare_models
            output_file: Optional file path to save the visualization
        """
        if not comparison_data:
            log_error("No comparison data to visualize")
            return
            
        # Create figure and subplots
        fig = plt.figure(figsize=(15, 10))
        
        # 1. Overall scores comparison
        ax1 = fig.add_subplot(2, 2, 1)
        models = ["Base Model", "Fine-tuned Model"]
        scores = [comparison_data["base_overall"], comparison_data["finetuned_overall"]]
        ax1.bar(models, scores, color=["#1f77b4", "#ff7f0e"])
        ax1.set_ylim(0, 100)
        ax1.set_title("Overall Model Performance")
        ax1.set_ylabel("Average Score")
        
        # 2. Category scores comparison
        ax2 = fig.add_subplot(2, 2, 2)
        categories = list(comparison_data["category_improvements"].keys())
        improvements = [comparison_data["category_improvements"][c] for c in categories]
        
        # Sort by improvement for better visualization
        sorted_indices = np.argsort(improvements)
        categories = [categories[i] for i in sorted_indices]
        improvements = [improvements[i] for i in sorted_indices]
        
        colors = ["#d62728" if imp < 0 else "#2ca02c" for imp in improvements]
        ax2.barh(categories, improvements, color=colors)
        ax2.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
        ax2.set_title("Improvement by Category")
        ax2.set_xlabel("% Improvement")
        
        # 3. Tool scores comparison
        ax3 = fig.add_subplot(2, 2, 3)
        base_tools = comparison_data["base_tool_scores"]
        finetuned_tools = comparison_data["finetuned_tool_scores"]
        
        # Combine tool keys and filter for more common ones
        tool_ids = list(set(base_tools.keys()) & set(finetuned_tools.keys()))
        
        # If there are too many tools, select a subset
        if len(tool_ids) > 5:
            # Select tools with biggest score differences
            differences = {t: abs(finetuned_tools.get(t, 0) - base_tools.get(t, 0)) for t in tool_ids}
            tool_ids = sorted(differences, key=differences.get, reverse=True)[:5]
        
        # Create the grouped bar chart
        x = np.arange(len(tool_ids))
        width = 0.35
        
        base_scores = [base_tools.get(t, 0) for t in tool_ids]
        finetuned_scores = [finetuned_tools.get(t, 0) for t in tool_ids]
        
        ax3.bar(x - width/2, base_scores, width, label="Base Model", color="#1f77b4")
        ax3.bar(x + width/2, finetuned_scores, width, label="Fine-tuned Model", color="#ff7f0e")
        
        ax3.set_title("Tool Understanding Comparison")
        ax3.set_xticks(x)
        ax3.set_xticklabels(tool_ids, rotation=45, ha="right")
        ax3.set_ylim(0, 100)
        ax3.set_ylabel("Average Score")
        ax3.legend()
        
        # 4. Tool improvements
        ax4 = fig.add_subplot(2, 2, 4)
        tool_improvements = comparison_data["tool_improvements"]
        
        # Sort tools by improvement
        tools = list(tool_improvements.keys())
        if len(tools) > 5:
            # Sort by absolute improvement and take top 5
            tools = sorted(tools, key=lambda t: abs(tool_improvements[t]), reverse=True)[:5]
            
        improvements = [tool_improvements[t] for t in tools]
        
        # Sort for better visualization
        sorted_indices = np.argsort(improvements)
        tools = [tools[i] for i in sorted_indices]
        improvements = [improvements[i] for i in sorted_indices]
        
        colors = ["#d62728" if imp < 0 else "#2ca02c" for imp in improvements]
        ax4.barh(tools, improvements, color=colors)
        ax4.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
        ax4.set_title("Improvement by Tool")
        ax4.set_xlabel("% Improvement")
        
        # Add overall title and adjust layout
        plt.suptitle(f"Model Comparison: Base vs. Fine-tuned\nOverall Improvement: {comparison_data['overall_improvement']:.2f}%", 
                    fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        # Save or display
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches="tight")
            log_info(f"Visualization saved to {output_file}")
        else:
            plt.show()


def main():
    parser = argparse.ArgumentParser(description="Track and visualize model training metrics")
    parser.add_argument("--base-model", type=str, required=True,
                        help="ID of the base model")
    parser.add_argument("--finetuned-model", type=str, required=True,
                        help="ID of the fine-tuned model")
    parser.add_argument("--output", type=str, default="data/metrics/model_comparison.png",
                        help="Path to save the visualization")
    
    args = parser.parse_args()
    
    tracker = TrainingMetricsTracker()
    comparison = tracker.compare_models(args.base_model, args.finetuned_model)
    
    if comparison:
        tracker.visualize_comparison(comparison, args.output)
        
        # Print a summary
        print("\n===== MODEL COMPARISON SUMMARY =====")
        print(f"Base Model: {args.base_model}")
        print(f"Fine-tuned Model: {args.finetuned_model}")
        print(f"Overall Base Score: {comparison['base_overall']:.2f}")
        print(f"Overall Fine-tuned Score: {comparison['finetuned_overall']:.2f}")
        print(f"Overall Improvement: {comparison['overall_improvement']:.2f}%")
        
        print("\nCategory Improvements:")
        for category, improvement in comparison["category_improvements"].items():
            print(f"  {category}: {improvement:.2f}%")
            
        print("\nTool Improvements:")
        for tool_id, improvement in comparison["tool_improvements"].items():
            print(f"  {tool_id}: {improvement:.2f}%")
    else:
        print("No comparison data available. Make sure both models have metrics recorded.")


if __name__ == "__main__":
    main()
