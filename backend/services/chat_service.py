from .. import database
import re

def process_message(user_message: str) -> str:
    """
    Process user message and generate response
    Mock AI response for demo
    """
    message_lower = user_message.lower()
    
    if "hello" in message_lower or "hi" in message_lower:
        return "Hi there! How can I help you today?"
    elif "how are you" in message_lower:
        return "I'm doing great, thanks for asking! How about you?"
    elif "what is your name" in message_lower or "who are you" in message_lower:
        return "I'm a chat bot. I'm here to assist you with your questions!"
    elif "bye" in message_lower or "goodbye" in message_lower:
        return "Goodbye! Have a wonderful day!"
    elif "thank" in message_lower:
        return "You're welcome! Happy to help!"
    else:
        return f"You said: '{user_message}'. I'm learning to respond better each day!"

def save_chat(user_id: str, message: str, response: str) -> dict:
    """Save chat message and response to database"""
    message_id = database.save_message(user_id, message, response)
    return {
        "message_id": message_id,
        "success": True
    }

def get_chat_history(user_id: str) -> list:
    """Retrieve chat history for user"""
    messages = database.get_user_messages(user_id)
    return messages
