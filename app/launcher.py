"""
Auto Docket Desktop Launcher.
Starts the FastAPI server and opens the browser automatically.
Double-click this file or run: python launcher.py
"""

import webbrowser
import threading
import time
import sys
import os


def open_browser():
    """Wait for server to start, then open browser."""
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:8000")


if __name__ == "__main__":
    # Ensure working directory is correct (important for PyInstaller)
    if getattr(sys, "frozen", False):
        os.chdir(os.path.dirname(sys.executable))
    else:
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

    print("="*50)
    print("  Auto Docket - Starting...")
    print("="*50)
    print()
    print("  Server: http://127.0.0.1:8000")
    print("  Browser will open automatically.")
    print("  Press Ctrl+C to stop.")
    print()

    try:
        import uvicorn
        from api.app import app

        # Open browser in background thread
        threading.Thread(target=open_browser, daemon=True).start()

        # Start FastAPI server (blocks until Ctrl+C)
        uvicorn.run(app, host="127.0.0.1", port=8000, workers=1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to close...")
