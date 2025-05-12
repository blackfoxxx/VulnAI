# Multi-Model Security Domain Approach

This document describes the multi-model approach implemented in VulnLearnAI for specialized analysis of different security domains.

## Overview

The multi-model approach routes vulnerability analysis requests to specialized models that have been optimized for specific security domains. This results in more accurate and domain-relevant analyses compared to using a single general-purpose model.

## Supported Security Domains

The system currently supports the following security domains:

1. **Web Vulnerabilities**: SQL Injection, XSS, CSRF, etc.
2. **Network Security**: Firewall misconfigurations, DNS vulnerabilities, etc.
3. **Mobile Security**: Android/iOS vulnerabilities, app-specific issues
4. **Cloud Security**: AWS, Azure, GCP vulnerabilities, misconfigured cloud resources
5. **IoT Security**: Embedded device vulnerabilities, firmware issues, etc.

## Architecture

The multi-model system consists of:

1. **Domain Detection**: Analyzes vulnerability titles and descriptions to detect the appropriate security domain
2. **Model Selection**: Maps security domains to specialized fine-tuned models
3. **Analysis Routing**: Directs the analysis request to the appropriate model
4. **Response Integration**: Combines domain-specific insights with general vulnerability knowledge

## Implementation

The implementation is contained in the `app/ml/multi_model_manager.py` module, which provides:

1. `MultiModelManager` class for managing domain-specific models
2. Domain detection using keyword-based classification
3. Configuration management for model-to-domain mapping
4. Fallback mechanisms when domain detection is inconclusive

## Usage

### API Integration

```python
from app.ml.multi_model_manager import multi_model_manager

# Analyze a vulnerability with automatic domain detection
result = await multi_model_manager.analyze_vulnerability(
    title="SQL Injection in Login Form",
    description="The login form doesn't properly sanitize user inputs..."
)

# Force analysis with a specific domain model
result = await multi_model_manager.analyze_vulnerability(
    title="Misconfigured S3 Bucket",
    description="The AWS S3 bucket has public write access enabled...",
    force_domain="cloud_security"
)
```

### REST API

```bash
# Automatic domain detection
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"title": "SQL Injection in Login Form", "description": "The login form input is not sanitized..."}'

# Specify security domain
curl -X POST http://localhost:8000/api/analyze/domain \
  -H "Content-Type: application/json" \
  -d '{"title": "Misconfigured S3 Bucket", "description": "The AWS S3 bucket has public write access...", "domain": "cloud_security"}'
```

## Configuration

The domain-to-model mapping is stored in `config/domain_models.json`:

```json
{
  "web_vulnerabilities": "ft:gpt-4o-2024-08-06:personal::WebVulnModel",
  "network_security": "ft:gpt-4o-2024-08-06:personal::NetworkSecModel",
  "mobile_security": "ft:gpt-4o-2024-08-06:personal::MobileSecModel",
  "cloud_security": "ft:gpt-4o-2024-08-06:personal::CloudSecModel",
  "iot_security": "ft:gpt-4o-2024-08-06:personal::IoTSecModel",
  "default": "ft:gpt-4o-2024-08-06:personal::BWAukKEO"
}
```

## Domain Detection

The system uses a keyword-based approach to detect security domains:

1. **Web Vulnerabilities**: sql injection, xss, cross-site, csrf, web, http, ajax, rest, api
2. **Network Security**: network, firewall, dns, tcp, ip, ddos, mitm, man in the middle
3. **Mobile Security**: mobile, android, ios, app, apk, swift, kotlin
4. **Cloud Security**: cloud, aws, azure, gcp, s3, bucket, containerization, kubernetes, docker
5. **IoT Security**: iot, device, embedded, firmware, smart home, smart device

## Benefits

The multi-model approach provides several advantages:

1. **Improved Accuracy**: Specialized models better understand domain-specific concepts
2. **Relevant Remediation**: Provides more targeted and effective remediation suggestions
3. **Scalability**: Easy to add new domains as security landscape evolves
4. **Resource Efficiency**: Uses the most appropriate model for each analysis

## Future Improvements

1. **ML-Based Domain Classification**: Replace keyword detection with a machine learning classifier
2. **Fine-Tuning Pipeline**: Create specialized training datasets for each security domain
3. **Dynamic Model Selection**: Use performance metrics to continuously improve model selection
4. **Ensemble Approach**: Combine insights from multiple domain models for complex vulnerabilities
