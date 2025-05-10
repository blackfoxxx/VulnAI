# VulnLearnAI

VulnLearnAI is an AI-powered cybersecurity tool that learns from real-world pentesting outputs and vulnerability write-ups. It integrates with active offensive tools and uses machine learning to classify and prioritize security findings.

## Features

- Machine learning-based vulnerability classification
- Admin panel for training data management
- Integration with common security tools (Nuclei, FFUF, WhatWeb, DirBuster)
- REST API for automated interactions
- Real-time vulnerability assessment and classification

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/VulnAI.git
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

## Future Extensions

- LLM-based exploit recommendations
- Automated report generation
- Adaptive scoring based on context
- Integration with more security tools
- Enhanced ML model training options

## License

MIT License - feel free to use and modify as needed.
