# backend/app/models/auth_models.py

from pydantic import BaseModel
from typing import Optional

class LoginRequest(BaseModel):
    student_id: str
    password: str
    language: str = "en"

class ChatRequest(BaseModel):
    student_id: str
    session_token: str
    message: str
    language: str = "en"

class FeedbackRequest(BaseModel):
    student_id: str
    rating: int
    comment: Optional[str] = None

class UserResponse(BaseModel):
    student_id: str
    name: str
    email: str
    department: str
    is_admin: bool = False

class SessionResponse(BaseModel):
    session_token: str
    user: UserResponse