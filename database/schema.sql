-- First, drop existing foreign key constraints if they exist
-- First, drop existing foreign key constraints if they exist
ALTER TABLE IF EXISTS unanswered_questions 
DROP CONSTRAINT IF EXISTS unanswered_questions_answered_by_fkey;

ALTER TABLE IF EXISTS unanswered_questions 
DROP CONSTRAINT IF EXISTS unanswered_questions_student_id_fkey;

ALTER TABLE IF EXISTS user_sessions 
DROP CONSTRAINT IF EXISTS user_sessions_student_id_fkey;

ALTER TABLE IF EXISTS fqa 
DROP CONSTRAINT IF EXISTS fqa_created_by_fkey;

ALTER TABLE unanswered_questions 
ADD COLUMN status VARCHAR(30);

-- FQA table (Frequently Asked Questions) - NO foreign key initially
CREATE TABLE IF NOT EXISTS fqa (
    id SERIAL PRIMARY KEY,
    question_ar TEXT NOT NULL,
    question_en TEXT NOT NULL,
    answer_ar TEXT NOT NULL,
    answer_en TEXT NOT NULL,
    category VARCHAR(50),
    attachment_type VARCHAR(20),
    attachment_content TEXT,
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User sessions - NO foreign key initially
CREATE TABLE IF NOT EXISTS user_sessions (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(20),
    session_token VARCHAR(255) UNIQUE NOT NULL,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_time TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- App usage statistics
CREATE TABLE IF NOT EXISTS app_usage (
    id SERIAL PRIMARY KEY,
    date DATE DEFAULT CURRENT_DATE,
    total_sessions INTEGER DEFAULT 0,
    total_queries INTEGER DEFAULT 0,
    unique_students INTEGER DEFAULT 0
);










-- Create categories table
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name_ar VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    description_ar TEXT,
    description_en TEXT,
    icon VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Update fqa table with category_id
ALTER TABLE fqa ADD COLUMN IF NOT EXISTS category_id INTEGER REFERENCES categories(id);
ALTER TABLE fqa ADD COLUMN IF NOT EXISTS source_type VARCHAR(20); -- 'manual', 'pdf', 'html', 'url'
ALTER TABLE fqa ADD COLUMN IF NOT EXISTS source_url TEXT;
ALTER TABLE fqa ADD COLUMN IF NOT EXISTS keywords TEXT[]; -- Array of keywords for better matching

-- Create index for keyword search
CREATE INDEX IF NOT EXISTS idx_fqa_keywords ON fqa USING GIN(keywords);

-- Insert default categories
INSERT INTO categories (name_ar, name_en, description_ar, description_en, icon) VALUES
('عام', 'General', 'أسئلة عامة عن الجامعة', 'General university questions', 'fa-university'),
('التسجيل', 'Registration', 'أسئلة عن التسجيل في المواد', 'Course registration questions', 'fa-calendar-plus'),
('المعدل', 'GPA', 'أسئلة عن المعدل والدرجات', 'GPA and grades questions', 'fa-chart-line'),
('الجدول', 'Schedule', 'أسئلة عن الجدول الدراسي', 'Schedule related questions', 'fa-calendar-alt'),
('الحضور', 'Attendance', 'أسئلة عن الحضور والغياب', 'Attendance related questions', 'fa-user-check'),
('المرشد الأكاديمي', 'Academic Advisor', 'أسئلة عن المرشد الأكاديمي', 'Academic advisor questions', 'fa-chalkboard-user'),
('الامتحانات', 'Exams', 'أسئلة عن الامتحانات', 'Exam related questions', 'fa-pen-to-square'),
('الخدمات الإلكترونية', 'E-Services', 'أسئلة عن الخدمات الإلكترونية', 'E-Services questions', 'fa-laptop')
ON CONFLICT DO NOTHING;

-- Verify everything was created
SELECT '✅ Database schema created successfully!' AS status_message;
SELECT COUNT(*) AS total_students FROM students;
SELECT COUNT(*) AS total_fqa FROM fqa;
SELECT COUNT(*) AS total_schedules FROM student_schedule;
SELECT COUNT(*) AS total_gpa_records FROM student_gpa;
SELECT COUNT(*) AS total_attendance_records FROM student_attendance;
SELECT COUNT(*) AS total_unanswered FROM unanswered_questions;