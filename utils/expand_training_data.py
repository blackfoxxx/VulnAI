#!/usr/bin/env python3
# filepath: /Users/mac/VulnAI/utils/expand_training_data.py

import os
import json
import logging
import argparse
import random
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Common vulnerability templates for data augmentation
VULNERABILITY_TEMPLATES = [
    {
        "name": "SQL Injection",
        "description_template": "A SQL injection vulnerability was found in the {component} of {application}. The vulnerability allows attackers to inject malicious SQL statements via the {input_vector}, potentially leading to unauthorized access to the database, data leakage, or data manipulation.",
        "severity": ["Critical", "High"],
        "components": ["login form", "search function", "user profile", "admin panel", "registration page"],
        "input_vectors": ["user input field", "URL parameter", "HTTP header", "cookie value", "API parameter"]
    },
    {
        "name": "Cross-Site Scripting (XSS)",
        "description_template": "A {type} Cross-Site Scripting vulnerability was discovered in the {component} of {application}. Malicious scripts can be injected via the {input_vector}, allowing attackers to steal cookies, session tokens, or other sensitive information.",
        "severity": ["High", "Medium"],
        "components": ["comment section", "user profile", "search result page", "message form", "input field"],
        "input_vectors": ["user input", "URL parameter", "file upload", "JSON response", "HTML attributes"],
        "types": ["reflected", "stored", "DOM-based"]
    },
    {
        "name": "Insecure Direct Object Reference (IDOR)",
        "description_template": "An Insecure Direct Object Reference vulnerability was identified in the {component} of {application}. The vulnerability allows attackers to access or modify {data_type} by manipulating resource identifiers, bypassing authorization checks.",
        "severity": ["High", "Medium"],
        "components": ["user profile", "account settings", "document viewer", "payment system", "data management"],
        "data_types": ["user data", "financial records", "personal information", "confidential documents", "system files"]
    },
    {
        "name": "Server-Side Request Forgery (SSRF)",
        "description_template": "A Server-Side Request Forgery vulnerability was detected in the {component} of {application}. This vulnerability allows attackers to induce the server to make requests to an arbitrary domain of the attacker's choosing, potentially leading to access to internal services or data exfiltration.",
        "severity": ["Critical", "High"],
        "components": ["URL validator", "webhook processor", "API integration", "image processor", "content fetcher"]
    },
    {
        "name": "Cross-Site Request Forgery (CSRF)",
        "description_template": "A Cross-Site Request Forgery vulnerability was found in the {component} of {application}. The vulnerability allows attackers to trick users into performing unintended actions on the application when they are authenticated.",
        "severity": ["Medium", "High"],
        "components": ["user settings", "password change", "fund transfer", "account management", "profile update"]
    },
    {
        "name": "Authentication Bypass",
        "description_template": "An authentication bypass vulnerability was identified in the {component} of {application}. This vulnerability allows attackers to gain unauthorized access by {bypass_method}, effectively circumventing the authentication mechanism.",
        "severity": ["Critical", "High"],
        "components": ["login system", "two-factor authentication", "password reset", "session management", "API endpoints"],
        "bypass_methods": ["manipulating request parameters", "session fixation", "exploiting logic flaws", "brute forcing credentials", "modifying client-side validation"]
    }
]

# Common applications for generating examples
APPLICATIONS = [
    "E-commerce Platform", "Banking Portal", "Healthcare System", "Content Management System", 
    "Social Media Application", "Customer Relationship Management", "HR Management System",
    "Learning Management System", "Inventory Management Software", "Payment Gateway",
    "Cloud Storage Service", "Email Service", "Project Management Tool", "Booking System"
]

class TrainingDataExpander:
    """Utility class to expand training data through synthesis and augmentation."""
    
    def __init__(self, output_path: str):
        self.output_path = output_path
    
    def generate_synthetic_examples(self, count: int = 20) -> List[Dict[str, Any]]:
        """Generate synthetic vulnerability examples based on templates."""
        examples = []
        
        for _ in range(count):
            # Randomly select a vulnerability template
            template = random.choice(VULNERABILITY_TEMPLATES)
            
            # Randomly select an application
            application = random.choice(APPLICATIONS)
            
            # Generate a synthetic vulnerability
            vuln = self._generate_from_template(template, application)
            
            # Convert to training format
            training_example = self._convert_to_training_format(vuln)
            examples.append(training_example)
        
        return examples
    
    def _generate_from_template(self, template: Dict[str, Any], application: str) -> Dict[str, Any]:
        """Generate a synthetic vulnerability from a template."""
        # Select random elements for the template
        severity = random.choice(template.get("severity", ["Medium"]))
        
        # Fill in template-specific fields
        description = template["description_template"]
        
        # Replace {application} with a specific application
        description = description.replace("{application}", application)
        
        # Replace other placeholders
        if "{component}" in description:
            component = random.choice(template.get("components", ["component"]))
            description = description.replace("{component}", component)
        
        if "{input_vector}" in description:
            input_vector = random.choice(template.get("input_vectors", ["input"]))
            description = description.replace("{input_vector}", input_vector)
        
        if "{data_type}" in description:
            data_type = random.choice(template.get("data_types", ["data"]))
            description = description.replace("{data_type}", data_type)
        
        if "{type}" in description:
            type_ = random.choice(template.get("types", ["type"]))
            description = description.replace("{type}", type_)
        
        if "{bypass_method}" in description:
            bypass_method = random.choice(template.get("bypass_methods", ["method"]))
            description = description.replace("{bypass_method}", bypass_method)
        
        # Create the vulnerability object
        return {
            "title": f"{template['name']} in {application}",
            "description": description,
            "severity": severity,
            "source": "synthetic",
            "timestamp": self._get_timestamp()
        }
    
    def _convert_to_training_format(self, vuln: Dict[str, Any]) -> Dict[str, Any]:
        """Convert vulnerability data to the message format needed for training."""
        # Generate an appropriate response based on severity
        advice = self._generate_remediation_advice(vuln)
        
        return {
            "messages": [
                {"role": "system", "content": "You are a cybersecurity expert analyzing vulnerabilities."},
                {"role": "user", "content": f"Analyze this vulnerability:\nTitle: {vuln['title']}\nDescription: {vuln['description']}"},
                {"role": "assistant", "content": f"Based on my analysis, this is a {vuln['severity']} severity vulnerability. {advice}"}
            ]
        }
    
    def _generate_remediation_advice(self, vuln: Dict[str, Any]) -> str:
        """Generate appropriate remediation advice based on the vulnerability."""
        title_lower = vuln['title'].lower()
        
        # SQL Injection advice
        if "sql injection" in title_lower:
            return "To remediate SQL injection vulnerabilities, implement parameterized queries or prepared statements instead of dynamic SQL. Use input validation, apply the principle of least privilege for database accounts, and consider using an ORM (Object-Relational Mapping) layer."
        
        # XSS advice
        elif "xss" in title_lower or "cross-site scripting" in title_lower:
            return "To prevent Cross-Site Scripting, implement proper output encoding, use Content Security Policy (CSP), validate and sanitize all user inputs, and utilize modern frameworks with built-in XSS protections. Consider using the HTTPOnly flag for cookies to prevent them from being accessed by client-side scripts."
        
        # IDOR advice
        elif "idor" in title_lower or "insecure direct object reference" in title_lower:
            return "To fix Insecure Direct Object References, implement proper authorization checks for every request, use indirect references (such as database keys that don't expose the actual resource IDs), and adopt a robust access control system. Regularly audit access control mechanisms to ensure they're working as intended."
        
        # SSRF advice
        elif "ssrf" in title_lower or "server-side request forgery" in title_lower:
            return "To mitigate Server-Side Request Forgery, implement a whitelist of allowed domains and IP addresses, disable unnecessary URL schemas, use a dedicated service for remote resource access with proper validation, and consider network-level controls to prevent access to internal services."
        
        # CSRF advice
        elif "csrf" in title_lower or "cross-site request forgery" in title_lower:
            return "To prevent Cross-Site Request Forgery attacks, implement anti-CSRF tokens, use the SameSite cookie attribute, check the Referer header for sensitive operations, and require re-authentication for critical functions. Consider adopting the synchronizer token pattern."
        
        # Authentication Bypass advice
        elif "authentication bypass" in title_lower:
            return "To address authentication bypass vulnerabilities, implement multi-factor authentication, ensure session management is secure, validate authentication at both client and server sides, use proper cryptographic methods for storing credentials, and conduct regular security testing of authentication mechanisms."
        
        # Generic advice
        else:
            return "To address this vulnerability, follow security best practices including input validation, proper authentication and authorization, secure coding practices, and regular security testing. Consider implementing defense-in-depth strategies and keeping all software components updated."
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def save_to_jsonl(self, examples: List[Dict[str, Any]]) -> None:
        """Save examples to a JSONL file."""
        with open(self.output_path, 'a', encoding='utf-8') as jsonl_file:
            for example in examples:
                jsonl_file.write(json.dumps(example) + '\n')
        
        logger.info(f"Added {len(examples)} examples to {self.output_path}")
    
    def load_existing_jsonl(self, input_path: str) -> List[Dict[str, Any]]:
        """Load existing examples from a JSONL file."""
        examples = []
        try:
            with open(input_path, 'r', encoding='utf-8') as jsonl_file:
                for line in jsonl_file:
                    if line.strip():
                        examples.append(json.loads(line))
            logger.info(f"Loaded {len(examples)} examples from {input_path}")
        except Exception as e:
            logger.error(f"Error loading examples from {input_path}: {str(e)}")
        
        return examples
    
    def augment_existing_examples(self, examples: List[Dict[str, Any]], augmentation_factor: int = 2) -> List[Dict[str, Any]]:
        """Augment existing examples with variations to increase dataset size."""
        augmented_examples = []
        
        for example in examples:
            # Skip if not in the expected format
            if "messages" not in example or len(example["messages"]) < 3:
                continue
            
            # Extract the original content
            system_msg = next((msg for msg in example["messages"] if msg["role"] == "system"), {"content": ""})
            user_msg = next((msg for msg in example["messages"] if msg["role"] == "user"), {"content": ""})
            assistant_msg = next((msg for msg in example["messages"] if msg["role"] == "assistant"), {"content": ""})
            
            # Extract title and description if available
            title = ""
            description = ""
            
            user_content = user_msg.get("content", "")
            if "Title:" in user_content and "Description:" in user_content:
                parts = user_content.split("Description:", 1)
                title_part = parts[0].replace("Analyze this vulnerability:", "").replace("Title:", "").strip()
                title = title_part
                description = parts[1].strip()
            
            # Skip if we couldn't extract necessary info
            if not title or not description:
                continue
            
            # Create variations
            for _ in range(augmentation_factor):
                new_title = self._create_title_variation(title)
                new_description = self._create_description_variation(description)
                
                new_user_content = f"Analyze this vulnerability:\nTitle: {new_title}\nDescription: {new_description}"
                
                # Create a new training example with variations
                augmented_examples.append({
                    "messages": [
                        {"role": "system", "content": system_msg.get("content", "")},
                        {"role": "user", "content": new_user_content},
                        {"role": "assistant", "content": assistant_msg.get("content", "")}
                    ]
                })
        
        logger.info(f"Created {len(augmented_examples)} augmented examples from {len(examples)} original examples")
        return augmented_examples
    
    def _create_title_variation(self, title: str) -> str:
        """Create a variation of the vulnerability title."""
        # Simple variations
        variations = [
            f"Potential {title}",
            f"{title} Vulnerability",
            f"Discovered {title}",
            f"{title} Security Issue",
            f"Possible {title}"
        ]
        return random.choice(variations)
    
    def _create_description_variation(self, description: str) -> str:
        """Create a variation of the vulnerability description."""
        # Simple rewriting techniques
        sentences = description.split(". ")
        
        if len(sentences) <= 1:
            return description
        
        # Shuffle some sentences
        if len(sentences) > 2:
            cutoff = random.randint(1, len(sentences) - 1)
            sentences = sentences[:cutoff] + sentences[cutoff:]
        
        # Add some filler phrases
        fillers = [
            "Upon investigation, ",
            "After analysis, ",
            "During testing, ",
            "Security scanning revealed that ",
            "It was found that "
        ]
        
        if random.random() > 0.5 and sentences:
            idx = random.randint(0, len(sentences) - 1)
            sentences[idx] = random.choice(fillers) + sentences[idx].lower()
        
        return ". ".join(sentences)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Expand training data for VulnLearnAI.')
    parser.add_argument('--output', '-o', required=True, help='Output JSONL file path')
    parser.add_argument('--input', '-i', help='Optional input JSONL file to augment')
    parser.add_argument('--count', '-c', type=int, default=20, help='Number of synthetic examples to generate')
    parser.add_argument('--augment-factor', '-a', type=int, default=2, help='Factor for augmenting existing examples')
    args = parser.parse_args()
    
    expander = TrainingDataExpander(args.output)
    
    # Generate synthetic examples
    synthetic_examples = expander.generate_synthetic_examples(args.count)
    expander.save_to_jsonl(synthetic_examples)
    
    # Augment existing examples if input file provided
    if args.input and os.path.exists(args.input):
        existing_examples = expander.load_existing_jsonl(args.input)
        augmented_examples = expander.augment_existing_examples(existing_examples, args.augment_factor)
        expander.save_to_jsonl(augmented_examples)
    
    print(f"Successfully expanded training data. Added {len(synthetic_examples)} synthetic examples.")
    if args.input and os.path.exists(args.input):
        existing_count = len(expander.load_existing_jsonl(args.input))
        print(f"Augmented {existing_count} existing examples by a factor of {args.augment_factor}.")
    print(f"Output saved to {args.output}")
