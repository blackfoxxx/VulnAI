#!/usr/bin/env python3
# filepath: /Users/mac/VulnAI/utils/benchmark_model.py

import os
import json
import time
import asyncio
import argparse
import logging
import csv
from typing import List, Dict, Any
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the AI integration module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.ml.ai_integration import AIIntegration

class ModelBenchmark:
    """
    Utility for benchmarking the performance of fine-tuned models.
    Evaluates models on a test dataset and measures:
    - Accuracy
    - Response time
    - Consistency
    - Relevance
    """
    
    def __init__(self, test_data_path: str, output_dir: str = "data/benchmarks"):
        self.test_data_path = test_data_path
        self.output_dir = output_dir
        self.ai_integration = AIIntegration()
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
    
    async def load_test_data(self) -> List[Dict[str, Any]]:
        """Load test data from JSONL file."""
        test_data = []
        try:
            with open(self.test_data_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        entry = json.loads(line)
                        # Extract test case from the entry
                        if "messages" in entry:
                            user_msg = next((msg for msg in entry["messages"] if msg["role"] == "user"), None)
                            assistant_msg = next((msg for msg in entry["messages"] if msg["role"] == "assistant"), None)
                            
                            if user_msg and assistant_msg:
                                # Extract title and description
                                content = user_msg["content"]
                                title = ""
                                description = ""
                                
                                if "Title:" in content and "Description:" in content:
                                    parts = content.split("Description:", 1)
                                    title_part = parts[0].replace("Analyze this vulnerability:", "").replace("Title:", "").strip()
                                    title = title_part
                                    description = parts[1].strip()
                                
                                if title and description:
                                    test_data.append({
                                        "title": title,
                                        "description": description,
                                        "expected_response": assistant_msg["content"]
                                    })
            
            logger.info(f"Loaded {len(test_data)} test cases from {self.test_data_path}")
            return test_data
        except Exception as e:
            logger.error(f"Error loading test data: {str(e)}")
            return []
    
    async def run_benchmark(self, providers: List[str] = ["openai"], sample_size: int = None) -> Dict[str, Any]:
        """Run the benchmark on the test dataset."""
        test_data = await self.load_test_data()
        
        if not test_data:
            logger.error("No test data available. Benchmark cannot proceed.")
            return {}
        
        # Limit sample size if specified
        if sample_size and sample_size < len(test_data):
            import random
            test_data = random.sample(test_data, sample_size)
            logger.info(f"Using a sample of {len(test_data)} test cases")
        
        benchmark_results = {
            "timestamp": datetime.now().isoformat(),
            "test_data_path": self.test_data_path,
            "sample_size": len(test_data),
            "providers": {}
        }
        
        # Loop through each provider
        for provider in providers:
            provider_results = await self._benchmark_provider(provider, test_data)
            benchmark_results["providers"][provider] = provider_results
        
        # Save the benchmark results
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        result_path = os.path.join(self.output_dir, f"benchmark_results_{timestamp}.json")
        with open(result_path, 'w', encoding='utf-8') as f:
            json.dump(benchmark_results, f, indent=2)
        
        # Also save a CSV summary
        csv_path = os.path.join(self.output_dir, f"benchmark_summary_{timestamp}.csv")
        self._save_csv_summary(benchmark_results, csv_path)
        
        logger.info(f"Benchmark completed. Results saved to {result_path} and {csv_path}")
        return benchmark_results
    
    async def _benchmark_provider(self, provider: str, test_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Benchmark a specific provider on the test dataset."""
        logger.info(f"Benchmarking provider: {provider}")
        
        results = {
            "total_cases": len(test_data),
            "total_time": 0,
            "response_times": [],
            "error_count": 0,
            "responses": []
        }
        
        for i, test_case in enumerate(test_data):
            logger.info(f"Processing test case {i+1}/{len(test_data)} for {provider}")
            
            try:
                # Measure response time
                start_time = time.time()
                response = await self.ai_integration.analyze_vulnerability(
                    test_case["title"],
                    test_case["description"],
                    provider=provider
                )
                end_time = time.time()
                
                # Calculate response time
                response_time = end_time - start_time
                results["response_times"].append(response_time)
                results["total_time"] += response_time
                
                if response:
                    # Calculate metrics for this response
                    metrics = self._calculate_response_metrics(
                        response["analysis"],
                        test_case["expected_response"],
                        test_case["title"],
                        test_case["description"]
                    )
                    
                    # Save the response with metrics
                    results["responses"].append({
                        "test_case": test_case["title"],
                        "response": response["analysis"],
                        "expected": test_case["expected_response"],
                        "response_time": response_time,
                        "metrics": metrics
                    })
                else:
                    results["error_count"] += 1
            except Exception as e:
                logger.error(f"Error processing test case {i+1}: {str(e)}")
                results["error_count"] += 1
        
        # Calculate aggregate metrics
        if results["response_times"]:
            results["avg_response_time"] = results["total_time"] / len(results["response_times"])
            results["min_response_time"] = min(results["response_times"])
            results["max_response_time"] = max(results["response_times"])
        
        # Calculate success rate
        results["success_rate"] = (len(test_data) - results["error_count"]) / len(test_data) if test_data else 0
        
        # Calculate average metrics across all responses
        avg_metrics = {
            "relevance": 0,
            "consistency": 0,
            "completeness": 0
        }
        
        for response in results["responses"]:
            for key in avg_metrics:
                avg_metrics[key] += response["metrics"][key]
        
        if results["responses"]:
            for key in avg_metrics:
                avg_metrics[key] /= len(results["responses"])
        
        results["avg_metrics"] = avg_metrics
        
        logger.info(f"Completed benchmark for {provider}. Success rate: {results['success_rate']:.2f}")
        return results
    
    def _calculate_response_metrics(self, response: str, expected: str, title: str, description: str) -> Dict[str, float]:
        """
        Calculate metrics for a single response:
        - Relevance: How well the response addresses the specific vulnerability
        - Consistency: How consistent the response is with the expected response
        - Completeness: How complete the response is in covering necessary information
        """
        # Simple metric calculation based on text similarity
        # In a production system, you would use more sophisticated NLP techniques
        
        # Relevance: Check if the response mentions keywords from the title and description
        title_words = set(title.lower().split())
        desc_words = set(' '.join(description.lower().split()[:20]).split())  # Use first ~20 words of description
        response_lower = response.lower()
        
        title_matches = sum(1 for word in title_words if word in response_lower and len(word) > 3)
        desc_matches = sum(1 for word in desc_words if word in response_lower and len(word) > 3)
        
        relevance = (title_matches / len(title_words) if title_words else 0) * 0.7 + \
                   (desc_matches / len(desc_words) if desc_words else 0) * 0.3
        
        # Consistency: Compare with expected response
        expected_words = set(expected.lower().split())
        response_words = set(response_lower.split())
        
        common_words = expected_words.intersection(response_words)
        consistency = len(common_words) / len(expected_words) if expected_words else 0
        
        # Completeness: Check for key sections (severity, impact, remediation)
        completeness_factors = [
            "severity" in response_lower,
            "impact" in response_lower,
            "risk" in response_lower,
            "remediation" in response_lower or "fix" in response_lower,
            "recommend" in response_lower,
        ]
        
        completeness = sum(completeness_factors) / len(completeness_factors)
        
        return {
            "relevance": min(relevance, 1.0),  # Cap at 1.0
            "consistency": min(consistency, 1.0),
            "completeness": completeness
        }
    
    def _save_csv_summary(self, results: Dict[str, Any], csv_path: str) -> None:
        """Save a CSV summary of the benchmark results."""
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Provider', 'Success Rate', 'Avg Response Time (s)', 
                'Relevance', 'Consistency', 'Completeness',
                'Error Count', 'Sample Size'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for provider, provider_results in results["providers"].items():
                writer.writerow({
                    'Provider': provider,
                    'Success Rate': f"{provider_results['success_rate']:.2f}",
                    'Avg Response Time (s)': f"{provider_results.get('avg_response_time', 0):.2f}",
                    'Relevance': f"{provider_results['avg_metrics']['relevance']:.2f}",
                    'Consistency': f"{provider_results['avg_metrics']['consistency']:.2f}",
                    'Completeness': f"{provider_results['avg_metrics']['completeness']:.2f}",
                    'Error Count': provider_results['error_count'],
                    'Sample Size': results['sample_size']
                })


async def main():
    parser = argparse.ArgumentParser(description='Benchmark model performance for VulnLearnAI.')
    parser.add_argument('--test-data', required=True, help='Path to test data JSONL file')
    parser.add_argument('--output-dir', default='data/benchmarks', help='Directory to save benchmark results')
    parser.add_argument('--providers', nargs='+', default=['openai'], help='List of providers to benchmark')
    parser.add_argument('--sample-size', type=int, help='Number of test cases to sample (if not specified, use all)')
    
    args = parser.parse_args()
    
    benchmark = ModelBenchmark(args.test_data, args.output_dir)
    results = await benchmark.run_benchmark(providers=args.providers, sample_size=args.sample_size)
    
    # Print a summary of the results
    print("\nBenchmark Results Summary:")
    print("=" * 50)
    print(f"Test data: {args.test_data}")
    print(f"Sample size: {results['sample_size']}")
    print("-" * 50)
    
    for provider, provider_results in results["providers"].items():
        print(f"Provider: {provider}")
        print(f"  Success Rate: {provider_results['success_rate']:.2f}")
        print(f"  Avg Response Time: {provider_results.get('avg_response_time', 0):.2f} seconds")
        print(f"  Relevance: {provider_results['avg_metrics']['relevance']:.2f}")
        print(f"  Consistency: {provider_results['avg_metrics']['consistency']:.2f}")
        print(f"  Completeness: {provider_results['avg_metrics']['completeness']:.2f}")
        print(f"  Error Count: {provider_results['error_count']}")
        print("-" * 50)


if __name__ == "__main__":
    import sys
    asyncio.run(main())
