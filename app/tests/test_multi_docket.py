"""
Test: Multi-docket automation — 2 dockets, California Southern District.

Docket 1: 3:26-CV-00397
Docket 2: 3:26-CV-00552

Usage:
    cd app
    python tests/test_multi_docket.py

The API server must already be running:
    python run_api.py
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api.api_client import DocketAlertAPIClient

BASE_URL = "http://127.0.0.1:8000"
USER_EMAIL = "vidit.vaibhav@thomsonreuters.com"

DOCKETS = [
    {
        "state": "California",
        "district": "Southern District",
        "docket_number": "3:26-CV-00397",
        "alert_name": "Alert CAs-1",
        "alert_description": "",
        "user_email": USER_EMAIL,
        "frequency": "daily",
        "alert_times": ["5am", "12pm", "3pm", "5pm"],
    },
    {
        "state": "California",
        "district": "Southern District",
        "docket_number": "3:26-CV-00552",
        "alert_name": "Alert CAs-2",
        "alert_description": "",
        "user_email": USER_EMAIL,
        "frequency": "daily",
        "alert_times": ["5am", "12pm", "3pm", "5pm"],
    },
]


def print_separator(char="=", width=70):
    print(char * width)


def main():
    print_separator()
    print("  Multi-Docket Automation Test — 2x California Southern District")
    print_separator()
    print(f"  Dockets:")
    for d in DOCKETS:
        print(f"    - {d['docket_number']}  ({d['state']} · {d['district']})")
    print(f"  Email : {USER_EMAIL}")
    print_separator()

    client = DocketAlertAPIClient(base_url=BASE_URL)
    session_id = None

    try:
        # ── 1. Health check ──────────────────────────────────────────────
        print("\n[1/3] Health check...")
        health = client.health_check()
        print(f"      Status  : {health['status']}")
        print(f"      Version : {health['version']}")

        # ── 2. Start automation session ──────────────────────────────────
        print("\n[2/3] Starting automation session (browser will open)...")
        start = client.start_automation()
        session_id = start["session_id"]
        print(f"      Session ID : {session_id}")
        print(f"      Status     : {start['status']}")

        # ── 3. Multi-docket processing ───────────────────────────────────
        print("\n[3/3] Running multi-docket processing...")
        print("      This navigates once to 'Select the state:' page,")
        print("      then opens a new tab for each additional docket.")
        print("      Please wait — this may take 60-120 seconds...\n")

        result = client.multi_process_dockets(
            session_id=session_id,
            dockets=DOCKETS
        )

        # ── Results ──────────────────────────────────────────────────────
        print_separator("-")
        print(f"  Overall status: {result['status'].upper()}")
        print_separator("-")
        for r in result["results"]:
            icon = "✓" if r["status"] == "success" else "✗"
            print(f"  {icon}  {r['docket_number']}  ({r['state']})")
            print(f"       Status  : {r['status']}")
            print(f"       Message : {r['message']}")
        print_separator("-")

    except Exception as e:
        print(f"\n  ERROR: {e}")
        print("\n  Make sure the API server is running:")
        print("      cd app && python run_api.py")

    finally:
        if session_id:
            print("\n  Cleaning up session...")
            try:
                cleanup = client.cleanup_session(session_id)
                print(f"  Cleanup: {cleanup['status']}")
            except Exception as e:
                print(f"  Cleanup failed: {e}")

    print_separator()


if __name__ == "__main__":
    main()
