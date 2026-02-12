"""
Gmail IMAP Service for JobPulse
Connects to Gmail using IMAP + App Password (no Google Cloud needed!)
Scans inbox for job application confirmation emails.
"""

import imaplib
import email
import json
import os
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta

from email_parser import parse_email

BASE_DIR = os.path.dirname(__file__)
CONFIG_FILE = os.path.join(BASE_DIR, "gmail_config.json")

IMAP_SERVER = "imap.gmail.com"
IMAP_PORT = 993


# ---------- Multi-account config helpers ----------

def _load_all_config() -> dict:
    """Load full config file. Returns {"accounts": [...]}."""
    if not os.path.exists(CONFIG_FILE):
        return {"accounts": []}
    try:
        with open(CONFIG_FILE, "r") as f:
            data = json.load(f)
        # Migrate old single-account format
        if "email" in data and "accounts" not in data:
            migrated = {
                "accounts": [{
                    "id": 1,
                    "email": data["email"],
                    "app_password": data["app_password"],
                }]
            }
            _save_all_config(migrated)
            return migrated
        return data
    except Exception:
        return {"accounts": []}


def _save_all_config(data: dict):
    """Persist full config to disk."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _next_id(accounts: list) -> int:
    return max((a["id"] for a in accounts), default=0) + 1


# ---------- Public API ----------

def get_accounts(include_password: bool = False) -> list[dict]:
    """Return list of connected accounts (without passwords by default)."""
    data = _load_all_config()
    accounts = data.get("accounts", [])
    if include_password:
        return accounts
    return [{"id": a["id"], "email": a["email"]} for a in accounts]


def add_account(email_address: str, app_password: str) -> dict:
    """Add a new Gmail account. Returns the new account dict."""
    data = _load_all_config()
    # Prevent duplicate emails
    for a in data["accounts"]:
        if a["email"].lower() == email_address.lower():
            raise ValueError(f"{email_address} is already connected.")
    new_acct = {
        "id": _next_id(data["accounts"]),
        "email": email_address,
        "app_password": app_password,
    }
    data["accounts"].append(new_acct)
    _save_all_config(data)
    return {"id": new_acct["id"], "email": new_acct["email"]}


def remove_account(account_id: int) -> bool:
    """Remove an account by id. Returns True if found and removed."""
    data = _load_all_config()
    before = len(data["accounts"])
    data["accounts"] = [a for a in data["accounts"] if a["id"] != account_id]
    if len(data["accounts"]) < before:
        _save_all_config(data)
        return True
    return False


# ---------- Backward-compat wrappers (used by old endpoints) ----------

def save_config(email_address: str, app_password: str):
    """Save Gmail credentials (adds as first account if none exist)."""
    add_account(email_address, app_password)


def load_config() -> dict | None:
    """Load first account credentials (backward compat)."""
    accounts = get_accounts(include_password=True)
    return accounts[0] if accounts else None


def delete_config():
    """Remove ALL saved credentials."""
    _save_all_config({"accounts": []})


def is_authenticated() -> bool:
    """Check if at least one account is connected."""
    return len(get_accounts()) > 0


def test_connection(email_address: str, app_password: str) -> tuple[bool, str]:
    """Test Gmail IMAP connection with given credentials."""
    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        mail.login(email_address, app_password)
        mail.logout()
        return True, "Connection successful!"
    except imaplib.IMAP4.error as e:
        error_msg = str(e)
        if "AUTHENTICATIONFAILED" in error_msg.upper():
            return False, "Authentication failed. Check your email and App Password."
        return False, f"IMAP error: {error_msg}"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


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


def get_email_body(msg) -> str:
    """Extract text body from email message."""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                continue
            if content_type == "text/plain":
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or "utf-8"
                    body = payload.decode(charset, errors="replace")
                    break
                except Exception:
                    continue
            elif content_type == "text/html" and not body:
                try:
                    payload = part.get_payload(decode=True)
                    charset = part.get_content_charset() or "utf-8"
                    body = payload.decode(charset, errors="replace")
                except Exception:
                    continue
    else:
        try:
            payload = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or "utf-8"
            body = payload.decode(charset, errors="replace")
        except Exception:
            pass
    return body


def _scan_single_account(account: dict, days_back: int, max_results: int) -> list[dict]:
    """
    Scan one Gmail account via IMAP for job application confirmation emails.
    Returns list of parsed application dicts.
    """
    print(f"📧 Connecting to Gmail as {account['email']}...")
    mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
    mail.login(account["email"], account["app_password"])

    # Try All Mail first, fall back to INBOX
    status, _ = mail.select('"[Gmail]/All Mail"')
    if status != "OK":
        mail.select("INBOX")

    since_date = (datetime.now() - timedelta(days=days_back)).strftime("%d-%b-%Y")

    all_email_ids = set()

    def _search(criteria):
        """Run one IMAP search, return list of message IDs."""
        try:
            status, data = mail.search(None, criteria)
            if status == "OK" and data[0]:
                return data[0].split()
        except Exception as e:
            print(f"  ⚠️ Search failed: {e}")
        return []

    # ------------------------------------------------------------------
    # TIER 1 + 2: ATS + Company domains (batch using OR)
    # IMAP OR syntax: (OR FROM "a.com" FROM "b.com") for 2
    #   For 3+, nest: (OR (OR FROM "a.com" FROM "b.com") FROM "c.com")
    # ------------------------------------------------------------------
    all_sender_domains = [
        # ATS platforms (low noise, high signal)
        "myworkday.com", "myworkdayjobs.com",
        "greenhouse.io", "lever.co", "icims.com",
        "smartrecruiters.com", "taleo.net",
        "successfactors.com", "workable.com", "ashbyhq.com",
        "jobvite.com", "ultipro.com", "breezy.hr", "recruiterbox.com",
        "bamboohr.com", "jazz.co", "recruitee.com", "teamtailor.com",
        # Banking / Finance
        "barclays.com", "jpmorgan.com", "jpmorganchase.com",
        "goldmansachs.com", "morganstanley.com", "citi.com",
        "hsbc.com", "standardchartered.com", "wellsfargo.com",
        "bankofamerica.com", "deutschebank.com", "ubs.com",
        "credit-suisse.com", "blackrock.com", "fidelity.com",
        # Indian IT
        "infosys.com", "tcs.com", "wipro.com", "hcltech.com",
        "cognizant.com", "ltimindtree.com",
        "mphasis.com", "hexaware.com", "persistent.com",
        "techmahindra.com", "coforge.com", "mindtree.com",
        # Big Tech
        "google.com", "amazon.com", "microsoft.com", "apple.com",
        "meta.com", "netflix.com", "salesforce.com", "oracle.com",
        "adobe.com", "ibm.com", "intel.com", "nvidia.com",
        "spotify.com", "snap.com", "twitter.com", "uber.com",
        "lyft.com", "airbnb.com", "stripe.com", "square.com",
        "paypal.com", "servicenow.com", "snowflake.com", "databricks.com",
        "atlassian.com", "slack.com", "zoom.us", "docusign.com",
        # Consulting
        "accenture.com", "deloitte.com", "ey.com", "kpmg.com", "pwc.com",
        "capgemini.com", "bain.com", "bcg.com", "mckinsey.com",
        "boozallen.com", "slalom.com", "thoughtworks.com",
        # E-commerce / Retail
        "flipkart.com", "walmart.com", "target.com", "bestbuy.com",
        "costco.com", "homedepot.com", "ebay.com", "etsy.com",
        # Startups / Scale-ups
        "freshworks.com", "zoho.com", "razorpay.com", "paytm.com",
        "swiggy.in", "zomato.com", "ola.com", "policybazaar.com",
        "cred.club", "byju.com", "upgrad.com",
        # Healthcare / Pharma
        "amgen.com", "pfizer.com", "jnj.com", "roche.com",
        "novartis.com", "merck.com", "abbvie.com", "gilead.com",
        # Automotive / Manufacturing
        "tesla.com", "ford.com", "gm.com", "bmw.com",
        "toyota.com", "volkswagen.com", "bosch.com",
        # Aerospace / Defense
        "boeing.com", "lockheedmartin.com", "raytheon.com",
        "northropgrumman.com", "spacex.com", "blueorigin.com",
        # Telecom
        "verizon.com", "att.com", "tmobile.com", "vodafone.com",
        "airtel.in", "jio.com", "ericsson.com", "nokia.com",
        # Other major employers
        "siemens.com", "cisco.com", "sap.com", "vmware.com",
        "dell.com", "hp.com", "lenovo.com", "ge.com",
        "honeywell.com", "3m.com", "caterpillar.com",
    ]

    # Batch into groups of 5 domains using IMAP OR
    print(f"  🔍 Searching {len(all_sender_domains)} company/ATS domains...")
    batch_size = 5
    for i in range(0, len(all_sender_domains), batch_size):
        batch = all_sender_domains[i:i + batch_size]
        if len(batch) == 1:
            criteria = f'(SINCE {since_date} FROM "{batch[0]}")'
        else:
            # Build nested OR: (OR (OR FROM "a" FROM "b") FROM "c")
            expr = f'FROM "{batch[0]}"'
            for d in batch[1:]:
                expr = f'OR {expr} FROM "{d}"'
            criteria = f'(SINCE {since_date} {expr})'
        ids = _search(criteria)
        all_email_ids.update(ids)

    print(f"  📊 After domain search: {len(all_email_ids)} emails")

    # ------------------------------------------------------------------
    # TIER 3: Job platforms - TARGETED (sender + subject together)
    # ------------------------------------------------------------------
    platform_targeted_searches = [
        ('linkedin.com', 'application'),
        ('linkedin.com', 'you applied'),
        ('linkedin.com', 'application was sent'),
        ('linkedin.com', 'thank you for applying'),
        ('naukri.com', 'successfully applied'),
        ('naukri.com', 'application confirmation'),
        ('naukri.com', 'your application for'),
        ('naukri.com', 'profile sent'),
        ('indeed.com', 'you applied'),
        ('indeed.com', 'application submitted'),
        ('indeed.com', 'application sent'),
        ('glassdoor.com', 'application submitted'),
        ('glassdoor.com', 'you applied'),
        ('wellfound.com', 'application'),
        ('wellfound.com', 'you applied'),
        ('instahyre.com', 'application'),
        ('instahyre.com', 'profile shared'),
        ('internshala.com', 'applied'),
        ('internshala.com', 'application'),
        ('monster.com', 'application'),
        ('monster.com', 'you applied'),
        ('shine.com', 'applied'),
        ('shine.com', 'application sent'),
        ('apna.co', 'applied'),
        ('foundit.in', 'application'),
        ('hirist.com', 'applied'),
        ('cutshort.io', 'application'),
    ]
    print(f"  🔍 Searching {len(platform_targeted_searches)} platform-targeted queries...")
    for sender_domain, keyword in platform_targeted_searches:
        ids = _search(f'(SINCE {since_date} FROM "{sender_domain}" SUBJECT "{keyword}")')
        all_email_ids.update(ids)

    print(f"  📊 After platform search: {len(all_email_ids)} emails")

    # ------------------------------------------------------------------
    # TIER 4: Subject-only searches (catch from unknown domains)
    # ------------------------------------------------------------------
    subject_keywords = [
        # Application confirmations
        "application submitted", "application was sent",
        "successfully applied", "application confirmation",
        "thank you for applying", "we received your application",
        "thank you for your application", "application received",
        "your application to", "application for the position",
        "application has been submitted", "we have received your application",
        # Rejections
        "regret to inform", "not been selected",
        "not moving forward", "after careful consideration",
        "unfortunately", "will not be moving forward",
        "decided to pursue other candidates", "position has been filled",
        "unsuccessful", "did not progress",
        # Interviews
        "interview scheduled", "interview invitation",
        "invite you to interview", "schedule an interview",
        "interview opportunity", "next steps in the interview",
        "phone screen", "technical interview", "onsite interview",
        # Assessments
        "assessment invitation", "online assessment",
        "coding challenge", "technical assessment",
        "complete the assessment", "take home assignment",
        "coding test", "technical evaluation",
        # Role-specific keywords
        "software engineer position", "data scientist role",
        "product manager opening", "designer position",
        "analyst role", "developer position",
        "intern application", "internship confirmation",
    ]
    print(f"  🔍 Searching {len(subject_keywords)} subject keywords...")
    for keyword in subject_keywords:
        ids = _search(f'(SINCE {since_date} SUBJECT "{keyword}")')
        all_email_ids.update(ids)

    print(f"  📊 Total unique emails found: {len(all_email_ids)}")

    email_ids = list(all_email_ids)[:max_results]
    print(f"📬 Processing {len(email_ids)} potential job emails")

    if not email_ids:
        mail.logout()
        return []

    parsed_applications = []
    seen = set()

    for eid in email_ids:
        try:
            status, msg_data = mail.fetch(eid, "(RFC822)")
            if status != "OK":
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)

            sender = decode_mime_header(msg.get("From", ""))
            subject = decode_mime_header(msg.get("Subject", ""))
            date_str = msg.get("Date", "")

            try:
                parsed_date = parsedate_to_datetime(date_str)
                applied_date = parsed_date.strftime("%Y-%m-%d")
            except Exception:
                applied_date = datetime.now().strftime("%Y-%m-%d")

            body = get_email_body(msg)
            app = parse_email(sender, subject, body, applied_date)

            if app:
                key = f"{app['company'].lower().strip()}_{app['role'].lower().strip()}"
                if key not in seen:
                    seen.add(key)
                    parsed_applications.append(app)
                    print(f"  ✅ {app['platform']}: {app['role']} at {app['company']}")
            else:
                print(f"  ⏭️ Skipped: [{sender[:50]}] {subject[:80]}")

        except Exception as e:
            print(f"  ⚠️ Error processing email: {e}")
            continue

    mail.logout()
    print(f"\n🎯 Parsed {len(parsed_applications)} job applications from {account['email']}!")
    return parsed_applications


def scan_emails_for_account(email_address: str, app_password: str,
                             days_back: int = 90, max_results: int = 500) -> list[dict]:
    """Scan a single Gmail account using explicit credentials (for MongoDB-backed auth)."""
    account = {"email": email_address, "app_password": app_password}
    return _scan_single_account(account, days_back, max_results)


def scan_emails(days_back: int = 90, max_results: int = 500, account_id: int | None = None) -> list[dict]:
    """
    Scan Gmail for job application emails.
    If account_id is given, scan only that account. Otherwise scan all.
    """
    accounts = get_accounts(include_password=True)
    if not accounts:
        raise ValueError("No Gmail accounts connected. Please add one first.")

    if account_id is not None:
        accounts = [a for a in accounts if a["id"] == account_id]
        if not accounts:
            raise ValueError(f"Account #{account_id} not found.")

    all_apps = []
    seen = set()
    for acct in accounts:
        try:
            apps = _scan_single_account(acct, days_back, max_results)
            for app in apps:
                key = f"{app['company'].lower().strip()}_{app['role'].lower().strip()}"
                if key not in seen:
                    seen.add(key)
                    all_apps.append(app)
        except Exception as e:
            print(f"  ⚠️ Error scanning {acct['email']}: {e}")

    print(f"\n📊 Total: {len(all_apps)} unique applications from {len(accounts)} account(s)")
    return all_apps
