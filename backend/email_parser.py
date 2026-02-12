"""
Gmail Email Parser for JobPulse
Parses ONLY actual job-application-confirmation emails.
Rejects digests, newsletters, job alerts, and recommendations.
"""

import re
import html
from datetime import datetime


# ============================================================
#  REJECT PATTERNS - Skip these emails outright
# ============================================================

REJECT_SUBJECT_PATTERNS = [
    # --- Generic digest / alert patterns ---
    r"\d+\s+jobs?\s+(?:on|for|matching|in)\b",
    r"jobs?\s+matching\s+your\s+profile",
    r"recommended\s+jobs?\s+for\s+you",
    r"new\s+jobs?\s+(?:for|near|in)\b",
    r"top\s+\d+\s+jobs?",
    r"jobs?\s+you\s+might\s+(?:like|be\s+interested)",
    r"jobs?\s+you\s+(?:may|might)\s+be\s+interested",
    r"job\s+alert",
    r"job\s+recommendations?",
    r"daily\s+job\s+digest",
    r"weekly\s+job\s+digest",
    r"similar\s+jobs?\s+to",
    r"companies?\s+(?:are\s+)?hiring",
    r"hiring\s+(?:now|alert|update)",
    r"career\s+(?:update|newsletter|digest)",
    r"recruiter\s+(?:viewed|searched|looked)",
    r"profile\s+(?:views?|visitors?|strength|update)",
    r"complete\s+your\s+profile",
    r"update\s+your\s+(?:resume|profile|cv)",
    r"salary\s+(?:insight|report|trend)",
    r"invitation\s+to\s+(?:connect|apply)",
    r"(?:course|skill|certification)\s+recommendation",
    r"people\s+(?:also|are)\s+(?:viewed|applied)",
    r"upcoming\s+(?:webinar|event|workshop)",
    r"new\s+(?:review|salary|interview)\s+(?:for|at|on)",
    r"company\s+(?:review|rating)",
    r"interview\s+(?:tips?|questions?|preparation)",
    r"salary\s+(?:for|at|estimate)",
    r"new\s+jobs?\s+(?:posted|available|near)",
    r"jobs?\s+added\s+(?:for|near|today)",
    r"(?:who.s|who\s+is)\s+(?:viewed|looking|hiring)",
    r"is\s+hiring",
    r"since\s+you\s+(?:applied|viewed|searched)",
    r"network\s+(?:update|digest)",
    r"(?:\d+)\s+new\s+(?:jobs?|opportunities)",
    r"trending\s+(?:jobs?|articles?|news)",
    r"newsletter",
    r"weekly\s+(?:update|roundup|digest)",
    r"monthly\s+(?:update|roundup|digest)",

    # --- Glassdoor daily job alert format: "X at Company and N more jobs" ---
    r"and\s+\d+\s+more\s+jobs?",
    r"others\s+are\s+hiring",
    r"just\s+in\s+at\s+.+?:\s+this\s+week",
    r"employee\s+reviews?",
    r"check\s+out\s+recent\s+updates?",
    r"explore\s+real\s+talk",

    # --- Naukri spam patterns ---
    r"check\s+out\s+jobs?\s+applied\s+by",
    r"weekly\s+recap.*jobs?\s+that\s+await",
    r"discover\s+missed\s+opportunities",
    r"show\s+your\s+.+?\s+expertise",
    r"feedback\s+on\s+your\s+(?:naukri|job)\s+(?:applies|applications)",
    r"you\s+just\s+got\s+a\s+free",
    r"exciting\s+job\s+opportunit",
    r"urgent\s+requirement\s+for",
    r"active\s+jobs",
    r"pro\s+nvite",
    r"mental\s+health",
    r"fastforward",
    r"walk[- ]?in\s+interview",

    # --- Naukri recruiter invite format ---
    r"^\u2709\ufe0f?\s*(?:Job|Walk-in)",

    # --- Indeed job match format ---
    r"@\s+.+$",  # "Role @ Company" format from Indeed matches
]

_REJECT_RE = re.compile(
    "|".join(f"(?:{p})" for p in REJECT_SUBJECT_PATTERNS),
    re.IGNORECASE,
)


# ============================================================
#  CONFIRMATION KEYWORDS - Must appear in subject or body
# ============================================================

CONFIRMATION_KEYWORDS = [
    "application was sent",
    "application has been submitted",
    "application submitted",
    "application confirmation",
    "application received",
    "successfully applied",
    "you have successfully applied",
    "you applied for",
    "you applied to",
    "your application for",
    "your application to",
    "your application was sent",
    "thank you for applying",
    "thanks for applying",
    "we received your application",
    "we have received your application",
    "application sent to",
    "applied to the position",
    "applied for the position",
    "applied for the role",
    # Additional real-world phrasings
    "thank you for your application",
    "thank you for your interest",
    "thanks for your interest",
    "application has been received",
    "your application has been received",
    "we have your application",
    "we received your resume",
    "your resume has been submitted",
    "your resume has been received",
    "thank you for submitting",
    "thanks for submitting",
    "acknowledgment of your application",
    "acknowledge receipt of your application",
    "confirming your application",
    "your application is under review",
    "your application is being reviewed",
    "we will review your application",
    "application is now under review",
    "application under consideration",
    "you have applied for",
    "you have applied to",
    "applied successfully",
]


# ============================================================
#  REJECTION KEYWORDS - Detect rejection / not-selected emails
# ============================================================

REJECTION_KEYWORDS = [
    "regret to inform",
    "not been selected",
    "not been shortlisted",
    "not selected",
    "not shortlisted",
    "unable to move forward",
    "will not be moving forward",
    "not moving forward",
    "decided not to proceed",
    "decided to move forward with other",
    "moved forward with other",
    "move forward with other",
    "decided to pursue other",
    "pursuing other candidates",
    "position has been filled",
    "role has been filled",
    "no longer considering",
    "not progressing your application",
    "unsuccessful",
    "your application was not",
    "application is not",
    "we will not be",
    "we won't be",
    "unfortunately",
    "after careful consideration",
    "after careful review",
    "we appreciate your interest but",
    "not a match",
    "not the right fit",
    "rejected",
    "your application to .+ has been closed",
    "application closed",
    "decided not to progress",
    "not to progress your application",
    "will not be proceeding",
    "unable to offer you",
    "cannot offer you",
]


# ============================================================
#  INTERVIEW / PROGRESS KEYWORDS
# ============================================================

INTERVIEW_KEYWORDS = [
    "interview scheduled",
    "schedule an interview",
    "schedule your interview",
    "interview invitation",
    "invite you for an interview",
    "like to invite you",
    "would like to schedule",
    "next steps in the process",
    "next round",
    "move to the next step",
    "proceed to the next",
    "shortlisted",
    "you have been shortlisted",
    "selected for interview",
    "technical interview",
    "phone screen",
    "phone interview",
    "video interview",
    "face to face interview",
    "in-person interview",
]


# ============================================================
#  ASSESSMENT / TEST KEYWORDS (separate from interview!)
# ============================================================

ASSESSMENT_KEYWORDS = [
    "assessment invitation",
    "online assessment",
    "online test",
    "coding challenge",
    "coding test",
    "coding assessment",
    "aptitude test",
    "technical test",
    "complete your assessment",
    "complete the assessment",
    "complete your test",
    "complete the test",
    "take the test",
    "take the assessment",
    "test invitation",
    "test link",
    "assessment link",
    "hackerrank",
    "hackerearth",
    "codility",
    "hirevue",
    "mettl",
    "amcat",
    "shl assessment",
    "pymetrics",
]


# ============================================================
#  PLATFORM PATTERNS - Extraction rules per platform
# ============================================================

PLATFORM_PATTERNS = {
    "LinkedIn": {
        "senders": [
            "jobs-noreply@linkedin.com",
            "linkedin@e.linkedin.com",
        ],
        "subject_patterns": [
            r"[Yy]ou applied for (?P<role>.+?) at (?P<company>.+)",
            r"[Yy]our application to (?P<role>.+?) at (?P<company>.+)",
            r"[Yy]our application (?:was sent|has been submitted) to (?P<company>.+?)\.?$",
            r"[Yy]our application to (?P<company>.+?) was sent",
        ],
        "body_patterns": [
            r"[Yy]ou applied for\s+(?P<role>.+?)\s+at\s+(?P<company>.+?)(?:\.|,|\s+\xb7|\s*$)",
            r"applied for the\s+(?P<role>.+?)\s+position at\s+(?P<company>.+?)(?:\.|,|\s+\xb7|\s*$)",
            r"[Yy]our application for\s+(?P<role>.+?)\s+at\s+(?P<company>.+?)\s+was sent",
            r"[Yy]ou applied for\s+(?P<role>.+?)\s+(?P<company>[A-Z][A-Za-z0-9&()\s,.-]+?)(?:\s+\xb7|\s+[A-Z][a-z]+,|\s*$)",
        ],
    },
    "Naukri": {
        "senders": [
            "info@naukri.com",
            "notification@naukri.com",
            "do_not_reply@naukri.com",
            "mailer@naukri.com",
        ],
        "subject_patterns": [
            r"[Yy]ou have successfully applied (?:to|for) (.+?) at (.+)",
            r"[Aa]pplication [Cc]onfirmation.+?(.+?) at (.+)",
            r"[Yy]our application for (.+?) at (.+?) (?:has been|was)",
        ],
        "body_patterns": [
            r"[Yy]ou have successfully applied (?:for|to)\s+(.+?)\s+at\s+(.+?)[\.\n,]",
            r"applied (?:for|to) the (?:position|role) of\s+(.+?)\s+at\s+(.+?)[\.\n,]",
            r"[Pp]osition\s*:\s*(.+?)[\n\r]",
            r"[Cc]ompany\s*:\s*(.+?)[\n\r]",
            r"[Rr]ole\s*:\s*(.+?)[\n\r]",
        ],
    },
    "Indeed": {
        "senders": [
            "indeedapply@indeed.com",
            "noreply@indeed.com",
            "indeed@indeed.com",
            "apply@indeed.com",
        ],
        "subject_patterns": [
            r"[Yy]our application to (.+?) has been submitted",
            r"[Yy]ou applied to (.+?) at (.+)",
            r"[Aa]pplication received.+?(.+?) at (.+)",
            r"(.+?) application submitted",
        ],
        "body_patterns": [
            r"[Yy]ou applied to\s+(.+?)\s+at\s+(.+?)[\.\n]",
            r"applied for\s+(.+?)\s+at\s+(.+?)[\.\n]",
            r"[Pp]osition\s*:\s*(.+?)[\n\r]",
            r"[Cc]ompany\s*:\s*(.+?)[\n\r]",
        ],
    },
    "Glassdoor": {
        "senders": [
            "noreply@glassdoor.com",
            "glassdoor@glassdoor.com",
        ],
        "subject_patterns": [
            r"[Yy]our application to (.+?) has been submitted",
            r"[Yy]ou applied for (.+?) at (.+)",
            r"[Aa]pplication submitted.+?(.+?) at (.+)",
        ],
        "body_patterns": [
            r"applied (?:for|to)\s+(.+?)\s+at\s+(.+?)[\.\n]",
            r"[Yy]ou applied for\s+(.+?)\s+at\s+(.+?)[\.\n]",
        ],
    },
    "Wellfound": {
        "senders": [
            "noreply@wellfound.com",
            "talent@wellfound.com",
            "noreply@angel.co",
        ],
        "subject_patterns": [
            r"[Yy]ou applied to (.+?) at (.+)",
            r"[Aa]pplication (?:sent|submitted).+?(.+?) at (.+)",
        ],
        "body_patterns": [
            r"applied to\s+(.+?)\s+at\s+(.+?)[\.\n]",
        ],
    },
    "Instahyre": {
        "senders": [
            "noreply@instahyre.com",
            "notifications@instahyre.com",
        ],
        "subject_patterns": [
            r"[Aa]pplication.+?(.+?) at (.+)",
        ],
        "body_patterns": [
            r"applied (?:for|to)\s+(.+?)\s+at\s+(.+?)[\.\n]",
        ],
    },
    "Internshala": {
        "senders": [
            "noreply@internshala.com",
            "trainings@internshala.com",
        ],
        "subject_patterns": [
            r"[Aa]pplication.+?(.+?) at (.+)",
            r"[Yy]ou have applied for (.+?) at (.+)",
        ],
        "body_patterns": [
            r"applied for\s+(.+?)\s+at\s+(.+?)[\.\n]",
            r"[Pp]rofile\s*:\s*(.+?)[\n\r]",
            r"[Cc]ompany\s*:\s*(.+?)[\n\r]",
        ],
    },
    "ZipRecruiter": {
        "senders": ["noreply@ziprecruiter.com"],
        "subject_patterns": [
            r"[Yy]ou applied for (.+?) at (.+)",
        ],
        "body_patterns": [
            r"applied for\s+(.+?)\s+at\s+(.+?)[\.\n]",
        ],
    },
    "Monster": {
        "senders": ["noreply@monster.com", "jobs@monster.com"],
        "subject_patterns": [
            r"[Yy]ou applied for (.+?) at (.+)",
        ],
        "body_patterns": [
            r"applied for\s+(.+?)\s+at\s+(.+?)[\.\n]",
        ],
    },    "Workday": {
        "senders": [
            "myworkday.com",
            "myworkdayjobs.com",
            "workday.com",
            "wd3.myworkday.com",
            "wd5.myworkday.com",
        ],
        "subject_patterns": [
            r"[Yy]our application (?:for|to)\s+(.+?)\s+(?:at|with|-|–)\s+(.+?)(?:\s+(?:has|was|is|have)\b|$)",
            r"[Aa]pplication (?:received|submitted|confirmation).+?(.+?)\s+(?:at|with|-|–)\s+(.+?)(?:\s+(?:has|was|is|have)\b|$)",
            r"[Tt]hank you for applying.+?(.+?)\s+(?:at|with|-|–)\s+(.+?)(?:\s+(?:has|was|is|have)\b|$)",
            r"[Yy]ou applied for\s+(.+?)\s+(?:at|with)\s+(.+?)(?:\s+(?:has|was|is|have)\b|$)",
            r"[Rr]egarding your application.+?(?:at|with)\s+(.+?)(?:\s+(?:has|was|is|have)\b|$)",
        ],
        "body_patterns": [
            r"appl(?:ied|ying) (?:for|to)\s+(?:the\s+)?(?:position\s+of\s+)?(.+?)\s+(?:at|with)\s+(.+?)[.,\n]",
            r"application for\s+(?:the\s+)?(?:position\s+of\s+)?(.+?)\s+(?:at|with)\s+(.+?)[.,\n]",
            r"interest in\s+(?:the\s+)?(.+?)\s+(?:position|role|opportunity)\s+(?:at|with)\s+(.+?)[.,\n]",
            r"thank you for (?:your )?(?:interest|applying).+?(?:at|with)\s+(.+?)[.,\n]",
            r"[Pp]osition\s*:\s*(.+?)[\n\r]",
            r"[Cc]ompany\s*:\s*(.+?)[\n\r]",
            r"[Rr]ole\s*:\s*(.+?)[\n\r]",
            r"[Jj]ob\s+[Tt]itle\s*:\s*(.+?)[\n\r]",
            r"[Oo]rganization\s*:\s*(.+?)[\n\r]",
        ],
    },}


# ============================================================
#  ROLE GARBAGE PHRASES - Reject these as roles
# ============================================================

ROLE_GARBAGE_PHRASES = [
    "time and effort",
    "time you",
    "time & effort",
    "this time",
    "at this time",
    "exploring a",
    "interest in",
    "interest you",
    "applying to",
    "applying for",
    "your application",
    "your interest",
    "your candidacy",
    "your resume",
    "this opportunity",
    "this position",
    "our team",
    "our company",
    "our organization",
    "the opportunity",
    "the time",
    "the effort",
    "the process",
    "the role has been",
    "careful consideration",
    "careful review",
    "other candidates",
    "other applicants",
    "unfortunately",
    "regret to",
    "we appreciate",
    "we regret",
    "we wish you",
    "best of luck",
    "all the best",
    "good luck",
    "wish you well",
    "not been selected",
    "not selected",
    "not moving forward",
    "move forward with",
    "moved forward with",
    # LinkedIn body false-match patterns
    "applied on",
    "more success",
    "view similar",
    "next steps",
    "take these",
    "view job",
    "careers at",
    # Generic single-word false roles
    "careers",
    "suitable",
    "opportunity",
    "update",
    "status",
    "notification",
    "confirmation",
]


def _is_role_garbage(text):
    """Return True if text looks like rejection filler, not a real role."""
    if not text:
        return True
    low = text.lower().strip()
    # Check against known garbage phrases
    for phrase in ROLE_GARBAGE_PHRASES:
        if phrase in low:
            return True
    # Too many words for a role title (typically max 6-8 words)
    if len(low.split()) > 10:
        return True
    # Must contain at least one letter
    if not any(c.isalpha() for c in low):
        return True
    # Too short - single letter or 1-2 char "roles" are garbage
    if len(low) <= 2:
        return True
    # Single capitalised word with NO job-title keyword → likely a company
    # fragment or name, not a role (e.g. "Turbotech", "Barclays")
    words = low.split()
    if len(words) == 1 and text[0:1].isupper() and not _has_job_title_keyword(text):
        return True
    return False


# ============================================================
#  COMPANY GARBAGE PHRASES - Reject these as company names
# ============================================================

COMPANY_GARBAGE_PHRASES = [
    "your application",
    "at this time",
    "this time",
    "this opportunity",
    "this position",
    "this role",
    "the position",
    "the role",
    "the opportunity",
    "the process",
    "the team",
    "our team",
    "our company",
    "our organization",
    "careful consideration",
    "careful review",
    "unfortunately",
    "regret to",
    "we appreciate",
    "we regret",
    "we have decided",
    "not to progress",
    "not moving forward",
    "move forward",
    "other candidates",
    "best of luck",
    "all the best",
    "good luck",
    "dear candidate",
    "dear applicant",
    "thank you for",
    "thanks for",
    "time and effort",
    # Sender display names — never a real company
    "jobs-noreply",
    "noreply",
    "no-reply",
    "do-not-reply",
    "donotreply",
    "do_not_reply",
    "mailer",
    "notifications",
    "job-alerts",
    "indeedapply",
]


def _is_company_garbage(text):
    """Return True if text looks like rejection filler, not a real company."""
    if not text:
        return True
    low = text.lower().strip()
    for phrase in COMPANY_GARBAGE_PHRASES:
        if phrase in low:
            return True
    # Too many words for a company name
    if len(low.split()) > 8:
        return True
    # Too short (single letter, 1-2 chars)
    if len(low) <= 2:
        return True
    # URL fragments that got extracted as company names
    url_garbage = {"www", "com", "net", "org", "io", "co", "us", "uk", "in",
                   "http", "https", "html", "htm", "php", "asp", "jsp",
                   "mailto", "email", "noreply", "donotreply", "no-reply",
                   "mail", "e", "web", "accounts", "notifications"}
    if low in url_garbage:
        return True
    # Must contain at least one letter
    if not any(c.isalpha() for c in low):
        return True
    return False


# ============================================================
#  KNOWN COMPANY NAME MAPPINGS (proper capitalization)
# ============================================================

KNOWN_COMPANY_NAMES = {
    "ibm": "IBM",
    "hp": "HP",
    "jpmorgan": "JPMorgan",
    "hsbc": "HSBC",
    "kpmg": "KPMG",
    "pwc": "PwC",
    "ey": "EY",
    "sap": "SAP",
    "hcl": "HCL",
    "tcs": "TCS",
    "wipro": "Wipro",
    "dxc": "DXC",
    "ubs": "UBS",
    "rbs": "RBS",
    "aig": "AIG",
    "bny": "BNY",
    "att": "AT&T",
    "ge": "GE",
    "bmw": "BMW",
    "dhl": "DHL",
    "ups": "UPS",
    "aws": "AWS",
    "gcp": "GCP",
}


# ============================================================
#  JOB TITLE KEYWORDS — a real role should contain at least one
# ============================================================

JOB_TITLE_KEYWORDS = [
    # Core titles
    "engineer", "developer", "analyst", "manager", "designer",
    "scientist", "architect", "consultant", "administrator",
    "specialist", "coordinator", "director", "lead", "head",
    "programmer", "tester", "intern", "trainee", "apprentice",
    "executive", "officer", "associate", "assistant", "fellow",
    # Tech roles
    "devops", "sre", "mlops", "qa", "sdet",
    "frontend", "backend", "fullstack", "full-stack", "full stack",
    # Domains
    "data", "software", "hardware", "network", "cloud", "security",
    "product", "project", "program", "scrum",
    "web", "mobile", "ios", "android", "embedded",
    "machine learning", "ai ", "artificial intelligence",
    "devops", "devsecops", "platform",
    # Business roles
    "marketing", "sales", "business", "finance", "accounting",
    "hr", "human resource", "recruiter", "talent",
    "support", "operations", "logistics",
    # Other
    "research", "professor", "lecturer", "teacher",
    "writer", "editor", "content",
    "technician", "mechanic", "electrician",
    "pyspark", "python", "java", "sql", "etl", "integration",
    "tableau", "power bi", "snowflake", "databricks",
    "warehouse", "pipeline", "bi ", "reporting",
]


def _is_sender_display_name(text):
    """Return True if text looks like an email sender display name, not a company."""
    if not text:
        return True
    low = text.lower().strip()
    sender_patterns = [
        "noreply", "no-reply", "no_reply", "donotreply", "do-not-reply",
        "do_not_reply", "mailer", "jobs-noreply", "job-alerts",
        "notifications", "indeedapply", "notification",
    ]
    for pat in sender_patterns:
        if pat in low:
            return True
    # Pattern: ends with or is a bare email-like token
    if "@" in low:
        return True
    return False


def _has_job_title_keyword(text):
    """Return True if text contains at least one job-title keyword."""
    if not text:
        return False
    low = " " + text.lower().strip() + " "
    for kw in JOB_TITLE_KEYWORDS:
        if kw in low:
            return True
    return False


def _looks_like_company_not_role(text):
    """Return True if text looks more like a company name than a job role.
    
    Heuristic: multi-word capitalised name with NO job-title keywords
    is almost certainly a company name (e.g. 'Turbotech Global Solutions').
    """
    if not text:
        return False
    text = text.strip()
    # If it contains job title keywords, it's a role
    if _has_job_title_keyword(text):
        return False
    # Single word — ambiguous, don't swap
    words = text.split()
    if len(words) < 2:
        return False
    # Multi-word with mostly capitalised words and no job keywords → company
    cap_count = sum(1 for w in words if w[0:1].isupper())
    if cap_count >= len(words) * 0.6:
        return True
    return False


def _fix_company_name(name):
    """Fix known company name capitalizations."""
    if not name:
        return name
    low = name.lower().strip()
    if low in KNOWN_COMPANY_NAMES:
        return KNOWN_COMPANY_NAMES[low]
    return name


def _clean_role(text):
    """Post-process an extracted role to strip job IDs, suffixes, and trailing junk."""
    if not text:
        return text
    # Strip leading job requisition IDs: JR-0000070329, R-232719, REQ-12345, etc.
    text = re.sub(r'^[A-Z]{1,4}[-]\d{3,}\s*', '', text).strip()
    # Strip leading pure-numeric job IDs: "69706 - " or "12345 -"
    text = re.sub(r'^\d{3,}\s*[-\u2013]\s*', '', text).strip()
    # Strip "(Open)", "(Closed)", "(Filled)", etc. - with or without closing paren
    text = re.sub(r'\s*\((?:Open|Closed|Filled|Active|Inactive|Draft|Expired)\)?\s*', '', text, flags=re.IGNORECASE).strip()
    # Strip leading phrasing noise: "coding challenge for the", "online test for", etc.
    text = re.sub(r'^(?:coding\s+(?:challenge|test)|online\s+(?:assessment|test)|aptitude\s+test|technical\s+test)\s+(?:for\s+(?:the\s+)?)?', '', text, flags=re.IGNORECASE).strip()
    # Truncate at sentence boundary - period/excl followed by space + capital or common follow words
    text = re.split(r'\s*[.!]\s+(?=[A-Z]|Unfortunately|We |However|Please|Thank|Currently)', text, maxsplit=1)[0].strip()
    # Strip trailing "position", "role", "opening", etc.
    text = re.sub(r'\s+(?:position|role|opening)\s*$', '', text, flags=re.IGNORECASE).strip()
    # Strip trailing periods, commas, parens, etc.
    text = text.strip(' .-,;:"\'/()[]')
    # Balance parentheses: if opening paren without closing, add it
    if '(' in text and ')' not in text:
        text += ')'
    return text


# ============================================================
#  HELPERS
# ============================================================

def _strip_html(text):
    """Aggressively strip HTML / CSS from text."""
    if not text:
        return ""
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\{[^}]*\}", " ", text)
    text = re.sub(r"[.#][a-zA-Z_][\w-]*\s*\{", " ", text)
    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _clean(text):
    """Clean a single extracted value (company / role)."""
    if not text:
        return ""
    text = _strip_html(text)
    text = text.strip(" .-,;:\"'/[]")
    # Only strip outer parens if unbalanced
    while text.startswith('(') and ')' not in text:
        text = text[1:].strip()
    while text.endswith(')') and '(' not in text:
        text = text[:-1].strip()
    if _is_garbage(text):
        return ""
    return text[:150]


def _is_garbage(text):
    """Return True if text looks like HTML/CSS residue, not real data."""
    if not text:
        return True
    if len(text) > 150:
        return True
    if re.search(r"[{};]|color\s*:|font-|background|margin|padding|display\s*:", text, re.IGNORECASE):
        return True
    alnum = sum(c.isalnum() or c.isspace() for c in text)
    if len(text) > 5 and alnum / len(text) < 0.6:
        return True
    stripped = re.sub(r"[\s\-/]", "", text)
    if stripped.isdigit():
        return True
    if re.match(r"^\d+$", text.strip()):
        return True
    return False


# ============================================================
#  CORE LOGIC
# ============================================================

def identify_platform(sender_email):
    """Return platform name if sender matches a known pattern, else None."""
    sender_lower = sender_email.lower().strip()
    for platform, cfg in PLATFORM_PATTERNS.items():
        for addr in cfg["senders"]:
            if addr in sender_lower:
                return platform
    return None


def _is_confirmation_email(subject, body_preview):
    """Return True only if the email is an actual application confirmation."""
    combined = (subject + " " + body_preview).lower()
    return any(kw in combined for kw in CONFIRMATION_KEYWORDS)


def _is_rejection_email(subject, body_preview):
    """Return True if the email is a rejection / not-selected notification."""
    combined = (subject + " " + body_preview).lower()
    return any(kw in combined for kw in REJECTION_KEYWORDS)


def _is_interview_email(subject, body_preview):
    """Return True if the email is an interview invitation or next-step notice."""
    combined = (subject + " " + body_preview).lower()
    return any(kw in combined for kw in INTERVIEW_KEYWORDS)


def _is_assessment_email(subject, body_preview):
    """Return True if the email is an assessment/test invitation."""
    combined = (subject + " " + body_preview).lower()
    return any(kw in combined for kw in ASSESSMENT_KEYWORDS)


# Map ATS sender domains to their proper platform names
ATS_DOMAIN_TO_PLATFORM = {
    "myworkday.com": "Workday",
    "myworkdayjobs.com": "Workday",
    "workday.com": "Workday",
    "wd3.myworkday.com": "Workday",
    "wd5.myworkday.com": "Workday",
    "greenhouse.io": "Greenhouse",
    "lever.co": "Lever",
    "icims.com": "iCIMS",
    "smartrecruiters.com": "SmartRecruiters",
    "brassring.com": "BrassRing",
    "taleo.net": "Taleo",
    "successfactors.com": "SuccessFactors",
    "workable.com": "Workable",
    "ashbyhq.com": "Ashby",
    "bamboohr.com": "BambooHR",
    "jobvite.com": "Jobvite",
    "phenom.com": "Phenom",
    "eightfold.ai": "Eightfold",
}


def _detect_ats_platform(sender):
    """Return ATS platform name if sender is from a known ATS domain, else None."""
    sender_lower = sender.lower()
    for domain, platform_name in ATS_DOMAIN_TO_PLATFORM.items():
        if domain in sender_lower:
            return platform_name
    return None


def _is_from_trusted_job_domain(sender):
    """Return True if the sender is from a known ATS/recruitment platform."""
    return _detect_ats_platform(sender) is not None


def _should_reject(subject):
    """Return True if the subject matches a known digest/alert pattern."""
    return bool(_REJECT_RE.search(subject))


def _extract_from_subject(subject, platform):
    """Try to extract role and company from the subject line."""
    result = {"company": None, "role": None}
    patterns = []
    if platform and platform in PLATFORM_PATTERNS:
        patterns = PLATFORM_PATTERNS[platform]["subject_patterns"]
    for pat in patterns:
        m = re.search(pat, subject, re.IGNORECASE)
        if m:
            gd = m.groupdict()
            if gd:
                # Named groups — use them directly
                if gd.get("company"):
                    result["company"] = _clean(gd["company"])
                if gd.get("role"):
                    result["role"] = _clean(gd["role"])
            else:
                # Positional groups (legacy / non-LinkedIn platforms)
                groups = m.groups()
                if len(groups) >= 2:
                    result["role"] = _clean(groups[0])
                    result["company"] = _clean(groups[1])
                elif len(groups) == 1:
                    result["role"] = _clean(groups[0])
            break
    return result


def _extract_from_body(body, platform):
    """Try to extract role, company, location from the email body."""
    result = {"company": None, "role": None, "location": None}
    clean_body = _strip_html(body)
    patterns = []
    if platform and platform in PLATFORM_PATTERNS:
        patterns = PLATFORM_PATTERNS[platform]["body_patterns"]
    for pat in patterns:
        m = re.search(pat, clean_body, re.IGNORECASE)
        if m:
            gd = m.groupdict()
            if gd:
                # Named groups — use them directly
                if gd.get("role"):
                    result["role"] = _clean(gd["role"])
                if gd.get("company"):
                    result["company"] = _clean(gd["company"])
                if result["role"] or result["company"]:
                    break
            else:
                # Positional groups (legacy)
                groups = m.groups()
                if len(groups) >= 2:
                    result["role"] = _clean(groups[0])
                    result["company"] = _clean(groups[1])
                    break
                elif len(groups) == 1:
                    val = _clean(groups[0])
                    if val:
                        if not result["role"]:
                            result["role"] = val
                        elif not result["company"]:
                            result["company"] = val
    for pat in [
        r"[Ll]ocation\s*:\s*(.+?)[\n\r]",
        r"[Ll]ocated\s+in\s+(.+?)[\.\n]",
        r"[Jj]ob\s+[Ll]ocation\s*:\s*(.+?)[\n\r]",
    ]:
        m = re.search(pat, clean_body)
        if m:
            loc = _clean(m.group(1))
            if loc and not _is_garbage(loc):
                result["location"] = loc
            break
    return result


def _extract_company_generic(subject, body_preview, sender=""):
    """Try to extract company name from generic rejection / update emails
    that don't come from known job platforms (e.g., noreply@barclays.com)."""

    def _clean_company(val):
        """Strip trailing noise from company name."""
        if not val:
            return ""
        val = _clean(val)
        if not val:
            return ""
        # Strip trailing ". Currently", ". We", ". Thank" etc.
        val = re.split(r'\.\s+(?:Currently|We |However|Please|Thank|Unfortunately)', val, maxsplit=1)[0].strip()
        # Strip trailing punctuation
        val = val.strip(' .-,;:"\'/()[]')
        if _is_company_garbage(val):
            return ""
        return val

    # Try subject first (shorter, more precise)
    subject_patterns = [
        r"(?:at|with|from)\s+([A-Z][A-Za-z&\s]{1,40})$",
        r"(?:at|with|from)\s+([A-Z][A-Za-z&\s]{1,40})(?:\s*[-\u2013:])",
    ]
    for pat in subject_patterns:
        m = re.search(pat, subject)
        if m:
            val = _clean_company(m.group(1))
            if val and len(val) > 2 and len(val) < 50:
                return val

    # Try body patterns
    body_patterns = [
        r"(?:interest in|applying to|applied (?:to|at|with))\s+([A-Z][A-Za-z&\s]{1,50})[\.\n,]",
        r"(?:position|role|opportunity)\s+(?:at|with)\s+([A-Z][A-Za-z&\s]{1,50})[\.\n,]",
        r"(?:at|from|with)\s+([A-Z][A-Za-z&\s]{1,40})(?:\s+(?:has|is|was|we))\b",
    ]
    for pat in body_patterns:
        m = re.search(pat, body_preview)
        if m:
            val = _clean_company(m.group(1))
            if val and len(val) > 2 and len(val) < 50:
                return val

    # Fallback: try to get company from the sender domain
    # e.g. "noreply@barclays.com" -> "Barclays"
    sender_match = re.search(r"@([a-zA-Z0-9-]+)\.", sender or subject)
    if sender_match:
        domain = sender_match.group(1).lower()
        # Skip generic email providers AND job platforms (Workday, etc.)
        skip = {
            "gmail", "yahoo", "outlook", "hotmail", "icloud", "protonmail", "mail",
            "myworkday", "myworkdayjobs", "workday", "wd3", "wd5",
            "linkedin", "naukri", "indeed", "glassdoor", "ziprecruiter",
            "monster", "wellfound", "instahyre", "internshala",
            "greenhouse", "lever", "icims", "smartrecruiters",
            "brassring", "taleo", "successfactors", "workable", "ashbyhq", "bamboohr",
            "jobvite", "phenom", "eightfold",
        }
        if domain not in skip:
            return _fix_company_name(domain.capitalize())
        else:
            # For ATS domains, the username part may be the company
            # e.g. "barclays@myworkday.com" -> "Barclays"
            user_match = re.search(r"<?([a-zA-Z][a-zA-Z0-9._-]*)@", sender or "")
            if user_match:
                username = user_match.group(1).lower()
                # Skip generic usernames
                generic_users = {
                    "noreply", "no-reply", "do-not-reply", "donotreply",
                    "notifications", "notify", "info", "support", "admin",
                    "careers", "jobs", "talent", "recruit", "hr", "hiring",
                    "mailer", "apply", "system", "service", "alert",
                    "jobs-noreply", "no-reply-jobs", "job-alerts",
                    "linkedin", "indeedapply", "noreply-glassdoor",
                }
                if username not in generic_users and len(username) > 2:
                    return _fix_company_name(username.capitalize())
    return ""


def _extract_role_generic(subject, body_preview):
    """Try to extract role/position from generic emails."""
    patterns = [
        # "interview for the Software Developer role at" or "interview for the position of X at"
        r"interview for (?:the\s+)?(?:position of\s+)?(.+?)\s+(?:role\s+)?(?:at|with)\b",
        # "application for Software Engineer at Company"
        r"(?:application for|applied (?:for|to))\s+(?:the\s+)?(?:position\s+of\s+)?(.+?)\s+(?:at|with)\b",
        # "position of: Software Engineer" or "role: Data Analyst"
        r"(?:position|role|job|opening)\s*(?:of|:|for|as)\s+(.+?)(?:[.,;\n]|\s+(?:at|with|in)\b)",
        # "the Software Developer role at" / "the Software Engineer position at"
        r"(?:the|a|an)\s+(.+?)\s+(?:role|position|opening|opportunity)\s+(?:at|with|in)\b",
        # "for the Software Engineer position"
        r"for (?:the|a|an)\s+(.+?)\s+(?:position|role|opening)\b",
        # "as a Software Engineer at" / "as Software Developer with"
        r"as\s+(?:a|an)\s+(.+?)\s+(?:at|with|in)\b",
        # "Software Engineer - Company" / "Data Scientist | Company"
        r"^(.+?)\s+[-|]\s+[A-Z]",
        # "Your application: Software Engineer"
        r"your application:\s+(.+?)(?:[.,;\n]|$)",
        # "Job title: Software Engineer"
        r"job title:\s+(.+?)(?:[.,;\n]|\s+(?:at|with|in)\b)",
        # "Role title: Data Analyst"
        r"role title:\s+(.+?)(?:[.,;\n]|\s+(?:at|with|in)\b)",
        # Common role titles standalone
        r"(?:senior|junior|lead|principal|staff)\s+(?:software|full[\s-]?stack|frontend|front[\s-]?end|backend|back[\s-]?end|mobile|ios|android|devops|cloud|data|machine[\s-]?learning|ai|ml)\s+(?:engineer|developer|architect)",
        r"(?:data|business|financial|market|systems?|security|quality)\s+analyst",
        r"(?:product|project|program|engineering|technical)\s+manager",
        r"(?:ui|ux|product|graphic|web)\s+designer",
        r"(?:intern|internship|trainee|associate|consultant|specialist|coordinator)",
    ]
    # Search subject and body separately to avoid cross-matching
    for text in [subject, body_preview]:
        for pat in patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                val = _clean(m.group(1))
                # Make sure the extracted role doesn't contain "at Company" residue
                at_split = re.split(r'\s+at\s+', val, maxsplit=1, flags=re.IGNORECASE)
                val = at_split[0].strip()
                if val and len(val) > 1 and len(val) < 80 and not _is_role_garbage(val):
                    return val
    return ""


def parse_email(sender, subject, body, date_str):
    """
    Parse a single email and return application details dict, or None.
    Detects: application confirmations, rejections, and interview invites.
    Returns a dict with an 'email_type' field: 'applied', 'rejected', or 'interview'.
    """
    platform = identify_platform(sender)

    # Quick reject: digests / alerts / newsletters
    if _should_reject(subject):
        return None

    body_preview = _strip_html(body)[:800]

    # Determine email type
    is_confirm = _is_confirmation_email(subject, body_preview)
    is_reject = _is_rejection_email(subject, body_preview)
    is_interview = _is_interview_email(subject, body_preview)
    is_assessment = _is_assessment_email(subject, body_preview)

    if not is_confirm and not is_reject and not is_interview and not is_assessment:
        # FALLBACK: If from a trusted ATS domain (Workday, Greenhouse, etc.),
        # treat it as an application email even without exact keyword match
        if _is_from_trusted_job_domain(sender):
            is_confirm = True
        else:
            return None

    # Decide status and email_type (priority: reject > assessment > interview > applied)
    if is_reject:
        status = "Rejected"
        email_type = "rejected"
    elif is_assessment:
        status = "Assessment"
        email_type = "assessment"
    elif is_interview:
        status = "Interview Scheduled"
        email_type = "interview"
    else:
        status = "Applied"
        email_type = "applied"

    # Extract details from platform-specific patterns
    subj_data = _extract_from_subject(subject, platform)
    body_data = _extract_from_body(body, platform)

    # Prefer subject company when available (subjects are shorter, more precise)
    # Fall back to body company only when subject has no company
    company = subj_data.get("company") or body_data.get("company") or ""
    # Prefer body role (usually more detailed), fall back to subject role
    role = body_data.get("role") or subj_data.get("role") or ""
    location = body_data.get("location") or ""

    # For non-platform emails (Barclays, Google, etc.) try generic company extraction
    if not company:
        company = _extract_company_generic(subject, body_preview, sender)

    # Specific role extraction from body (e.g., IBM "role of 69706 - Data Engineer")
    if company and not role:
        specific_role_pats = [
            r"role of\s+(?:\d+\s*[-\u2013]\s*)?(.+?)\s+(?:with|at)\b",
            r"Ref:\s*(?:\d+\s*[-\u2013]\s*)?(.+?)\s+(?:Dear|\n)",
            r"applied (?:to|for) (?:the )?(?:role of\s+)?(?:\d+\s*[-\u2013]\s*)?(.+?)\s+(?:at|with)\s",
        ]
        for pat in specific_role_pats:
            m = re.search(pat, body_preview, re.IGNORECASE)
            if m:
                val = _clean_role(_clean(m.group(1)))
                if val and not _is_role_garbage(val) and len(val) > 2:
                    role = val
                    break

    # Company-anchored role extraction (most reliable when company is known)
    # Always try when company is known — anchored results use context and are
    # more accurate than generic body patterns. Prefer longer anchored result.
    if company:
        company_esc = re.escape(company)
        for anchor_pat in [
            rf"[Yy]ou applied for\s+(.+?)\s+(?:at\s+)?{company_esc}",
            rf"applied for\s+(?:the\s+)?(.+?)\s+(?:at\s+)?{company_esc}",
            rf"application for\s+(?:the\s+)?(.+?)\s+(?:at\s+)?{company_esc}",
            rf"sent to\s+{company_esc}\s+(.+?)\s+{company_esc}",
            rf"{company_esc}\s+(.+?)\s+{company_esc}",
        ]:
            m = re.search(anchor_pat, body_preview, re.IGNORECASE)
            if m:
                val = _clean(m.group(1))
                if val and not _is_role_garbage(val) and len(val) > 1:
                    anchored_role = _clean_role(val)
                    # Use anchored role if we have no role or anchored is longer
                    if not role or len(anchored_role) > len(role):
                        role = anchored_role
                    break

    # Generic role extraction (last resort)
    if not role:
        role = _extract_role_generic(subject, body_preview)

    # Post-process: clean up role (strip job IDs, suffixes, rejection text)
    role = _clean_role(role) if role else role

    # Post-process: reject sender display names as company (e.g. "Jobs-noreply")
    if company and _is_sender_display_name(company):
        company = ""

    # Post-process: reject garbage company names (rejection filler text)
    if company and _is_company_garbage(company):
        # Try to re-extract from sender domain as fallback
        company = _extract_company_generic("", "", sender)

    # Post-process: reject garbage role text
    if role and _is_role_garbage(role):
        role = ""

    # ---- ROLE / COMPANY SWAP ----
    # If the extracted "role" looks like a company name (multi-word capitalised
    # with NO job-title keywords) and company is empty, swap them.
    if role and not company and _looks_like_company_not_role(role):
        company = role
        role = ""
    # If we have both, but the role has no job-title keywords and looks like
    # a company, while the company has job-title keywords (parser swapped them)
    if role and company and _looks_like_company_not_role(role) and _has_job_title_keyword(company):
        role, company = company, role

    # Post-process: fix known company name capitalizations
    company = _fix_company_name(company) if company else company

    # Must have at least a company for rejections/interviews
    if not company and not role:
        return None
    if _is_garbage(company) and _is_garbage(role):
        return None

    company = company or "Unknown Company"
    role = role or "Unknown Role"

    # Determine platform: known platform > ATS detection > Company Website
    if not platform:
        platform = _detect_ats_platform(sender) or "Company Website"

    return {
        "company": company,
        "role": role,
        "platform": platform,
        "status": status,
        "email_type": email_type,
        "location": location,
        "applied_date": date_str,
        "notes": f"Auto-imported from Gmail ({sender})",
    }
