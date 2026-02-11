"""Run a Gmail scan directly (bypasses HTTP timeout issues)."""
import sys
import json
sys.path.insert(0, ".")
from gmail_service import scan_emails

print("Starting scan...")
apps = scan_emails(days_back=60, max_results=500)

print(f"\n{'='*60}")
print(f"TOTAL PARSED: {len(apps)}")
print(f"{'='*60}")
for i, app in enumerate(apps, 1):
    print(f"  {i}. [{app.get('email_type','?'):10}] {app['company']:25} | {app['role']:40} | {app['platform']}")
print(f"{'='*60}")

# Save to file for inspection
with open("/tmp/scan_apps.json", "w") as f:
    json.dump(apps, f, indent=2)
print(f"Full results saved to /tmp/scan_apps.json")
