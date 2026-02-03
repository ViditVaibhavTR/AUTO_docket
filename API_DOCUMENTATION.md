# Docket Alert Automation API Documentation

## Overview

This FastAPI-based REST API provides endpoints for automating docket alert creation on WestLaw Precision. The API handles browser automation, docket selection, and alert configuration.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API does not require authentication. In production, implement proper authentication mechanisms.

## Getting Started

### 1. Install Dependencies

```bash
cd app
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the `app` directory with your credentials:

```env
WESTLAW_USERNAME=your_email@example.com
WESTLAW_PASSWORD=your_password
ROUTING_PAGE_URL=your_routing_url
IAC_VALUES=value1,value2,value3
```

### 3. Start the API Server

```bash
python run_api.py
```

The server will start on `http://localhost:8000`

### 4. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check

#### GET `/health`

Check if the API is running.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "message": "API is operational"
}
```

---

### Get Docket Categories

#### GET `/api/v1/docket-categories`

Get all available docket categories and their options.

**Response:**
```json
{
  "categories": {
    "Dockets by State": ["California", "New York", "Texas", ...],
    "Federal Dockets by Court": [...],
    ...
  }
}
```

---

### Get States

#### GET `/api/v1/states`

Get available states (limited to 3 for demo).

**Response:**
```json
{
  "states": ["California", "New York", "Texas"]
}
```

---

### Get Districts

#### GET `/api/v1/districts?state={state}`

Get available districts for a specific state.

**Parameters:**
- `state` (query): State name

**Response:**
```json
{
  "state": "California",
  "districts": ["Central District", "Eastern District", "Northern District", "Southern District"]
}
```

---

### Start Automation

#### POST `/api/v1/automation/start`

Start the automation process: login, configure gateway, and IAC.

**Request Body:**
```json
{
  "include_docket": false
}
```

**Response:**
```json
{
  "status": "login_success",
  "message": "Successfully logged in and configured",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Note:** Save the `session_id` for subsequent requests.

---

### Select Docket

#### POST `/api/v1/docket/select`

Select a docket category and specific docket.

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "category": "Dockets by State",
  "specific_docket": "California"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully selected Dockets by State → California"
}
```

---

### Select District

#### POST `/api/v1/district/select`

Select a district for the chosen state.

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "state": "California",
  "district": "Central District"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully selected district: Central District"
}
```

---

### Search Docket

#### POST `/api/v1/docket/search`

Search for a specific docket number.

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "docket_number": "1:25-CV-01815"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully searched for docket: 1:25-CV-01815"
}
```

---

### Create Alert

#### POST `/api/v1/alert/create`

Click "Create Docket Alert" button.

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Successfully clicked 'Create Docket Alert'"
}
```

---

### Complete Alert Setup

#### POST `/api/v1/alert/complete-setup`

Fill in alert details and complete the setup.

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "alert_name": "My Docket Alert",
  "alert_description": "Track important filings",
  "user_email": "user@example.com",
  "frequency": "daily",
  "alert_times": ["5am", "12pm", "3pm", "5pm"]
}
```

**Frequency Options:**
- `daily`
- `weekdays`
- `weekly`
- `biweekly`
- `monthly`

**Alert Times Options:**
- `5am`
- `12pm`
- `3pm`
- `5pm`

**Response:**
```json
{
  "status": "success",
  "message": "Alert setup completed successfully"
}
```

---

### Cleanup Session

#### POST `/api/v1/session/cleanup`

Cleanup and close a browser session.

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Session 550e8400-e29b-41d4-a716-446655440000 cleaned up successfully"
}
```

---

### List Sessions

#### GET `/api/v1/sessions`

List all active browser sessions.

**Response:**
```json
{
  "active_sessions": ["550e8400-e29b-41d4-a716-446655440000"],
  "count": 1
}
```

---

## Complete Workflow Example

### Using Python Client

```python
from api_client import DocketAlertAPIClient

# Initialize client
client = DocketAlertAPIClient(base_url="http://localhost:8000")

# 1. Start automation
result = client.start_automation()
session_id = result['session_id']
print(f"Session ID: {session_id}")

# 2. Select docket
client.select_docket(
    session_id=session_id,
    category="Dockets by State",
    specific_docket="California"
)

# 3. Select district
client.select_district(
    session_id=session_id,
    state="California",
    district="Central District"
)

# 4. Search docket
client.search_docket(
    session_id=session_id,
    docket_number="1:25-CV-01815"
)

# 5. Create alert
client.create_alert(session_id=session_id)

# 6. Complete alert setup
client.complete_alert_setup(
    session_id=session_id,
    alert_name="Important Case Alert",
    alert_description="Track this case",
    user_email="user@example.com",
    frequency="daily",
    alert_times=["5am", "12pm"]
)

# 7. Cleanup
client.cleanup_session(session_id=session_id)
```

### Using cURL

```bash
# 1. Start automation
curl -X POST http://localhost:8000/api/v1/automation/start \
  -H "Content-Type: application/json" \
  -d '{"include_docket": false}'

# Response: {"session_id": "550e8400-...", "status": "login_success"}

# 2. Select docket
curl -X POST http://localhost:8000/api/v1/docket/select \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-...",
    "category": "Dockets by State",
    "specific_docket": "California"
  }'

# 3. Cleanup
curl -X POST http://localhost:8000/api/v1/session/cleanup \
  -H "Content-Type: application/json" \
  -d '{"session_id": "550e8400-..."}'
```

---

## Frontend Integration

The Streamlit frontend can be adapted to use the API by replacing direct function calls with API client calls.

### Example Integration

```python
import streamlit as st
from api_client import DocketAlertAPIClient

# Initialize client
client = DocketAlertAPIClient()

# Start automation via API instead of direct function call
if st.button("Start Automation"):
    result = client.start_automation()
    st.session_state.session_id = result['session_id']
    st.success("Automation started!")
```

---

## Error Handling

All endpoints return standard HTTP status codes:

- `200`: Success
- `404`: Session not found
- `500`: Internal server error

**Error Response Format:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## Testing

Run the test script to verify API functionality:

```bash
python test_api.py
```

---

## Production Considerations

1. **Session Management**: Use Redis or a database instead of in-memory storage
2. **Authentication**: Implement JWT or OAuth2 authentication
3. **Rate Limiting**: Add rate limiting to prevent abuse
4. **HTTPS**: Use HTTPS in production
5. **CORS**: Configure CORS properly for your frontend domain
6. **Logging**: Enhance logging for monitoring and debugging
7. **Error Handling**: Add more comprehensive error handling
8. **Session Timeout**: Implement session expiration
9. **Load Balancing**: Use multiple workers for production load

---

## Troubleshooting

### API Server Won't Start

- Check if port 8000 is already in use
- Verify all dependencies are installed
- Check `.env` file configuration

### Session Not Found Error

- Ensure you're using the correct `session_id`
- Check if the session has been cleaned up or expired
- Use `/api/v1/sessions` to list active sessions

### Browser Automation Fails

- Verify Selenium and ChromeDriver are properly installed
- Check `.env` credentials
- Review logs in the `logs/` directory
- Check screenshots in the `screenshots/` directory

---

## Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Review logs in the `logs/` directory
3. Check screenshots in the `screenshots/` directory
