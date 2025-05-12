"""
API Endpoints for Admin Panel

This module provides endpoints for managing training data, checking model status, and triggering model training.
"""

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
import json
import os
from datetime import datetime
from app.ml.training_engine import engine
from app.utils.logger import log_error, log_info
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from html import escape

router = APIRouter()

class TrainingEntry(BaseModel):
    title: str
    description: str
    writeup_links: List[HttpUrl]
    cves: Optional[List[str]] = None
    metadata: dict = {}
    timestamp: str = datetime.now().isoformat()

class URLInput(BaseModel):
    url: HttpUrl

# Helper function to load admin token from environment
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "default_admin_token")

def load_training_data():
    data_file = "data/training_data.json"
    if not os.path.exists(data_file):
        os.makedirs(os.path.dirname(data_file), exist_ok=True)
        return []
    try:
        with open(data_file, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_training_data(entries):
    with open("data/training_data.json", "w") as f:
        json.dump(entries, f, indent=4)

@router.post("/training-data", summary="Add Training Data", description="Add a new training data entry for model training.")
async def add_training_data(
    entry: TrainingEntry,
    x_admin_token: str = Header(None)
):
    """
    Add a new training data entry.

    - **entry**: Training data entry details (title, description, writeup links, etc.)
    - **x_admin_token**: Admin token for authentication

    Returns:
    - Success message if the entry is added successfully.
    """
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized access")

    try:
        # Sanitize inputs to prevent XSS
        entry.title = escape(entry.title)
        entry.description = escape(entry.description)

        entries = load_training_data()
        entries.append(jsonable_encoder(entry))
        save_training_data(entries)
        return JSONResponse(content={"status": "success", "message": "Training data entry added successfully"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding training data: {str(e)}")

@router.get("/training-data", summary="Get Training Data", description="Retrieve all training data entries.")
async def get_training_data(
    x_admin_token: str = Header(None)
):
    """
    Retrieve all training data entries.

    - **x_admin_token**: Admin token for authentication

    Returns:
    - List of training data entries.
    """
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized access")

    try:
        entries = load_training_data()
        return {"status": "success", "entries": entries}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving training data: {str(e)}")

@router.get("/model-status")
async def model_status(x_admin_token: str = Header(None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized access")
    try:
        import json
        model_meta_path = "data/model/model_metadata.json"
        if os.path.exists(model_meta_path):
            with open(model_meta_path, "r") as f:
                metadata = json.load(f)
        else:
            metadata = {"status": "Model metadata not found"}

        # Add current model load status
        metadata["model_loaded"] = engine.load_models()

        return {"status": "success", "model_status": metadata}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get model status: {str(e)}")

@router.post("/train")
async def train_model_endpoint(x_admin_token: str = Header(None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized access")
    try:
        # Call the training engine's train_model method
        result = engine.train_model()
        log_info("Model training completed successfully")
        
        # Save metadata
        model_meta_path = "data/model/model_metadata.json"
        metadata = {
            "status": "success",
            "last_training": result,
            "updated_at": datetime.now().isoformat()
        }
        os.makedirs(os.path.dirname(model_meta_path), exist_ok=True)
        with open(model_meta_path, "w") as f:
            json.dump(metadata, f, indent=4)
        
        # Append to training update history
        history_file = "data/training_update_history.json"
        os.makedirs(os.path.dirname(history_file), exist_ok=True)
        try:
            with open(history_file, "r") as f:
                history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            history = []
        history.append(result)
        with open(history_file, "w") as f:
            json.dump(history, f, indent=4)
            
        return {"status": "success", "data": result}
    except Exception as e:
        log_error(f"Training failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")

@router.get("/training-update-history")
async def get_training_update_history(x_admin_token: str = Header(None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized access")
    try:
        history_file = "data/training_update_history.json"
        if not os.path.exists(history_file):
            return {"status": "success", "history": []}
        with open(history_file, "r") as f:
            history = json.load(f)
        return {"status": "success", "history": history}
    except Exception as e:
        log_error(f"Failed to get training update history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get training update history: {str(e)}")

@router.post("/summarize-url")
async def summarize_url(input: URLInput, x_admin_token: str = Header(None)):
    if x_admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized access")
    try:
        from app.ml.summarization import summarize_url as summarize_func
        summary = summarize_func(input.url)
        return {"status": "success", "summary": summary}
    except Exception as e:
        log_error(f"Error summarizing URL: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Summarization error: {str(e)}")
