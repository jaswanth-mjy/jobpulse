#!/usr/bin/env python3
"""
Quick script to delete a user from the database for testing
Usage: python3 delete_user.py email@example.com
"""

import sys
from database import get_db
from bson import ObjectId

def delete_user(email):
    """Delete a user by email"""
    db = get_db()
    
    # Find user
    user = db.users.find_one({"email": email.lower()})
    if not user:
        print(f"❌ User not found: {email}")
        return False
    
    user_id = user["_id"]
    print(f"👤 Found user: {user.get('name')} ({email})")
    print(f"   Verified: {user.get('email_verified', False)}")
    print(f"   Created: {user.get('created_at', 'N/A')}")
    
    # Delete verification codes
    verification_result = db.email_verifications.delete_many({"user_id": user_id})
    print(f"🗑️  Deleted {verification_result.deleted_count} verification code(s)")
    
    # Delete Gmail OAuth tokens
    gmail_result = db.gmail_oauth_tokens.delete_many({"user_id": user_id})
    print(f"🗑️  Deleted {gmail_result.deleted_count} Gmail token(s)")
    
    # Delete applications
    apps_result = db.applications.delete_many({"user_id": user_id})
    print(f"🗑️  Deleted {apps_result.deleted_count} application(s)")
    
    # Delete user
    db.users.delete_one({"_id": user_id})
    print(f"✅ User deleted: {email}")
    
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 delete_user.py email@example.com")
        print("\nCurrent users:")
        db = get_db()
        users = list(db.users.find({}, {'email': 1, 'name': 1, 'email_verified': 1}))
        for user in users:
            verified = '✅' if user.get('email_verified') else '❌'
            print(f"  {verified} {user.get('email')} - {user.get('name')}")
        sys.exit(1)
    
    email = sys.argv[1]
    delete_user(email)
