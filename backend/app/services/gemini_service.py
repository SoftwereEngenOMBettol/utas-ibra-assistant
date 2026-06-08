# backend/app/services/gemini_service.py

from datetime import datetime
import google.generativeai as genai
import os
import json
import re
from dotenv import load_dotenv
from typing import Dict, Any
import json
import psycopg2

from ..database import get_db

load_dotenv()

# ==================== GEMINI CONFIGURATION ====================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.5-flash")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    print(f"✅ Gemini AI model initialized successfully with {GEMINI_MODEL}")
else:
    model = None
    print("⚠️ WARNING: GEMINI_API_KEY not found!")

# Font Awesome CDN
FONTAWESOME_CDN = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">'


# ==================== HELPER FUNCTIONS ====================

def validate_language_consistency(text: str, expected_language: str) -> bool:
    """Validate that the text matches the expected language"""
    if expected_language == "ar":
        if re.search(r'[a-zA-Z]', text) and not re.search(r'[\u0600-\u06FF]', text):
            return False
        return True
    else:
        if re.search(r'[\u0600-\u06FF]', text):
            return False
        return True


def test_gemini_connection():
    """Test if Gemini API is working"""
    if not model:
        print("❌ Gemini not configured")
        return False
    try:
        response = model.generate_content("Say 'Hello, UTAS Chatbot is working!'")
        print(f"✅ Gemini test successful: {response.text[:50]}...")
        return True
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        return False


def build_html_response(content: str, title: str = None, lang: str = 'en') -> str:
    """Build beautiful HTML response with Font Awesome"""
    direction = 'rtl' if lang == 'ar' else 'ltr'
    font = "Cairo, 'Segoe UI', Arial, sans-serif" if lang == 'ar' else "'Segoe UI', Arial, sans-serif"
    
    title_html = f'<h2 style="margin: 0; font-size: 24px;">{title}</h2>' if title else ''
    
    return f'''
    {FONTAWESOME_CDN}
    <div style="font-family: {font}; max-width: 100%; margin: 10px 0; direction: {direction};">
        <div style="background: linear-gradient(135deg, #1800ad 0%, #1800ad 100%); padding: 20px; border-radius: 15px 15px 0 0; color: white;">
            {title_html}
        </div>
        <div style="background: white; padding: 20px; border: 1px solid #d3cdf8; border-radius: 0 0 15px 15px;">
            {content}
            <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #d3cdf8; font-size: 12px; color: #666; text-align: center;">
                <i class="fas fa-university"></i> UTAS Ibra - Student Information System
            </div>
        </div>
    </div>
    '''


# ==================== BASIC RESPONSE GENERATION ====================

async def generate_response(question: str, language: str, student_data: dict):
    """Generate response using Gemini AI for student queries"""
    
    if not model:
        return "AI service is not available. Please try again later or contact support."
    
    context = f"""
    You are UTAS Ibra Assistant. Answer in {language} language.
    
    Student Information:
    - Name: {student_data.get('student', {}).get('name', 'Unknown')}
    - Department: {student_data.get('student', {}).get('department', 'Unknown')}
    
    Answer the student's question helpfully and concisely.
    If you don't know the answer, say exactly:
    "I don't know this answer yet, but I will learn soon."
    
    Question: {question}
    """
    
    try:
        response = model.generate_content(context)
        return response.text
    except Exception as e:
        print(f"❌ Gemini response error: {e}")
        return "I'm having trouble processing your request. Please try again."


# ==================== FAQ GENERATION FROM CONTENT ====================

async def generate_faqs_from_content(content: str, content_type: str, admin_id: str = None):
    """Generate FAQs from content using Gemini AI"""
    
    if not model:
        print("❌ Gemini model not available")
        return []
    
    max_length = 15000
    if len(content) > max_length:
        content = content[:max_length]
        print(f"⚠️ Content truncated to {max_length} characters")
    
    prompt = f"""
    You are an AI assistant helping a university admin create a comprehensive FAQ database.
    
    Content Type: {content_type}
    Content to analyze:
    {content}
    
    Generate between 3 to 10 frequently asked questions and their answers.
    
    FORMAT YOUR RESPONSE AS JSON ARRAY:
    [
        {{
            "question_ar": "السؤال باللغة العربية",
            "question_en": "Question in English language",
            "answer_ar": "إجابة مفصلة باللغة العربية",
            "answer_en": "Detailed answer in English language"
        }}
    ]
    """
    
    try:
        print(f"🤖 Sending request to Gemini AI...")
        response = model.generate_content(prompt)
        
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(response.text)
    except Exception as e:
        print(f"❌ Gemini error: {e}")
        return []


async def generate_faqs_with_html(content: str, content_type: str, category: str = "General"):
    """Generate FAQs with beautiful HTML/CSS responses"""
    
    if not model:
        return []
    
    prompt = f"""
    Create beautiful HTML FAQs from this content.
    
    Content: {content[:8000]}
    Category: {category}
    
    Return JSON array with question_ar, question_en, answer_html_ar, answer_html_en.
    Use beautiful styling with gradients, icons, and colors.
    """
    
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []


async def extract_categories_with_gemini(content: str, content_type: str):
    """Extract categories and FAQs using Gemini AI"""
    
    if not model:
        return None
    
    prompt = f"""
    Analyze this content and extract categories with FAQs.
    
    Content: {content[:8000]}
    
    Return JSON: {{"categories": [{{"name_ar": "", "name_en": "", "faqs": []}}]}}
    """
    
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


async def extract_with_gemini(content: str, content_type: str):
    """Extract FAQs using Gemini AI"""
    
    if not model:
        return None
    
    prompt = f"""
    Extract FAQs from this {content_type} content.
    
    Content: {content[:8000]}
    
    Return JSON: {{"faqs": [{{"question_en": "", "question_ar": "", "answer_en": "", "answer_ar": "", "category": ""}}]}}
    """
    
    try:
        response = model.generate_content(prompt)
        json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


async def save_beautiful_faqs_to_db(faqs, category, source_type, source_name, admin_id):
    """Save beautifully formatted FAQs to database"""
    conn = get_db()
    cur = conn.cursor()
    saved_count = 0
    
    for faq in faqs:
        cur.execute("""
            INSERT INTO fqa (question_ar, question_en, answer_ar, answer_en, category, 
                           attachment_type, attachment_content, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            faq.get('question_ar', ''),
            faq.get('question_en', ''),
            faq.get('answer_html_ar', faq.get('answer_ar', '')),
            faq.get('answer_html_en', faq.get('answer_en', '')),
            category,
            source_type,
            source_name,
            admin_id,
            datetime.now()
        ))
        saved_count += 1
    
    conn.commit()
    cur.close()
    conn.close()
    return saved_count


# ==================== QUERY HANDLERS ====================



async def handle_gpa_query(student_id: str, lang: str) -> Dict[str, Any]:
    """Handle GPA query with beautiful dynamic design - From chatbot_service.py"""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        # Get student info
        cur.execute("SELECT id, name FROM students WHERE student_id = %s", (student_id,))
        student = cur.fetchone()
        if not student:
            cur.close()
            conn.close()
            return {"answer": "Student not found", "from_faq": False}
        
        db_student_id = student['id']
        
        # Get GPA records
        cur.execute("""
            SELECT gpa_value, gpa_type, semester 
            FROM student_gpa 
            WHERE student_id = %s 
            ORDER BY updated_at DESC
        """, (db_student_id,))
        
        gpa_records = cur.fetchall()
        cur.close()
        conn.close()
        
        if not gpa_records:
            content = '<p><i class="fas fa-chart-line"></i> No GPA records found. Please check CIMS for your grades.</p>' if lang == 'en' else '<p><i class="fas fa-chart-line"></i> لا توجد سجلات للمعدل. الرجاء التحقق من CIMS لمعرفة درجاتك.</p>'
            return {"answer": build_html_response(content, 'GPA Report' if lang == 'en' else 'تقرير المعدل', lang), "from_faq": False, "intent": "gpa_query"}
        
        # Find cumulative GPA
        cumulative_gpa = None
        semester_gpa = None
        for record in gpa_records:
            if record['gpa_type'] == 'cumulative':
                cumulative_gpa = record['gpa_value']
            elif record['gpa_type'] == 'semester':
                semester_gpa = record['gpa_value']
        
        if cumulative_gpa is None and gpa_records:
            cumulative_gpa = gpa_records[0]['gpa_value']
        
        # Determine status and color
        if cumulative_gpa and cumulative_gpa >= 3.5:
            status = "Excellent - Dean's List" if lang == 'en' else "ممتاز - قائمة العميد"
            status_color = "#1800ad"
        elif cumulative_gpa and cumulative_gpa >= 3.0:
            status = "Good" if lang == 'en' else "جيد جداً"
            status_color = "#28a745"
        elif cumulative_gpa and cumulative_gpa >= 2.0:
            status = "Satisfactory" if lang == 'en' else "مقبول"
            status_color = "#ff620c"
        else:
            status = "Academic Warning" if lang == 'en' else "تحذير أكاديمي"
            status_color = "#dc3545"
        
        # Build the HTML content dynamically
        content = f'''
        <div style="display: flex; justify-content: space-between; margin-bottom: 20px; flex-wrap: wrap; gap: 15px;">
            <div style="background: #d3cdf8; padding: 20px; border-radius: 10px; flex: 1; text-align: center;">
                <p style="margin: 0; font-size: 12px; color: #666;"><i class="fas fa-star"></i> {"Cumulative GPA" if lang == 'en' else "المعدل التراكمي"}</p>
                <p style="margin: 5px 0 0; font-size: 32px; font-weight: bold; color: #1800ad;">{cumulative_gpa if cumulative_gpa else 'N/A'}</p>
            </div>
            <div style="background: #d3cdf8; padding: 20px; border-radius: 10px; flex: 1; text-align: center;">
                <p style="margin: 0; font-size: 12px; color: #666;"><i class="fas fa-calendar-alt"></i> {"Semester GPA" if lang == 'en' else "معدل الفصل"}</p>
                <p style="margin: 5px 0 0; font-size: 32px; font-weight: bold; color: #1800ad;">{semester_gpa if semester_gpa else 'N/A'}</p>
            </div>
        </div>
        <div style="background: {status_color}20; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
            <p style="margin: 0; font-size: 16px; font-weight: bold; color: {status_color};"><i class="fas fa-info-circle"></i> {status}</p>
        </div>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 10px;">
            <p style="margin: 0;"><strong><i class="fas fa-lightbulb"></i> {"Tips to improve your GPA:" if lang == 'en' else "نصائح لتحسين معدلك:"}</strong></p>
            <ul style="margin: 10px 0 0 20px;">
                <li>{"Attend all classes regularly" if lang == 'en' else "احضر جميع المحاضرات بانتظام"}</li>
                <li>{"Submit assignments on time" if lang == 'en' else "سلم الواجبات في وقتها"}</li>
                <li>{"Form study groups" if lang == 'en' else "شكل مجموعات دراسة"}</li>
            </ul>
        </div>
        <p style="margin-top: 15px; text-align: center;">
            <i class="fas fa-download"></i> {"Download full GPA report by saying 'Download GPA report'" if lang == 'en' else "يمكنك تحميل تقرير المعدل الكامل بقولك 'تحميل تقرير المعدل'"}
        </p>
        '''
        
        return {
            "answer": build_html_response(content, 'Academic Transcript' if lang == 'en' else 'السجل الأكاديمي', lang),
            "from_faq": False,
            "intent": "gpa_query"
        }
    except Exception as e:
        print(f"GPA error: {e}")
        return {"answer": "Error fetching GPA data", "from_faq": False, "intent": "error"}

async def handle_schedule_query(student_id: str, lang: str) -> Dict[str, Any]:
    """Handle schedule query with beautiful dynamic table"""
    try:
        conn = get_db()
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        cur.execute("SELECT id FROM students WHERE student_id = %s", (student_id,))
        student = cur.fetchone()
        if not student:
            return {"answer": "Student not found", "from_faq": False}
        
        db_student_id = student['id']
        
        cur.execute("""
            SELECT day_of_week, time_start, time_end, course_code, course_name, room
            FROM student_schedule 
            WHERE student_id = %s 
            ORDER BY 
                CASE day_of_week
                    WHEN 'Sunday' THEN 1
                    WHEN 'Monday' THEN 2
                    WHEN 'Tuesday' THEN 3
                    WHEN 'Wednesday' THEN 4
                    WHEN 'Thursday' THEN 5
                END,
                time_start
        """, (db_student_id,))
        
        schedule = cur.fetchall()
        cur.close()
        conn.close()
        
        if not schedule:
            content = '<p><i class="fas fa-calendar-alt"></i> No schedule found. Please check CIMS.</p>' if lang == 'en' else '<p><i class="fas fa-calendar-alt"></i> لا يوجد جدول. الرجاء التحقق من CIMS.</p>'
            return {"answer": build_html_response(content, 'Schedule' if lang == 'en' else 'الجدول الدراسي', lang), "from_faq": False}
        
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
        days_ar = ['الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس']
        time_slots = ['08:00-10:00', '10:00-12:00', '12:00-14:00', '14:00-16:00']
        
        # Build schedule table dynamically
        table_html = '<div style="overflow-x: auto;"><table style="width: 100%; border-collapse: collapse;">'
        table_html += '<thead><tr style="background: linear-gradient(135deg, #1800ad 0%, #d3cdf8 100%); color: white;">'
        table_html += f'<th style="padding: 12px;"><i class="fas fa-clock"></i> {"Time" if lang == "en" else "الوقت"}</th>'
        for day in (days_ar if lang == 'ar' else days):
            table_html += f'<th style="padding: 12px;">{day}</th>'
        table_html += '</tr></thead><tbody>'
        
        for time_slot in time_slots:
            table_html += f'<tr><td style="padding: 12px; font-weight: 600; background: #d3cdf8;">{time_slot}</td>'
            for day in days:
                course_at_time = None
                for course in schedule:
                    if course['day_of_week'] == day:
                        time_start = str(course['time_start'])[:5] if course['time_start'] else ""
                        time_end = str(course['time_end'])[:5] if course['time_end'] else ""
                        course_time = f"{time_start}-{time_end}"
                        if course_time == time_slot:
                            course_at_time = course
                            break
                if course_at_time:
                    table_html += f'<td style="padding: 12px;"><strong>{course_at_time["course_code"]}</strong><br/><span style="font-size: 12px; color: #666;">{course_at_time["course_name"][:25]}</span><br/><span style="font-size: 11px; color: #999;"><i class="fas fa-location-dot"></i> {course_at_time["room"] or "TBA"}</span></td>'
                else:
                    table_html += '<td style="padding: 12px; color: #ccc; text-align: center;">—</td>'
            table_html += '</tr>'
        table_html += '</tbody></table></div>'
        
        return {
            "answer": build_html_response(table_html, 'Student Time Table' if lang == 'en' else 'الجدول الدراسي', lang),
            "from_faq": False,
            "intent": "schedule_query"
        }
    except Exception as e:
        print(f"Schedule error: {e}")
        return {"answer": "Error fetching schedule", "from_faq": False}

async def handle_attendance_query(student_id: str, lang: str):
    """Handle attendance query with beautiful design"""
    return {"answer": "Attendance feature coming soon", "from_faq": False}


async def detect_intent(message: str, language: str = 'en') -> str:
    """Detect intent from message"""
    message_lower = message.lower()
    if any(w in message_lower for w in ['gpa', 'معدل', 'معدلي']):
        return 'gpa_query'
    elif any(w in message_lower for w in ['schedule', 'جدول']):
        return 'schedule_query'
    elif any(w in message_lower for w in ['attendance', 'حضور']):
        return 'attendance_query'
    return 'general'


async def process_chat_message(message: str, student_id: str, session_id: str, language: str = 'en'):
    """Main function to process chat messages"""
    intent = await detect_intent(message, language)
    
    if intent == 'gpa_query':
        return await handle_gpa_query(student_id, language)
    elif intent == 'schedule_query':
        return await handle_schedule_query(student_id, language)
    elif intent == 'attendance_query':
        return await handle_attendance_query(student_id, language)
    else:
        return {"answer": "I'm your UTAS Assistant. How can I help you?", "from_faq": False}


# ==================== SMART CHAT SERVICE ====================

class SmartChatService:
    def __init__(self):
        self.model = model
    
    async def process_message(self, message: str, student_id: str, session_id: str, language: str = 'en'):
        return await process_chat_message(message, student_id, session_id, language)


def get_smart_chat_service():
    return SmartChatService()


# ==================== INITIALIZATION ====================

if GEMINI_API_KEY:
    test_gemini_connection()
    print("✅ Gemini service ready")