# backend/check_users.py

import bcrypt
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

def check_password(hashed, plain_password):
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed.encode('utf-8'))
    except:
        return False

# Connect to database
conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    database=os.getenv("DB_NAME", "utas_chatbot"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "your_password"),
    port=os.getenv("DB_PORT", "5432")
)

cur = conn.cursor()
cur.execute("SELECT student_id, name, password_hash, is_admin FROM students")
users = cur.fetchall()

print("\n" + "="*60)
print("USERS IN DATABASE")
print("="*60)

for user in users:
    student_id, name, hash_val, is_admin = user
    print(f"\nStudent ID: {student_id}")
    print(f"Name: {name}")
    print(f"Is Admin: {is_admin}")
    print(f"Hash: {hash_val[:30] if hash_val else 'None'}...")
    
    # Test common passwords
    test_passwords = ['admin123', 'student123', 'password123', '123456', 'admin', 'test123']
    
    print("Testing passwords:")
    for test_pwd in test_passwords:
        if hash_val and check_password(hash_val, test_pwd):
            print(f"  ✅ CORRECT PASSWORD: '{test_pwd}'")
            break
    else:
        print("  ❌ No matching password found in common list")

cur.close()
conn.close()