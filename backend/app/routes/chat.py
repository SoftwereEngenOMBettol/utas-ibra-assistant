# backend/app/routes/chat.py

from fastapi import APIRouter, HTTPException
from datetime import datetime
from ..database import get_db
from pydantic import BaseModel
from typing import Optional
import uuid
import re

router = APIRouter(prefix="/api", tags=["chat"])

# ==================== MODELS ====================

class ChatRequest(BaseModel):
    student_id: str
    session_token: str
    message: str
    language: str = "en"

class FeedbackRequest(BaseModel):
    student_id: str
    rating: int
    comment: Optional[str] = None

class StartSessionRequest(BaseModel):
    student_id: str
    language: str = "en"


# ==================== HELPER FUNCTIONS ====================

async def detect_intent_with_gemini(message: str, language: str) -> str:
    """Use Gemini to understand the question and detect intent"""
    
    try:
        from ..services.gemini_service import model
        
        if not model:
            return None
        
        prompt = f"""
        Analyze this student question and determine the INTENT category.
        
        Question: {message}
        Language: {language}
        
        Possible intents:
        - GPA_QUERY: questions about grades, GPA, marks, المعدل
        - SCHEDULE_QUERY: questions about timetable, classes, schedule, الجدول
        - ATTENDANCE_QUERY: questions about attendance, حضور, غياب
        - ADVISOR_CONTACT: questions about academic advisor, مرشد
        - REGISTRATION: questions about course registration, تسجيل
        - CIMS_ACCESS: questions about CIMS portal, نظام CIMS
        - EXAM_SCHEDULE: questions about exams, امتحانات
        - TRANSCRIPT: questions about transcript, كشف الدرجات
        - PASSWORD_RESET: questions about forgot password, كلمة المرور
        - SCHOLARSHIP: questions about scholarships, منح
        - INTERNSHIP: questions about internships, تدريب
        - EMERGENCY: questions about emergency, طوارئ
        - PDF_DOWNLOAD: requests to download reports, تحميل
        - GENERAL: other questions
        
        Return ONLY the intent name (e.g., GPA_QUERY, SCHEDULE_QUERY, etc.)
        """
        
        response = model.generate_content(prompt)
        intent = response.text.strip().upper()
        
        # Map Gemini intent to internal intent names
        intent_map = {
            'GPA_QUERY': 'gpa_query',
            'SCHEDULE_QUERY': 'schedule_query',
            'ATTENDANCE_QUERY': 'attendance_query',
            'ADVISOR_CONTACT': 'advisor_contact',
            'REGISTRATION': 'registration',
            'CIMS_ACCESS': 'cims_access',
            'EXAM_SCHEDULE': 'exam_schedule',
            'TRANSCRIPT': 'transcript_query',
            'PASSWORD_RESET': 'password_reset',
            'SCHOLARSHIP': 'scholarships',
            'INTERNSHIP': 'internships_jobs',
            'EMERGENCY': 'emergency',
            'PDF_DOWNLOAD': 'pdf_download',
            'GENERAL': 'general'
        }
        
        return intent_map.get(intent, 'general')
        
    except Exception as e:
        print(f"Gemini intent detection error: {e}")
        return None


def save_unanswered_question(student_id: str, question: str, language: str):
    """Save unanswered question to database"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO unanswered_questions (student_id, question, language, asked_at, status, times_asked)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (student_id, question, language, datetime.now(), 'pending', 1))
        new_id = cur.fetchone()[0]
        conn.commit()
        print(f"📝 Saved unanswered question ID: {new_id}")
    except Exception as e:
        print(f"Error saving unanswered question: {e}")
    finally:
        cur.close()
        conn.close()


def log_chat(student_id: str, session_token: str, question: str, answer: str, language: str):
    """Log chat to database"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO chat_logs (student_id, session_token, question, answer, language, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (student_id, session_token, question, answer, language, datetime.now()))
        conn.commit()
    except Exception as e:
        print(f"Error logging chat: {e}")
    finally:
        cur.close()
        conn.close()


# ==================== CHAT ENDPOINT ====================

@router.post("/chat")
async def chat(request: ChatRequest):
    """Process chat message with Gemini understanding and UTASVirtualAssistant"""
    
    print(f"\n{'='*60}")
    print(f"📨 Chat Message: {request.message}")
    print(f"👤 Student ID: {request.student_id}")
    print(f"🌐 Language: {request.language}")
    print(f"{'='*60}")
    
    # ==================== STEP 1: GEMINI UNDERSTANDS THE QUESTION ====================
    detected_intent = await detect_intent_with_gemini(request.message, request.language)
    print(f"🤖 Gemini detected intent: {detected_intent}")
    
    # ==================== STEP 2: CHECK FAQ DATABASE FIRST ====================
    conn = get_db()
    cur = conn.cursor()
    
    message_lower = request.message.lower()
    
    # Search for matching FAQ in database - FIXED VERSION without STRING_TO_ARRAY
    cur.execute("""
        SELECT id, question_ar, question_en, answer_ar, answer_en, category
        FROM fqa 
        WHERE is_active = true 
        AND (
            LOWER(question_en) LIKE %s 
            OR LOWER(question_ar) LIKE %s
        )
        ORDER BY 
            CASE WHEN LOWER(question_en) = %s THEN 1
                 WHEN LOWER(question_ar) = %s THEN 1
                 ELSE 2
            END
        LIMIT 1
    """, (
        f'%{message_lower}%',
        f'%{message_lower}%',
        message_lower,
        message_lower
    ))
    
    faq_match = cur.fetchone()
    cur.close()
    conn.close()
    
    if faq_match:
        # Found in database - return answer directly
        answer = faq_match[4] if request.language == 'en' else faq_match[3]
        
        if answer and answer.strip():
            print(f"✅ Found in FAQ database (ID: {faq_match[0]}, Category: {faq_match[5]})")
            
            # Log the chat
            log_chat(request.student_id, request.session_token, request.message, answer, request.language)
            
            return {
                "answer": answer,
                "from_faq": True,
                "intent": faq_match[5] if len(faq_match) > 5 else "general",
                "detected_intent": detected_intent
            }
    
    # ==================== STEP 3: USE UTASVirtualAssistant FOR DYNAMIC HANDLERS ====================
    try:
        from ..services.chatbot_service import UTASVirtualAssistant
        
        assistant = UTASVirtualAssistant()
        
        # Process message with the assistant (handles GPA, Schedule, Attendance, PDF)
        result = assistant.handle_message(
            message=request.message,
            student_id=request.student_id,
            session_id=request.session_token
        )
        
        # Check if assistant found a response
        if result and result.get('response'):
            print(f"✅ Assistant handled: {result.get('intent', 'unknown')}")
            
            # Log the chat
            log_chat(request.student_id, request.session_token, request.message, result['response'], request.language)
            
            return {
                "answer": result['response'],
                "from_faq": result.get('from_faq', False),
                "intent": result.get('intent', 'general'),
                "detected_intent": detected_intent,
                "pdf_data": result.get('pdf_data'),
                "filename": result.get('filename')
            }
    
    except Exception as e:
        print(f"❌ Assistant error: {e}")
        import traceback
        traceback.print_exc()
    
    # ==================== STEP 4: NO RESPONSE FOUND ====================
    print(f"❌ No response found for: {request.message}")
    
    # Save to unanswered questions
    save_unanswered_question(request.student_id, request.message, request.language)
    
    # Return fallback response
    if request.language == 'ar':
        fallback = "شكراً لسؤالك! لم أجد إجابة لهذا السؤال حالياً. سيتم مراجعة سؤالك وإضافته إلى قاعدة المعرفة قريباً."
    else:
        fallback = "Thank you for your question! I don't have an answer for this yet. Your question has been saved and will be reviewed by our team."
    
    # Log the fallback response
    log_chat(request.student_id, request.session_token, request.message, fallback, request.language)
    
    return {
        "answer": fallback,
        "from_faq": False,
        "intent": "unknown",
        "detected_intent": detected_intent,
        "saved_to_unanswered": True
    }


# ==================== FEEDBACK ENDPOINT ====================

@router.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """Submit user feedback"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO feedback (student_id, rating, comment, created_at)
            VALUES (%s, %s, %s, %s)
        """, (feedback.student_id, feedback.rating, feedback.comment, datetime.now()))
        conn.commit()
        print(f"✅ Feedback from {feedback.student_id}: {feedback.rating} stars")
        return {"message": "Feedback submitted successfully"}
    except Exception as e:
        print(f"❌ Feedback error: {e}")
        return {"message": "Feedback received"}
    finally:
        cur.close()
        conn.close()


# ==================== SESSION START ENDPOINT ====================

@router.post("/chat/start")
async def start_chat_session(request: StartSessionRequest):
    """Start a new chat session"""
    session_id = str(uuid.uuid4())
    
    print(f"✅ Session started: {session_id} for student {request.student_id}")
    
    return {
        "success": True,
        "session_id": session_id,
        "student_id": request.student_id,
        "message": "Session started successfully"
    }


# ==================== SESSION END ENDPOINT ====================

@router.post("/chat/end")
async def end_chat_session(session_id: str):
    """End a chat session"""
    print(f"✅ Session ended: {session_id}")
    return {
        "success": True,
        "message": "Session ended successfully"
    }