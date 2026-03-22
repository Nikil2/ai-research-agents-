#!/usr/bin/env python3
"""
Initialize database with a test user.
Run this ONCE to create the first user for testing.
"""

import sys
import os
from database.connection import get_connection
from main import pwd_context

def create_test_user():
    """Create a test user in the database."""
    
    email = "test@example.com"
    username = "testuser"
    password = "password123"
    
    # Hash the password
    password_hash = pwd_context.hash(password)
    
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            existing = cursor.fetchone()
            
            if existing:
                print(f"✓ User already exists: {email}")
                print(f"  User ID: {existing['id']}")
                conn.close()
                return
            
            # Create new user
            cursor.execute("""
                INSERT INTO users (email, username, password_hash, is_active)
                VALUES (%s, %s, %s, true)
                RETURNING id, email, username, is_active, created_at;
            """, (email, username, password_hash))
            
            new_user = cursor.fetchone()
            conn.commit()
            
            print("✅ Test user created successfully!")
            print(f"   Email:    {new_user['email']}")
            print(f"   Username: {new_user['username']}")
            print(f"   Password: {password}")
            print(f"   User ID:  {new_user['id']}")
            print(f"   Active:   {new_user['is_active']}")
            print(f"   Created:  {new_user['created_at']}")
            
            conn.close()
            return new_user
            
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE USER INITIALIZATION")
    print("=" * 60)
    print()
    create_test_user()
