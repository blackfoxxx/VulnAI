import os
from typing import Optional, Dict, Any, List
from openai import OpenAI, AsyncOpenAI
import requests
import json
from app.utils.logger import log_info, log_error

class AIIntegration:
    def __init__(self):
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Initialize API keys from environment variables
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        
        # Load model configuration
        self.models = self._load_model_config()
        
        if self.openai_api_key:
            self.client = AsyncOpenAI(api_key=self.openai_api_key)
            log_info("OpenAI API key loaded successfully")
        else:
            log_error("OpenAI API key not found in environment variables")
            
    def _load_model_config(self) -> Dict[str, str]:
        """Load model configuration from the config file."""
        config_file = "config/domain_models.json"
        default_models = {
            "default": "ft:gpt-4o-2024-08-06:personal::BWAukKEO",
            "tools_model": "ft:gpt-4o-2024-08-06:personal::BWAukKEO"
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, "r") as f:
                    return json.load(f)
            return default_models
        except Exception as e:
            log_error(f"Failed to load model config: {str(e)}")
            return default_models

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
                model="ft:gpt-4o-2024-08-06:personal::BWAukKEO",  # Use the fine-tuned model
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
                model="ft:gpt-4o-2024-08-06:personal::BWAukKEO",
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
                model="ft:gpt-4o-2024-08-06:personal::BWAukKEO",
                messages=[
                    {"role": "system", "content": "You are VulnLearnAI, an AI-powered cybersecurity assistant. You help users understand security concepts, analyze vulnerabilities, and learn about cybersecurity tools and best practices. You can recommend security tools when appropriate and explain how to use them."},
                    {"role": "user", "content": message}
                ]
            )

            return response.choices[0].message.content
        except Exception as e:
            log_error(f"Chat interaction failed: {str(e)}")
            if "api_key" in str(e).lower():
                return "Invalid or expired OpenAI API key. Please check your OPENAI_API_KEY environment variable."
            return f"Error processing message: {str(e)}"
            
    async def detect_tool_intention(self, message: str, available_tools: List[str]) -> Dict[str, Any]:
        """
        Determine if a message is intending to use a tool, and extract parameters.
        Also detects if the user is requesting to add a new tool.
        
        Args:
            message: The user message
            available_tools: List of available tool names
            
        Returns:
            Dictionary with:
              - is_tool_command: boolean
              - tool_name: string (if is_tool_command is True)
              - parameters: dict (if is_tool_command is True)
              - is_add_tool_request: boolean (if user is requesting to add a new tool)
              - new_tool_info: dict (if user is providing info about a new tool)
        """
        try:
            if not self.openai_api_key:
                return {"is_tool_command": False}

            if not hasattr(self, 'client'):
                self.client = AsyncOpenAI(api_key=self.openai_api_key)
            
            # Load tools metadata to provide more context
            tools_metadata_path = "tools/tools_metadata.json"
            tool_descriptions = {}
            try:
                with open(tools_metadata_path, "r") as f:
                    tools_data = json.load(f)
                    for tool_id, tool_info in tools_data.items():
                        tool_descriptions[tool_id] = {
                            "description": tool_info.get("description", ""),
                            "examples": tool_info.get("usage_example", f"Run {tool_id}")
                        }
            except Exception as e:
                log_error(f"Failed to load tools metadata: {str(e)}")
                
            # Create a more detailed context about available tools
            tools_context = []
            for tool in available_tools:
                desc = tool_descriptions.get(tool, {}).get("description", "")
                example = tool_descriptions.get(tool, {}).get("examples", "")
                tools_context.append(f"- {tool}: {desc}. Example: {example}")
                
            tools_str = "\n".join(tools_context)
                
            prompt = f"""Determine if this message is intending to use a security tool, add a new security tool, or is just a general question.
            
            Available tools and their purposes:
            {tools_str}
            
            User message: "{message}"
            
            First, determine what the user is trying to do:
            1. If they want to use an existing tool from the available list, identify which tool and what parameters they're providing.
            2. If they're asking to add a new tool, identify that they want to add a tool and extract any information about the tool they're providing.
            3. If they're just asking a security question, set is_tool_command and is_add_tool_request to false.
            
            Respond in this JSON format only:
            {{
                "is_tool_command": true/false,
                "tool_name": "name_of_tool" (if attempting to use a tool),
                "parameters": {{"key": "value"}} (if attempting to use a tool),
                "is_add_tool_request": true/false,
                "new_tool_info": {{
                    "name": "tool name" (if provided),
                    "description": "tool description" (if provided),
                    "command": "command to run the tool" (if provided),
                    "category": "tool category" (if provided)
                }} (only if is_add_tool_request is true)
            }}
            
            Just respond with the JSON, nothing else."""

            # Import the multi_model_manager here to avoid circular imports
            from app.ml.multi_model_manager import multi_model_manager
            
            # Let the multi_model_manager decide if this is a tool-related query
            model_id = multi_model_manager.select_model_for_request(message)

            response = await self.client.chat.completions.create(
                model=model_id,
                messages=[
                    {"role": "system", "content": "You are a security tool parser. You determine if a message is intending to use a tool, and extract parameters."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            try:
                result = json.loads(result_text)
                return result
            except json.JSONDecodeError:
                log_error(f"Could not parse JSON response from AI: {result_text}")
                return {"is_tool_command": False}
        except Exception as e:
            log_error(f"Tool intention detection failed: {str(e)}")
            return {"is_tool_command": False}

    async def learn_tool_usage(self, tool_metadata: Dict[str, Any]) -> str:
        """
        Learn how to use a tool based on its metadata.
        This includes understanding its purpose, command, and expected output.
        """
        try:
            tool_name = tool_metadata.get("name", "Unknown Tool")
            description = tool_metadata.get("description", "No description available.")
            command = tool_metadata.get("command", "No command provided.")
            expected_output = tool_metadata.get("expected_output", "No expected output specified.")

            prompt = f"""
            You are an AI assistant.            Learn how to use the following tool:

            Tool Name: {tool_name}
            Description: {description}
            Command: {command}
            Expected Output: {expected_output}

            Summarize the tool's purpose and provide a step-by-step guide on how to use it effectively.
            """

            if self.openai_api_key:
                response = await self.client.chat.completions.create(
                    model="ft:gpt-4o-2024-08-06:personal::BWAukKEO",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content
            else:
                raise ValueError("OpenAI API key is not configured.")
        except Exception as e:
            log_error(f"Failed to learn tool usage: {str(e)}")
            return "Error: Unable to process the tool metadata."

    async def learn_from_tool_output(self, tool_output: dict):
        """
        Process and learn from a tool's output.
        Provides security analysis and insights based on the tool results.
        """
        try:
            # Extract relevant information from the tool output
            tool_name = tool_output.get("tool_name", "Unknown Tool")
            parameters = tool_output.get("parameters", {})
            output = tool_output.get("output", "")

            # Format parameters for display
            params_str = ""
            for key, value in parameters.items():
                params_str += f"\n- {key}: {value}"
            
            # Load additional context about the tool
            tool_context = ""
            try:
                with open("tools/tools_metadata.json", "r") as f:
                    tools_metadata = json.load(f)
                    if tool_name in tools_metadata:
                        tool_info = tools_metadata[tool_name]
                        tool_context = f"""
                        Tool Description: {tool_info.get('description', 'No description available')}
                        Expected Output: {tool_info.get('expected_output', 'No expected output information available')}
                        """
            except Exception as e:
                log_error(f"Failed to load tool metadata: {str(e)}")

            # Use AI to analyze the output and improve decision-making
            prompt = f"""
            Analyze the following security tool output and provide insights:

            Tool Name: {tool_name}
            {tool_context}
            Parameters: {params_str if params_str else "None"}
            
            Tool Output:
            ```
            {output[:4000]}  # Limit to prevent token overflow
            ```

            Provide a concise analysis in these sections:
            1. FINDINGS: What vulnerabilities or issues were found (if any)
            2. SEVERITY: The severity of any findings (Critical/High/Medium/Low/None)
            3. IMPACT: What these results mean for the system's security
            4. RECOMMENDATIONS: Specific next steps or remediation actions
            5. ADDITIONAL TESTS: What other security tools or tests would be valuable to run next

            Format your response in a clear, security-focused way that highlights the most important information first.
            If the tool found no issues, clearly state that, but still provide context on what was checked and suggestions for additional security measures.
            """

            if self.openai_api_key:
                # Import the multi_model_manager here to avoid circular imports
                from app.ml.multi_model_manager import multi_model_manager
                
                # Always use the tools model for analyzing tool outputs
                model_id = multi_model_manager.get_model_for_domain("tools_model")
                
                response = await self.client.chat.completions.create(
                    model=model_id,
                    messages=[
                        {"role": "system", "content": "You are a cybersecurity expert analyzing security tool outputs. Provide concise, actionable insights."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content
            else:
                raise ValueError("OpenAI API key is not configured.")
        except Exception as e:
            log_error(f"Failed to learn from tool output: {str(e)}")
            return "I've processed the tool output but encountered an error during analysis. Please review the raw output for details."

    async def extract_tool_info(self, message: str) -> Dict[str, Any]:
        """
        Extract information about a new tool from a message.
        
        Args:
            message: The user message containing tool information
            
        Returns:
            Dictionary with tool information (name, description, command, etc.)
        """
        try:
            if not self.openai_api_key:
                return None

            if not hasattr(self, 'client'):
                self.client = AsyncOpenAI(api_key=self.openai_api_key)
                
            prompt = f"""Extract information about a security tool from this message:
            
            Message: "{message}"
            
            Look for the following details:
            1. Tool name
            2. Description (what the tool does)
            3. Command (how to run the tool)
            4. Expected output (what the tool returns)
            5. Category (e.g., web_security, network, forensics)
            6. Natural language patterns (phrases that would indicate someone wants to use this tool)
            
            Respond in this JSON format:
            {{
                "name": "name of the tool",
                "description": "what the tool does",
                "command": "how to run the tool (include parameter placeholders like {{url}} or {{target}})",
                "expected_output": "what the tool returns",
                "category": "tool category",
                "nl_patterns": ["phrase 1", "phrase 2", ...]
            }}
            
            If any field is not mentioned in the message, omit it from the JSON.
            """

            response = await self.client.chat.completions.create(
                model="ft:gpt-4o-2024-08-06:personal::BWAukKEO",
                messages=[
                    {"role": "system", "content": "You are a security tool parser. You extract information about security tools from user messages."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            try:
                result = json.loads(result_text)
                return result
            except json.JSONDecodeError:
                log_error(f"Could not parse JSON response from AI: {result_text}")
                return None
        except Exception as e:
            log_error(f"Tool information extraction failed: {str(e)}")
            return None

# Create global instance
ai_service = AIIntegration()
