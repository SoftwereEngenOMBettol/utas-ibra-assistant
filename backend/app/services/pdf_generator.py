# backend/app/pdf_generator.py

"""PDF Generator for student reports"""

import io
import logging
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Generate PDF files for student schedules and attendance"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1800ad'),
            alignment=TA_CENTER,
            spaceAfter=30
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#ffffff'),
            alignment=TA_CENTER,
            backColor=colors.HexColor("#c1ccff")
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            alignment=TA_LEFT
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomFooter',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#999999'),
            alignment=TA_CENTER
        ))
    
    def generate_timetable_pdf(self, student_data, schedule_data):
        """Generate timetable PDF for a student"""
        try:
            buffer = io.BytesIO()
            
            doc = SimpleDocTemplate(
                buffer,
                pagesize=landscape(letter),
                rightMargin=30,
                leftMargin=30,
                topMargin=50,
                bottomMargin=50
            )
            
            story = []
            
            # Header
            story.append(Paragraph(
                "University of Technology and Applied Sciences - Ibra Branch",
                self.styles['CustomTitle']
            ))
            
            # Student Information
            story.append(Paragraph(
                f"<b>Student Name:</b> {student_data.get('name', 'N/A')}",
                self.styles['Normal']
            ))
            story.append(Paragraph(
                f"<b>Student ID:</b> {student_data.get('student_id', 'N/A')}",
                self.styles['Normal']
            ))
            story.append(Paragraph(
                f"<b>Department:</b> {student_data.get('department', 'N/A')}",
                self.styles['Normal']
            ))
            story.append(Paragraph(
                f"<b>Generated on:</b> {datetime.now().strftime('%A, %d %B %Y %H:%M')}",
                self.styles['CustomInfo']
            ))
            story.append(Spacer(1, 20))
            
            # Academic Information
            story.append(Paragraph(
                f"<b>Semester:</b> {student_data.get('current_semester', 'Current Semester')}",
                self.styles['Normal']
            ))
            story.append(Paragraph(
                f"<b>Academic Year:</b> {student_data.get('academic_year', '2025-2026')}",
                self.styles['Normal']
            ))
            story.append(Spacer(1, 20))
            
            # Create timetable table
            if schedule_data and len(schedule_data) > 0:
                # Prepare table data
                table_data = [['Day', 'Time', 'Course Code', 'Course Name', 'Lecturer', 'Room']]
                
                # Group by day for better organization
                days_order = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday']
                for day in days_order:
                    day_schedule = [s for s in schedule_data if s.get('day_of_week') == day]
                    if day_schedule:
                        for i, course in enumerate(day_schedule):
                            time_start = str(course.get('time_start', ''))[:5] if course.get('time_start') else ''
                            time_end = str(course.get('time_end', ''))[:5] if course.get('time_end') else ''
                            time_range = f"{time_start} - {time_end}" if time_start and time_end else 'TBA'
                            
                            if i == 0:
                                table_data.append([
                                    day,
                                    time_range,
                                    course.get('course_code', ''),
                                    course.get('course_name', ''),
                                    course.get('lecturer', 'TBA'),
                                    course.get('room', 'TBA')
                                ])
                            else:
                                table_data.append([
                                    '',
                                    time_range,
                                    course.get('course_code', ''),
                                    course.get('course_name', ''),
                                    course.get('lecturer', 'TBA'),
                                    course.get('room', 'TBA')
                                ])
                
                # Create table
                table = Table(table_data, repeatRows=1)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#ced7ff")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                # Alternate row colors
                for i in range(1, len(table_data)):
                    if i % 2 == 0:
                        table.setStyle(TableStyle([
                            ('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8f9fa'))
                        ]))
                
                story.append(table)
                story.append(Spacer(1, 20))
                
                # Add summary information
                total_courses = len(schedule_data)
                story.append(Paragraph(
                    f"<b>Summary:</b> {total_courses} courses",
                    self.styles['CustomInfo']
                ))
            else:
                story.append(Paragraph(
                    "No schedule data available for the current semester.",
                    self.styles['Normal']
                ))
            
            story.append(Spacer(1, 30))
            
            # Add footer
            story.append(Paragraph(
                "This is an official timetable generated from UTAS Ibra Academic System.",
                self.styles['CustomFooter']
            ))
            story.append(Paragraph(
                "Please report any discrepancies to the Registration Office.",
                self.styles['CustomFooter']
            ))
            
            # Build PDF
            doc.build(story)
            
            # Get PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error generating timetable PDF: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_attendance_pdf(self, student_data, attendance_data):
        """Generate attendance PDF for a student"""
        try:
            buffer = io.BytesIO()
            
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=30,
                leftMargin=30,
                topMargin=50,
                bottomMargin=50
            )
            
            story = []
            
            # Header
            story.append(Paragraph(
                "University of Technology and Applied Sciences - Ibra Branch",
                self.styles['CustomTitle']
            ))
            
            story.append(Paragraph(
                f"<b>Student Name:</b> {student_data.get('name', 'N/A')}",
                self.styles['Normal']
            ))
            story.append(Paragraph(
                f"<b>Student ID:</b> {student_data.get('student_id', 'N/A')}",
                self.styles['Normal']
            ))
            story.append(Paragraph(
                f"<b>Department:</b> {student_data.get('department', 'N/A')}",
                self.styles['Normal']
            ))
            story.append(Paragraph(
                f"<b>Generated on:</b> {datetime.now().strftime('%A, %d %B %Y %H:%M')}",
                self.styles['CustomInfo']
            ))
            story.append(Spacer(1, 20))
            
            # Attendance Summary Header
            story.append(Paragraph(
                "<b>ATTENDANCE REPORT</b>",
                self.styles['CustomHeader']
            ))
            story.append(Spacer(1, 10))
            
            # Create attendance table
            if attendance_data and len(attendance_data) > 0:
                table_data = [['Course Code', 'Course Name', 'Total Classes', 'Absences', 'Percentage', 'Status']]
                
                for record in attendance_data:
                    percentage = record.get('percentage', 0)
                    status = "✅ Satisfactory" if percentage >= 75 else "⚠️ Warning"
                    
                    table_data.append([
                        record.get('course_code', ''),
                        record.get('course_name', ''),
                        str(record.get('total_classes', 0)),
                        str(record.get('absences', 0)),
                        f"{percentage:.1f}%",
                        status
                    ])
                
                table = Table(table_data, repeatRows=1)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#bfc9f7")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                ]))
                
                # Color code status column
                for i in range(1, len(table_data)):
                    status_cell = table_data[i][5]
                    if "Warning" in status_cell:
                        table.setStyle(TableStyle([
                            ('TEXTCOLOR', (5, i), (5, i), colors.HexColor('#dc3545'))
                        ]))
                    else:
                        table.setStyle(TableStyle([
                            ('TEXTCOLOR', (5, i), (5, i), colors.HexColor('#28a745'))
                        ]))
                
                story.append(table)
                story.append(Spacer(1, 20))
                
                # Calculate overall attendance
                avg_percentage = sum([r.get('percentage', 0) for r in attendance_data]) / len(attendance_data)
                story.append(Paragraph(
                    f"<b>Overall Attendance Average:</b> {avg_percentage:.1f}%",
                    self.styles['Normal']
                ))
                
                if avg_percentage >= 75:
                    story.append(Paragraph(
                        "✅ Your attendance is satisfactory. Keep up the good work!",
                        self.styles['Normal']
                    ))
                else:
                    story.append(Paragraph(
                        "⚠️ Your attendance is below the required 75%. Please attend classes regularly.",
                        self.styles['Normal']
                    ))
                
                story.append(Spacer(1, 20))
                
                # Attendance rules
                story.append(Paragraph(
                    "<b>Attendance Policy:</b>",
                    self.styles['Normal']
                ))
                story.append(Paragraph(
                    "• Minimum attendance required: 75% per course",
                    self.styles['CustomInfo']
                ))
                story.append(Paragraph(
                    "• Students with less than 75% attendance may be barred from final exams",
                    self.styles['CustomInfo']
                ))
                story.append(Paragraph(
                    "• Medical certificates must be submitted within 3 days of absence",
                    self.styles['CustomInfo']
                ))
            else:
                story.append(Paragraph(
                    "No attendance records found for the current semester.",
                    self.styles['Normal']
                ))
            
            story.append(Spacer(1, 30))
            
            # Footer
            story.append(Paragraph(
                "This is an official attendance report from UTAS Ibra Academic System.",
                self.styles['CustomFooter']
            ))
            
            doc.build(story)
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error generating attendance PDF: {e}")
            import traceback
            traceback.print_exc()
            return None
    # Add these methods to your PDFGenerator class

    def generate_transcript_pdf(self, student_data, transcript_data, gpa_records):
       """Generate complete academic transcript PDF"""
       try:
           buffer = io.BytesIO()
           
           doc = SimpleDocTemplate(
               buffer,
               pagesize=letter,
               rightMargin=30,
               leftMargin=30,
               topMargin=50,
               bottomMargin=50
           )
           
           story = []
           
           # Header
           story.append(Paragraph(
               "University of Technology and Applied Sciences - Ibra Branch",
               self.styles['CustomTitle']
           ))
           story.append(Paragraph(
               "ACADEMIC TRANSCRIPT",
               self.styles['CustomHeader']
           ))
           story.append(Spacer(1, 20))
           
           # Student Information
           story.append(Paragraph(
               f"<b>Student Name:</b> {student_data.get('name', 'N/A')}",
               self.styles['Normal']
           ))
           story.append(Paragraph(
               f"<b>Student ID:</b> {student_data.get('student_id', 'N/A')}",
               self.styles['Normal']
           ))
           story.append(Paragraph(
               f"<b>Department:</b> {student_data.get('department', 'N/A')}",
               self.styles['Normal']
           ))
           story.append(Paragraph(
               f"<b>Generated on:</b> {datetime.now().strftime('%A, %d %B %Y %H:%M')}",
               self.styles['CustomInfo']
           ))
           story.append(Spacer(1, 20))
           
           # Group by semester
           semesters = {}
           for record in transcript_data:
               sem = record.get('semester', 'Unknown')
               if sem not in semesters:
                   semesters[sem] = []
               semesters[sem].append(record)
           
           total_points = 0
           total_credits = 0
           
           for semester, courses in semesters.items():
               story.append(Paragraph(
                   f"<b>{semester}</b>",
                   ParagraphStyle(name='SemesterHeader', parent=self.styles['Heading2'], fontSize=14, textColor=colors.HexColor('#1800ad'))
               ))
               story.append(Spacer(1, 10))
               
               # Create table for courses
               table_data = [['Course Code', 'Course Name', 'Credits', 'Grade', 'Points', 'Result']]
               
               sem_credits = 0
               sem_points = 0
               
               for course in courses:
                   credits = course.get('credit_hours', 0)
                   points = course.get('points', 0)
                   grade = course.get('grade', '')
                   result = course.get('result', '')
                   
                   sem_credits += credits
                   sem_points += points * credits
                   
                   table_data.append([
                       course.get('course_code', ''),
                       course.get('course_name', ''),
                       str(credits),
                       grade,
                       f"{points:.2f}" if points else '-',
                       result
                   ])
               
               table = Table(table_data, repeatRows=1)
               table.setStyle(TableStyle([
                   ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                   ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                   ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                   ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                   ('FONTSIZE', (0, 0), (-1, 0), 10),
                   ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                   ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                   ('FONTSIZE', (0, 1), (-1, -1), 9),
               ]))
               
               story.append(table)
               
               sem_gpa = sem_points / sem_credits if sem_credits > 0 else 0
               total_points += sem_points
               total_credits += sem_credits
               
               story.append(Paragraph(
                   f"<b>Semester GPA:</b> {sem_gpa:.2f} | <b>Credits:</b> {sem_credits}",
                   self.styles['CustomInfo']
               ))
               story.append(Spacer(1, 15))
           
           # Cumulative GPA
           cumulative_gpa = total_points / total_credits if total_credits > 0 else 0
           
           story.append(Spacer(1, 20))
           story.append(Paragraph(
               f"<b>📊 CUMULATIVE GPA:</b> {cumulative_gpa:.2f}",
               self.styles['CustomHeader']
           ))
           story.append(Paragraph(
               f"<b>📚 TOTAL CREDITS COMPLETED:</b> {total_credits}",
               self.styles['Normal']
           ))
           story.append(Spacer(1, 30))
           
           # Footer
           story.append(Paragraph(
               "This is an official academic transcript from UTAS Ibra Academic System.",
               self.styles['CustomFooter']
           ))
           story.append(Paragraph(
               "For verification purposes, please contact the Registration Office.",
               self.styles['CustomFooter']
           ))
           
           doc.build(story)
           pdf_content = buffer.getvalue()
           buffer.close()
           
           return pdf_content
           
       except Exception as e:
           logger.error(f"Error generating transcript PDF: {e}")
           return None
   
   
    def generate_gpa_report_pdf(self, student_data, gpa_data, transcript_data):
        """Generate GPA report PDF"""
        try:
            buffer = io.BytesIO()
            
            doc = SimpleDocTemplate(
                buffer,
                pagesize=letter,
                rightMargin=30,
                leftMargin=30,
                topMargin=50,
                bottomMargin=50
            )
            
            story = []
            
            # Header
            story.append(Paragraph(
                "University of Technology and Applied Sciences - Ibra Branch",
                self.styles['CustomTitle']
            ))
            story.append(Paragraph(
                "GPA REPORT",
                self.styles['CustomHeader']
            ))
            story.append(Spacer(1, 20))
            
            # Student Information
            story.append(Paragraph(
                f"<b>Student Name:</b> {student_data.get('name', 'N/A')}",
                self.styles['Normal']
            ))
            story.append(Paragraph(
                f"<b>Student ID:</b> {student_data.get('student_id', 'N/A')}",
                self.styles['Normal']
            ))
            story.append(Paragraph(
                f"<b>Department:</b> {student_data.get('department', 'N/A')}",
                self.styles['Normal']
            ))
            story.append(Spacer(1, 20))
            
            # GPA Summary Cards
            story.append(Paragraph(
                "<b>GPA SUMMARY</b>",
                self.styles['CustomHeader']
            ))
            story.append(Spacer(1, 10))
            
            # GPA values
            semester_gpa = None
            cumulative_gpa = None
            overall_gpa = None
            
            for record in gpa_data:
                if record.get('gpa_type') == 'semester':
                    semester_gpa = record.get('gpa_value', 0)
                elif record.get('gpa_type') == 'cumulative':
                    cumulative_gpa = record.get('gpa_value', 0)
                elif record.get('gpa_type') == 'overall':
                    overall_gpa = record.get('gpa_value', 0)
            
            # Create GPA info table
            gpa_table_data = [
                ['GPA Type', 'Value', 'Status'],
                ['Semester GPA', f"{semester_gpa:.2f}" if semester_gpa else 'N/A', 'Current Semester'],
                ['Cumulative GPA', f"{cumulative_gpa:.2f}" if cumulative_gpa else 'N/A', 'All Courses'],
                ['Overall GPA', f"{overall_gpa:.2f}" if overall_gpa else 'N/A', 'Total Average']
            ]
            
            gpa_table = Table(gpa_table_data, repeatRows=1)
            gpa_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            
            story.append(gpa_table)
            story.append(Spacer(1, 20))
            
            # Calculate grade distribution
            grade_distribution = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
            for course in transcript_data:
                grade = course.get('grade', '')
                if grade:
                    if grade.startswith('A'):
                        grade_distribution['A'] += 1
                    elif grade.startswith('B'):
                        grade_distribution['B'] += 1
                    elif grade.startswith('C'):
                        grade_distribution['C'] += 1
                    elif grade.startswith('D'):
                        grade_distribution['D'] += 1
                    elif grade == 'F':
                        grade_distribution['F'] += 1
            
            # Grade distribution table
            story.append(Paragraph(
                "<b>GRADE DISTRIBUTION</b>",
                self.styles['CustomHeader']
            ))
            story.append(Spacer(1, 10))
            
            grade_table_data = [['Grade', 'Count', 'Percentage']]
            total_courses = sum(grade_distribution.values())
            
            for grade, count in grade_distribution.items():
                percentage = (count / total_courses * 100) if total_courses > 0 else 0
                grade_table_data.append([grade, str(count), f"{percentage:.1f}%"])
            
            grade_table = Table(grade_table_data, repeatRows=1)
            grade_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            
            story.append(grade_table)
            story.append(Spacer(1, 30))
            
            # Footer
            story.append(Paragraph(
                "This is an official GPA report from UTAS Ibra Academic System.",
                self.styles['CustomFooter']
            ))
            
            doc.build(story)
            pdf_content = buffer.getvalue()
            buffer.close()
            
            return pdf_content
            
        except Exception as e:
            logger.error(f"Error generating GPA report PDF: {e}")
            return None