from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LoginRequest(BaseModel):
    student_id: str
    password: str
    language: str = "en"

class ChatRequest(BaseModel):
    student_id: str
    session_token: str
    message: str
    language: str = "en"

class FQACreate(BaseModel):
    question_ar: str
    question_en: str
    answer_ar: Optional[str] = None
    answer_en: Optional[str] = None
    category: Optional[str] = None
    attachment_type: Optional[str] = None
    attachment_content: Optional[str] = None

class FeedbackRequest(BaseModel):
    student_id: str
    rating: int
    comment: Optional[str] = None
    