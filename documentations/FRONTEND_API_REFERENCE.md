# Docket Alert Automation API - Frontend Reference

**Base URL:** `http://localhost:8000` (development) or your deployed URL

**Version:** 1.0.0

**Last Updated:** 2026-02-13

---

## Important Changes (Latest)

### Rate Limiting (NEW)
- **Max concurrent sessions:** 2
- **Rate limit per client:** 1 request per 30 seconds
- **Error code:** HTTP 429 (Too Many Requests)
- **Auto cleanup:** Sessions older than 30 minutes are automatically cleaned up

---

## Quick Start

```javascript
// Example: Start automation and create alert
const API_BASE = "http://localhost:8000";

// 1. Check API health
const health = await fetch(`${API_BASE}/health`);

// 2. Start automation (login + setup)
const response = await fetch(`${API_BASE}/api/v1/automation/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ include_docket: false })
});
const { session_id } = await response.json();

// 3. Select docket
await fetch(`${API_BASE}/api/v1/docket/select`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        session_id,
        category: "Dockets by State",
        specific_docket: "California"
    })
});

// 4. Create alert
await fetch(`${API_BASE}/api/v1/alert/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id })
});
```

---

## Endpoints

### 1. Health Check

**GET** `/health`

Check if API is running.

**Response (200):**
```json
{
    "status": "healthy",
    "version": "1.0.0"
}
```

---

### 2. Start Automation

**POST** `/api/v1/automation/start`

Starts browser automation: login to WestLaw, configure gateway/IAC.

**Rate Limits:**
- Max 2 concurrent sessions globally
- Max 1 request per 30 seconds per client IP

**Request Body:**
```json
{
    "include_docket": false
}
```

**Response (200):**
```json
{
    "status": "login_success",
    "message": "Successfully logged in and configured",
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses:**

**429 - Too Many Concurrent Sessions:**
```json
{
    "detail": "Too many concurrent sessions. Maximum 2 allowed. Current: 2. Please cleanup unused sessions."
}
```

**429 - Rate Limit (Per Client):**
```json
{
    "detail": "Automation already in progress for your session. Please wait 15 seconds."
}
```

**500 - Automation Failed:**
```json
{
    "detail": "Automation failed: [error details]"
}
```

**Frontend Handling:**
```javascript
try {
    const response = await fetch(`${API_BASE}/api/v1/automation/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ include_docket: false })
    });

    if (response.status === 429) {
        const error = await response.json();
        alert(`Rate limit: ${error.detail}`);
        return;
    }

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    return data.session_id;
} catch (error) {
    console.error("Automation start failed:", error);
}
```

---

### 3. Get Docket Categories

**GET** `/api/v1/docket-categories`

Get available docket categories.

**Response (200):**
```json
{
    "categories": [
        "Dockets by State",
        "Dockets by District",
        "Dockets by Judge",
        "Dockets by Party Name",
        "Dockets by Docket Number"
    ]
}
```

---

### 4. Select Docket Category

**POST** `/api/v1/docket/select`

Select a docket category and specific docket.

**Request Body:**
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "category": "Dockets by State",
    "specific_docket": "California"
}
```

**Response (200):**
```json
{
    "status": "docket_selected",
    "message": "Selected California in Dockets by State"
}
```

**Errors:**
- **404:** Session not found
- **500:** Selection failed

---

### 5. Get States

**GET** `/api/v1/states`

Get list of available states.

**Response (200):**
```json
{
    "states": [
        "Alabama",
        "Alaska",
        "Arizona",
        "California",
        "..."
    ]
}
```

---

### 6. Get Districts for State

**GET** `/api/v1/districts?state=California`

Get districts for a specific state.

**Query Parameters:**
- `state` (required): State name

**Response (200):**
```json
{
    "state": "California",
    "districts": [
        "Central District",
        "Eastern District",
        "Northern District",
        "Southern District"
    ]
}
```

---

### 7. Select District

**POST** `/api/v1/district/select`

Select a district within the chosen state.

**Request Body:**
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "state": "California",
    "district": "Central District"
}
```

**Response (200):**
```json
{
    "status": "district_selected",
    "message": "Selected Central District for California"
}
```

---

### 8. Search Docket Number

**POST** `/api/v1/docket/search`

Search for a specific docket number.

**Request Body:**
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "docket_number": "3:26-CV-00397"
}
```

**Response (200):**
```json
{
    "status": "docket_found",
    "message": "Docket 3:26-CV-00397 found and selected"
}
```

---

### 9. Create Alert

**POST** `/api/v1/alert/create`

Navigate to create alert page.

**Request Body:**
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (200):**
```json
{
    "status": "alert_page_ready",
    "message": "Ready to configure alert"
}
```

---

### 10. Complete Alert Setup

**POST** `/api/v1/alert/complete-setup`

Complete alert configuration with details.

**Request Body:**
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "alert_name": "California Central District Monitor",
    "alert_description": "Monitor all filings in CA Central District",
    "user_email": "user@example.com",
    "frequency": "daily",
    "alert_times": ["5am", "12pm", "5pm"]
}
```

**Frequency Options:**
- `"daily"` - Every day
- `"weekdays"` - Monday through Friday
- `"weekly"` - Once per week
- `"biweekly"` - Every two weeks
- `"monthly"` - Once per month

**Alert Times Options:**
- `"5am"` - 5:00 AM
- `"12pm"` - 12:00 PM (Noon)
- `"3pm"` - 3:00 PM
- `"5pm"` - 5:00 PM

**Response (200):**
```json
{
    "status": "alert_created",
    "message": "Alert created successfully"
}
```

---

### 11. List Active Sessions

**GET** `/api/v1/sessions`

Get all active browser sessions.

**Response (200):**
```json
{
    "active_sessions": [
        "550e8400-e29b-41d4-a716-446655440000",
        "660e8400-e29b-41d4-a716-446655440001"
    ],
    "count": 2
}
```

---

### 12. Cleanup Session

**POST** `/api/v1/session/cleanup`

Manually cleanup a browser session.

**Request Body:**
```json
{
    "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (200):**
```json
{
    "status": "success",
    "message": "Session 550e8400-e29b-41d4-a716-446655440000 cleaned up successfully"
}
```

**Errors:**
- **404:** Session not found

---

## Complete Workflow Example

```javascript
class DocketAlertClient {
    constructor(baseUrl = "http://localhost:8000") {
        this.baseUrl = baseUrl;
        this.sessionId = null;
    }

    async checkHealth() {
        const response = await fetch(`${this.baseUrl}/health`);
        return response.ok;
    }

    async startAutomation() {
        const response = await fetch(`${this.baseUrl}/api/v1/automation/start`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ include_docket: false })
        });

        if (response.status === 429) {
            const error = await response.json();
            throw new Error(`Rate limit: ${error.detail}`);
        }

        if (!response.ok) {
            throw new Error(`Failed to start automation: ${response.status}`);
        }

        const data = await response.json();
        this.sessionId = data.session_id;
        return this.sessionId;
    }

    async selectDocket(category, specificDocket) {
        const response = await fetch(`${this.baseUrl}/api/v1/docket/select`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: this.sessionId,
                category,
                specific_docket: specificDocket
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to select docket: ${response.status}`);
        }

        return response.json();
    }

    async getStates() {
        const response = await fetch(`${this.baseUrl}/api/v1/states`);
        const data = await response.json();
        return data.states;
    }

    async getDistricts(state) {
        const response = await fetch(
            `${this.baseUrl}/api/v1/districts?state=${encodeURIComponent(state)}`
        );
        const data = await response.json();
        return data.districts;
    }

    async selectDistrict(state, district) {
        const response = await fetch(`${this.baseUrl}/api/v1/district/select`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: this.sessionId,
                state,
                district
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to select district: ${response.status}`);
        }

        return response.json();
    }

    async searchDocket(docketNumber) {
        const response = await fetch(`${this.baseUrl}/api/v1/docket/search`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: this.sessionId,
                docket_number: docketNumber
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to search docket: ${response.status}`);
        }

        return response.json();
    }

    async createAlert(alertConfig) {
        // First navigate to alert page
        const createResponse = await fetch(`${this.baseUrl}/api/v1/alert/create`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: this.sessionId })
        });

        if (!createResponse.ok) {
            throw new Error(`Failed to navigate to alert page: ${createResponse.status}`);
        }

        // Then complete setup
        const setupResponse = await fetch(`${this.baseUrl}/api/v1/alert/complete-setup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                session_id: this.sessionId,
                ...alertConfig
            })
        });

        if (!setupResponse.ok) {
            throw new Error(`Failed to complete alert setup: ${setupResponse.status}`);
        }

        return setupResponse.json();
    }

    async cleanup() {
        if (!this.sessionId) return;

        await fetch(`${this.baseUrl}/api/v1/session/cleanup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ session_id: this.sessionId })
        });

        this.sessionId = null;
    }
}

// Usage Example
async function createCaliforniaAlert() {
    const client = new DocketAlertClient();

    try {
        // 1. Check API health
        const isHealthy = await client.checkHealth();
        if (!isHealthy) {
            throw new Error("API is not healthy");
        }

        // 2. Start automation
        await client.startAutomation();
        console.log("Automation started, session ID:", client.sessionId);

        // 3. Select docket by state
        await client.selectDocket("Dockets by State", "California");

        // 4. Get districts for California
        const districts = await client.getDistricts("California");
        console.log("Available districts:", districts);

        // 5. Select Central District
        await client.selectDistrict("California", "Central District");

        // 6. Create alert
        await client.createAlert({
            alert_name: "CA Central District Monitor",
            alert_description: "Monitor all filings",
            user_email: "user@example.com",
            frequency: "daily",
            alert_times: ["5am", "12pm", "5pm"]
        });

        console.log("Alert created successfully!");

    } catch (error) {
        console.error("Error:", error.message);
    } finally {
        // Always cleanup session
        await client.cleanup();
    }
}
```

---

## Error Handling Best Practices

### 1. Rate Limiting (429 Errors)

```javascript
async function startWithRetry(maxRetries = 3) {
    for (let i = 0; i < maxRetries; i++) {
        try {
            const response = await fetch(`${API_BASE}/api/v1/automation/start`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ include_docket: false })
            });

            if (response.status === 429) {
                const error = await response.json();
                const waitTime = parseInt(error.detail.match(/\d+/)?.[0] || "30");
                console.log(`Rate limited. Waiting ${waitTime} seconds...`);
                await new Promise(resolve => setTimeout(resolve, waitTime * 1000));
                continue;
            }

            if (response.ok) {
                return await response.json();
            }

            throw new Error(`HTTP ${response.status}`);
        } catch (error) {
            if (i === maxRetries - 1) throw error;
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
    }
}
```

### 2. Session Management

```javascript
// Always cleanup on page unload
window.addEventListener('beforeunload', async () => {
    if (currentSessionId) {
        // Use sendBeacon for reliability during unload
        navigator.sendBeacon(
            `${API_BASE}/api/v1/session/cleanup`,
            JSON.stringify({ session_id: currentSessionId })
        );
    }
});
```

### 3. Timeout Handling

```javascript
async function fetchWithTimeout(url, options, timeout = 120000) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            throw new Error('Request timeout - automation may be taking longer than expected');
        }
        throw error;
    }
}
```

---

## TypeScript Types

```typescript
// Request Types
interface AutomationStartRequest {
    include_docket: boolean;
}

interface DocketSelectRequest {
    session_id: string;
    category: string;
    specific_docket: string;
}

interface DistrictSelectRequest {
    session_id: string;
    state: string;
    district: string;
}

interface DocketSearchRequest {
    session_id: string;
    docket_number: string;
}

interface AlertCreateRequest {
    session_id: string;
}

interface AlertCompleteSetupRequest {
    session_id: string;
    alert_name: string;
    alert_description: string | null;
    user_email: string;
    frequency: "daily" | "weekdays" | "weekly" | "biweekly" | "monthly";
    alert_times: Array<"5am" | "12pm" | "3pm" | "5pm">;
}

interface SessionCleanupRequest {
    session_id: string;
}

// Response Types
interface HealthResponse {
    status: string;
    version: string;
}

interface AutomationStartResponse {
    status: string;
    message: string;
    session_id: string;
}

interface DocketCategoriesResponse {
    categories: string[];
}

interface StatesResponse {
    states: string[];
}

interface DistrictsResponse {
    state: string;
    districts: string[];
}

interface GenericStatusResponse {
    status: string;
    message: string;
}

interface SessionsListResponse {
    active_sessions: string[];
    count: number;
}

interface ErrorResponse {
    detail: string;
}
```

---

## Testing the API

### Using cURL

```bash
# Health check
curl http://localhost:8000/health

# Start automation
curl -X POST http://localhost:8000/api/v1/automation/start \
  -H "Content-Type: application/json" \
  -d '{"include_docket": false}'

# Select docket
curl -X POST http://localhost:8000/api/v1/docket/select \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "YOUR_SESSION_ID",
    "category": "Dockets by State",
    "specific_docket": "California"
  }'

# Get states
curl http://localhost:8000/api/v1/states

# Get districts
curl "http://localhost:8000/api/v1/districts?state=California"

# List sessions
curl http://localhost:8000/api/v1/sessions

# Cleanup session
curl -X POST http://localhost:8000/api/v1/session/cleanup \
  -H "Content-Type: application/json" \
  -d '{"session_id": "YOUR_SESSION_ID"}'
```

### Using Python Health Checker

```python
from documentations.api_health_checker import check_api_health

# Simple check
if check_api_health():
    print("API is running!")
else:
    print("API is not running")

# Verbose check
check_api_health(verbose=True)

# Custom URL
check_api_health(base_url="https://api.yourdomain.com", verbose=True)
```

---

## Important Notes

1. **Session Lifecycle:**
   - Sessions auto-expire after 30 minutes of inactivity
   - Always cleanup sessions when done to free resources
   - Maximum 2 concurrent sessions allowed

2. **Rate Limits:**
   - Global limit: 2 concurrent browser sessions
   - Per-client limit: 1 request per 30 seconds per IP
   - Returns HTTP 429 with retry information

3. **Timeouts:**
   - Automation start can take 30-60 seconds
   - Set frontend timeouts to at least 120 seconds
   - Backend has retry logic for transient failures

4. **Error Recovery:**
   - All 500 errors include detailed error messages
   - Backend automatically retries browser startup (2 attempts)
   - Rate limit errors include wait time in message

5. **CORS:**
   - Currently allows all origins (`*`)
   - Configure appropriately for production

---

## Support

For issues or questions:
- Check logs at `app/logs/`
- Review API health: `http://localhost:8000/health`
- Check active sessions: `http://localhost:8000/api/v1/sessions`
- Use health checker: `python documentations/api_health_checker.py`

---

**API Version:** 1.0.0
**Last Updated:** 2026-02-13
**Changes:** Added rate limiting, automatic session cleanup, retry logic
