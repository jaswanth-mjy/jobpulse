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
        msg["Subject"] = f"Verify Your JobPulse Account"
        msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg["To"] = to_email
        msg["Reply-To"] = "noreply@jobpulse.app"
        
        # Create HTML and text versions
        greeting = f"Hello {user_name}," if user_name else "Hello,"
        
        text_content = f"""
{greeting}

Thank you for signing up with JobPulse - Your Job Application Tracker!

To verify your email address and activate your account, please enter this verification code:

{verification_code}

This code will expire in 10 minutes for security purposes.

If you didn't create a JobPulse account, please disregard this email.

Best regards,
The JobPulse Team

---
JobPulse - Track Your Career Journey
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
        }}
        .email-wrapper {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
        }}
        .email-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px 30px;
            text-align: center;
        }}
        .logo {{
            width: 80px;
            height: 80px;
            margin: 0 auto 20px;
            background: #ffffff;
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 48px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .email-header h1 {{
            margin: 0;
            color: #ffffff;
            font-size: 28px;
            font-weight: 600;
        }}
        .email-header p {{
            margin: 10px 0 0 0;
            color: rgba(255,255,255,0.9);
            font-size: 16px;
        }}
        .email-body {{
            padding: 40px 30px;
        }}
        .greeting {{
            font-size: 18px;
            color: #333;
            margin-bottom: 20px;
        }}
        .message {{
            font-size: 15px;
            color: #555;
            line-height: 1.8;
            margin-bottom: 30px;
        }}
        .code-container {{
            background: #f8f9fa;
            border: 2px solid #667eea;
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            margin: 30px 0;
        }}
        .code-label {{
            font-size: 14px;
            color: #666;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }}
        .verification-code {{
            font-size: 42px;
            font-weight: bold;
            color: #667eea;
            letter-spacing: 12px;
            font-family: 'Courier New', monospace;
            margin: 0;
            padding: 10px;
        }}
        .expiry-notice {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 25px 0;
            border-radius: 4px;
            font-size: 14px;
            color: #856404;
        }}
        .security-notice {{
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 15px;
            margin: 25px 0;
            border-radius: 4px;
            font-size: 14px;
            color: #0c5087;
        }}
        .email-footer {{
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #e5e5e5;
        }}
        .footer-brand {{
            font-size: 18px;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 10px;
        }}
        .footer-tagline {{
            font-size: 13px;
            color: #999;
            margin-bottom: 15px;
        }}
        .footer-text {{
            font-size: 12px;
            color: #999;
            line-height: 1.5;
        }}
        .social-links {{
            margin: 20px 0;
        }}
        .social-links a {{
            display: inline-block;
            margin: 0 10px;
            color: #667eea;
            text-decoration: none;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="email-wrapper">
        <!-- Header with Logo -->
        <div class="email-header">
            <div class="logo">🎯</div>
            <h1>JobPulse</h1>
            <p>Your Job Application Tracker</p>
        </div>
        
        <!-- Body -->
        <div class="email-body">
            <div class="greeting">{greeting}</div>
            
            <div class="message">
                Thank you for choosing JobPulse to manage your job search journey. We're excited to have you on board!
            </div>
            
            <div class="message">
                To verify your email address and activate your account, please use the verification code below:
            </div>
            
            <!-- Verification Code -->
            <div class="code-container">
                <div class="code-label">Your Verification Code</div>
                <div class="verification-code">{verification_code}</div>
            </div>
            
            <!-- Expiry Notice -->
            <div class="expiry-notice">
                <strong>⏱️ Time Sensitive:</strong> This verification code will expire in <strong>10 minutes</strong> for your security.
            </div>
            
            <!-- Security Notice -->
            <div class="security-notice">
                <strong>🔒 Security Note:</strong> If you didn't create a JobPulse account, please disregard this email. Your information is safe.
            </div>
            
            <div class="message" style="margin-top: 30px;">
                Once verified, you'll be able to:
                <ul style="margin: 15px 0; padding-left: 20px;">
                    <li>Track all your job applications in one organized dashboard</li>
                    <li>Automatically import applications from Gmail</li>
                    <li>Get insights and analytics on your job search</li>
                    <li>Never miss a follow-up or deadline</li>
                </ul>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="email-footer">
            <div class="footer-brand">JobPulse</div>
            <div class="footer-tagline">Track Your Career Journey</div>
            <div class="footer-text">
                This is an automated message. Please do not reply to this email.<br>
                © 2026 JobPulse. All rights reserved.
            </div>
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
        msg["Reply-To"] = "noreply@jobpulse.app"
        
        greeting = f"Hello {user_name}," if user_name else "Hello,"
        
        text_content = f"""
{greeting}

Welcome to JobPulse! Your email has been verified successfully.

You can now:
• Track all your job applications in one organized dashboard
• Connect Gmail to automatically import applications
• Get insights and analytics on your job search progress
• Set reminders and never miss a follow-up

Start tracking your applications and land your dream job!

Best regards,
The JobPulse Team

---
JobPulse - Track Your Career Journey
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f4f4f4;
        }}
        .email-wrapper {{
            max-width: 600px;
            margin: 0 auto;
            background-color: #ffffff;
        }}
        .email-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 50px 30px;
            text-align: center;
        }}
        .logo {{
            width: 80px;
            height: 80px;
            margin: 0 auto 20px;
            background: #ffffff;
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 48px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .welcome-message {{
            color: #ffffff;
            margin: 0;
        }}
        .welcome-message h1 {{
            margin: 0 0 10px 0;
            font-size: 32px;
            font-weight: 600;
        }}
        .welcome-message p {{
            margin: 0;
            font-size: 16px;
            opacity: 0.95;
        }}
        .email-body {{
            padding: 40px 30px;
        }}
        .greeting {{
            font-size: 18px;
            color: #333;
            margin-bottom: 20px;
        }}
        .message {{
            font-size: 15px;
            color: #555;
            line-height: 1.8;
            margin-bottom: 30px;
        }}
        .features {{
            margin: 30px 0;
        }}
        .feature {{
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .feature-icon {{
            display: inline-block;
            width: 40px;
            font-size: 24px;
            vertical-align: middle;
        }}
        .feature-content {{
            display: inline-block;
            vertical-align: middle;
            width: calc(100% - 50px);
        }}
        .feature-title {{
            font-size: 16px;
            font-weight: 600;
            color: #333;
            margin: 0 0 5px 0;
        }}
        .feature-desc {{
            font-size: 14px;
            color: #666;
            margin: 0;
        }}
        .cta-button {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff;
            padding: 15px 40px;
            text-decoration: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            margin: 20px 0;
            text-align: center;
        }}
        .email-footer {{
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            border-top: 1px solid #e5e5e5;
        }}
        .footer-brand {{
            font-size: 18px;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 10px;
        }}
        .footer-tagline {{
            font-size: 13px;
            color: #999;
            margin-bottom: 15px;
        }}
        .footer-text {{
            font-size: 12px;
            color: #999;
            line-height: 1.5;
        }}
    </style>
</head>
<body>
    <div class="email-wrapper">
        <!-- Header -->
        <div class="email-header">
            <div class="logo">🎯</div>
            <div class="welcome-message">
                <h1>Welcome to JobPulse!</h1>
                <p>Your account is ready to use ✓</p>
            </div>
        </div>
        
        <!-- Body -->
        <div class="email-body">
            <div class="greeting">{greeting}</div>
            
            <div class="message">
                We're thrilled to have you join JobPulse! Your email has been verified and your account is now fully activated.
            </div>
            
            <div class="message">
                JobPulse is designed to help you stay organized and focused throughout your job search journey. Here's what you can do:
            </div>
            
            <!-- Features -->
            <div class="features">
                <div class="feature">
                    <span class="feature-icon">📊</span>
                    <div class="feature-content">
                        <div class="feature-title">Track Applications</div>
                        <div class="feature-desc">Keep all your job applications organized in one centralized dashboard with status tracking</div>
                    </div>
                </div>
                
                <div class="feature">
                    <span class="feature-icon">📧</span>
                    <div class="feature-content">
                        <div class="feature-title">Gmail Integration</div>
                        <div class="feature-desc">Automatically import and track applications from your Gmail inbox</div>
                    </div>
                </div>
                
                <div class="feature">
                    <span class="feature-icon">📈</span>
                    <div class="feature-content">
                        <div class="feature-title">Analytics & Insights</div>
                        <div class="feature-desc">Visualize your progress, identify trends, and optimize your job search strategy</div>
                    </div>
                </div>
                
                <div class="feature">
                    <span class="feature-icon">⏰</span>
                    <div class="feature-content">
                        <div class="feature-title">Reminders & Follow-ups</div>
                        <div class="feature-desc">Never miss an important deadline or follow-up opportunity</div>
                    </div>
                </div>
            </div>
            
            <div style="text-align: center; margin: 40px 0;">
                <div class="message" style="margin-bottom: 20px;">
                    <strong>Ready to supercharge your job search?</strong>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div class="email-footer">
            <div class="footer-brand">JobPulse</div>
            <div class="footer-tagline">Track Your Career Journey</div>
            <div class="footer-text">
                This is an automated message. Please do not reply to this email.<br>
                © 2026 JobPulse. All rights reserved.
            </div>
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
