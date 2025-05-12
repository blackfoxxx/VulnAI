# Model Benchmarking Framework

This document describes the comprehensive benchmarking framework implemented in VulnLearnAI for evaluating and comparing the performance of fine-tuned models.

## Overview

The benchmarking framework allows for systematic evaluation of model performance across various metrics, helping to:

1. Compare different models and fine-tuning approaches
2. Track performance improvements over time
3. Identify strengths and weaknesses in different security domains
4. Make data-driven decisions for model selection

## Key Metrics

The framework evaluates models on the following metrics:

1. **Response Time**: How quickly the model generates analysis
2. **Success Rate**: Percentage of requests completed without errors
3. **Relevance**: How well the response addresses the specific vulnerability
4. **Consistency**: How consistent the response is with expected patterns
5. **Completeness**: Whether the response includes all necessary components (severity, impact, remediation)

## Implementation

The benchmarking tool is implemented in `utils/benchmark_model.py` and includes:

1. `ModelBenchmark` class for running benchmarks
2. Test dataset loading and processing
3. Metrics calculation and aggregation
4. Results reporting in JSON and CSV formats

## Usage

### Basic Usage

```bash
# Run a benchmark with default settings
python utils/benchmark_model.py --test-data data/test_dataset.jsonl

# Run with a sample of test cases
python utils/benchmark_model.py --test-data data/test_dataset.jsonl --sample-size 20

# Test multiple providers
python utils/benchmark_model.py --test-data data/test_dataset.jsonl --providers openai deepseek
```

### Output Files

The benchmark generates two output files in the specified directory (default: `data/benchmarks/`):

1. **JSON Report**: Detailed benchmark results including all metrics and individual responses
   ```
   benchmark_results_20250512123045.json
   ```

2. **CSV Summary**: Tabular summary for easy comparison
   ```
   benchmark_summary_20250512123045.csv
   ```

## Test Dataset Format

The benchmark accepts test datasets in JSONL format with the following structure:

```json
{"messages":[{"role":"system","content":"You are a cybersecurity expert analyzing vulnerabilities."},{"role":"user","content":"Analyze this vulnerability:\nTitle: SQL Injection\nDescription: The login form is vulnerable to SQL injection..."},{"role":"assistant","content":"Based on my analysis, this is a High severity vulnerability..."}]}
```

The test dataset should include diverse examples covering different:
- Vulnerability types
- Severity levels
- Security domains
- Description lengths and formats

## Metrics Calculation

### Relevance

Relevance measures how well the response addresses the specific vulnerability described in the test case:

1. Extracts important keywords from the title and description
2. Calculates the percentage of these keywords present in the response
3. Gives higher weight to title keywords (70%) vs. description keywords (30%)

### Consistency

Consistency measures how closely the response matches the expected answer pattern:

1. Compares word overlap between the model response and the expected response
2. Calculates the percentage of expected words present in the actual response

### Completeness

Completeness checks whether the response includes all necessary components:

1. Checks for presence of key sections:
   - Severity assessment
   - Impact analysis
   - Risk level
   - Remediation steps
   - Recommendations

## Visualization

The benchmark results can be visualized using common data analysis tools:

1. Load the CSV summary into spreadsheet software
2. Use Python libraries (matplotlib, seaborn) for more advanced visualizations:

```python
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load benchmark results
df = pd.read_csv('data/benchmarks/benchmark_summary_20250512123045.csv')

# Create a comparison chart
plt.figure(figsize=(10, 6))
sns.barplot(x='Provider', y='Relevance', data=df)
plt.title('Model Relevance Comparison')
plt.savefig('data/benchmarks/relevance_comparison.png')
```

## Integration with Continuous Improvement

The benchmarking framework integrates with the CI/CD pipeline to:

1. Automatically test new models after fine-tuning
2. Compare performance against baseline models
3. Generate reports for review
4. Flag significant performance changes

## Future Improvements

1. **Advanced Metrics**: Add more sophisticated evaluation metrics like BLEU or ROUGE scores
2. **Human Evaluation**: Include support for human-in-the-loop evaluation
3. **Domain-Specific Benchmarks**: Create specialized test datasets for each security domain
4. **Performance Over Time**: Track model performance evolution across versions
5. **Statistical Analysis**: Add confidence intervals and statistical significance tests
