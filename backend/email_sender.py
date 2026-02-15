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
        # Don't add Reply-To - let replies go to the actual sender email
        
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
        # Don't add Reply-To - let replies go to the actual sender email
        
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


def send_password_reset_email(to_email: str, reset_code: str, user_name: str = "") -> bool:
    """
    Send a password reset email with a 6-digit code
    
    Args:
        to_email: Recipient email address
        reset_code: 6-digit reset code
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
        msg["Subject"] = f"Reset Your JobPulse Password"
        msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg["To"] = to_email
        
        # Create HTML and text versions
        greeting = f"Hello {user_name}," if user_name else "Hello,"
        
        text_content = f"""
{greeting}

We received a request to reset your JobPulse password.

Your password reset code is: {reset_code}

This code will expire in 10 minutes.

If you didn't request this password reset, please ignore this email or contact support if you have concerns.

Thanks,
The JobPulse Team
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; margin: 0; padding: 0; background-color: #f5f5f5; }}
        .container {{ max-width: 600px; margin: 40px auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center; }}
        .logo {{ font-size: 48px; margin-bottom: 10px; }}
        .header h1 {{ color: #ffffff; margin: 0; font-size: 28px; font-weight: 700; }}
        .content {{ padding: 40px 30px; }}
        .greeting {{ font-size: 18px; color: #333; margin-bottom: 20px; font-weight: 600; }}
        .message {{ color: #555; line-height: 1.6; margin-bottom: 30px; font-size: 16px; }}
        .code-box {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; padding: 30px; text-align: center; border-radius: 8px; margin: 30px 0; }}
        .code-label {{ font-size: 14px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; opacity: 0.9; }}
        .code {{ font-size: 42px; font-weight: 700; letter-spacing: 8px; font-family: 'Courier New', monospace; }}
        .warning {{ background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 4px; }}
        .warning-icon {{ color: #ffc107; font-size: 20px; margin-right: 10px; }}
        .warning-text {{ color: #856404; font-size: 14px; }}
        .expiry {{ text-align: center; color: #666; font-size: 13px; margin-top: 15px; font-style: italic; }}
        .footer {{ background-color: #f8f9fa; padding: 30px; text-align: center; color: #666; font-size: 14px; }}
        .footer-note {{ margin-top: 15px; font-size: 12px; color: #999; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="logo">🔐</div>
            <h1>Password Reset Request</h1>
        </div>
        
        <div class="content">
            <div class="greeting">{greeting}</div>
            
            <div class="message">
                We received a request to reset your JobPulse password. Use the code below to reset your password:
            </div>
            
            <div class="code-box">
                <div class="code-label">Your Reset Code</div>
                <div class="code">{reset_code}</div>
                <div class="expiry">⏰ Expires in 10 minutes</div>
            </div>
            
            <div class="message">
                Enter this code in the password reset form to create a new password.
            </div>
            
            <div class="warning">
                <span class="warning-icon">⚠️</span>
                <span class="warning-text"><strong>Didn't request this?</strong> If you didn't request a password reset, please ignore this email. Your password will remain unchanged.</span>
            </div>
        </div>
        
        <div class="footer">
            <strong>JobPulse</strong> - Smart Job Application Tracker
            <div class="footer-note">
                This is an automated message. For security reasons, this code will expire in 10 minutes.
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
        
        print(f"✅ Password reset email sent to {to_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send password reset email: {e}")
        return False


def send_bulk_announcement_email(recipients: list, subject: str, message: str, sender_name: str = "JobPulse Team", gmail_credentials: dict = None) -> dict:
    """
    Send a bulk announcement email to multiple recipients with modern styling
    
    Args:
        recipients: List of dicts with 'email' and optional 'name' keys
        subject: Email subject line
        message: Email message body (supports basic markdown-like formatting)
        sender_name: Name to show as sender
        gmail_credentials: Optional Gmail OAuth credentials dict for sending via Gmail API (HTTPS, not blocked)
        
    Returns:
        dict: {'success': int, 'failed': int, 'errors': list}
    """
    # Check if we have Gmail API credentials (preferred - HTTPS, not blocked on Render)
    use_gmail_api = gmail_credentials is not None
    
    if not use_gmail_api and (not SMTP_USER or not SMTP_PASSWORD):
        print("⚠️  Email sending disabled: No Gmail OAuth or SMTP credentials configured")
        return {'success': 0, 'failed': len(recipients), 'errors': ['No email sending method configured. Connect Gmail in admin or add SMTP credentials.']}
    
    # Import Gmail OAuth functions if using Gmail API
    if use_gmail_api:
        try:
            from gmail_oauth import credentials_from_dict, refresh_credentials_if_needed, send_email_via_gmail_api
            credentials, updated_creds = refresh_credentials_if_needed(gmail_credentials)
            print(f"✅ Using Gmail API for sending (HTTPS-based)")
        except Exception as e:
            print(f"❌ Failed to initialize Gmail API: {e}")
            return {'success': 0, 'failed': len(recipients), 'errors': [f'Gmail API init failed: {str(e)}']}
    
    results = {'success': 0, 'failed': 0, 'errors': []}
    
    for recipient in recipients:
        try:
            to_email = recipient.get('email', '')
            user_name = recipient.get('name', '')
            
            if not to_email:
                results['failed'] += 1
                results['errors'].append(f"Missing email for recipient")
                continue
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
            msg["To"] = to_email
            
            greeting = f"Hi {user_name}," if user_name else "Hi there,"
            
            # Convert markdown-like formatting to HTML
            html_message = message
            # Bold: **text** -> <strong>text</strong>
            import re
            html_message = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html_message)
            # Italic: *text* -> <em>text</em>
            html_message = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html_message)
            # Links: [text](url) -> <a href="url">text</a>
            html_message = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2" style="color: #6366f1; text-decoration: none; font-weight: 500;">\1</a>', html_message)
            # Bullet points: - item -> styled list
            lines = html_message.split('\n')
            formatted_lines = []
            in_list = False
            for line in lines:
                if line.strip().startswith('- '):
                    if not in_list:
                        formatted_lines.append('<ul style="margin: 15px 0; padding-left: 20px;">')
                        in_list = True
                    formatted_lines.append(f'<li style="margin: 8px 0; color: #374151;">{line.strip()[2:]}</li>')
                else:
                    if in_list:
                        formatted_lines.append('</ul>')
                        in_list = False
                    if line.strip():
                        formatted_lines.append(f'<p style="margin: 0 0 15px 0; color: #374151; line-height: 1.7;">{line}</p>')
                    else:
                        formatted_lines.append('<br>')
            if in_list:
                formatted_lines.append('</ul>')
            html_message = '\n'.join(formatted_lines)
            
            text_content = f"""
{greeting}

{message}

Best regards,
{sender_name}

---
JobPulse - Track Your Career Journey
https://jobpulse.app

To unsubscribe from future updates, reply to this email with "UNSUBSCRIBE" in the subject line.
"""
            
            html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <title>{subject}</title>
    <!--[if mso]>
    <noscript>
        <xml>
            <o:OfficeDocumentSettings>
                <o:PixelsPerInch>96</o:PixelsPerInch>
            </o:OfficeDocumentSettings>
        </xml>
    </noscript>
    <![endif]-->
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background-color: #f3f4f6; -webkit-font-smoothing: antialiased;">
    
    <!-- Preheader text (hidden but shows in email preview) -->
    <div style="display: none; max-height: 0; overflow: hidden;">
        {message[:100]}...
    </div>
    
    <!-- Main wrapper -->
    <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: #f3f4f6;">
        <tr>
            <td style="padding: 40px 20px;">
                
                <!-- Email container -->
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" style="margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);">
                    
                    <!-- Header with gradient -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%); padding: 40px 30px; text-align: center;">
                            <!-- Logo -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin: 0 auto;">
                                <tr>
                                    <td style="background-color: rgba(255,255,255,0.2); border-radius: 12px; padding: 12px 20px;">
                                        <span style="font-size: 28px; color: #ffffff; font-weight: 800; letter-spacing: -0.5px;">
                                            💼 JobPulse
                                        </span>
                                    </td>
                                </tr>
                            </table>
                            <!-- Tagline -->
                            <p style="color: rgba(255,255,255,0.9); font-size: 14px; margin: 15px 0 0 0; font-weight: 500;">
                                Smart Job Application Tracker
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Announcement badge -->
                    <tr>
                        <td style="padding: 30px 30px 0 30px; text-align: center;">
                            <span style="display: inline-block; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); color: #92400e; font-size: 12px; font-weight: 700; padding: 6px 16px; border-radius: 20px; text-transform: uppercase; letter-spacing: 0.5px;">
                                📢 Announcement
                            </span>
                        </td>
                    </tr>
                    
                    <!-- Body content -->
                    <tr>
                        <td style="padding: 30px 40px 40px 40px;">
                            <!-- Greeting -->
                            <h2 style="margin: 0 0 25px 0; color: #111827; font-size: 24px; font-weight: 700; line-height: 1.3;">
                                {greeting}
                            </h2>
                            
                            <!-- Message content -->
                            <div style="font-size: 16px; line-height: 1.7; color: #374151;">
                                {html_message}
                            </div>
                            
                            <!-- CTA Button -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin: 35px 0;">
                                <tr>
                                    <td style="border-radius: 10px; background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);">
                                        <a href="https://jobpulse.app" target="_blank" style="display: inline-block; padding: 16px 32px; color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px;">
                                            Open JobPulse →
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- Signature -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="border-top: 1px solid #e5e7eb; padding-top: 25px; margin-top: 30px; width: 100%;">
                                <tr>
                                    <td>
                                        <p style="margin: 0; color: #6b7280; font-size: 15px;">
                                            Best regards,<br>
                                            <strong style="color: #374151;">{sender_name}</strong>
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #1f2937; padding: 30px 40px; text-align: center;">
                            <!-- Social links placeholder -->
                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin: 0 auto 20px auto;">
                                <tr>
                                    <td style="padding: 0 8px;">
                                        <span style="color: #9ca3af; font-size: 20px;">🌐</span>
                                    </td>
                                    <td style="padding: 0 8px;">
                                        <span style="color: #9ca3af; font-size: 20px;">📧</span>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 0 0 15px 0; color: #9ca3af; font-size: 14px;">
                                <strong style="color: #ffffff;">JobPulse</strong> — Track every application, land more interviews
                            </p>
                            
                            <p style="margin: 0; color: #6b7280; font-size: 12px; line-height: 1.6;">
                                You're receiving this because you're a JobPulse user.<br>
                                <a href="mailto:shramkavach@gmail.com?subject=UNSUBSCRIBE" style="color: #6b7280; text-decoration: underline;">Unsubscribe</a> from future updates
                            </p>
                        </td>
                    </tr>
                    
                </table>
                
                <!-- Footer note -->
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="600" style="margin: 20px auto 0 auto;">
                    <tr>
                        <td style="text-align: center; color: #9ca3af; font-size: 11px;">
                            © 2026 JobPulse. Made with ❤️ for job seekers everywhere.
                        </td>
                    </tr>
                </table>
                
            </td>
        </tr>
    </table>
    
</body>
</html>
"""
            
            # Try Gmail API first (HTTPS-based, works on Render)
            if use_gmail_api:
                try:
                    if send_email_via_gmail_api(credentials, to_email, subject, html_content, text_content):
                        results['success'] += 1
                        continue
                    else:
                        # Gmail API failed, will try SMTP as fallback
                        print(f"⚠️  Gmail API failed for {to_email}, trying SMTP...")
                except Exception as gmail_err:
                    print(f"⚠️  Gmail API error for {to_email}: {gmail_err}, trying SMTP...")
            
            # Fall back to SMTP
            if not SMTP_USER or not SMTP_PASSWORD:
                results['failed'] += 1
                results['errors'].append(f"{to_email}: No SMTP fallback available")
                continue
                
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
            msg["To"] = to_email
            
            part1 = MIMEText(text_content, "plain")
            part2 = MIMEText(html_content, "html")
            msg.attach(part1)
            msg.attach(part2)
            
            # Add timeout to prevent infinite hanging (30 seconds)
            # Try TLS on port 587 first, fall back to SSL on 465
            try:
                server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30)
                server.starttls()
            except (OSError, smtplib.SMTPConnectError) as conn_err:
                # Try SSL on port 465 as fallback
                print(f"⚠️  Port {SMTP_PORT} failed, trying SSL port 465...")
                try:
                    server = smtplib.SMTP_SSL(SMTP_HOST, 465, timeout=30)
                except Exception as ssl_err:
                    raise ConnectionError(f"Cannot connect to SMTP server. Both port {SMTP_PORT} and 465 failed. Connect Gmail in admin dashboard to use Gmail API instead.")
            
            try:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
                results['success'] += 1
                print(f"✅ Announcement sent to {to_email}")
            finally:
                server.quit()
            
        except ConnectionError as e:
            results['failed'] += 1
            results['errors'].append(f"Network Error: {str(e)}")
            print(f"❌ Network error: {e}")
            # If we can't connect at all, no point trying other recipients via SMTP
            if results['success'] == 0 and results['failed'] == 1:
                results['errors'].append("Tip: Connect your Gmail account with 'Send' permission in admin dashboard.")
            break
        except smtplib.SMTPAuthenticationError as e:
            results['failed'] += 1
            results['errors'].append(f"Authentication error: Check SMTP credentials")
            print(f"❌ SMTP authentication failed: {e}")
        except TimeoutError as e:
            results['failed'] += 1
            results['errors'].append(f"Timeout: SMTP server not responding")
            print(f"❌ SMTP timeout: {e}")
        except Exception as e:
            results['failed'] += 1
            results['errors'].append(f"{to_email}: {str(e)}")
            print(f"❌ Failed to send to {to_email}: {e}")
    
    return results
