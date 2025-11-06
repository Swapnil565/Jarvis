# 🚀 CELERY QUICK REFERENCE CARD

## 📦 Installation
```bash
pip install celery[redis] flower redis
```

## 🎯 Core Concepts

### 1. **Celery App** (jarvis_celery.py)
The brain - configures everything
```python
from celery import Celery
app = Celery('jarvis', broker='redis://localhost:6379/0')
```

### 2. **Task** (celery_tasks.py)
A function that runs in background
```python
@app.task
def my_task(x, y):
    return x + y
```

### 3. **Broker** (Redis)
The queue - stores pending tasks
```bash
redis-server  # Start Redis
```

### 4. **Worker**
Executes tasks from queue
```bash
celery -A jarvis_celery worker --loglevel=info --pool=solo
```

### 5. **Beat**
Scheduler - triggers periodic tasks
```bash
celery -A jarvis_celery beat --loglevel=info
```

### 6. **Flower**
Web dashboard - monitor tasks
```bash
celery -A jarvis_celery flower
# Visit: http://localhost:5555
```

---

## 📝 Task Syntax

### Basic Task
```python
@app.task
def add(x, y):
    return x + y

# Call it:
result = add.delay(4, 6)  # Non-blocking!
print(result.get())       # Wait for result: 10
```

### Task with Retry
```python
@app.task(bind=True, max_retries=3)
def risky_task(self, url):
    try:
        return requests.get(url).json()
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

### Named Task
```python
@app.task(name='jarvis.my_task')
def my_task():
    return "Hello"
```

---

## ⏰ Schedule Syntax

### Import
```python
from celery.schedules import crontab
```

### Common Schedules
```python
# Every day at 2am
'schedule': crontab(hour=2, minute=0)

# Every 6 hours
'schedule': crontab(hour='*/6')

# Every Monday at 9am
'schedule': crontab(day_of_week=1, hour=9)

# Every 15 minutes
'schedule': crontab(minute='*/15')

# Every 60 seconds
'schedule': 60.0
```

### Full Schedule Definition
```python
BEAT_SCHEDULE = {
    'my-task': {
        'task': 'jarvis.my_task',
        'schedule': crontab(hour=2, minute=0),
        'args': (1, 2)
    }
}
```

---

## 🎮 Calling Tasks

### Fire and Forget
```python
task = my_task.delay(arg1, arg2)
print(task.id)  # Task ID
```

### Wait for Result
```python
result = my_task.delay(4, 6)
print(result.get(timeout=10))  # Blocks until done
```

### Schedule for Later
```python
from datetime import datetime, timedelta
eta = datetime.now() + timedelta(hours=1)
task = my_task.apply_async(args=[1, 2], eta=eta)
```

### Check Status
```python
if task.ready():
    print(task.result)
else:
    print(task.state)  # PENDING, SUCCESS, FAILURE
```

---

## 🐳 Docker Commands

### Start Redis & Flower
```bash
docker-compose up -d
```

### Check Status
```bash
docker-compose ps
```

### View Logs
```bash
docker-compose logs -f redis
```

### Stop Services
```bash
docker-compose down
```

### Test Redis
```bash
docker exec -it jarvis-redis redis-cli ping
# Should return: PONG
```

---

## 🔧 Development Workflow

### Terminal 1: Redis
```bash
docker-compose up redis
```

### Terminal 2: Celery Worker
```bash
celery -A jarvis_celery worker --loglevel=info --pool=solo
```

### Terminal 3: Celery Beat (Optional)
```bash
celery -A jarvis_celery beat --loglevel=info
```

### Terminal 4: Flower (Optional)
```bash
celery -A jarvis_celery flower
```

### Terminal 5: FastAPI
```bash
python simple_main.py
```

---

## 🐛 Troubleshooting

### Redis not connecting?
```bash
redis-cli ping  # Should return PONG
```

### Task not found?
Check imports in jarvis_celery.py:
```python
from celery_tasks import *
```

### Worker not starting?
Use --pool=solo on Windows:
```bash
celery -A jarvis_celery worker --loglevel=info --pool=solo
```

### Circular import?
Import app at bottom of celery_tasks.py:
```python
from jarvis_celery import app  # At bottom
```

---

## 📊 Monitoring

### Check Worker Status
```bash
celery -A jarvis_celery inspect active
```

### List Scheduled Tasks
```bash
celery -A jarvis_celery inspect scheduled
```

### Check Registered Tasks
```bash
celery -A jarvis_celery inspect registered
```

### Flower Dashboard
Visit: http://localhost:5555
- See active workers
- Monitor task execution
- View task history
- Check resource usage

---

## 🎯 JARVIS Specific Tasks

### Analyze Event (Event-Triggered)
```python
from celery_tasks import analyze_event_task
analyze_event_task.delay(user_id=123, event_id='abc')
```

### Daily Workflow (Scheduled)
```python
from celery_tasks import daily_workflow_task
daily_workflow_task.delay(user_id=123)
```

### Pattern Detection (Manual)
```python
from celery_tasks import detect_patterns_all_users
detect_patterns_all_users.delay()
```

---

**Keep this card handy while coding! 📌**
