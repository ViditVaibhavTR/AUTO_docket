# Docket Alert Automation

Automated workflow for configuring Docket Alert settings in West Classic application.

## Overview

This project automates the configuration of Gateway Live External and Infrastructure Access Controls (IAC) in the West Classic application routing page.

### Current Implementation: Step 1

**Objectives:**
1. Set **Gateway Live External** to `True`
2. Turn **OFF** Infrastructure Access Controls
3. Add the following IAC values:
   - IAC-RAS-DOCKET-VALIDATION
   - IAC-RAS-DOCKET-LIST
   - IAC-RAS-DOCKET-TRACK-ALERTS

## Project Structure

```
AUTO DOCKET/
├── venv/                          # Virtual environment
└── app/                           # Application directory
    ├── .env                       # Environment variables (credentials)
    ├── .gitignore                 # Git ignore file
    ├── requirements.txt           # Python dependencies
    ├── README.md                  # This file
    ├── src/
    │   ├── __init__.py
    │   ├── main.py                # Main entry point
    │   ├── config/
    │   │   ├── __init__.py
    │   │   └── settings.py        # Configuration loader
    │   ├── automation/
    │   │   ├── __init__.py
    │   │   ├── browser.py         # Browser management
    │   │   ├── gateway_config.py  # Gateway configuration
    │   │   └── iac_config.py      # IAC configuration
    │   └── utils/
    │       ├── __init__.py
    │       ├── logger.py          # Logging utility
    │       └── screenshot.py      # Screenshot utility
    ├── logs/                      # Execution logs
    └── screenshots/               # Captured screenshots
```

## Setup Instructions

### 1. Prerequisites

- Python 3.14+ installed
- Virtual environment created (already exists in your project)

### 2. Install Dependencies

Activate your virtual environment and install required packages:

```bash
# Windows - activate from the root directory
venv\Scripts\activate

# Navigate to the app directory
cd app

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### 3. Configure Environment Variables

Edit the `.env` file and update the following values:

```env
# West Classic Application Configuration
WESTLAW_URL=https://1.next.qed.westlaw.com/routing
WESTLAW_USERNAME=your_actual_username
WESTLAW_PASSWORD=your_actual_password

# Browser Configuration
HEADLESS=false  # Set to true for headless mode (no UI)

# Logging Configuration
LOG_LEVEL=INFO
```

**Important:** Replace `your_actual_username` and `your_actual_password` with your real credentials.

## Usage

### Option 1: Interactive Chatbot (Recommended)

Run the Streamlit chatbot interface for an interactive experience:

```bash
# From the root directory (AUTO DOCKET)
# Make sure your virtual environment is activated
venv\Scripts\activate

# Navigate to app directory
cd app

# Run the chatbot
streamlit run chatbot.py
```

Or simply double-click `run_chatbot.bat` in the app directory.

The chatbot will:
- Ask if you want to start the automation
- Show real-time progress with emojis
- Display success/error messages
- Allow you to run again or exit

### Option 2: Command Line

Run the automation directly from the command line:

```bash
# From the root directory (AUTO DOCKET)
# Make sure your virtual environment is activated
venv\Scripts\activate

# Navigate to app directory
cd app

# Run the automation
python src/main.py
```

### What Happens

The automation will:
1. Validate configuration from `.env`
2. Launch browser (Chrome)
3. Navigate to the Cobalt Routing page
4. Configure Gateway Live External to True
5. Turn OFF Infrastructure Access Controls
6. Add the three required IAC values
7. Click "Save Changes and Sign On"
8. Login to WestLaw Precision
9. Select client ID and start new session
10. Capture screenshots at each step
11. Generate execution logs

### Output

- **Logs:** Check `logs/` directory for detailed execution logs
- **Screenshots:** Check `screenshots/` directory for captured screenshots at each step
- **Console:** Real-time progress displayed in the terminal

## Troubleshooting

### Selector Issues

The automation uses multiple fallback selectors to find elements on the page. If elements are not found:

1. Check the screenshots in `screenshots/` directory to see what the page looks like
2. Inspect the actual HTML structure of the routing page
3. Update the selectors in the following files:
   - [src/automation/browser.py](src/automation/browser.py) - Login form selectors
   - [src/automation/gateway_config.py](src/automation/gateway_config.py) - Gateway selectors
   - [src/automation/iac_config.py](src/automation/iac_config.py) - IAC selectors

### Login Issues

If login fails:
1. Verify credentials in `.env` are correct
2. Check `screenshots/login_page.png` to see the login form
3. Update login selectors in [src/automation/browser.py:78-80](src/automation/browser.py#L78-L80)

### Configuration Not Saved

If changes don't persist:
1. Check if Save button was clicked (see logs)
2. Verify save button selector in [src/automation/iac_config.py:140-148](src/automation/iac_config.py#L140-L148)
3. Look for error screenshots in `screenshots/` directory

## Development

### Adding More Steps

This project is designed to be extended with additional workflow steps:

1. Create a new module in `src/automation/` (e.g., `step2_config.py`)
2. Implement the configuration class with similar structure
3. Add the step to [src/main.py](src/main.py) workflow
4. Update this README with the new step

### Logging

The project uses `loguru` for enhanced logging:
- **Console:** Colored output with INFO level
- **File:** Detailed DEBUG level logs with rotation
- **Location:** `logs/docket_automation_YYYY-MM-DD.log`

### Screenshots

Screenshots are automatically captured:
- **Before/After:** Major configuration steps
- **Errors:** When exceptions occur
- **Success:** After successful operations
- **Format:** PNG with timestamps
- **Location:** `screenshots/`

## Technologies Used

- **Python 3.14.2**
- **Selenium** - Browser automation
- **Streamlit** - Interactive chatbot interface
- **python-dotenv** - Environment variable management
- **loguru** - Enhanced logging
- **webdriver-manager** - Automatic ChromeDriver management

## Next Steps

After Step 1 is complete and verified:
- Provide details for Step 2 of the Docket Alert workflow
- Extend the automation to handle additional configuration steps
- Build on the established patterns and architecture

## Notes

- Browser stays open for 5 seconds after completion for manual verification
- All sensitive data is stored in `.env` (excluded from git)
- Screenshots help with debugging and verification
- Element selectors may need updates if the UI changes

## Support

If you encounter issues:
1. Check the logs in `logs/` directory
2. Review screenshots in `screenshots/` directory
3. Verify selectors match the actual page structure
4. Update selectors as needed based on the HTML structure
