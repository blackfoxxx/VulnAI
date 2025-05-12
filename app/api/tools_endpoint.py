from fastapi import APIRouter, Header, HTTPException
import json
import os
from app.utils.logger import log_info, log_error

router = APIRouter()

@router.get("/tools/list")
async def list_tools():
    """
    Get a list of all available security tools with their metadata
    for display in the chat interface.
    """
    try:
        tools_metadata_path = "tools/tools_metadata.json"
        
        # Check if the tools metadata file exists
        if not os.path.exists(tools_metadata_path):
            log_error(f"Tools metadata file not found: {tools_metadata_path}")
            return {"tools": []}
        
        # Load tools metadata
        with open(tools_metadata_path, "r") as f:
            tools_metadata = json.load(f)
        
        # Format tools for frontend display
        tools_list = []
        for tool_id, tool_data in tools_metadata.items():
            tools_list.append({
                "id": tool_id,
                "name": tool_data.get("name", tool_id),
                "description": tool_data.get("description", ""),
                "category": tool_data.get("category", "general"),
                "example": tool_data.get("usage_example", f"Run {tool_id} on example.com")
            })
        
        return {"tools": tools_list}
        
    except Exception as e:
        log_error(f"Error fetching tools list: {str(e)}")
        return {"tools": [], "error": str(e)}
