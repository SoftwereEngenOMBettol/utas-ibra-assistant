# backend/main.py - Alternative version without reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI(
    title="UTAS Chatbot API",
    description="Backend API for UTAS Ibra Assistant",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from app.routes import auth_router, chat_router, admin_router

app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(admin_router)

@app.get("/")
async def root():
    return {"message": "UTAS Chatbot API is running", "status": "active"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        app,  # Pass the app object directly
        host="0.0.0.0",
        port=8000,
        reload=False  # Set reload to False to avoid the warning
    )