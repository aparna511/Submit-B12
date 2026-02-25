#!/usr/bin/env python3
"""
B12 application submission script for GitHub Actions (or other CI)
Submits application with HMAC-SHA256 signature
"""

import os
import sys
import json
import hashlib
import hmac
import time
from datetime import datetime, timezone
import requests





SIGNING_SECRET = "hello-there-from-b12"           

ENDPOINT = "https://b12.io/apply/submission"



NAME          = os.environ.get("APPLICANT_NAME",         secrets.APPLICANT_NAME)                   
EMAIL         = os.environ.get("APPLICANT_EMAIL",        secrets.APPLICANT_EMAIL)         
RESUME_LINK   = os.environ.get("RESUME_LINK",            secrets.RESUME_LINK)                        
REPO_LINK     = os.environ.get("GITHUB_REPOSITORY_URL",  os.environ.get("GITHUB_SERVER_URL", "https://github.com") + "/" + os.environ.get("GITHUB_REPOSITORY", ""))


RUN_ID        = os.environ.get("GITHUB_RUN_ID",          "")
RUN_ATTEMPT   = os.environ.get("GITHUB_RUN_ATTEMPT",     "1")
ACTION_RUN_LINK = (
    f"{os.environ.get('GITHUB_SERVER_URL', 'https://github.com')}/"
    f"{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/{RUN_ID}"
    if RUN_ID else
    "https://github.com/placeholder/repo/actions/runs/unknown"
)


def get_iso_timestamp() -> str:
    """Return current time in ISO 8601 with millisecond precision and Z suffix"""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def create_canonical_payload() -> dict:
    return {
        "action_run_link": ACTION_RUN_LINK,
        "email":           EMAIL,
        "name":            NAME,
        "repository_link": REPO_LINK,
        "resume_link":     RESUME_LINK,
        "timestamp":       get_iso_timestamp(),
    }


def canonical_json(d: dict) -> bytes:
    """
    Create compact, alphabetically sorted JSON bytes (exactly as B12 expects)
    """
    return json.dumps(
        d,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False
    ).encode("utf-8")


def sign_payload(payload_bytes: bytes, secret: str) -> str:
    """HMAC-SHA256 of payload using the secret, return hex digest"""
    secret_bytes = secret.encode("utf-8")
    digest = hmac.new(secret_bytes, payload_bytes, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def main():
    if not all([NAME.strip(), EMAIL.strip(), RESUME_LINK.strip(), REPO_LINK.strip()]):
        print("ERROR: Missing required fields (name, email, resume_link, repository_link)", file=sys.stderr)
        sys.exit(1)

    payload_dict = create_canonical_payload()
    payload_bytes = canonical_json(payload_dict)

    signature = sign_payload(payload_bytes, SIGNING_SECRET)

    headers = {
        "Content-Type": "application/json",
        "X-Signature-256": signature,
    }

    print("Submitting application to B12...", flush=True)
    print(f"Payload timestamp: {payload_dict['timestamp']}", flush=True)
    print(f"Signature: {signature}", flush=True)

    try:
        r = requests.post(
            ENDPOINT,
            data=payload_bytes,
            headers=headers,
            timeout=15,
        )
        r.raise_for_status()

        response = r.json()
        if response.get("success") is True:
            receipt = response.get("receipt", "no-receipt-returned")
            print("\nSubmission successful!")
            print(f"Receipt: {receipt}")
            print("\nFull response:", json.dumps(response, indent=2))
            return 0
        else:
            print("Server responded success:false", file=sys.stderr)
            print(r.text, file=sys.stderr)
            return 1

    except requests.RequestException as e:
        print(f"Request failed: {e}", file=sys.stderr)
        if hasattr(e, "response") and e.response is not None:
            print(f"Status: {e.response.status_code}", file=sys.stderr)
            print(e.response.text, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
