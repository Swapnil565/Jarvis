# 📡 JARVIS 3.0 - API ENDPOINTS DOCUMENTATION

## ✅ EXISTING ENDPOINTS (Already in simple_main.py)

### **Authentication** (`/api/v1/auth/`)
```
POST /api/v1/auth/register
  Request:  {"email": "user@example.com", "password": "strongpass"}
  Response: {"message": "User registered", "user_id": 1}

POST /api/v1/auth/login
  Request:  {"email": "user@example.com", "password": "strongpass"}
  Response: {"access_token": "eyJ...", "token_type": "bearer"}
```

---

### **Event Logging** (`/api/events/`)

#### **1. Manual Event (Structured Data)**
```http
POST /api/events
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "category": "physical",
  "event_type": "workout",
  "feeling": "great",
  "data": {
    "workout_type": "upper_body",
    "intensity": "heavy",
    "duration": 60
  }
}

Response 201:
{
  "message": "Event logged successfully",
  "event": {
    "id": 123,
    "user_id": 1,
    "category": "physical",
    "event_type": "workout",
    "feeling": "great",
    "data": {...},
    "timestamp": "2025-11-12T10:30:00"
  }
}
```

#### **2. Natural Language Parsing**
```http
POST /api/events/parse
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "text": "upper body heavy felt great"
}

Response 201:
{
  "message": "Event parsed and logged successfully",
  "event": {...},
  "parsed_from": "upper body heavy felt great",
  "analysis_task_id": "abc123"  // Celery task ID
}
```

#### **3. Voice Input**
```http
POST /api/events/voice
Authorization: Bearer <jwt_token>
Content-Type: multipart/form-data

audio: <audio file>

Response 201:
{
  "message": "Voice input processed successfully",
  "transcription": "I did upper body heavy today",
  "event": {...}
}
```

#### **4. Quick Tap (Instant, No AI)**
```http
POST /api/events/quick
Authorization: Bearer <jwt_token>

{
  "category": "physical",
  "event_type": "workout",
  "feeling": "good",
  "data": {}
}

Response 201:
{
  "message": "Event logged instantly",
  "event": {...},
  "processing_method": "quick_tap"
}
```

#### **5. Get Events (with filters)**
```http
GET /api/events?category=physical&limit=10
Authorization: Bearer <jwt_token>

Response 200:
{
  "events": [...],
  "count": 10
}
```

#### **6. Get Today's Status**
```http
GET /api/events/today
Authorization: Bearer <jwt_token>

Response 200:
{
  "physical": {"logged": true, "event_type": "workout", ...},
  "mental": {"completed": 2, "total": 5},
  "spiritual": null,
  "mood": "great",
  "total_events": 7
}
```

#### **7. Delete Event**
```http
DELETE /api/events/123
Authorization: Bearer <jwt_token>

Response 200:
{
  "message": "Event deleted successfully"
}
```

---

### **Insights & Patterns** (`/api/insights/`)

```http
POST /api/insights/generate?days=90
Authorization: Bearer <jwt_token>

Response 200:
{
  "message": "Insights generated",
  "patterns": [
    {
      "id": 1,
      "input_dimension": "physical",
      "input_metric": "workout_completed",
      "output_dimension": "mental",
      "output_metric": "energy_level",
      "correlation": 0.75,
      "insight_text": "Workout increases energy by 40%",
      "confidence": "high"
    }
  ],
  "count": 6
}
```

---

### **Forecast** (`/api/forecast`)

```http
POST /api/forecast?days=7
Authorization: Bearer <jwt_token>

Response 200:
{
  "message": "Forecast generated",
  "forecast": {
    "energy_debt": 9.21,
    "forecast": [
      {
        "date": "2025-11-13",
        "capacity": "medium",
        "demand": "high",
        "category": 4,
        "details": {...}
      }
      // ... 7 days
    ],
    "crash_risk": {
      "risk_level": "low",
      "probability": 30,
      "predicted_date": "2025-11-13",
      "days_until_crash": 1
    },
    "recommendations": [...]
  }
}
```

---

### **Interventions** (`/api/interventions/`)

#### **1. Check for Interventions**
```http
POST /api/interventions/check
Authorization: Bearer <jwt_token>

Response 200:
{
  "interventions": [
    {
      "id": 1,
      "type": "warning",
      "priority": "high",
      "message": "Burnout risk detected",
      "action": "Take rest day",
      "created_at": "2025-11-12T10:00:00"
    }
  ],
  "count": 1,
  "message": "1 intervention(s) detected"
}
```

#### **2. Get Pending Interventions**
```http
GET /api/interventions
Authorization: Bearer <jwt_token>

Response 200:
{
  "interventions": [...],
  "count": 3
}
```

#### **3. Acknowledge Intervention**
```http
POST /api/interventions/123/acknowledge
Authorization: Bearer <jwt_token>

Response 200:
{
  "message": "Intervention acknowledged",
  "intervention_id": 123
}
```

#### **4. Rate Intervention**
```http
POST /api/interventions/123/rate
Authorization: Bearer <jwt_token>

{
  "rating": 5,
  "was_helpful": true
}

Response 200:
{
  "message": "Feedback recorded",
  "intervention_id": 123,
  "rating": 5
}
```

---

### **Celery Tasks** (`/api/tasks/`)

#### **1. Get Task Status**
```http
GET /api/tasks/abc123

Response 200:
{
  "task_id": "abc123",
  "status": "SUCCESS",
  "ready": true,
  "successful": true,
  "result": {...}
}
```

#### **2. Trigger Daily Workflow**
```http
POST /api/tasks/trigger/daily-workflow
Authorization: Bearer <jwt_token>

Response 200:
{
  "message": "Daily workflow queued successfully",
  "task_id": "def456",
  "user_id": 1
}
```

#### **3. Trigger Pattern Detection**
```http
POST /api/tasks/trigger/detect-patterns
Authorization: Bearer <jwt_token>

Response 200:
{
  "message": "Pattern detection queued for all users",
  "task_id": "ghi789"
}
```

#### **4. Trigger Forecast Generation**
```http
POST /api/tasks/trigger/generate-forecasts
Authorization: Bearer <jwt_token>

Response 200:
{
  "message": "Forecast generation queued for all users",
  "task_id": "jkl012"
}
```

#### **5. Celery Health Check**
```http
GET /api/tasks/health

Response 200:
{
  "status": "healthy",
  "workers_online": 4,
  "broker": "redis://localhost:6379/0",
  "scheduled_tasks": 5,
  "message": "Celery workers running"
}
```

---

### **Statistics & Health**

#### **1. User Stats**
```http
GET /api/stats
Authorization: Bearer <jwt_token>

Response 200:
{
  "total_events": 274,
  "events_by_category": {
    "physical": 120,
    "mental": 100,
    "spiritual": 54
  },
  "streak_days": 15,
  "last_event": "2025-11-12T10:30:00"
}
```

#### **2. System Health**
```http
GET /health

Response 200:
{
  "status": "healthy",
  "message": "JARVIS Backend is operational",
  "version": "3.0.0",
  "services": {
    "database": {"status": "healthy", "type": "SQLite"},
    "authentication": {"status": "healthy", "type": "JWT"},
    "event_tracking": {"status": "healthy", "total_events": 274},
    "api": {"status": "healthy", "endpoints": 8}
  }
}
```

---

## 🔄 WORKFLOW ENDPOINTS (Old - References Deleted Orchestrator)

⚠️ **These endpoints reference the deleted orchestrator and need to be updated or removed:**

```http
POST /api/workflow/daily
GET /api/workflow/status
```

**Status:** ❌ **BROKEN** (orchestrator deleted)  
**Fix:** Either remove or update to use Celery tasks instead

---

## 📱 WHAT YOUR FRONTEND NEEDS

Based on the existing endpoints, your frontend should be able to:

### **User Flow:**

1. **Authentication:**
   - `POST /api/v1/auth/register` - Sign up
   - `POST /api/v1/auth/login` - Get JWT token
   - Store JWT in localStorage/secure storage

2. **Log Events (3 methods):**
   - **Quick Tap:** `POST /api/events/quick` (instant, no AI)
   - **Text Input:** `POST /api/events/parse` (AI parsing)
   - **Voice:** `POST /api/events/voice` (audio → AI)

3. **View Dashboard:**
   - `GET /api/events/today` - Today's summary
   - `GET /api/stats` - User statistics

4. **View Insights:**
   - `POST /api/insights/generate` - Get patterns
   - `POST /api/forecast` - Get 7-day prediction
   - `GET /api/interventions` - Get recommendations

5. **Event Management:**
   - `GET /api/events` - List all events (with filters)
   - `DELETE /api/events/:id` - Delete event

---

## 🛠️ WHAT NEEDS TO BE FIXED

### **1. Update Orchestrator Endpoints** (30 min)

Current broken endpoints:
```python
@app.post("/api/workflow/daily")
async def run_daily_workflow_endpoint(...)
    from agents.orchestrator import orchestrator  # ❌ DELETED!
```

**Fix Option A: Remove** (easiest)
Just delete these endpoints since Celery handles it now:
- `POST /api/workflow/daily` → Already have `POST /api/tasks/trigger/daily-workflow`
- `GET /api/workflow/status` → Already have `GET /api/tasks/{task_id}`

**Fix Option B: Update** to use Celery tasks
Replace orchestrator calls with Celery task calls

---

### **2. Update Agent Imports** (5 min)

Some endpoints still reference async agents that might not exist:
```python
from agents.pattern_detector import pattern_detector  # Might be old
from agents.forecaster import forecaster  # Might be old
```

**Fix:** Update to use new synchronous agents:
```python
from agents.insight_generator import InsightGenerator
from agents.forecaster import ForecasterAgent
from agents.interventionist import InterventionistAgent
```

---

### **3. Add Missing Endpoint** (optional, 10 min)

Frontend might want a simple "Get Insights" endpoint:
```python
@app.get("/api/insights")
async def get_insights(current_user: dict = Depends(get_current_user)):
    """Get stored insights/patterns for user"""
    db = SimpleJarvisDB()
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM patterns 
            WHERE user_id = ? 
            ORDER BY last_seen DESC
        """, (current_user["id"],))
        patterns = cursor.fetchall()
    return {"insights": patterns, "count": len(patterns)}
```

---

## 📋 SUMMARY

### **✅ What Works:**
- ✅ Authentication (register, login)
- ✅ Event logging (4 methods)
- ✅ Event retrieval/deletion
- ✅ Celery task management
- ✅ Health checks
- ✅ Stats

### **⚠️ What Needs Updates:**
- ⚠️ Orchestrator endpoints (broken - references deleted agent)
- ⚠️ Agent imports (might be old async versions)
- ⚠️ GET /api/insights (doesn't exist, just POST)

### **📱 What Frontend Needs:**
Your frontend just needs to:
1. Get JWT token from login
2. Send events via `/api/events/parse` (text) or `/api/events/quick` (quick-tap)
3. Get insights via `/api/insights/generate`
4. Get forecast via `/api/forecast`
5. Display interventions from `/api/interventions`

---

## 🎯 NEXT STEPS

**Pick one:**

**A)** Fix broken orchestrator endpoints (30 min) - I can do this now  
**B)** Test existing API with current frontend  
**C)** Deploy as-is and fix later  
**D)** Show me what frontend requests look like

**The good news:** Most endpoints are already built! Just need small fixes. 🚀
