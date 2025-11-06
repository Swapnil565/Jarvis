"""
=============================================================================
JARVIS 3.0 - CELERY BEAT SCHEDULE CONFIGURATION [DAY 6]
=============================================================================

PURPOSE:
--------
Define periodic task schedules using Celery Beat (like cron jobs).
This tells Celery WHEN to run each task automatically.

RESPONSIBILITY:
---------------
- Schedule daily workflow at 2am UTC
- Schedule pattern detection every 6 hours
- Schedule forecast generation daily at 1am
- Schedule data cleanup monthly

WHAT IS CELERY BEAT?
--------------------
Celery Beat is a scheduler that triggers periodic tasks.
Think of it as a better cron that integrates with Celery.

CRON SYNTAX EXPLAINED:
----------------------
from celery.schedules import crontab

Examples:
- crontab(hour=2, minute=0)           → Every day at 2:00 AM
- crontab(hour='*/6')                 → Every 6 hours
- crontab(day_of_week=1, hour=9)      → Every Monday at 9:00 AM
- crontab(day_of_month=1, hour=0)     → First day of month at midnight
- crontab(minute='*/15')              → Every 15 minutes

Or use seconds:
- 60.0                                → Every 60 seconds
- 3600.0                              → Every hour

SCHEDULE STRUCTURE:
-------------------
beat_schedule = {
    'task-unique-name': {
        'task': 'jarvis.task_name',      # Task to run
        'schedule': crontab(...),         # When to run
        'args': (arg1, arg2),            # Arguments to pass
        'options': {'expires': 3600}      # Optional: task expires after 1 hour
    }
}

OUR JARVIS SCHEDULE:
--------------------
1. Daily Workflow (2am): Run comprehensive analysis for all users
2. Pattern Detection (6am, 12pm, 6pm, 12am): Find new patterns
3. Forecast Generation (1am): Generate daily forecasts
4. Data Cleanup (First of month, 3am): Remove old data

HOW TO USE:
-----------
1. Define schedule in this file
2. Import in jarvis_celery.py: app.conf.beat_schedule = BEAT_SCHEDULE
3. Start beat: celery -A jarvis_celery beat --loglevel=info

DATA FLOW:
----------
Celery Beat Scheduler
    ↓
Check schedule every second
    ↓
When time matches schedule
    ↓
Queue task in Redis
    ↓
Celery Worker picks up task
    ↓
Execute task function

STATUS: TO BE IMPLEMENTED
"""

# TODO: Import crontab for cron-style scheduling
# from celery.schedules import crontab

# YOUR CODE STARTS HERE:
# ----------------------

from celery.schedules import crontab

# Define the beat schedule dictionary
# This tells Celery Beat WHEN to run each task automatically
BEAT_SCHEDULE = {
    
    # Schedule 1: Daily Workflow (Every day at 2am UTC)
    # --------------------------------------------------
    # Runs comprehensive analysis for all active users
    # Provides morning insights and recommendations
    'daily-workflow-all-users': {
        'task': 'jarvis.daily_workflow',
        'schedule': crontab(hour=2, minute=0),  # 2:00 AM UTC daily
        'args': (),
        'options': {
            'expires': 3600  # Task expires after 1 hour if not picked up
        }
    },
    
    # Schedule 2: Pattern Detection (Every 6 hours)
    # ----------------------------------------------
    # Keeps patterns fresh throughout the day
    # Runs at: 12am, 6am, 12pm, 6pm UTC
    'detect-patterns-all-users': {
        'task': 'jarvis.detect_patterns_all_users',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
        'args': (),
    },
    
    # Schedule 3: Forecast Generation (Daily at 1am UTC)
    # ---------------------------------------------------
    # Runs before daily workflow to ensure forecasts are ready
    # Generates 7-day predictions for all users
    'generate-forecasts-all-users': {
        'task': 'jarvis.generate_forecasts_all_users',
        'schedule': crontab(hour=1, minute=0),  # 1:00 AM UTC daily
        'args': (),
    },
    
    # Schedule 4: Data Cleanup (Monthly on 1st at 3am)
    # -------------------------------------------------
    # Removes events/patterns older than 1 year
    # Keeps database size manageable
    'cleanup-old-data': {
        'task': 'jarvis.cleanup_old_data',
        'schedule': crontab(day_of_month=1, hour=3, minute=0),  # 1st of month at 3 AM
        'args': (365,),  # Remove data older than 365 days
    },
    
    # Schedule 5: Health Check (Every hour)
    # --------------------------------------
    # Verifies system is operational
    # Checks database connectivity and agent availability
    'health-check': {
        'task': 'jarvis.health_check',
        'schedule': 3600.0,  # Every 3600 seconds (1 hour)
        'args': (),
    },
    
    # Schedule 6: Quick Pattern Refresh (Every 15 minutes during peak hours)
    # -----------------------------------------------------------------------
    # Optional: More frequent pattern updates during active hours (6am-10pm)
    # Commented out by default - enable if needed
    # 'quick-pattern-refresh': {
    #     'task': 'jarvis.detect_patterns_all_users',
    #     'schedule': crontab(minute='*/15', hour='6-22'),  # Every 15 min, 6am-10pm
    #     'args': (),
    # },
}

# Export the schedule
__all__ = ['BEAT_SCHEDULE']

