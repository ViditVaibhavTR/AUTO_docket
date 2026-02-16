"""
API Health Checker Utility for Docket Alert Automation

This module provides utilities to check if the FastAPI backend is running and healthy.
Can be used as a standalone script or imported as a module.

Usage as module:
    from documentations.api_health_checker import check_api_health

    if check_api_health():
        print("API is running!")
    else:
        print("API is not running")

Usage as script:
    python documentations/api_health_checker.py
    python documentations/api_health_checker.py --url https://api.example.com
    python documentations/api_health_checker.py --quiet
"""

import requests
import time
import sys
from typing import Dict, Tuple, Optional


class APIHealthChecker:
    """Utility to check if the Docket Alert API is running."""

    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 5):
        """
        Initialize health checker.

        Args:
            base_url: Base URL of the API server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url
        self.timeout = timeout
        self.health_endpoint = f"{base_url}/health"

    def check(self, retries: int = 3, backoff: float = 1.0) -> Tuple[bool, str]:
        """
        Check if API is running with retry logic.

        Args:
            retries: Number of retry attempts (default: 3)
            backoff: Base seconds between retries (exponential backoff)

        Returns:
            Tuple of (is_healthy: bool, message: str)

        Example:
            >>> checker = APIHealthChecker()
            >>> is_healthy, message = checker.check()
            >>> print(f"API Status: {message}")
        """
        for attempt in range(retries):
            try:
                response = requests.get(self.health_endpoint, timeout=self.timeout)

                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status', 'unknown')
                    return True, f"[OK] API is running - Status: {status}"
                else:
                    return False, f"[ERROR] API returned HTTP {response.status_code}"

            except requests.ConnectionError:
                if attempt < retries - 1:
                    delay = backoff * (2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                    time.sleep(delay)
                    continue
                return False, "[ERROR] Cannot connect to API - Is the server running?"

            except requests.Timeout:
                if attempt < retries - 1:
                    delay = backoff * (2 ** attempt)
                    time.sleep(delay)
                    continue
                return False, f"[ERROR] API timeout after {self.timeout}s"

            except Exception as e:
                return False, f"[ERROR] Unexpected error: {str(e)}"

        return False, "[ERROR] API check failed after retries"

    def check_simple(self) -> bool:
        """
        Simple check - returns True if healthy, False otherwise.

        Returns:
            True if API is healthy, False otherwise

        Example:
            >>> checker = APIHealthChecker()
            >>> if checker.check_simple():
            ...     print("API is ready!")
        """
        is_healthy, _ = self.check(retries=1)
        return is_healthy

    def check_detailed(self) -> Dict[str, any]:
        """
        Detailed check - returns full status information.

        Returns:
            Dict with keys:
                - healthy (bool): Whether API is healthy
                - message (str): Status message
                - url (str): Base URL checked
                - endpoint (str): Full endpoint URL
                - timestamp (str): Time of check

        Example:
            >>> checker = APIHealthChecker()
            >>> status = checker.check_detailed()
            >>> print(f"Healthy: {status['healthy']}")
            >>> print(f"Message: {status['message']}")
        """
        is_healthy, message = self.check()

        return {
            "healthy": is_healthy,
            "message": message,
            "url": self.base_url,
            "endpoint": self.health_endpoint,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

    def check_verbose(self) -> bool:
        """
        Verbose check - prints colored output and returns status.

        Returns:
            True if healthy, False otherwise

        Example:
            >>> checker = APIHealthChecker()
            >>> checker.check_verbose()
            Checking API at http://localhost:8000...
            --------------------------------------------------
            ✓ API is running - Status: healthy
            ✓ API is ready to accept requests
            --------------------------------------------------
        """
        print(f"\nChecking API at {self.base_url}...")
        print("-" * 50)

        is_healthy, message = self.check()

        if is_healthy:
            print(f"\n{message}")
            print("\n[OK] API is ready to accept requests")
        else:
            print(f"\n{message}")
            print("\n[ERROR] API is not available")
            print("\nTo start the API server:")
            print("  cd app")
            print("  python run_api.py")

        print("-" * 50)
        return is_healthy


def check_api_health(
    base_url: str = "http://localhost:8000",
    timeout: int = 5,
    retries: int = 3,
    verbose: bool = False
) -> bool:
    """
    Convenience function to check API health.

    Args:
        base_url: Base URL of the API server (default: http://localhost:8000)
        timeout: Request timeout in seconds (default: 5)
        retries: Number of retry attempts (default: 3)
        verbose: Print verbose output (default: False)

    Returns:
        True if API is healthy, False otherwise

    Example:
        >>> # Simple check
        >>> if check_api_health():
        ...     print("API is running!")
        ... else:
        ...     print("API is not running")

        >>> # Verbose check
        >>> check_api_health(verbose=True)

        >>> # Custom URL
        >>> check_api_health(base_url="https://api.example.com")
    """
    checker = APIHealthChecker(base_url, timeout)

    if verbose:
        return checker.check_verbose()
    else:
        is_healthy, _ = checker.check(retries=retries)
        return is_healthy


# CLI Interface
if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(
        description="Check if the Docket Alert API is running",
        epilog="""
Examples:
  python api_health_checker.py
  python api_health_checker.py --url https://api.example.com
  python api_health_checker.py --quiet
  python api_health_checker.py --detailed
  python api_health_checker.py --timeout 10 --retries 5
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--url",
        default=os.getenv("API_URL", "http://localhost:8000"),
        help="API base URL (default: http://localhost:8000, or API_URL env var)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=5,
        help="Request timeout in seconds (default: 5)"
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Number of retry attempts (default: 3)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Quiet mode - no output, just exit code (0=healthy, 1=unhealthy)"
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed JSON output"
    )

    args = parser.parse_args()

    checker = APIHealthChecker(args.url, args.timeout)

    if args.detailed:
        # Detailed JSON output
        import json
        result = checker.check_detailed()
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["healthy"] else 1)

    elif args.quiet:
        # Quiet mode - just exit code
        is_healthy = checker.check_simple()
        sys.exit(0 if is_healthy else 1)

    else:
        # Verbose mode (default)
        is_healthy = checker.check_verbose()
        sys.exit(0 if is_healthy else 1)
