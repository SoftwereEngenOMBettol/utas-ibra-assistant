# backend/app/database/connector.py

import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import uuid

load_dotenv()
logger = logging.getLogger(__name__)


class DatabaseConnector:
    """Complete Database Connector for UTAS Virtual Assistant"""
    
    def __init__(self):
        self.connection_params = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': os.getenv('DB_PORT', '5432'),
            'database': os.getenv('DB_NAME', 'utas_assistant'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '123456')
        }
    
    def get_connection(self):
        """Get database connection"""
        return psycopg2.connect(**self.connection_params)
    
    def check_connection(self):
        """Check database connection"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False
    
    # ==================== STUDENT METHODS ====================
    
    def get_student(self, student_id):
        """Get student by student_id (the string ID like '36S2023')"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, student_id, name, email, department, preferred_language,
                               advisor, advisor_email, contact, admission_type, current_semester,
                               status, allowance, warnings, created_at, updated_at
                        FROM students 
                        WHERE student_id = %s
                    """, (student_id,))
                    result = cur.fetchone()
                if result:
                    print(f"✅ Found student: {result.get('name')} (DB ID: {result.get('id')})")
                else:
                    print(f"❌ Student {student_id} not found in database")
                return result
        except Exception as e:
            print(f"❌ Database error in get_student: {e}")
            return None
    
    def get_student_by_id(self, id):
        """Get student by database id (integer)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM students 
                        WHERE id = %s
                    """, (id,))
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Error getting student by id: {e}")
            return None
    
    def get_all_students(self, limit=100, offset=0):
        """Get all students with pagination"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, student_id, name, email, department, preferred_language,
                               advisor, advisor_email, contact, status, created_at
                        FROM students 
                        ORDER BY student_id 
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting all students: {e}")
            return []
    
    def get_students_count(self):
        """Get total number of students"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM students")
                    return cur.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting students count: {e}")
            return 0
    
    def update_student(self, student_id, **kwargs):
        """Update student information"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    update_fields = []
                    values = []
                    
                    for key, value in kwargs.items():
                        if value is not None:
                            update_fields.append(f"{key} = %s")
                            values.append(value)
                    
                    if not update_fields:
                        return False
                    
                    values.append(student_id)
                    query = f"UPDATE students SET {', '.join(update_fields)}, updated_at = %s WHERE student_id = %s"
                    
                    cur.execute(query, values + [datetime.now()])
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating student: {e}")
            return False
    
    def update_student_preference(self, student_id, field, value):
        """Update student preference"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"""
                        UPDATE students 
                        SET {field} = %s, updated_at = %s
                        WHERE student_id = %s
                    """, (value, datetime.now(), student_id))
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating student preference: {e}")
            return False
    
    def update_student_password(self, student_id, password_hash):
        """Update student password"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE students 
                        SET password_hash = %s, updated_at = %s
                        WHERE student_id = %s
                    """, (password_hash, datetime.now(), student_id))
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating student password: {e}")
            return False
    
    def reset_login_attempts(self, student_id):
        """Reset login attempts counter"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE students 
                        SET login_attempts = 0, locked_until = NULL
                        WHERE student_id = %s
                    """, (student_id,))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error resetting login attempts: {e}")
            return False
    
    def get_student_advisor(self, student_id):
        """Get advisor information for a specific student"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            advisor as advisor_name,
                            advisor_email,
                            advisor_office,
                            advisor_phone
                        FROM students 
                        WHERE student_id = %s
                    """, (student_id,))
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Error getting advisor info: {e}")
            return None
    
    # ==================== GPA METHODS ====================

    # ==================== SCHEDULE METHODS ====================
    
    def get_student_schedule(self, student_id):
        """Get full schedule for a student"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT day_of_week, time_start, time_end, 
                               course_code, course_name, room, lecturer
                        FROM student_schedule 
                        WHERE student_id = %s
                        ORDER BY 
                            CASE day_of_week
                                WHEN 'Sunday' THEN 1
                                WHEN 'Monday' THEN 2
                                WHEN 'Tuesday' THEN 3
                                WHEN 'Wednesday' THEN 4
                                WHEN 'Thursday' THEN 5
                                ELSE 6
                            END,
                            time_start
                    """, (student_id,))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting schedule: {e}")
            return []
    
    def get_student_schedule_for_day(self, student_id, day):
        """Get schedule for a specific day"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM student_schedule 
                        WHERE student_id = %s AND day_of_week = %s
                        ORDER BY time_start
                    """, (student_id, day))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting schedule for day: {e}")
            return []
    
    # ==================== COURSE METHODS ====================
    
    def get_student_courses(self, student_id, semester='all'):
        """Get courses for a student"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    if semester == 'current':
                        cur.execute("""
                            SELECT course_code, course_name, credit_hours, instructor
                            FROM student_courses 
                            WHERE student_id = %s AND grade IS NULL
                            ORDER BY course_code
                        """, (student_id,))
                    elif semester != 'all':
                        cur.execute("""
                            SELECT * FROM student_courses 
                            WHERE student_id = %s AND semester = %s
                            ORDER BY course_code
                        """, (student_id, semester))
                    else:
                        cur.execute("""
                            SELECT * FROM student_courses 
                            WHERE student_id = %s
                            ORDER BY semester DESC, course_code
                        """, (student_id,))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting courses: {e}")
            return []
    
    def get_current_courses(self, student_id):
        """Get current semester courses"""
        return self.get_student_courses(student_id, 'current')
    
    def get_course_details(self, course_code):
        """Get course details by code"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM courses 
                        WHERE course_code = %s
                    """, (course_code,))
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Error getting course details: {e}")
            return None
    
    # ==================== GPA METHODS ====================
    
    def get_student_gpa(self, student_id):
        """Get all GPA records for a student"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT semester, gpa_type, gpa_value
                        FROM student_gpa 
                        WHERE student_id = %s
                        ORDER BY 
                            CASE 
                                WHEN gpa_type = 'semester' THEN 1
                                WHEN gpa_type = 'cumulative' THEN 2
                                ELSE 3
                            END,
                            semester DESC
                    """, (student_id,))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting GPA: {e}")
            return []
    
    def get_student_gpa_by_type(self, student_id, gpa_type):
        """Get specific GPA type for a student"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT semester, gpa_type, gpa_value
                        FROM student_gpa 
                        WHERE student_id = %s AND gpa_type = %s
                        ORDER BY 
                            CASE 
                                WHEN gpa_type = 'semester' THEN semester
                                ELSE NULL
                            END DESC
                        LIMIT 1
                    """, (student_id, gpa_type))
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Error getting GPA by type: {e}")
            return None
    
    def get_student_semester_gpa(self, student_id):
        """Get current semester GPA"""
        return self.get_student_gpa_by_type(student_id, 'semester')
    
    def get_student_cumulative_gpa(self, student_id):
        """Get cumulative GPA"""
        return self.get_student_gpa_by_type(student_id, 'cumulative')
    
    
    # ==================== ATTENDANCE METHODS ====================
    
    def get_attendance_percentage(self, student_id, course_code=None):
        """Get attendance percentage for a student"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    if course_code:
                        cur.execute("""
                            SELECT 
                                course_code,
                                total_classes,
                                absences,
                                ((total_classes - absences)::float / NULLIF(total_classes, 0) * 100) as percentage
                            FROM student_attendance 
                            WHERE student_id = %s AND course_code = %s
                        """, (student_id, course_code))
                        return cur.fetchone()
                    else:
                        cur.execute("""
                            SELECT 
                                course_code,
                                total_classes,
                                absences,
                                ((total_classes - absences)::float / NULLIF(total_classes, 0) * 100) as percentage
                            FROM student_attendance 
                            WHERE student_id = %s
                            ORDER BY course_code
                        """, (student_id,))
                        results = cur.fetchall()
                        
                        # إضافة أسماء المواد من جدول منفصل إذا لزم الأمر
                        # أو استخدام course_code كاسم مؤقت
                        for row in results:
                            # يمكن إضافة اسم المادة من جدول courses إذا كان موجوداً
                            row['course_name'] = row['course_code']  # مؤقتاً
                        
                        return results
        except Exception as e:
            logger.error(f"Error getting attendance percentage: {e}")
            return [] if not course_code else None
    
    def get_attendance_with_course_names(self, student_id):
        """Get attendance with course names from courses table"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            sa.course_code,
                            c.course_name as course_name,
                            sa.total_classes,
                            sa.absences,
                            ((sa.total_classes - sa.absences)::float / NULLIF(sa.total_classes, 0) * 100) as percentage
                        FROM student_attendance sa
                        LEFT JOIN courses c ON sa.course_code = c.course_code
                        WHERE sa.student_id = %s
                        ORDER BY sa.course_code
                    """, (student_id,))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting attendance with course names: {e}")
            # Fallback to basic attendance
            return self.get_attendance_percentage(student_id)
    # ==================== TRANSCRIPT METHODS ====================
    
    def get_student_transcript(self, student_id):
        """Get complete transcript"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT semester, course_code, course_name, 
                               credit_hours, grade, points, result
                        FROM student_courses 
                        WHERE student_id = %s AND grade IS NOT NULL
                        ORDER BY semester DESC, course_code
                    """, (student_id,))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting transcript: {e}")
            return []
    
    def get_student_transcript_summary(self, student_id):
        """Get transcript summary by semester"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            semester,
                            COUNT(*) as courses,
                            SUM(credit_hours) as total_credits,
                            ROUND(AVG(CASE 
                                WHEN grade = 'A' THEN 4.0
                                WHEN grade = 'A-' THEN 3.7
                                WHEN grade = 'B+' THEN 3.3
                                WHEN grade = 'B' THEN 3.0
                                WHEN grade = 'B-' THEN 2.7
                                WHEN grade = 'C+' THEN 2.3
                                WHEN grade = 'C' THEN 2.0
                                WHEN grade = 'C-' THEN 1.7
                                WHEN grade = 'D' THEN 1.0
                                WHEN grade = 'F' THEN 0.0
                                ELSE NULL
                            END), 2) as semester_gpa
                        FROM student_courses 
                        WHERE student_id = %s AND grade IS NOT NULL
                        GROUP BY semester
                        ORDER BY semester DESC
                    """, (student_id,))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting transcript summary: {e}")
            return []
    
    # ==================== CHAT SESSION METHODS ====================
    
    def create_chat_session(self, student_id):
        """Create a new chat session"""
        try:
            student = self.get_student(student_id)
            if not student:
                logger.error(f"Student not found: {student_id}")
                return None, None
                
            student_db_id = student['id']
            session_uuid = str(uuid.uuid4())
            
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO chat_sessions (student_id, session_uuid, start_time, is_active)
                        VALUES (%s, %s, %s, true)
                        RETURNING id
                    """, (student_db_id, session_uuid, datetime.now()))
                    
                    session_id = cur.fetchone()[0]
                    conn.commit()
                    
                    logger.info(f"✅ Chat session created for student {student_id} (DB ID: {student_db_id})")
                    return session_id, session_uuid
                    
        except Exception as e:
            logger.error(f"Error creating chat session: {e}")
            return None, None
    
    def log_session_start(self, student_id, session_id):
        """Log chat session start to database"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    student = self.get_student(student_id)
                    if not student:
                        logger.error(f"Student not found: {student_id}")
                        return False
                    
                    student_db_id = student['id']
                    
                    cur.execute("""
                        INSERT INTO chat_sessions (student_id, session_uuid, start_time, is_active)
                        VALUES (%s, %s, %s, true)
                    """, (student_db_id, session_id, datetime.now()))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error logging session start: {e}")
            return False
    
    def end_chat_session(self, session_id):
        """End a chat session"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE chat_sessions 
                        SET end_time = %s, is_active = false
                        WHERE session_uuid = %s
                    """, (datetime.now(), session_id))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error ending chat session: {e}")
            return False
    
    def get_active_session(self, student_id):
        """Get active session for a student"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    student = self.get_student(student_id)
                    if not student:
                        return None
                    
                    cur.execute("""
                        SELECT * FROM chat_sessions 
                        WHERE student_id = %s AND is_active = true
                        ORDER BY start_time DESC
                        LIMIT 1
                    """, (student['id'],))
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Error getting active session: {e}")
            return None
    
    def get_session_messages(self, session_id):
        """Get messages for a session"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM messages 
                        WHERE session_id = %s
                        ORDER BY timestamp
                    """, (session_id,))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    def save_message(self, session_id, student_id, message, sender, intent=None, confidence=None):
        """Save a chat message"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    student = self.get_student(student_id)
                    if not student:
                        logger.error(f"Student not found: {student_id}")
                        return False
                    
                    cur.execute("""
                        INSERT INTO messages 
                        (session_id, student_id, message_text, sender_type, intent_detected, confidence_score, timestamp)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (session_id, student['id'], message, sender, intent, confidence, datetime.now()))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return False
    
    # ==================== FAQ METHODS ====================
    
    def search_faqs(self, query):
        """Search FAQs by keyword"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM faq_knowledge_base 
                        WHERE is_active = true 
                        AND (question_en ILIKE %s OR question_ar ILIKE %s OR answer_en ILIKE %s OR answer_ar ILIKE %s)
                        ORDER BY times_asked DESC
                        LIMIT 10
                    """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error searching FAQs: {e}")
            return []
    
    def get_faq_by_category(self, category):
        """Get FAQs by category"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM faq_knowledge_base 
                        WHERE is_active = true AND category = %s
                        ORDER BY times_asked DESC
                    """, (category,))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting FAQs by category: {e}")
            return []
    
    def get_all_faqs(self, category=None, active_only=True):
        """Get all FAQs with optional filters"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    query = "SELECT * FROM faq_knowledge_base WHERE 1=1"
                    params = []
                    
                    if category:
                        query += " AND category = %s"
                        params.append(category)
                    
                    if active_only:
                        query += " AND is_active = true"
                    
                    query += " ORDER BY times_asked DESC"
                    
                    cur.execute(query, params)
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting all FAQs: {e}")
            return []
    
    def get_faq_by_id(self, faq_id):
        """Get FAQ by ID"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM faq_knowledge_base 
                        WHERE id = %s
                    """, (faq_id,))
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Error getting FAQ by ID: {e}")
            return None
    
    def get_all_faq_categories(self):
        """Get all FAQ categories"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT DISTINCT category, COUNT(*) as count
                        FROM faq_knowledge_base
                        WHERE is_active = true
                        GROUP BY category
                        ORDER BY category
                    """)
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting FAQ categories: {e}")
            return []
    
    def add_to_knowledge_base(self, question_en, question_ar, answer_en, answer_ar, category, tags='', unanswered_id=None):
        """Add a new FAQ to knowledge base"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO faq_knowledge_base 
                        (question_en, question_ar, answer_en, answer_ar, category, tags, is_active, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, true, %s)
                        RETURNING id
                    """, (question_en, question_ar, answer_en, answer_ar, category, tags, datetime.now()))
                    
                    faq_id = cur.fetchone()[0]
                    
                    if unanswered_id:
                        cur.execute("""
                            UPDATE unanswered_questions 
                            SET resolved = true, resolved_at = %s, added_to_faq_id = %s
                            WHERE id = %s
                        """, (datetime.now(), faq_id, unanswered_id))
                    
                    conn.commit()
                    return faq_id
        except Exception as e:
            logger.error(f"Error adding to knowledge base: {e}")
            return None
    
    def update_faq(self, faq_id, **kwargs):
        """Update an existing FAQ"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    update_fields = []
                    values = []
                    
                    for key, value in kwargs.items():
                        if value is not None:
                            update_fields.append(f"{key} = %s")
                            values.append(value)
                    
                    if not update_fields:
                        return False
                    
                    values.append(faq_id)
                    values.append(datetime.now())
                    query = f"UPDATE faq_knowledge_base SET {', '.join(update_fields)}, updated_at = %s WHERE id = %s"
                    
                    cur.execute(query, values)
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating FAQ: {e}")
            return False
    
    def delete_faq(self, faq_id):
        """Delete an FAQ (soft delete)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE faq_knowledge_base 
                        SET is_active = false, updated_at = %s
                        WHERE id = %s
                    """, (datetime.now(), faq_id))
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting FAQ: {e}")
            return False
    
    # ==================== UNANSWERED QUESTIONS METHODS ====================
    
    def get_unanswered_questions(self, resolved=False):
        """Get unanswered questions with student details"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            uq.*, 
                            s.student_id as student_id_string, 
                            s.name as student_name,
                            s.email as student_email
                        FROM unanswered_questions uq
                        LEFT JOIN students s ON uq.student_id = s.id
                        WHERE uq.resolved = %s
                        ORDER BY 
                            uq.times_asked DESC,
                            uq.asked_at DESC
                    """, (resolved,))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting unanswered questions: {e}")
            return []
    
    def get_unanswered_count(self, resolved=False):
        """Get count of unanswered questions"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT COUNT(*) FROM unanswered_questions 
                        WHERE resolved = %s
                    """, (resolved,))
                    return cur.fetchone()[0]
        except Exception as e:
            logger.error(f"Error getting unanswered count: {e}")
            return 0
    
    def get_unanswered_by_id(self, question_id):
        """Get unanswered question by ID"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM unanswered_questions 
                        WHERE id = %s
                    """, (question_id,))
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Error getting unanswered by ID: {e}")
            return None
    
    def log_unanswered_question(self, question_text, student_id, language, intent_guessed, confidence_guessed=0.5):
        """Log an unanswered question"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Get student DB ID
                    cur.execute("SELECT id FROM students WHERE student_id = %s", (student_id,))
                    student_result = cur.fetchone()
                    
                    if not student_result:
                        logger.error(f"Student not found with student_id: {student_id}")
                        return False
                    
                    student_db_id = student_result[0]
                    
                    # Check if similar question exists
                    cur.execute("""
                        SELECT id, times_asked FROM unanswered_questions 
                        WHERE resolved = false 
                        AND LOWER(question_text) = LOWER(%s)
                        AND student_id = %s
                    """, (question_text, student_db_id))
                    
                    existing = cur.fetchone()
                    
                    if existing:
                        cur.execute("""
                            UPDATE unanswered_questions 
                            SET times_asked = times_asked + 1, 
                                last_asked = %s,
                                intent_guessed = %s,
                                confidence_guessed = %s
                            WHERE id = %s
                        """, (datetime.now(), intent_guessed, confidence_guessed, existing[0]))
                    else:
                        cur.execute("""
                            INSERT INTO unanswered_questions 
                            (question_text, student_id, language, intent_guessed, confidence_guessed, asked_at, last_asked, times_asked, resolved)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            question_text, student_db_id, language, intent_guessed, 
                            confidence_guessed, datetime.now(), datetime.now(), 1, False
                        ))
                    
                    conn.commit()
                    return True
                    
        except Exception as e:
            logger.error(f"Error logging unanswered question: {e}")
            return False
    
    def mark_question_resolved(self, question_id, faq_id):
        """Mark a question as resolved"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE unanswered_questions 
                        SET resolved = true, resolved_at = %s, added_to_faq_id = %s
                        WHERE id = %s
                    """, (datetime.now(), faq_id, question_id))
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error marking question resolved: {e}")
            return False
    
    # ==================== FEEDBACK METHODS ====================
    
    def save_feedback(self, message_id, student_id, rating, feedback_text=None):
        """Save feedback for a message"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    student = self.get_student(student_id)
                    if not student:
                        logger.error(f"Student not found: {student_id}")
                        return False
                    
                    cur.execute("""
                        INSERT INTO feedback 
                        (message_id, student_id, rating, feedback_text, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (message_id, student['id'], rating, feedback_text, datetime.now()))
                    conn.commit()
                    return True
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
            return False
    
    def get_feedback_for_message(self, message_id):
        """Get feedback for a specific message"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM feedback 
                        WHERE message_id = %s
                    """, (message_id,))
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Error getting feedback for message: {e}")
            return None
    
    def get_all_feedback(self, limit=100, offset=0):
        """Get all feedback with pagination"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT f.*, s.student_id, s.name as student_name
                        FROM feedback f
                        LEFT JOIN students s ON f.student_id = s.id
                        ORDER BY f.created_at DESC
                        LIMIT %s OFFSET %s
                    """, (limit, offset))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting all feedback: {e}")
            return []
    
    def get_feedback_statistics(self):
        """Get feedback statistics"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT 
                            AVG(rating) as avg_rating,
                            COUNT(*) as total,
                            SUM(CASE WHEN rating >= 4 THEN 1 ELSE 0 END) as positive
                        FROM feedback
                        WHERE created_at >= NOW() - INTERVAL '30 days'
                    """)
                    result = cur.fetchone()
                    
                    if result and result['total'] > 0:
                        avg = float(result['avg_rating']) if result['avg_rating'] else 4.5
                        rate = (result['positive'] / result['total'] * 100) if result['positive'] else 75
                        return {
                            'average': round(avg, 2),
                            'rate': round(rate, 2),
                            'total': result['total']
                        }
                    return {'average': 4.5, 'rate': 75, 'total': 0}
        except Exception as e:
            logger.error(f"Error getting feedback stats: {e}")
            return {'average': 4.5, 'rate': 75, 'total': 0}
    
    # ==================== STAFF METHODS ====================
    
    def get_staff_by_username(self, username):
        """Get staff by username"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT * FROM staff 
                        WHERE username = %s AND active = true
                    """, (username,))
                    return cur.fetchone()
        except Exception as e:
            logger.error(f"Error getting staff by username: {e}")
            return None
    
    def get_all_staff(self):
        """Get all staff members"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, username, name, email, role, department, phone, active, last_login, created_at
                        FROM staff 
                        ORDER BY name
                    """)
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting all staff: {e}")
            return []
    
    def add_staff(self, username, name, email, password_hash, role, department, phone=None):
        """Add a new staff member"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO staff 
                        (username, name, email, password_hash, role, department, phone, active, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, true, %s)
                        RETURNING id
                    """, (username, name, email, password_hash, role, department, phone, datetime.now()))
                    
                    staff_id = cur.fetchone()[0]
                    conn.commit()
                    return staff_id
        except Exception as e:
            logger.error(f"Error adding staff: {e}")
            return None
    
    def update_staff(self, staff_id, **kwargs):
        """Update staff member"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    update_fields = []
                    values = []
                    
                    for key, value in kwargs.items():
                        if value is not None:
                            update_fields.append(f"{key} = %s")
                            values.append(value)
                    
                    if not update_fields:
                        return False
                    
                    values.append(staff_id)
                    query = f"UPDATE staff SET {', '.join(update_fields)} WHERE id = %s"
                    
                    cur.execute(query, values)
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating staff: {e}")
            return False
    
    def delete_staff(self, staff_id):
        """Delete staff member (soft delete)"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        UPDATE staff 
                        SET active = false
                        WHERE id = %s
                    """, (staff_id,))
                    conn.commit()
                    return cur.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting staff: {e}")
            return False
    
    # ==================== EVENTS & ANNOUNCEMENTS METHODS ====================
    
    def get_upcoming_events(self, limit=10):
        """Get upcoming events"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, event_date, title_en, title_ar, 
                               description_en, description_ar, location, event_link, event_type
                        FROM events 
                        WHERE event_date >= CURRENT_DATE
                        ORDER BY event_date ASC
                        LIMIT %s
                    """, (limit,))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting events: {e}")
            return []
    
    def get_announcements(self, limit=10):
        """Get latest announcements"""
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT id, title_en, title_ar, content_en, content_ar, 
                               created_at, priority, link
                        FROM announcements 
                        WHERE is_active = true
                        ORDER BY priority DESC, created_at DESC
                        LIMIT %s
                    """, (limit,))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting announcements: {e}")
            return []
    
    def get_academic_calendar(self, academic_year=None):
        """Get academic calendar for a specific year"""
        if not academic_year:
            current_year = datetime.now().year
            if datetime.now().month >= 9:
                academic_year = f"{current_year}-{current_year + 1}"
            else:
                academic_year = f"{current_year - 1}-{current_year}"
        
        try:
            with self.get_connection() as conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("""
                        SELECT event_name_en, event_name_ar, event_date, event_type
                        FROM academic_calendar 
                        WHERE academic_year = %s
                        ORDER BY event_date ASC
                    """, (academic_year,))
                    return cur.fetchall()
        except Exception as e:
            logger.error(f"Error getting academic calendar: {e}")
            return []
    
    # ==================== DASHBOARD STATS METHODS ====================
    
    def get_dashboard_stats(self):
        """Get dashboard statistics"""
        try:
            stats = {
                'total_students': self.get_students_count(),
                'total_unanswered': self.get_unanswered_count(resolved=False),
                'total_faqs': len(self.get_all_faqs()),
                'feedback_stats': self.get_feedback_statistics()
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting dashboard stats: {e}")
            return {}