# backend/app/routes/admin.py

import asyncio

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Header, Request
from typing import Optional, List
import json
import PyPDF2
import io
from pydantic import BaseModel
import re
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import psycopg2.extras
import jwt
import os
import httpx
from ..database import get_db
from ..models.fqa_models import FQACreate
from ..services.gemini_service import model
import google.generativeai as genai

router = APIRouter(prefix="/api/admin", tags=["Admin"])

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-this-in-production-2026")
ALGORITHM = "HS256"
class CategoryCreate(BaseModel):
    name_ar: str
    name_en: str
    description_ar: Optional[str] = ""
    description_en: Optional[str] = ""
    icon: Optional[str] = "fa-tag"

class ResponseTemplateCreate(BaseModel):
    intent_name: str
    keywords: List[str]
    response_html_en: str
    response_html_ar: str
    requires_data: bool = False
    data_tables: Optional[List[str]] = []
    category: Optional[str] = "General"

# Configure Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel('models/gemini-2.5-flash')
    print("✅ Gemini AI configured successfully")
else:
    gemini_model = None
    print("⚠️ GEMINI_API_KEY not found! AI features disabled.")
# ======================================================
# ADMIN AUTH - FIXED JWT VERIFICATION
# ======================================================
async def get_current_admin(authorization: str = Header(None)):

    if not authorization:
        print("❌ No authorization header")
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    try:
        # Extract Bearer token
        if not authorization.startswith("Bearer "):
            print("❌ Invalid auth header format")
            raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
        token = authorization.replace("Bearer ", "").strip()
        
        if not token:
            print("❌ Empty token")
            raise HTTPException(status_code=401, detail="Empty token")
        
        print(f"🔐 Verifying token: {token[:50]}...")
        
        # Decode JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        student_id = payload.get("student_id")
        is_admin = payload.get("is_admin", False)
        
        print(f"📥 Token payload: student_id={student_id}, is_admin={is_admin}")
        
        if not student_id:
            print("❌ No student_id in token")
            raise HTTPException(status_code=401, detail="Invalid token payload")
        
        # Double-check with database
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute(
            "SELECT is_admin FROM students WHERE student_id = %s",
            (student_id,)
        )
        
        row = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if not row:
            print(f"❌ User not found in DB: {student_id}")
            raise HTTPException(status_code=401, detail="User not found")
        
        db_is_admin = row[0]
        
        if not db_is_admin:
            print(f"❌ User {student_id} is not admin (DB value: {db_is_admin})")
            raise HTTPException(status_code=403, detail="Admin access required")
        
        print(f"✅ Admin verified: {student_id}")
        return student_id
        
    except jwt.ExpiredSignatureError:
        print("❌ Token expired")
        raise HTTPException(status_code=401, detail="Token expired")
        
    except jwt.InvalidTokenError as e:
        print(f"❌ Invalid token: {e}")
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
        
    except HTTPException:
        raise
        
    except Exception as e:
        print(f"❌ Auth error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
# backend/app/routes/admin.py - Add this function

# backend/app/utils/content_extractor.py

async def extract_url_content(url: str, max_length: int = 5000) -> str:
    """
    Extract meaningful content from a URL with size limit
    """
    import httpx
    from bs4 import BeautifulSoup
    
    print(f"\n📡 Extracting content from URL: {url}")
    
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(["script", "style", "noscript", "iframe", "nav", "footer", "header", "aside"]):
                element.decompose()
            
            # Try to find main content
            content = ""
            
            # Look for main content containers
            main_selectors = ['main', 'article', '.content', '#content', '.main-content']
            
            for selector in main_selectors:
                main_element = soup.select_one(selector)
                if main_element:
                    content = extract_text_from_element(main_element)
                    if len(content) > 500:
                        print(f"✅ Found content using selector: {selector}")
                        break
            
            # If no main content, use body
            if len(content) < 200:
                body = soup.find('body')
                if body:
                    content = extract_text_from_element(body)
            
            # If still no content, get all text
            if len(content) < 100:
                content = soup.get_text()
            
            # Clean the content
            content = re.sub(r'\n{3,}', '\n\n', content)
            content = re.sub(r' +', ' ', content)
            content = content.strip()
            
            # **CRITICAL: Limit content size to avoid timeout**
            if len(content) > max_length:
                # Take first max_length characters + important sections
                content = content[:max_length]
                print(f"⚠️ Content truncated to {max_length} characters")
            
            return content
            
    except Exception as e:
        print(f"❌ Content extraction error: {e}")
        return ""


def extract_text_from_element(element) -> str:
    """Extract clean text from BeautifulSoup element preserving structure"""
    text_parts = []
    
    # Extract headings (most important)
    for heading in element.find_all(['h1', 'h2', 'h3']):
        heading_text = heading.get_text(strip=True)
        if heading_text and len(heading_text) > 3:
            text_parts.append(f"\n## {heading_text}\n")
    
    # Extract paragraphs (limit to first 20)
    paragraphs = element.find_all('p')
    for p in paragraphs[:20]:  # Limit to first 20 paragraphs
        p_text = p.get_text(strip=True)
        if len(p_text) > 30:
            text_parts.append(p_text)
    
    # Extract list items
    list_items = element.find_all('li')
    for li in list_items[:30]:  # Limit to first 30 list items
        li_text = li.get_text(strip=True)
        if li_text and len(li_text) > 5:
            text_parts.append(f"• {li_text}")
    
    return '\n\n'.join(text_parts)
def extract_text_from_element(element) -> str:
    """
    Extract clean text from a BeautifulSoup element
    Preserves structure with headings, paragraphs, and lists
    """
    text_parts = []
    
    # Extract headings
    for heading in element.find_all(['h1', 'h2', 'h3', 'h4']):
        heading_text = heading.get_text(strip=True)
        if heading_text:
            text_parts.append(f"\n## {heading_text}\n")
    
    # Extract paragraphs
    for p in element.find_all('p'):
        p_text = p.get_text(strip=True)
        if len(p_text) > 20:  # Only meaningful paragraphs
            text_parts.append(p_text)
    
    # Extract list items
    for ul in element.find_all('ul'):
        for li in ul.find_all('li'):
            li_text = li.get_text(strip=True)
            if li_text:
                text_parts.append(f"• {li_text}")
    
    for ol in element.find_all('ol'):
        for idx, li in enumerate(ol.find_all('li'), 1):
            li_text = li.get_text(strip=True)
            if li_text:
                text_parts.append(f"{idx}. {li_text}")
    
    # Extract div content if no paragraphs found
    if not text_parts:
        for div in element.find_all('div'):
            div_text = div.get_text(strip=True)
            if len(div_text) > 50:
                text_parts.append(div_text)
    
    # Join all parts
    return '\n\n'.join(text_parts)

# ======================================================
# GEMINI FAQ GENERATOR
# ======================================================
async def process_with_gemini(content: str, content_type: str):
    """Generate bilingual FAQ from content."""
    
    if content_type == "html_css":
        soup = BeautifulSoup(content, "html.parser")
        text_content = soup.get_text(" ", strip=True)
    else:
        text_content = content
    
    prompt = f"""
You are helping a university admin create FAQs.

Analyze this content and generate 5 FAQs.

Content:
{text_content[:8000]}

Return ONLY valid JSON:

[
  {{
    "question_ar": "",
    "question_en": "",
    "answer_ar": "",
    "answer_en": ""
  }}
]
"""
    
    try:
        response = model.generate_content(prompt)
        
        text = response.text.strip()
        
        match = re.search(r"\[.*\]", text, re.DOTALL)
        
        if match:
            return json.loads(match.group())
        
        return json.loads(text)
        
    except Exception as e:
        print("Gemini error:", e)
        return []

async def extract_categories_with_gemini(content: str, content_type: str):
    """Extract categories and Q&A from content using Gemini AI"""
    
    if not gemini_model:
        return {
            "categories": [
                {
                    "name_ar": "عام",
                    "name_en": "General",
                    "description_ar": "أسئلة عامة عن الجامعة",
                    "description_en": "General university questions",
                    "faqs": [
                        {
                            "question_ar": "ما هي خدمات الجامعة؟",
                            "question_en": "What are university services?",
                            "answer_ar": "تقدم الجامعة العديد من الخدمات للطلاب.",
                            "answer_en": "The university offers many services for students.",
                            "keywords": ["services", "university"]
                        }
                    ]
                }
            ]
        }
    
    prompt = f"""
    You are an AI assistant helping a university admin create a comprehensive FAQ database.
    
    Content Type: {content_type}
    Content to analyze:
    {content[:10000]}
    
    Based on the above content, extract ALL categories and generate FAQs for each category.
    
    FORMAT YOUR RESPONSE AS JSON (ONLY JSON, no other text):
    {{
        "categories": [
            {{
                "name_ar": "اسم الفئة بالعربية",
                "name_en": "Category name in English",
                "description_ar": "وصف الفئة بالعربية",
                "description_en": "Category description in English",
                "faqs": [
                    {{
                        "question_ar": "السؤال بالعربية",
                        "question_en": "Question in English",
                        "answer_ar": "الإجابة المفصلة بالعربية",
                        "answer_en": "Detailed answer in English",
                        "keywords": ["keyword1", "keyword2"]
                    }}
                ]
            }}
        ]
    }}
    
    Requirements:
    1. Identify ALL main categories from the content (minimum 3 categories)
    2. For each category, generate 3-8 relevant FAQs
    3. All answers must be detailed and helpful for university students
    4. Include keywords for better search matching
    5. Make sure questions and answers are in BOTH Arabic and English
    6. Focus on academic, administrative, and student life topics
    """
    
    try:
        response = gemini_model.generate_content(prompt)
        
        # Extract JSON from response
        response_text = response.text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(response_text)
        
        return result
        
    except Exception as e:
        print(f"Gemini extraction error: {e}")
        return None
# backend/app/routes/admin.py

# Add this function to your admin.py file

async def extract_with_gemini(content: str, content_type: str):
    """
    Extract FAQs from content using Gemini AI
    
    Args:
        content: The text content to analyze (URL text, PDF text, or HTML content)
        content_type: Type of content ('url', 'pdf', 'html')
    
    Returns:
        Dictionary with 'faqs' array or None if failed
    """
    
    if not gemini_model:
        print("❌ Gemini model not available. Check your API key.")
        return None
    
    # Truncate content if too long (Gemini has token limits)
    max_chars = 15000
    if len(content) > max_chars:
        print(f"⚠️ Content truncated from {len(content)} to {max_chars} characters")
        content = content[:max_chars]
    
    # Build the prompt for Gemini
    prompt = f"""
You are a UTAS (University of Technology and Applied Sciences) AI assistant. 
Your task is to analyze the following {content_type} content and extract useful FAQs for university students.

CONTENT TO ANALYZE:
{content}

INSTRUCTIONS:
1. Read the content carefully
2. Identify important topics and create categories for them
3. For each category, generate 2-6 relevant FAQs
4. **CREATE NEW CATEGORIES** based on the content - don't limit to predefined categories

OUTPUT FORMAT (ONLY return valid JSON, no other text):
{{
    "categories": [
        {{
            "name_en": "Category Name in English",
            "name_ar": "اسم الفئة بالعربية",
            "description_en": "Brief description of this category",
            "description_ar": "وصف مختصر لهذه الفئة",
            "faqs": [
                {{
                    "question_en": "Question in English",
                    "question_ar": "السؤال بالعربية",
                    "answer_en": "Detailed answer in English",
                    "answer_ar": "إجابة مفصلة بالعربية"
                }}
            ]
        }}
    ]
}}

RULES:
1. Create NEW categories based on the content topics
2. Each category should have 2-6 related FAQs
3. ALL text must be in BOTH Arabic and English
4. Return ONLY valid JSON
"""
    try:
        print(f"🤖 Sending request to Gemini AI (Free: gemini-2.5-flash)...")
        print(f"📝 Content length: {len(content)} characters")
        
        # Make the API call
        response = gemini_model.generate_content(prompt)
        
        print(f"✅ Gemini response received")
        
        # Get the response text
        response_text = response.text
        print(f"📄 Response preview: {response_text[:200]}...")
        
        # Try to extract JSON from the response
        # Look for JSON pattern with braces
        json_match = re.search(r'\{[^{}]*"faqs"[^{}]*\[.*?\][^{}]*\}', response_text, re.DOTALL)
        
        if not json_match:
            # Try more flexible pattern
            json_match = re.search(r'\{.*"faqs".*\}', response_text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group()
            result = json.loads(json_str)
        else:
            # Try parsing the whole response as JSON
            result = json.loads(response_text)
        
        # Validate the result structure
        if 'faqs' not in result:
            print("⚠️ Response missing 'faqs' field, creating default structure")
            result = {'faqs': []}
        
        # Ensure minimum FAQs
        if len(result.get('faqs', [])) == 0:
            print("⚠️ No FAQs generated, using fallback")
            result['faqs'] = [
                {
                    "question_en": "What information is available in this content?",
                    "question_ar": "ما المعلومات المتوفرة في هذا المحتوى؟",
                    "answer_en": f"Based on the {content_type} content, we have extracted the following information. Please check the source for more details.",
                    "answer_ar": f"بناءً على محتوى {content_type}، قمنا باستخراج المعلومات التالية. يرجى مراجعة المصدر لمزيد من التفاصيل.",
                    "category": "General"
                }
            ]
        
        print(f"✅ Successfully generated {len(result['faqs'])} FAQs")
        return result
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        print(f"Raw response: {response_text[:500]}")
        return None
        
    except Exception as e:
        print(f"❌ Gemini API error: {e}")
        import traceback
        traceback.print_exc()
        return None


# Alternative: Simpler version for testing
async def extract_with_gemini_simple(content: str, content_type: str):
    """
    Simplified version of Gemini extraction - returns fallback FAQs
    Use this for testing if the full version has issues
    """
    
    if not gemini_model:
        print("❌ Gemini model not available")
        # Return fallback FAQs
        return {
            "faqs": [
                {
                    "question_en": "How to access the content?",
                    "question_ar": "كيفية الوصول إلى المحتوى؟",
                    "answer_en": f"The content from {content_type} has been saved. Please review it manually for specific information.",
                    "answer_ar": f"تم حفظ المحتوى من {content_type}. يرجى مراجعته يدوياً للحصول على معلومات محددة.",
                    "category": "General"
                }
            ]
        }
    
    try:
        prompt = f"""
Analyze this {content_type} content and extract 3-5 FAQs:

{content[:5000]}

Return JSON:
{{"faqs": [{{"question_en": "", "question_ar": "", "answer_en": "", "answer_ar": "", "category": ""}}]}}
"""
        
        response = gemini_model.generate_content(prompt)
        response_text = response.text
        
        # Extract JSON
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(response_text)
        
    except Exception as e:
        print(f"❌ Simple extraction error: {e}")
        return None


# Complete URL processing function using the extractor


@router.post("/fqa/from-url")
async def create_fqa_from_url(
    url: str = Form(...),
    category: str = Form(...),
    admin_id: str = Depends(get_current_admin)
):
    """Extract from URL and generate FAQs using Gemini AI"""
    try:
        from ..services.gemini_service import generate_faqs_from_content
        
        print(f"\n{'='*60}")
        print(f"📡 Processing URL: {url}")
        print(f"👤 Admin ID: {admin_id}")
        print(f"{'='*60}")
        
        # Extract content with size limit (max 5000 chars to avoid timeout)
        content = await extract_url_content(url, max_length=5000)
        
        if not content or len(content) < 100:
            raise HTTPException(status_code=400, detail="Could not extract enough content from URL")
        
        print(f"📄 Extracted {len(content)} characters for processing")
        
        # Generate FAQs with timeout handling
        try:
            generated_faqs = await asyncio.wait_for(
                generate_faqs_from_content(content, "url", admin_id),
                timeout=60.0  # 60 second timeout
            )
        except asyncio.TimeoutError:
            print("⏰ Gemini request timed out, using fallback")
            generated_faqs = get_fallback_faqs_for_url(url, category)
        
        if not generated_faqs:
            generated_faqs = get_fallback_faqs_for_url(url, category)
        
        # Save to database
        saved_faqs = []
        conn = get_db()
        cur = conn.cursor()
        
        for faq in generated_faqs:
            cur.execute("""
                INSERT INTO fqa (question_ar, question_en, answer_ar, answer_en, category, 
                               attachment_type, attachment_content, created_by, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                faq.get('question_ar', ''),
                faq.get('question_en', ''),
                faq.get('answer_ar', ''),
                faq.get('answer_en', ''),
                category or 'University Regulations',
                'url',
                url,
                str(admin_id),  # Ensure it's string
                datetime.now()
            ))
            fqa_id = cur.fetchone()[0]
            saved_faqs.append({"id": fqa_id, **faq})
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "message": f"✅ Successfully generated {len(saved_faqs)} FAQs from URL",
            "faqs": saved_faqs
        }
        
    except Exception as e:
        print(f"❌ URL processing error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def get_fallback_faqs_for_url(url: str, category: str):
    """Return fallback FAQs when Gemini fails"""
    return [
        {
            "question_ar": "ما هي المعلومات الموجودة في هذا الرابط؟",
            "question_en": "What information is in this link?",
            "answer_ar": f"هذا الرابط يحتوي على معلومات حول {category}. لمزيد من التفاصيل، يرجى زيارة الرابط مباشرة.",
            "answer_en": f"This link contains information about {category}. For more details, please visit the link directly."
        },
        {
            "question_ar": "كيف يمكنني الوصول إلى هذه المعلومات؟",
            "question_en": "How can I access this information?",
            "answer_ar": f"يمكنك الوصول إلى المعلومات الكاملة من خلال الرابط: {url}",
            "answer_en": f"You can access the full information through the link: {url}"
        }
    ]

async def save_categories_and_faqs(result: dict, admin_id: str, source_type: str, source_name: str):
    """Save extracted categories and FAQs to database"""
    conn = get_db()
    cur = conn.cursor()
    
    categories_count = 0
    faqs_count = 0
    saved_categories = []
    
    try:
        # Check if categories table exists, if not create it
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name_ar VARCHAR(255),
                name_en VARCHAR(255),
                description_ar TEXT,
                description_en TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        for category_data in result.get('categories', []):
            # Check if category already exists
            cur.execute("SELECT id FROM categories WHERE name_en = %s", (category_data.get('name_en'),))
            existing = cur.fetchone()
            
            if existing:
                category_id = existing[0]
                saved_categories.append({"id": category_id, "name": category_data.get('name_en')})
            else:
                # Insert new category
                cur.execute("""
                    INSERT INTO categories (name_ar, name_en, description_ar, description_en, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    category_data.get('name_ar', ''),
                    category_data.get('name_en', ''),
                    category_data.get('description_ar', ''),
                    category_data.get('description_en', ''),
                    datetime.now()
                ))
                category_id = cur.fetchone()[0]
                categories_count += 1
                saved_categories.append({"id": category_id, "name": category_data.get('name_en')})
            
            # Insert FAQs for this category
            for faq in category_data.get('faqs', []):
                # Check if FAQ already exists to avoid duplicates
                cur.execute("""
                    SELECT id FROM fqa 
                    WHERE question_en = %s OR question_ar = %s
                    LIMIT 1
                """, (faq.get('question_en', ''), faq.get('question_ar', '')))
                
                existing_faq = cur.fetchone()
                
                if not existing_faq:
                    cur.execute("""
                        INSERT INTO fqa (
                            question_ar, question_en, answer_ar, answer_en, 
                            category_id, category, source_type, source_name, 
                            keywords, created_by, created_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        faq.get('question_ar', ''),
                        faq.get('question_en', ''),
                        faq.get('answer_ar', ''),
                        faq.get('answer_en', ''),
                        category_id,
                        category_data.get('name_en', 'General'),
                        source_type,
                        source_name,
                        ', '.join(faq.get('keywords', [])),
                        admin_id,
                        datetime.now()
                    ))
                    faqs_count += 1
        
        conn.commit()
        
        return {
            "categories_count": categories_count,
            "faqs_count": faqs_count,
            "total_faqs": faqs_count,
            "categories": saved_categories
        }
        
    except Exception as e:
        conn.rollback()
        print(f"Save error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

# ======================================================
# DASHBOARD STATS
# ======================================================


# ==================== AI GENERATION ENDPOINTS ====================

@router.post("/fqa/generate-from-content")
async def generate_fqa_from_content(
    content: str = Form(...),
    content_type: str = Form(...),
    category: str = Form(...),
    admin_id: str = Depends(get_current_admin)
):
    """Generate FAQs from HTML/CSS content using Gemini AI"""
    try:
        # Import Gemini service
        from ..services.gemini_service import generate_faqs_from_content
        
        # Process content with Gemini
        generated_faqs = await generate_faqs_from_content(content, content_type)
        
        saved_faqs = []
        conn = get_db()
        cur = conn.cursor()
        
        for faq in generated_faqs:
            cur.execute("""
                INSERT INTO fqa (question_ar, question_en, answer_ar, answer_en, category, 
                               attachment_type, attachment_content, created_by, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                faq.get('question_ar', ''),
                faq.get('question_en', ''),
                faq.get('answer_ar', ''),
                faq.get('answer_en', ''),
                category,
                content_type,
                content[:1000],
                admin_id,
                datetime.now()
            ))
            fqa_id = cur.fetchone()[0]
            saved_faqs.append({"id": fqa_id, **faq})
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "message": f"Successfully generated and saved {len(saved_faqs)} FAQs",
            "faqs": saved_faqs
        }
    except Exception as e:
        print(f"Generate from content error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fqa/upload-pdf")
async def upload_pdf_generate_fqa(
    file: UploadFile = File(...),
    category: str = Form(...),
    admin_id: str = Depends(get_current_admin)
):
    """Upload PDF and generate FAQs using Gemini AI"""
    try:
        import PyPDF2
        import io
        
        # Read PDF content
        pdf_content = await file.read()
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
        
        extracted_text = ""
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                extracted_text += text
        
        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from PDF")
        
        # Process with Gemini
        from ..services.gemini_service import generate_faqs_from_content
        
        generated_faqs = await generate_faqs_from_content(extracted_text, "pdf")
        
        saved_faqs = []
        conn = get_db()
        cur = conn.cursor()
        
        for faq in generated_faqs:
            cur.execute("""
                INSERT INTO fqa (question_ar, question_en, answer_ar, answer_en, category, 
                               attachment_type, attachment_content, created_by, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                faq.get('question_ar', ''),
                faq.get('question_en', ''),
                faq.get('answer_ar', ''),
                faq.get('answer_en', ''),
                category,
                'pdf',
                file.filename,
                admin_id,
                datetime.now()
            ))
            fqa_id = cur.fetchone()[0]
            saved_faqs.append({"id": fqa_id, **faq})
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "message": f"Successfully generated {len(saved_faqs)} FAQs from PDF",
            "faqs": saved_faqs
        }
    except Exception as e:
        print(f"PDF upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# backend/app/routes/admin.py



@router.get("/usage")
async def get_usage(admin_id: str = Depends(get_current_admin)):
    """Get app usage statistics"""
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT *
            FROM app_usage
            WHERE date = CURRENT_DATE
        """)
        
        today = cur.fetchone()
        
        cur.execute("""
            SELECT
                COALESCE(SUM(total_sessions),0),
                COALESCE(SUM(total_queries),0),
                COALESCE(SUM(unique_students),0)
            FROM app_usage
            WHERE date >= CURRENT_DATE - INTERVAL '7 days'
        """)
        
        week = cur.fetchone()
        
        cur.execute("""
            SELECT
                date,
                total_sessions,
                total_queries,
                unique_students
            FROM app_usage
            WHERE date >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY date
        """)
        
        chart = cur.fetchall()
        
        return {
            "today": {
                "total_sessions": today[2] if today else 0,
                "total_queries": today[3] if today else 0,
                "unique_students": today[4] if today else 0
            },
            "week": {
                "total_sessions": week[0],
                "total_queries": week[1],
                "total_users": week[2]
            },
            "month": {
                "total_sessions": week[0],
                "total_queries": week[1],
                "total_users": week[2]
            },
            "chart_data": [
                {
                    "date": str(r[0]),
                    "total_sessions": r[1],
                    "total_queries": r[2],
                    "unique_students": r[3]
                }
                for r in chart
            ]
        }
        
    finally:
        cur.close()
        conn.close()

# backend/app/routes/admin.py

@router.post("/fqa/from-url")
async def process_url(
    url: str = Form(...),
    admin_id: str = Depends(get_current_admin)  # Keep as string, not int
):
    """Process URL and extract FAQs using Gemini"""
    try:
        print(f"\n{'='*60}")
        print(f"📡 Processing URL: {url}")
        print(f"👤 Admin ID: {admin_id}")
        print(f"{'='*60}")
        
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Fetch URL content
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script/style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Extract meaningful text (not just all text)
            text_parts = []
            
            # Get title
            title = soup.find('title')
            if title:
                text_parts.append(f"Title: {title.get_text(strip=True)}")
            
            # Get headings
            for heading in soup.find_all(['h1', 'h2', 'h3']):
                h_text = heading.get_text(strip=True)
                if h_text and len(h_text) > 5:
                    text_parts.append(h_text)
            
            # Get paragraphs
            for p in soup.find_all('p'):
                p_text = p.get_text(strip=True)
                if len(p_text) > 30:
                    text_parts.append(p_text)
            
            # Get list items
            for li in soup.find_all('li'):
                li_text = li.get_text(strip=True)
                if li_text and len(li_text) > 5:
                    text_parts.append(f"• {li_text}")
            
            text_content = '\n\n'.join(text_parts)
            
            # Limit content size
            if len(text_content) > 8000:
                text_content = text_content[:8000]
                print(f"⚠️ Content truncated to 8000 characters")
            
            print(f"📄 Extracted {len(text_content)} characters")
        
        if not text_content.strip():
            raise HTTPException(status_code=400, detail="Could not extract text from URL")
        
        # Extract FAQs with Gemini
        from ..services.gemini_service import generate_faqs_from_content
        
        generated_faqs = await generate_faqs_from_content(text_content, "url", admin_id)
        
        if not generated_faqs:
            # Create fallback FAQs
            generated_faqs = [
                {
                    "question_ar": f"ما هي المعلومات المتعلقة بـ {url}؟",
                    "question_en": f"What information is available at {url}?",
                    "answer_ar": f"تم استخراج هذا المحتوى من الرابط: {url}. لمزيد من التفاصيل، يرجى زيارة الرابط مباشرة.",
                    "answer_en": f"This content was extracted from: {url}. For more details, please visit the link directly."
                }
            ]
        
        # Save to database
        conn = get_db()
        cur = conn.cursor()
        saved_count = 0
        
        for faq in generated_faqs:
            try:
                # Get question and answer (handle both possible formats)
                question_en = faq.get('question_en', faq.get('question', ''))
                question_ar = faq.get('question_ar', '')
                answer_en = faq.get('answer_en', faq.get('answer', ''))
                answer_ar = faq.get('answer_ar', '')
                
                if not question_en:
                    question_en = f"Information from {url}"
                if not answer_en:
                    answer_en = f"Please visit {url} for more information"
                
                cur.execute("""
                    INSERT INTO fqa (
                        question_en, question_ar, answer_en, answer_ar, 
                        category, source_type, source_name, created_by, created_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    question_en,
                    question_ar,
                    answer_en,
                    answer_ar,
                    faq.get('category', 'General'),
                    'url',
                    url,
                    admin_id,  # This is a string, which matches your DB column
                    datetime.now()
                ))
                new_id = cur.fetchone()[0]
                saved_count += 1
                print(f"✅ Saved FAQ {saved_count} (ID: {new_id}): {question_en[:50]}...")
            except Exception as e:
                print(f"❌ Error saving FAQ: {e}")
                continue
        
        conn.commit()
        cur.close()
        conn.close()
        
        return {
            "success": True,
            "message": f"✅ Successfully processed URL! Created {saved_count} FAQs",
            "count": saved_count,
            "faqs": generated_faqs
        }
        
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="URL request timed out")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"HTTP error: {e.response.status_code}")
    except Exception as e:
        print(f"❌ URL processing error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
# ======================================================
# STUDENTS
# ======================================================
@router.get("/students")
async def get_students(admin_id: str = Depends(get_current_admin)):
    """Get all students list"""
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT
                student_id,
                name,
                email,
                department,
                created_at
            FROM students
            ORDER BY created_at DESC
        """)
        
        rows = cur.fetchall()
        
        return [dict(r) for r in rows]
        
    finally:
        cur.close()
        conn.close()


# ======================================================
# FAQ LIST
# ======================================================
@router.get("/fqa")
async def get_faqs(admin_id: str = Depends(get_current_admin)):
    """Get all FAQs"""
    
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT *
            FROM fqa
            ORDER BY id DESC
        """)
        
        rows = cur.fetchall()
        
        return [dict(r) for r in rows]
        
    finally:
        cur.close()
        conn.close()


# ======================================================
# CREATE FAQ MANUAL
# ======================================================
# backend/app/routes/admin.py - Add template management

@router.post("/response-templates")
async def create_response_template(
    template: ResponseTemplateCreate,
    admin_id: str = Depends(get_current_admin)
):
    """Admin creates new response template with HTML/CSS"""
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO response_templates (intent_name, keywords, response_html_en, response_html_ar, requires_data, data_tables)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (
        template.intent_name,
        template.keywords,
        template.response_html_en,
        template.response_html_ar,
        template.requires_data,
        template.data_tables
    ))
    
    conn.commit()
    return {"message": "Template created", "id": cur.fetchone()[0]}


@router.get("/response-templates")
async def get_response_templates():
    """Get all response templates for admin to view/edit"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cur.execute("SELECT * FROM response_templates WHERE is_active = true")
    templates = cur.fetchall()
    return [dict(t) for t in templates]

# ======================================================
# DELETE FAQ
# ======================================================
@router.delete("/fqa/{faq_id}")
async def delete_faq(
    faq_id: int,
    admin_id: str = Depends(get_current_admin)
):
    """Delete an FAQ"""
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute(
            "DELETE FROM fqa WHERE id=%s RETURNING id",
            (faq_id,)
        )
        
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="FAQ not found")
        
        conn.commit()
        
        return {"message": "Deleted"}
        
    finally:
        cur.close()
        conn.close()


# ======================================================
# PENDING QUESTIONS
# ======================================================
@router.get("/fqa/pending")
async def get_pending_questions(admin_id: str = Depends(get_current_admin)):
    """Get unanswered questions from students for admin to review"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    
    try:
        cur.execute("""
            SELECT 
                uq.id,
                uq.student_id,
                uq.question,
                uq.language,
                uq.asked_at,
                uq.status,
                uq.times_asked,
                uq.last_asked,
                COALESCE(s.name, 'Unknown Student') as student_name
            FROM unanswered_questions uq
            LEFT JOIN students s ON CAST(s.student_id AS VARCHAR) = CAST(uq.student_id AS VARCHAR)
            WHERE uq.status = 'pending'
            ORDER BY uq.times_asked DESC, uq.asked_at ASC
        """)
        
        questions = cur.fetchall()
        result = []
        for q in questions:
            result.append({
                "id": q[0],
                "student_id": str(q[1]),
                "question": q[2],
                "language": q[3],
                "asked_at": q[4].isoformat() if q[4] else None,
                "status": q[5],
                "times_asked": q[6] or 1,
                "last_asked": q[7].isoformat() if q[7] else None,
                "student_name": q[8]
            })
        
        print(f"📋 Retrieved {len(result)} pending questions")
        return result
        
    except Exception as e:
        print(f"Error in get_pending_questions: {e}")
        return []
    finally:
        cur.close()
        conn.close()
# Add to backend/app/routes/admin.py - Update the create endpoint

@router.post("/fqa/manual")
async def create_manual_fqa(
    fqa: FQACreate,
    admin_id: str = Depends(get_current_admin)
):
    """Admin manually creates Q&A with date fields"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO fqa (
                question_ar, question_en, answer_ar, answer_en, category, 
                valid_from, valid_until, academic_year, semester, is_active,
                created_by, created_at, effective_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            fqa.question_ar,
            fqa.question_en,
            fqa.answer_ar,
            fqa.answer_en,
            fqa.category,
            fqa.valid_from,
            fqa.valid_until,
            fqa.academic_year,
            fqa.semester,
            fqa.is_active,
            admin_id,
            datetime.now(),
            datetime.now()
        ))
        fqa_id = cur.fetchone()[0]
        conn.commit()
        
        return {
            "success": True,
            "message": "FAQ created successfully",
            "id": fqa_id
        }
    except Exception as e:
        print(f"Create manual FQA error: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

# Add endpoint to get FAQs by date/semester
@router.get("/fqa/by-semester")
async def get_faqs_by_semester(
    academic_year: Optional[str] = None,
    semester: Optional[str] = None,
    admin_id: str = Depends(get_current_admin)
):
    """Get FAQs filtered by academic year and semester"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        query = """
            SELECT * FROM fqa 
            WHERE is_active = TRUE
        """
        params = []
        
        if academic_year:
            query += " AND academic_year = %s"
            params.append(academic_year)
        
        if semester:
            query += " AND semester = %s"
            params.append(semester)
        
        query += " ORDER BY effective_date DESC"
        
        cur.execute(query, params)
        fqas = cur.fetchall()
        return [dict(f) for f in fqas]
    finally:
        cur.close()
        conn.close()

# Get unique academic years for filter
@router.get("/fqa/academic-years")
async def get_academic_years(admin_id: str = Depends(get_current_admin)):
    """Get list of unique academic years"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT DISTINCT academic_year 
            FROM fqa 
            WHERE academic_year IS NOT NULL 
            ORDER BY academic_year DESC
        """)
        years = [row[0] for row in cur.fetchall()]
        return {"academic_years": years}
    finally:
        cur.close()
        conn.close()
# ======================================================
# ANSWER QUESTION
# ======================================================
@router.post("/fqa/answer-pending/{question_id}")
async def answer_question(
    question_id: int,
    answer_ar: str = Form(...),
    answer_en: str = Form(...),
    admin_id: str = Depends(get_current_admin)
):
    """Answer a pending question and convert to FAQ"""
    
    conn = get_db()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            SELECT question, language
            FROM unanswered_questions
            WHERE id = %s
        """, (question_id,))
        
        row = cur.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Question not found")
        
        original_question = row[0]
        original_language = row[1]
        
        # Add to FAQ
        cur.execute("""
            INSERT INTO fqa
            (
                question_ar,
                question_en,
                answer_ar,
                answer_en,
                category,
                created_by,
                created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            original_question if original_language == 'ar' else original_question,
            original_question if original_language == 'en' else original_question,
            answer_ar,
            answer_en,
            "student_question",
            admin_id,
            datetime.now()
        ))
        
        # Mark as answered
        cur.execute("""
            UPDATE unanswered_questions
            SET status = 'answered',
                answered_at = %s
            WHERE id = %s
        """, (datetime.now(), question_id))
        
        conn.commit()
        
        return {"message": "Answered successfully and added to FAQs"}
        
    finally:
        cur.close()
        conn.close()
# Add these endpoints to backend/app/routes/admin.py

from fastapi import UploadFile, File, Form
import PyPDF2
import io
import httpx

@router.post("/generate-faqs")
async def generate_faqs_with_ai(
    content: str = Form(...),
    content_type: str = Form(...),
    category: str = Form("general"),
    num_questions: int = Form(5),
    admin_id: str = Depends(get_current_admin)
):
    """Generate FAQs from text content using Gemini AI"""
    
    try:
        # Process content based on type
        if content_type == "url":
            # Fetch website content
            async with httpx.AsyncClient() as client:
                response = await client.get(content, timeout=30)
                soup = BeautifulSoup(response.text, "html.parser")
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                text_content = soup.get_text(" ", strip=True)
        else:
            # HTML content
            soup = BeautifulSoup(content, "html.parser")
            text_content = soup.get_text(" ", strip=True)
        
        # Generate FAQs with Gemini
        prompt = f"""
You are a university assistant creating FAQs. Analyze this content and generate {num_questions} FAQs.

Content:
{text_content[:8000]}

Return ONLY valid JSON array:
[
  {{
    "question_ar": "السؤال بالعربية",
    "question_en": "Question in English",
    "answer_ar": "الإجابة بالعربية",
    "answer_en": "Answer in English"
  }}
]

Make sure each FAQ is relevant to university topics.
"""
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Extract JSON
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            faqs = json.loads(match.group())
        else:
            faqs = json.loads(text)
        
        return {
            "success": True,
            "faqs": faqs,
            "count": len(faqs)
        }
        
    except Exception as e:
        print(f"Error generating FAQs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fqa/public")
async def get_public_fqa():
    """
    PUBLIC endpoint to get all FAQs (no authentication required)
    This is for the chat interface to display FAQs
    """
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        cur.execute("""
            SELECT id, question_ar, question_en, answer_ar, answer_en, category 
            FROM fqa 
            ORDER BY id DESC
        """)
        fqas = cur.fetchall()
        return [dict(f) for f in fqas]
    except Exception as e:
        print(f"Public FQA error: {e}")
        return []
    finally:
        cur.close()
        conn.close()

# ==================== CATEGORIES ====================
@router.post("/categories")
async def create_category(
    name_ar: str = Form(...),
    name_en: str = Form(...),
    description_ar: str = Form(""),
    description_en: str = Form(""),
    admin_numeric_id: int = Depends(get_current_admin)
):
    """Create a new category"""
    conn = get_db()
    cur = conn.cursor()
    try:
        # Ensure table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id SERIAL PRIMARY KEY,
                name_ar VARCHAR(255),
                name_en VARCHAR(255),
                description_ar TEXT,
                description_en TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        cur.execute("""
            INSERT INTO categories (name_ar, name_en, description_ar, description_en, created_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (name_ar, name_en, description_ar, description_en, admin_numeric_id, datetime.now()))
        
        cat_id = cur.fetchone()[0]
        conn.commit()
        
        return {
            "success": True,
            "message": "Category created successfully",
            "id": cat_id
        }
    except Exception as e:
        print(f"Create category error: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()

@router.get("/categories")
async def get_all_categories():
    """Get all categories - No authentication required"""
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    try:
        # Check if categories table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'categories'
            )
        """)
        table_exists = cur.fetchone()[0]
        
        if not table_exists:
            # Return default categories
            return [
                {"id": 1, "name_ar": "عام", "name_en": "General", "icon": "fa-university"},
                {"id": 2, "name_ar": "التسجيل", "name_en": "Registration", "icon": "fa-calendar-plus"},
                {"id": 3, "name_ar": "المعدل", "name_en": "GPA", "icon": "fa-chart-line"},
                {"id": 4, "name_ar": "الجدول", "name_en": "Schedule", "icon": "fa-calendar-alt"}
            ]
        
        cur.execute("SELECT * FROM categories ORDER BY id")
        categories = cur.fetchall()
        return [dict(c) for c in categories]
    except Exception as e:
        print(f"Categories error: {e}")
        return []
    finally:
        cur.close()
        conn.close()
@router.put("/categories/{category_id}")
async def update_category(
    category_id: int,
    name_ar: str = Form(...),
    name_en: str = Form(...),
    description_ar: str = Form(""),
    description_en: str = Form(""),
    admin_id: str = Depends(get_current_admin)
):
    """Update a category"""
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE categories 
            SET name_ar=%s, name_en=%s, description_ar=%s, description_en=%s
            WHERE id=%s
        """, (name_ar, name_en, description_ar, description_en, category_id))
        conn.commit()
        return {"success": True, "message": "Category updated"}
    finally:
        cur.close()
        conn.close()

@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int,
    admin_id: str = Depends(get_current_admin)
):
    """Delete a category and all its FAQs"""
    conn = get_db()
    cur = conn.cursor()
    try:
        # Delete FAQs in this category first
        cur.execute("DELETE FROM fqa WHERE category_id = %s", (category_id,))
        # Delete the category
        cur.execute("DELETE FROM categories WHERE id = %s", (category_id,))
        conn.commit()
        return {"success": True, "message": "Category deleted"}
    finally:
        cur.close()
        conn.close()

# ==================== HEALTH CHECK ====================

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "gemini_configured": gemini_model is not None,
        "timestamp": datetime.now().isoformat()
    }

@router.post("/generate-faqs/pdf")
async def generate_faqs_from_pdf(
    file: UploadFile = File(...),
    category: str = Form("general"),
    admin_id: str = Depends(get_current_admin)
):
    """Generate FAQs from PDF using Gemini AI"""
    
    try:
        # Read PDF file
        contents = await file.read()
        pdf_file = io.BytesIO(contents)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Extract text from all pages
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text()
        
        # Generate FAQs with Gemini
        prompt = f"""
You are a university assistant creating FAQs. Analyze this PDF content and generate 5 FAQs.

Content:
{text_content[:8000]}

Return ONLY valid JSON array:
[
  {{
    "question_ar": "السؤال بالعربية",
    "question_en": "Question in English",
    "answer_ar": "الإجابة بالعربية",
    "answer_en": "Answer in English"
  }}
]

Make sure each FAQ is relevant to university topics.
"""
        
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Extract JSON
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            faqs = json.loads(match.group())
        else:
            faqs = json.loads(text)
        
        return {
            "success": True,
            "faqs": faqs,
            "count": len(faqs)
        }
        
    except Exception as e:
        print(f"Error generating FAQs from PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))