from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from pathlib import Path

from .routers import auth, chat
from . import database

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(
    title="Chat Application API",
    description="University Assignment - Chat App with Firebase Auth",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize database
database.init_db()

# Add CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Chat Application API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
