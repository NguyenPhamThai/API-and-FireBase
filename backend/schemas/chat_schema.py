from pydantic import BaseModel
from typing import List
from datetime import datetime

class MessageRequest(BaseModel):
    message: str

class MessageResponse(BaseModel):
    success: bool
    response: str
    message_id: int

class ChatMessage(BaseModel):
    id: int
    message: str
    response: str
    timestamp: str

class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessage]
    total: int
