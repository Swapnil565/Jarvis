"""
=============================================================================
JARVIS 3.0 - CELERY APPLICATION CONFIGURATION [DAY 6]
=============================================================================

PURPOSE:
--------
Celery app initialization and configuration for background task processing.
This is the core Celery instance that workers will use to execute tasks.

RESPONSIBILITY:
---------------
- Initialize Celery app with Redis broker
- Configure task serialization and timezone
- Define periodic task schedules (Celery Beat)
- Import all task definitions

WHAT IS CELERY?
---------------
Celery is a distributed task queue system that lets you:
1. Run heavy computations in background (don't block API)
2. Schedule periodic tasks (like cron jobs)
3. Scale horizontally (run multiple workers)
4. Automatic retries on failure

ARCHITECTURE:
-------------
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  FastAPI     │────▶│    Redis     │────▶│   Celery     │
│  (Producer)  │     │   (Broker)   │     │   Worker     │
└──────────────┘     └──────────────┘     └──────────────┘
      │                     │                     │
      │                     │                     │
   Queue task         Store tasks           Execute tasks
   instantly          in memory             in background

CONFIGURATION EXPLAINED:
------------------------
broker: Where tasks are queued (Redis)
backend: Where results are stored (Redis)
task_serializer: How to convert Python objects to strings (JSON)
timezone: When to run scheduled tasks (UTC)

HOW TO RUN CELERY WORKER:
--------------------------
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Celery Worker
celery -A jarvis_celery worker --loglevel=info --pool=solo

# Terminal 3: Start Celery Beat (for scheduled tasks)
celery -A jarvis_celery beat --loglevel=info

# Terminal 4: Start Flower (monitoring dashboard)
celery -A jarvis_celery flower

DEPENDENCIES:
-------------
- celery[redis]: Task queue library with Redis support
- redis: Python Redis client
- celery_tasks.py: Task definitions (imported below)

STATUS: TO BE IMPLEMENTED
"""

# TODO: Import Celery and create app instance
# TODO: Configure broker (Redis connection string)
# TODO: Configure backend (Redis for result storage)
# TODO: Set task serialization to JSON
# TODO: Set timezone to UTC
# TODO: Import tasks from celery_tasks.py

# YOUR CODE STARTS HERE:
# ----------------------
from celery import Celery

# Create Celery app instance
app = Celery(
    'jarvis',
    broker='redis://localhost:6379/0',      # Redis database 0 for task queue
    backend='redis://localhost:6379/1'      # Redis database 1 for results
)

# Configure Celery settings
app.conf.update(
    task_serializer='json',           # Serialize tasks as JSON
    accept_content=['json'],          # Only accept JSON content
    result_serializer='json',         # Serialize results as JSON
    timezone='UTC',                   # Use UTC timezone
    enable_utc=True,                  # Enable UTC
    task_track_started=True,          # Track when tasks start
    task_time_limit=30 * 60,          # Task timeout: 30 minutes
)

# Import and configure Celery Beat schedule
from celery_beat_schedule import BEAT_SCHEDULE
app.conf.beat_schedule = BEAT_SCHEDULE

# Import tasks so Celery can discover them
# This must be at the bottom to avoid circular imports
from celery_tasks import *  # noqa