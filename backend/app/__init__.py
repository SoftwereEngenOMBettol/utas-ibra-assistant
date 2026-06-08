"""
UTAS Chatbot Backend Application
Main package initializer for the FastAPI application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Application metadata
__version__ = "1.0.0"
__author__ = "UTAS Ibra"
__description__ = "UTAS Ibra Assistant Chatbot API"

# Create FastAPI application instance
app = FastAPI(
    title="UTAS Ibra Assistant API",
    description="Backend API for UTAS Ibra College Chatbot Assistant",
    version=__version__,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register routers (will be populated after routes are created)
from app.routes import auth_router, chat_router, admin_router

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(admin_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint to check if API is running"""
    return {
        "message": "UTAS Ibra Assistant API is running",
        "version": __version__,
        "status": "active"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "utas-chatbot-api",
        "version": __version__
    }