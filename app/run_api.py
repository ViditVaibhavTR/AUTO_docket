"""
Runner script for the FastAPI server.
"""

import os
import uvicorn
# Note: We don't import app directly here - uvicorn will import it using the string "api.app:app"
# This prevents issues with reload mode and circular imports

if __name__ == "__main__":
    # Determine environment (production vs development)
    is_production = os.getenv("ENVIRONMENT", "development") == "production"

    print("=" * 80)
    print("Starting Docket Alert Automation API Server")
    print(f"Environment: {'PRODUCTION' if is_production else 'DEVELOPMENT'}")
    print("=" * 80)
    print("\nAPI Documentation:")
    print("  - Swagger UI: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print("  - Health Check: http://localhost:8000/health")
    print("\nPress CTRL+C to stop the server")
    print("=" * 80)
    print()

    if is_production:
        # Production mode: Multiple workers for parallel request handling
        # Workers = (2 x CPU cores) + 1 is a common formula
        # But we'll use a conservative 4 workers to start
        print("Running in PRODUCTION mode with 4 workers for parallel processing")
        uvicorn.run(
            "api.app:app",  # Module string required for workers
            host="0.0.0.0",
            port=8000,
            workers=4,  # Multiple worker processes for parallelism
            log_level="info",
            access_log=True,
        )
    else:
        # Development mode: Single worker with auto-reload
        print("Running in DEVELOPMENT mode with auto-reload")
        uvicorn.run(
            "api.app:app",  # Must use import string for reload to work
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=True  # Enable auto-reload during development
        )
