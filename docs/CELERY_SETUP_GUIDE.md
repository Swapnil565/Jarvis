# 🚀 CELERY SETUP GUIDE FOR JARVIS 3.0

## 📋 Overview

We've set up **production-ready Celery** for task scheduling and background processing. Celery replaces the orchestrator and handles all agent scheduling directly.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│              API ENDPOINTS                   │
│  POST /events → Store → Trigger analysis     │
└─────────────────────────────────────────────┘
                    ↓
        ┌──────────────────────┐
        │   CELERY BROKER       │
        │    (Redis)            │
        └──────────────────────┘
                    ↓
        ┌──────────────────────┐
        │   CELERY WORKERS      │
        │  (Process tasks)      │
        └──────────────────────┘
                    ↓
        ┌──────────────────────┐
        │    AGENT TASKS        │
        ├──────────────────────┤
        │ • InsightGenerator    │
        │ • Forecaster          │
        │ • Interventionist     │
        └──────────────────────┘
                    ↓
        ┌──────────────────────┐
        │      DATABASE         │
        │   (Store results)     │
        └──────────────────────┘
```

## 📁 Files Created

1. **celery_config.py** - Production configuration
   - Redis broker/backend
   - Task scheduling (Beat)
   - Error handling & retries
   - Rate limiting
   - Queue routing

2. **celery_app.py** - Celery app initialization
   - Creates Celery instance
   - Loads configuration
   - Auto-discovers tasks

3. **celery_tasks.py** - All agent tasks
   - `run_insight_generator()` - Daily insights
   - `run_forecaster()` - Daily predictions
   - `run_interventionist()` - Daily interventions
   - `health_check()` - System health
   - `cleanup_old_data()` - Weekly cleanup
   - `run_single_user_analysis()` - Event-triggered

4. **celery_monitoring.py** - Logging & monitoring
   - File logging (rotating)
   - Task metrics
   - Performance tracking

5. **Startup Scripts**:
   - `start_celery_worker.ps1` - Start worker (production)
   - `start_celery_beat.ps1` - Start scheduler (production)
   - `start_celery_all.ps1` - Start both (production)
   - `start_celery_worker_dev.ps1` - Worker (development)
   - `start_celery_beat_dev.ps1` - Beat (development)

## 🔧 Installation

### 1. Install Redis

**Windows:**
```powershell
# Download Redis for Windows from:
https://github.com/microsoftarchive/redis/releases

# Or use WSL with Redis:
wsl -d Ubuntu
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

**Linux/Mac:**
```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis

# Mac
brew install redis
brew services start redis
```

### 2. Install Python Packages

```powershell
pip install -r requirements_celery.txt
```

This installs:
- `celery[redis]` - Celery with Redis support
- `redis` - Redis Python client
- `flower` - Web monitoring tool
- `pytz` - Timezone support

### 3. Verify Redis is Running

```powershell
redis-cli ping
# Should return: PONG
```

## 🚀 Running Celery

### Development Mode (Frequent Tasks for Testing)

**Terminal 1 - Worker:**
```powershell
.\start_celery_worker_dev.ps1
```

**Terminal 2 - Beat:**
```powershell
.\start_celery_beat_dev.ps1
```

**Or start both:**
```powershell
.\start_celery_all.ps1
```

### Production Mode (Scheduled Daily Tasks)

**Terminal 1 - Worker:**
```powershell
.\start_celery_worker.ps1
```

**Terminal 2 - Beat:**
```powershell
.\start_celery_beat.ps1
```

## 📅 Task Schedule

### Production Schedule:

| Task | Schedule | Description |
|------|----------|-------------|
| **InsightGenerator** | Daily 2:00 AM | Find patterns in user events |
| **Forecaster** | Daily 2:10 AM | Generate 7-day forecasts |
| **Interventionist** | Daily 2:20 AM | Create interventions |
| **Health Check** | Every 5 minutes | Verify system health |
| **Database Cleanup** | Sunday 3:00 AM | Remove old data (90+ days) |

### Development Schedule:

| Task | Schedule | Description |
|------|----------|-------------|
| **InsightGenerator** | Every 5 minutes | Frequent testing |
| **Forecaster** | Every 6 minutes | Frequent testing |
| **Interventionist** | Every 7 minutes | Frequent testing |

## 🎯 Using Tasks from API

### From FastAPI Endpoints:

```python
from celery_tasks import (
    run_insight_generator,
    run_forecaster,
    run_interventionist,
    run_single_user_analysis
)

# Fire and forget (async)
@app.post("/api/analyze")
def trigger_analysis(user_id: int):
    # Queue task
    run_single_user_analysis.delay(user_id)
    return {"status": "queued"}

# Wait for result
@app.post("/api/analyze-sync")
def trigger_analysis_sync(user_id: int):
    # Run and wait
    result = run_single_user_analysis.apply_async(args=[user_id])
    result_data = result.get(timeout=30)  # Wait max 30 seconds
    return result_data

# Schedule for later
from datetime import datetime, timedelta
@app.post("/api/schedule-analysis")
def schedule_analysis(user_id: int, hours: int):
    eta = datetime.now() + timedelta(hours=hours)
    run_single_user_analysis.apply_async(
        args=[user_id],
        eta=eta
    )
    return {"status": "scheduled", "eta": eta}
```

## 📊 Monitoring

### 1. Flower Web UI (Recommended)

Start Flower:
```powershell
celery -A celery_app flower --port=5555
```

Open browser:
```
http://localhost:5555
```

Features:
- ✅ Real-time task monitoring
- ✅ Task history
- ✅ Worker stats
- ✅ Task routing visualization

### 2. Command Line Monitoring

**Check active tasks:**
```powershell
celery -A celery_app inspect active
```

**Check scheduled tasks:**
```powershell
celery -A celery_app inspect scheduled
```

**Check worker stats:**
```powershell
celery -A celery_app inspect stats
```

**View registered tasks:**
```powershell
celery -A celery_app inspect registered
```

### 3. Log Files

Logs are saved in `logs/` directory:

- `celery_all.log` - All logs (INFO+)
- `celery_errors.log` - Errors only
- `celery_tasks.log` - Task execution logs
- `agents.log` - Agent-specific logs

**View logs:**
```powershell
Get-Content logs\celery_all.log -Tail 50 -Wait
```

## 🔍 Testing Tasks

### Test Individual Task:

```powershell
# Start Python
python

# Import and run task
from celery_tasks import run_insight_generator
result = run_insight_generator.delay()
print(result.get())  # Wait for result
```

### Test All Tasks:

```powershell
python
from celery_tasks import run_all_agents
result = run_all_agents.delay()
print(result.get(timeout=60))
```

## 🐛 Troubleshooting

### Redis Connection Error

**Error:** `celery.exceptions.ImproperlyConfigured: Error: cannot connect to redis`

**Fix:**
```powershell
# Check if Redis is running
redis-cli ping

# Start Redis (WSL)
wsl -d Ubuntu
sudo service redis-server start
```

### Task Not Running

**Check:**
1. Is worker running? → Check worker terminal
2. Is beat running? → Check beat terminal
3. Is task registered? → `celery -A celery_app inspect registered`

### Import Errors

**Error:** `ModuleNotFoundError: No module named 'celery_app'`

**Fix:**
```powershell
# Make sure you're in the correct directory
cd C:\Users\swapn\OneDrive\Documents\Jarvis\Jarvis_Backend\JARVIS3.0_BACKEND\Jarvis3.0

# Verify files exist
ls celery_app.py
ls celery_tasks.py
```

## 🔐 Production Deployment

### 1. Environment Variables

Create `.env` file:
```env
JARVIS_ENV=production
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### 2. Systemd Service (Linux)

Create `/etc/systemd/system/celery-worker.service`:
```ini
[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=jarvis
Group=jarvis
WorkingDirectory=/path/to/jarvis
Environment="JARVIS_ENV=production"
ExecStart=/usr/local/bin/celery -A celery_app worker --loglevel=INFO --concurrency=4

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/celery-beat.service`:
```ini
[Unit]
Description=Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=jarvis
Group=jarvis
WorkingDirectory=/path/to/jarvis
Environment="JARVIS_ENV=production"
ExecStart=/usr/local/bin/celery -A celery_app beat --loglevel=INFO

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable celery-worker celery-beat
sudo systemctl start celery-worker celery-beat
```

### 3. Windows Service (Windows)

Use `nssm` (Non-Sucking Service Manager):
```powershell
# Download NSSM
# https://nssm.cc/download

# Install worker service
nssm install JarvisCeleryWorker "C:\path\to\python.exe" "C:\path\to\start_celery_worker.ps1"

# Install beat service
nssm install JarvisCeleryBeat "C:\path\to\python.exe" "C:\path\to\start_celery_beat.ps1"

# Start services
nssm start JarvisCeleryWorker
nssm start JarvisCeleryBeat
```

## ✅ Verification Checklist

- [ ] Redis installed and running
- [ ] Python packages installed (`pip install -r requirements_celery.txt`)
- [ ] Worker starts without errors
- [ ] Beat starts without errors
- [ ] Tasks are registered (`celery -A celery_app inspect registered`)
- [ ] Health check passes (check logs after 5 minutes)
- [ ] Flower monitoring works (optional)

## 📚 Next Steps

1. **Install Redis** (if not done)
2. **Run development mode** to test
3. **Verify tasks execute** properly
4. **Integrate with FastAPI** endpoints
5. **Set up production deployment**

## 🎉 Benefits Over Orchestrator

✅ **Simpler** - No extra orchestration layer  
✅ **Scalable** - Add more workers easily  
✅ **Reliable** - Built-in retries and error handling  
✅ **Monitorable** - Flower UI + detailed logs  
✅ **Flexible** - Easy to add/remove tasks  
✅ **Production-ready** - Battle-tested Celery framework

---

**Questions?** Check the official Celery docs: https://docs.celeryq.dev/
