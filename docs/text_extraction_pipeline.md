# Text Extraction and Training Data Pipeline

This document describes the enhanced training data pipeline implemented in VulnLearnAI, which adds support for multiple file formats and data expansion capabilities.

## Text Extraction (text_extractor.py)

The text extraction module allows you to extract vulnerability information from various text-based file formats and convert them into the proper JSONL format for model training.

### Supported File Formats

- Plain text files (.txt)
- PDF documents (.pdf)
- Microsoft Word documents (.docx)

### Usage

```bash
# Process a single file
python utils/text_extractor.py --input /path/to/vulnerability_report.pdf --output data/extracted_training.jsonl

# Process an entire directory (recursively)
python utils/text_extractor.py --input /path/to/documents_dir/ --output data/extracted_training.jsonl
```

### How It Works

1. The tool detects the file format based on the extension
2. It extracts text using the appropriate library:
   - TXT: Native Python file operations
   - PDF: PyPDF2 library
   - DOCX: python-docx library
3. The extracted text is parsed to identify:
   - Vulnerability title (typically the first line or most prominent heading)
   - Severity level (by keyword detection)
   - Description (the main content)
4. The extracted information is converted to the message format required for fine-tuning:
   - System message: "You are a cybersecurity expert analyzing vulnerabilities."
   - User message: Contains the title and description
   - Assistant message: Generated response that includes severity assessment and remediation advice

### Example

**Input file (vulnerability_report.txt):**
```
SQL Injection in Authentication System

A critical vulnerability was discovered in the authentication system.
The login form does not properly sanitize user inputs, allowing attackers
to inject arbitrary SQL queries. This could lead to unauthorized access,
data leakage, or complete system compromise.
```

**Output JSONL entry:**
```json
{"messages":[{"role":"system","content":"You are a cybersecurity expert analyzing vulnerabilities."},{"role":"user","content":"Analyze this vulnerability:\nTitle: SQL Injection in Authentication System\nDescription: A critical vulnerability was discovered in the authentication system. The login form does not properly sanitize user inputs, allowing attackers to inject arbitrary SQL queries. This could lead to unauthorized access, data leakage, or complete system compromise."},{"role":"assistant","content":"Based on my analysis, this appears to be a Critical severity vulnerability. The vulnerability involves sql injection in authentication system which can lead to security issues. To remediate this, it's recommended to implement parameterized queries or prepared statements, validate and sanitize all user inputs, and apply the principle of least privilege for database accounts."}]}
```

## Training Data Expansion (expand_training_data.py)

The training data expansion module provides capabilities for generating synthetic vulnerability examples and augmenting existing training data to create a more robust dataset.

### Features

1. **Synthetic Data Generation**: Create artificial but realistic vulnerability examples based on templates covering common vulnerability types like:
   - SQL Injection
   - Cross-Site Scripting (XSS)
   - Insecure Direct Object References (IDOR)
   - Server-Side Request Forgery (SSRF)
   - Cross-Site Request Forgery (CSRF)
   - Authentication Bypass

2. **Data Augmentation**: Create variations of existing training examples by:
   - Modifying titles
   - Rewriting descriptions with variations
   - Preserving the core vulnerability information

### Usage

```bash
# Generate synthetic examples
python utils/expand_training_data.py --output data/synthetic_training.jsonl --count 30

# Augment existing examples
python utils/expand_training_data.py --output data/augmented_training.jsonl --input data/original_training.jsonl --augment-factor 3
```

### How It Works

#### Synthetic Data Generation

1. The tool selects a vulnerability template from the predefined list
2. It fills in the template with random but appropriate components:
   - Application names (e.g., "E-commerce Platform", "Banking Portal")
   - Components (e.g., "login form", "admin panel")
   - Input vectors (e.g., "user input field", "URL parameter")
3. The generated vulnerability is converted to the training format
4. Appropriate remediation advice is added based on the vulnerability type

#### Data Augmentation

1. The tool reads existing examples from a JSONL file
2. For each example, it creates variations:
   - Title variations (e.g., "SQL Injection" → "Potential SQL Injection")
   - Description rewrites with reordered sentences and filler phrases
3. The core meaning is preserved while providing more training diversity

## Fine-Tuning Automation (automate_fine_tuning.py)

The fine-tuning automation module has been enhanced to support multiple data sources and streamline the fine-tuning process.

### Features

1. **Multi-Source Support**: Combine training data from:
   - Existing JSONL files
   - Extracted text files
   - Synthetic and augmented examples

2. **Validation**: Ensure all training data follows the required format

3. **Fine-Tuning Automation**: Streamline the process of:
   - Uploading training files to OpenAI
   - Creating fine-tuning jobs
   - Monitoring progress
   - Integrating the new model

### Usage

```bash
# Basic usage
python utils/automate_fine_tuning.py --training-file data/combined_training.jsonl

# Advanced usage with multiple sources
python utils/automate_fine_tuning.py \
  --input-files data/original_training.jsonl data/synthetic_training.jsonl \
  --text-dirs /path/to/documents/ \
  --output-file data/combined_training.jsonl \
  --model gpt-4o-2024-08-06 \
  --update-integration
```

## Integration with CI/CD

The training data pipeline is fully integrated with the CI/CD workflow, allowing for:

1. **Automated Testing**: Unit tests ensure the extraction and expansion functions work correctly
2. **Continuous Improvement**: Regular updates to the training dataset
3. **Model Versioning**: Each fine-tuned model is tracked with its training source

## Future Improvements

1. **Enhanced Extraction**: Implement more sophisticated text parsing for better extraction
2. **Domain-Specific Templates**: Add templates for specialized security domains
3. **Quality Filtering**: Add automatic filtering of low-quality training examples
4. **Cross-Validation**: Implement validation techniques to avoid overfitting
