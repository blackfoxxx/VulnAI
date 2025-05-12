#!/usr/bin/env python3
# filepath: /Users/mac/VulnAI/app/ml/multi_model_manager.py

import os
import json
import logging
from typing import Dict, Any, List, Optional

# Import the AI integration module
from app.ml.ai_integration import AIIntegration
from app.utils.logger import log_info, log_error

class MultiModelManager:
    """
    Manager for using multiple specialized AI models based on security domains.
    This approach allows for more accurate analysis by routing vulnerability
    analysis requests to domain-specific fine-tuned models.
    """
    
    def __init__(self):
        self.ai_integration = AIIntegration()
        self.models_config_path = os.path.join("config", "domain_models.json")
        self.domain_models = self._load_domain_models()
        self.default_model = "ft:gpt-4o-2024-08-06:personal::BWAukKEO"  # Default fine-tuned model
    
    def _load_domain_models(self) -> Dict[str, str]:
        """Load domain-specific model configuration."""
        try:
            if os.path.exists(self.models_config_path):
                with open(self.models_config_path, 'r') as f:
                    return json.load(f)
            else:
                # Create default configuration if it doesn't exist
                default_config = {
                    "web_vulnerabilities": "ft:gpt-4o-2024-08-06:personal::BWAukKEO",
                    "network_security": "ft:gpt-4o-2024-08-06:personal::BWAukKEO",
                    "mobile_security": "ft:gpt-4o-2024-08-06:personal::BWAukKEO",
                    "cloud_security": "ft:gpt-4o-2024-08-06:personal::BWAukKEO",
                    "iot_security": "ft:gpt-4o-2024-08-06:personal::BWAukKEO",
                    "tools_model": "ft:gpt-4o-2024-08-06:personal::BWAukKEO",
                    "default": "ft:gpt-4o-2024-08-06:personal::BWAukKEO"
                }
                
                # Ensure config directory exists
                os.makedirs(os.path.dirname(self.models_config_path), exist_ok=True)
                
                # Write default configuration
                with open(self.models_config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                
                return default_config
        except Exception as e:
            log_error(f"Error loading domain models configuration: {str(e)}")
            return {"default": self.default_model}
    
    def save_domain_models(self) -> bool:
        """Save domain models configuration."""
        try:
            with open(self.models_config_path, 'w') as f:
                json.dump(self.domain_models, f, indent=2)
            return True
        except Exception as e:
            log_error(f"Error saving domain models configuration: {str(e)}")
            return False
    
    def update_domain_model(self, domain: str, model_id: str) -> bool:
        """Update the model for a specific security domain."""
        try:
            self.domain_models[domain] = model_id
            return self.save_domain_models()
        except Exception as e:
            log_error(f"Error updating domain model: {str(e)}")
            return False
    
    def get_model_for_domain(self, domain: str) -> str:
        """Get the appropriate model ID for a security domain."""
        return self.domain_models.get(domain, self.domain_models.get("default", self.default_model))
    
    def detect_security_domain(self, title: str, description: str) -> str:
        """
        Detect the security domain from the vulnerability title and description.
        Uses keyword matching for efficiency, but could be enhanced with ML classification.
        """
        text = (title + " " + description).lower()
        
        # Check if this is a tool-related query first
        if self.is_tool_related(text):
            return "tools_model"
            
        # Web vulnerability keywords
        if any(kw in text for kw in ["sql injection", "xss", "cross-site", "csrf", "web", "http", "ajax", "rest", "api"]):
            return "web_vulnerabilities"
        
        # Network security keywords
        elif any(kw in text for kw in ["network", "firewall", "dns", "tcp", "ip", "ddos", "mitm", "man in the middle"]):
            return "network_security"
        
        # Mobile security keywords
        elif any(kw in text for kw in ["mobile", "android", "ios", "app", "apk", "swift", "kotlin"]):
            return "mobile_security"
        
        # Cloud security keywords
        elif any(kw in text for kw in ["cloud", "aws", "azure", "gcp", "s3", "bucket", "containerization", "kubernetes", "docker"]):
            return "cloud_security"
        
        # IoT security keywords
        elif any(kw in text for kw in ["iot", "device", "embedded", "firmware", "smart home", "smart device"]):
            return "iot_security"
        
        # Default domain
        return "default"
        
    def is_tool_related(self, text: str) -> bool:
        """
        Determine if a query is related to security tools.
        """
        text = text.lower()
        
        # Check for tool names
        tool_names = ["nuclei", "nmap", "sqlmap", "ffuf", "dirsearch", "whatweb", "subfinder", 
                      "httpx", "katana", "naabu", "gau", "url scanner", "log analyzer"]
        
        # Check for tool-related keywords
        tool_keywords = ["scan", "check", "tool", "command", "run", "execute", "probe", "reconnaissance", 
                        "fingerprint", "discover", "crawl", "fuzz", "ports", "subdomains", "urls"]
                        
        # Check for action verbs related to tools
        action_verbs = ["use", "run", "execute", "launch", "start", "perform", "do", "conduct", "scan with"]
        
        # Check if the text mentions tool names
        if any(tool in text for tool in tool_names):
            return True
            
        # Check if the text contains tool keywords with action verbs
        for verb in action_verbs:
            for keyword in tool_keywords:
                if f"{verb} {keyword}" in text:
                    return True
                    
        return False
        
    def select_model_for_request(self, message: str) -> str:
        """
        Select the appropriate model for a given request message.
        """
        if self.is_tool_related(message):
            return self.get_model_for_domain("tools_model")
        
        # Treat the message as a vulnerability description for domain detection
        domain = self.detect_security_domain("", message)
        return self.get_model_for_domain(domain)
    
    async def analyze_vulnerability(self, title: str, description: str, provider: str = "openai", 
                                  force_domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze a vulnerability using the appropriate domain-specific model.
        
        Args:
            title: The title of the vulnerability
            description: The description of the vulnerability
            provider: The AI provider to use
            force_domain: Optional domain to force using a specific model
            
        Returns:
            Analysis results
        """
        try:
            # Detect the security domain
            domain = force_domain if force_domain else self.detect_security_domain(title, description)
            log_info(f"Detected security domain: {domain}")
            
            # Get the model for this domain
            model_id = self.get_model_for_domain(domain)
            log_info(f"Using model {model_id} for domain {domain}")
            
            # Set the model on the AI integration class (monkey patch for now)
            # In a more robust implementation, the AI Integration class should accept a model parameter
            original_model = None
            
            result = await self.ai_integration.analyze_vulnerability(title, description, provider)
            
            # Add domain and model information to the result
            if result:
                result["security_domain"] = domain
                result["model_used"] = model_id
            
            return result
        except Exception as e:
            log_error(f"Error in multi-model analysis: {str(e)}")
            # Fall back to default analysis
            return await self.ai_integration.analyze_vulnerability(title, description, provider)
    
    def list_available_domains(self) -> List[str]:
        """List all available security domains."""
        return list(self.domain_models.keys())
    
    def get_domain_model_map(self) -> Dict[str, str]:
        """Get the mapping of domains to models."""
        return self.domain_models.copy()

# Create a global instance
multi_model_manager = MultiModelManager()
