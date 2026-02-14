#!/usr/bin/env python3
"""
Vercel Deployment Validator
Checks all requirements before deploying to Vercel
"""

import os
import sys
import json
import re
from pathlib import Path

# Color codes
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

def print_header(msg):
    print(f"\n{BLUE}{'='*60}{NC}")
    print(f"{BLUE}{msg}{NC}")
    print(f"{BLUE}{'='*60}{NC}\n")

def print_success(msg):
    print(f"{GREEN}✓ {msg}{NC}")

def print_error(msg):
    print(f"{RED}✗ {msg}{NC}")

def print_warning(msg):
    print(f"{YELLOW}⚠ {msg}{NC}")

def check_file_exists(filepath, description):
    """Check if a required file exists"""
    if Path(filepath).exists():
        print_success(f"{description} found: {filepath}")
        return True
    else:
        print_error(f"{description} missing: {filepath}")
        return False

def check_env_vars():
    """Check required environment variables"""
    print_header("Checking Environment Variables")
    
    required_vars = [
        'MONGODB_URI',
        'JWT_SECRET',
        'ENCRYPTION_KEY',
        'GOOGLE_OAUTH_CLIENT_ID',
        'GOOGLE_OAUTH_CLIENT_SECRET',
        'SMTP_USER',
        'SMTP_PASSWORD',
    ]
    
    # Check .env file
    env_file = Path('.env')
    if not env_file.exists():
        print_warning(".env file not found - using environment variables")
        print_warning("Recommended: Create .env file from .env.example")
        return False
    
    print_success(".env file found")
    
    # Parse .env file
    with open('.env', 'r') as f:
        env_content = f.read()
    
    missing_vars = []
    for var in required_vars:
        pattern = f"{var}=(.+)"
        match = re.search(pattern, env_content)
        if match and match.group(1).strip() and not match.group(1).startswith('your-'):
            print_success(f"{var} is set")
        else:
            missing_vars.append(var)
            print_error(f"{var} is not set or using placeholder")
    
    return len(missing_vars) == 0

def check_vercel_config():
    """Validate vercel.json configuration"""
    print_header("Checking Vercel Configuration")
    
    if not check_file_exists('vercel.json', 'Vercel config'):
        return False
    
    try:
        with open('vercel.json', 'r') as f:
            config = json.load(f)
        
        # Check builds
        if 'builds' in config:
            print_success(f"Found {len(config['builds'])} build configurations")
            
            # Check for api/index.py
            api_build = next((b for b in config['builds'] if 'api/index.py' in b.get('src', '')), None)
            if api_build:
                print_success("API entry point configured: api/index.py")
            else:
                print_warning("API entry point might be misconfigured")
        
        # Check routes
        if 'routes' in config:
            print_success(f"Found {len(config['routes'])} route configurations")
        
        # Check environment variables
        if 'env' in config:
            env_secrets = [k for k in config['env'].keys()]
            print_success(f"Found {len(env_secrets)} environment variables")
            for secret in env_secrets:
                if config['env'][secret].startswith('@'):
                    print_success(f"  - {secret}: {config['env'][secret]}")
                else:
                    print_warning(f"  - {secret}: Not using Vercel secret")
        
        return True
        
    except json.JSONDecodeError as e:
        print_error(f"vercel.json is not valid JSON: {e}")
        return False

def check_api_entry():
    """Check if api/index.py exists and is valid"""
    print_header("Checking API Entry Point")
    
    if not check_file_exists('api/index.py', 'API entry point'):
        return False
    
    try:
        with open('api/index.py', 'r') as f:
            content = f.read()
        
        if 'from app import app' in content:
            print_success("Flask app import found")
        else:
            print_warning("Flask app import might be missing")
        
        return True
    except Exception as e:
        print_error(f"Error reading api/index.py: {e}")
        return False

def check_requirements():
    """Check requirements.txt"""
    print_header("Checking Python Dependencies")
    
    if not check_file_exists('requirements.txt', 'Requirements file'):
        return False
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.readlines()
        
        required_packages = ['Flask', 'pymongo', 'gunicorn', 'PyJWT', 'bcrypt', 'cryptography']
        found_packages = []
        
        for line in requirements:
            line = line.strip()
            if line and not line.startswith('#'):
                package = line.split('==')[0].split('>=')[0].split('~=')[0]
                if any(req.lower() in package.lower() for req in required_packages):
                    found_packages.append(package)
        
        print_success(f"Found {len(found_packages)} required packages")
        for pkg in found_packages:
            print_success(f"  - {pkg}")
        
        missing = [r for r in required_packages if not any(r.lower() in f.lower() for f in found_packages)]
        if missing:
            for pkg in missing:
                print_warning(f"  - {pkg} might be missing")
        
        return True
        
    except Exception as e:
        print_error(f"Error reading requirements.txt: {e}")
        return False

def check_gitignore():
    """Check .gitignore configuration"""
    print_header("Checking .gitignore")
    
    if not Path('.gitignore').exists():
        print_warning(".gitignore not found")
        return False
    
    with open('.gitignore', 'r') as f:
        gitignore = f.read()
    
    important_entries = ['.env', '__pycache__', '*.pyc', '.vercel', 'venv', 'node_modules']
    
    for entry in important_entries:
        if entry in gitignore:
            print_success(f"{entry} is ignored")
        else:
            print_warning(f"{entry} should be in .gitignore")
    
    return True

def check_frontend_files():
    """Check frontend structure"""
    print_header("Checking Frontend Files")
    
    required_files = [
        ('frontend/index.html', 'Main HTML'),
        ('frontend/js/app.js', 'Main JavaScript'),
        ('frontend/css/styles.css', 'Main CSS'),
    ]
    
    all_exist = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_exist = False
    
    return all_exist

def check_backend_files():
    """Check backend structure"""
    print_header("Checking Backend Files")
    
    required_files = [
        ('backend/app.py', 'Flask application'),
        ('backend/database.py', 'Database module'),
        ('backend/email_parser.py', 'Email parser'),
        ('backend/gmail_service.py', 'Gmail service'),
    ]
    
    all_exist = True
    for filepath, description in required_files:
        if not check_file_exists(filepath, description):
            all_exist = False
    
    return all_exist

def main():
    """Run all validation checks"""
    print_header("Vercel Deployment Validation")
    
    checks = [
        ("Environment Variables", check_env_vars),
        ("Vercel Configuration", check_vercel_config),
        ("API Entry Point", check_api_entry),
        ("Python Dependencies", check_requirements),
        (".gitignore", check_gitignore),
        ("Frontend Files", check_frontend_files),
        ("Backend Files", check_backend_files),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Error during {name} check: {e}")
            results.append((name, False))
    
    # Summary
    print_header("Validation Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        if result:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")
    
    print(f"\n{BLUE}Overall: {passed}/{total} checks passed{NC}\n")
    
    if passed == total:
        print_success("✓ Ready for Vercel deployment!")
        print_success("\nNext steps:")
        print(f"  1. Run: {YELLOW}./setup-vercel.sh{NC} (first time)")
        print(f"  2. Or run: {YELLOW}vercel --prod{NC} (direct deploy)")
        return 0
    else:
        print_error("✗ Some checks failed. Please fix the issues above.")
        print_warning("\nCommon fixes:")
        print("  1. Create .env from .env.example and fill in values")
        print("  2. Ensure all required files exist")
        print("  3. Check vercel.json configuration")
        return 1

if __name__ == '__main__':
    sys.exit(main())
