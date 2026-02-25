#!/usr/bin/env python3
"""
B12 application submission script for GitHub Actions / CI
"""
from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.showtraceback = lambda *args, **kwargs: None
import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone
import requests


# ──────────────────────────────────────────────────────────────────────────────
# Configuration – only these should be customized
# ──────────────────────────────────────────────────────────────────────────────

NAME = "APARNA NALGONDA"
EMAIL = "aparnaneshani@gmail.com"
RESUME_LINK = "https://www.linkedin.com/in/aparna511"          
REPOSITORY_LINK = os.getenv("GITHUB_REPOSITORY_URL", "https://github.com/aparna511")

# For GitHub Actions – will be auto-detected in most cases
ACTION_RUN_LINK = os.getenv("GITHUB_SERVER_URL", "https://github.com") + "/" + \
                  os.getenv("GITHUB_REPOSITORY", "aparna511/Submit-B12") + "/actions/runs/" + \
                  os.getenv("GITHUB_RUN_ID", "unknown")

SIGNING_SECRET = b"hello-there-from-b12"   # kept as bytes for HMAC

# ──────────────────────────────────────────────────────────────────────────────
# Main logic
# ──────────────────────────────────────────────────────────────────────────────

def main():
    # 1. Current UTC time in ISO 8601 with milliseconds and Z
    now = datetime.now(timezone.utc)
    timestamp = now.isoformat(timespec="milliseconds").replace("+00:00", "Z")

    # 2. Prepare payload – keys MUST be sorted alphabetically
    payload = {
        "action_run_link": ACTION_RUN_LINK,
        "email": EMAIL,
        "name": NAME,
        "repository_link": REPOSITORY_LINK,
        "resume_link": RESUME_LINK,
        "timestamp": timestamp,
    }

    # 3. Create compact JSON (no extra whitespace, sorted keys)
    json_payload = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    json_bytes = json_payload.encode("utf-8")

    # 4. Compute HMAC-SHA256 signature
    signature = hmac.new(
        key=SIGNING_SECRET,
        msg=json_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Signature-256": f"sha256={signature}",
    }

    # 5. Send POST request
    url = "https://b12.io/apply/submission"
    try:
        resp = requests.post(url, data=json_bytes, headers=headers, timeout=15)
        resp.raise_for_status()

        result = resp.json()
        if result.get("success") is True:
            receipt = result.get("receipt", "no-receipt-returned")
            print("Submission successful!")
            print(f"Receipt: {receipt}")
            print("\nFull response:", json.dumps(result, indent=2))
            return 0
        else:
            print("Server responded, but success=false", file=sys.stderr)
            print(json.dumps(result, indent=2), file=sys.stderr)
            return 1

    except requests.RequestException as e:
        print(f"Failed to submit application: {e}", file=sys.stderr)
        if hasattr(e.response, "text"):
            print("Response body:", e.response.text, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
