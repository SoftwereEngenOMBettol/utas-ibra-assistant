Manual Setup
# Backend
cd backend
pip install -r requirements.txt
python main.py

# Frontend (new terminal)
cd frontend
npm install
npm start
🔑 Default Logins
Student: STU001 / student123

Admin: ADMIN001 / admin123

📚 Features
🤖 Bilingual AI Assistant (Arabic/English)
📊 Real-time GPA, Schedule, Attendance
📄 PDF Reports (4 types)
👨‍💼 Admin Dashboard with Analytics
❓ FAQ Management System
⭐ 5-Star Feedback System

🛠️ Tech Stack
Frontend: React.js + Bootstrap
Backend: FastAPI (Python)
Database: PostgreSQL
AI: Google Gemini 2.5 Flash

📧 Contact
For any inquiries, please contact the project team.
Email: zumurudalshabib@gmail.com

**`.gitignore`** (What files NOT to upload)

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/
.pytest_cache/
.coverage
*.log

# Backend
backend/.env
backend/.env.local
*.db
*.sqlite
backend/venv/

# Frontend
frontend/node_modules/
frontend/build/
frontend/.env
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Environment variables
.env
.env.local
.env.production

# Database
*.sqlite
*.db
*.sqlite3

# Logs
logs/
*.log
