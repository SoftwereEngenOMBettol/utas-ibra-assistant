# backend/check_models.py

import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ No API key found!")
    exit()

genai.configure(api_key=api_key)

print("\n📋 Available Gemini Models:\n")
print("=" * 60)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")
    else:
        print(f"⚠️ {model.name} (no generateContent)")

print("=" * 60)