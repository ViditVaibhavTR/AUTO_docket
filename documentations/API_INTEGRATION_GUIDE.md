# Docket Alert Automation API - Integration Guide

**Version:** 1.0.0
**Last Updated:** 2026-02-13
**Target Audience:** Frontend Developers (React, Vue, Angular, Mobile)

---

## Table of Contents

1. [Introduction & Overview](#1-introduction--overview)
2. [Getting Started](#2-getting-started)
3. [Complete API Reference](#3-complete-api-reference)
4. [Complete Workflow Examples](#4-complete-workflow-examples)
5. [Best Practices & Optimization](#5-best-practices--optimization)
6. [UI Integration Patterns](#6-ui-integration-patterns)
7. [Testing Guide](#7-testing-guide)
8. [Troubleshooting Guide](#8-troubleshooting-guide)
9. [Deployment Guide](#9-deployment-guide)
10. [FAQ](#10-faq)
11. [Appendices](#11-appendices)
12. [Quick Reference Cheat Sheet](#12-quick-reference-cheat-sheet)

---

## 1. Introduction & Overview

### Purpose

The **Docket Alert Automation API** is a REST API that automates the creation of docket alerts on **WestLaw Precision**. It handles the entire workflow from browser initialization and authentication to docket selection and alert configuration.

### Architecture

```
┌─────────────────────┐
│  Your Frontend      │  ← Web, Mobile, Desktop
│  (React/Vue/etc)    │
└──────────┬──────────┘
           │ HTTP/REST
           │ (JSON)
           ▼
┌─────────────────────┐
│  FastAPI Backend    │  ← This API
│  (Python + Uvicorn) │
└──────────┬──────────┘
           │ Selenium WebDriver
           ▼
┌─────────────────────┐
│  Chrome Browser     │
└──────────┬──────────┘
           │ Automation
           ▼
┌─────────────────────┐
│  WestLaw Precision  │  ← Target Website
│  (Thomson Reuters)  │
└─────────────────────┘
```

### Key Concepts

#### Session-Based Workflow

The API is **stateful** - each automation workflow requires a browser session that persists across multiple API calls:

1. **Start session** → Get `session_id` (browser opens, logs in)
2. **Select docket** → Use `session_id`
3. **Select district** → Use same `session_id`
4. **Search docket** → Use same `session_id`
5. **Create alert** → Use same `session_id`
6. **Complete setup** → Use same `session_id`
7. **Cleanup** → Destroys session and closes browser

**Important:** The `session_id` is your handle to a running browser instance. Treat it like a connection handle in a database.

#### UUID Session Tracking

Each session gets a unique UUID (e.g., `550e8400-e29b-41d4-a716-446655440000`). This allows:
- Multiple concurrent sessions (parallel workflows)
- Session isolation (operations don't interfere)
- Resource tracking (know which browser belongs to which request)

#### Long-Running Operations

Browser automation isn't instant. Typical timings:
- **Browser startup + login**: 15-20 seconds
- **Docket selection**: 2-3 seconds
- **District selection**: 2-3 seconds
- **Docket search**: 3-5 seconds
- **Alert creation**: 2 seconds
- **Alert completion**: 3-5 seconds

**Total workflow**: ~30-40 seconds

Your frontend should:
- Show progress indicators
- Use appropriate timeouts (30+ seconds for `/automation/start`)
- Not assume instant responses

#### Thread-Safe Concurrent Sessions

The API supports multiple simultaneous sessions:
```javascript
// These can run in parallel (different session IDs)
const session1 = await startAutomation(); // User A
const session2 = await startAutomation(); // User B
// Each gets isolated browser instance
```

But operations on the **same session** are serialized to prevent race conditions.

### Prerequisites

- **API Server**: Running on `http://localhost:8000` (development) or your production URL
- **Python 3.11+**: Backend requirement
- **Chrome/Chromium**: For Selenium automation
- **Network Access**: To WestLaw Precision

### Quick Start (5 minutes)

Here's the simplest possible integration:

```javascript
const API_URL = 'http://localhost:8000';

async function createDocketAlert() {
  try {
    // 1. Start automation (15-20s)
    const startResp = await fetch(`${API_URL}/api/v1/automation/start`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({include_docket: false})
    });
    const {session_id} = await startResp.json();

    // 2. Select docket (2-3s)
    await fetch(`${API_URL}/api/v1/docket/select`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        session_id,
        category: 'Dockets by State',
        specific_docket: 'California'
      })
    });

    // 3. Select district (2-3s)
    await fetch(`${API_URL}/api/v1/district/select`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        session_id,
        state: 'California',
        district: 'Central District'
      })
    });

    // 4. Search docket number (3-5s)
    await fetch(`${API_URL}/api/v1/docket/search`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        session_id,
        docket_number: '3:26-CV-00397'
      })
    });

    // 5. Create alert (2s)
    await fetch(`${API_URL}/api/v1/alert/create`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({session_id})
    });

    // 6. Complete alert setup (3-5s)
    await fetch(`${API_URL}/api/v1/alert/complete-setup`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        session_id,
        alert_name: 'Important Case Alert',
        alert_description: 'Track updates for case 3:26-CV-00397',
        user_email: 'user@example.com',
        frequency: 'daily',
        alert_times: ['5am', '3pm']
      })
    });

    // 7. Cleanup (always!)
    await fetch(`${API_URL}/api/v1/session/cleanup`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({session_id})
    });

    console.log('✓ Alert created successfully!');
  } catch (error) {
    console.error('✗ Failed to create alert:', error);
  }
}
```

---

## 2. Getting Started

### Server Setup

#### Development Mode

```bash
cd app
python run_api.py
```

This starts the API with:
- Single worker process
- Auto-reload on code changes
- Accessible at `http://localhost:8000`

#### Production Mode

```bash
cd app
ENVIRONMENT=production python run_api.py
```

This starts the API with:
- 4 worker processes (parallel request handling)
- No auto-reload
- Better performance under load

### Health Check

Verify the API is running:

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "message": "Docket Alert Automation API is running"
}
```

If you get `Connection refused`, the server isn't running.

### Authentication

**Current:** No authentication required
**Future:** Bearer token authentication planned

For now, anyone who can reach the API can use it. In production, you should:
- Put API behind a firewall/VPN
- Add authentication middleware
- Use API gateway with rate limiting

### Base URL Configuration

Don't hardcode `http://localhost:8000` in your frontend. Use environment variables:

**React:**
```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
```

**Vue:**
```javascript
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

**Python:**
```python
import os
API_BASE_URL = os.getenv('API_URL', 'http://localhost:8000')
```

Then configure per environment:
- **Development**: `http://localhost:8000`
- **Staging**: `https://api-staging.yourdomain.com`
- **Production**: `https://api.yourdomain.com`

---

## 3. Complete API Reference

### Endpoint Categories

| Category | Endpoints | Purpose |
|----------|-----------|---------|
| **Health** | `GET /`, `GET /health` | API availability checks |
| **Metadata** | `GET /api/v1/docket-categories`, `GET /api/v1/states`, `GET /api/v1/districts` | Static data for UI |
| **Session** | `POST /api/v1/automation/start`, `POST /api/v1/session/cleanup`, `GET /api/v1/sessions` | Browser lifecycle |
| **Docket** | `POST /api/v1/docket/select`, `POST /api/v1/district/select`, `POST /api/v1/docket/search` | Docket navigation |
| **Alert** | `POST /api/v1/alert/create`, `POST /api/v1/alert/complete-setup` | Alert creation |

### Base URL

All endpoints use base URL: `http://localhost:8000` (or your configured URL)

---

### Health Endpoints

#### `GET /`

**Description:** Root health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "message": "Docket Alert Automation API is running"
}
```

**Example:**
```bash
curl http://localhost:8000/
```

**Use Case:** Basic connectivity test, load balancer health checks

---

#### `GET /health`

**Description:** Detailed health check (same as root for now)

**Response:**
```json
{
  "status": "healthy",
  "message": "Docket Alert Automation API is running"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

**Use Case:** Monitoring systems, uptime checks

---

### Metadata Endpoints

#### `GET /api/v1/docket-categories`

**Description:** Get hierarchical docket menu structure

**Response:**
```json
{
  "categories": {
    "Federal Dockets by Court": [
      "U.S. Supreme Court",
      "U.S. Courts of Appeals",
      "Federal District Courts",
      "Federal Bankruptcy Courts",
      "U.S. Tax Court",
      "U.S. Court of Federal Claims",
      "U.S. Court of International Trade",
      "U.S. Judicial Panel on Multidistrict Litigation"
    ],
    "Federal Dockets by Agency": [
      "Copyright Claims Board",
      "Patent Trial & Appeal Board",
      "Securities & Exchange Commission",
      "Trademark Trial & Appeal Board",
      "U.S. International Trade Commission"
    ],
    "Dockets by State": [
      "Alabama", "Alaska", "Arizona", "Arkansas", "California",
      "Colorado", "Connecticut", "Delaware", "District of Columbia",
      "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana",
      "Iowa", "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland",
      "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri",
      "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey",
      "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
      "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
      "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia",
      "Washington", "West Virginia", "Wisconsin", "Wyoming"
    ],
    "Dockets by Territory": [
      "Guam",
      "Northern Mariana Islands",
      "Puerto Rico",
      "Virgin Islands"
    ],
    "International": [
      "United Kingdom"
    ],
    "Dockets by Topic": [
      "Admiralty & Maritime",
      "Business & Commercial",
      "Environmental Law",
      "Family Law",
      "Foreign Corrupt Practices Act",
      "Immigration",
      "Insurance",
      "Intellectual Property",
      "Labor & Employment",
      "Real Property",
      "Securities (Federal)",
      "Tax"
    ]
  }
}
```

**Examples:**

```bash
curl http://localhost:8000/api/v1/docket-categories
```

```javascript
const response = await fetch('http://localhost:8000/api/v1/docket-categories');
const {categories} = await response.json();
```

```python
import requests
response = requests.get('http://localhost:8000/api/v1/docket-categories')
categories = response.json()['categories']
```

**Use Case:** Populate dropdown menus for docket category selection

**Performance Tip:** ⚡ This data is static - **cache it aggressively**. No need to fetch on every page load.

**TypeScript Interface:**
```typescript
interface DocketCategoriesResponse {
  categories: {
    [category: string]: string[];
  };
}
```

---

#### `GET /api/v1/states`

**Description:** Get available states (demo returns CA, NY, TX)

**Response:**
```json
{
  "states": ["California", "New York", "Texas"]
}
```

**Examples:**

```bash
curl http://localhost:8000/api/v1/states
```

```javascript
const response = await fetch('http://localhost:8000/api/v1/states');
const {states} = await response.json();
// Use for dropdown: <select>{states.map(s => <option>{s}</option>)}</select>
```

**Use Case:** State selection dropdown

**Note:** Demo limitation - only 3 states. Production version would return all 50+ states/territories.

---

#### `GET /api/v1/districts?state={state}`

**Description:** Get districts for a given state

**Query Parameters:**
- `state` (required): State name (e.g., "California", "New York")

**Response:**
```json
{
  "districts": [
    "Central District",
    "Northern District",
    "Southern District",
    "Eastern District"
  ]
}
```

**Examples:**

```bash
curl "http://localhost:8000/api/v1/districts?state=California"
```

```javascript
const state = 'California';
const response = await fetch(`http://localhost:8000/api/v1/districts?state=${encodeURIComponent(state)}`);
const {districts} = await response.json();
```

**Use Case:** District dropdown after user selects state

**Note:** Currently returns generic 4-district list for all states. Production version would have state-specific districts.

---

### Session Management Endpoints

#### `POST /api/v1/automation/start` ⭐ START HERE

**Description:** Initialize browser session, login to WestLaw, navigate to dockets page

**Request Body:**
```json
{
  "include_docket": false
}
```

**Request Fields:**
- `include_docket` (boolean, optional): Reserved for future use. Always use `false` for now.

**Response (Success):**
```json
{
  "status": "success",
  "message": "Automation started successfully",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response (Error):**
```json
{
  "status": "error",
  "message": "Failed to start browser: Connection refused"
}
```

**Duration:** ~15-20 seconds (browser startup + login + page navigation)

**What Happens:**
1. Launches Chrome browser (headless or visible)
2. Navigates to WestLaw gateway
3. Performs authentication
4. Navigates to IAC configuration
5. Navigates to WestLaw login
6. Logs in with credentials
7. Navigates to dockets page
8. Returns `session_id` for subsequent operations

**Important:**
- **Store the `session_id`** - you'll need it for every subsequent request
- **This is the slowest operation** - show a loading indicator
- **Session remains active** until you call `/session/cleanup`
- **Browser stays open** until cleanup

**Examples:**

```bash
curl -X POST http://localhost:8000/api/v1/automation/start \
  -H "Content-Type: application/json" \
  -d '{"include_docket": false}'
```

```javascript
const response = await fetch('http://localhost:8000/api/v1/automation/start', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({include_docket: false})
});
const {session_id} = await response.json();
console.log('Session started:', session_id);
```

```python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/automation/start',
    json={'include_docket': False}
)
data = response.json()
session_id = data['session_id']
print(f'Session started: {session_id}')
```

**Error Codes:**
- `500`: Browser startup failed, login failed, or navigation error

**TypeScript Interface:**
```typescript
interface SessionStartRequest {
  include_docket: boolean;
}

interface SessionResponse {
  status: 'success' | 'error';
  message: string;
  session_id: string;
}
```

---

#### `POST /api/v1/session/cleanup` ⭐ ALWAYS CALL WHEN DONE

**Description:** Close browser and free resources

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
  "message": "Session cleaned up successfully"
}
```

**Duration:** ~1 second

**What Happens:**
1. Closes the browser window
2. Terminates WebDriver session
3. Frees memory and resources
4. Removes session from server storage

**Critical:** Always call this endpoint when:
- Workflow completes successfully
- Workflow fails (use try/finally)
- User cancels operation
- Session times out

**Consequences of not cleaning up:**
- Browser remains open consuming memory
- Server resources leak
- Eventually hits max concurrent sessions

**Examples:**

```bash
curl -X POST http://localhost:8000/api/v1/session/cleanup \
  -H "Content-Type: application/json" \
  -d '{"session_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

```javascript
// Always use try/finally pattern
let sessionId = null;
try {
  sessionId = await startAutomation();
  await doWork(sessionId);
} finally {
  if (sessionId) {
    await fetch('http://localhost:8000/api/v1/session/cleanup', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({session_id: sessionId})
    });
  }
}
```

**Error Codes:**
- `404`: Session not found (already cleaned up or never existed)
- `500`: Error closing browser

**TypeScript Interface:**
```typescript
interface SessionCleanupRequest {
  session_id: string;
}
```

---

#### `GET /api/v1/sessions`

**Description:** List all active sessions (for monitoring/debugging)

**Response:**
```json
{
  "active_sessions": [
    {
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "started_at": "2026-02-13T10:30:00Z"
    },
    {
      "session_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
      "started_at": "2026-02-13T10:35:00Z"
    }
  ]
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/sessions
```

**Use Case:** Admin dashboard showing active automation sessions

---

### Docket Selection Endpoints

#### `POST /api/v1/docket/select`

**Description:** Navigate docket hierarchy (category → specific docket)

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "category": "Dockets by State",
  "specific_docket": "California"
}
```

**Request Fields:**
- `session_id` (string, required): Session ID from `/automation/start`
- `category` (string, required): Docket category (must match `/docket-categories` response)
- `specific_docket` (string, required): Specific docket within category

**Valid Categories:**
- `"Federal Dockets by Court"`
- `"Federal Dockets by Agency"`
- `"Dockets by State"` ← Most common
- `"Dockets by Territory"`
- `"International"`
- `"Dockets by Topic"`

**Response:**
```json
{
  "status": "success",
  "message": "Docket selected successfully"
}
```

**Duration:** ~2-3 seconds

**What Happens:**
1. Clicks "Content Types" menu
2. Hovers over "Dockets"
3. Clicks specified category (e.g., "Dockets by State")
4. Waits for submenu to load
5. Clicks specific docket (e.g., "California")
6. Waits for page navigation

**Examples:**

```bash
curl -X POST http://localhost:8000/api/v1/docket/select \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "category": "Dockets by State",
    "specific_docket": "California"
  }'
```

```javascript
await fetch('http://localhost:8000/api/v1/docket/select', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    session_id: sessionId,
    category: 'Dockets by State',
    specific_docket: 'California'
  })
});
```

**Error Codes:**
- `404`: Session not found
- `500`: Element not found, navigation timeout, invalid category/docket

**TypeScript Interface:**
```typescript
interface DocketSelectRequest {
  session_id: string;
  category: string;
  specific_docket: string;
}
```

---

#### `POST /api/v1/district/select`

**Description:** Select federal district within a state

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "state": "California",
  "district": "Central District"
}
```

**Request Fields:**
- `session_id` (string, required): Session ID
- `state` (string, required): State name (must match previous docket selection)
- `district` (string, required): District name

**Valid Districts:**
- `"Central District"`
- `"Northern District"`
- `"Southern District"`
- `"Eastern District"`

**Response:**
```json
{
  "status": "success",
  "message": "District selected successfully"
}
```

**Duration:** ~2-3 seconds

**What Happens:**
1. Finds district link on page
2. Clicks district link
3. Waits for page navigation
4. Verifies navigation success

**Examples:**

```bash
curl -X POST http://localhost:8000/api/v1/district/select \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "state": "California",
    "district": "Central District"
  }'
```

```javascript
await fetch('http://localhost:8000/api/v1/district/select', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    session_id: sessionId,
    state: 'California',
    district: 'Central District'
  })
});
```

**Error Codes:**
- `404`: Session not found
- `500`: District not found, navigation failed

**TypeScript Interface:**
```typescript
interface DistrictSelectRequest {
  session_id: string;
  state: string;
  district: string;
}
```

---

#### `POST /api/v1/docket/search`

**Description:** Search for specific docket number

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "docket_number": "3:26-CV-00397"
}
```

**Request Fields:**
- `session_id` (string, required): Session ID
- `docket_number` (string, required): Docket number in standard format

**Docket Number Format:**
- Pattern: `N:NN-CV-NNNNN`
- Examples: `"1:25-CV-01815"`, `"3:26-CV-00397"`, `"2:24-CV-12345"`

**Response:**
```json
{
  "status": "success",
  "message": "Docket search completed successfully"
}
```

**Duration:** ~3-5 seconds

**What Happens:**
1. Locates docket number input field
2. **Removes `maxlength` attribute** (critical bug fix - see MEMORY.md)
3. Enters docket number character-by-character with delays
4. Verifies entered value matches request
5. Clicks search button
6. Waits for search results

**Critical Bug Fix:** The input field has a `maxlength` attribute that can truncate entries. The backend automatically removes this before entering the docket number and verifies the full number was entered correctly.

**Examples:**

```bash
curl -X POST http://localhost:8000/api/v1/docket/search \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "docket_number": "3:26-CV-00397"
  }'
```

```javascript
await fetch('http://localhost:8000/api/v1/docket/search', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    session_id: sessionId,
    docket_number: '3:26-CV-00397'
  })
});
```

**Error Codes:**
- `404`: Session not found
- `500`: Input field not found, verification failed, search failed

**TypeScript Interface:**
```typescript
interface DocketSearchRequest {
  session_id: string;
  docket_number: string;
}
```

---

### Alert Creation Endpoints

#### `POST /api/v1/alert/create`

**Description:** Click "Create Docket Alert" button to initiate alert creation

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
  "message": "Alert creation initiated"
}
```

**Duration:** ~2 seconds

**What Happens:**
1. Locates notification/alert icon
2. Clicks to open alert menu
3. Clicks "Create Docket Alert" option
4. Waits for alert configuration form to appear

**Examples:**

```bash
curl -X POST http://localhost:8000/api/v1/alert/create \
  -H "Content-Type": application/json" \
  -d '{"session_id": "550e8400-e29b-41d4-a716-446655440000"}'
```

```javascript
await fetch('http://localhost:8000/api/v1/alert/create', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({session_id: sessionId})
});
```

**Error Codes:**
- `404`: Session not found
- `500`: Alert button not found, form didn't open

**TypeScript Interface:**
```typescript
interface AlertCreateRequest {
  session_id: string;
}
```

---

#### `POST /api/v1/alert/complete-setup` ⭐ FINAL STEP

**Description:** Fill out alert form with all details and save

**Request Body:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "alert_name": "Important Case Alert",
  "alert_description": "Track updates for case 3:26-CV-00397",
  "user_email": "user@example.com",
  "frequency": "daily",
  "alert_times": ["5am", "3pm"]
}
```

**Request Fields:**

| Field | Type | Required | Description | Valid Values |
|-------|------|----------|-------------|--------------|
| `session_id` | string | Yes | Session ID | UUID |
| `alert_name` | string | Yes | Alert name | Non-empty string |
| `alert_description` | string | No | Alert description | Any string |
| `user_email` | string | Yes | Email for alerts | Valid email format |
| `frequency` | string | Yes | Alert frequency | `"daily"`, `"weekdays"`, `"weekly"`, `"biweekly"`, `"monthly"` |
| `alert_times` | array | Yes | Times to receive alerts | 1-4 items from: `"5am"`, `"12pm"`, `"3pm"`, `"5pm"` |

**Response:**
```json
{
  "status": "success",
  "message": "Alert setup completed successfully"
}
```

**Duration:** ~3-5 seconds

**What Happens:**
1. Fills alert name field
2. Fills description field (if provided)
3. Fills email field
4. Selects frequency from dropdown
5. Checks time checkboxes for each specified time
6. Clicks "Save" button
7. Waits for confirmation

**Validation:**
- **alert_name**: Cannot be empty
- **user_email**: Must be valid email format (validated by Pydantic EmailStr)
- **frequency**: Must be one of the 5 valid values
- **alert_times**: Must have 1-4 items, each must be valid time value

**Examples:**

```bash
curl -X POST http://localhost:8000/api/v1/alert/complete-setup \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "alert_name": "Important Case Alert",
    "alert_description": "Track updates for case 3:26-CV-00397",
    "user_email": "user@example.com",
    "frequency": "daily",
    "alert_times": ["5am", "3pm"]
  }'
```

```javascript
await fetch('http://localhost:8000/api/v1/alert/complete-setup', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    session_id: sessionId,
    alert_name: 'Important Case Alert',
    alert_description: 'Track updates for case 3:26-CV-00397',
    user_email: 'user@example.com',
    frequency: 'daily',
    alert_times: ['5am', '3pm']
  })
});
```

**Error Codes:**
- `404`: Session not found
- `422`: Validation error (invalid email, frequency, or alert times)
- `500`: Form field not found, save failed

**TypeScript Interface:**
```typescript
type AlertFrequency = 'daily' | 'weekdays' | 'weekly' | 'biweekly' | 'monthly';
type AlertTime = '5am' | '12pm' | '3pm' | '5pm';

interface AlertCompleteRequest {
  session_id: string;
  alert_name: string;
  alert_description?: string;
  user_email: string;
  frequency: AlertFrequency;
  alert_times: AlertTime[];
}
```

---

## 4. Complete Workflow Examples

### Vanilla JavaScript (Fetch API)

Complete, production-ready client class:

```javascript
class DocketAlertClient {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.sessionId = null;
  }

  async _call(endpoint, body = null) {
    const options = {
      method: body ? 'POST' : 'GET',
      headers: {'Content-Type': 'application/json'}
    };
    if (body) {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, options);
    if (!response.ok) {
      const error = await response.json().catch(() => ({message: `HTTP ${response.status}`}));
      throw new Error(error.message || `HTTP ${response.status}`);
    }
    return response.json();
  }

  async healthCheck() {
    return this._call('/health');
  }

  async getDocketCategories() {
    return this._call('/api/v1/docket-categories');
  }

  async getStates() {
    const data = await this._call('/api/v1/states');
    return data.states;
  }

  async getDistricts(state) {
    const data = await this._call(`/api/v1/districts?state=${encodeURIComponent(state)}`);
    return data.districts;
  }

  async startAutomation() {
    const data = await this._call('/api/v1/automation/start', {include_docket: false});
    this.sessionId = data.session_id;
    return data;
  }

  async selectDocket(category, specificDocket) {
    if (!this.sessionId) throw new Error('No active session');
    return this._call('/api/v1/docket/select', {
      session_id: this.sessionId,
      category,
      specific_docket: specificDocket
    });
  }

  async selectDistrict(state, district) {
    if (!this.sessionId) throw new Error('No active session');
    return this._call('/api/v1/district/select', {
      session_id: this.sessionId,
      state,
      district
    });
  }

  async searchDocket(docketNumber) {
    if (!this.sessionId) throw new Error('No active session');
    return this._call('/api/v1/docket/search', {
      session_id: this.sessionId,
      docket_number: docketNumber
    });
  }

  async createAlert() {
    if (!this.sessionId) throw new Error('No active session');
    return this._call('/api/v1/alert/create', {
      session_id: this.sessionId
    });
  }

  async completeAlertSetup(alertInfo) {
    if (!this.sessionId) throw new Error('No active session');
    return this._call('/api/v1/alert/complete-setup', {
      session_id: this.sessionId,
      ...alertInfo
    });
  }

  async cleanup() {
    if (!this.sessionId) return;
    try {
      await this._call('/api/v1/session/cleanup', {
        session_id: this.sessionId
      });
    } finally {
      this.sessionId = null;
    }
  }

  async completeWorkflow(docketInfo, alertInfo) {
    try {
      console.log('Starting automation...');
      await this.startAutomation();

      console.log('Selecting docket...');
      await this.selectDocket(docketInfo.category, docketInfo.state);

      console.log('Selecting district...');
      await this.selectDistrict(docketInfo.state, docketInfo.district);

      console.log('Searching docket number...');
      await this.searchDocket(docketInfo.docketNumber);

      console.log('Creating alert...');
      await this.createAlert();

      console.log('Completing alert setup...');
      await this.completeAlertSetup(alertInfo);

      console.log('✓ Alert created successfully!');
      return {success: true};
    } catch (error) {
      console.error('✗ Workflow failed:', error);
      throw error;
    } finally {
      console.log('Cleaning up session...');
      await this.cleanup();
    }
  }
}

// Usage Example
async function main() {
  const client = new DocketAlertClient('http://localhost:8000');

  try {
    await client.completeWorkflow(
      {
        category: 'Dockets by State',
        state: 'California',
        district: 'Central District',
        docketNumber: '3:26-CV-00397'
      },
      {
        alert_name: 'Important Case Alert',
        alert_description: 'Track updates for case 3:26-CV-00397',
        user_email: 'user@example.com',
        frequency: 'daily',
        alert_times: ['5am', '3pm']
      }
    );
  } catch (error) {
    console.error('Failed to create alert:', error.message);
  }
}

// Run it
main();
```

---

### React with Hooks

Custom hook with progress tracking:

```jsx
// hooks/useDocketAlert.js
import {useState, useCallback} from 'react';

export const useDocketAlert = (apiBaseURL = 'http://localhost:8000') => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState('');

  const createAlert = useCallback(async (docketInfo, alertInfo) => {
    setLoading(true);
    setError(null);
    setProgress(0);

    try {
      // Step 1: Start automation (40% of time)
      setCurrentStep('Initializing browser and logging in...');
      setProgress(10);
      const startResponse = await fetch(`${apiBaseURL}/api/v1/automation/start`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({include_docket: false})
      });
      if (!startResponse.ok) throw new Error('Failed to start automation');
      const {session_id} = await startResponse.json();
      setSessionId(session_id);
      setProgress(30);

      // Step 2: Select docket (10% of time)
      setCurrentStep('Selecting docket category...');
      const docketResponse = await fetch(`${apiBaseURL}/api/v1/docket/select`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          session_id,
          category: docketInfo.category,
          specific_docket: docketInfo.state
        })
      });
      if (!docketResponse.ok) throw new Error('Failed to select docket');
      setProgress(50);

      // Step 3: Select district (10% of time)
      setCurrentStep('Selecting district...');
      const districtResponse = await fetch(`${apiBaseURL}/api/v1/district/select`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          session_id,
          state: docketInfo.state,
          district: docketInfo.district
        })
      });
      if (!districtResponse.ok) throw new Error('Failed to select district');
      setProgress(65);

      // Step 4: Search docket number (15% of time)
      setCurrentStep('Searching docket number...');
      const searchResponse = await fetch(`${apiBaseURL}/api/v1/docket/search`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          session_id,
          docket_number: docketInfo.docketNumber
        })
      });
      if (!searchResponse.ok) throw new Error('Failed to search docket');
      setProgress(80);

      // Step 5: Create alert (5% of time)
      setCurrentStep('Creating alert...');
      const createResponse = await fetch(`${apiBaseURL}/api/v1/alert/create`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({session_id})
      });
      if (!createResponse.ok) throw new Error('Failed to create alert');
      setProgress(90);

      // Step 6: Complete setup (15% of time)
      setCurrentStep('Completing alert setup...');
      const completeResponse = await fetch(`${apiBaseURL}/api/v1/alert/complete-setup`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({session_id, ...alertInfo})
      });
      if (!completeResponse.ok) throw new Error('Failed to complete alert setup');
      setProgress(100);

      setCurrentStep('Alert created successfully!');

      // Cleanup
      await fetch(`${apiBaseURL}/api/v1/session/cleanup`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({session_id})
      });

      return {success: true};
    } catch (err) {
      setError(err.message);
      setCurrentStep(`Error: ${err.message}`);
      // Cleanup on error
      if (sessionId) {
        try {
          await fetch(`${apiBaseURL}/api/v1/session/cleanup`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({session_id: sessionId})
          });
        } catch (cleanupError) {
          console.error('Cleanup failed:', cleanupError);
        }
      }
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiBaseURL]);

  return {createAlert, loading, error, progress, currentStep};
};

// Component using the hook
function DocketAlertForm() {
  const {createAlert, loading, error, progress, currentStep} = useDocketAlert();
  const [formData, setFormData] = useState({
    category: 'Dockets by State',
    state: 'California',
    district: 'Central District',
    docketNumber: '',
    alertName: '',
    alertDescription: '',
    email: '',
    frequency: 'daily',
    times: ['5am']
  });

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      await createAlert(
        {
          category: formData.category,
          state: formData.state,
          district: formData.district,
          docketNumber: formData.docketNumber
        },
        {
          alert_name: formData.alertName,
          alert_description: formData.alertDescription,
          user_email: formData.email,
          frequency: formData.frequency,
          alert_times: formData.times
        }
      );
      alert('Alert created successfully!');
    } catch (err) {
      console.error('Failed to create alert:', err);
    }
  };

  return (
    <div className="docket-alert-form">
      <h2>Create Docket Alert</h2>

      {loading && (
        <div className="progress-section">
          <div className="progress-bar">
            <div className="progress-fill" style={{width: `${progress}%`}} />
          </div>
          <p className="progress-text">{currentStep} ({progress}%)</p>
        </div>
      )}

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Docket Number:</label>
          <input
            type="text"
            value={formData.docketNumber}
            onChange={(e) => setFormData({...formData, docketNumber: e.target.value})}
            placeholder="3:26-CV-00397"
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label>Alert Name:</label>
          <input
            type="text"
            value={formData.alertName}
            onChange={(e) => setFormData({...formData, alertName: e.target.value})}
            placeholder="Important Case Alert"
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label>Email:</label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
            placeholder="user@example.com"
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label>Frequency:</label>
          <select
            value={formData.frequency}
            onChange={(e) => setFormData({...formData, frequency: e.target.value})}
            disabled={loading}
          >
            <option value="daily">Daily</option>
            <option value="weekdays">Weekdays</option>
            <option value="weekly">Weekly</option>
            <option value="biweekly">Biweekly</option>
            <option value="monthly">Monthly</option>
          </select>
        </div>

        <div className="form-group">
          <label>Alert Times:</label>
          {['5am', '12pm', '3pm', '5pm'].map(time => (
            <label key={time}>
              <input
                type="checkbox"
                checked={formData.times.includes(time)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setFormData({...formData, times: [...formData.times, time]});
                  } else {
                    setFormData({...formData, times: formData.times.filter(t => t !== time)});
                  }
                }}
                disabled={loading}
              />
              {time}
            </label>
          ))}
        </div>

        <button type="submit" disabled={loading}>
          {loading ? 'Creating Alert...' : 'Create Alert'}
        </button>
      </form>
    </div>
  );
}

export default DocketAlertForm;
```

---

### Python Requests

Complete Python client:

```python
import requests
from typing import List, Dict, Any, Optional


class DocketAlertClient:
    """Client for Docket Alert Automation API."""

    def __init__(self, base_url: str = 'http://localhost:8000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.session_id: Optional[str] = None

    def _call(self, endpoint: str, method: str = 'GET', json_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API call."""
        url = f'{self.base_url}{endpoint}'
        response = self.session.request(method, url, json=json_data)
        response.raise_for_status()
        return response.json()

    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        return self._call('/health')

    def get_docket_categories(self) -> Dict[str, List[str]]:
        """Get docket categories."""
        data = self._call('/api/v1/docket-categories')
        return data['categories']

    def get_states(self) -> List[str]:
        """Get available states."""
        data = self._call('/api/v1/states')
        return data['states']

    def get_districts(self, state: str) -> List[str]:
        """Get districts for a state."""
        data = self._call(f'/api/v1/districts?state={state}')
        return data['districts']

    def start_automation(self) -> str:
        """Start automation and return session ID."""
        data = self._call(
            '/api/v1/automation/start',
            method='POST',
            json_data={'include_docket': False}
        )
        self.session_id = data['session_id']
        return self.session_id

    def select_docket(self, category: str, specific_docket: str) -> Dict[str, Any]:
        """Select docket category and specific docket."""
        if not self.session_id:
            raise ValueError('No active session')
        return self._call(
            '/api/v1/docket/select',
            method='POST',
            json_data={
                'session_id': self.session_id,
                'category': category,
                'specific_docket': specific_docket
            }
        )

    def select_district(self, state: str, district: str) -> Dict[str, Any]:
        """Select district."""
        if not self.session_id:
            raise ValueError('No active session')
        return self._call(
            '/api/v1/district/select',
            method='POST',
            json_data={
                'session_id': self.session_id,
                'state': state,
                'district': district
            }
        )

    def search_docket(self, docket_number: str) -> Dict[str, Any]:
        """Search for docket number."""
        if not self.session_id:
            raise ValueError('No active session')
        return self._call(
            '/api/v1/docket/search',
            method='POST',
            json_data={
                'session_id': self.session_id,
                'docket_number': docket_number
            }
        )

    def create_alert(self) -> Dict[str, Any]:
        """Create docket alert."""
        if not self.session_id:
            raise ValueError('No active session')
        return self._call(
            '/api/v1/alert/create',
            method='POST',
            json_data={'session_id': self.session_id}
        )

    def complete_alert_setup(
        self,
        alert_name: str,
        user_email: str,
        frequency: str,
        alert_times: List[str],
        alert_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Complete alert setup."""
        if not self.session_id:
            raise ValueError('No active session')

        payload = {
            'session_id': self.session_id,
            'alert_name': alert_name,
            'user_email': user_email,
            'frequency': frequency,
            'alert_times': alert_times
        }
        if alert_description:
            payload['alert_description'] = alert_description

        return self._call('/api/v1/alert/complete-setup', method='POST', json_data=payload)

    def cleanup(self) -> None:
        """Cleanup session."""
        if not self.session_id:
            return
        try:
            self._call(
                '/api/v1/session/cleanup',
                method='POST',
                json_data={'session_id': self.session_id}
            )
        finally:
            self.session_id = None

    def complete_workflow(
        self,
        docket_info: Dict[str, str],
        alert_info: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Execute complete workflow."""
        try:
            print('Starting automation...')
            self.start_automation()

            print('Selecting docket...')
            self.select_docket(docket_info['category'], docket_info['state'])

            print('Selecting district...')
            self.select_district(docket_info['state'], docket_info['district'])

            print('Searching docket number...')
            self.search_docket(docket_info['docket_number'])

            print('Creating alert...')
            self.create_alert()

            print('Completing alert setup...')
            self.complete_alert_setup(**alert_info)

            print('✓ Alert created successfully!')
            return {'success': True}
        except Exception as e:
            print(f'✗ Workflow failed: {e}')
            raise
        finally:
            print('Cleaning up session...')
            self.cleanup()


# Usage Example
if __name__ == '__main__':
    client = DocketAlertClient('http://localhost:8000')

    try:
        client.complete_workflow(
            docket_info={
                'category': 'Dockets by State',
                'state': 'California',
                'district': 'Central District',
                'docket_number': '3:26-CV-00397'
            },
            alert_info={
                'alert_name': 'Important Case Alert',
                'alert_description': 'Track updates for case 3:26-CV-00397',
                'user_email': 'user@example.com',
                'frequency': 'daily',
                'alert_times': ['5am', '3pm']
            }
        )
    except Exception as e:
        print(f'Failed to create alert: {e}')
```

---

## 5. Best Practices & Optimization

### Error Handling

#### Network Errors

Always handle network failures gracefully:

```javascript
async function callAPI(url, options) {
  try {
    const response = await fetch(url, options);
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || `HTTP ${response.status}`);
    }
    return response.json();
  } catch (error) {
    if (error.name === 'TypeError' || error.message.includes('fetch')) {
      throw new Error('Cannot connect to API server. Is it running?');
    }
    throw error;
  }
}
```

#### Timeout Handling

Browser automation is slow - use appropriate timeouts:

```javascript
async function callAPIWithTimeout(url, options, timeoutMs = 30000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(timeout);
    return response.json();
  } catch (error) {
    clearTimeout(timeout);
    if (error.name === 'AbortError') {
      throw new Error(`Request timeout after ${timeoutMs}ms`);
    }
    throw error;
  }
}

// Usage
await callAPIWithTimeout(
  'http://localhost:8000/api/v1/automation/start',
  {method: 'POST', ...},
  30000  // 30 seconds for browser startup
);
```

#### Retry Logic with Exponential Backoff

For transient failures:

```javascript
async function retryAPI(fn, maxRetries = 3, baseDelay = 1000) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === maxRetries - 1) throw error;

      const delay = baseDelay * Math.pow(2, i); // 1s, 2s, 4s
      console.log(`Retry ${i + 1}/${maxRetries} after ${delay}ms...`);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}

// Usage
await retryAPI(() => fetch('http://localhost:8000/api/v1/docket/select', {...}));
```

---

### Session Management

#### Always Cleanup

Use try/finally to ensure cleanup:

```javascript
let sessionId = null;

try {
  sessionId = await startAutomation();
  await doWork(sessionId);
} catch (error) {
  console.error('Workflow failed:', error);
  throw error;
} finally {
  if (sessionId) {
    await cleanupSession(sessionId);
  }
}
```

#### Session Timeout Detection

Handle 404 errors (session expired):

```javascript
async function withSessionRecovery(fn, sessionId) {
  try {
    return await fn(sessionId);
  } catch (error) {
    if (error.message.includes('404') || error.message.includes('not found')) {
      console.log('Session expired, restarting...');
      const newSessionId = await startAutomation();
      return await fn(newSessionId);
    }
    throw error;
  }
}
```

---

### Performance Optimization

#### Caching Static Data

Docket categories never change - cache them:

```javascript
let cachedCategories = null;

async function getDocketCategories() {
  if (cachedCategories) {
    console.log('Using cached categories');
    return cachedCategories;
  }

  const response = await fetch('http://localhost:8000/api/v1/docket-categories');
  cachedCategories = await response.json();

  // Cache for 1 hour
  setTimeout(() => { cachedCategories = null; }, 3600000);

  return cachedCategories;
}
```

#### Connection Pooling (Python)

Reuse `requests.Session()`:

```python
# Good - reuses connections
session = requests.Session()
session.get('http://localhost:8000/health')
session.post('http://localhost:8000/api/v1/automation/start', json={...})

# Bad - creates new connection each time
requests.get('http://localhost:8000/health')
requests.post('http://localhost:8000/api/v1/automation/start', json={...})
```

#### Sequential Operations (NOT Parallel)

**DON'T** try to parallelize the workflow - it's stateful:

```javascript
// ❌ WRONG - workflow must be sequential
await Promise.all([
  selectDocket(sessionId, category, docket),
  selectDistrict(sessionId, state, district)
]);

// ✅ CORRECT - operations depend on each other
await selectDocket(sessionId, category, docket);
await selectDistrict(sessionId, state, district);
```

---

### TypeScript Type Safety

Define all types for safety:

```typescript
// types.ts
export interface SessionResponse {
  status: 'success' | 'error';
  message: string;
  session_id: string;
}

export interface DocketInfo {
  category: string;
  state: string;
  district: string;
  docketNumber: string;
}

export type AlertFrequency = 'daily' | 'weekdays' | 'weekly' | 'biweekly' | 'monthly';
export type AlertTime = '5am' | '12pm' | '3pm' | '5pm';

export interface AlertInfo {
  alert_name: string;
  alert_description?: string;
  user_email: string;
  frequency: AlertFrequency;
  alert_times: AlertTime[];
}

// api-client.ts
export class DocketAlertClient {
  async startAutomation(): Promise<SessionResponse> {
    const response = await fetch(...);
    return response.json();
  }

  async completeWorkflow(
    docketInfo: DocketInfo,
    alertInfo: AlertInfo
  ): Promise<{success: boolean}> {
    // ...
  }
}
```

---

### Security Best Practices

#### Environment-Based Configuration

Never hardcode URLs:

```javascript
// .env.development
REACT_APP_API_URL=http://localhost:8000

// .env.production
REACT_APP_API_URL=https://api.yourdomain.com

// App code
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Production check
if (process.env.NODE_ENV === 'production' && !API_URL.startsWith('https')) {
  console.error('SECURITY: API must use HTTPS in production');
}
```

#### Input Validation

Validate user input before sending to API:

```javascript
function validateDocketNumber(docketNumber) {
  // Format: N:NN-CV-NNNNN
  const regex = /^\d+:\d+-[A-Z]+-\d+$/;
  if (!regex.test(docketNumber)) {
    throw new Error('Invalid docket number format. Expected: N:NN-CV-NNNNN');
  }
  return docketNumber.toUpperCase();
}

function validateEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!regex.test(email)) {
    throw new Error('Invalid email format');
  }
  return email.toLowerCase();
}

function validateAlertTimes(times) {
  const valid = ['5am', '12pm', '3pm', '5pm'];
  if (times.length < 1 || times.length > 4) {
    throw new Error('Must select 1-4 alert times');
  }
  if (!times.every(t => valid.includes(t))) {
    throw new Error(`Invalid alert time. Must be one of: ${valid.join(', ')}`);
  }
  return times;
}
```

#### Logging & Monitoring

Track API calls for debugging:

```javascript
class APIClient {
  async callEndpoint(endpoint, options) {
    const startTime = Date.now();
    const method = options?.method || 'GET';

    console.log(`[API] → ${method} ${endpoint}`);

    try {
      const response = await fetch(endpoint, options);
      const duration = Date.now() - startTime;

      if (!response.ok) {
        console.error(`[API] ✗ ${endpoint} (${response.status}) ${duration}ms`);
        throw new Error(`HTTP ${response.status}`);
      }

      console.log(`[API] ✓ ${endpoint} ${duration}ms`);
      return response.json();
    } catch (error) {
      const duration = Date.now() - startTime;
      console.error(`[API] ✗ ${endpoint} ERROR: ${error.message} (${duration}ms)`);
      throw error;
    }
  }
}
```

---

## 6. UI Integration Patterns

### Progress Tracking

Show users what's happening during long operations:

```javascript
function DocketAlertWizard() {
  const [step, setStep] = useState(0);
  const [sessionId, setSessionId] = useState(null);

  const steps = [
    {
      label: 'Initializing browser and logging in',
      duration: 15000,
      action: async () => {
        const response = await startAutomation();
        setSessionId(response.session_id);
      }
    },
    {
      label: 'Selecting docket category',
      duration: 3000,
      action: async () => {
        await selectDocket(sessionId, category, state);
      }
    },
    {
      label: 'Selecting district',
      duration: 3000,
      action: async () => {
        await selectDistrict(sessionId, state, district);
      }
    },
    {
      label: 'Searching docket number',
      duration: 5000,
      action: async () => {
        await searchDocket(sessionId, docketNumber);
      }
    },
    {
      label: 'Creating alert',
      duration: 2000,
      action: async () => {
        await createAlert(sessionId);
      }
    },
    {
      label: 'Completing alert setup',
      duration: 5000,
      action: async () => {
        await completeAlertSetup(sessionId, alertInfo);
      }
    },
  ];

  const runWorkflow = async () => {
    for (let i = 0; i < steps.length; i++) {
      setStep(i);
      await steps[i].action();
    }
    setStep(steps.length); // Complete
    alert('Alert created successfully!');
  };

  const progressPercent = (step / steps.length) * 100;

  return (
    <div className="wizard">
      <div className="progress-bar">
        <div className="progress-fill" style={{width: `${progressPercent}%`}} />
      </div>
      <p className="progress-text">
        Step {step + 1}/{steps.length}: {steps[step]?.label || 'Complete'}
      </p>
      <button onClick={runWorkflow} disabled={step > 0 && step < steps.length}>
        {step === 0 ? 'Start' : step === steps.length ? 'Done' : 'Running...'}
      </button>
    </div>
  );
}
```

---

### Form Validation

Validate before submitting:

```javascript
function validateAlertForm(formData) {
  const errors = {};

  // Alert name required
  if (!formData.alertName || formData.alertName.trim() === '') {
    errors.alertName = 'Alert name is required';
  }

  // Email required and valid
  if (!formData.email) {
    errors.email = 'Email is required';
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
    errors.email = 'Invalid email format';
  }

  // Docket number format
  if (!formData.docketNumber) {
    errors.docketNumber = 'Docket number is required';
  } else if (!/^\d+:\d+-[A-Z]+-\d+$/.test(formData.docketNumber)) {
    errors.docketNumber = 'Invalid format (expected: N:NN-CV-NNNNN)';
  }

  // Frequency required
  if (!formData.frequency) {
    errors.frequency = 'Frequency is required';
  }

  // Alert times: 1-4 required
  if (!formData.alertTimes || formData.alertTimes.length === 0) {
    errors.alertTimes = 'Select at least one alert time';
  } else if (formData.alertTimes.length > 4) {
    errors.alertTimes = 'Maximum 4 alert times allowed';
  }

  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
}

// In your form component
const handleSubmit = (e) => {
  e.preventDefault();

  const {isValid, errors} = validateAlertForm(formData);
  if (!isValid) {
    setFormErrors(errors);
    return;
  }

  // Proceed with API call
  createAlert(formData);
};
```

---

### Error Display

User-friendly error messages:

```javascript
function ErrorMessage({error, onRetry, onClose}) {
  const getErrorInfo = (error) => {
    if (error.includes('Cannot connect')) {
      return {
        title: 'Connection Error',
        message: 'Unable to connect to the automation server. Please ensure the API server is running.',
        action: 'Check Server',
        icon: '🔌'
      };
    }
    if (error.includes('404') || error.includes('not found')) {
      return {
        title: 'Session Expired',
        message: 'Your session has expired. Please start a new automation workflow.',
        action: 'Restart',
        icon: '⏱️'
      };
    }
    if (error.includes('timeout')) {
      return {
        title: 'Timeout',
        message: 'The operation took too long. Please try again.',
        action: 'Retry',
        icon: '⏳'
      };
    }
    return {
      title: 'Error',
      message: error,
      action: 'Retry',
      icon: '❌'
    };
  };

  const {title, message, action, icon} = getErrorInfo(error);

  return (
    <div className="error-banner">
      <div className="error-icon">{icon}</div>
      <div className="error-content">
        <h3>{title}</h3>
        <p>{message}</p>
      </div>
      <div className="error-actions">
        <button onClick={onRetry}>{action}</button>
        <button onClick={onClose}>Dismiss</button>
      </div>
    </div>
  );
}
```

---

## 7. Testing Guide

### Unit Testing API Calls

#### JavaScript (Jest)

Mock fetch for isolated testing:

```javascript
// api-client.test.js
import {DocketAlertClient} from './api-client';

// Mock fetch globally
global.fetch = jest.fn();

describe('DocketAlertClient', () => {
  let client;

  beforeEach(() => {
    client = new DocketAlertClient('http://localhost:8000');
    fetch.mockClear();
  });

  test('startAutomation returns session_id', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        status: 'success',
        message: 'Automation started',
        session_id: 'test-session-123'
      })
    });

    const response = await client.startAutomation();

    expect(response.session_id).toBe('test-session-123');
    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/v1/automation/start',
      expect.objectContaining({
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({include_docket: false})
      })
    );
  });

  test('handles network errors', async () => {
    fetch.mockRejectedValueOnce(new TypeError('Failed to fetch'));

    await expect(client.startAutomation()).rejects.toThrow('Cannot connect');
  });

  test('handles HTTP errors', async () => {
    fetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      json: async () => ({message: 'Browser startup failed'})
    });

    await expect(client.startAutomation()).rejects.toThrow('Browser startup failed');
  });

  test('cleanup removes session_id', async () => {
    client.sessionId = 'test-session-123';
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({status: 'success'})
    });

    await client.cleanup();

    expect(client.sessionId).toBeNull();
  });
});
```

#### Python (pytest)

Mock requests for isolated testing:

```python
# test_api_client.py
import pytest
from unittest.mock import Mock, patch
from api_client import DocketAlertClient


@pytest.fixture
def mock_session():
    with patch('requests.Session') as mock:
        yield mock.return_value


def test_start_automation(mock_session):
    mock_response = Mock()
    mock_response.json.return_value = {
        'status': 'success',
        'session_id': 'test-session-123'
    }
    mock_response.raise_for_status = Mock()
    mock_session.request.return_value = mock_response

    client = DocketAlertClient()
    session_id = client.start_automation()

    assert session_id == 'test-session-123'
    assert client.session_id == 'test-session-123'
    mock_session.request.assert_called_once_with(
        'POST',
        'http://localhost:8000/api/v1/automation/start',
        json={'include_docket': False}
    )


def test_cleanup_removes_session_id(mock_session):
    client = DocketAlertClient()
    client.session_id = 'test-session-123'

    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_session.request.return_value = mock_response

    client.cleanup()

    assert client.session_id is None
```

---

### Integration Testing

Test against real API in staging:

```javascript
// integration.test.js
describe('Full Docket Alert Workflow', () => {
  const API_URL = process.env.STAGING_API_URL || 'http://localhost:8000';
  let client;

  beforeEach(() => {
    client = new DocketAlertClient(API_URL);
  });

  test('complete workflow succeeds', async () => {
    // Start automation
    const {session_id} = await client.startAutomation();
    expect(session_id).toBeTruthy();
    expect(session_id).toMatch(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/);

    // Select docket
    await client.selectDocket('Dockets by State', 'California');

    // Select district
    await client.selectDistrict('California', 'Central District');

    // Search docket
    await client.searchDocket('1:25-CV-01815');

    // Create alert
    await client.createAlert();

    // Complete setup
    await client.completeAlertSetup({
      alert_name: 'Test Alert',
      user_email: 'test@example.com',
      frequency: 'daily',
      alert_times: ['5am']
    });

    // Cleanup
    await client.cleanup();
  }, 60000); // 60 second timeout

  test('cleanup works even after error', async () => {
    await client.startAutomation();

    // Force an error
    await expect(client.selectDocket('Invalid Category', 'Invalid Docket')).rejects.toThrow();

    // Cleanup should still work
    await expect(client.cleanup()).resolves.not.toThrow();
  }, 30000);
});
```

---

### Load Testing

Test concurrent sessions:

```bash
# Using Apache Bench
echo '{"include_docket": false}' > start.json

ab -n 10 -c 2 \
   -T application/json \
   -p start.json \
   http://localhost:8000/api/v1/automation/start
```

Or Python script:

```python
# load_test.py
import asyncio
import aiohttp
import time


async def start_automation(session, url):
    """Start a single automation session."""
    start_time = time.time()
    try:
        async with session.post(
            f'{url}/api/v1/automation/start',
            json={'include_docket': False}
        ) as response:
            data = await response.json()
            duration = time.time() - start_time
            return {'success': True, 'duration': duration, 'session_id': data['session_id']}
    except Exception as e:
        duration = time.time() - start_time
        return {'success': False, 'duration': duration, 'error': str(e)}


async def load_test(url, num_sessions=10):
    """Test concurrent session creation."""
    print(f'Starting {num_sessions} concurrent automation sessions...')

    async with aiohttp.ClientSession() as session:
        tasks = [start_automation(session, url) for _ in range(num_sessions)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    successes = [r for r in results if isinstance(r, dict) and r.get('success')]
    failures = [r for r in results if isinstance(r, dict) and not r.get('success')]

    print(f'\nResults:')
    print(f'  Successful: {len(successes)}/{num_sessions}')
    print(f'  Failed: {len(failures)}/{num_sessions}')

    if successes:
        avg_duration = sum(r['duration'] for r in successes) / len(successes)
        print(f'  Average duration: {avg_duration:.2f}s')


if __name__ == '__main__':
    asyncio.run(load_test('http://localhost:8000', num_sessions=5))
```

---

## 8. Troubleshooting Guide

### Common Issues & Solutions

#### Problem: "Cannot connect to API server"

**Symptoms:**
- `TypeError: Failed to fetch`
- `Connection refused`
- `ERR_CONNECTION_REFUSED`

**Cause:** API server not running or wrong URL

**Solution:**
```bash
# Check if server is running
curl http://localhost:8000/health

# If not running, start it
cd app
python run_api.py

# Check correct port
netstat -an | grep 8000  # Linux/Mac
netstat -an | findstr 8000  # Windows

# Verify URL in frontend matches server
console.log(API_BASE_URL);  // Should be http://localhost:8000
```

---

#### Problem: "Session not found" (404)

**Symptoms:**
- HTTP 404 error on docket/alert endpoints
- Error message: "Session not found"

**Cause:** Session expired, cleaned up, or invalid session_id

**Solution:**
1. Session may have been cleaned up by server restart
2. Session timeout (if implemented)
3. Wrong session_id sent

```javascript
// Implement session recovery
async function withSessionRecovery(fn) {
  try {
    return await fn();
  } catch (error) {
    if (error.message.includes('404')) {
      console.log('Session expired, restarting automation...');
      const newSessionId = await startAutomation();
      return await fn();
    }
    throw error;
  }
}
```

---

#### Problem: "Timeout Error" - Request takes too long

**Symptoms:**
- Request aborts after N seconds
- "AbortError" or "Timeout"

**Cause:** Browser automation can take 15-30 seconds

**Solution:**
Use appropriate timeouts:

```javascript
// Good timeout values
const TIMEOUTS = {
  START: 30000,         // 30s for browser startup
  DOCKET_SELECT: 10000, // 10s for navigation
  DISTRICT_SELECT: 10000,
  DOCKET_SEARCH: 10000,
  ALERT_CREATE: 5000,
  ALERT_COMPLETE: 10000,
  CLEANUP: 5000
};

// Apply per endpoint
await callAPIWithTimeout(
  '/api/v1/automation/start',
  {...},
  TIMEOUTS.START
);
```

---

#### Problem: "Element not found" errors in backend logs

**Symptoms:**
- 500 error from API
- Backend logs show "ElementNotFoundError" or "TimeoutException"

**Cause:** WestLaw UI changed or timing issue

**Solution:**
1. Check backend logs for specific error
2. WestLaw UI may have changed - report to API maintainer
3. Temporary glitch - retry the operation

```javascript
// Implement retry
await retryAPI(
  () => selectDocket(sessionId, category, docket),
  maxRetries = 2
);
```

---

#### Problem: Slow performance

**Symptoms:**
- Requests take longer than expected
- Overall workflow > 1 minute

**Possible Causes & Solutions:**

1. **Network latency**
   ```bash
   # Test network speed to API
   time curl http://localhost:8000/health
   ```

2. **Not using production mode**
   ```bash
   # Use production mode for better performance
   ENVIRONMENT=production python run_api.py
   ```

3. **Not caching static data**
   ```javascript
   // Cache docket categories
   const cachedCategories = await getCategoriesOnce();
   ```

4. **Creating too many sessions**
   ```javascript
   // Reuse session_id where possible
   // Don't call /automation/start multiple times
   ```

---

#### Problem: CORS errors in browser

**Symptoms:**
- "CORS policy: No 'Access-Control-Allow-Origin' header"
- "Blocked by CORS policy"

**Cause:** Cross-origin request from different domain

**Solution:**

Development (already configured):
- API has CORS enabled for all origins (`allow_origins=["*"]`)

Production (needs configuration):
```python
# app/api/app.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specific origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Debugging Tips

1. **Check API logs**: Backend logs show detailed Selenium operations
   ```bash
   cd app
   python run_api.py  # Watch console output
   ```

2. **Use browser DevTools**: Network tab shows request/response
   - Open DevTools (F12)
   - Network tab
   - Filter by "Fetch/XHR"
   - Inspect request/response

3. **Test with curl**: Isolate frontend vs backend issues
   ```bash
   curl -v http://localhost:8000/health
   ```

4. **Check active sessions**: See what's running
   ```bash
   curl http://localhost:8000/api/v1/sessions
   ```

5. **Screenshots**: Backend saves error screenshots to `app/screenshots/`
   - Check this folder after failures
   - Screenshots show exact state when error occurred

6. **Verbose logging**: Add logging to your API calls
   ```javascript
   console.log('[API] Starting automation...');
   const response = await fetch(...);
   console.log('[API] Response:', await response.json());
   ```

---

## 9. Deployment Guide

### Development Environment

**Terminal 1: Start API server**
```bash
cd app
python run_api.py
```

**Terminal 2: Start your frontend**
```bash
# React
npm run dev

# Vue
npm run serve

# Angular
ng serve
```

**Environment Variables:**
```bash
# .env.development
REACT_APP_API_URL=http://localhost:8000
```

---

### Production Deployment

#### Option 1: Docker

**Dockerfile for API:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Chrome for Selenium
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ .

# Environment
ENV ENVIRONMENT=production
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Run
CMD ["python", "run_api.py"]
```

**Build and run:**
```bash
docker build -t docket-alert-api .
docker run -d -p 8000:8000 --name docket-api docket-alert-api
```

**Docker Compose (API + Frontend):**
```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
    restart: always

  frontend:
    image: nginx:alpine
    volumes:
      - ./frontend/build:/usr/share/nginx/html
    ports:
      - "80:80"
    depends_on:
      - api
    restart: always
```

---

#### Option 2: Systemd Service (Linux)

**Create service file:**
```ini
# /etc/systemd/system/docket-api.service
[Unit]
Description=Docket Alert Automation API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/docket-alert/app
Environment="ENVIRONMENT=production"
Environment="PYTHONUNBUFFERED=1"
ExecStart=/usr/bin/python3 run_api.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable docket-api
sudo systemctl start docket-api
sudo systemctl status docket-api
```

---

#### Option 3: Nginx Reverse Proxy

**Nginx configuration:**
```nginx
# /etc/nginx/sites-available/docket-api
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Increase timeout for long-running operations
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }
}
```

**Enable and restart:**
```bash
sudo ln -s /etc/nginx/sites-available/docket-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

### Frontend Deployment

**Build frontend:**
```bash
npm run build
# Creates build/ or dist/ folder
```

**Deploy options:**
1. **Vercel/Netlify**: Connect GitHub repo, auto-deploy
2. **Nginx**: Serve static files from `build/`
3. **S3 + CloudFront**: AWS static hosting
4. **Docker**: Multi-stage build with nginx

**Environment variables:**
```bash
# .env.production
REACT_APP_API_URL=https://api.yourdomain.com
```

---

### Security Checklist

Before going live:

- [ ] **HTTPS**: Use SSL certificate (Let's Encrypt, CloudFlare)
- [ ] **CORS**: Configure specific origins (not `"*"`)
  ```python
  allow_origins=["https://yourdomain.com"]
  ```
- [ ] **Authentication**: Implement API keys or Bearer tokens
- [ ] **Rate Limiting**: Prevent abuse
- [ ] **Environment Variables**: Use `.env` files, not hardcoded secrets
- [ ] **Firewall**: Restrict API access to known IPs
- [ ] **Monitoring**: Set up logging and alerts
- [ ] **Backups**: Regular backups of any persistent data

---

## 10. FAQ

**Q: Do I need to authenticate to use the API?**
A: Currently no. Future versions will implement Bearer token authentication.

**Q: How long does a session last?**
A: Sessions persist until you call `/session/cleanup` or the server restarts. Always cleanup when done.

**Q: Can I run multiple workflows in parallel?**
A: Yes! Each call to `/automation/start` creates an isolated browser session. You can have multiple concurrent sessions.

**Q: Why does `/automation/start` take so long?**
A: It starts a Chrome browser, logs into WestLaw, and navigates to the dockets page. This typically takes 15-20 seconds.

**Q: Can I reuse a session_id?**
A: Yes, but only for sequential operations. Once you complete a workflow and cleanup, the session is destroyed.

**Q: What happens if I forget to cleanup a session?**
A: The browser remains open, consuming memory. The server will cleanup on shutdown, but you should always explicitly cleanup.

**Q: Can I cache the docket categories?**
A: Yes! `/api/v1/docket-categories` returns static data. Cache it aggressively to reduce API calls.

**Q: How do I test the API?**
A: Use curl, Postman, or your frontend's fetch() against `http://localhost:8000`. See section 3 for examples.

**Q: What's the difference between states and districts?**
A: States (CA, NY, TX) contain multiple federal districts (Central, Northern, Southern, Eastern).

**Q: Can I skip the district selection?**
A: No, the workflow requires: docket → state → district → docket number → alert.

**Q: What docket number format is accepted?**
A: Standard federal format: `"N:NN-CV-NNNNN"` (e.g., "3:26-CV-00397")

**Q: What email addresses are accepted?**
A: Any valid email format. The backend uses Pydantic's EmailStr validation.

**Q: How many alert times can I select?**
A: 1-4 times from: `"5am"`, `"12pm"`, `"3pm"`, `"5pm"`

**Q: Does the API support webhooks?**
A: Not yet. This is planned for a future version.

**Q: Can I get real-time progress updates?**
A: Not currently. The API uses request-response pattern. WebSocket support is planned for the future.

**Q: Is the API stateless?**
A: No, it's stateful. The browser session persists across multiple API calls using the `session_id`.

---

## 11. Appendices

### Appendix A: Complete TypeScript Types

```typescript
// types.ts - Complete type definitions

/** Session management */
export interface SessionStartRequest {
  include_docket: boolean;
}

export interface SessionResponse {
  status: 'success' | 'error';
  message: string;
  session_id: string;
}

export interface SessionCleanupRequest {
  session_id: string;
}

/** Metadata */
export interface DocketCategoriesResponse {
  categories: {
    [category: string]: string[];
  };
}

export interface StatesResponse {
  states: string[];
}

export interface DistrictsResponse {
  districts: string[];
}

/** Docket selection */
export interface DocketSelectRequest {
  session_id: string;
  category: string;
  specific_docket: string;
}

export interface DistrictSelectRequest {
  session_id: string;
  state: string;
  district: string;
}

export interface DocketSearchRequest {
  session_id: string;
  docket_number: string;
}

/** Alert creation */
export interface AlertCreateRequest {
  session_id: string;
}

export type AlertFrequency = 'daily' | 'weekdays' | 'weekly' | 'biweekly' | 'monthly';
export type AlertTime = '5am' | '12pm' | '3pm' | '5pm';

export interface AlertCompleteRequest {
  session_id: string;
  alert_name: string;
  alert_description?: string;
  user_email: string;
  frequency: AlertFrequency;
  alert_times: AlertTime[];
}

/** Workflow types */
export interface DocketInfo {
  category: string;
  state: string;
  district: string;
  docketNumber: string;
}

export interface AlertInfo {
  alert_name: string;
  alert_description?: string;
  user_email: string;
  frequency: AlertFrequency;
  alert_times: AlertTime[];
}

/** Generic response */
export interface APIResponse {
  status: 'success' | 'error';
  message: string;
}
```

---

### Appendix B: Error Codes Reference

| HTTP Code | Meaning | Common Causes | Solution |
|-----------|---------|---------------|----------|
| **200** | Success | Request completed successfully | Continue workflow |
| **404** | Not Found | Session ID doesn't exist | Start new session with `/automation/start` |
| **422** | Validation Error | Invalid request body (wrong type, missing field, invalid email) | Check request format against docs |
| **500** | Server Error | Backend automation failed (browser error, element not found, timeout) | Check logs, retry, report bug if persistent |

---

### Appendix C: Environment Variables

**Frontend:**
```bash
# React
REACT_APP_API_URL=http://localhost:8000

# Vue
VITE_API_URL=http://localhost:8000

# Angular
API_URL=http://localhost:8000
```

**Backend:**
```bash
# Worker count: development=1, production=4
ENVIRONMENT=development

# Python
PYTHONUNBUFFERED=1
```

---

### Appendix D: Postman Collection

```json
{
  "info": {
    "name": "Docket Alert API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/health",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["health"]
        }
      }
    },
    {
      "name": "Get Docket Categories",
      "request": {
        "method": "GET",
        "header": [],
        "url": {
          "raw": "http://localhost:8000/api/v1/docket-categories",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "v1", "docket-categories"]
        }
      }
    },
    {
      "name": "Start Automation",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\"include_docket\": false}"
        },
        "url": {
          "raw": "http://localhost:8000/api/v1/automation/start",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "v1", "automation", "start"]
        }
      }
    },
    {
      "name": "Select Docket",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\"session_id\": \"{{session_id}}\", \"category\": \"Dockets by State\", \"specific_docket\": \"California\"}"
        },
        "url": {
          "raw": "http://localhost:8000/api/v1/docket/select",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "v1", "docket", "select"]
        }
      }
    },
    {
      "name": "Cleanup Session",
      "request": {
        "method": "POST",
        "header": [{"key": "Content-Type", "value": "application/json"}],
        "body": {
          "mode": "raw",
          "raw": "{\"session_id\": \"{{session_id}}\"}"
        },
        "url": {
          "raw": "http://localhost:8000/api/v1/session/cleanup",
          "protocol": "http",
          "host": ["localhost"],
          "port": "8000",
          "path": ["api", "v1", "session", "cleanup"]
        }
      }
    }
  ]
}
```

---

### Appendix E: Useful Links

- **FastAPI Documentation**: https://fastapi.tiangolo.com
- **Selenium Documentation**: https://selenium-python.readthedocs.io
- **Requests Library**: https://requests.readthedocs.io
- **Fetch API**: https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API

---

## 12. Quick Reference Cheat Sheet

### Complete Workflow (Copy-Paste Ready)

```javascript
const API_URL = 'http://localhost:8000';

// 1. Start automation (15-20s)
const startResp = await fetch(`${API_URL}/api/v1/automation/start`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({include_docket: false})
});
const {session_id} = await startResp.json();

// 2. Select docket (2-3s)
await fetch(`${API_URL}/api/v1/docket/select`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    session_id,
    category: 'Dockets by State',
    specific_docket: 'California'
  })
});

// 3. Select district (2-3s)
await fetch(`${API_URL}/api/v1/district/select`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    session_id,
    state: 'California',
    district: 'Central District'
  })
});

// 4. Search docket number (3-5s)
await fetch(`${API_URL}/api/v1/docket/search`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    session_id,
    docket_number: '3:26-CV-00397'
  })
});

// 5. Create alert (2s)
await fetch(`${API_URL}/api/v1/alert/create`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({session_id})
});

// 6. Complete alert setup (3-5s)
await fetch(`${API_URL}/api/v1/alert/complete-setup`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    session_id,
    alert_name: 'Important Case Alert',
    alert_description: 'Track updates',
    user_email: 'user@example.com',
    frequency: 'daily',
    alert_times: ['5am', '3pm']
  })
});

// 7. Cleanup (always!)
await fetch(`${API_URL}/api/v1/session/cleanup`, {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({session_id})
});
```

### Key Points to Remember

✅ **Always start with** `/automation/start` to get `session_id`
✅ **Operations are sequential** - follow the order above
✅ **Always cleanup** when done or on error (use try/finally)
✅ **Operations take time** - total workflow ~30-40 seconds
✅ **Cache static data** - docket categories never change
✅ **Use appropriate timeouts** - 30s for browser startup, 10s for other ops
✅ **Validate input** - docket number format, email format, alert times
✅ **Handle errors gracefully** - network errors, session expiration, timeouts

---

## Support

For issues, questions, or feature requests:
- **GitHub Issues**: (TBD)
- **Email**: (TBD)
- **Documentation**: This file

---

**End of API Integration Guide**
