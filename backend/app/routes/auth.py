# backend/app/routes/auth.py

from fastapi import APIRouter, HTTPException, Header, Request
from datetime import datetime, timedelta
import jwt
import bcrypt
import uuid
import re
import os
from ..database import get_db
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api", tags=["auth"]) 

SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-super-secret-key-change-this-in-production-2026')
ALGORITHM = "HS256"

# Models
class LoginRequest(BaseModel):
    student_id: str
    password: str
    language: str = "en"

class TokenResponse(BaseModel):
    success: bool
    token: str
    session_token: str
    student: dict
    preferred_language: str

# backend/app/routes/auth.py

async def get_current_admin(authorization: str = Header(None)):
    """Get current admin ID as string"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization token")
    
    try:
        token = authorization.split(' ')[1] if 'Bearer ' in authorization else authorization
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        student_id = payload.get('student_id')
        
        if not student_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT is_admin FROM students WHERE student_id = %s", (student_id,))
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if not result or not result[0]:
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Return the string student_id (not an integer)
        return student_id  # This returns "admin3" not 3
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")
    
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password using bcrypt"""
    try:
        if not hashed_password:
            print("No hashed password provided")
            return False
        
        result = bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        return result
    except Exception as e:
        print(f"Password verification error: {e}")
        return False
def create_jwt_token(student_id: str, is_admin: bool = False) -> str:
    """Create JWT token for authentication (used by both admin and regular users)"""
    payload = {
        'student_id': student_id,
        'is_admin': is_admin,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def create_session_token(student_id: str, ip: str = None, user_agent: str = None) -> str:
    """Create session token in database"""
    conn = get_db()
    cur = conn.cursor()
    session_token = str(uuid.uuid4())
    try:
        cur.execute(
            "INSERT INTO user_sessions (student_id, session_token, ip_address, user_agent, login_time) VALUES (%s, %s, %s, %s, %s)",
            (student_id, session_token, ip, user_agent, datetime.now())
        )
        conn.commit()
        return session_token
    except Exception as e:
        print(f"Session creation error: {e}")
        return None
    finally:
        cur.close()
        conn.close()

@router.post("/login")
async def login(request: LoginRequest, req: Request):
    """Student login endpoint - returns BOTH JWT and session token"""
    
    print(f"\n{'='*60}")
    print(f"🔐 LOGIN ATTEMPT")
    print(f"{'='*60}")
    print(f"Student ID: {request.student_id}")
    print(f"Language: {request.language}")
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        # Get student from database
        cur.execute("""
            SELECT id, student_id, name, email, department, preferred_language,
                   advisor, advisor_email, contact, current_semester, status, password_hash, is_admin
            FROM students 
            WHERE student_id = %s
        """, (request.student_id,))
        
        student = cur.fetchone()
        
        if not student:
            print(f"❌ Student not found: {request.student_id}")
            raise HTTPException(status_code=401, detail="Invalid student ID or password")
        
        stored_hash = student[11]
        is_admin = bool(student[12]) if len(student) > 12 else False
        
        # Verify password
        if not verify_password(request.password, stored_hash):
            print(f"❌ Invalid password for: {request.student_id}")
            raise HTTPException(status_code=401, detail="Invalid student ID or password")
        
        print(f"✅ Password verified for: {student[2]}")
        
        # Create JWT token (used for API authentication)
        jwt_token = create_jwt_token(request.student_id, is_admin)
        
        # Create session token (used for chat)
        client_ip = req.client.host if req.client else None
        user_agent = req.headers.get("user-agent")
        session_token = create_session_token(request.student_id, client_ip, user_agent)
        
        # Update last login and preferred language
        cur.execute("""
            UPDATE students 
            SET last_login = %s, preferred_language = %s 
            WHERE student_id = %s
        """, (datetime.now(), request.language, request.student_id))
        conn.commit()
        
        student_data = {
            'student_id': student[1],
            'name': student[2],
            'email': student[3],
            'department': student[4],
            'preferred_language': request.language,
            'is_admin': is_admin
        }
        
        response_data = {
            'success': True,
            'token': jwt_token,  # JWT for API auth
            'session_token': session_token,  # Session for chat
            'student': student_data,
            'preferred_language': request.language
        }
        
        print(f"✅ Login successful! JWT token created")
        print(f"{'='*60}\n")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        cur.close()
        conn.close()

@router.get("/verify")
async def verify_token(authorization: Optional[str] = None):
    """Verify JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")
    
    try:
        token = authorization.split(' ')[1] if 'Bearer ' in authorization else authorization
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        student_id = payload.get('student_id')
        
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT student_id, name, email, department, preferred_language, is_admin
            FROM students 
            WHERE student_id = %s
        """, (student_id,))
        
        student = cur.fetchone()
        cur.close()
        conn.close()
        
        if not student:
            raise HTTPException(status_code=401, detail="Student not found")
        
        return {
            'valid': True,
            'student': {
                'student_id': student[0],
                'name': student[1],
                'email': student[2],
                'department': student[3],
                'preferred_language': student[4],
                'is_admin': bool(student[5]) if len(student) > 5 else False
            }
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        print(f"Verify error: {e}")
        raise HTTPException(status_code=401, detail=str(e))

@router.post("/logout")
async def logout(session_token: str = None):
    """Logout endpoint"""
    if session_token:
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE user_sessions SET logout_time = %s WHERE session_token = %s", 
                       (datetime.now(), session_token))
            conn.commit()
        except Exception as e:
            print(f"Logout error: {e}")
        finally:
            cur.close()
            conn.close()
    
    return {'success': True}