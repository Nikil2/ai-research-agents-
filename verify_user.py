"""Script to verify existing user credentials in the database."""
import sys
from database.crud import get_user_by_email
from database.connection import get_connection
import bcrypt

def list_all_users():
    """List all users in database."""
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, email, username, is_active, created_at
                FROM users
                ORDER BY created_at DESC;
            """)
            users = cursor.fetchall()
            conn.close()
            
            if not users:
                print("❌ No users found in database")
                return None
                
            print("\n📋 EXISTING USERS:")
            print("=" * 80)
            for user in users:
                print(f"ID:       {user['id']}")
                print(f"Email:    {user['email']}")
                print(f"Username: {user['username']}")
                print(f"Active:   {user['is_active']}")
                print(f"Created:  {user['created_at']}")
                print("-" * 80)
            return users
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        return None

def verify_credentials(email, password):
    """Verify user email and password."""
    try:
        user = get_user_by_email(email)
        
        if not user:
            print(f"❌ User with email '{email}' not found")
            return False
            
        print(f"\n✓ User found: {user['username']}")
        
        # Verify password
        password_hash = user['password_hash']
        
        if bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
            print(f"✓ Password is CORRECT")
            print(f"✓ User ID: {user['id']}")
            return user
        else:
            print(f"❌ Password is INCORRECT")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying credentials: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("USER VERIFICATION TOOL")
    print("=" * 80)
    
    # List all users
    users = list_all_users()
    
    if users:
        print("\n" + "=" * 80)
        print("VERIFY CREDENTIALS")
        print("=" * 80)
        
        email = input("\nEnter email to verify: ").strip()
        password = input("Enter password: ").strip()
        
        verified_user = verify_credentials(email, password)
        
        if verified_user:
            print("\n✓ LOGIN SUCCESSFUL!")
            print(f"✓ User ID to use for jobs: {verified_user['id']}")
        else:
            print("\n❌ LOGIN FAILED - Invalid credentials")
