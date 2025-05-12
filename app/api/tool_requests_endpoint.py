from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import os
from app.utils.logger import log_info, log_error
from datetime import datetime

router = APIRouter()

class ToolRequestResponse(BaseModel):
    id: str
    tool_id: str
    tool_name: str
    description: str
    status: str
    timestamp: str

class ToolRequestAction(BaseModel):
    request_id: str
    action: str  # approve, reject
    modifications: Optional[Dict[str, Any]] = None

@router.get("/tool-requests", response_model=List[ToolRequestResponse])
async def list_tool_requests(x_admin_token: str = Header(None)):
    """
    List all pending tool addition requests for administrator review.
    Requires admin authentication.
    """
    try:
        # Check admin token (simple implementation)
        if not x_admin_token or x_admin_token != os.getenv("ADMIN_TOKEN"):
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        tool_requests_path = "data/tool_requests.json"
        if not os.path.exists(tool_requests_path):
            return []
        
        with open(tool_requests_path, "r") as f:
            tool_requests = json.load(f)
        
        # Format for response
        response = []
        for idx, request in enumerate(tool_requests):
            response.append(ToolRequestResponse(
                id=str(idx),
                tool_id=request.get("tool_id", ""),
                tool_name=request.get("tool_data", {}).get("name", ""),
                description=request.get("tool_data", {}).get("description", ""),
                status=request.get("status", "pending"),
                timestamp=request.get("timestamp", "")
            ))
        
        return response
    except Exception as e:
        log_error(f"Error listing tool requests: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tool-requests/action")
async def handle_tool_request(request: ToolRequestAction, x_admin_token: str = Header(None)):
    """
    Approve or reject a tool addition request.
    Requires admin authentication.
    """
    try:
        # Check admin token
        if not x_admin_token or x_admin_token != os.getenv("ADMIN_TOKEN"):
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        tool_requests_path = "data/tool_requests.json"
        if not os.path.exists(tool_requests_path):
            raise HTTPException(status_code=404, detail="No tool requests found")
        
        with open(tool_requests_path, "r") as f:
            tool_requests = json.load(f)
        
        # Find the request
        try:
            idx = int(request.request_id)
            if idx < 0 or idx >= len(tool_requests):
                raise ValueError("Invalid request ID")
            tool_request = tool_requests[idx]
        except (ValueError, IndexError):
            raise HTTPException(status_code=404, detail="Tool request not found")
        
        # Update request status
        tool_request["status"] = "approved" if request.action == "approve" else "rejected"
        tool_request["action_timestamp"] = datetime.now().isoformat()
        
        # If approving, add the tool to tools_metadata.json
        if request.action == "approve":
            tools_metadata_path = "tools/tools_metadata.json"
            with open(tools_metadata_path, "r") as f:
                tools_metadata = json.load(f)
            
            tool_id = tool_request["tool_id"]
            tool_data = tool_request["tool_data"]
            
            # Apply any admin modifications
            if request.modifications:
                for key, value in request.modifications.items():
                    if key in tool_data:
                        tool_data[key] = value
            
            # Add the tool
            tools_metadata[tool_id] = tool_data
            
            with open(tools_metadata_path, "w") as f:
                json.dump(tools_metadata, f, indent=4)
            
            log_info(f"Tool '{tool_id}' added to the system")
        
        # Save updated requests
        with open(tool_requests_path, "w") as f:
            json.dump(tool_requests, f, indent=4)
        
        return {
            "status": "success", 
            "action": request.action, 
            "tool_id": tool_request["tool_id"]
        }
    except Exception as e:
        log_error(f"Error handling tool request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
