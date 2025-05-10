from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from app.ml.ai_integration import ai_service

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat_endpoint(request: ChatRequest, x_admin_token: str = Header(None)):
    if not request.message:
        return {"reply": "Please provide a message."}

    try:
        # Call AI service to get chat response
        reply = await ai_service.chat(request.message)
        return {"reply": reply}
    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower():
            return {"reply": "Invalid or expired OpenAI API key. Please check your OPENAI_API_KEY environment variable."}
        return {"reply": f"Error processing message: {error_msg}"}
