# backend/change_password.py

import bcrypt
import psycopg2
from dotenv import load_dotenv
import os
from getpass import getpass

load_dotenv()

def hash_password(password):
    """Generate bcrypt hash for a password"""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, hashed):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def change_password(student_id, new_password):
    """Change password for a specific student"""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "utas_chatbot"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "password"),
        port=os.getenv("DB_PORT", "5432")
    )
    
    cur = conn.cursor()
    
    # Check if user exists
    cur.execute("SELECT student_id, name FROM students WHERE student_id = %s", (student_id,))
    user = cur.fetchone()
    
    if not user:
        print(f"❌ User '{student_id}' not found!")
        return False
    
    # Generate new hash
    new_hash = hash_password(new_password)
    
    # Update password
    cur.execute("UPDATE students SET password_hash = %s WHERE student_id = %s", (new_hash, student_id))
    conn.commit()
    
    print(f"✅ Password changed for {user[1]} ({student_id})")
    print(f"   New password: {new_password}")
    print(f"   New hash: {new_hash[:30]}...")
    
    cur.close()
    conn.close()
    return True

def create_new_user(student_id, name, email, department, password, is_admin=False):
    """Create a new user with encrypted password"""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "utas_chatbot"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "password"),
        port=os.getenv("DB_PORT", "5432")
    )
    
    cur = conn.cursor()
    
    # Check if user exists
    cur.execute("SELECT student_id FROM students WHERE student_id = %s", (student_id,))
    if cur.fetchone():
        print(f"❌ User '{student_id}' already exists!")
        return False
    
    # Generate hash
    password_hash = hash_password(password)
    
    # Insert new user
    cur.execute("""
        INSERT INTO students (student_id, name, email, department, password_hash, is_admin, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
    """, (student_id, name, email, department, password_hash, is_admin))
    
    conn.commit()
    print(f"✅ User created: {student_id} ({name})")
    print(f"   Password: {password}")
    print(f"   Hash: {password_hash[:30]}...")
    print(f"   Admin: {is_admin}")
    
    cur.close()
    conn.close()
    return True

def list_all_users():
    """List all users in the database"""
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "utas_chatbot"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "password"),
        port=os.getenv("DB_PORT", "5432")
    )
    
    cur = conn.cursor()
    cur.execute("SELECT student_id, name, email, is_admin FROM students ORDER BY student_id")
    users = cur.fetchall()
    
    print("\n" + "="*60)
    print("Current Users:")
    print("="*60)
    for user in users:
        role = "👑 ADMIN" if user[3] else "👤 STUDENT"
        print(f"{role} | {user[0]} | {user[1]} | {user[2]}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    print("="*60)
    print("Password Management Tool")
    print("="*60)
    
    while True:
        print("\nOptions:")
        print("1. Change password for existing user")
        print("2. Create new user")
        print("3. List all users")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            student_id = input("Enter Student ID: ").strip()
            new_password = getpass("Enter new password: ")
            confirm = getpass("Confirm password: ")
            
            if new_password == confirm:
                change_password(student_id, new_password)
            else:
                print("❌ Passwords do not match!")
        
        elif choice == "2":
            student_id = input("Enter Student ID: ").strip()
            name = input("Enter Full Name: ").strip()
            email = input("Enter Email: ").strip()
            department = input("Enter Department: ").strip()
            password = getpass("Enter Password: ")
            confirm = getpass("Confirm Password: ")
            is_admin = input("Is Admin? (y/n): ").strip().lower() == 'y'
            
            if password == confirm:
                create_new_user(student_id, name, email, department, password, is_admin)
            else:
                print("❌ Passwords do not match!")
        
        elif choice == "3":
            list_all_users()
        
        elif choice == "4":
            print("Goodbye!")
            break