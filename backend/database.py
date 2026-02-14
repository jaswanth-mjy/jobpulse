"""
MongoDB Atlas Database Module for JobPulse
Replaces SQLite with MongoDB for cloud deployment.
"""

import os
import ssl
import certifi
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

MONGODB_URI = os.environ.get(
    "MONGODB_URI",
    "mongodb+srv://admin:admin@cluster0.mongodb.net/jobpulse?retryWrites=true&w=majority"
)

_client = None
_db = None


def get_client():
    """Get (or create) the singleton MongoClient."""
    global _client
    if _client is None:
        # Build a custom SSL context to handle macOS + Atlas TLS issues
        import ssl as _ssl
        ctx = _ssl.create_default_context(cafile=certifi.where())
        ctx.check_hostname = True
        ctx.verify_mode = _ssl.CERT_REQUIRED

        _client = MongoClient(
            MONGODB_URI,
            tls=True,
            tlsCAFile=certifi.where(),
            server_api=None,
            serverSelectionTimeoutMS=10000,  # Reduced for faster failure
            connectTimeoutMS=10000,
            socketTimeoutMS=30000,
        )
    return _client


def get_db():
    """Get the jobpulse database."""
    global _db
    if _db is None:
        _db = get_client()["jobpulse"]
    return _db


def init_db():
    """Ensure collections and indexes exist."""
    db = get_db()

    # Users collection
    db.users.create_index("email", unique=True)

    # Applications collection — compound index for fast per-user queries
    db.applications.create_index([("user_id", 1), ("applied_date", -1)])
    db.applications.create_index([("user_id", 1), ("company", 1), ("role", 1), ("applied_date", 1)])

    # Gmail config collection
    db.gmail_config.create_index("user_id")

    # Reports collection — index by user and application
    db.reports.create_index([("user_id", 1), ("reported_date", -1)])
    db.reports.create_index("application_id")

    print("✅ MongoDB indexes ensured!")


def close_db():
    """Close the MongoClient."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None


if __name__ == "__main__":
    init_db()
    print("✅ MongoDB connected and initialized!")
