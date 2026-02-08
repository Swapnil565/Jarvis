# 🚀 CELERY QUICK REFERENCE

## ⚡ Quick Start (3 Steps)

```powershell
# 1. Install Redis (one-time)
# Download: https://github.com/microsoftarchive/redis/releases

# 2. Install packages
pip install -r requirements_celery.txt

# 3. Start Celery
.\start_celery_all.ps1
```

## 📋 Common Commands

### Start Services
```powershell
# Development (frequent tasks for testing)
.\start_celery_worker_dev.ps1     # Terminal 1
.\start_celery_beat_dev.ps1       # Terminal 2

# Production (daily tasks at 2am)
.\start_celery_worker.ps1         # Terminal 1
.\start_celery_beat.ps1           # Terminal 2

# Both at once
.\start_celery_all.ps1
```

### Monitor Tasks
```powershell
# Web UI (best option)
celery -A celery_app flower --port=5555
# Open: http://localhost:5555

# Active tasks
celery -A celery_app inspect active

# Scheduled tasks
celery -A celery_app inspect scheduled

# Worker stats
celery -A celery_app inspect stats
```

### Check Logs
```powershell
# All logs (live)
Get-Content logs\celery_all.log -Tail 50 -Wait

# Errors only
Get-Content logs\celery_errors.log -Tail 50 -Wait

# Task logs
Get-Content logs\celery_tasks.log -Tail 50 -Wait
```

## 🎯 Task Names

```
celery_tasks.run_insight_generator    → Daily insights
celery_tasks.run_forecaster           → Daily forecasts
celery_tasks.run_interventionist      → Daily interventions
celery_tasks.health_check             → Every 5 min
celery_tasks.cleanup_old_data         → Weekly cleanup
celery_tasks.run_all_agents           → All agents at once
celery_tasks.run_single_user_analysis → Single user
```

## 🔧 From Python/API

### Fire and Forget (Async)
```python
from celery_tasks import run_single_user_analysis

# Queue task (doesn't block)
run_single_user_analysis.delay(user_id)
```

### Wait for Result
```python
# Run and wait (blocks)
result = run_single_user_analysis.apply_async(args=[user_id])
data = result.get(timeout=30)  # Wait max 30 sec
```

### Schedule for Later
```python
from datetime import datetime, timedelta

# Run in 1 hour
eta = datetime.now() + timedelta(hours=1)
run_single_user_analysis.apply_async(
    args=[user_id],
    eta=eta
)
```

## 📅 Default Schedule

| Time | Task | Description |
|------|------|-------------|
| 2:00 AM | InsightGenerator | Find patterns |
| 2:10 AM | Forecaster | 7-day predictions |
| 2:20 AM | Interventionist | Create recommendations |
| Every 5 min | Health Check | System health |
| Sun 3:00 AM | Cleanup | Remove old data (90+ days) |

## 🐛 Troubleshooting

### Redis not running
```powershell
# Check
redis-cli ping
# Should return: PONG

# Start (WSL)
wsl -d Ubuntu
sudo service redis-server start
```

### Import errors
```powershell
# Verify you're in correct directory
cd C:\Users\swapn\OneDrive\Documents\Jarvis\Jarvis_Backend\JARVIS3.0_BACKEND\Jarvis3.0

# Test imports
python -c "from celery_app import app; print('OK')"
```

### Tasks not running
```powershell
# 1. Check worker is running
# 2. Check beat is running
# 3. Check registered tasks
celery -A celery_app inspect registered
```

## 📁 Important Files

```
celery_app.py          → Celery initialization
celery_config.py       → Configuration
celery_tasks.py        → All tasks
celery_monitoring.py   → Logging setup
logs/                  → Log files
  ├─ celery_all.log    → All logs
  ├─ celery_errors.log → Errors only
  └─ celery_tasks.log  → Task logs
```

## 🔐 Environment Variables

```powershell
# Set environment
$env:JARVIS_ENV = "production"  # or "development"

# Custom Redis URL
$env:CELERY_BROKER_URL = "redis://localhost:6379/0"
$env:CELERY_RESULT_BACKEND = "redis://localhost:6379/1"
```

## 📊 Monitoring URLs

```
Flower UI:     http://localhost:5555
Redis:         redis://localhost:6379
```

## ✅ Health Check

```powershell
# Quick test
python -c "from celery_tasks import health_check; print(health_check())"

# Should return:
# {'status': 'healthy', 'database': 'connected', 'event_count': X}
```

## 🎉 Success Indicators

✅ Worker shows: `celery@worker ready`  
✅ Beat shows: `Scheduler: Sending due task`  
✅ Flower shows: Workers online  
✅ Logs show: Task execution  
✅ No errors in error log  

## 📚 Full Documentation

See `CELERY_SETUP_GUIDE.md` for complete guide!
