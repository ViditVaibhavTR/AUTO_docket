"""
Example: How to use the API Health Checker in your frontend

This file demonstrates various ways to integrate the API health checker
into your frontend application (Streamlit, Flask, FastAPI, etc.)
"""

import sys
from pathlib import Path

# Add project root to path (if needed)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from documentations.api_health_checker import check_api_health, APIHealthChecker


# ============================================================================
# Example 1: Simple Check (Basic Usage)
# ============================================================================
def example_simple_check():
    """Simplest way to check if API is running."""
    print("Example 1: Simple Check")
    print("-" * 50)

    if check_api_health():
        print("SUCCESS: API is running!")
        print("You can now proceed with API calls...")
    else:
        print("ERROR: API is not running!")
        print("Please start the API server: python app/run_api.py")

    print()


# ============================================================================
# Example 2: Verbose Check (With User Feedback)
# ============================================================================
def example_verbose_check():
    """Check with detailed output for users."""
    print("Example 2: Verbose Check")
    print("-" * 50)

    is_healthy = check_api_health(verbose=True)

    if is_healthy:
        print("\nProceeding with application startup...")
    else:
        print("\nCannot start application without API")
        sys.exit(1)

    print()


# ============================================================================
# Example 3: Using the Class Directly
# ============================================================================
def example_class_usage():
    """Using APIHealthChecker class for more control."""
    print("Example 3: Class Usage")
    print("-" * 50)

    checker = APIHealthChecker("http://localhost:8000", timeout=5)

    # Get detailed status
    is_healthy, message = checker.check(retries=3)

    print(f"Status: {'Healthy' if is_healthy else 'Unhealthy'}")
    print(f"Message: {message}")

    # Get full details
    details = checker.check_detailed()
    print(f"\nDetailed Information:")
    print(f"  URL: {details['url']}")
    print(f"  Endpoint: {details['endpoint']}")
    print(f"  Timestamp: {details['timestamp']}")
    print(f"  Healthy: {details['healthy']}")

    print()


# ============================================================================
# Example 4: Custom URL and Timeout
# ============================================================================
def example_custom_config():
    """Check API with custom configuration."""
    print("Example 4: Custom Configuration")
    print("-" * 50)

    # For production environment
    production_url = "https://api.yourdomain.com"

    # Check with custom timeout and retries
    is_healthy = check_api_health(
        base_url=production_url,
        timeout=10,  # 10 seconds timeout
        retries=5,   # Try 5 times
        verbose=True
    )

    print(f"Production API healthy: {is_healthy}")
    print()


# ============================================================================
# Example 5: Integration with Streamlit
# ============================================================================
def example_streamlit_integration():
    """Example of how to use in a Streamlit app."""
    print("Example 5: Streamlit Integration")
    print("-" * 50)
    print("\nIn your Streamlit app (app.py):")
    print("""
import streamlit as st
from documentations.api_health_checker import check_api_health

# Check API at startup
st.title("Docket Alert Application")

with st.spinner("Checking API connection..."):
    if not check_api_health():
        st.error("⚠️ API server is not running!")
        st.info("Please start the API server:")
        st.code("cd app && python run_api.py")
        st.stop()

st.success("✓ API is running")

# Continue with your app...
st.write("Welcome to Docket Alert!")
    """)
    print()


# ============================================================================
# Example 6: Retry with Exponential Backoff
# ============================================================================
def example_retry_logic():
    """Demonstrate retry logic with exponential backoff."""
    print("Example 6: Retry Logic")
    print("-" * 50)

    checker = APIHealthChecker()

    # Will retry 5 times with exponential backoff (1s, 2s, 4s, 8s, 16s)
    is_healthy, message = checker.check(retries=5, backoff=1.0)

    print(f"After retries: {message}")
    print()


# ============================================================================
# Example 7: Using in a Test Suite
# ============================================================================
def example_test_integration():
    """Example of using in pytest tests."""
    print("Example 7: Test Integration")
    print("-" * 50)
    print("\nIn your test file (test_api.py):")
    print("""
import pytest
from documentations.api_health_checker import APIHealthChecker

@pytest.fixture(scope="session", autouse=True)
def ensure_api_running():
    '''Ensure API is running before any tests.'''
    checker = APIHealthChecker()
    is_healthy = checker.check_simple()

    if not is_healthy:
        pytest.fail(
            "API is not running. Start with: python app/run_api.py"
        )

    print("\\n[OK] API is running - tests can proceed")
    return checker

def test_api_health(ensure_api_running):
    '''Test that API health check works.'''
    checker = ensure_api_running
    is_healthy = checker.check_simple()
    assert is_healthy, "API should be healthy"
    """)
    print()


# ============================================================================
# Example 8: Multiple Environment Support
# ============================================================================
def example_multi_environment():
    """Check different environments."""
    print("Example 8: Multiple Environment Support")
    print("-" * 50)

    environments = {
        "development": "http://localhost:8000",
        "staging": "https://api-staging.example.com",
        "production": "https://api.example.com"
    }

    for env_name, url in environments.items():
        print(f"\nChecking {env_name} environment...")
        checker = APIHealthChecker(url, timeout=3)
        is_healthy = checker.check_simple()

        status = "[OK]" if is_healthy else "[ERROR]"
        print(f"  {status} {url}")

    print()


# ============================================================================
# Example 9: Error Handling
# ============================================================================
def example_error_handling():
    """Proper error handling when API is down."""
    print("Example 9: Error Handling")
    print("-" * 50)

    checker = APIHealthChecker()
    is_healthy, message = checker.check()

    if not is_healthy:
        print(f"API Check Failed: {message}")

        # Different actions based on error type
        if "Cannot connect" in message:
            print("\nAction: Start the API server")
            print("  Command: python app/run_api.py")

        elif "timeout" in message:
            print("\nAction: Check if API is responding slowly")
            print("  - Check server logs")
            print("  - Check server resources (CPU, memory)")

        elif "HTTP" in message:
            print("\nAction: API returned an error")
            print("  - Check server logs for errors")
            print("  - Verify API is configured correctly")
    else:
        print(f"API is healthy: {message}")

    print()


# ============================================================================
# Run All Examples
# ============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("API Health Checker - Usage Examples")
    print("=" * 70)
    print()

    try:
        example_simple_check()
        example_verbose_check()
        example_class_usage()
        # example_custom_config()  # Uncomment if you have production URL
        example_streamlit_integration()
        example_retry_logic()
        example_test_integration()
        example_multi_environment()
        example_error_handling()

        print("=" * 70)
        print("All examples completed!")
        print("=" * 70)

    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
        sys.exit(0)
