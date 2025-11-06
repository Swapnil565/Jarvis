# 🎓 DAY 6 LEARNING GUIDE - YOUR IMPLEMENTATION CHECKLIST

## 📝 What You Need to Write

### ✅ **FILE 1: jarvis_celery.py** (Celery App Configuration)

**Your tasks:**
1. Import Celery from celery
2. Create Celery app with name 'jarvis'
3. Set broker to 'redis://localhost:6379/0'
4. Set backend to 'redis://localhost:6379/1'
5. Configure timezone to 'UTC'
6. Import tasks from celery_tasks

**Hint - Basic Structure:**
```python
from celery import Celery

app = Celery('jarvis')
app.conf.broker_url = 'redis://localhost:6379/0'
# ... more config
```

**Expected Lines:** ~20 lines

---

### ✅ **FILE 2: celery_tasks.py** (Task Definitions)

**Your tasks:**
1. Import the celery app from jarvis_celery
2. Import orchestrator, interventionist from agents
3. Import jarvis_db from simple_jarvis_db
4. Create 5 tasks with @app.task decorator:

**Task 1: analyze_event_task(user_id, event_id)**
- Check for urgent interventions
- If found, log them
- Return count of interventions

**Task 2: daily_workflow_task(user_id)**
- Call orchestrator.run_daily_workflow(user_id)
- Return the result

**Task 3: detect_patterns_all_users()**
- Get all users from database
- For each user, detect patterns
- Return count processed

**Task 4: generate_forecasts_all_users()**
- Get all users
- For each user, generate forecast
- Handle errors gracefully

**Task 5: cleanup_old_data(days=365)**
- Delete events older than X days
- Return count deleted

**Hint - Task Structure:**
```python
@app.task(name='jarvis.task_name')
def my_task(arg1, arg2):
    try:
        # Your logic here
        result = do_something(arg1, arg2)
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None
```

**Expected Lines:** ~100 lines

---

### ✅ **FILE 3: celery_beat_schedule.py** (Periodic Schedules)

**Your tasks:**
1. Import crontab from celery.schedules
2. Create BEAT_SCHEDULE dictionary with 5 schedules:

**Schedule 1: Daily Workflow**
- Task: 'jarvis.daily_workflow_all_users'
- Time: Every day at 2:00 AM
- Use: crontab(hour=2, minute=0)

**Schedule 2: Pattern Detection**
- Task: 'jarvis.detect_patterns_all_users'
- Time: Every 6 hours
- Use: crontab(hour='*/6')

**Schedule 3: Forecast Generation**
- Task: 'jarvis.generate_forecasts_all_users'
- Time: Every day at 1:00 AM
- Use: crontab(hour=1, minute=0)

**Schedule 4: Data Cleanup**
- Task: 'jarvis.cleanup_old_data'
- Time: First day of month at 3 AM
- Use: crontab(day_of_month=1, hour=3)

**Schedule 5: Health Check (Optional)**
- Task: 'jarvis.health_check'
- Time: Every hour
- Use: 3600.0 (seconds)

**Hint - Schedule Structure:**
```python
from celery.schedules import crontab

BEAT_SCHEDULE = {
    'my-scheduled-task': {
        'task': 'jarvis.my_task',
        'schedule': crontab(hour=2, minute=0),
        'args': ()
    }
}
```

**Expected Lines:** ~50 lines

---

### ✅ **FILE 4: docker-compose.yml** (Redis & Flower)

**Your tasks:**
1. Define redis service:
   - Image: redis:alpine
   - Ports: 6379:6379
   - Restart: always

2. Define flower service:
   - Image: mher/flower
   - Ports: 5555:5555
   - Environment: CELERY_BROKER_URL
   - Depends_on: redis

**Hint - Service Structure:**
```yaml
version: '3.8'

services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    restart: always

  flower:
    image: mher/flower
    # ... more config
```

**Expected Lines:** ~30 lines

---

### ✅ **FILE 5: simple_main.py Updates**

**Your tasks:**
1. Add imports at top:
   ```python
   from celery_tasks import analyze_event_task, daily_workflow_task
   ```

2. Update POST /api/events/parse endpoint:
   - After creating event, add:
   ```python
   analyze_event_task.delay(current_user["id"], event_id)
   ```

3. Add new endpoint GET /api/tasks/{task_id}:
   - Check task status using AsyncResult
   - Return task state and result

4. Add new endpoint POST /api/tasks/trigger-daily:
   - Queue daily_workflow_task
   - Return task ID

**Expected Changes:** ~40 lines

---

## 🎯 Testing Checklist

### Step 1: Install Dependencies
```bash
pip install celery[redis] flower redis
```

### Step 2: Start Redis
```bash
# Option A: Docker
docker-compose up -d redis

# Option B: Windows (Chocolatey)
choco install redis-64
redis-server
```

### Step 3: Test Celery Worker
```bash
celery -A jarvis_celery worker --loglevel=info --pool=solo
```

### Step 4: Test Task from Python
```python
from celery_tasks import analyze_event_task
result = analyze_event_task.delay(123, 'abc')
print(f"Task ID: {result.id}")
```

### Step 5: Start Celery Beat
```bash
celery -A jarvis_celery beat --loglevel=info
```

### Step 6: Start Flower Dashboard
```bash
celery -A jarvis_celery flower
# Open: http://localhost:5555
```

---

## 🐛 Common Errors & Solutions

### Error: "No module named 'celery'"
**Solution:** `pip install celery[redis]`

### Error: "Can't connect to Redis"
**Solution:** Make sure Redis is running: `redis-cli ping` should return PONG

### Error: "Task not found"
**Solution:** Make sure you imported tasks in jarvis_celery.py: `from celery_tasks import *`

### Error: "Circular import"
**Solution:** Import celery app at bottom of file, not top

---

## 📚 Learning Resources

### Celery Basics:
- Official Docs: https://docs.celeryproject.org/
- Task Tutorial: https://docs.celeryproject.org/en/stable/getting-started/first-steps-with-celery.html
- Beat Schedule: https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html

### Cron Syntax:
- crontab(hour=2) → Every day at 2am
- crontab(hour='*/6') → Every 6 hours
- crontab(day_of_week=1) → Every Monday
- 60.0 → Every 60 seconds

---

## 🎉 Success Criteria

You'll know you succeeded when:
- ✅ Celery worker starts without errors
- ✅ Can queue a task and see it execute
- ✅ Celery Beat schedules tasks automatically
- ✅ Flower dashboard shows worker status
- ✅ API endpoints queue tasks instead of blocking

---

**Now go write that code, brother! Show me when you're done and I'll review it! 🚀**
