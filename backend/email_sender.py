"""
Email Sender Utility for JobPulse
Handles sending verification emails and notifications
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

# Email configuration from environment variables
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")  # Your email address
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # App password or email password
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
FROM_NAME = os.getenv("FROM_NAME", "JobPulse")


def send_verification_email(to_email: str, verification_code: str, user_name: str = "") -> bool:
    """
    Send a verification email with a 6-digit code
    
    Args:
        to_email: Recipient email address
        verification_code: 6-digit verification code
        user_name: User's name for personalization
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        print("⚠️  Email sending disabled: SMTP credentials not configured in .env")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"JobPulse Email Verification - Code: {verification_code}"
        msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg["To"] = to_email
        
        # Create HTML and text versions
        greeting = f"Hi {user_name}," if user_name else "Hi,"
        
        text_content = f"""
{greeting}

Thank you for signing in to JobPulse!

To verify your email address, please enter this verification code:

{verification_code}

This code will expire in 10 minutes.

If you didn't attempt to sign in, please ignore this email.

Best regards,
The JobPulse Team
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .container {{
            background: #ffffff;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .logo {{
            font-size: 28px;
            font-weight: bold;
            color: #6366f1;
            margin-bottom: 10px;
        }}
        .code-box {{
            background: #f5f5f5;
            border: 2px dashed #6366f1;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            margin: 30px 0;
        }}
        .code {{
            font-size: 36px;
            font-weight: bold;
            color: #6366f1;
            letter-spacing: 8px;
            font-family: 'Courier New', monospace;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e5e5e5;
            font-size: 14px;
            color: #666;
        }}
        .warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 12px;
            margin: 20px 0;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🎯 JobPulse</div>
            <h2 style="margin: 0; color: #333;">Email Verification</h2>
        </div>
        
        <p>{greeting}</p>
        
        <p>Thank you for signing in to JobPulse! To complete the verification process, please use the code below:</p>
        
        <div class="code-box">
            <div style="font-size: 14px; color: #666; margin-bottom: 10px;">Your Verification Code</div>
            <div class="code">{verification_code}</div>
        </div>
        
        <div class="warning">
            ⏱️ This code will expire in <strong>10 minutes</strong>.
        </div>
        
        <p style="margin-top: 30px;">If you didn't attempt to sign in to JobPulse, please ignore this email or contact support if you're concerned about your account security.</p>
        
        <div class="footer">
            <p style="margin: 5px 0;"><strong>JobPulse</strong> - Your Job Application Tracker</p>
            <p style="margin: 5px 0; color: #999;">This is an automated email, please do not reply.</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Attach both versions
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Verification email sent to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send verification email: {e}")
        return False


def send_welcome_email(to_email: str, user_name: str = "") -> bool:
    """
    Send a welcome email after successful verification (optional)
    
    Args:
        to_email: Recipient email address
        user_name: User's name for personalization
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    if not SMTP_USER or not SMTP_PASSWORD:
        return False
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Welcome to JobPulse! 🎉"
        msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg["To"] = to_email
        
        greeting = f"Hi {user_name}," if user_name else "Hi,"
        
        text_content = f"""
{greeting}

Welcome to JobPulse! Your email has been verified successfully.

You can now:
• Track all your job applications in one place
• Connect Gmail to auto-import applications
• Get insights on your job search progress
• Set reminders for follow-ups

Start tracking your applications and land your dream job!

Best regards,
The JobPulse Team
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .container {{
            background: #ffffff;
            border-radius: 8px;
            padding: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .logo {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        .welcome {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            text-align: center;
            margin: 20px 0;
        }}
        .features {{
            margin: 30px 0;
        }}
        .feature {{
            padding: 15px;
            margin: 10px 0;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid #6366f1;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e5e5e5;
            font-size: 14px;
            color: #666;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🎯</div>
        </div>
        
        <div class="welcome">
            <h1 style="margin: 0; font-size: 28px;">Welcome to JobPulse!</h1>
            <p style="margin: 10px 0 0 0; opacity: 0.9;">Your email has been verified successfully ✓</p>
        </div>
        
        <p>{greeting}</p>
        
        <p>We're excited to have you on board! JobPulse helps you stay organized and focused during your job search.</p>
        
        <div class="features">
            <div class="feature">
                <strong>📊 Track Applications</strong><br>
                Keep all your job applications organized in one place
            </div>
            <div class="feature">
                <strong>📧 Gmail Integration</strong><br>
                Automatically import applications from your email
            </div>
            <div class="feature">
                <strong>📈 Get Insights</strong><br>
                Visualize your progress and identify trends
            </div>
            <div class="feature">
                <strong>⏰ Stay Updated</strong><br>
                Set reminders and never miss a follow-up
            </div>
        </div>
        
        <p style="text-align: center; margin-top: 30px;">
            <strong>Ready to get started? Start tracking your applications now!</strong>
        </p>
        
        <div class="footer">
            <p style="margin: 5px 0;"><strong>JobPulse</strong> - Your Job Application Tracker</p>
            <p style="margin: 5px 0; color: #999;">This is an automated email, please do not reply.</p>
        </div>
    </div>
</body>
</html>
"""
        
        part1 = MIMEText(text_content, "plain")
        part2 = MIMEText(html_content, "html")
        msg.attach(part1)
        msg.attach(part2)
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Welcome email sent to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send welcome email: {e}")
        return False
