"""
JobPulse — Backend API (MongoDB Atlas + JWT Auth)
"""

from flask import Flask, request, jsonify, g, send_from_directory
from flask_cors import CORS
from database import get_db, init_db
from datetime import datetime, date, timedelta
from bson import ObjectId
from functools import wraps
import traceback
import bcrypt
import jwt
import json
import os
import threading
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import random

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Resolve frontend folder (sibling of backend/)
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")

# Import email sender
try:
    from email_sender import send_verification_email, send_welcome_email
    EMAIL_ENABLED = True
except ImportError as e:
    print(f"⚠️  Email sending disabled: {e}")
    EMAIL_ENABLED = False
    def send_verification_email(*args, **kwargs): return False
    def send_welcome_email(*args, **kwargs): return False

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")
CORS(app, supports_credentials=True)

JWT_SECRET = os.environ.get("JWT_SECRET", "jobpulse-secret-change-me-in-production")
JWT_EXPIRY_HOURS = 72
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")

# ---- Encryption for sensitive data (Gmail app passwords) ----
ENCRYPTION_KEY = os.environ.get("ENCRYPTION_KEY", "")
if ENCRYPTION_KEY:
    _fernet = Fernet(ENCRYPTION_KEY.encode())
else:
    _fernet = Fernet(Fernet.generate_key())  # fallback — not persistent across restarts
    print("⚠️  No ENCRYPTION_KEY in .env — generated a temporary one. App passwords won't survive restarts.")


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string and return base64-encoded ciphertext."""
    return _fernet.encrypt(plaintext.encode("utf-8")).decode("utf-8")


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a base64-encoded ciphertext back to plaintext."""
    return _fernet.decrypt(ciphertext.encode("utf-8")).decode("utf-8")

# ---------- PLATFORMS ----------
PLATFORMS = [
    "LinkedIn", "Naukri", "Glassdoor", "Indeed", "AngelList",
    "Wellfound", "Instahyre", "Internshala", "Monster",
    "CareerBuilder", "ZipRecruiter", "Hired",
    "Workday", "Greenhouse", "Lever", "iCIMS", "SmartRecruiters",
    "Taleo", "BrassRing", "SuccessFactors", "Workable", "Ashby",
    "BambooHR", "Jobvite", "Phenom", "Eightfold",
    "Company Website", "Referral", "Other"
]

STATUSES = [
    "Applied", "Viewed", "In Review", "Assessment", "Phone Screen",
    "Interview Scheduled", "Interviewed", "Technical Round",
    "HR Round", "Offer Received", "Accepted", "Rejected", "Withdrawn", "Ghosted"
]


# ============================================================
#  HELPERS
# ============================================================

def mongo_to_dict(doc):
    """Convert a MongoDB document to a JSON-safe dict."""
    if not doc:
        return None
    doc["id"] = str(doc.pop("_id"))
    if "user_id" in doc:
        doc["user_id"] = str(doc["user_id"])
    return doc


def require_auth(f):
    """Decorator — require valid JWT in Authorization header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]

        if not token:
            return jsonify({"error": "Authentication required"}), 401

        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            g.user_id = payload["user_id"]
            g.user_email = payload.get("email", "")
            g.verified = payload.get("verified", False)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired. Please sign in again."}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated


def require_verified_email(f):
    """Decorator — require verified email (use after @require_auth)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.get("verified", False):
            return jsonify({"error": "Email verification required"}), 403
        return f(*args, **kwargs)
    return decorated


# ============================================================
#  AUTH ROUTES
# ============================================================

@app.route("/api/auth/signup", methods=["POST"])
def signup():
    data = request.get_json()
    name = data.get("name", "").strip()
    email_addr = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not name or not email_addr or not password:
        return jsonify({"error": "Name, email, and password are required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    db = get_db()

    # Check if user exists
    if db.users.find_one({"email": email_addr}):
        return jsonify({"error": "An account with this email already exists"}), 409

    # Hash password
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    user = {
        "name": name,
        "email": email_addr,
        "password": hashed.decode("utf-8"),
        "created_at": datetime.utcnow().isoformat(),
        "email_verified": False,
    }
    result = db.users.insert_one(user)
    user_id = str(result.inserted_id)
    
    # Generate 6-digit verification code
    verification_code = "{:06d}".format(random.randint(0, 999999))
    verification_expiry = datetime.utcnow() + timedelta(minutes=10)
    
    # Store verification code in database
    db.email_verifications.update_one(
        {"user_id": ObjectId(user_id)},
        {
            "$set": {
                "user_id": ObjectId(user_id),
                "code": verification_code,
                "email": email_addr,
                "expires_at": verification_expiry,
                "verified": False,
                "created_at": datetime.utcnow(),
            }
        },
        upsert=True
    )
    
    # Send verification email
    email_sent = send_verification_email(email_addr, verification_code, name)
    
    if not email_sent:
        print(f"⚠️  Failed to send verification email to {email_addr}")

    # Generate temporary token (will be upgraded after verification)
    temp_token = jwt.encode({
        "user_id": user_id,
        "email": email_addr,
        "verified": False,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
    }, JWT_SECRET, algorithm="HS256")

    return jsonify({
        "message": "Account created! Please verify your email.",
        "token": temp_token,
        "user": {"id": user_id, "name": name, "email": email_addr, "email_verified": False},
        "pending_verification": True,
        "email_sent": email_sent,
    }), 201


@app.route("/api/auth/signin", methods=["POST"])
def signin():
    data = request.get_json()
    email_addr = data.get("email", "").strip().lower()
    password = data.get("password", "").strip()

    if not email_addr or not password:
        return jsonify({"error": "Email and password are required"}), 400

    db = get_db()
    user = db.users.find_one({"email": email_addr})

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401
    
    # Handle password encoding - might be string or bytes in database
    stored_password = user["password"]
    if isinstance(stored_password, str):
        stored_password = stored_password.encode("utf-8")
    
    if not bcrypt.checkpw(password.encode("utf-8"), stored_password):
        return jsonify({"error": "Invalid email or password"}), 401

    user_id = str(user["_id"])
    
    # Check if email is already verified
    # For backward compatibility: if field doesn't exist, consider it a legacy user and mark as verified
    email_already_verified = user.get("email_verified", None)
    
    if email_already_verified is None:
        # Legacy user without email_verified field - auto-verify them
        update_fields = {
            "email_verified": True, 
            "email_verified_at": datetime.utcnow()
        }
        # Also ensure created_at exists for legacy users
        if not user.get("created_at"):
            update_fields["created_at"] = datetime.utcnow().isoformat()
        
        db.users.update_one(
            {"_id": user["_id"]},
            {"$set": update_fields}
        )
        email_already_verified = True
    elif not user.get("created_at"):
        # Ensure created_at exists for verified users
        db.users.update_one(
            {"_id": user["_id"]},
            {"$set": {"created_at": datetime.utcnow().isoformat()}}
        )
    
    if email_already_verified:
        # User already verified - direct login
        token = jwt.encode({
            "user_id": user_id,
            "email": email_addr,
            "verified": True,
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
        }, JWT_SECRET, algorithm="HS256")

        return jsonify({
            "message": "Signed in successfully",
            "token": token,
            "user": {"id": user_id, "name": user["name"], "email": email_addr, "email_verified": True},
            "pending_verification": False,
        })
    
    # Email not verified - send verification code
    verification_code = "{:06d}".format(random.randint(0, 999999))
    verification_expiry = datetime.utcnow() + timedelta(minutes=10)
    
    # Store verification code in database
    db.email_verifications.update_one(
        {"user_id": ObjectId(user_id)},
        {
            "$set": {
                "user_id": ObjectId(user_id),
                "code": verification_code,
                "email": email_addr,
                "expires_at": verification_expiry,
                "verified": False,
                "created_at": datetime.utcnow(),
            }
        },
        upsert=True
    )
    
    # Send verification email
    email_sent = send_verification_email(email_addr, verification_code, user.get("name", ""))
    
    if not email_sent:
        # If email fails, still allow login but warn user
        print(f"⚠️  Failed to send verification email to {email_addr}")
    
    # Generate temporary token (will be upgraded after verification)
    temp_token = jwt.encode({
        "user_id": user_id,
        "email": email_addr,
        "verified": False,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
    }, JWT_SECRET, algorithm="HS256")

    return jsonify({
        "message": "Verification code sent to your email",
        "token": temp_token,
        "user": {"id": user_id, "name": user["name"], "email": email_addr, "email_verified": False},
        "pending_verification": True,
        "email_sent": email_sent,
    })


@app.route("/api/auth/google", methods=["POST"])
def google_auth():
    """Sign in (or sign up) using Google OAuth 2.0 authorization code."""
    import requests as http_requests

    data = request.get_json()
    code = data.get("code", "")
    redirect_uri = data.get("redirect_uri", "")

    if not code:
        return jsonify({"error": "Authorization code is required"}), 400

    if not GOOGLE_CLIENT_ID:
        return jsonify({"error": "Google sign-in is not configured on the server."}), 500

    # Get client secret from environment
    GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    if not GOOGLE_CLIENT_SECRET:
        return jsonify({"error": "Google client secret not configured"}), 500

    try:
        # Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        
        token_response = http_requests.post(token_url, data=token_data)
        if token_response.status_code != 200:
            return jsonify({"error": "Failed to exchange authorization code"}), 400
        
        token_json = token_response.json()
        access_token = token_json.get("access_token")
        
        # Get user info using access token
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        userinfo_response = http_requests.get(userinfo_url, headers=headers)
        
        if userinfo_response.status_code != 200:
            return jsonify({"error": "Failed to get user info from Google"}), 400
        
        idinfo = userinfo_response.json()

        google_email = idinfo["email"].lower()
        google_name = idinfo.get("name", google_email.split("@")[0])
        google_picture = idinfo.get("picture", "")

        db = get_db()
        user = db.users.find_one({"email": google_email})

        if user:
            # Existing user — sign in
            user_id = str(user["_id"])
            name = user["name"]
            
            # Ensure email_verified is set for Google users (backward compatibility)
            if not user.get("email_verified"):
                db.users.update_one(
                    {"_id": user["_id"]},
                    {"$set": {
                        "email_verified": True, 
                        "email_verified_at": datetime.utcnow(),
                        "auth_provider": "google"
                    }}
                )
            
            # Ensure created_at exists (backward compatibility)
            if not user.get("created_at"):
                db.users.update_one(
                    {"_id": user["_id"]},
                    {"$set": {"created_at": datetime.utcnow().isoformat()}}
                )
        else:
            # New user — create account (no password needed for Google users)
            new_user = {
                "name": google_name,
                "email": google_email,
                "password": "",  # Google users don't have a local password
                "auth_provider": "google",
                "picture": google_picture,
                "email_verified": True,  # Google has already verified the email
                "email_verified_at": datetime.utcnow(),
                "created_at": datetime.utcnow().isoformat(),
            }
            result = db.users.insert_one(new_user)
            user_id = str(result.inserted_id)
            name = google_name

        token = jwt.encode({
            "user_id": user_id,
            "email": google_email,
            "verified": True,  # Google users are always verified
            "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
        }, JWT_SECRET, algorithm="HS256")

        # Check Gmail connection + auto-scan
        gmail_connected = db.gmail_config.count_documents({"user_id": ObjectId(user_id)}) > 0
        if gmail_connected:
            _trigger_background_scan(user_id)

        return jsonify({
            "message": "Signed in with Google!",
            "token": token,
            "user": {"id": user_id, "name": name, "email": google_email, "email_verified": True},
            "gmail_connected": gmail_connected,
            "auto_scan": gmail_connected,
        })

    except ValueError as e:
        return jsonify({"error": f"Invalid Google token: {str(e)}"}), 401
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Google sign-in failed: {str(e)}"}), 500


@app.route("/api/auth/me", methods=["GET"])
@require_auth
def auth_me():
    db = get_db()
    user = db.users.find_one({"_id": ObjectId(g.user_id)})
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Convert datetime objects to ISO strings
    created_at = user.get("created_at", "")
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()
    
    email_verified_at = user.get("email_verified_at", "")
    if isinstance(email_verified_at, datetime):
        email_verified_at = email_verified_at.isoformat()
    
    return jsonify({
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "email_verified": user.get("email_verified", False),
            "created_at": created_at,
            "email_verified_at": email_verified_at,
        }
    })


@app.route("/api/auth/verify-email", methods=["POST"])
@require_auth
def verify_email():
    """Verify email with code sent during signin"""
    data = request.get_json()
    code = data.get("code", "").strip()
    
    if not code:
        return jsonify({"error": "Verification code is required"}), 400
    
    db = get_db()
    user_id = ObjectId(g.user_id)
    
    # Find verification record
    verification = db.email_verifications.find_one({"user_id": user_id})
    
    if not verification:
        return jsonify({"error": "No verification code found. Please request a new one."}), 404
    
    # Check if already verified
    if verification.get("verified"):
        return jsonify({"message": "Email already verified", "verified": True})
    
    # Check expiry
    if datetime.utcnow() > verification["expires_at"]:
        return jsonify({"error": "Verification code has expired. Please request a new one."}), 400
    
    # Verify code
    if verification["code"] != code:
        return jsonify({"error": "Invalid verification code"}), 400
    
    # Mark as verified
    db.email_verifications.update_one(
        {"user_id": user_id},
        {"$set": {"verified": True, "verified_at": datetime.utcnow()}}
    )
    
    # Update user record
    db.users.update_one(
        {"_id": user_id},
        {"$set": {"email_verified": True, "email_verified_at": datetime.utcnow()}}
    )
    
    # Generate new token with verified status
    user = db.users.find_one({"_id": user_id})
    new_token = jwt.encode({
        "user_id": str(user_id),
        "email": user["email"],
        "verified": True,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
    }, JWT_SECRET, algorithm="HS256")
    
    # Send welcome email (optional)
    send_welcome_email(user["email"], user.get("name", ""))
    
    # Check if user has Gmail connected for auto-scan
    gmail_connected = db.gmail_config.count_documents({"user_id": user_id}) > 0
    if gmail_connected:
        _trigger_background_scan(str(user_id))
    
    return jsonify({
        "message": "Email verified successfully!",
        "verified": True,
        "token": new_token,
        "gmail_connected": gmail_connected,
        "auto_scan": gmail_connected,
    })


@app.route("/api/auth/resend-verification", methods=["POST"])
@require_auth
def resend_verification():
    """Resend verification code"""
    db = get_db()
    user_id = ObjectId(g.user_id)
    user = db.users.find_one({"_id": user_id})
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    # Check if already verified
    verification = db.email_verifications.find_one({"user_id": user_id})
    if verification and verification.get("verified"):
        return jsonify({"error": "Email already verified"}), 400
    
    # Generate new code
    verification_code = "{:06d}".format(random.randint(0, 999999))
    verification_expiry = datetime.utcnow() + timedelta(minutes=10)
    
    # Update verification record
    db.email_verifications.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "code": verification_code,
                "expires_at": verification_expiry,
                "created_at": datetime.utcnow(),
            }
        },
        upsert=True
    )
    
    # Send email
    email_sent = send_verification_email(user["email"], verification_code, user.get("name", ""))
    
    if not email_sent:
        return jsonify({"error": "Failed to send verification email. Please try again later."}), 500
    
    return jsonify({
        "message": "Verification code sent to your email",
        "email_sent": True,
    })


@app.route("/api/auth/forgot-password", methods=["POST"])
def forgot_password():
    """Request a password reset code via email"""
    from email_sender import send_password_reset_email
    
    data = request.get_json()
    email_addr = data.get("email", "").strip().lower()
    
    if not email_addr:
        return jsonify({"error": "Email is required"}), 400
    
    db = get_db()
    user = db.users.find_one({"email": email_addr})
    
    # Always return success (don't reveal if email exists)
    if not user:
        return jsonify({
            "message": "If that email is registered, you'll receive a password reset code shortly.",
            "email_sent": True
        })
    
    # Generate 6-digit reset code
    reset_code = "{:06d}".format(random.randint(0, 999999))
    reset_expiry = datetime.utcnow() + timedelta(minutes=10)
    
    # Store reset code in database
    db.password_resets.update_one(
        {"user_id": user["_id"]},
        {
            "$set": {
                "code": reset_code,
                "expires_at": reset_expiry,
                "created_at": datetime.utcnow(),
                "used": False
            }
        },
        upsert=True
    )
    
    # Send reset email
    email_sent = send_password_reset_email(email_addr, reset_code, user.get("name", ""))
    
    return jsonify({
        "message": "If that email is registered, you'll receive a password reset code shortly.",
        "email_sent": email_sent
    })


@app.route("/api/auth/reset-password", methods=["POST"])
def reset_password():
    """Reset password with code from email"""
    data = request.get_json()
    email_addr = data.get("email", "").strip().lower()
    code = data.get("code", "").strip()
    new_password = data.get("new_password", "").strip()
    
    if not email_addr or not code or not new_password:
        return jsonify({"error": "Email, code, and new password are required"}), 400
    
    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    
    db = get_db()
    user = db.users.find_one({"email": email_addr})
    
    if not user:
        return jsonify({"error": "Invalid email or reset code"}), 400
    
    # Find reset record
    reset_record = db.password_resets.find_one({"user_id": user["_id"]})
    
    if not reset_record:
        return jsonify({"error": "No password reset request found"}), 404
    
    # Check if already used
    if reset_record.get("used"):
        return jsonify({"error": "This reset code has already been used"}), 400
    
    # Check expiry
    if datetime.utcnow() > reset_record["expires_at"]:
        return jsonify({"error": "Reset code has expired. Please request a new one."}), 400
    
    # Verify code
    if reset_record["code"] != code:
        return jsonify({"error": "Invalid reset code"}), 400
    
    # Update password
    hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
    db.users.update_one(
        {"_id": user["_id"]},
        {"$set": {"password": hashed_password}}
    )
    
    # Mark reset code as used
    db.password_resets.update_one(
        {"user_id": user["_id"]},
        {"$set": {"used": True, "used_at": datetime.utcnow()}}
    )
    
    return jsonify({
        "message": "Password reset successfully! You can now sign in with your new password.",
        "success": True
    })


@app.route("/api/auth/delete-account", methods=["DELETE"])
@require_auth
def delete_account():
    """Permanently delete user account and all associated data"""
    db = get_db()
    user_id = ObjectId(g.user_id)
    
    try:
        # Delete all user data
        db.applications.delete_many({"user_id": user_id})
        db.gmail_config.delete_many({"user_id": user_id})
        db.email_verifications.delete_many({"user_id": user_id})
        db.password_resets.delete_many({"user_id": user_id})
        
        # Finally delete the user
        result = db.users.delete_one({"_id": user_id})
        
        if result.deleted_count == 0:
            return jsonify({"error": "User not found"}), 404
        
        return jsonify({
            "message": "Account deleted successfully",
            "success": True
        })
    except Exception as e:
        print(f"Error deleting account: {e}")
        return jsonify({"error": "Failed to delete account"}), 500


# ============================================================
#  METADATA
# ============================================================

@app.route("/api/platforms", methods=["GET"])
def get_platforms():
    return jsonify(PLATFORMS)


@app.route("/api/statuses", methods=["GET"])
def get_statuses():
    return jsonify(STATUSES)


# ============================================================
#  APPLICATIONS — CRUD (all require auth)
# ============================================================

@app.route("/api/applications", methods=["POST"])
@require_auth
def create_application():
    data = request.get_json()

    required = ["company", "role", "platform"]
    for field in required:
        if not data.get(field):
            return jsonify({"error": f"'{field}' is required"}), 400

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    applied = data.get("applied_date", date.today().isoformat())
    initial_status = data.get("status", "Applied")

    doc = {
        "user_id": ObjectId(g.user_id),
        "company": data["company"],
        "role": data["role"],
        "platform": data["platform"],
        "status": initial_status,
        "salary": data.get("salary", ""),
        "location": data.get("location", ""),
        "job_url": data.get("job_url", ""),
        "notes": data.get("notes", ""),
        "applied_date": applied,
        "updated_date": now,
        "interview_date": data.get("interview_date", ""),
        "response_date": data.get("response_date", ""),
        "status_history": [{"status": initial_status, "date": now, "source": "manual"}],
    }

    db = get_db()
    result = db.applications.insert_one(doc)
    return jsonify({"message": "Application added!", "id": str(result.inserted_id)}), 201


@app.route("/api/applications", methods=["GET"])
@require_auth
@require_verified_email
def get_applications():
    db = get_db()

    platform = request.args.get("platform")
    status = request.args.get("status")
    search = request.args.get("search")
    sort_by = request.args.get("sort_by", "applied_date")
    order = request.args.get("order", "desc")
    
    # Pagination parameters
    limit = request.args.get("limit", type=int)
    offset = request.args.get("offset", 0, type=int)

    query = {"user_id": ObjectId(g.user_id)}

    if platform:
        query["platform"] = platform
    if status:
        query["status"] = status
    if search:
        query["$or"] = [
            {"company": {"$regex": search, "$options": "i"}},
            {"role": {"$regex": search, "$options": "i"}},
            {"location": {"$regex": search, "$options": "i"}},
        ]

    allowed_sort = ["applied_date", "updated_date", "company", "role", "status", "platform"]
    if sort_by not in allowed_sort:
        sort_by = "applied_date"
    sort_dir = -1 if order.lower() == "desc" else 1

    # Get total count for pagination metadata
    total_count = db.applications.count_documents(query)
    
    cursor = db.applications.find(query).sort(sort_by, sort_dir)
    
    # Apply pagination if limit is specified
    if limit:
        cursor = cursor.skip(offset).limit(limit)
        applications = [mongo_to_dict(doc) for doc in cursor]
        return jsonify({
            "applications": applications,
            "total": total_count,
            "offset": offset,
            "limit": limit,
            "has_more": offset + limit < total_count
        })
    else:
        # Legacy support - return all applications without pagination
        return jsonify([mongo_to_dict(doc) for doc in cursor])


@app.route("/api/applications/<app_id>", methods=["GET"])
@require_auth
@require_verified_email
def get_application(app_id):
    db = get_db()
    doc = db.applications.find_one({"_id": ObjectId(app_id), "user_id": ObjectId(g.user_id)})
    if not doc:
        return jsonify({"error": "Application not found"}), 404
    return jsonify(mongo_to_dict(doc))


@app.route("/api/applications/<app_id>", methods=["PUT"])
@require_auth
@require_verified_email
def update_application(app_id):
    data = request.get_json()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

    db = get_db()
    existing = db.applications.find_one({"_id": ObjectId(app_id), "user_id": ObjectId(g.user_id)})
    if not existing:
        return jsonify({"error": "Application not found"}), 404

    update_fields = {"updated_date": now}
    
    # Track status changes
    if "status" in data and data["status"] != existing.get("status"):
        status_history = existing.get("status_history", [])
        status_history.append({
            "status": data["status"],
            "date": now,
            "source": "manual"
        })
        update_fields["status_history"] = status_history
    
    for field in ["company", "role", "platform", "status", "salary", "location",
                   "job_url", "notes", "applied_date", "interview_date", "response_date"]:
        if data.get(field) is not None:
            update_fields[field] = data[field]

    db.applications.update_one({"_id": ObjectId(app_id)}, {"$set": update_fields})
    return jsonify({"message": "Application updated!"})


@app.route("/api/applications/<app_id>", methods=["DELETE"])
@require_auth
@require_verified_email
def delete_application(app_id):
    db = get_db()
    result = db.applications.delete_one({"_id": ObjectId(app_id), "user_id": ObjectId(g.user_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Application not found"}), 404
    return jsonify({"message": "Application deleted!"})


@app.route("/api/applications/clear/all", methods=["DELETE"])
@require_auth
@require_verified_email
def clear_all_applications():
    """Delete all applications for the current user."""
    db = get_db()
    result = db.applications.delete_many({"user_id": ObjectId(g.user_id)})
    return jsonify({
        "message": f"Deleted {result.deleted_count} applications",
        "deleted_count": result.deleted_count
    })


@app.route("/api/applications/export", methods=["GET"])
@require_auth
@require_verified_email
def export_applications():
    """Export all applications for the current user as JSON or CSV."""
    db = get_db()
    format_type = request.args.get("format", "json").lower()
    
    # Fetch all applications
    applications = list(db.applications.find({"user_id": ObjectId(g.user_id)}).sort("applied_date", -1))
    
    if not applications:
        return jsonify({"error": "No applications to export"}), 404
    
    if format_type == "csv":
        import csv
        from io import StringIO
        
        output = StringIO()
        fieldnames = ["company", "role", "platform", "status", "salary", "location", 
                      "job_url", "notes", "applied_date", "interview_date", "response_date"]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for app in applications:
            row = {
                "company": app.get("company", ""),
                "role": app.get("role", ""),
                "platform": app.get("platform", ""),
                "status": app.get("status", ""),
                "salary": app.get("salary", ""),
                "location": app.get("location", ""),
                "job_url": app.get("job_url", ""),
                "notes": app.get("notes", ""),
                "applied_date": app.get("applied_date", ""),
                "interview_date": app.get("interview_date", ""),
                "response_date": app.get("response_date", ""),
            }
            writer.writerow(row)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename=jobpulse_export_{date.today().isoformat()}.csv"}
        )
    else:
        # JSON export
        export_data = []
        for app in applications:
            export_data.append({
                "company": app.get("company", ""),
                "role": app.get("role", ""),
                "platform": app.get("platform", ""),
                "status": app.get("status", ""),
                "salary": app.get("salary", ""),
                "location": app.get("location", ""),
                "job_url": app.get("job_url", ""),
                "notes": app.get("notes", ""),
                "applied_date": app.get("applied_date", ""),
                "interview_date": app.get("interview_date", ""),
                "response_date": app.get("response_date", ""),
                "status_history": app.get("status_history", []),
            })
        
        from flask import Response
        return Response(
            json.dumps({"applications": export_data, "exported_at": datetime.utcnow().isoformat(), "count": len(export_data)}, indent=2),
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment; filename=jobpulse_export_{date.today().isoformat()}.json"}
        )


@app.route("/api/applications/import", methods=["POST"])
@require_auth
@require_verified_email
def import_applications():
    """Import applications from JSON or CSV file."""
    db = get_db()
    
    # Handle JSON data
    if request.is_json:
        data = request.get_json()
        applications = data.get("applications", [])
        
        if not isinstance(applications, list):
            applications = [data]  # Single application object
    else:
        # Handle file upload (CSV or JSON)
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400
        
        file_content = file.read().decode("utf-8")
        
        if file.filename.endswith(".json"):
            file_data = json.loads(file_content)
            applications = file_data.get("applications", file_data if isinstance(file_data, list) else [file_data])
        elif file.filename.endswith(".csv"):
            import csv
            from io import StringIO
            
            csv_reader = csv.DictReader(StringIO(file_content))
            applications = list(csv_reader)
        else:
            return jsonify({"error": "Unsupported file format. Use JSON or CSV."}), 400
    
    if not applications:
        return jsonify({"error": "No applications found in import data"}), 400
    
    # Validate and import
    imported = 0
    updated = 0
    skipped = 0
    errors = []
    
    for idx, app_data in enumerate(applications):
        try:
            # Validate required fields
            if not app_data.get("company") or not app_data.get("role"):
                errors.append(f"Row {idx + 1}: Missing company or role")
                skipped += 1
                continue
            
            # Check for duplicates
            existing = db.applications.find_one({
                "user_id": ObjectId(g.user_id),
                "company": app_data["company"],
                "role": app_data["role"],
                "applied_date": app_data.get("applied_date", ""),
            })
            
            if existing:
                # Update existing if status is different
                if app_data.get("status") and app_data["status"] != existing.get("status"):
                    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    status_history = existing.get("status_history", [])
                    status_history.append({
                        "status": app_data["status"],
                        "date": now,
                        "source": "import"
                    })
                    
                    update_fields = {
                        "status": app_data["status"],
                        "updated_date": now,
                        "status_history": status_history,
                    }
                    
                    # Update other fields if provided
                    for field in ["platform", "salary", "location", "job_url", "notes", "interview_date", "response_date"]:
                        if app_data.get(field):
                            update_fields[field] = app_data[field]
                    
                    db.applications.update_one({"_id": existing["_id"]}, {"$set": update_fields})
                    updated += 1
                else:
                    skipped += 1
            else:
                # Import as new application
                now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                initial_status = app_data.get("status", "Applied")
                
                new_doc = {
                    "user_id": ObjectId(g.user_id),
                    "company": app_data["company"],
                    "role": app_data["role"],
                    "platform": app_data.get("platform", "Other"),
                    "status": initial_status,
                    "salary": app_data.get("salary", ""),
                    "location": app_data.get("location", ""),
                    "job_url": app_data.get("job_url", ""),
                    "notes": app_data.get("notes", ""),
                    "applied_date": app_data.get("applied_date", date.today().isoformat()),
                    "updated_date": now,
                    "interview_date": app_data.get("interview_date", ""),
                    "response_date": app_data.get("response_date", ""),
                    "status_history": app_data.get("status_history", [{"status": initial_status, "date": now, "source": "import"}]),
                }
                
                db.applications.insert_one(new_doc)
                imported += 1
                
        except Exception as e:
            errors.append(f"Row {idx + 1}: {str(e)}")
            skipped += 1
    
    return jsonify({
        "message": f"Import complete: {imported} new, {updated} updated, {skipped} skipped",
        "imported": imported,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
    })


# ============================================================
#  STATS
# ============================================================

@app.route("/api/stats", methods=["GET"])
@require_auth
@require_verified_email
def get_stats():
    db = get_db()
    user_filter = {"user_id": ObjectId(g.user_id)}

    total = db.applications.count_documents(user_filter)

    # Group by status
    pipeline_status = [
        {"$match": user_filter},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}},
    ]
    by_status = {doc["_id"]: doc["count"] for doc in db.applications.aggregate(pipeline_status)}

    # Group by platform
    pipeline_platform = [
        {"$match": user_filter},
        {"$group": {"_id": "$platform", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    by_platform = {doc["_id"]: doc["count"] for doc in db.applications.aggregate(pipeline_platform)}

    # Response rate
    responded = (
        by_status.get("Rejected", 0) + by_status.get("Interview Scheduled", 0) +
        by_status.get("Interviewed", 0) + by_status.get("Offer Received", 0) +
        by_status.get("Accepted", 0) + by_status.get("Phone Screen", 0) +
        by_status.get("Technical Round", 0) + by_status.get("HR Round", 0) +
        by_status.get("Assessment", 0)
    )
    response_rate = round((responded / total * 100), 1) if total > 0 else 0

    return jsonify({
        "total": total,
        "by_status": by_status,
        "by_platform": by_platform,
        "weekly": {},
        "response_rate": response_rate,
    })


# ============================================================
#  GMAIL INTEGRATION
# ============================================================

@app.route("/api/gmail/accounts", methods=["GET"])
@require_auth
@require_verified_email
def gmail_accounts():
    try:
        db = get_db()
        accounts = list(db.gmail_config.find({"user_id": ObjectId(g.user_id)}))
        result = []
        for acct in accounts:
            result.append({
                "id": str(acct["_id"]),
                "email": acct["email"],
                "auth_type": acct.get("auth_type", "app_password"),  # Default for legacy accounts
            })
        return jsonify({"accounts": result})
    except Exception as e:
        return jsonify({"accounts": [], "error": str(e)})


@app.route("/api/gmail/accounts", methods=["POST"])
@require_auth
@require_verified_email
def gmail_add_account():
    try:
        from gmail_service import test_connection

        data = request.get_json()
        email_addr = data.get("email", "").strip()
        app_password = data.get("app_password", "").strip()

        if not email_addr or not app_password:
            return jsonify({"error": "Email and App Password are required."}), 400

        success, message = test_connection(email_addr, app_password)
        if not success:
            return jsonify({"error": message}), 401

        db = get_db()
        # Check if already added
        existing = db.gmail_config.find_one({
            "user_id": ObjectId(g.user_id),
            "email": email_addr
        })
        if existing:
            return jsonify({"error": "This Gmail account is already connected."}), 409

        doc = {
            "user_id": ObjectId(g.user_id),
            "email": email_addr,
            "app_password": encrypt_value(app_password),  # encrypted!
        }
        db.gmail_config.insert_one(doc)
        return jsonify({"message": f"{email_addr} connected successfully!", "account": {"email": email_addr}})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/gmail/accounts/<account_id>", methods=["DELETE"])
@require_auth
@require_verified_email
def gmail_remove_account(account_id):
    db = get_db()
    result = db.gmail_config.delete_one({"_id": ObjectId(account_id), "user_id": ObjectId(g.user_id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Account not found."}), 404
    return jsonify({"message": "Account removed."})


@app.route("/api/gmail/status", methods=["GET"])
@require_auth
@require_verified_email
def gmail_status():
    db = get_db()
    accounts = list(db.gmail_config.find({"user_id": ObjectId(g.user_id)}))
    result = [{"id": str(a["_id"]), "email": a["email"]} for a in accounts]
    return jsonify({
        "is_authenticated": len(result) > 0,
        "email": result[0]["email"] if result else "",
        "accounts": result,
    })


@app.route("/api/gmail/scan", methods=["POST"])
@require_auth
@require_verified_email
def gmail_scan():
    try:
        from gmail_service import scan_emails_for_account
        from gmail_oauth import scan_emails_oauth

        db = get_db()
        accounts = list(db.gmail_config.find({"user_id": ObjectId(g.user_id)}))

        if not accounts:
            return jsonify({"error": "No Gmail accounts connected. Please connect first."}), 401

        data = request.get_json() or {}
        days_back = data.get("days_back", 90)
        max_results = data.get("max_results", 500)

        all_applications = []
        for acct in accounts:
            try:
                auth_type = acct.get("auth_type", "app_password")
                
                if auth_type == "oauth":
                    # Use OAuth credentials
                    encrypted_creds = acct.get("oauth_credentials", "")
                    if not encrypted_creds:
                        print(f"No OAuth credentials for {acct['email']}")
                        continue
                    
                    try:
                        creds_json = decrypt_value(encrypted_creds)
                        creds_dict = json.loads(creds_json)
                    except Exception as e:
                        print(f"Failed to decrypt OAuth credentials: {e}")
                        continue
                    
                    apps, updated_creds = scan_emails_oauth(creds_dict, days_back, max_results)
                    
                    # Update stored credentials if refreshed
                    if updated_creds:
                        db.gmail_config.update_one(
                            {"_id": acct["_id"]},
                            {"$set": {"oauth_credentials": encrypt_value(json.dumps(updated_creds))}}
                        )
                    
                    all_applications.extend(apps)
                else:
                    # Use App Password (IMAP)
                    raw_password = acct.get("app_password", "")
                    if not raw_password:
                        print(f"No app password for {acct['email']}")
                        continue
                    
                    try:
                        decrypted_pw = decrypt_value(raw_password)
                    except Exception:
                        decrypted_pw = raw_password  # fallback for legacy unencrypted entries

                    apps = scan_emails_for_account(acct["email"], decrypted_pw,
                                                    days_back=days_back, max_results=max_results)
                    all_applications.extend(apps)
                    
            except Exception as e:
                print(f"Error scanning {acct['email']}: {e}")
                traceback.print_exc()

        if not all_applications:
            return jsonify({
                "message": "No new job application emails found.",
                "imported": 0, "found": 0, "skipped": 0, "updated": 0,
                "applications": []
            })

        imported = 0
        skipped = 0
        updated = 0
        imported_apps = []
        user_oid = ObjectId(g.user_id)

        for app_data in all_applications:
            email_type = app_data.get("email_type", "applied")

            if email_type in ("rejected", "interview", "assessment"):
                # Try to find existing application by company name (most recent one)
                existing = db.applications.find_one(
                    {"user_id": user_oid, "company": {"$regex": f"^{app_data['company']}$", "$options": "i"}},
                    sort=[("applied_date", -1)]
                )
                if existing:
                    old_status = existing["status"]
                    new_status = app_data["status"]
                    
                    # Always update if status is different, prioritizing negative outcomes
                    should_update = False
                    if old_status != new_status:
                        should_update = True
                    elif email_type == "rejected" and old_status != "Rejected":
                        # Force update to Rejected even if status field matches
                        should_update = True
                    
                    if should_update:
                        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                        
                        # Build status history entry
                        status_history = existing.get("status_history", [])
                        status_history.append({
                            "status": new_status,
                            "date": now,
                            "source": "gmail_scan"
                        })
                        
                        update_set = {
                            "status": new_status, 
                            "updated_date": now,
                            "status_history": status_history
                        }
                        
                        if email_type == "rejected":
                            update_set["response_date"] = app_data.get("applied_date", now)
                        if email_type in ("interview", "assessment"):
                            update_set["interview_date"] = app_data.get("applied_date", now)
                        
                        # Add debug logging
                        print(f"🔄 Updating {existing['company']} from '{old_status}' to '{new_status}'")
                        
                        db.applications.update_one(
                            {"_id": existing["_id"]},
                            {"$set": update_set}
                        )
                        updated += 1
                        app_data["id"] = str(existing["_id"])
                        app_data["_action"] = "updated"
                        app_data["old_status"] = old_status
                        app_data["new_status"] = new_status
                        imported_apps.append(app_data)
                    else:
                        print(f"⏭️  Skipping {app_data['company']} - already {old_status}")
                        skipped += 1
                else:
                    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                    initial_status = app_data.get("status", "Applied")
                    new_doc = {
                        "user_id": user_oid,
                        "company": app_data["company"],
                        "role": app_data["role"],
                        "platform": app_data["platform"],
                        "status": initial_status,
                        "salary": app_data.get("salary", ""),
                        "location": app_data.get("location", ""),
                        "job_url": app_data.get("job_url", ""),
                        "notes": app_data.get("notes", ""),
                        "applied_date": app_data["applied_date"],
                        "updated_date": now,
                        "interview_date": app_data["applied_date"] if email_type == "interview" else "",
                        "response_date": app_data["applied_date"] if email_type == "rejected" else "",
                        "status_history": [{"status": initial_status, "date": now, "source": "gmail_scan"}],
                    }
                    result = db.applications.insert_one(new_doc)
                    imported += 1
                    app_data["id"] = str(result.inserted_id)
                    app_data["_action"] = "new"
                    imported_apps.append(app_data)
            else:
                existing = db.applications.find_one({
                    "user_id": user_oid,
                    "company": app_data["company"],
                    "role": app_data["role"],
                    "applied_date": app_data["applied_date"],
                })
                if existing:
                    skipped += 1
                    continue

                now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                initial_status = app_data.get("status", "Applied")
                new_doc = {
                    "user_id": user_oid,
                    "company": app_data["company"],
                    "role": app_data["role"],
                    "platform": app_data["platform"],
                    "status": initial_status,
                    "salary": app_data.get("salary", ""),
                    "location": app_data.get("location", ""),
                    "job_url": app_data.get("job_url", ""),
                    "notes": app_data.get("notes", ""),
                    "status_history": [{"status": initial_status, "date": now, "source": "gmail_scan"}],
                    "applied_date": app_data["applied_date"],
                    "updated_date": now,
                    "interview_date": "",
                    "response_date": "",
                }
                result = db.applications.insert_one(new_doc)
                imported += 1
                app_data["id"] = str(result.inserted_id)
                app_data["_action"] = "new"
                imported_apps.append(app_data)

        return jsonify({
            "message": f"Imported {imported} new, updated {updated} existing applications from Gmail!",
            "imported": imported,
            "updated": updated,
            "found": len(all_applications),
            "skipped": skipped,
            "applications": imported_apps,
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Scan failed: {str(e)}"}), 500


# ============================================================
#  BACKGROUND SCAN
# ============================================================

_scan_status = {}  # user_id -> {"status": "scanning"/"done"/"error", "result": {...}}


def _trigger_background_scan(user_id: str):
    """Run Gmail scan in a background thread after login."""
    def _do_scan():
        try:
            from gmail_service import scan_emails_for_account
            from gmail_oauth import scan_emails_oauth
            _scan_status[user_id] = {"status": "scanning", "result": None}

            db = get_db()
            accounts = list(db.gmail_config.find({"user_id": ObjectId(user_id)}))
            if not accounts:
                _scan_status[user_id] = {"status": "done", "result": {"imported": 0, "message": "No Gmail accounts"}}
                return

            all_applications = []
            for acct in accounts:
                try:
                    auth_type = acct.get("auth_type", "app_password")
                    
                    if auth_type == "oauth":
                        # Use OAuth credentials
                        encrypted_creds = acct.get("oauth_credentials", "")
                        if not encrypted_creds:
                            continue
                        try:
                            creds_json = decrypt_value(encrypted_creds)
                            creds_dict = json.loads(creds_json)
                        except Exception:
                            continue
                        
                        apps, updated_creds = scan_emails_oauth(creds_dict, days_back=30, max_results=200)
                        
                        # Update stored credentials if refreshed
                        if updated_creds:
                            db.gmail_config.update_one(
                                {"_id": acct["_id"]},
                                {"$set": {"oauth_credentials": encrypt_value(json.dumps(updated_creds))}}
                            )
                        
                        all_applications.extend(apps)
                    else:
                        # Use App Password (IMAP)
                        raw_pw = acct.get("app_password", "")
                        if not raw_pw:
                            continue
                        try:
                            pw = decrypt_value(raw_pw)
                        except Exception:
                            pw = raw_pw
                        apps = scan_emails_for_account(acct["email"], pw, days_back=30, max_results=200)
                        all_applications.extend(apps)
                        
                except Exception as e:
                    print(f"Background scan error for {acct['email']}: {e}")

            # Import results
            imported = 0
            updated = 0
            user_oid = ObjectId(user_id)
            for app_data in all_applications:
                email_type = app_data.get("email_type", "applied")
                if email_type in ("rejected", "interview", "assessment"):
                    existing = db.applications.find_one(
                        {"user_id": user_oid, "company": {"$regex": f"^{app_data['company']}$", "$options": "i"}},
                        sort=[("applied_date", -1)]
                    )
                    if existing:
                        old_status = existing["status"]
                        new_status = app_data["status"]
                        if old_status != new_status:
                            now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                            update_set = {"status": new_status, "updated_date": now}
                            if email_type == "rejected":
                                update_set["response_date"] = app_data["applied_date"]
                            if email_type in ("interview", "assessment"):
                                update_set["interview_date"] = app_data["applied_date"]
                            db.applications.update_one({"_id": existing["_id"]}, {"$set": update_set})
                            updated += 1
                    else:
                        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                        db.applications.insert_one({
                            "user_id": user_oid,
                            "company": app_data["company"], "role": app_data["role"],
                            "platform": app_data["platform"], "status": app_data.get("status", "Applied"),
                            "salary": "", "location": app_data.get("location", ""),
                            "job_url": "", "notes": "",
                            "applied_date": app_data["applied_date"], "updated_date": now,
                            "interview_date": app_data["applied_date"] if email_type == "interview" else "",
                            "response_date": app_data["applied_date"] if email_type == "rejected" else "",
                        })
                        imported += 1
                else:
                    existing = db.applications.find_one({
                        "user_id": user_oid,
                        "company": app_data["company"],
                        "role": app_data["role"],
                        "applied_date": app_data["applied_date"],
                    })
                    if not existing:
                        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
                        db.applications.insert_one({
                            "user_id": user_oid,
                            "company": app_data["company"], "role": app_data["role"],
                            "platform": app_data["platform"], "status": app_data.get("status", "Applied"),
                            "salary": "", "location": app_data.get("location", ""),
                            "job_url": "", "notes": "",
                            "applied_date": app_data["applied_date"], "updated_date": now,
                            "interview_date": "", "response_date": "",
                        })
                        imported += 1

            _scan_status[user_id] = {
                "status": "done",
                "result": {"imported": imported, "updated": updated, "found": len(all_applications)}
            }
            print(f"✅ Background scan done for user {user_id}: {imported} imported, {updated} updated")

        except Exception as e:
            print(f"❌ Background scan error: {e}")
            _scan_status[user_id] = {"status": "error", "result": {"error": str(e)}}

    thread = threading.Thread(target=_do_scan, daemon=True)
    thread.start()


@app.route("/api/scan/status", methods=["GET"])
@require_auth
@require_verified_email
def scan_status():
    """Check the status of a background scan triggered on login."""
    status = _scan_status.get(g.user_id, {"status": "idle", "result": None})
    return jsonify(status)


# ============================================================
#  GMAIL OAUTH 2.0 (No App Password Needed)
# ============================================================

@app.route("/api/gmail/oauth/status", methods=["GET"])
def gmail_oauth_status():
    """Check if OAuth is configured on the server."""
    try:
        from gmail_oauth import is_oauth_configured, get_redirect_uri
        return jsonify({
            "oauth_available": is_oauth_configured(),
            "redirect_uri": get_redirect_uri(),
            "message": "OAuth 2.0 is available" if is_oauth_configured() else "OAuth not configured on server"
        })
    except Exception as e:
        return jsonify({"oauth_available": False, "message": str(e)})


@app.route("/api/gmail/oauth/start", methods=["POST"])
@require_auth
@require_verified_email
def gmail_oauth_start():
    """Start the OAuth 2.0 flow - returns authorization URL."""
    try:
        from gmail_oauth import is_oauth_configured, get_authorization_url
        
        if not is_oauth_configured():
            return jsonify({"error": "OAuth is not configured on the server. Please use App Password method."}), 400
        
        # Use user_id as state for security
        state = f"{g.user_id}"
        auth_url, state = get_authorization_url(state)
        
        return jsonify({
            "authorization_url": auth_url,
            "state": state,
            "message": "Redirect user to authorization_url to complete OAuth flow"
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Failed to start OAuth: {str(e)}"}), 500


@app.route("/api/gmail/oauth/callback", methods=["GET"])
def gmail_oauth_callback():
    """OAuth callback - exchanges code for tokens."""
    try:
        from gmail_oauth import exchange_code_for_tokens, test_oauth_connection
        
        code = request.args.get("code")
        state = request.args.get("state")  # This is the user_id
        error = request.args.get("error")
        
        if error:
            # Redirect to frontend with error
            return f"""
            <html>
            <head><title>OAuth Error</title></head>
            <body>
                <h2>Authentication Failed</h2>
                <p>Error: {error}</p>
                <script>
                    window.opener?.postMessage({{ type: 'oauth_error', error: '{error}' }}, '*');
                    setTimeout(() => window.close(), 3000);
                </script>
            </body>
            </html>
            """
        
        if not code or not state:
            return jsonify({"error": "Missing authorization code or state"}), 400
        
        # Exchange code for tokens
        creds_dict = exchange_code_for_tokens(code, state)
        
        # Test connection and get email
        success, email_or_error, updated_creds = test_oauth_connection(creds_dict)
        
        if not success:
            return f"""
            <html>
            <head><title>OAuth Error</title></head>
            <body>
                <h2>Connection Failed</h2>
                <p>{email_or_error}</p>
                <script>
                    window.opener?.postMessage({{ type: 'oauth_error', error: '{email_or_error}' }}, '*');
                    setTimeout(() => window.close(), 3000);
                </script>
            </body>
            </html>
            """
        
        email_address = email_or_error
        final_creds = updated_creds or creds_dict
        
        # Store in database
        db = get_db()
        user_id = state  # state contains user_id
        
        # Check if already connected
        existing = db.gmail_config.find_one({
            "user_id": ObjectId(user_id),
            "email": email_address
        })
        
        if existing:
            # Update existing entry
            db.gmail_config.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "oauth_credentials": encrypt_value(json.dumps(final_creds)),
                    "auth_type": "oauth",
                    "app_password": "",  # Clear app password if exists
                }}
            )
        else:
            # Create new entry
            db.gmail_config.insert_one({
                "user_id": ObjectId(user_id),
                "email": email_address,
                "auth_type": "oauth",
                "oauth_credentials": encrypt_value(json.dumps(final_creds)),
                "app_password": "",
            })
        
        # Return success page that notifies opener window
        return f"""
        <html>
        <head>
            <title>Gmail Connected!</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                       display: flex; justify-content: center; align-items: center; height: 100vh;
                       background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0; }}
                .card {{ background: white; padding: 40px; border-radius: 16px; text-align: center;
                        box-shadow: 0 20px 60px rgba(0,0,0,0.3); max-width: 400px; }}
                h2 {{ color: #22c55e; margin-bottom: 10px; }}
                p {{ color: #666; }}
                .email {{ font-weight: bold; color: #333; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>✅ Gmail Connected!</h2>
                <p>Successfully connected <span class="email">{email_address}</span></p>
                <p>This window will close automatically...</p>
            </div>
            <script>
                window.opener?.postMessage({{ 
                    type: 'oauth_success', 
                    email: '{email_address}' 
                }}, '*');
                setTimeout(() => window.close(), 2000);
            </script>
        </body>
        </html>
        """
        
    except Exception as e:
        traceback.print_exc()
        error_msg = str(e).replace("'", "\\'")
        return f"""
        <html>
        <head><title>OAuth Error</title></head>
        <body>
            <h2>Authentication Error</h2>
            <p>{error_msg}</p>
            <script>
                window.opener?.postMessage({{ type: 'oauth_error', error: '{error_msg}' }}, '*');
                setTimeout(() => window.close(), 5000);
            </script>
        </body>
        </html>
        """


@app.route("/api/gmail/oauth/accounts", methods=["GET"])
@require_auth
@require_verified_email
def gmail_oauth_accounts():
    """List all connected Gmail accounts (both OAuth and App Password)."""
    try:
        db = get_db()
        accounts = list(db.gmail_config.find({"user_id": ObjectId(g.user_id)}))
        result = []
        for acct in accounts:
            result.append({
                "id": str(acct["_id"]),
                "email": acct["email"],
                "auth_type": acct.get("auth_type", "app_password"),  # Default to app_password for legacy
            })
        return jsonify({"accounts": result})
    except Exception as e:
        return jsonify({"accounts": [], "error": str(e)})


# ============================================================
#  HEALTH CHECK (for Render)
# ============================================================

@app.route("/health")
def health_check():
    """Health check endpoint for Render deployment."""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()}), 200


# ============================================================
#  SERVE FRONTEND
# ============================================================

@app.route("/")
def serve_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    """Serve frontend static files; fall back to index.html for SPA routes."""
    file_path = os.path.join(FRONTEND_DIR, path)
    if os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIR, path)
    return send_from_directory(FRONTEND_DIR, "index.html")


# ============================================================
#  START
# ============================================================

# ==================== LEGAL PAGES ====================
@app.route("/privacy-policy")
def privacy_policy():
    """Serve privacy policy page"""
    return send_from_directory(app.static_folder, "privacy-policy.html")

@app.route("/terms-of-service")
@app.route("/terms")
def terms_of_service():
    """Serve terms of service page"""
    return send_from_directory(app.static_folder, "terms-of-service.html")

# Initialize database on module load (for gunicorn)
try:
    init_db()
    print("✅ Database initialized successfully")
except Exception as e:
    print(f"⚠️ Database initialization deferred: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print(f"🚀 JobPulse API running on http://localhost:{port}")
    app.run(debug=True, host="0.0.0.0", port=port, use_reloader=False)
