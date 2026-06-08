# backend/app/models/fqa_models.py

from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date

class FQACreate(BaseModel):
    question_ar: str
    question_en: str
    answer_ar: Optional[str] = None
    answer_en: Optional[str] = None
    category: Optional[str] = None
    attachment_type: Optional[str] = None
    attachment_content: Optional[str] = None
    # Date fields for academic tracking
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    is_active: Optional[bool] = True

class FQAResponse(BaseModel):
    id: int
    question_ar: str
    question_en: str
    answer_ar: str
    answer_en: str
    category: str
    created_at: datetime
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    is_active: bool
    effective_date: Optional[datetime] = None
    source_type: Optional[str] = None
    source_name: Optional[str] = None
    created_by: Optional[str] = None

class FQAUpdate(BaseModel):
    question_ar: Optional[str] = None
    question_en: Optional[str] = None
    answer_ar: Optional[str] = None
    answer_en: Optional[str] = None
    category: Optional[str] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    academic_year: Optional[str] = None
    semester: Optional[str] = None
    is_active: Optional[bool] = None

class FQABatchGenerate(BaseModel):
    content: str
    content_type: str
    category: str
    num_questions: int = 5

class UnansweredQuestionResponse(BaseModel):
    """Model for unanswered questions from students"""
    id: int
    student_id: str
    student_name: str
    question: str
    language: str
    asked_at: datetime
    status: str
    answer_faq_id: Optional[int] = None
    answered_at: Optional[datetime] = None

class CategoryCreate(BaseModel):
    name_ar: str
    name_en: str
    description_ar: Optional[str] = None
    description_en: Optional[str] = None

class CategoryResponse(BaseModel):
    id: int
    name_ar: str
    name_en: str
    description_ar: Optional[str] = None
    description_en: Optional[str] = None
    created_at: datetime
    faq_count: Optional[int] = 0

class ConversationResponse(BaseModel):
    """Model for conversation responses"""
    id: int
    type: str  # greeting, how_are_you, thanks, goodbye, default
    language: str  # en, ar
    text: str
    is_active: bool = True
    created_at: datetime
    updated_at: Optional[datetime] = None