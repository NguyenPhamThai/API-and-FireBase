from fastapi import APIRouter, HTTPException, status, Header
from typing import Optional

from ..schemas.chat_schema import MessageRequest, MessageResponse, ChatHistoryResponse, ChatMessage
from ..services import auth_service, chat_service

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_model=MessageResponse)
async def send_message(request: MessageRequest, authorization: Optional[str] = Header(None)):
    """
    Send a message and get response
    Requires Bearer token (Firebase ID token) in Authorization header
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    id_token = authorization.split(" ")[1]
    
    # Verify Firebase ID token
    user_data = auth_service.verify_id_token(id_token)
    user_id = user_data["uid"]
    
    if not request.message or request.message.strip() == "":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message cannot be empty"
        )
    
    # Process message and get response
    response = chat_service.process_message(request.message)
    
    # Save to database
    result = chat_service.save_chat(user_id, request.message, response)
    
    return MessageResponse(
        success=True,
        response=response,
        message_id=result["message_id"]
    )

@router.get("/messages", response_model=ChatHistoryResponse)
async def get_messages(authorization: Optional[str] = Header(None)):
    """
    Get chat history for current user
    Requires Bearer token (Firebase ID token) in Authorization header
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )
    
    id_token = authorization.split(" ")[1]
    
    # Verify Firebase ID token
    user_data = auth_service.verify_id_token(id_token)
    user_id = user_data["uid"]
    
    messages = chat_service.get_chat_history(user_id)
    
    chat_messages = [
        ChatMessage(
            id=msg["id"],
            message=msg["message"],
            response=msg["response"],
            timestamp=msg["timestamp"]
        )
        for msg in messages
    ]
    
    return ChatHistoryResponse(
        messages=chat_messages,
        total=len(chat_messages)
    )
