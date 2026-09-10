# UTAS Ibra Assistant — المساعد الذكي لجامعة التقنية والعلوم التطبيقية بإبراء

A bilingual (Arabic / English) AI chatbot that answers student questions about their own academic record — GPA, class schedule, attendance, advisor, exams, registration deadlines — and generates official-looking PDF reports on request.

Built with **FastAPI**, **React**, **PostgreSQL**, and **Google Gemini 2.5 Flash**.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688)
![React](https://img.shields.io/badge/React-18.2-61DAFB)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791)
![License](https://img.shields.io/badge/License-MIT-green)

---

## What problem does it solve?

Students at UTAS Ibra ask the same questions every semester — *what is my GPA, when is my next class, how many absences do I have, who is my advisor, when does add/drop close*. Answering them means either queuing at the registration office or navigating several separate university portals.

This assistant puts all of it behind one chat box in the student's own language. It does two different things depending on the question:

1. **Personal data questions** are answered from the university database directly, so the number is always real — not something the AI guessed.
2. **General questions** are answered from an admin-managed FAQ knowledge base, and only fall back to the Gemini model when nothing matches.

Anything the assistant cannot answer is logged as a **pending question**, which an administrator can then answer once — turning it into a permanent FAQ entry that every future student gets instantly.

---

## Demo

A recorded walkthrough is included in the repository: [`UTAS Assistant Demo_compressed.mp4`](./UTAS%20Assistant%20Demo_compressed.mp4)

> Consider uploading this to YouTube and linking it here instead — a 14 MB video makes the repo slow to clone, and GitHub won't play it inline.

## Screenshots

> Add images to a `docs/` folder and link them here.

| Student chat | Admin dashboard | FAQ manager |
| --- | --- | --- |
| ![Chat](docs/screenshot-chat.png) | ![Dashboard](docs/screenshot-dashboard.png) | ![FAQ](docs/screenshot-faq.png) |

---

## Features

### For students
- **Bilingual chat** — the assistant detects Arabic or English and replies in the same language
- **Live academic data** — GPA (semester and cumulative), weekly timetable, attendance percentage per course
- **PDF reports**, generated on demand with ReportLab:
  - Timetable
  - Attendance report
  - Academic transcript
  - GPA report
- **Guidance answers** — CIMS portal access, password reset, academic advisor contact, exam schedule, add/drop deadlines, scholarships, internships, emergency contacts, CV writing help
- **5-star feedback** on any answer
- Session tracking, so each conversation is logged as a session

### For administrators
- Separate admin login with a protected route guard on the frontend
- **Usage analytics dashboard** with charts (Chart.js) — sessions, queries, unique students
- **FAQ knowledge base management** — create, edit, delete bilingual FAQ entries with categories
- **AI-assisted FAQ generation** — feed the system a URL, a pasted block of content, or a PDF, and Gemini extracts question/answer pairs in both languages for the admin to review
- **Pending questions queue** — every unanswered student question is captured; answering one promotes it into the knowledge base
- **Category management** and reusable response templates
- Student directory browsing

---

## Architecture

```
┌──────────────────────────────┐
│  React frontend (port 3000)  │
│  ChatPage · AdminDashboard   │
└──────────────┬───────────────┘
               │  JSON over HTTP, JWT in Authorization header
               ▼
┌──────────────────────────────┐
│  FastAPI backend (port 8000) │
│  /api/login  /api/chat       │
│  /api/admin/*                │
└───┬──────────────┬───────────┘
    │              │
    ▼              ▼
┌─────────┐   ┌──────────────────┐
│PostgreSQL│   │ Google Gemini    │
│ students │   │ 2.5 Flash        │
│ fqa      │   │ intent detection │
│ chat_logs│   │ FAQ generation   │
└─────────┘   └──────────────────┘
```

### How one chat message is handled

```
Student sends a message
        │
        ▼
1. Gemini classifies the intent (gpa / schedule / attendance / general / ...)
        │
        ▼
2. Search the FQA table for a matching question  ──── match ──▶ return stored answer
        │ no match
        ▼
3. Is it a personal-data intent?  ──── yes ──▶ UTASVirtualAssistant queries PostgreSQL
        │ no                                    and formats the real numbers
        ▼                                              │
4. Ask Gemini to answer generally                      │
        │                                              │
        ▼                                              ▼
5. Log to chat_logs; if unanswered, insert into unanswered_questions
        │
        ▼
   Response returned to the browser (HTML-formatted, correct language)
```

The key design choice: **the AI is used to understand the question, not to invent the answer.** GPA and attendance figures always come from SQL.

---

## Tech stack

| Layer | Technology |
| --- | --- |
| Frontend | React 18, React Router 6, Bootstrap 5, Chart.js, react-markdown, Axios |
| Backend | FastAPI, Uvicorn, Pydantic |
| Database | PostgreSQL 15 (via `psycopg2`) |
| AI | Google Gemini 2.5 Flash (`google-generativeai`) |
| Auth | JWT (`python-jose` / `pyjwt`) + bcrypt password hashing |
| PDF | ReportLab |
| Content ingestion | BeautifulSoup4 (URL scraping), PyPDF2 (PDF text extraction) |
| Deployment | Docker Compose |

---

## Project structure

```
utas-ibra-assistant/
├── backend/
│   ├── main.py                      # FastAPI entry point, CORS, router registration
│   ├── requirements.txt
│   └── app/
│       ├── database.py              # PostgreSQL connection factory
│       ├── models/                  # Pydantic request/response schemas
│       │   ├── auth_models.py
│       │   └── fqa_models.py
│       ├── routes/
│       │   ├── auth.py              # Login, token verification, logout
│       │   ├── chat.py              # Chat, feedback, session start/end
│       │   └── admin.py             # FAQ CRUD, analytics, AI generation
│       └── services/
│           ├── chatbot_service.py   # UTASVirtualAssistant — intent handlers
│           ├── connector.py         # DatabaseConnector — all SQL queries
│           ├── gemini_service.py    # Gemini prompts and calls
│           └── pdf_generator.py     # Four ReportLab PDF builders
├── frontend/
│   ├── package.json
│   └── src/
│       ├── pages/                   # ChatPage, LoginPage, AdminDashboard, ...
│       ├── components/              # Navigation, FQAManager, TemplateManager
│       └── services/                # API helpers, notifications
├── database/
│   └── schema.sql                   # Table definitions (see note below)
├── docker-compose.yaml
└── LICENSE
```

---

## Getting started

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15 (or Docker)
- A Google Gemini API key — free from [Google AI Studio](https://aistudio.google.com/app/apikey)

### 1. Clone

```bash
git clone https://github.com/SoftwereEngenOMBettol/utas-ibra-assistant.git
cd utas-ibra-assistant
```

### 2. Configure environment variables

Create `backend/.env`:

```env
DB_HOST=localhost
DB_NAME=utas_chatbot
DB_USER=postgres
DB_PASSWORD=postgres123
DB_PORT=5432

GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=models/gemini-2.5-flash

JWT_SECRET_KEY=generate_a_long_random_string_here
```

Generate a secure JWT key with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 3. Create the database

```bash
createdb utas_chatbot
psql -d utas_chatbot -f database/schema.sql
```

> ⚠️ **`database/schema.sql` is currently incomplete.** It creates `fqa`, `user_sessions`, `app_usage`, and `categories`, but the application also reads and writes `students`, `student_schedule`, `student_gpa`, `student_attendance`, `student_courses`, `courses`, `staff`, `chat_logs`, `chat_sessions`, `messages`, `feedback`, `unanswered_questions`, `announcements`, `events`, `academic_calendar`, `faq_knowledge_base`, and `response_templates`. Until those `CREATE TABLE` statements are added, a fresh clone will not run. See [Known issues](#known-issues).

### 4. Run the backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

The API starts on <http://localhost:8000>. Interactive docs are at <http://localhost:8000/docs>.

### 5. Run the frontend

In a second terminal:

```bash
cd frontend
npm install
npm start
```

The app opens at <http://localhost:3000>. `package.json` proxies API calls to port 8000, so no extra configuration is needed in development.

### Default logins (development only)

| Role | ID | Password |
| --- | --- | --- |
| Student | `STU001` | `student123` |
| Admin | `ADMIN001` | `admin123` |

**Change these before any real deployment.** Use `backend/change_password..py` or insert a fresh bcrypt hash into the `students` table.

---

## API reference

Full interactive documentation is auto-generated at `/docs` when the backend is running.

### Authentication — `/api`

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/login` | Log in; returns a JWT and a session token |
| `GET` | `/api/verify` | Validate the current JWT |
| `POST` | `/api/logout` | End the session |

### Chat — `/api`

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/chat` | Send a message, receive an answer |
| `POST` | `/api/chat/start` | Open a chat session |
| `POST` | `/api/chat/end` | Close a chat session |
| `POST` | `/api/feedback` | Submit a 1–5 star rating |

### Admin — `/api/admin` (JWT required, `is_admin` must be true)

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/admin/usage` | Usage analytics for the dashboard |
| `GET` | `/api/admin/students` | List students |
| `GET` | `/api/admin/fqa` | List FAQ entries |
| `POST` | `/api/admin/fqa/manual` | Create an FAQ entry by hand |
| `DELETE` | `/api/admin/fqa/{faq_id}` | Delete an FAQ entry |
| `GET` | `/api/admin/fqa/pending` | Unanswered student questions |
| `POST` | `/api/admin/fqa/answer-pending/{id}` | Answer one and promote it to the knowledge base |
| `POST` | `/api/admin/fqa/from-url` | Scrape a URL and generate FAQs with Gemini |
| `POST` | `/api/admin/fqa/upload-pdf` | Extract FAQs from an uploaded PDF |
| `POST` | `/api/admin/fqa/generate-from-content` | Generate FAQs from pasted text |
| `GET` `POST` `PUT` `DELETE` | `/api/admin/categories` | Category management |
| `GET` `POST` | `/api/admin/response-templates` | Reusable response templates |

### Example request

```bash
# 1. Log in
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"student_id":"STU001","password":"student123","language":"en"}'

# 2. Ask a question with the returned token
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
        "student_id": "STU001",
        "session_token": "<session_token>",
        "message": "What is my GPA?",
        "language": "en"
      }'
```

---

## Running with Docker

```bash
export GEMINI_API_KEY=your_key_here
docker compose up --build
```

> ⚠️ `docker-compose.yaml` currently references three files that are not in the repository: `backend/Dockerfile`, `frontend/Dockerfile`, and `database/seed_data.sql`. Add them, or use the manual setup above.

---

## Known issues

Honest list of what still needs work — worth keeping visible so contributors know where to help.

- [ ] `database/schema.sql` creates only 4 of the ~18 tables the code uses; the rest are missing
- [ ] `database/seed_data.sql` is referenced by Docker Compose but does not exist
- [ ] `backend/Dockerfile` and `frontend/Dockerfile` are missing, so `docker compose up` fails
- [ ] `frontend/src/services/api.js` is an empty file
- [ ] `backend/app/models.py` and `backend/app/models/` both exist — the package shadows the module, making `models.py` dead code. Delete one.
- [ ] `POST /api/admin/fqa/from-url` is defined twice in `admin.py` (lines 568 and 964); the second definition wins
- [ ] `__pycache__/*.pyc` files are committed despite being in `.gitignore` — run `git rm -r --cached backend/app/__pycache__`
- [ ] The root `package.json` contains only `react-hot-toast` and appears to be a stray file
- [ ] `backend/change_password..py` has a double dot in the filename
- [ ] FAQ matching uses `LIKE '%full message%'`, which only matches when the FAQ question contains the student's entire sentence. Keyword or vector search would improve hit rate substantially.
- [ ] No automated tests
- [ ] `admin.py` is 1,700 lines and would benefit from being split by concern

---

## Security notes

- Passwords are hashed with bcrypt — good.
- JWTs expire after 24 hours.
- `JWT_SECRET_KEY` has an insecure default in code; always set it in `.env`.
- The `.env` file is correctly gitignored. Never commit it.
- This system handles real student academic records. Before production use: enable HTTPS, restrict CORS to the real frontend domain (currently only `localhost` origins are allowed), add rate limiting on `/api/login`, and confirm the deployment meets the university's data-protection requirements.

---

## نبذة بالعربية

**المساعد الذكي لجامعة التقنية والعلوم التطبيقية — فرع إبراء**

روبوت محادثة ثنائي اللغة (عربي/إنجليزي) يجيب الطلبة عن أسئلتهم الأكاديمية: المعدل التراكمي والفصلي، الجدول الدراسي، نسبة الحضور والغياب، بيانات المرشد الأكاديمي، مواعيد الامتحانات، والتسجيل في المواد. كما يولّد تقارير PDF جاهزة للطباعة (الجدول، الحضور، كشف الدرجات، تقرير المعدل).

**كيف يعمل؟** يستخدم النظام نموذج Gemini لفهم سؤال الطالب فقط، أما الأرقام فتُجلب مباشرة من قاعدة البيانات لضمان دقتها. إذا لم يجد إجابة، يُحفظ السؤال في قائمة الأسئلة المعلّقة ليجيب عليه المشرف مرة واحدة، فيصبح متاحاً لجميع الطلبة تلقائياً.

**لوحة المشرف** توفّر إحصائيات الاستخدام، وإدارة قاعدة الأسئلة الشائعة، وإمكانية توليد أسئلة وأجوبة تلقائياً من رابط أو ملف PDF أو نص.

---

## License

MIT — see [LICENSE](LICENSE).

## Author

Developed at the University of Technology and Applied Sciences — Ibra.

**Contact:** zumurudalshabib@gmail.com
**GitHub:** [@SoftwereEngenOMBettol](https://github.com/SoftwereEngenOMBettol)
