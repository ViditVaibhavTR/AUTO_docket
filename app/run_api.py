"""
Runner script for the FastAPI server.
"""

import uvicorn
from api.main import app

if __name__ == "__main__":
    print("=" * 80)
    print("Starting Docket Alert Automation API Server")
    print("=" * 80)
    print("\nAPI Documentation:")
    print("  - Swagger UI: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print("  - Health Check: http://localhost:8000/health")
    print("\nPress CTRL+C to stop the server")
    print("=" * 80)
    print()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=True  # Enable auto-reload during development
    )
