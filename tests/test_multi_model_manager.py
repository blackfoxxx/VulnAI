import os
import json
import unittest
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.multi_model_manager import MultiModelManager

class TestMultiModelManager(unittest.TestCase):
    def setUp(self):
        # Create a temporary config file path
        self.temp_config_path = "temp_domain_models.json"
        
        # Mock the AI integration
        self.mock_ai_integration = MagicMock()
        self.mock_ai_integration.analyze_vulnerability = AsyncMock()
        
        # Create sample domain models config
        self.sample_config = {
            "web_vulnerabilities": "model-web",
            "network_security": "model-network",
            "default": "model-default"
        }
        
        # Patch the _load_domain_models method to use our sample config
        with patch.object(MultiModelManager, '_load_domain_models', return_value=self.sample_config):
            self.manager = MultiModelManager()
            self.manager.models_config_path = self.temp_config_path
            self.manager.ai_integration = self.mock_ai_integration
    
    def tearDown(self):
        # Remove temporary config file if it exists
        if os.path.exists(self.temp_config_path):
            os.remove(self.temp_config_path)
    
    def test_get_model_for_domain(self):
        # Test getting model for existing domain
        model = self.manager.get_model_for_domain("web_vulnerabilities")
        self.assertEqual(model, "model-web")
        
        # Test getting model for non-existing domain (should return default)
        model = self.manager.get_model_for_domain("nonexistent_domain")
        self.assertEqual(model, "model-default")
    
    def test_detect_security_domain(self):
        # Test web vulnerabilities detection
        domain = self.manager.detect_security_domain(
            "SQL Injection in Login Form",
            "The login form is vulnerable to SQL injection attacks."
        )
        self.assertEqual(domain, "web_vulnerabilities")
        
        # Test network security detection
        domain = self.manager.detect_security_domain(
            "Firewall Misconfiguration",
            "The network firewall has weak rules allowing traffic on sensitive ports."
        )
        self.assertEqual(domain, "network_security")
        
        # Test default domain
        domain = self.manager.detect_security_domain(
            "Unknown Vulnerability",
            "A vulnerability of unknown type was detected."
        )
        self.assertEqual(domain, "default")
    
    def test_update_domain_model(self):
        # Mock save_domain_models
        self.manager.save_domain_models = MagicMock(return_value=True)
        
        # Update a domain model
        result = self.manager.update_domain_model("mobile_security", "new-mobile-model")
        
        # Check the result and domain models
        self.assertTrue(result)
        self.assertEqual(self.manager.domain_models["mobile_security"], "new-mobile-model")
        self.manager.save_domain_models.assert_called_once()
    
    def test_save_domain_models(self):
        # Mock open to prevent actual file writing
        with patch("builtins.open", unittest.mock.mock_open()) as mock_open:
            result = self.manager.save_domain_models()
            
            # Check the result
            self.assertTrue(result)
            mock_open.assert_called_once_with(self.temp_config_path, 'w')
    
    @pytest.mark.asyncio
    async def test_analyze_vulnerability(self):
        # Mock AI integration response
        mock_response = {
            "provider": "openai",
            "analysis": "Test analysis",
            "raw_response": {}
        }
        self.manager.ai_integration.analyze_vulnerability.return_value = mock_response
        
        # Test analysis
        result = await self.manager.analyze_vulnerability(
            "SQL Injection in Login Form",
            "The login form is vulnerable to SQL injection attacks."
        )
        
        # Check the result
        self.assertEqual(result["provider"], "openai")
        self.assertEqual(result["analysis"], "Test analysis")
        self.assertEqual(result["security_domain"], "web_vulnerabilities")
        self.assertEqual(result["model_used"], "model-web")
        
        # Verify AI integration was called
        self.manager.ai_integration.analyze_vulnerability.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_vulnerability_force_domain(self):
        # Mock AI integration response
        mock_response = {
            "provider": "openai",
            "analysis": "Test analysis",
            "raw_response": {}
        }
        self.manager.ai_integration.analyze_vulnerability.return_value = mock_response
        
        # Test analysis with forced domain
        result = await self.manager.analyze_vulnerability(
            "Unknown Vulnerability",
            "Description of unknown vulnerability",
            force_domain="network_security"
        )
        
        # Check the result
        self.assertEqual(result["security_domain"], "network_security")
        self.assertEqual(result["model_used"], "model-network")
    
    def test_list_available_domains(self):
        # Test listing domains
        domains = self.manager.list_available_domains()
        
        # Check the result
        self.assertIsInstance(domains, list)
        self.assertEqual(len(domains), 3)
        self.assertIn("web_vulnerabilities", domains)
        self.assertIn("network_security", domains)
        self.assertIn("default", domains)
    
    def test_get_domain_model_map(self):
        # Test getting domain model map
        domain_map = self.manager.get_domain_model_map()
        
        # Check the result
        self.assertIsInstance(domain_map, dict)
        self.assertEqual(domain_map, self.sample_config)
        
        # Verify it's a copy, not the original
        domain_map["test"] = "test-model"
        self.assertNotIn("test", self.manager.domain_models)


if __name__ == "__main__":
    pytest.main(["-v", "test_multi_model_manager.py"])
