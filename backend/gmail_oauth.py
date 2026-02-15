"""
Gmail OAuth 2.0 Service for JobPulse
Connects to Gmail using OAuth 2.0 (no app password needed!)
Uses Google Gmail API instead of IMAP.
"""

import os
import json
import base64
from datetime import datetime, timedelta
from email import message_from_bytes
from email.header import decode_header

# Disable OAuthlib's HTTPS requirement for local testing
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
# Allow OAuth to work even when scopes change (Google adds extra scopes)
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from email_parser import parse_email

BASE_DIR = os.path.dirname(__file__)
CLIENT_SECRETS_FILE = os.path.join(BASE_DIR, "client_secrets.json")

# OAuth 2.0 scopes - readonly access to Gmail + send emails
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

# Redirect URI for OAuth flow
# For local development, use localhost; for production, use your domain
DEFAULT_REDIRECT_URI = "http://localhost:5050/api/gmail/oauth/callback"
PRODUCTION_REDIRECT_URI = "https://jobpulse.shramkavach.com/api/gmail/oauth/callback"


def get_redirect_uri():
    """Get the OAuth redirect URI from environment or auto-detect."""
    # Check environment variable first (strip to remove any whitespace/newlines)
    env_uri = os.environ.get("OAUTH_REDIRECT_URI", "").strip()
    if env_uri:
        return env_uri
    
    # Auto-detect based on environment
    # If running on Render/production, use production URI
    if os.environ.get("RENDER") or os.environ.get("PRODUCTION"):
        return PRODUCTION_REDIRECT_URI
    
    return DEFAULT_REDIRECT_URI


def is_oauth_configured() -> bool:
    """Check if OAuth client secrets are configured."""
    if os.path.exists(CLIENT_SECRETS_FILE):
        return True
    # Also check environment variables
    return bool(os.environ.get("GOOGLE_OAUTH_CLIENT_ID") and 
                os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET"))


def get_client_config() -> dict:
    """Load OAuth client configuration."""
    if os.path.exists(CLIENT_SECRETS_FILE):
        with open(CLIENT_SECRETS_FILE, 'r') as f:
            return json.load(f)
    
    # Fall back to environment variables (strip whitespace to avoid issues)
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID", "").strip()
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
    
    if not client_id or not client_secret:
        raise ValueError("OAuth not configured. Add client_secrets.json or set GOOGLE_OAUTH_CLIENT_ID/SECRET env vars.")
    
    redirect_uri = get_redirect_uri()
    
    return {
        "web": {
            "client_id": client_id,
            "project_id": "jobpulse",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": [redirect_uri],
            "javascript_origins": [redirect_uri.rsplit('/api/', 1)[0]],
        }
    }


def create_oauth_flow(state: str = None) -> Flow:
    """Create an OAuth 2.0 flow instance."""
    client_config = get_client_config()
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=get_redirect_uri()
    )
    
    if state:
        flow.state = state
    
    return flow


def get_authorization_url(state: str = None) -> tuple[str, str]:
    """
    Generate the OAuth authorization URL.
    Returns (authorization_url, state).
    """
    flow = create_oauth_flow()
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',  # Get refresh token
        include_granted_scopes='true',
        prompt='consent',  # Always ask for consent to get refresh token
        state=state
    )
    
    return authorization_url, state


def exchange_code_for_tokens(authorization_code: str, state: str = None) -> dict:
    """
    Exchange the authorization code for access and refresh tokens.
    Returns the credentials as a dict.
    """
    flow = create_oauth_flow(state)
    # Allow scope changes (Google may add additional scopes)
    flow.fetch_token(code=authorization_code)
    
    credentials = flow.credentials
    
    # Get the actual scopes granted (may include extras from Google)
    granted_scopes = list(credentials.scopes) if credentials.scopes else SCOPES
    
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes),
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
    }


def credentials_from_dict(creds_dict: dict) -> Credentials:
    """Reconstruct Credentials from a stored dict."""
    expiry = None
    if creds_dict.get("expiry"):
        try:
            expiry = datetime.fromisoformat(creds_dict["expiry"])
        except Exception:
            pass
    
    return Credentials(
        token=creds_dict.get("token"),
        refresh_token=creds_dict.get("refresh_token"),
        token_uri=creds_dict.get("token_uri", "https://oauth2.googleapis.com/token"),
        client_id=creds_dict.get("client_id"),
        client_secret=creds_dict.get("client_secret"),
        scopes=creds_dict.get("scopes", SCOPES),
        expiry=expiry
    )


def refresh_credentials_if_needed(creds_dict: dict) -> tuple[Credentials, dict | None]:
    """
    Refresh credentials if expired.
    Returns (credentials, updated_dict or None if not refreshed).
    """
    credentials = credentials_from_dict(creds_dict)
    
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
        
        # Return updated credentials dict
        updated = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": list(credentials.scopes) if credentials.scopes else SCOPES,
            "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
        }
        return credentials, updated
    
    return credentials, None


def get_gmail_service(credentials: Credentials):
    """Build the Gmail API service."""
    return build('gmail', 'v1', credentials=credentials)


def send_email_via_gmail_api(credentials: Credentials, to_email: str, subject: str, 
                              html_content: str, text_content: str = "") -> bool:
    """
    Send an email using Gmail API (HTTPS-based, works even when SMTP is blocked).
    
    Args:
        credentials: OAuth credentials with gmail.send scope
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email body
        text_content: Plain text email body (optional)
        
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        service = get_gmail_service(credentials)
        
        # Create the email message
        message = MIMEMultipart('alternative')
        message['To'] = to_email
        message['Subject'] = subject
        
        # Add text and HTML parts
        if text_content:
            part1 = MIMEText(text_content, 'plain')
            message.attach(part1)
        
        part2 = MIMEText(html_content, 'html')
        message.attach(part2)
        
        # Encode the message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        # Send the email
        result = service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        print(f"✅ Email sent via Gmail API to {to_email}, Message ID: {result.get('id')}")
        return True
        
    except HttpError as e:
        print(f"❌ Gmail API error sending to {to_email}: {e}")
        return False
    except Exception as e:
        print(f"❌ Error sending email via Gmail API to {to_email}: {e}")
        return False


def get_user_email(credentials: Credentials) -> str:
    """Get the authenticated user's email address."""
    service = get_gmail_service(credentials)
    profile = service.users().getProfile(userId='me').execute()
    return profile.get('emailAddress', '')


def test_oauth_connection(creds_dict: dict) -> tuple[bool, str, dict | None]:
    """
    Test OAuth connection and return user email.
    Returns (success, message_or_email, updated_creds_or_none).
    """
    try:
        credentials, updated_creds = refresh_credentials_if_needed(creds_dict)
        email = get_user_email(credentials)
        return True, email, updated_creds
    except HttpError as e:
        return False, f"Gmail API error: {e.reason}", None
    except Exception as e:
        return False, f"Connection failed: {str(e)}", None


def decode_mime_header(header_value: str) -> str:
    """Decode MIME-encoded email header."""
    if not header_value:
        return ""
    decoded_parts = decode_header(header_value)
    result = ""
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result += part.decode(charset or "utf-8", errors="replace")
        else:
            result += part
    return result


def get_email_body_from_payload(payload: dict) -> str:
    """Extract text body from Gmail API message payload."""
    body = ""
    
    def extract_parts(parts):
        nonlocal body
        for part in parts:
            mime_type = part.get('mimeType', '')
            if 'parts' in part:
                extract_parts(part['parts'])
            elif mime_type == 'text/plain' and not body:
                data = part.get('body', {}).get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
            elif mime_type == 'text/html' and not body:
                data = part.get('body', {}).get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
    
    if 'parts' in payload:
        extract_parts(payload['parts'])
    else:
        # Single part message
        data = payload.get('body', {}).get('data', '')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
    
    return body


def scan_emails_oauth(creds_dict: dict, days_back: int = 90, max_results: int = 500) -> tuple[list[dict], dict | None]:
    """
    Scan Gmail for job application emails using OAuth.
    Returns (list of parsed applications, updated_creds_or_none).
    """
    credentials, updated_creds = refresh_credentials_if_needed(creds_dict)
    service = get_gmail_service(credentials)
    
    email_address = get_user_email(credentials)
    print(f"📧 Scanning Gmail as {email_address} (OAuth)...")
    
    since_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
    
    # OPTIMIZED: Single comprehensive query approach for speed
    # Combine all high-confidence domains in one large query
    search_queries = []
    
    # Priority domains: ATS platforms (highest signal-to-noise ratio)
    ats_domains = [
        "myworkday.com", "myworkdayjobs.com", "greenhouse.io", "lever.co", 
        "icims.com", "smartrecruiters.com", "taleo.net", "successfactors.com", 
        "workable.com", "ashbyhq.com", "jobvite.com", "ultipro.com", 
        "breezy.hr", "recruiterbox.com", "bamboohr.com", "jazz.co", 
        "recruitee.com", "teamtailor.com",
    ]
    
    # Major company domains (verified reliable senders)
    company_domains = [
        # Tech Giants
        "google.com", "amazon.com", "microsoft.com", "apple.com", "meta.com", 
        "netflix.com", "salesforce.com", "oracle.com", "adobe.com", "ibm.com",
        "intel.com", "nvidia.com", "spotify.com", "uber.com", "lyft.com",
        "airbnb.com", "stripe.com", "paypal.com", "servicenow.com",
        # Finance
        "jpmorgan.com", "goldmansachs.com", "morganstanley.com", "citi.com",
        "blackrock.com", "wellsfargo.com", "bankofamerica.com",
        # Indian IT
        "infosys.com", "tcs.com", "wipro.com", "hcltech.com", "cognizant.com",
        "ltimindtree.com", "techmahindra.com",
        # Consulting
        "accenture.com", "deloitte.com", "ey.com", "kpmg.com", "pwc.com",
        "mckinsey.com", "bcg.com", "bain.com",
    ]
    
    # Job board platforms (catch-all for platforms)
    job_platforms = [
        "linkedin.com", "naukri.com", "indeed.com", "glassdoor.com",
        "wellfound.com", "instahyre.com", "internshala.com",
    ]
    
    # Combine all into larger batches (20 domains per query for speed)
    all_domains = ats_domains + company_domains + job_platforms
    batch_size = 20
    num_batches = (len(all_domains) + batch_size - 1) // batch_size
    print(f"  🚀 Fast search: {len(all_domains)} domains in {num_batches} queries...")
    
    for i in range(0, len(all_domains), batch_size):
        batch = all_domains[i:i + batch_size]
        or_query = " OR ".join(f"from:{domain}" for domain in batch)
        search_queries.append(f"({or_query}) after:{since_date}")
    
    # High-value subject keywords only (skip redundant platform searches since domains already cover them)
    # Focus on job-specific terms that are unlikely to be spam
    critical_keywords = [
        "application submitted", "successfully applied", "thank you for applying",
        "interview scheduled", "interview invitation", "coding challenge",
        "technical assessment", "online assessment", "regret to inform",
        "not been selected", "position has been filled",
    ]
    
    # Single batched query for critical keywords
    batch_size = 5
    num_keyword_batches = (len(critical_keywords) + batch_size - 1) // batch_size
    print(f"  🔍 Adding {len(critical_keywords)} critical keywords in {num_keyword_batches} queries...")
    for i in range(0, len(critical_keywords), batch_size):
        batch = critical_keywords[i:i + batch_size]
        or_query = " OR ".join(f'subject:"{keyword}"' for keyword in batch)
        search_queries.append(f"({or_query}) after:{since_date}")
    
    # Collect message IDs with early exit if we have enough
    all_message_ids = set()
    target_emails = max_results * 2  # Get 2x target to account for filtering
    
    print(f"  ⚙️ Executing {len(search_queries)} optimized queries (target: {target_emails} emails)...")
    query_count = 0
    
    for query in search_queries:
        # Early exit if we have enough emails
        if len(all_message_ids) >= target_emails:
            print(f"  ✓ Reached target ({len(all_message_ids)} emails), skipping remaining queries")
            break
            
        query_count += 1
        try:
            results = service.users().messages().list(
                userId='me',
                q=query,
                maxResults=100  # Reduced for speed - we have larger batches
            ).execute()
            
            messages = results.get('messages', [])
            if messages:
                print(f"  📧 Q{query_count}: +{len(messages)} emails (total: {len(all_message_ids)})")
            for msg in messages:
                all_message_ids.add(msg['id'])
                
        except HttpError as e:
            if hasattr(e, 'status_code') and e.status_code == 429:
                print(f"  ⚠️ Rate limit hit! Stopping search.")
                break
            continue
        except Exception as e:
            print(f"  ⚠️ Unexpected error in query {query_count}: {e}")
            continue
    
    print(f"  📊 Found {len(all_message_ids)} unique emails")
    
    # Process emails efficiently with skip tracking
    message_ids = list(all_message_ids)
    print(f"📬 Processing {min(len(message_ids), max_results)} emails...")
    
    if not message_ids:
        print("  ℹ️ No emails found")
        return [], updated_creds
    
    parsed_applications = []
    seen = set()  # Track company+role combinations
    skipped_msg_ids = set()  # Track message IDs that were skipped
    processed = 0
    skipped = 0
    
    # Process only up to max_results (already have enough from search)
    for msg_id in message_ids[:max_results * 2]:  # 2x buffer for filtering
        # Skip if this message was already processed and skipped
        if msg_id in skipped_msg_ids:
            continue
            
        # Early exit if we have enough parsed applications
        if len(parsed_applications) >= max_results:
            print(f"  ✓ Reached {max_results} applications, stopping processing")
            break
            
        processed += 1
        if processed % 100 == 0:
            print(f"  ⏳ {processed} processed, {len(parsed_applications)} parsed...")
        
        try:
            # Fetch with minimal format for speed
            msg = service.users().messages().get(
                userId='me',
                id=msg_id,
                format='full'
            ).execute()
            
            # Extract headers efficiently
            headers = {h['name'].lower(): h['value'] for h in msg['payload'].get('headers', [])}
            sender = decode_mime_header(headers.get('from', ''))
            subject = decode_mime_header(headers.get('subject', ''))
            
            # Quick date parsing
            try:
                internal_date = int(msg.get('internalDate', 0)) / 1000
                applied_date = datetime.fromtimestamp(internal_date).strftime("%Y-%m-%d")
            except Exception:
                applied_date = datetime.now().strftime("%Y-%m-%d")
            
            # Extract body
            body = get_email_body_from_payload(msg['payload'])
            
            if not body or len(body.strip()) < 20:
                skipped += 1
                skipped_msg_ids.add(msg_id)  # Remember to skip this email
                continue
            
            # Parse the email - parser handles filtering
            app = parse_email(sender, subject, body, applied_date)
            
            if app:
                # Deduplicate by company+role
                key = f"{app['company'].lower().strip()}_{app['role'].lower().strip()}"
                if key not in seen:
                    seen.add(key)
                    parsed_applications.append(app)
                    print(f"  ✅ {app['company']}: {app['role']}")
                else:
                    skipped += 1
                    skipped_msg_ids.add(msg_id)  # Remember duplicate
            else:
                skipped += 1
                skipped_msg_ids.add(msg_id)  # Remember non-job email
                
        except HttpError as e:
            if hasattr(e, 'status_code') and e.status_code == 429:
                print(f"  ⚠️ Rate limit hit! Stopping.")
                break  # Exit early on rate limit
            skipped += 1
            skipped_msg_ids.add(msg_id)  # Remember failed email
            continue
        except Exception:
            skipped += 1
            skipped_msg_ids.add(msg_id)  # Remember failed email
            continue
    
    print(f"\n🎯 Optimized OAuth Scan Complete:")
    print(f"  • {processed} emails processed")
    print(f"  • {len(parsed_applications)} applications found")
    print(f"  • {skipped} filtered/skipped")
    return parsed_applications, updated_creds
