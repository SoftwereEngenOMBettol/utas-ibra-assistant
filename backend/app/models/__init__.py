# backend/app/models/__init__.py

from .auth_models import LoginRequest, ChatRequest, FeedbackRequest, UserResponse, SessionResponse
from .fqa_models import (
    FQACreate, 
    FQAResponse, 
    FQAUpdate, 
    FQABatchGenerate, 
    UnansweredQuestionResponse,
    CategoryCreate,
    CategoryResponse,
    ConversationResponse
)

__all__ = [
    'LoginRequest',
    'ChatRequest', 
    'FeedbackRequest',
    'UserResponse',
    'SessionResponse',
    'FQACreate',
    'FQAResponse', 
    'FQAUpdate',
    'FQABatchGenerate',
    'UnansweredQuestionResponse',
    'CategoryCreate',
    'CategoryResponse',
    'ConversationResponse'
]