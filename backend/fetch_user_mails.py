"""
Fetch User Mails from MongoDB Atlas
Run this script to retrieve all Gmail accounts connected by users.
"""

from database_mongo import get_db, init_db
from bson import ObjectId
import json


def fetch_all_user_mails():
    """Fetch all Gmail accounts from all users."""
    db = get_db()
    
    print("=" * 60)
    print("FETCHING USER MAILS FROM MONGODB ATLAS")
    print("=" * 60)
    
    # Fetch all gmail configurations
    gmail_configs = list(db.gmail_config.find({}))
    
    if not gmail_configs:
        print("\n❌ No Gmail accounts found in database.")
        return []
    
    print(f"\n✅ Found {len(gmail_configs)} Gmail account(s)\n")
    
    results = []
    for idx, config in enumerate(gmail_configs, 1):
        # Get user details
        user_id = config.get("user_id")
        user = None
        if user_id:
            user = db.users.find_one({"_id": ObjectId(user_id)})
        
        mail_info = {
            "index": idx,
            "config_id": str(config["_id"]),
            "user_id": str(user_id) if user_id else "N/A",
            "user_name": user.get("name") if user else "Unknown",
            "user_email": user.get("email") if user else "Unknown",
            "gmail_account": config.get("email", "N/A"),
            "has_app_password": bool(config.get("app_password"))
        }
        
        results.append(mail_info)
        
        print(f"[{idx}] Gmail Account Info:")
        print(f"    Config ID: {mail_info['config_id']}")
        print(f"    User ID: {mail_info['user_id']}")
        print(f"    User Name: {mail_info['user_name']}")
        print(f"    User Login Email: {mail_info['user_email']}")
        print(f"    Gmail Account: {mail_info['gmail_account']}")
        print(f"    Has App Password: {'✓' if mail_info['has_app_password'] else '✗'}")
        print()
    
    return results


def fetch_user_mails_by_user_id(user_id_str):
    """Fetch Gmail accounts for a specific user ID."""
    db = get_db()
    
    try:
        user_oid = ObjectId(user_id_str)
    except:
        print(f"❌ Invalid user ID format: {user_id_str}")
        return []
    
    print("=" * 60)
    print(f"FETCHING MAILS FOR USER ID: {user_id_str}")
    print("=" * 60)
    
    # Get user info
    user = db.users.find_one({"_id": user_oid})
    if not user:
        print(f"\n❌ User not found with ID: {user_id_str}")
        return []
    
    print(f"\nUser: {user.get('name')} ({user.get('email')})\n")
    
    # Fetch gmail configs for this user
    gmail_configs = list(db.gmail_config.find({"user_id": user_oid}))
    
    if not gmail_configs:
        print(f"❌ No Gmail accounts found for this user.")
        return []
    
    print(f"✅ Found {len(gmail_configs)} Gmail account(s)\n")
    
    results = []
    for idx, config in enumerate(gmail_configs, 1):
        mail_info = {
            "index": idx,
            "config_id": str(config["_id"]),
            "gmail_account": config.get("email", "N/A"),
            "has_app_password": bool(config.get("app_password"))
        }
        
        results.append(mail_info)
        
        print(f"[{idx}] {mail_info['gmail_account']}")
        print(f"    Config ID: {mail_info['config_id']}")
        print(f"    Has App Password: {'✓' if mail_info['has_app_password'] else '✗'}")
        print()
    
    return results


def fetch_user_mails_by_email(email_address):
    """Fetch Gmail accounts for a specific user by their login email."""
    db = get_db()
    
    print("=" * 60)
    print(f"FETCHING MAILS FOR USER EMAIL: {email_address}")
    print("=" * 60)
    
    # Get user by email
    user = db.users.find_one({"email": email_address.lower().strip()})
    if not user:
        print(f"\n❌ User not found with email: {email_address}")
        return []
    
    user_id = str(user["_id"])
    return fetch_user_mails_by_user_id(user_id)


def list_all_users():
    """List all registered users."""
    db = get_db()
    
    print("=" * 60)
    print("ALL REGISTERED USERS")
    print("=" * 60)
    
    users = list(db.users.find({}))
    
    if not users:
        print("\n❌ No users found in database.")
        return []
    
    print(f"\n✅ Found {len(users)} user(s)\n")
    
    for idx, user in enumerate(users, 1):
        print(f"[{idx}] {user.get('name')}")
        print(f"    User ID: {user['_id']}")
        print(f"    Email: {user.get('email')}")
        print(f"    Created: {user.get('created_at', 'N/A')}")
        print()
    
    return users


if __name__ == "__main__":
    import sys
    
    # Initialize database connection
    try:
        init_db()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list-users":
            list_all_users()
        
        elif command == "user-id" and len(sys.argv) > 2:
            user_id = sys.argv[2]
            fetch_user_mails_by_user_id(user_id)
        
        elif command == "user-email" and len(sys.argv) > 2:
            email = sys.argv[2]
            fetch_user_mails_by_email(email)
        
        else:
            print("❌ Invalid command or missing arguments")
            print("\nUsage:")
            print("  python fetch_user_mails.py                    # Fetch all mails")
            print("  python fetch_user_mails.py list-users         # List all users")
            print("  python fetch_user_mails.py user-id <ID>       # Fetch by user ID")
            print("  python fetch_user_mails.py user-email <EMAIL> # Fetch by user email")
    else:
        # Default: fetch all
        fetch_all_user_mails()
    
    print("=" * 60)
    print("✅ DONE")
    print("=" * 60)
