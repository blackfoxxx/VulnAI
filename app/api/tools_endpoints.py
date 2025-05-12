from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.tools.manager import ToolsManager
from app.utils.logger import log_info, log_error
from app.ml.url_scanner import fetch_url_text
from app.ml.training_engine import engine
import json
import os

router = APIRouter()
tools_manager = ToolsManager()

class ToolInstallRequest(BaseModel):
    name: str
    git_repo_url: Optional[str] = None
    install_commands: Optional[List[str]] = None
    description: Optional[str] = None
    category: Optional[str] = None
    use_preconfigured: bool = False

class URLTestRequest(BaseModel):
    url: str

class ToolRegistrationRequest(BaseModel):
    name: str
    description: str
    command: str
    expected_output: str
    git_repo_url: Optional[str] = None
    usage_examples: Optional[List[str]] = None
    parameter_template: Optional[Dict[str, Any]] = None

@router.get("/list")
async def list_tools():
    """List all available security tools"""
    try:
        # Load tools metadata
        tools_metadata_path = "tools/tools_metadata.json"
        if not os.path.exists(tools_metadata_path):
            return {"tools": []}
            
        with open(tools_metadata_path, "r") as f:
            tools_metadata = json.load(f)
        
        # Format tools for display
        formatted_tools = []
        for tool_id, tool_info in tools_metadata.items():
            formatted_tools.append({
                "id": tool_id,
                "name": tool_info.get("name", tool_id),
                "description": tool_info.get("description", "No description available"),
                "example": tool_info.get("usage_example", f"Run {tool_info.get('name', tool_id)} on example.com"),
                "category": tool_info.get("category", "General")
            })
            
        return {"tools": formatted_tools}
    except Exception as e:
        log_error(f"Error listing tools: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error listing tools: {str(e)}")

@router.post("/install")
async def install_tool(
    request: ToolInstallRequest,
    x_admin_token: str = Header(None)
):
    """Install a new security tool"""
    try:
        result = tools_manager.install_tool(
            request.name,
            request.git_repo_url,
            request.install_commands
        )
        log_info(f"Tool installation: {result}")
        return {"status": "success", "message": result}
    except Exception as e:
        log_error(f"Tool installation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/urltest")
async def url_test(
    request: URLTestRequest,
    x_admin_token: str = Header(None)
):
    """Test a URL using AI-based vulnerability classification"""
    try:
        # Fetch URL content
        text = fetch_url_text(request.url)
        if text.startswith("Error"):
            raise Exception(text)
        
        # Use AI classification engine
        # For demo, use title as URL and description as fetched text
        result = await engine.classify_vulnerability(
            title=f"URL Scan: {request.url}",
            description=text
        )
        return {"status": "success", "analysis": result}
    except Exception as e:
        log_error(f"URL test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preconfigured")
async def list_preconfigured_tools(
    x_admin_token: str = Header(None)
):
    """List all preconfigured tools available for installation"""
    try:
        tools = tools_manager.get_preconfigured_tools()
        return {"status": "success", "tools": tools}
    except Exception as e:
        log_error(f"Failed to list preconfigured tools: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list")
async def list_tools(
    x_admin_token: str = Header(None)
):
    """List all installed tools"""
    try:
        installed_tools = tools_manager.list_tools()
        preconfigured_tools = tools_manager.get_preconfigured_tools()
        
        # Enhance installed tools info with preconfigured data
        for name, info in installed_tools.items():
            if name in preconfigured_tools:
                info.update({
                    "description": preconfigured_tools[name]["description"],
                    "category": preconfigured_tools[name]["category"]
                })
        
        return {
            "status": "success",
            "tools": installed_tools
        }
    except Exception as e:
        log_error(f"Failed to list tools: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{tool_name}")
async def remove_tool(
    tool_name: str,
    x_admin_token: str = Header(None)
):
    """Remove an installed tool"""
    try:
        result = tools_manager.remove_tool(tool_name)
        log_info(f"Tool removal: {result}")
        return {"status": "success", "message": result}
    except Exception as e:
        log_error(f"Tool removal failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/wordlists/add")
async def add_wordlist(
    name: str,
    url: str,
    x_admin_token: str = Header(None)
):
    """Add a new wordlist"""
    try:
        # TODO: Implement wordlist download and management
        return {"status": "success", "message": f"Wordlist {name} added"}
    except Exception as e:
        log_error(f"Failed to add wordlist: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/register-tool")
async def register_tool(request: ToolRegistrationRequest):
    """Register a new tool dynamically."""
    try:
        # Load existing tools metadata
        tools_metadata_path = "tools/tools_metadata.json"
        with open(tools_metadata_path, "r") as f:
            tools_metadata = json.load(f)

        # Add the new tool to the metadata
        tools_metadata[request.name.lower().replace(" ", "_")] = {
            "name": request.name,
            "description": request.description,
            "command": request.command,
            "expected_output": request.expected_output,
            "git_repo_url": request.git_repo_url
        }

        # Save the updated metadata
        with open(tools_metadata_path, "w") as f:
            json.dump(tools_metadata, f, indent=4)

        # Optionally clone the repository and install dependencies
        if request.git_repo_url:
            tools_manager.clone_and_install_tool(request.git_repo_url)

        log_info(f"Tool registered successfully: {request.name}")
        return {"status": "success", "message": f"Tool '{request.name}' registered successfully."}

    except Exception as e:
        log_error(f"Tool registration failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
