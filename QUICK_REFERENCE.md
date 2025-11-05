# JARVIS 3.0 - Quick Reference Guide

## 🎯 System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT REQUEST                           │
│              (Mobile App / Web Dashboard / Voice)                │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                      simple_main.py (FastAPI)                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Endpoints:                                                │  │
│  │ • POST /api/events/parse    (natural language)           │  │
│  │ • POST /api/events/voice    (audio → text → parse)       │  │
│  │ • POST /api/events/quick    (quick-tap, no LLM)          │  │
│  │ • GET  /api/events          (list with filters)          │  │
│  │ • GET  /api/events/today    (dashboard status)           │  │
│  │ • POST /api/insights/generate (pattern detection)        │  │
│  │ • POST /api/forecast         (capacity predictions)      │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────┬──────────────────────────────────┬───────────────┘
               │                                  │
               ▼                                  ▼
    ┌──────────────────┐              ┌──────────────────┐
    │  simple_auth.py  │              │     agents/      │
    │  (JWT Auth)      │              │  data_collector  │
    │                  │              │  (Agent 1)       │
    │ • Register user  │              │                  │
    │ • Login          │              │ GPT-4o-mini      │
    │ • Verify token   │              │ Parse NL → JSON  │
    └──────────────────┘              └──────────────────┘
               │                                  │
               ▼                                  │
    ┌──────────────────┐                        │
    │   simple_db.py   │                        │
    │  (Users Table)   │                        │
    │                  │                        │
    │ jarvis_dev.db    │                        │
    └──────────────────┘                        │
                                                 ▼
                              ┌──────────────────────────────┐
                              │   simple_jarvis_db.py        │
                              │   (Events Database)          │
                              │                              │
                              │ jarvis_events.db             │
                              │ • events table               │
                              │ • patterns table (Day 3)     │
                              │ • interventions table (Day 4)│
                              └──────────────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    ▼                    ▼                    ▼
        ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
        │ pattern_detector │  │   forecaster     │  │ interventionist  │
        │   (Agent 2)      │  │   (Agent 3)      │  │   (Agent 4)      │
        │                  │  │                  │  │                  │
        │ Correlations     │  │ ARIMA/Prophet    │  │ Warnings         │
        │ Trends           │  │ Burnout Risk     │  │ Suggestions      │
        │ Anomalies        │  │ 7-day Forecast   │  │ Insights         │
        │                  │  │                  │  │                  │
        │ [✅ DAY 3]       │  │ [✅ DAY 4]       │  │ [DAY 4]          │
        └──────────────────┘  └──────────────────┘  └──────────────────┘
```

---

## 📁 File Purpose Summary

| File | Purpose | Status | Lines |
|------|---------|--------|-------|
| `simple_main.py` | Main API server, all endpoints | ✅ OPERATIONAL | 542 |
| `simple_auth.py` | JWT authentication | ✅ OPERATIONAL | 206 |
| `simple_db.py` | Users database (SQLite) | ✅ OPERATIONAL | 157 |
| `simple_jarvis_db.py` | Events database (SQLite) | ✅ OPERATIONAL | 351 |
| `agents/base_agent.py` | Shared agent utilities | ✅ OPERATIONAL | 70 |
| `agents/data_collector.py` | Agent 1: NL parser | ✅ OPERATIONAL | 182 |
| `agents/pattern_detector.py` | Agent 2: Correlations | ✅ DAY 3 COMPLETE | 285 |
| `agents/forecaster.py` | Agent 3: ARIMA/Prophet forecasts | ✅ DAY 4 COMPLETE | 340 |
| `agents/interventionist.py` | Agent 4: Recommendations | 🔨 DAY 4 | 18 |
| `app/models/event.py` | Event Pydantic schemas | ✅ OPERATIONAL | 70 |
| `app/models/pattern.py` | Pattern Pydantic schemas | ✅ OPERATIONAL | 52 |
| `app/models/intervention.py` | Intervention schemas | ✅ OPERATIONAL | 95 |

**Total:** 14 files, 1779 lines of code

---

## 🔄 Request Flow Examples

### Example 1: Parse Natural Language

```
1. USER INPUT: "ran 5k this morning felt amazing"
   
2. POST /api/events/parse
   Headers: Authorization: Bearer <JWT>
   Body: {"text": "ran 5k this morning felt amazing"}
   
3. simple_main.py validates JWT (simple_auth.py)
   
4. DataCollectorAgent.parse(text)
   
5. GPT-4o-mini API call (cost: $0.00002)
   System Prompt: "Parse this into structured event..."
   
6. LLM Response:
   {
     "category": "physical",
     "event_type": "workout",
     "feeling": "amazing",
     "data": {
       "workout_type": "cardio",
       "duration": 30,
       "intensity": "moderate"
     }
   }
   
7. Validate with WorkoutData Pydantic schema
   
8. jarvis_db.create_event(user_id, parsed_data)
   
9. INSERT INTO events (...) → SQLite
   
10. Return EventResponse to client:
    {
      "id": 123,
      "category": "physical",
      "event_type": "workout",
      "timestamp": "2025-10-27T10:30:00",
      ...
    }
```

### Example 2: Voice Input

```
1. USER: Records audio "upper body heavy felt great"
   
2. POST /api/events/voice
   Headers: Authorization: Bearer <JWT>
   Body: multipart/form-data with audio file
   
3. simple_main.py validates JWT
   
4. Whisper API transcription (cost: $0.006/min)
   Audio → "upper body heavy felt great"
   
5. DataCollectorAgent.parse(transcribed_text)
   
6. [Same flow as Example 1 from step 5]
```

### Example 3: Quick-Tap (No LLM)

```
1. USER: Taps "Workout" button in mobile app
   
2. POST /api/events/quick
   Headers: Authorization: Bearer <JWT>
   Body: {
     "category": "physical",
     "event_type": "workout"
   }
   
3. simple_main.py validates JWT
   
4. SKIP DataCollectorAgent (instant response)
   
5. jarvis_db.create_event(user_id, data)
   
6. INSERT INTO events → SQLite
   
7. Return EventResponse (< 50ms total)
```

---

## 🧠 Agent System (4-Agent Workflow)

### Agent Roles

```
┌─────────────────────────────────────────────────────────────┐
│                     USER ACTIVITY                           │
└─────────────────────────────────┬───────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │  AGENT 1: DataCollector  │ ✅ DAY 2
                    │  Natural Language → JSON  │
                    └──────────────────────────┘
                                  │
                                  ▼
                         ┌────────────────┐
                         │  DATABASE      │
                         │  Store Events  │
                         └────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ AGENT 2:        │    │ AGENT 3:        │    │ AGENT 4:        │
│ PatternDetector │───▶│ Forecaster      │───▶│ Interventionist │
│                 │    │                 │    │                 │
│ Find patterns   │    │ Predict future  │    │ Generate        │
│ Correlations    │    │ Burnout risk    │    │ recommendations │
│ Trends          │    │ Capacity        │    │ Warnings        │
│                 │    │                 │    │ Suggestions     │
│ 🔨 DAY 3        │    │ 🔨 DAY 4        │    │ 🔨 DAY 4        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                         │                         │
        └─────────────────────────┴─────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────┐
                    │  INTERVENTIONS           │
                    │  Delivered to User       │
                    └──────────────────────────┘
```

### Scheduling (Day 6)

- **Real-time:** DataCollectorAgent on every event
- **Every 24 hours:** PatternDetectorAgent (nightly analysis)
- **Every 24 hours:** ForecasterAgent (daily forecast)
- **Every 6 hours:** InterventionistAgent (check state)
- **Manual:** All agents via API endpoints

---

## 📊 Database Schema

### jarvis_dev.db (Users)

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,  -- SHA256 hashed
    created_at TEXT  -- ISO timestamp
);
```

### jarvis_events.db (Events, Patterns, Interventions)

```sql
-- Events table
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category TEXT NOT NULL,  -- physical/mental/spiritual
    event_type TEXT NOT NULL,  -- workout/task/meditation/etc
    feeling TEXT,  -- User's mood
    data TEXT,  -- JSON blob {workout_type, intensity, duration, etc}
    timestamp TEXT  -- ISO timestamp
);

-- Patterns table (Day 3)
CREATE TABLE patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    pattern_type TEXT NOT NULL,  -- correlation/trend/anomaly
    description TEXT NOT NULL,  -- "Workout → 85% more tasks"
    confidence REAL NOT NULL,  -- 0.0 to 1.0
    frequency INTEGER DEFAULT 1,  -- How many times observed
    data TEXT,  -- JSON with correlation coefficients, etc
    first_detected TEXT,
    last_seen TEXT,
    is_active INTEGER DEFAULT 1
);

-- Interventions table (Day 4)
CREATE TABLE interventions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    intervention_type TEXT NOT NULL,  -- warning/suggestion/insight/forecast
    urgency TEXT NOT NULL,  -- low/medium/high/critical
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT DEFAULT 'pending',  -- pending/delivered/acknowledged
    created_at TEXT,
    delivered_at TEXT,
    acknowledged_at TEXT,
    user_rating INTEGER,  -- 1-5 stars
    was_helpful INTEGER,  -- 0 or 1
    data TEXT  -- JSON with supporting data
);
```

---

## 🔑 Key Concepts

### 1. Three Dimensions
- **PHYSICAL:** Workouts, sleep, meals, energy
- **MENTAL:** Tasks, work sessions, focus, overwhelm
- **SPIRITUAL:** Meditation, prayer, reflection, gratitude

### 2. LLM Cost Optimization
- **GPT-4o-mini:** $0.15 per 1M tokens (200x cheaper than GPT-4)
- **Typical parse:** 150 input + 50 output = 200 tokens = $0.00002
- **Monthly cost (100 parses/day):** ~$0.60/month

### 3. Authentication Flow
- Register → Hash password (SHA256) → Store user → Generate JWT
- Login → Verify credentials → Generate JWT (24h expiry)
- Protected endpoint → Extract Bearer token → Verify JWT → Get user_id

### 4. Pydantic Validation
- Request → Deserialize JSON → Validate types → Pass to handler
- Invalid data → 422 Unprocessable Entity with error details
- Response → Serialize Pydantic model → Return JSON

---

## 🚀 Quick Start Commands

```powershell
# Navigate to project
cd C:\Users\swapn\OneDrive\Documents\Jarvis\Jarvis_Backend\JARVIS3.0_BACKEND\Jarvis3.0

# Start server
python simple_main.py

# Server running on: http://localhost:8000
# API docs: http://localhost:8000/docs

# Test endpoints
# 1. Register user
curl -X POST http://localhost:8000/api/v1/auth/register `
  -H "Content-Type: application/json" `
  -d '{"username":"test","password":"test123"}'

# 2. Parse natural language
curl -X POST http://localhost:8000/api/events/parse `
  -H "Authorization: Bearer <TOKEN>" `
  -H "Content-Type: application/json" `
  -d '{"text":"ran 5k this morning felt amazing"}'

# 3. Get today's events
curl http://localhost:8000/api/events/today `
  -H "Authorization: Bearer <TOKEN>"
```

---

## 📖 Documentation Index

Each file has comprehensive header documentation explaining:

1. **simple_main.py** - Main API server (CLIENT → ENDPOINTS → DATABASE → RESPONSE)
2. **simple_auth.py** - Authentication (REGISTER → LOGIN → JWT VERIFICATION)
3. **simple_db.py** - Users database (CREATE → FETCH → VERIFY)
4. **simple_jarvis_db.py** - Events database (INSERT → QUERY → UPDATE)
5. **agents/base_agent.py** - Agent utilities (INIT → LLM CLIENT → ERROR HANDLING)
6. **agents/data_collector.py** - Parser (TEXT → LLM → JSON → VALIDATE)
7. **agents/pattern_detector.py** - Correlations (EVENTS → ANALYZE → PATTERNS) ✅ DAY 3
8. **agents/forecaster.py** - Predictions (HISTORY → ARIMA/PROPHET → FORECAST) ✅ DAY 4
9. **agents/interventionist.py** - Recommendations (STATE → RULES → INTERVENTIONS)
10. **app/models/event.py** - Event schemas (REQUEST → VALIDATE → RESPONSE)
11. **app/models/pattern.py** - Pattern schemas
12. **app/models/intervention.py** - Intervention schemas

**Read the full summary:** `DOCUMENTATION_SUMMARY.md`

---

## 🔮 Day 4: ForecasterAgent Implementation

### Features
- **Capacity Prediction:** 7-day energy and capacity forecasts
- **Advanced Algorithms:** ARIMA and Prophet models with fallback to exponential smoothing
- **Burnout Risk Scoring:** Heuristic 0-100 score based on recent energy, consecutive work days, sleep debt
- **Async Pattern Integration:** Fully async flow using pattern detector insights
- **Pattern Deduplication:** Prevents duplicate patterns via smart merging in database

### API Endpoint: POST /api/forecast

**Request:**
```json
{
  "days": 7  // optional, defaults to 7
}
```

**Response:**
```json
{
  "forecast": {
    "energy_forecast": [72, 74, 76, 73, 71, 69, 70],
    "capacity_forecast": [75, 78, 80, 77, 74, 72, 73],
    "next_7_days": ["2024-01-15", "2024-01-16", ...]
  },
  "burnout_risk": 35,
  "patterns_count": 12
}
```

### Forecasting Algorithms

**1. ARIMA (AutoRegressive Integrated Moving Average)**
- Used when: `HAS_ARIMA=True` and `len(series) >= 10`
- Model: ARIMA(1,1,1) order
- Fallback: Exponential smoothing if unavailable

**2. Prophet (Facebook Time Series)**
- Used when: `HAS_PROPHET=True` with date series
- Features: Automatic seasonality detection
- Fallback: Exponential smoothing if unavailable

**3. Exponential Smoothing (baseline)**
- Always available (no dependencies)
- Alpha: 0.3 (default smoothing factor)
- Simple weighted average of past values

### Installation for Advanced Forecasting
```bash
# Optional dependencies for better forecasts
pip install pandas numpy statsmodels prophet
```

### Usage Example
```python
# In your client app
response = await fetch('/api/forecast', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${jwt_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ days: 7 })
});

const { forecast, burnout_risk } = await response.json();

// Display burnout warning if high risk
if (burnout_risk > 70) {
  showWarning("High burnout risk - consider scheduling rest");
}
```

---

**Generated:** October 27, 2025  
**Status:** Core system + PatternDetector + ForecasterAgent operational  
**Next:** Day 4 - Implement InterventionistAgent
