from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from app.ml.ai_integration import ai_service
import json
import os
import re
from datetime import datetime
import subprocess
from app.utils.logger import log_info, log_error

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat_endpoint(request: ChatRequest, x_admin_token: str = Header(None)):
    if not request.message:
        return {"reply": "Please provide a message."}

    try:
        # Check if the message might be a tool command or add tool request
        tool_info = await detect_tool_command(request.message)
        
        if tool_info:
            # Check if it's a tool addition request
            if tool_info.get("is_add_tool_request", False):
                # Handle tool addition request
                tool_name = tool_info.get("tool_name", "")
                return await handle_add_tool_request(request.message, tool_name)
            
            # Execute the detected tool
            tool_output = await execute_tool(tool_info["tool_name"], tool_info["parameters"])
            
            # Get AI to analyze the tool output
            ai_analysis = await ai_service.learn_from_tool_output({
                "tool_name": tool_info["tool_name"],
                "parameters": tool_info["parameters"],
                "output": tool_output
            })
            
            # Return both the tool execution result and AI analysis
            return {
                "reply": ai_analysis,
                "tool_execution": {
                    "tool_name": tool_info["tool_name"],
                    "parameters": tool_info["parameters"],
                    "output": tool_output
                }
            }
        else:
            # More advanced detection with AI
            ai_intent = await ai_service.detect_tool_intention(request.message, [])
            if ai_intent.get("is_add_tool_request", False):
                return await handle_add_tool_request(request.message, 
                                                  ai_intent.get("new_tool_info", {}).get("name", ""))
            
            # Regular chat processing
            reply = await ai_service.chat(request.message)
            return {"reply": reply}
            
    except Exception as e:
        error_msg = str(e)
        log_error(f"Chat processing error: {error_msg}")
        if "api_key" in error_msg.lower():
            return {"reply": "Invalid or expired OpenAI API key. Please check your OPENAI_API_KEY environment variable."}
        return {"reply": f"Error processing message: {error_msg}"}

async def detect_tool_command(message):
    """
    Detect if a message is attempting to invoke a tool or add a new tool.
    Returns the tool name and parameters if detected, otherwise None.
    """
    try:
        # Load available tools
        tools_metadata_path = "tools/tools_metadata.json"
        with open(tools_metadata_path, "r") as f:
            tools_metadata = json.load(f)
        
        # Check for add tool request patterns
        add_tool_patterns = [
            r"(?i)add (?:a |the |new )(?:tool|scanner|security tool)(?: called| named)? ([^\s,]+)",
            r"(?i)install (?:a |the |new )(?:tool|scanner|security tool)(?: called| named)? ([^\s,]+)",
            r"(?i)create (?:a |the |new )(?:tool|scanner|security tool)(?: called| named)? ([^\s,]+)"
        ]
        
        for pattern in add_tool_patterns:
            match = re.search(pattern, message)
            if match:
                tool_name = match.group(1).strip()
                # Pass to the tool addition handler
                return {
                    "is_add_tool_request": True,
                    "tool_name": tool_name
                }
        
        # Common command patterns for using existing tools
        patterns = [
            r"(?i)run\s+(\w+)(?:\s+on)?\s+(.*)",
            r"(?i)execute\s+(\w+)(?:\s+on)?\s+(.*)",
            r"(?i)use\s+(\w+)(?:\s+to\s+scan|check|analyze)?\s+(.*)",
            r"(?i)scan\s+(.*?)(?:\s+with\s+(\w+)|$)",
            r"(?i)analyze\s+(.*?)(?:\s+with\s+(\w+)|$)",
            r"(?i)check\s+(.*?)(?:\s+with\s+(\w+)|$)"
        ]
        
        # First try explicit command patterns
        for pattern in patterns:
            match = re.search(pattern, message)
            if match:
                groups = match.groups()
                tool_name = None
                target = None
                
                # Handle different pattern formats
                if len(groups) >= 2:
                    if pattern.startswith(r"(?i)scan") or pattern.startswith(r"(?i)analyze") or pattern.startswith(r"(?i)check"):
                        target = groups[0].strip()
                        tool_name = groups[1].strip() if groups[1] else get_default_tool_for_action(pattern)
                    else:
                        tool_name = groups[0].strip()
                        target = groups[1].strip()
                
                if tool_name:
                    # Normalize tool name
                    normalized_tool_name = find_matching_tool(tool_name, tools_metadata)
                    
                    if normalized_tool_name:
                        # Extract parameters based on the tool
                        parameters = extract_parameters(normalized_tool_name, target, tools_metadata)
                        return {
                            "tool_name": normalized_tool_name,
                            "parameters": parameters
                        }
        
        # Try natural language pattern matching if explicit patterns didn't match
        for tool_name, tool_info in tools_metadata.items():
            if "natural_language_patterns" in tool_info:
                for nl_pattern in tool_info["natural_language_patterns"]:
                    if nl_pattern.lower() in message.lower():
                        # Try to extract a target from the message
                        target = extract_target_from_message(message)
                        if target:
                            parameters = extract_parameters(tool_name, target, tools_metadata)
                            return {
                                "tool_name": tool_name,
                                "parameters": parameters
                            }
        
        # More advanced detection: Ask AI to interpret if it's a tool request
        is_tool_command = await ai_service.detect_tool_intention(message, list(tools_metadata.keys()))
        if is_tool_command and is_tool_command.get("is_tool_command", False):
            return {
                "tool_name": is_tool_command["tool_name"],
                "parameters": is_tool_command["parameters"]
            }
        
        return None
    except Exception as e:
        log_error(f"Error detecting tool command: {str(e)}")
        return None

def extract_target_from_message(message):
    """Extract a target (URL, domain, IP) from a message using regex patterns"""
    # Try to find URLs
    url_pattern = r'https?://[^\s]+'
    url_match = re.search(url_pattern, message)
    if url_match:
        return url_match.group(0)
    
    # Try to find domains
    domain_pattern = r'(?<![/@])[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?'
    domain_match = re.search(domain_pattern, message)
    if domain_match:
        return domain_match.group(0)
    
    # Try to find IP addresses
    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    ip_match = re.search(ip_pattern, message)
    if ip_match:
        return ip_match.group(0)
    
    return None

def get_default_tool_for_action(action_pattern):
    """Return a default tool based on the action type"""
    if "scan" in action_pattern:
        return "nuclei"
    elif "analyze" in action_pattern:
        return "whatweb"
    elif "check" in action_pattern:
        return "nmap"
    return None

def find_matching_tool(tool_name, tools_metadata):
    """Find a matching tool from available tools based on partial name"""
    tool_name = tool_name.lower()
    
    # Exact match
    if tool_name in tools_metadata:
        return tool_name
    
    # Partial match
    for key in tools_metadata:
        if tool_name in key.lower() or key.lower() in tool_name:
            return key
    
    return None

def extract_parameters(tool_name, target, tools_metadata):
    """Extract parameters for a specific tool based on the target"""
    tool_metadata = tools_metadata.get(tool_name, {})
    param_template = tool_metadata.get("parameter_template", {})
    
    # Handle complex parameter extraction
    if "url" in param_template:
        # Clean up URL if needed
        if target and not (target.startswith("http://") or target.startswith("https://")):
            target = f"https://{target}"
        return {"url": target}
    elif "target" in param_template:
        return {"target": target}
    elif "domain" in param_template:
        # Extract domain from URL if needed
        if target and (target.startswith("http://") or target.startswith("https://")):
            import re
            domain_match = re.search(r"https?://([^/]+)", target)
            if domain_match:
                target = domain_match.group(1)
        return {"domain": target}
    else:
        # Default parameter name based on tool
        default_param = tool_metadata.get("default_param", "target")
        return {default_param: target}

async def execute_tool(tool_name, parameters):
    """Execute a security tool with the given parameters"""
    try:
        # Load tools metadata
        tools_metadata_path = "tools/tools_metadata.json"
        with open(tools_metadata_path, "r") as f:
            tools_metadata = json.load(f)

        # Find the requested tool
        if tool_name not in tools_metadata:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found.")

        tool_metadata = tools_metadata[tool_name]
        command = tool_metadata["command"]

        # Replace placeholders in the command with provided parameters
        for key, value in parameters.items():
            command = command.replace(f"{{{key}}}", value)

        # Execute the tool command
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            log_error(f"Tool execution failed: {result.stderr}")
            return f"Error executing {tool_name}: {result.stderr}"

        # Log tool output for AI learning
        tool_log_path = "data/tool_outputs.json"
        tool_log_entry = {
            "tool_name": tool_name,
            "parameters": parameters,
            "output": result.stdout,
            "timestamp": datetime.now().isoformat()
        }

        # Append the log entry to the tool outputs file
        if os.path.exists(tool_log_path):
            with open(tool_log_path, "r") as f:
                tool_logs = json.load(f)
        else:
            tool_logs = []

        tool_logs.append(tool_log_entry)

        with open(tool_log_path, "w") as f:
            json.dump(tool_logs, f, indent=4)

        return result.stdout

    except Exception as e:
        log_error(f"Tool execution error: {str(e)}")
        return f"Error: {str(e)}"

async def handle_add_tool_request(message, tool_name):
    """
    Handle a request to add a new tool.
    Guides the user through the process of adding a new tool.
    """
    try:
        # Check if tool name already exists
        tools_metadata_path = "tools/tools_metadata.json"
        with open(tools_metadata_path, "r") as f:
            tools_metadata = json.load(f)
        
        if tool_name.lower() in [name.lower() for name in tools_metadata.keys()]:
            return {
                "reply": f"A tool with the name '{tool_name}' already exists in our system. Would you like to modify it instead? If so, please provide the details you'd like to update."
            }
        
        # Ask AI to extract potential tool information from the message
        tool_info = await ai_service.extract_tool_info(message)
        
        if tool_info:
            missing_fields = []
            required_fields = ["command", "description"]
            
            for field in required_fields:
                if not tool_info.get(field):
                    missing_fields.append(field)
            
            if missing_fields:
                # We need more information
                fields_list = ", ".join(missing_fields)
                return {
                    "reply": f"I'd be happy to add the tool '{tool_name}' to our system. To proceed, I'll need some additional information:\n\n" +
                             f"1. {fields_list}\n\n" +
                             f"Please provide these details so I can properly configure the tool."
                }
            
            # We have enough information to add the tool
            # Generate a tool_id from the name
            tool_id = tool_name.lower().replace(" ", "_")
            
            # Create the new tool metadata
            new_tool = {
                "name": tool_name,
                "description": tool_info.get("description", ""),
                "command": tool_info.get("command", ""),
                "expected_output": tool_info.get("expected_output", "Tool output"),
                "category": tool_info.get("category", "custom"),
                "usage_example": f"Run {tool_name} on example.com",
                "parameter_template": {
                    "target": "example.com"
                },
                "default_param": "target"
            }
            
            # Add natural language patterns if provided
            if tool_info.get("nl_patterns"):
                new_tool["natural_language_patterns"] = tool_info.get("nl_patterns")
            
            # Log the request for admin review
            tool_requests_path = "data/tool_requests.json"
            tool_request = {
                "tool_id": tool_id,
                "tool_data": new_tool,
                "user_message": message,
                "timestamp": datetime.now().isoformat(),
                "status": "pending"
            }
            
            if os.path.exists(tool_requests_path):
                with open(tool_requests_path, "r") as f:
                    tool_requests = json.load(f)
            else:
                tool_requests = []
            
            tool_requests.append(tool_request)
            
            with open(tool_requests_path, "w") as f:
                json.dump(tool_requests, f, indent=4)
            
            return {
                "reply": f"Thank you for providing the details for '{tool_name}'. Your request to add this tool has been submitted for administrator review. Once approved, the tool will be available through this chat interface. In the meantime, you can continue to use any of our existing tools."
            }
        else:
            # No specific tool information found
            return {
                "reply": f"I understand you'd like to add a new tool called '{tool_name}'. To add this tool, I need some information:\n\n" +
                         f"1. What command should be executed when this tool is used?\n" +
                         f"2. What does this tool do? (A brief description)\n" +
                         f"3. What category does this tool belong to? (e.g., web_security, network, forensics)\n\n" +
                         f"Please provide this information and I'll help set up the tool."
            }
    except Exception as e:
        log_error(f"Error handling add tool request: {str(e)}")
        return {
            "reply": f"I encountered an error while processing your request to add a new tool. Please try again with more details about the tool, or contact an administrator for assistance."
        }

class ToolExecutionRequest(BaseModel):
    tool_name: str
    parameters: dict

@router.post("/chat/tool")
async def execute_tool_via_chat(request: ToolExecutionRequest):
    """Execute a tool dynamically via chat."""
    try:
        result = await execute_tool(request.tool_name, request.parameters)
        return {"status": "success", "output": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
