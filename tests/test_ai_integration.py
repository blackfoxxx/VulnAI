#!/usr/bin/env python3
# filepath: /Users/mac/VulnAI/tests/test_ai_integration.py

import os
import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.ai_integration import AIIntegration

@pytest.fixture
def ai_integration():
    # Mock environment variables
    with patch.dict(os.environ, {"OPENAI_API_KEY": "mock-api-key", "DEEPSEEK_API_KEY": "mock-deepseek-key"}):
        return AIIntegration()

@pytest.mark.asyncio
async def test_analyze_vulnerability_openai(ai_integration):
    # Mock OpenAI API response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is a test analysis"
    mock_response.model_dump = MagicMock(return_value={"id": "test"})
    
    # Mock the chat.completions.create method
    ai_integration.client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # Call the method
    result = await ai_integration.analyze_vulnerability("Test Vulnerability", "This is a test", "openai")
    
    # Check the result
    assert result["provider"] == "openai"
    assert result["analysis"] == "This is a test analysis"
    assert "raw_response" in result

@pytest.mark.asyncio
async def test_analyze_vulnerability_invalid_provider(ai_integration):
    # Test with invalid provider
    result = await ai_integration.analyze_vulnerability("Test", "Test description", "invalid_provider")
    assert result is None

@pytest.mark.asyncio
async def test_generate_remediation_steps(ai_integration):
    # Mock OpenAI API response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Remediation steps"
    
    # Mock the chat.completions.create method
    ai_integration.client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # Call the method
    result = await ai_integration.generate_remediation_steps("SQL Injection", "Vulnerable login form")
    
    # Check the result
    assert result == "Remediation steps"

@pytest.mark.asyncio
async def test_chat(ai_integration):
    # Mock OpenAI API response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Chat response"
    
    # Mock the chat.completions.create method
    ai_integration.client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # Call the method
    result = await ai_integration.chat("Hello")
    
    # Check the result
    assert result == "Chat response"

if __name__ == "__main__":
    pytest.main(["-v"])
