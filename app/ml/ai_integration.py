import os
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
import requests
from app.utils.logger import log_info, log_error

class AIIntegration:
    def __init__(self):
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize API keys from environment variables
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        
        if self.openai_api_key:
            self.client = AsyncOpenAI(api_key=self.openai_api_key)
            log_info("OpenAI API key loaded successfully")
        else:
            log_error("OpenAI API key not found in environment variables")

    async def analyze_vulnerability(self, title: str, description: str, provider: str = "openai") -> Dict[str, Any]:
        """
        Analyze vulnerability using external AI services
        Returns enhanced analysis including:
        - Severity assessment
        - Attack vector classification
        - Required skill level
        - Potential impact
        - Remediation suggestions
        """
        try:
            if provider == "openai" and self.openai_api_key:
                return await self._analyze_with_openai(title, description)
            elif provider == "deepseek" and self.deepseek_api_key:
                return await self._analyze_with_deepseek(title, description)
            else:
                raise ValueError(f"Provider {provider} not configured or unsupported")
        except Exception as e:
            log_error(f"AI analysis failed: {str(e)}")
            return None

    async def _analyze_with_openai(self, title: str, description: str) -> Dict[str, Any]:
        """Analyze vulnerability using OpenAI's GPT models"""
        try:
            prompt = f"""Analyze this vulnerability and provide a structured assessment:
            Title: {title}
            Description: {description}
            
            Provide analysis in the following format:
            - Severity (Critical/High/Medium/Low)
            - Attack Vector
            - Required Skill Level
            - Potential Impact
            - Recommended Fixes
            """

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a cybersecurity expert analyzing vulnerabilities."},
                    {"role": "user", "content": prompt}
                ]
            )

            analysis = response.choices[0].message.content
            log_info(f"OpenAI analysis completed for: {title}")
            return {
                "provider": "openai",
                "analysis": analysis,
                "raw_response": response.model_dump()
            }
        except Exception as e:
            log_error(f"OpenAI analysis failed: {str(e)}")
            raise

    async def _analyze_with_deepseek(self, title: str, description: str) -> Dict[str, Any]:
        """Analyze vulnerability using DeepSeek's API"""
        try:
            # Replace with actual DeepSeek API endpoint and implementation
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "title": title,
                "description": description,
                "analysis_type": "vulnerability"
            }
            
            # This is a placeholder - replace with actual DeepSeek API endpoint
            response = requests.post(
                "https://api.deepseek.ai/v1/analyze",
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                analysis = response.json()
                log_info(f"DeepSeek analysis completed for: {title}")
                return {
                    "provider": "deepseek",
                    "analysis": analysis,
                    "raw_response": response.json()
                }
            else:
                raise Exception(f"DeepSeek API error: {response.status_code}")
        except Exception as e:
            log_error(f"DeepSeek analysis failed: {str(e)}")
            raise

    async def generate_remediation_steps(self, vulnerability_type: str, context: str) -> str:
        """Generate detailed remediation steps using AI"""
        try:
            if not self.openai_api_key:
                return "AI service not configured"

            prompt = f"""As a security expert, provide detailed remediation steps for this vulnerability:
            Type: {vulnerability_type}
            Context: {context}
            
            Include:
            1. Immediate mitigation steps
            2. Long-term fixes
            3. Prevention measures
            4. Testing procedures to verify the fix
            """

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a cybersecurity expert providing remediation guidance."},
                    {"role": "user", "content": prompt}
                ]
            )

            return response.choices[0].message.content
        except Exception as e:
            log_error(f"Remediation generation failed: {str(e)}")
            return f"Error generating remediation steps: {str(e)}"

    async def chat(self, message: str) -> str:
        """Handle chat interactions with AI"""
        try:
            if not self.openai_api_key:
                return "AI service not configured. Please set OPENAI_API_KEY in your environment variables to enable chat functionality."

            if not hasattr(self, 'client'):
                self.client = AsyncOpenAI(api_key=self.openai_api_key)

            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are VulnLearnAI, an AI-powered cybersecurity assistant. You help users understand security concepts, analyze vulnerabilities, and learn about cybersecurity tools and best practices."},
                    {"role": "user", "content": message}
                ]
            )

            return response.choices[0].message.content
        except Exception as e:
            log_error(f"Chat interaction failed: {str(e)}")
            if "api_key" in str(e).lower():
                return "Invalid or expired OpenAI API key. Please check your OPENAI_API_KEY environment variable."
            return f"Error processing message: {str(e)}"

# Create global instance
ai_service = AIIntegration()
