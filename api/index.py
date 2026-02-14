# Vercel Serverless Function Entry Point
# This file adapts the Flask app to work with Vercel's serverless architecture

import sys
import os

# Add backend directory to Python path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Import Flask app
from app import app

# Vercel expects the app to be named 'app' or exposed via a handler
# No modifications needed - the app is already configured correctly
