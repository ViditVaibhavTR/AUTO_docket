"""
Configuration settings loader for the Docket Alert automation project.
Loads and validates environment variables from .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    """Application settings loaded from environment variables."""

    # West Classic Application URLs
    WESTLAW_URL: str = os.getenv("WESTLAW_URL", "https://1.next.qed.westlaw.com/routing")
    WESTLAW_USERNAME: str = os.getenv("WESTLAW_USERNAME", "")
    WESTLAW_PASSWORD: str = os.getenv("WESTLAW_PASSWORD", "")

    # Browser Configuration
    HEADLESS: bool = os.getenv("HEADLESS", "false").lower() == "true"

    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # IAC Values (hard-coded as per requirements)
    IAC_VALUES = [
        "IAC-RAS-DOCKET-VALIDATION",
        "IAC-RAS-DOCKET-LIST",
        "IAC-RAS-DOCKET-TRACK-ALERTS"
    ]

    @classmethod
    def validate(cls) -> None:
        """
        Validate that all required configuration is present.

        Raises:
            ValueError: If required configuration is missing
        """
        if not cls.WESTLAW_USERNAME:
            raise ValueError("WESTLAW_USERNAME is not set in .env file")
        if not cls.WESTLAW_PASSWORD:
            raise ValueError("WESTLAW_PASSWORD is not set in .env file")
        if not cls.WESTLAW_URL:
            raise ValueError("WESTLAW_URL is not set in .env file")

    @classmethod
    def display_config(cls) -> dict:
        """
        Display current configuration (excluding sensitive data).

        Returns:
            Dictionary with configuration values
        """
        return {
            "WESTLAW_URL": cls.WESTLAW_URL,
            "WESTLAW_USERNAME": cls.WESTLAW_USERNAME[:3] + "***" if cls.WESTLAW_USERNAME else "NOT SET",
            "WESTLAW_PASSWORD": "***" if cls.WESTLAW_PASSWORD else "NOT SET",
            "HEADLESS": cls.HEADLESS,
            "LOG_LEVEL": cls.LOG_LEVEL,
            "IAC_VALUES": cls.IAC_VALUES
        }


# Create a singleton instance
settings = Settings()
