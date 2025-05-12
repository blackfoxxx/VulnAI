# VulnLearnAI

VulnLearnAI is an AI-powered cybersecurity tool that learns from real-world pentesting outputs and vulnerability write-ups. It integrates with active offensive tools and uses machine learning to classify and prioritize security findings.

## Features

- Machine learning-based vulnerability classification
- Fine-tuned GPT-4o model for vulnerability assessment
- Admin panel for training data management
- Integration with common security tools (Nuclei, FFUF, WhatWeb, DirBuster)
- REST API for automated interactions
- Real-time vulnerability assessment and classification
- Text file extraction for training data (PDF, Word, TXT)
- Synthetic training data generation and augmentation
- Multi-model approach for different security domains
- Automated CI/CD pipeline for testing and deployment
- Model performance benchmarking
- Natural language tool execution in chat interface

## Interactive Security Chat

VulnLearnAI features an integrated chat interface that allows users to execute security tools using natural language commands directly within the conversation flow. This feature provides a seamless experience for:

- Running security tools with simple natural language instructions
- Receiving AI analysis of tool outputs within the same conversation
- Getting recommendations for additional security checks
- Learning about security concepts and vulnerabilities

For example, users can type commands like:
- "Scan example.com with Nuclei"
- "Check what technologies are used on example.com"
- "Run an Nmap scan on 192.168.1.1"
- "Test if example.com is vulnerable to SQL injection"

The system automatically detects the user's intent, selects the appropriate tool, executes it with the right parameters, and provides an analysis of the results.

## Fine-Tuned Model

VulnLearnAI uses a custom fine-tuned GPT-4o model (ID: `ft:gpt-4o-2024-08-06:personal::BWAukKEO`) that has been specifically trained on vulnerability assessments. This model provides more accurate and domain-specific vulnerability analyses than generic LLMs.

### Fine-Tuning Process

The fine-tuning process involved:
1. Creating a specialized training dataset with examples of vulnerability analysis
2. Converting the data to the required JSONL message format
3. Uploading the dataset to OpenAI
4. Running the fine-tuning job on GPT-4o
5. Integrating the fine-tuned model into the application

The training data contains carefully crafted examples that teach the model how to:
- Analyze different types of security vulnerabilities
- Assess severity levels accurately
- Identify attack vectors and exploitation techniques
- Suggest appropriate remediation steps

### Testing the Fine-Tuned Model

You can test the fine-tuned model using the provided test scripts:

```bash
# Using the OpenAI CLI
openai api chat_completions.create -m ft:gpt-4o-2024-08-06:personal::BWAukKEO -g system "You are a cybersecurity expert analyzing vulnerabilities." -g user "SQL Injection in Login Form"

# Using the shell script (multiple examples)
./utils/test_model.sh

# Using the Python script
python utils/model_tester.py

# Using the benchmarking tool to compare model performance
python utils/benchmark_model.py --test-data data/final_training_data.jsonl --sample-size 20
```

### Model Enhancements

We have implemented several enhancements to improve model performance:

1. **Multi-Model Approach**: The system now uses domain-specific models for different security areas (web, network, mobile, cloud, IoT), automatically routing analysis requests to the appropriate specialized model.

2. **Benchmarking Framework**: A comprehensive benchmarking system evaluates models on metrics including accuracy, response time, relevance, consistency, and completeness.

3. **Training Data Pipeline**: Our enhanced pipeline supports:
   - Text extraction from various file formats (PDF, DOCX, TXT)
   - Synthetic data generation from vulnerability templates
   - Data augmentation to increase training variety
   - Automatic JSONL formatting for fine-tuning

4. **Continuous Integration**: Automated testing and deployment through GitHub Actions ensures code quality and streamlines updates.

See [Future Fine-Tuning Plans](/docs/future_fine_tuning.md) for upcoming enhancements.

## Golang Security Tools Support

VulnLearnAI now includes support for Golang-based security tools in its Docker container:

- **Nuclei**: Fast template-based vulnerability scanner from ProjectDiscovery
- **Subfinder**: Subdomain discovery tool for finding valid subdomains
- **httpx**: Fast and multi-purpose HTTP toolkit for web server probing
- **Katana**: A fast web crawler designed to efficiently crawl websites with JavaScript rendering
- **Naabu**: Fast port scanner with a focus on reliability and simplicity
- **Gau**: GetAllUrls tool that fetches known URLs from various sources for a domain

### Setting up Golang Tools

For local development, you can install the Golang tools using the provided script:

```bash
./tools/install_go_tools.sh
```

When using Docker, these tools are automatically installed and configured in the container.

### Using Golang Tools

You can use these tools directly through the interactive chat interface with commands like:

- "Run Nuclei scan on example.com"
- "Find subdomains of example.com using subfinder"
- "Probe example.com with httpx"
- "Crawl example.com with Katana"
- "Scan ports on example.com with Naabu"
- "Find all URLs for example.com with Gau"

The AI will interpret these commands, execute the appropriate tool, and provide an analysis of the results.

## Setup

1. Clone the repository:
```bash
git clone https://github.com/blackfoxxx/VulnAI.git
cd VulnAI
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory:
```env
ADMIN_TOKEN=your_secure_token_here
```

5. Run the application:
```bash
uvicorn app.main:app --reload --port 8000
```

The application will be available at:
- API: http://localhost:8000
- Admin Panel: http://localhost:8000/admin
- API Documentation: http://localhost:8000/docs

## Usage

### Admin Panel

1. Access the admin panel at http://localhost:8000/admin
2. Use the form to add new training data:
   - Vulnerability title and description
   - Related writeup links
   - Associated CVEs
   - Additional metadata

### API Endpoints

- `GET /health` - Check system health
- `POST /api/train` - Trigger model training
- `POST /api/admin/training-data` - Add new training data
- `GET /api/admin/training-data` - Retrieve training data entries

### Authentication

Admin endpoints require the `X-Admin-Token` header with the token specified in your `.env` file.

Example:
```bash
curl -X POST http://localhost:8000/api/admin/training-data \
  -H "X-Admin-Token: your_secure_token_here" \
  -H "Content-Type: application/json" \
  -d '{"title": "SQL Injection", "description": "..."}'
```

## Machine Learning

The system uses scikit-learn for:
- Text vectorization (TF-IDF)
- Random Forest classification
- Severity prediction (High/Low)

Models are automatically saved to `data/model/` and can be retrained using new data.

## Directory Structure

```
VulnLearnAI/
├── app/
│   ├── api/
│   │   ├── admin_endpoints.py
│   │   └── models.py
│   ├── ml/
│   │   └── training_engine.py
│   └── utils/
│       ├── logger.py
│       └── error_handlers.py
├── admin-panel/
│   ├── index.html
│   └── js/
│       └── app.js
├── data/
│   ├── logs/
│   └── model/
├── requirements.txt
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Contribution Guidelines

We welcome contributions to VulnLearnAI! To contribute:

1. **Fork the Repository**: Click the "Fork" button on the repository page.
2. **Clone Your Fork**: Clone your forked repository to your local machine.
   ```bash
   git clone https://github.com/your-username/VulnAI.git
   ```
3. **Create a Feature Branch**: Create a new branch for your feature or bug fix.
   ```bash
   git checkout -b feature-name
   ```
4. **Make Changes**: Implement your changes and commit them with clear commit messages.
   ```bash
   git commit -m "Add feature description"
   ```
5. **Push Changes**: Push your changes to your forked repository.
   ```bash
   git push origin feature-name
   ```
6. **Create a Pull Request**: Open a pull request to the main repository.

## Troubleshooting

### Common Issues

1. **Dependency Installation Errors**:
   - Ensure you are using the correct Python version (>=3.8).
   - Activate your virtual environment before installing dependencies.

2. **Application Fails to Start**:
   - Check if the `.env` file is correctly configured.
   - Ensure no other application is using port 8000.

3. **Model Training Issues**:
   - Verify the format of `training_data.json`.
   - Check logs in the `data/logs/` directory for detailed error messages.

## Changelog

For a detailed list of changes, refer to the [CHANGELOG.md](CHANGELOG.md) file.

## Future Extensions

- LLM-based exploit recommendations
- Automated report generation
- Adaptive scoring based on context
- Integration with more security tools
- Enhanced ML model training options

## Tool Knowledge Training

VulnLearnAI can be trained to better understand and interact with security tools through natural language. This training process enhances the AI's ability to:

1. Understand user commands about security tools
2. Select the right tool for a specific security task
3. Execute tools with appropriate parameters
4. Analyze and explain tool outputs correctly

For detailed instructions on training the system with tool documentation, see [Tool Documentation Training](/docs/tool_documentation_training.md).

