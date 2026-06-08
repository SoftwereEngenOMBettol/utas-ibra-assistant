# backend/app/services/chatbot_service.py

import logging
import random
import uuid
import base64
from datetime import datetime
import traceback

from .connector import DatabaseConnector

logger = logging.getLogger(__name__)


class UTASVirtualAssistant:
    """Complete UTAS Virtual Assistant with all features"""
    
    def __init__(self):
        self.db = DatabaseConnector()
        self.sessions = {}
        self.pdf_generator = None
        
        # Font Awesome CDN
        self.fontawesome = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">'
        
        # Conversation responses
        self.conversation_responses = {
            'en': {
                'greeting': [
                    "Hello! How can I help you with your UTAS inquiries today?",
                    "Hi there! What can I assist you with regarding your studies?",
                    "Greetings! Feel free to ask me about your courses, GPA, schedule, or anything UTAS-related."
                ],
                'how_are_you': [
                    "I'm doing great, thank you for asking! How can I assist you with your UTAS needs?",
                    "I'm functioning perfectly! Ready to help you with any UTAS-related questions."
                ],
                'thanks': [
                    "You're welcome! Is there anything else about UTAS I can help you with?",
                    "Happy to help! Let me know if you need any other information."
                ],
                'goodbye': [
                    "Goodbye! Feel free to return if you have more UTAS questions.",
                    "Take care! Come back anytime you need assistance with your studies."
                ],
                'default': [
                    "I'm here to help with UTAS-related questions! You can ask me about your GPA, schedule, courses, CIMS access, registration, exam dates, scholarships, internships, and more."
                ]
            },
            'ar': {
                'greeting': [
                    "مرحباً! كيف يمكنني مساعدتك في استفساراتك حول جامعة UTAS اليوم؟",
                    "أهلاً! بماذا يمكنني مساعدتك بخصوص دراستك؟",
                    "مرحباً بك! اسألني عن موادك، معدلك، جدولك، أو أي شيء يتعلق بالجامعة."
                ],
                'how_are_you': [
                    "أنا بخير، شكراً لسؤالك! كيف يمكنني مساعدتك؟",
                    "أنا ممتاز! جاهز لمساعدتك في أي استفسار عن الجامعة."
                ],
                'thanks': [
                    "العفو! هل هناك شيء آخر يمكنني مساعدتك به؟",
                    "سعيد بمساعدتك! أخبرني إذا احتجت أي معلومات أخرى."
                ],
                'goodbye': [
                    "مع السلامة! تفضل بالعودة إذا كان لديك المزيد من الأسئلة.",
                    "في أمان الله! تفضل بالعودة في أي وقت."
                ],
                'default': [
                    "أنا هنا للمساعدة في الأسئلة المتعلقة بجامعة UTAS! يمكنك سؤالي عن معدلك، جدولك، موادك، نظام CIMS، التسجيل، مواعيد الامتحانات، المنح الدراسية، فرص التدريب، والمزيد."
                ]
            }
        }
    
    # ==================== Helper Functions ====================
    
    def _detect_language(self, message, student_lang=None):
        if student_lang:
            return student_lang
        arabic_chars = sum(1 for c in message if '\u0600' <= c <= '\u06FF')
        total_chars = len(message.replace(' ', ''))
        if total_chars > 0 and (arabic_chars / total_chars) > 0.3:
            return 'ar'
        return 'en'
    
    
    def _get_pdf_generator(self):
        if self.pdf_generator is None:
            try:
                from app.services.pdf_generator import PDFGenerator
                self.pdf_generator = PDFGenerator()
                logger.info("PDF Generator initialized")
            except ImportError as e:
                logger.error(f"PDFGenerator not available: {e}")
                self.pdf_generator = None
        return self.pdf_generator
    
    # ==================== HTML Response Builder (Original Design) ====================
    
    def _build_html_response(self, content, title=None, lang='en'):
        """Build beautiful HTML response with Font Awesome - Original Design"""
        direction = 'rtl' if lang == 'ar' else 'ltr'
        font = "Cairo, 'Segoe UI', Arial, sans-serif" if lang == 'ar' else "'Segoe UI', Arial, sans-serif"
        
        title_html = f'<h2 style="margin: 0; font-size: 24px;">{title}</h2>' if title else ''
        
        return f'''
        {self.fontawesome}
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
    
    # ==================== 1. GPA QUERY HANDLER (Original Design) ====================
    
    def _handle_gpa_query(self, student_id, lang):
        """Handle GPA query with beautiful design - Original"""
        try:
            student = self.db.get_student(student_id)
            if not student:
                return self._get_fallback_response(lang)
            
            db_student_id = student['id']
            gpa_records = self.db.get_student_gpa(db_student_id)
            
            if not gpa_records:
                content = '<p><i class="fas fa-chart-line"></i> No GPA records found. Please check CIMS for your grades.</p>' if lang == 'en' else '<p><i class="fas fa-chart-line"></i> لا توجد سجلات للمعدل. الرجاء التحقق من CIMS لمعرفة درجاتك.</p>'
                return {'response': self._build_html_response(content, 'GPA Report' if lang == 'en' else 'تقرير المعدل', lang), 'language': lang, 'intent': 'gpa_query', 'from_faq': False}
            
            # Find cumulative GPA
            cumulative_gpa = None
            semester_gpa = None
            for record in gpa_records:
                if record.get('gpa_type') == 'cumulative':
                    cumulative_gpa = record.get('gpa_value')
                elif record.get('gpa_type') == 'semester':
                    semester_gpa = record.get('gpa_value')
            
            if cumulative_gpa is None and gpa_records:
                cumulative_gpa = gpa_records[0].get('gpa_value')
            
            # Determine status
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
                'response': self._build_html_response(content, 'Academic Transcript' if lang == 'en' else 'السجل الأكاديمي', lang),
                'language': lang,
                'intent': 'gpa_query',
                'from_faq': False
            }
        except Exception as e:
            logger.error(f"GPA error: {e}")
            return self._get_fallback_response(lang)
    
    # ==================== 2. SCHEDULE QUERY HANDLER (Original Design with Table) ====================
    
    def _handle_schedule_query(self, student_id, lang):
        """Handle schedule query with beautiful table - Original"""
        try:
            student = self.db.get_student(student_id)
            if not student:
                return self._get_fallback_response(lang)
            
            db_student_id = student['id']
            schedule = self.db.get_student_schedule(db_student_id)
            
            if not schedule:
                content = '<p><i class="fas fa-calendar-alt"></i> No schedule found for the current semester. Please check CIMS.</p>' if lang == 'en' else '<p><i class="fas fa-calendar-alt"></i> لا يوجد جدول للفصل الحالي. الرجاء التحقق من CIMS.</p>'
                return {'response': self._build_html_response(content, 'Schedule' if lang == 'en' else 'الجدول الدراسي', lang), 'language': lang, 'intent': 'schedule_query', 'from_faq': False}
            
            days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
            days_ar = ['الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس']
            time_slots = ['08:00-10:00', '10:00-12:00', '12:00-14:00', '14:00-16:00']
            
            table_html = '<div style="overflow-x: auto;"><table style="width: 100%; border-collapse: collapse;">'
            table_html += '<thead><tr style="background: linear-gradient(135deg, #1800ad 0%, #d3cdf8 100%); color: white;">'
            table_html += f'<th style="padding: 12px; text-align: {"right" if lang == "ar" else "left"};"><i class="fas fa-clock"></i> {"Time" if lang == "en" else "الوقت"}</th>'
            for day in (days_ar if lang == 'ar' else days):
                table_html += f'<th style="padding: 12px; text-align: {"right" if lang == "ar" else "left"};">{day}</th>'
            table_html += '</tr></thead><tbody>'
            
            for time_slot in time_slots:
                table_html += f'<tr style="border-bottom: 1px solid #e0e0e0;"><td style="padding: 12px; font-weight: 600; background: #d3cdf8;">{time_slot}</td>'
                for day in days:
                    course_at_time = None
                    for course in schedule:
                        if course.get('day_of_week') == day:
                            time_start = str(course.get('time_start', ''))[:5]
                            time_end = str(course.get('time_end', ''))[:5]
                            course_time = f"{time_start}-{time_end}"
                            if course_time == time_slot:
                                course_at_time = course
                                break
                    if course_at_time:
                        table_html += f'<td style="padding: 12px;"><strong>{course_at_time.get("course_code", "")}</strong><br/><span style="font-size: 12px; color: #666;">{course_at_time.get("course_name", "")}</span><br/><span style="font-size: 11px; color: #999;"><i class="fas fa-location-dot"></i> {course_at_time.get("room", "TBA")}</span></td>'
                    else:
                        table_html += '<td style="padding: 12px; color: #ccc; text-align: center;">—</td>'
                table_html += '</tr>'
            table_html += '</tbody></tr></div>'
            table_html += '<p style="margin-top: 15px; text-align: center;"><i class="fas fa-download"></i> Download timetable PDF by saying "Download my timetable"</p>'
            
            return {
                'response': self._build_html_response(table_html, 'Student Time Table' if lang == 'en' else 'الجدول الدراسي', lang),
                'language': lang,
                'intent': 'schedule_query',
                'from_faq': False
            }
        except Exception as e:
            logger.error(f"Schedule error: {e}")
            return self._get_fallback_response(lang)
    
    # ==================== 3. ATTENDANCE QUERY HANDLER (Original Design) ====================
    
    def _handle_attendance_query(self, student_id, lang):
        """Handle attendance query with beautiful design - Original"""
        try:
            student = self.db.get_student(student_id)
            if not student:
                return self._get_fallback_response(lang)
            
            db_student_id = student['id']
            attendance = self.db.get_attendance_percentage(db_student_id)
            
            if not attendance:
                content = '<p><i class="fas fa-chart-simple"></i> No attendance records found. Please check CIMS.</p>' if lang == 'en' else '<p><i class="fas fa-chart-simple"></i> لا توجد سجلات حضور. الرجاء التحقق من CIMS.</p>'
                return {'response': self._build_html_response(content, 'Attendance Report' if lang == 'en' else 'تقرير الحضور', lang), 'language': lang, 'intent': 'attendance_query', 'from_faq': False}
            
            # Calculate overall attendance
            total_percentage = sum([r.get('percentage', 0) for r in attendance]) / len(attendance) if attendance else 0
            
            # Determine status
            if total_percentage >= 85:
                status = "Excellent Attendance" if lang == 'en' else "حضور ممتاز"
                status_color = "#1800ad"
            elif total_percentage >= 75:
                status = "Good Standing" if lang == 'en' else "جيد"
                status_color = "#28a745"
            elif total_percentage >= 65:
                status = "Warning" if lang == 'en' else "تحذير"
                status_color = "#ff620c"
            else:
                status = "Critical - Risk of DN" if lang == 'en' else "حرج - خطر الحرمان"
                status_color = "#dc3545"
            
            table_html = '<table style="width: 100%; border-collapse: collapse;"><thead><tr style="background: linear-gradient(135deg, #1800ad 0%, #d3cdf8 100%); color: white;">'
            table_html += f'<th style="padding: 12px; text-align: {"right" if lang == "ar" else "left"};">{"Course" if lang == "en" else "المادة"}</th>'
            table_html += f'<th style="padding: 12px; text-align: center;">{"Attendance" if lang == "en" else "الحضور"}</th>'
            table_html += f'<th style="padding: 12px; text-align: center;">{"Status" if lang == "en" else "الحالة"}</th>'
            table_html += '</tr></thead><tbody>'
            
            for record in attendance:
                percentage = record.get('percentage', 0)
                status_color_course = "#28a745" if percentage >= 75 else "#dc3545"
                status_text = "Good" if percentage >= 75 else "Warning" if lang == 'en' else "جيد" if percentage >= 75 else "تحذير"
                course_name = record.get('course_name', record.get('course_code', ''))
                table_html += f'<tr style="border-bottom: 1px solid #e0e0e0;"><td style="padding: 12px;"><strong>{record.get("course_code", "")}</strong><br/><span style="font-size: 12px; color: #666;">{course_name}</span></td>'
                table_html += f'<td style="padding: 12px; text-align: center;"><span style="font-weight: bold; color: {status_color_course};">{percentage:.1f}%</span></td>'
                table_html += f'<td style="padding: 12px; text-align: center;"><span style="background: {status_color_course}20; color: {status_color_course}; padding: 4px 12px; border-radius: 20px; font-size: 12px;"><i class="fas {"fa-check-circle" if percentage >= 75 else "fa-exclamation-triangle"}"></i> {status_text}</span></td></tr>'
            
            table_html += '</tbody></table>'
            
            content = f'''
            <div style="background: {status_color}20; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
                <p style="margin: 0; font-size: 24px; font-weight: bold; color: {status_color};">{total_percentage:.1f}%</p>
                <p style="margin: 5px 0 0; font-size: 16px; color: {status_color};"><i class="fas fa-chart-line"></i> {status}</p>
            </div>
            {table_html}
            <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin-top: 15px;">
                <p style="margin: 0;"><strong><i class="fas fa-exclamation-triangle"></i> {"Minimum attendance required: 75% per course" if lang == 'en' else "الحد الأدنى للحضور: 75% لكل مادة"}</strong></p>
                <p style="margin: 10px 0 0;"><i class="fas fa-download"></i> {"Download full attendance report by saying 'Download attendance report'" if lang == 'en' else "يمكنك تحميل تقرير الحضور الكامل بقولك 'تحميل تقرير الحضور'"}</p>
            </div>
            '''
            
            return {
                'response': self._build_html_response(content, 'Attendance Report' if lang == 'en' else 'تقرير الحضور', lang),
                'language': lang,
                'intent': 'attendance_query',
                'from_faq': False
            }
        except Exception as e:
            logger.error(f"Attendance error: {e}")
            return self._get_fallback_response(lang)
    
    # ==================== 4. PDF HANDLER (Original) ====================
    
    def _handle_pdf_request(self, message, student_id, lang, pdf_type):
        """Handle PDF download requests - Original"""
        try:
            print(f"Generating {pdf_type} PDF for student: {student_id}")
            
            pdf_gen = self._get_pdf_generator()
            if not pdf_gen:
                return self._get_fallback_response(lang)
            
            student = self.db.get_student(student_id)
            if not student:
                return self._get_fallback_response(lang)
            
            student_data = {
                "name": student.get('name', 'Student'),
                "student_id": student_id,
                "department": student.get('department', 'Not specified'),
                "current_semester": student.get('current_semester', 'Current Semester'),
                "academic_year": "2025-2026"
            }
            
            pdf_content = None
            filename = None
            db_student_id = student['id']
            
            if pdf_type == 'timetable':
                schedule = self.db.get_student_schedule(db_student_id)
                if schedule:
                    schedule_list = [{
                        'day_of_week': s.get('day_of_week'),
                        'time_start': s.get('time_start'),
                        'time_end': s.get('time_end'),
                        'course_code': s.get('course_code', ''),
                        'course_name': s.get('course_name', ''),
                        'room': s.get('room', 'TBA'),
                        'lecturer': s.get('lecturer', 'TBA')
                    } for s in schedule]
                    pdf_content = pdf_gen.generate_timetable_pdf(student_data, schedule_list)
                    filename = f"timetable_{student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    response_text = "Here's your timetable!" if lang == 'en' else "هذا جدولك الدراسي!"
            
            elif pdf_type == 'attendance':
                attendance = self.db.get_attendance_percentage(db_student_id)
                if attendance:
                    attendance_list = [{
                        'course_code': a.get('course_code', ''),
                        'course_name': a.get('course_name', a.get('course_code', '')),
                        'total_classes': a.get('total_classes', 0),
                        'absences': a.get('absences', 0),
                        'percentage': a.get('percentage', 0)
                    } for a in attendance]
                    pdf_content = pdf_gen.generate_attendance_pdf(student_data, attendance_list)
                    filename = f"attendance_{student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    response_text = "Here's your attendance report!" if lang == 'en' else "هذا تقرير الحضور!"
            
            elif pdf_type == 'transcript':
                transcript = self.db.get_student_transcript(db_student_id)
                if transcript:
                    transcript_list = [{
                        'semester': t.get('semester', ''),
                        'course_code': t.get('course_code', ''),
                        'course_name': t.get('course_name', ''),
                        'credit_hours': t.get('credit_hours', 0),
                        'grade': t.get('grade', ''),
                        'points': t.get('points', 0),
                        'result': t.get('result', '')
                    } for t in transcript]
                    pdf_content = pdf_gen.generate_transcript_pdf(student_data, transcript_list, None)
                    filename = f"transcript_{student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    response_text = "Here's your transcript!" if lang == 'en' else "هذا كشف الدرجات الخاص بك!"
            
            elif pdf_type == 'gpa':
                gpa_records = self.db.get_student_gpa(db_student_id)
                if gpa_records:
                    gpa_list = [{
                        'semester': g.get('semester', ''),
                        'gpa_type': g.get('gpa_type', ''),
                        'gpa_value': g.get('gpa_value', 0)
                    } for g in gpa_records]
                    pdf_content = pdf_gen.generate_gpa_report_pdf(student_data, gpa_list, None)
                    filename = f"gpa_report_{student_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    response_text = "Here's your GPA report!" if lang == 'en' else "هذا تقرير المعدل الخاص بك!"
            
            if pdf_content and filename:
                pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
                return {
                    'response': response_text,
                    'language': lang,
                    'intent': f'{pdf_type}_pdf',
                    'from_faq': False,
                    'pdf_data': pdf_base64,
                    'filename': filename,
                    'content_type': 'application/pdf'
                }
            
            return self._get_fallback_response(lang)
                
        except Exception as e:
            logger.error(f"PDF error: {e}")
            traceback.print_exc()
            return self._get_fallback_response(lang)
    
    # ==================== 5. CIMS GRADES LINK HANDLER ====================
    
    def _handle_cims_grades_link(self, student_id, lang):
        """Provide direct link to CIMS grades"""
        cims_url = self._get_cims_link('login')
        
        content = f'''
        <div style="background: #d3cdf8; padding: 15px; border-radius: 10px;">
            <p><strong><i class="fas fa-chart-line"></i> {"To view your grades and GPA:" if lang == 'en' else "لعرض درجاتك ومعدلك:"}</strong></p>
            <p>1. <i class="fas fa-sign-in-alt"></i> {"Log in to CIMS portal" if lang == 'en' else "سجل دخول إلى نظام CIMS"}: <a href="{cims_url}" target="_blank">{cims_url}</a></p>
            <p>2. <i class="fas fa-tachometer-alt"></i> {"Go to 'Student Services' → 'Grades' or 'Academic Record'" if lang == 'en' else "اذهب إلى 'الخدمات الطلابية' ← 'الدرجات' أو 'السجل الأكاديمي'"}</p>
            <p>3. <i class="fas fa-calendar-alt"></i> {"Select the semester to view your grades" if lang == 'en' else "اختر الفصل لعرض درجاتك"}</p>
        </div>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin-top: 15px;">
            <p><strong><i class="fas fa-info-circle"></i> {"Note:" if lang == 'en' else "ملاحظة:"}</strong> {"Your grades are only available after logging in to CIMS." if lang == 'en' else "درجاتك متاحة فقط بعد تسجيل الدخول إلى CIMS."}</p>
            <p><i class="fas fa-phone-alt"></i> {"Need help? Contact IT Support: ithelp@utas.edu.om" if lang == 'en' else "تحتاج مساعدة؟ اتصل بدعم تقنية المعلومات: ithelp@utas.edu.om"}</p>
        </div>
        '''
        
        return {
            'response': self._build_html_response(content, 'CIMS Grades Access' if lang == 'en' else 'الوصول إلى الدرجات في CIMS', lang),
            'language': lang,
            'intent': 'cims_grades',
            'from_faq': True
        }
    
    # ==================== 6. REGISTRATION HANDLER ====================
    
    def _handle_registration(self, student_id, lang):
        content = '''
        <ol style="margin: 0 0 15px 20px;">
            <li><i class="fas fa-sign-in-alt"></i> Log in to <a href="https://cims.utas.edu.om" target="_blank">CIMS Portal</a></li>
            <li><i class="fas fa-tachometer-alt"></i> Go to "Student Services" → "Registration"</li>
            <li><i class="fas fa-calendar-alt"></i> Select the current semester</li>
            <li><i class="fas fa-search"></i> Search for courses by code or name</li>
            <li><i class="fas fa-plus-circle"></i> Add courses to your schedule</li>
            <li><i class="fas fa-check-circle"></i> Submit and confirm registration</li>
        </ol>
        <div style="background: #d3cdf8; padding: 15px; border-radius: 10px;">
            <p><i class="fas fa-info-circle"></i> <strong>Important:</strong> Max 18 credits | Add/Drop: First 2 weeks</p>
        </div>
        <p style="margin-top: 15px;"><i class="fas fa-chalkboard-user"></i> Need help? Contact your academic advisor.</p>
        ''' if lang == 'en' else '''
        <ol style="margin: 0 0 15px 20px;">
            <li><i class="fas fa-sign-in-alt"></i> سجل دخول إلى <a href="https://cims.utas.edu.om" target="_blank">نظام CIMS</a></li>
            <li><i class="fas fa-tachometer-alt"></i> اذهب إلى "الخدمات الطلابية" ← "التسجيل"</li>
            <li><i class="fas fa-calendar-alt"></i> اختر الفصل الحالي</li>
            <li><i class="fas fa-search"></i> ابحث عن المواد بالرمز أو الاسم</li>
            <li><i class="fas fa-plus-circle"></i> أضف المواد إلى جدولك</li>
            <li><i class="fas fa-check-circle"></i> أرسل وأكد التسجيل</li>
        </ol>
        <div style="background: #d3cdf8; padding: 15px; border-radius: 10px;">
            <p><i class="fas fa-info-circle"></i> <strong>مهم:</strong> الحد الأقصى 18 ساعة | الإضافة والحذف: أول أسبوعين</p>
        </div>
        <p style="margin-top: 15px;"><i class="fas fa-chalkboard-user"></i> تحتاج مساعدة؟ تواصل مع مرشدك الأكاديمي.</p>
        '''
        return {'response': self._build_html_response(content, 'Course Registration Guide' if lang == 'en' else 'دليل تسجيل المواد', lang), 'language': lang, 'intent': 'registration', 'from_faq': True}
    
    # ==================== 7. CIMS ACCESS HANDLER ====================
    
    def _handle_cims_access(self, student_id, lang):
        cims_url = self._get_cims_link('login')
        content = f'''
        <p><i class="fas fa-external-link-alt"></i> Access CIMS: <a href="{cims_url}" target="_blank">{cims_url}</a></p>
        <p><strong><i class="fas fa-user-graduate"></i> Login:</strong> Use your student ID and password</p>
        <div style="margin-top: 15px; padding: 10px; background: #d3cdf8; border-left: 4px solid #1800ad;">
            <i class="fas fa-key"></i> Forgot password? Click "Forgot Password" or contact IT Support: ithelp@utas.edu.om
        </div>
        <p style="margin-top: 15px;"><strong><i class="fas fa-list"></i> Features:</strong></p>
        <ul>
            <li><i class="fas fa-calendar-alt"></i> View schedule</li>
            <li><i class="fas fa-chart-line"></i> Check grades and GPA</li>
            <li><i class="fas fa-book"></i> Register for courses</li>
            <li><i class="fas fa-user-check"></i> View attendance</li>
            <li><i class="fas fa-file-alt"></i> Access transcript</li>
        </ul>
        ''' if lang == 'en' else f'''
        <p><i class="fas fa-external-link-alt"></i> الدخول إلى CIMS: <a href="{cims_url}" target="_blank">{cims_url}</a></p>
        <p><strong><i class="fas fa-user-graduate"></i> تسجيل الدخول:</strong> استخدم رقم الطالب وكلمة المرور</p>
        <div style="margin-top: 15px; padding: 10px; background: #d3cdf8; border-right: 4px solid #1800ad;">
            <i class="fas fa-key"></i> نسيت كلمة المرور؟ اضغط "نسيت كلمة المرور" أو اتصل بدعم تقنية المعلومات: ithelp@utas.edu.om
        </div>
        <p style="margin-top: 15px;"><strong><i class="fas fa-list"></i> الخدمات:</strong></p>
        <ul>
            <li><i class="fas fa-calendar-alt"></i> عرض الجدول</li>
            <li><i class="fas fa-chart-line"></i> مراجعة الدرجات والمعدل</li>
            <li><i class="fas fa-book"></i> تسجيل المواد</li>
            <li><i class="fas fa-user-check"></i> متابعة الحضور</li>
            <li><i class="fas fa-file-alt"></i> كشف الدرجات</li>
        </ul>
        '''
        return {'response': self._build_html_response(content, 'CIMS Student Portal' if lang == 'en' else 'نظام CIMS للطلاب', lang), 'language': lang, 'intent': 'cims_access', 'from_faq': True}
    
    # ==================== 8. ADVISOR HANDLER ====================
    
    def _handle_advisor_contact(self, student_id, lang):
        try:
            student = self.db.get_student(student_id)
            if not student or not student.get('advisor'):
                content = '<p><i class="fas fa-user-graduate"></i> Your advisor information is not available. Please visit Student Affairs.</p>' if lang == 'en' else '<p><i class="fas fa-user-graduate"></i> معلومات مرشدك غير متوفرة. الرجاء زيارة شؤون الطلاب.</p>'
                return {'response': self._build_html_response(content, 'Academic Advisor' if lang == 'en' else 'المرشد الأكاديمي', lang), 'language': lang, 'intent': 'advisor_contact', 'from_faq': False}
            
            content = f'''
            <div style="text-align: center; margin-bottom: 20px;">
                <div style="background: #d3cdf8; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                    <i class="fas fa-chalkboard-user" style="font-size: 40px; color: #1800ad;"></i>
                </div>
                <p style="font-size: 20px; font-weight: bold; margin: 10px 0 5px;">{student.get('advisor', 'Not Assigned')}</p>
                <p style="color: #666; margin: 0;"><i class="fas fa-building"></i> {student.get('department', 'Academic Advisor')}</p>
            </div>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 10px;">
                <p><i class="fas fa-envelope"></i> <strong>Email:</strong> {student.get('advisor_email', 'advisor@utas.edu.om')}</p>
                <p><i class="fas fa-clock"></i> <strong>Office Hours:</strong> Sunday-Thursday 9:00 AM - 2:00 PM</p>
                <p><i class="fas fa-location-dot"></i> <strong>Location:</strong> Academic Advising Office, Building A, 2nd Floor</p>
            </div>
            <p style="margin-top: 15px;"><i class="fas fa-calendar-check"></i> Schedule an appointment through CIMS or visit during office hours.</p>
            ''' if lang == 'en' else f'''
            <div style="text-align: center; margin-bottom: 20px;">
                <div style="background: #d3cdf8; width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto;">
                    <i class="fas fa-chalkboard-user" style="font-size: 40px; color: #1800ad;"></i>
                </div>
                <p style="font-size: 20px; font-weight: bold; margin: 10px 0 5px;">{student.get('advisor', 'غير محدد')}</p>
                <p style="color: #666; margin: 0;"><i class="fas fa-building"></i> {student.get('department', 'مرشد أكاديمي')}</p>
            </div>
            <div style="background: #f8f9fa; padding: 15px; border-radius: 10px;">
                <p><i class="fas fa-envelope"></i> <strong>البريد الإلكتروني:</strong> {student.get('advisor_email', 'advisor@utas.edu.om')}</p>
                <p><i class="fas fa-clock"></i> <strong>ساعات العمل:</strong> الأحد-الخميس 9ص - 2م</p>
                <p><i class="fas fa-location-dot"></i> <strong>الموقع:</strong> مكتب الإرشاد الأكاديمي، المبنى أ، الطابق الثاني</p>
            </div>
            <p style="margin-top: 15px;"><i class="fas fa-calendar-check"></i> احجز موعداً عبر CIMS أو قم بزيارة المكتب خلال ساعات العمل.</p>
            '''
            return {'response': self._build_html_response(content, 'Your Academic Advisor' if lang == 'en' else 'مرشدك الأكاديمي', lang), 'language': lang, 'intent': 'advisor_contact', 'from_faq': False}
        except Exception as e:
            logger.error(f"Advisor error: {e}")
            return self._get_fallback_response(lang)
    
    # ==================== 9. EXAM SCHEDULE HANDLER ====================
    
    def _handle_exam_schedule(self, student_id, lang):
        content = '''
        <div style="background: #d3cdf8; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
            <p><strong><i class="fas fa-calendar-alt"></i> Important Exam Dates (Spring 2026):</strong></p>
            <p>• <i class="fas fa-pen-alt"></i> Midterm Exams: March 9-20, 2026</p>
            <p>• <i class="fas fa-pen-fancy"></i> Final Exams: May 4-15, 2026</p>
        </div>
        <p><i class="fas fa-info-circle"></i> Your detailed schedule is on CIMS portal.</p>
        <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-left: 4px solid #1800ad;">
            <i class="fas fa-lightbulb"></i> Tips: Arrive 15 minutes early, bring your ID
        </div>
        ''' if lang == 'en' else '''
        <div style="background: #d3cdf8; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
            <p><strong><i class="fas fa-calendar-alt"></i> تواريخ الامتحانات الهامة (الفصل الثاني 2026):</strong></p>
            <p>• <i class="fas fa-pen-alt"></i> امتحانات منتصف الفصل: 9-20 مارس 2026</p>
            <p>• <i class="fas fa-pen-fancy"></i> الامتحانات النهائية: 4-15 مايو 2026</p>
        </div>
        <p><i class="fas fa-info-circle"></i> جدولك المفصل متاح على نظام CIMS.</p>
        <div style="margin-top: 15px; padding: 10px; background: #f8f9fa; border-right: 4px solid #1800ad;">
            <i class="fas fa-lightbulb"></i> نصائح: احضر قبل 15 دقيقة، أحضر بطاقتك
        </div>
        '''
        return {'response': self._build_html_response(content, 'Exam Schedule' if lang == 'en' else 'جدول الامتحانات', lang), 'language': lang, 'intent': 'exam_schedule', 'from_faq': True}
    
    # ==================== 10. TRANSCRIPT HANDLER ====================
    
    def _handle_transcript_query(self, student_id, lang):
        content = '<p><i class="fas fa-file-alt"></i> Your transcript is available on CIMS portal.</p><p style="text-align: center;"><i class="fas fa-download"></i> Download full transcript PDF by saying "Download transcript"</p>' if lang == 'en' else '<p><i class="fas fa-file-alt"></i> كشف درجاتك متاح على بوابة CIMS.</p><p style="text-align: center;"><i class="fas fa-download"></i> حمل كشف الدرجات الكامل بصيغة PDF بقولك "تحميل كشف الدرجات"</p>'
        return {'response': self._build_html_response(content, 'Academic Transcript' if lang == 'en' else 'كشف الدرجات الأكاديمي', lang), 'language': lang, 'intent': 'transcript_query', 'from_faq': True}
    
    # ==================== 11. CV WRITING HANDLER ====================
    
    def _handle_cv_writing(self, student_id, lang):
        content = '''
        <p><strong><i class="fas fa-file-alt"></i> Tips for an effective CV:</strong></p>
        <ul>
            <li><i class="fas fa-compress"></i> Keep it concise (1-2 pages)</li>
            <li><i class="fas fa-address-card"></i> Include contact information</li>
            <li><i class="fas fa-graduation-cap"></i> List education in reverse order</li>
            <li><i class="fas fa-star"></i> Highlight skills and achievements</li>
            <li><i class="fas fa-briefcase"></i> Include experience and internships</li>
            <li><i class="fas fa-spell-check"></i> Proofread for errors</li>
        </ul>
        <div style="background: #d3cdf8; padding: 15px; border-radius: 10px;">
            <p><i class="fas fa-download"></i> <strong>Resources:</strong> CV templates at Career Guidance Office</p>
            <p><i class="fas fa-envelope"></i> Contact: careers@utas.edu.om</p>
        </div>
        ''' if lang == 'en' else '''
        <p><strong><i class="fas fa-file-alt"></i> نصائح لسيرة ذاتية فعالة:</strong></p>
        <ul>
            <li><i class="fas fa-compress"></i> اجعلها موجزة (1-2 صفحة)</li>
            <li><i class="fas fa-address-card"></i> أضف معلومات الاتصال</li>
            <li><i class="fas fa-graduation-cap"></i> رتب التعليم من الأحدث للأقدم</li>
            <li><i class="fas fa-star"></i> أبرز المهارات والإنجازات</li>
            <li><i class="fas fa-briefcase"></i> أضف الخبرات والتدريب</li>
            <li><i class="fas fa-spell-check"></i> دققها لغوياً</li>
        </ul>
        <div style="background: #d3cdf8; padding: 15px; border-radius: 10px;">
            <p><i class="fas fa-download"></i> <strong>الموارد:</strong> قوالب السيرة الذاتية في مكتب التوجيه المهني</p>
            <p><i class="fas fa-envelope"></i> اتصل: careers@utas.edu.om</p>
        </div>
        '''
        return {'response': self._build_html_response(content, 'How to Write a Professional CV' if lang == 'en' else 'كيف تكتب سيرة ذاتية احترافية', lang), 'language': lang, 'intent': 'cv_writing', 'from_faq': True}
    
    # ==================== 12. PASSWORD RESET HANDLER ====================
    
    def _handle_password_reset(self, student_id, lang):
        cims_url = self._get_cims_link('login')
        content = f'''
        <p><strong><i class="fas fa-key"></i> Steps to reset your password:</strong></p>
        <ol>
            <li><i class="fas fa-external-link-alt"></i> Go to <a href="{cims_url}" target="_blank">CIMS Login Page</a></li>
            <li><i class="fas fa-question-circle"></i> Click "Forgot Password"</li>
            <li><i class="fas fa-id-card"></i> Enter Student ID and registered email</li>
            <li><i class="fas fa-envelope"></i> Check email for reset link</li>
            <li><i class="fas fa-pen"></i> Follow instructions to create new password</li>
        </ol>
        <div style="background: #d3cdf8; padding: 10px; border-radius: 8px;">
            <p><i class="fas fa-phone-alt"></i> <strong>Need help?</strong> Contact IT Support: ithelp@utas.edu.om</p>
        </div>
        ''' if lang == 'en' else f'''
        <p><strong><i class="fas fa-key"></i> خطوات إعادة تعيين كلمة المرور:</strong></p>
        <ol>
            <li><i class="fas fa-external-link-alt"></i> اذهب إلى <a href="{cims_url}" target="_blank">صفحة دخول CIMS</a></li>
            <li><i class="fas fa-question-circle"></i> انقر "نسيت كلمة المرور"</li>
            <li><i class="fas fa-id-card"></i> أدخل الرقم الجامعي والبريد الإلكتروني</li>
            <li><i class="fas fa-envelope"></i> تحقق من بريدك للحصول على رابط إعادة التعيين</li>
            <li><i class="fas fa-pen"></i> اتبع التعليمات لإنشاء كلمة مرور جديدة</li>
        </ol>
        <div style="background: #d3cdf8; padding: 10px; border-radius: 8px;">
            <p><i class="fas fa-phone-alt"></i> <strong>تحتاج مساعدة؟</strong> اتصل بدعم تقنية المعلومات: ithelp@utas.edu.om</p>
        </div>
        '''
        return {'response': self._build_html_response(content, 'Reset Your Password' if lang == 'en' else 'إعادة تعيين كلمة المرور', lang), 'language': lang, 'intent': 'password_reset', 'from_faq': True}
    
    # ==================== 13. ADD/DROP DEADLINE HANDLER ====================
    
    def _handle_add_drop_deadline(self, student_id, lang):
        content = '''
        <div style="text-align: center; margin-bottom: 20px;">
            <p style="font-size: 36px; font-weight: bold; color: #dc3545; margin: 0;"><i class="fas fa-calendar-times"></i> February 28, 2026</p>
            <p style="color: #666;">(2 weeks from semester start)</p>
        </div>
        <div style="background: #d3cdf8; padding: 15px; border-radius: 10px;">
            <p><i class="fas fa-info-circle"></i> <strong>Important Notes:</strong></p>
            <p>• <i class="fas fa-plus-circle"></i> Add/drop courses without penalty during this period</p>
            <p>• <i class="fas fa-exclamation-triangle"></i> After deadline, drops result in 'W' grade</p>
            <p>• <i class="fas fa-chart-line"></i> Max 18 credit hours | Min 12 credit hours</p>
        </div>
        <p style="margin-top: 15px;"><i class="fas fa-chalkboard-user"></i> Need help? Contact your academic advisor.</p>
        ''' if lang == 'en' else '''
        <div style="text-align: center; margin-bottom: 20px;">
            <p style="font-size: 36px; font-weight: bold; color: #dc3545; margin: 0;"><i class="fas fa-calendar-times"></i> 28 فبراير 2026</p>
            <p style="color: #666;">(أسبوعين من بداية الفصل)</p>
        </div>
        <div style="background: #d3cdf8; padding: 15px; border-radius: 10px;">
            <p><i class="fas fa-info-circle"></i> <strong>ملاحظات مهمة:</strong></p>
            <p>• <i class="fas fa-plus-circle"></i> يمكنك إضافة أو حذف المواد بدون عقوبات</p>
            <p>• <i class="fas fa-exclamation-triangle"></i> بعد الموعد، الحذف يؤدي إلى تقدير W</p>
            <p>• <i class="fas fa-chart-line"></i> الحد الأقصى 18 ساعة | الحد الأدنى 12 ساعة</p>
        </div>
        <p style="margin-top: 15px;"><i class="fas fa-chalkboard-user"></i> تحتاج مساعدة؟ تواصل مع مرشدك الأكاديمي.</p>
        '''
        return {'response': self._build_html_response(content, 'Add/Drop Deadline' if lang == 'en' else 'موعد الحذف والإضافة', lang), 'language': lang, 'intent': 'add_drop_deadline', 'from_faq': True}
    
    # ==================== 14. SCHOLARSHIPS HANDLER ====================
    
    def _handle_scholarships(self, student_id, lang):
        content = '''
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px; margin-bottom: 20px;">
            <div style="background: #d3cdf8; padding: 15px; border-radius: 10px;">
                <h4><i class="fas fa-trophy"></i> Merit Scholarship</h4>
                <p>100% tuition | CGPA >= 3.75</p>
            </div>
            <div style="background: #d3cdf8; padding: 15px; border-radius: 10px;">
                <h4><i class="fas fa-star"></i> Academic Excellence</h4>
                <p>50% tuition | CGPA >= 3.5</p>
            </div>
            <div style="background: #d3cdf8; padding: 15px; border-radius: 10px;">
                <h4><i class="fas fa-futbol"></i> Sports Scholarship</h4>
                <p>25% tuition | National team member</p>
            </div>
        </div>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 10px;">
            <p><i class="fas fa-graduation-cap"></i> Apply via CIMS → "Student Services" → "Scholarships"</p>
            <p><i class="fas fa-calendar-alt"></i> Deadlines: Fall: July 31 | Spring: December 15</p>
            <p><i class="fas fa-envelope"></i> Contact: financial.aid@utas.edu.om</p>
        </div>
        ''' if lang == 'en' else '''
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px; margin-bottom: 20px;">
            <div style="background: #d3cdf8; padding: 15px; border-radius: 10px;">
                <h4><i class="fas fa-trophy"></i> منحة التفوق</h4>
                <p>100% رسوم | معدل >= 3.75</p>
            </div>
            <div style="background: #d3cdf8; padding: 15px; border-radius: 10px;">
                <h4><i class="fas fa-star"></i> التميز الأكاديمي</h4>
                <p>50% رسوم | معدل >= 3.5</p>
            </div>
            <div style="background: #d3cdf8; padding: 15px; border-radius: 10px;">
                <h4><i class="fas fa-futbol"></i> المنحة الرياضية</h4>
                <p>25% رسوم | لاعب منتخب وطني</p>
            </div>
        </div>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 10px;">
            <p><i class="fas fa-graduation-cap"></i> قدم عبر CIMS ← "الخدمات الطلابية" ← "المنح الدراسية"</p>
            <p><i class="fas fa-calendar-alt"></i> المواعيد: الفصل الأول: 31 يوليو | الفصل الثاني: 15 ديسمبر</p>
            <p><i class="fas fa-envelope"></i> اتصل: financial.aid@utas.edu.om</p>
        </div>
        '''
        return {'response': self._build_html_response(content, 'Scholarships & Financial Aid' if lang == 'en' else 'المنح والمساعدات المالية', lang), 'language': lang, 'intent': 'scholarships', 'from_faq': True}
    
    # ==================== 15. INTERNSHIPS & JOBS HANDLER ====================
    
    def _handle_internships_jobs(self, student_id, lang):
        content = '''
        <div style="background: #d3cdf8; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
            <p><strong><i class="fas fa-clipboard-list"></i> Internship Requirements:</strong></p>
            <ul>
                <li><i class="fas fa-clock"></i> Completed 60+ credit hours</li>
                <li><i class="fas fa-chart-line"></i> CGPA >= 2.5</li>
                <li><i class="fas fa-user-check"></i> Advisor approval required</li>
            </ul>
        </div>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 10px;">
            <p><i class="fas fa-search"></i> <strong>How to find opportunities:</strong></p>
            <ul>
                <li><i class="fas fa-desktop"></i> Check CIMS "Career Services"</li>
                <li><i class="fas fa-building"></i> Visit Career Guidance Office</li>
                <li><i class="fas fa-calendar-alt"></i> Attend Career Fair (March)</li>
            </ul>
        </div>
        <p style="margin-top: 15px;"><i class="fas fa-calendar-alt"></i> Career Fair 2026: March 15-16, 2026</p>
        <p><i class="fas fa-envelope"></i> Contact: careers@utas.edu.om</p>
        ''' if lang == 'en' else '''
        <div style="background: #d3cdf8; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
            <p><strong><i class="fas fa-clipboard-list"></i> متطلبات التدريب:</strong></p>
            <ul>
                <li><i class="fas fa-clock"></i> إكمال 60+ ساعة معتمدة</li>
                <li><i class="fas fa-chart-line"></i> معدل >= 2.5</li>
                <li><i class="fas fa-user-check"></i> موافقة المرشد مطلوبة</li>
            </ul>
        </div>
        <div style="background: #f8f9fa; padding: 15px; border-radius: 10px;">
            <p><i class="fas fa-search"></i> <strong>كيفية إيجاد الفرص:</strong></p>
            <ul>
                <li><i class="fas fa-desktop"></i> تحقق من CIMS "الخدمات المهنية"</li>
                <li><i class="fas fa-building"></i> قم بزيارة مكتب التوجيه المهني</li>
                <li><i class="fas fa-calendar-alt"></i> احضر معرض التوظيف (مارس)</li>
            </ul>
        </div>
        <p style="margin-top: 15px;"><i class="fas fa-calendar-alt"></i> معرض التوظيف 2026: 15-16 مارس 2026</p>
        <p><i class="fas fa-envelope"></i> اتصل: careers@utas.edu.om</p>
        '''
        return {'response': self._build_html_response(content, 'Internship & Job Opportunities' if lang == 'en' else 'فرص التدريب والوظائف', lang), 'language': lang, 'intent': 'internships_jobs', 'from_faq': True}
    
    # ==================== 16. EMERGENCY HANDLER ====================
    
    def _handle_emergency(self, student_id, lang):
        content = '''
        <div style="background: #fee2e2; padding: 15px; border-radius: 10px; margin-bottom: 15px; border-left: 4px solid #dc3545;">
            <p><strong><i class="fas fa-phone-alt"></i> Emergency Contacts:</strong></p>
            <p>• <i class="fas fa-shield-alt"></i> Campus Security: 1234 (int) / +968 1234 5678</p>
            <p>• <i class="fas fa-ambulance"></i> Ambulance/Police/Fire: 999</p>
            <p>• <i class="fas fa-hospital-user"></i> UTAS Clinic: 1235 (int)</p>
            <p>• <i class="fas fa-clock"></i> After Hours: +968 9876 5432</p>
        </div>
        <div style="background: #d3cdf8; padding: 15px; border-radius: 10px;">
            <p><i class="fas fa-kit-medical"></i> First Aid Kits in every building near main entrance.</p>
        </div>
        ''' if lang == 'en' else '''
        <div style="background: #fee2e2; padding: 15px; border-radius: 10px; margin-bottom: 15px; border-right: 4px solid #dc3545;">
            <p><strong><i class="fas fa-phone-alt"></i> أرقام الطوارئ:</strong></p>
            <p>• <i class="fas fa-shield-alt"></i> أمن الحرم الجامعي: 1234 (داخلي) / +968 1234 5678</p>
            <p>• <i class="fas fa-ambulance"></i> إسعاف/شرطة/دفاع مدني: 999</p>
            <p>• <i class="fas fa-hospital-user"></i> عيادة UTAS: 1235 (داخلي)</p>
            <p>• <i class="fas fa-clock"></i> طوارئ بعد الدوام: +968 9876 5432</p>
        </div>
        <div style="background: #d3cdf8; padding: 15px; border-radius: 10px;">
            <p><i class="fas fa-kit-medical"></i> حقائب الإسعافات الأولية في كل مبنى عند المدخل الرئيسي.</p>
        </div>
        '''
        return {'response': self._build_html_response(content, 'Emergency Information' if lang == 'en' else 'معلومات الطوارئ', lang), 'language': lang, 'intent': 'emergency', 'from_faq': True}
    
    # ==================== 17. CONVERSATIONAL HANDLER ====================
    
    def _handle_conversational(self, message, student_id, lang):
        message_lower = message.lower().strip()
        
        if any(w in message_lower for w in ['hi', 'hello', 'hey', 'مرحبا', 'السلام عليكم', 'اهلا']):
            return {
                'response': random.choice(self.conversation_responses[lang]['greeting']),
                'language': lang,
                'intent': 'conversation',
                'confidence': 1.0,
                'from_faq': False
            }
        
        if any(w in message_lower for w in ['how are you', 'كيف حالك', 'شخبارك']):
            return {
                'response': random.choice(self.conversation_responses[lang]['how_are_you']),
                'language': lang,
                'intent': 'conversation',
                'confidence': 1.0,
                'from_faq': False
            }
        
        if any(w in message_lower for w in ['thanks', 'thank you', 'شكرا', 'مشكور']):
            return {
                'response': random.choice(self.conversation_responses[lang]['thanks']),
                'language': lang,
                'intent': 'conversation',
                'confidence': 1.0,
                'from_faq': False
            }
        
        if any(w in message_lower for w in ['bye', 'goodbye', 'مع السلامة', 'باي']):
            return {
                'response': random.choice(self.conversation_responses[lang]['goodbye']),
                'language': lang,
                'intent': 'conversation',
                'confidence': 1.0,
                'from_faq': False
            }
        
        return None
    
    # ==================== UTAS LINKS HANDLER ====================
    
    def _handle_utas_links(self, message, student_id, lang):
        result = self.link_service.get_response(message, lang)
        content = result['response']
        method = result.get('method', 'unknown')
        method_text = "AI" if method == 'ai' else "UTAS Database"
        
        if result['type'] == 'link':
            title = f"UTAS Link ({method_text})"
        elif result['type'] == 'multiple':
            title = f"UTAS Links ({method_text})"
        elif result['type'] == 'rejected':
            title = "Information"
        else:
            title = f"UTAS Information ({method_text})"
        
        return {
            'response': self._build_html_response(content, title, lang),
            'language': lang,
            'intent': 'utas_links',
            'method': method,
            'from_faq': True
        }
    
    # ==================== EVENTS HANDLER ====================
    
    def _handle_events(self, student_id, lang):
        result = self.ai_intent.get_live_events_response(lang)
        return {
            'response': self._build_html_response(result, 'Events & Announcements' if lang == 'en' else 'الفعاليات والإعلانات', lang),
            'language': lang,
            'intent': 'events',
            'from_faq': True
        }
    
    # ==================== QUICK RESPONSE ====================
    
    def _quick_response(self, message, student_id, lang):
        message_lower = message.lower().strip()
         # This allows admin-added FAQs to override hardcoded ones
        conn = self.db.get_connection()
        cur = conn.cursor()
        
        # Search by keywords first (most accurate)
        cur.execute("""
            SELECT question_ar, question_en, answer_ar, answer_en, category, keywords
            FROM fqa 
            WHERE is_active = true 
            AND (
                %s = ANY(keywords)
                OR LOWER(question_en) LIKE %s 
                OR LOWER(question_ar) LIKE %s
                OR %s ILIKE ANY(STRING_TO_ARRAY(category, ','))
            )
            ORDER BY 
                CASE WHEN %s = ANY(keywords) THEN 1
                     WHEN LOWER(question_en) = %s THEN 2
                     WHEN LOWER(question_ar) = %s THEN 2
                     ELSE 3
                END
            LIMIT 1
        """, (
            message_lower,           # keyword match
            f'%{message_lower}%',    # question_en like
            f'%{message_lower}%',    # question_ar like
            message_lower,           # category match
            message_lower,           # for order by
            message_lower,           # for order by
            message_lower            # for order by
        ))
        
        faq_match = cur.fetchone()
        
        if faq_match:
            answer = faq_match[3] if lang == 'en' else faq_match[2]  # answer_en or answer_ar
            if answer and answer.strip():
                cur.close()
                conn.close()
                print(f"✅ Found FAQ: {faq_match[4]} (matched by keywords)")
                return {
                    'response': answer,
                    'language': lang,
                    'intent': faq_match[4],
                    'from_faq': True
                }
        
        cur.close()
        conn.close()
        # PDF Requests
        pdf_keywords = {
            "timetable": ["download my timetable", "download timetable", "timetable pdf", "تحميل جدولي", "جدولي pdf"],
            "attendance": ["download attendance report", "attendance pdf", "تحميل تقرير الحضور"],
            "transcript": ["download transcript", "transcript pdf", "تحميل كشف الدرجات"],
            "gpa": ["download gpa report", "gpa pdf", "تحميل تقرير المعدل"]
        }
        
        for pdf_type, keywords in pdf_keywords.items():
            if any(kw in message_lower for kw in keywords):
                return self._handle_pdf_request(message, student_id, lang, pdf_type)
        
        # Academic
        if any(w in message_lower for w in ['gpa', 'معدل', 'معدلي', 'what is my gpa', 'my grades']):
            return self._handle_gpa_query(student_id, lang)
        
        if any(w in message_lower for w in ['schedule', 'timetable', 'جدول', 'مواعيد', 'my schedule', 'show my schedule']):
            return self._handle_schedule_query(student_id, lang)
        
        if any(w in message_lower for w in ['attendance', 'حضور', 'غياب', 'attendance report']):
            return self._handle_attendance_query(student_id, lang)
        
        if any(w in message_lower for w in ['my mark', 'my marks', 'my grade', 'check my mark', 'درجاتي', 'علاماتي']):
            return self._handle_cims_grades_link(student_id, lang)
        
        if any(w in message_lower for w in ['register', 'تسجيل', 'course registration', 'كيف اسجل']):
            return self._handle_registration(student_id, lang)
        
        if any(w in message_lower for w in ['cims', 'سيمس', 'portal', 'بوابة']):
            return self._handle_cims_access(student_id, lang)
        
        if any(w in message_lower for w in ['advisor', 'مرشد', 'my advisor', 'مرشدي']):
            return self._handle_advisor_contact(student_id, lang)
        
        if any(w in message_lower for w in ['exam', 'امتحان', 'اختبار', 'exam schedule']):
            return self._handle_exam_schedule(student_id, lang)
        
        if any(w in message_lower for w in ['transcript', 'كشف الدرجات', 'السجل الأكاديمي']):
            return self._handle_transcript_query(student_id, lang)
        
        if any(w in message_lower for w in ['cv', 'resume', 'سيرة ذاتية', 'how to write cv']):
            return self._handle_cv_writing(student_id, lang)
        
        if any(w in message_lower for w in ['forgot password', 'نسيت كلمة المرور', 'reset password']):
            return self._handle_password_reset(student_id, lang)
        
        if any(w in message_lower for w in ['add drop', 'الحذف والاضافة', 'add/drop deadline']):
            return self._handle_add_drop_deadline(student_id, lang)
        
        if any(w in message_lower for w in ['scholarship', 'منحة', 'financial aid']):
            return self._handle_scholarships(student_id, lang)
        
        if any(w in message_lower for w in ['internship', 'تدريب', 'job', 'وظيفة']):
            return self._handle_internships_jobs(student_id, lang)
        
        if any(w in message_lower for w in ['emergency', 'طوارئ', 'اسعاف', 'شرطة']):
            return self._handle_emergency(student_id, lang)
        
        # Links and Events
        if any(w in message_lower for w in ['link', 'links', 'رابط', 'روابط', 'url']):
            return self._handle_utas_links(message, student_id, lang)
        
        if any(w in message_lower for w in ['event', 'events', 'فعالية', 'فعاليات', 'what event today']):
            return self._handle_events(student_id, lang)
        
        # Conversation
        if any(w in message_lower for w in ['hi', 'hello', 'hey', 'مرحبا', 'السلام عليكم', 'اهلا', 'how are you']):
            return self._handle_conversational(message, student_id, lang)
        
        return None
    
    # ==================== FALLBACK & SESSION ====================
    
    def _get_fallback_response(self, lang):
        if lang == 'en':
            return "I'm here to help! Ask me about GPA, schedule, CIMS, advisor, registration, or UTAS links."
        return "أنا هنا للمساعدة! اسألني عن معدلك، جدولك، CIMS، مرشدك، التسجيل، أو روابط UTAS."
    
    def start_session(self, student_id):
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {'student_id': student_id, 'start_time': datetime.now().isoformat(), 'active': True}
        return {'session_id': session_id, 'student_id': student_id}
    
    def end_session(self, session_id):
        if session_id in self.sessions:
            self.sessions[session_id]['active'] = False
            return {'success': True}
        return {'success': False}
    
    def handle_message(self, message, student_id, session_id):
        try:
            print(f"\nProcessing: '{message}' for student {student_id}")
            
            student = self.db.get_student(student_id)
            lang = student.get('preferred_language', 'en') if student else 'en'
            
            response = self._quick_response(message, student_id, lang)
            if response:
                return response
            
            intent_result = self.ai_intent.detect_intent(message, lang)
            response_text = self.ai_intent.generate_response(intent_result, student_id, self)
            
            return {
                'response': response_text,
                'language': lang,
                'intent': intent_result['intent'],
                'confidence': intent_result['confidence'],
                'from_faq': False
            }
            
        except Exception as e:
            logger.error(f"Message error: {e}")
            return self._get_fallback_response('en')