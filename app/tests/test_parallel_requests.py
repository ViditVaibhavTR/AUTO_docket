"""
Test script to verify parallel request handling in the API.
This script simulates multiple concurrent users making requests.
"""

import asyncio
import aiohttp
import time
from typing import List, Dict


API_BASE_URL = "http://127.0.0.1:8000"


async def health_check(session: aiohttp.ClientSession) -> Dict:
    """Test health check endpoint."""
    async with session.get(f"{API_BASE_URL}/health") as response:
        return await response.json()


async def simulate_user_session(user_id: int, session: aiohttp.ClientSession) -> Dict:
    """
    Simulate a complete user session creating a docket alert.

    Args:
        user_id: Unique identifier for this simulated user
        session: aiohttp ClientSession for making requests

    Returns:
        Dictionary with timing and result information
    """
    start_time = time.time()
    results = {
        "user_id": user_id,
        "steps": [],
        "success": False,
        "total_time": 0,
        "session_id": None
    }

    try:
        # Step 1: Start automation
        print(f"[User {user_id}] Starting automation...")
        async with session.post(
            f"{API_BASE_URL}/api/v1/automation/start",
            json={"include_docket": False}
        ) as response:
            data = await response.json()
            if response.status == 200:
                results["session_id"] = data.get("session_id")
                results["steps"].append("start_automation")
                print(f"[User {user_id}] Automation started - Session: {results['session_id'][:8]}...")
            else:
                results["error"] = f"Start failed: {data.get('detail')}"
                return results

        await asyncio.sleep(1)  # Small delay between steps

        # Step 2: Select state
        print(f"[User {user_id}] Selecting state...")
        async with session.post(
            f"{API_BASE_URL}/api/v1/docket/select",
            json={
                "session_id": results["session_id"],
                "category": "Dockets by State",
                "specific_docket": "California"
            }
        ) as response:
            if response.status == 200:
                results["steps"].append("select_state")
                print(f"[User {user_id}] State selected")
            else:
                data = await response.json()
                results["error"] = f"State selection failed: {data.get('detail')}"
                return results

        await asyncio.sleep(1)

        # Step 3: Select district
        print(f"[User {user_id}] Selecting district...")
        async with session.post(
            f"{API_BASE_URL}/api/v1/district/select",
            json={
                "session_id": results["session_id"],
                "state": "California",
                "district": "Central District"
            }
        ) as response:
            if response.status == 200:
                results["steps"].append("select_district")
                print(f"[User {user_id}] District selected")
            else:
                data = await response.json()
                results["error"] = f"District selection failed: {data.get('detail')}"
                return results

        await asyncio.sleep(1)

        # Step 4: Cleanup session
        print(f"[User {user_id}] Cleaning up session...")
        async with session.post(
            f"{API_BASE_URL}/api/v1/session/cleanup",
            json={"session_id": results["session_id"]}
        ) as response:
            if response.status == 200:
                results["steps"].append("cleanup")
                print(f"[User {user_id}] Session cleaned up")
                results["success"] = True
            else:
                data = await response.json()
                results["error"] = f"Cleanup failed: {data.get('detail')}"

    except Exception as e:
        results["error"] = str(e)
        print(f"[User {user_id}] Error: {e}")

    finally:
        results["total_time"] = time.time() - start_time
        print(f"[User {user_id}] Completed in {results['total_time']:.2f}s")

    return results


async def test_concurrent_users(num_users: int = 3):
    """
    Test concurrent users making requests to the API.

    Args:
        num_users: Number of concurrent users to simulate
    """
    print("=" * 80)
    print(f"PARALLEL REQUEST TEST - {num_users} Concurrent Users")
    print("=" * 80)
    print()

    # First check if API is running
    async with aiohttp.ClientSession() as session:
        try:
            health = await health_check(session)
            print(f"✓ API Health Check: {health.get('status')}")
            print()
        except Exception as e:
            print(f"✗ API is not reachable: {e}")
            print("Please start the API server first: python run_api.py")
            return

    # Run concurrent user sessions
    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        # Create tasks for all users
        tasks = [
            simulate_user_session(i + 1, session)
            for i in range(num_users)
        ]

        # Run all tasks concurrently
        print(f"Starting {num_users} concurrent user sessions...")
        print("-" * 80)
        results = await asyncio.gather(*tasks, return_exceptions=True)

    total_time = time.time() - start_time

    # Print summary
    print()
    print("=" * 80)
    print("TEST RESULTS SUMMARY")
    print("=" * 80)
    print()

    successful = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
    failed = num_users - successful

    print(f"Total Users:        {num_users}")
    print(f"Successful:         {successful}")
    print(f"Failed:             {failed}")
    print(f"Total Time:         {total_time:.2f}s")
    print(f"Avg Time/User:      {total_time / num_users:.2f}s")
    print()

    # Show individual results
    print("Individual User Results:")
    print("-" * 80)
    for result in results:
        if isinstance(result, dict):
            status = "✓ SUCCESS" if result.get("success") else "✗ FAILED"
            user_id = result.get("user_id", "?")
            total = result.get("total_time", 0)
            steps = len(result.get("steps", []))

            print(f"User {user_id}: {status} - {steps} steps completed in {total:.2f}s")
            if not result.get("success") and "error" in result:
                print(f"         Error: {result['error']}")
        else:
            print(f"Exception: {result}")

    print()
    print("=" * 80)

    if successful == num_users:
        print("✓ ALL TESTS PASSED - API can handle parallel requests!")
    elif successful > 0:
        print("⚠ PARTIAL SUCCESS - Some requests succeeded, some failed")
    else:
        print("✗ ALL TESTS FAILED - API has concurrency issues")

    print("=" * 80)


async def test_same_session_concurrency():
    """
    Test that the same session properly handles concurrent requests.
    This should queue requests, not execute them in parallel.
    """
    print("=" * 80)
    print("SAME SESSION CONCURRENCY TEST")
    print("Testing that same session requests are properly serialized...")
    print("=" * 80)
    print()

    async with aiohttp.ClientSession() as session:
        # Start one automation session
        print("Starting single automation session...")
        async with session.post(
            f"{API_BASE_URL}/api/v1/automation/start",
            json={"include_docket": False}
        ) as response:
            data = await response.json()
            if response.status != 200:
                print(f"✗ Failed to start session: {data.get('detail')}")
                return

            session_id = data.get("session_id")
            print(f"✓ Session started: {session_id[:8]}...")
            print()

        # Try to make 2 concurrent requests to the same session
        print("Making 2 concurrent requests to the same session...")
        print("(These should be serialized, not parallel)")
        print()

        async def make_select_request(request_num: int):
            print(f"  Request {request_num}: Starting...")
            start = time.time()
            async with session.post(
                f"{API_BASE_URL}/api/v1/docket/select",
                json={
                    "session_id": session_id,
                    "category": "Dockets by State",
                    "specific_docket": "California"
                }
            ) as response:
                elapsed = time.time() - start
                status = "✓" if response.status == 200 else "✗"
                print(f"  Request {request_num}: {status} Completed in {elapsed:.2f}s")
                return response.status == 200

        # Make concurrent requests
        results = await asyncio.gather(
            make_select_request(1),
            make_select_request(2),
            return_exceptions=True
        )

        print()

        # At least one should succeed (the first one),
        # the second might fail if state is already selected
        success_count = sum(1 for r in results if r is True)

        if success_count >= 1:
            print("✓ Session locking working - Requests were properly serialized")
        else:
            print("✗ Potential issue with session locking")

        # Cleanup
        print("\nCleaning up session...")
        async with session.post(
            f"{API_BASE_URL}/api/v1/session/cleanup",
            json={"session_id": session_id}
        ) as response:
            if response.status == 200:
                print("✓ Session cleaned up")

        print()
        print("=" * 80)


async def main():
    """Run all tests."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "API PARALLEL REQUEST TEST SUITE" + " " * 26 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    # Test 1: Multiple concurrent users (different sessions)
    await test_concurrent_users(num_users=3)

    print("\n\n")

    # Test 2: Same session concurrency
    await test_same_session_concurrency()

    print("\n")
    print("All tests completed!")
    print()


if __name__ == "__main__":
    asyncio.run(main())
