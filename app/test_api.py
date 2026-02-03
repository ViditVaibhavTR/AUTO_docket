"""
Test script for the Docket Alert Automation API.
Demonstrates how to use the API endpoints.
"""

import time
from api_client import DocketAlertAPIClient


def main():
    """Test the API endpoints."""
    print("=" * 80)
    print("Docket Alert Automation API Test")
    print("=" * 80)

    # Initialize client
    client = DocketAlertAPIClient(base_url="http://127.0.0.1:8000")

    try:
        # Test 1: Health Check
        print("\n1. Testing Health Check...")
        health = client.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Version: {health['version']}")

        # Test 2: Get Docket Categories
        print("\n2. Getting Docket Categories...")
        categories = client.get_docket_categories()
        print(f"   Available categories: {len(categories['categories'])}")
        for cat, items in list(categories['categories'].items())[:2]:
            print(f"   - {cat}: {len(items)} items")

        # Test 3: Get States
        print("\n3. Getting Available States...")
        states = client.get_states()
        print(f"   Available states: {', '.join(states)}")

        # Test 4: Get Districts
        print("\n4. Getting Districts for California...")
        districts = client.get_districts("California")
        print(f"   Available districts: {', '.join(districts)}")

        # Test 5: Start Automation (commented out - requires browser)
        print("\n5. Starting Automation...")
        print("   NOTE: This will open a browser window")
        print("   Uncomment the code below to test full automation")

        # Uncomment to test full automation:
        """
        result = client.start_automation()
        session_id = result['session_id']
        print(f"   Session ID: {session_id}")
        print(f"   Status: {result['status']}")

        # Wait for user to be ready
        input("\n   Press Enter to continue with docket selection...")

        # Test 6: Select Docket
        print("\n6. Selecting Docket (California)...")
        docket_result = client.select_docket(
            session_id=session_id,
            category="Dockets by State",
            specific_docket="California"
        )
        print(f"   Status: {docket_result['status']}")
        print(f"   Message: {docket_result['message']}")

        # Test 7: Select District
        print("\n7. Selecting District (Central District)...")
        district_result = client.select_district(
            session_id=session_id,
            state="California",
            district="Central District"
        )
        print(f"   Status: {district_result['status']}")
        print(f"   Message: {district_result['message']}")

        # Test 8: Search Docket
        print("\n8. Searching for Docket Number...")
        search_result = client.search_docket(
            session_id=session_id,
            docket_number="1:25-CV-01815"
        )
        print(f"   Status: {search_result['status']}")
        print(f"   Message: {search_result['message']}")

        # Test 9: Create Alert
        print("\n9. Creating Docket Alert...")
        alert_result = client.create_alert(session_id=session_id)
        print(f"   Status: {alert_result['status']}")
        print(f"   Message: {alert_result['message']}")

        # Test 10: Complete Alert Setup
        print("\n10. Completing Alert Setup...")
        complete_result = client.complete_alert_setup(
            session_id=session_id,
            alert_name="Test Alert",
            alert_description="This is a test alert",
            user_email="test@example.com",
            frequency="daily",
            alert_times=["5am", "12pm"]
        )
        print(f"   Status: {complete_result['status']}")
        print(f"   Message: {complete_result['message']}")

        # Test 11: Cleanup Session
        print("\n11. Cleaning up session...")
        cleanup_result = client.cleanup_session(session_id=session_id)
        print(f"   Status: {cleanup_result['status']}")
        print(f"   Message: {cleanup_result['message']}")
        """

        print("\n" + "=" * 80)
        print("API Test Completed Successfully!")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure the API server is running:")
        print("  python run_api.py")


if __name__ == "__main__":
    main()
