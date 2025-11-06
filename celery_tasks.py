"""
=============================================================================
JARVIS 3.0 - CELERY TASK DEFINITIONS [DAY 6]
=============================================================================

PURPOSE:
--------
Define all background tasks that Celery workers will execute.
These tasks run asynchronously, separate from the FastAPI server.

RESPONSIBILITY:
---------------
- Define event-triggered tasks (run after user logs event)
- Define scheduled tasks (daily workflow, pattern detection)
- Implement task retry logic for reliability
- Handle errors gracefully

TASK TYPES WE'LL CREATE:
-------------------------
1. analyze_event_task: Quick intervention check after event logged
2. daily_workflow_task: Comprehensive analysis (2am daily)
3. detect_patterns_all_users: Run pattern detection for all active users
4. generate_forecasts_all_users: Run forecasts for all users
5. cleanup_old_data: Remove old events/logs (monthly)

TASK DECORATOR EXPLAINED:
--------------------------
@app.task(
    bind=True,              # Pass task instance as first arg (for retries)
    max_retries=3,          # Retry up to 3 times on failure
    default_retry_delay=60  # Wait 60 seconds between retries
)
def my_task(self, user_id):
    try:
        # Your task logic here
        pass
    except Exception as exc:
        # Retry the task
        raise self.retry(exc=exc)

HOW TASKS ARE CALLED:
---------------------
# From FastAPI endpoint:
analyze_event_task.delay(user_id=123, event_id='abc')  # Fire and forget

# With result tracking:
result = daily_workflow_task.apply_async(args=[user_id])
print(result.get(timeout=10))  # Wait for result

# Schedule for later:
from datetime import datetime, timedelta
eta = datetime.now() + timedelta(hours=1)
task.apply_async(args=[user_id], eta=eta)

DATA FLOW:
----------
1. API receives event → Store in DB → Queue task
2. Celery worker picks up task → Execute agent workflows
3. Store results in DB → Send notifications if needed
4. Return (user already has instant response from step 1)

INTEGRATION POINTS:
-------------------
- Called by: simple_main.py API endpoints
- Uses: orchestrator, pattern_detector, forecaster, interventionist
- Stores results in: jarvis_db

STATUS: TO BE IMPLEMENTED
"""

# TODO: Import jarvis_celery app
# TODO: Import orchestrator and agents
# TODO: Import jarvis_db for data access
# TODO: Import logging for task monitoring

# YOUR CODE STARTS HERE:
# ----------------------

# Import Celery app (must be at top to avoid circular imports)
from jarvis_celery import app

# Import our agents and orchestrator
from agents.orchestrator import orchestrator
from agents.interventionist import interventionist
from agents.pattern_detector import pattern_detector
from agents.forecaster import forecaster

# Import database
from simple_jarvis_db import jarvis_db

# Import utilities
import logging
import asyncio
from datetime import datetime, timedelta

# Setup logging
logger = logging.getLogger(__name__)


# ==============================================================================
# TASK 1: Analyze Event (Event-Triggered)
# ==============================================================================
@app.task(name='jarvis.analyze_event', bind=True, max_retries=3)
def analyze_event_task(self, user_id: int, event_id: str):
    """
    Quick intervention check after user logs an event.
    Target: <2 seconds execution time.
    
    This runs immediately after event logging to provide real-time feedback.
    If urgent interventions are found (e.g., overtraining), user gets notified.
    """
    try:
        logger.info(f"Analyzing event {event_id} for user {user_id}")
        
        # Get the event details
        event = {'id': event_id, 'user_id': user_id}
        
        # Run event-triggered workflow (quick check only)
        result = asyncio.run(
            orchestrator.run_event_triggered_workflow(user_id, event)
        )
        
        # Log result
        logger.info(f"Event analysis complete: {result}")
        
        # If urgent interventions found, send notification (optional)
        if result.get('immediate_feedback'):
            interventions = result['immediate_feedback']
            if interventions:
                logger.warning(f"Urgent interventions for user {user_id}: {interventions}")
                # TODO: Send push notification here
        
        return {
            'status': 'success',
            'user_id': user_id,
            'event_id': event_id,
            'interventions_count': len(result.get('immediate_feedback', [])),
            'execution_time_ms': result.get('execution_time_ms', 0)
        }
        
    except Exception as exc:
        logger.error(f"Error analyzing event {event_id}: {exc}")
        # Retry task with exponential backoff
        raise self.retry(exc=exc, countdown=60)


# ==============================================================================
# TASK 2: Daily Workflow (Scheduled)
# ==============================================================================
@app.task(name='jarvis.daily_workflow', bind=True, max_retries=2)
def daily_workflow_task(self, user_id: int):
    """
    Run comprehensive daily analysis for a user.
    Scheduled: Every day at 2:00 AM UTC.
    
    Executes full workflow: PatternDetector → Forecaster → Interventionist
    Provides morning insights and recommendations.
    """
    try:
        logger.info(f"Starting daily workflow for user {user_id}")
        
        # Run full daily workflow
        result = asyncio.run(
            orchestrator.run_daily_workflow(user_id)
        )
        
        logger.info(f"Daily workflow complete for user {user_id}: {result}")
        
        # Send morning summary notification (optional)
        if result.get('success'):
            summary = (
                f"Good morning! Your daily insights:\n"
                f"- {result.get('patterns_detected', 0)} patterns found\n"
                f"- Forecast: {result.get('forecast_generated', False)}\n"
                f"- {result.get('interventions_triggered', 0)} recommendations"
            )
            logger.info(f"Morning summary for user {user_id}: {summary}")
            # TODO: Send push notification with summary
        
        return result
        
    except Exception as exc:
        logger.error(f"Error in daily workflow for user {user_id}: {exc}")
        # Retry once after 5 minutes
        raise self.retry(exc=exc, countdown=300)


# ==============================================================================
# TASK 3: Detect Patterns for All Users (Scheduled)
# ==============================================================================
@app.task(name='jarvis.detect_patterns_all_users', bind=True)
def detect_patterns_all_users_task(self):
    """
    Run pattern detection for all active users.
    Scheduled: Every 6 hours.
    
    Keeps the pattern database fresh by analyzing recent events.
    """
    try:
        logger.info("Starting pattern detection for all users")
        
        # Get all active users (users with events in last 30 days)
        users = get_active_users(days=30)
        logger.info(f"Found {len(users)} active users")
        
        success_count = 0
        error_count = 0
        
        # Process each user
        for user_id in users:
            try:
                logger.info(f"Detecting patterns for user {user_id}")
                
                # Run pattern detection
                patterns = asyncio.run(
                    pattern_detector.detect_patterns(user_id)
                )
                
                logger.info(f"Found {len(patterns)} patterns for user {user_id}")
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to detect patterns for user {user_id}: {e}")
                error_count += 1
                continue  # Don't stop, process next user
        
        result = {
            'status': 'complete',
            'users_processed': success_count,
            'users_failed': error_count,
            'total_users': len(users)
        }
        
        logger.info(f"Pattern detection complete: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Error in pattern detection task: {exc}")
        return {'status': 'error', 'error': str(exc)}


# ==============================================================================
# TASK 4: Generate Forecasts for All Users (Scheduled)
# ==============================================================================
@app.task(name='jarvis.generate_forecasts_all_users', bind=True)
def generate_forecasts_all_users_task(self):
    """
    Generate 7-day forecasts for all active users.
    Scheduled: Every day at 1:00 AM UTC (before daily workflow).
    
    Predicts capacity, burnout risk, and optimal timing for next 7 days.
    """
    try:
        logger.info("Starting forecast generation for all users")
        
        # Get all active users
        users = get_active_users(days=30)
        logger.info(f"Found {len(users)} active users")
        
        success_count = 0
        error_count = 0
        
        # Process each user
        for user_id in users:
            try:
                logger.info(f"Generating forecast for user {user_id}")
                
                # Run forecast generation
                forecast = asyncio.run(
                    forecaster.generate_forecast(user_id, days=7)
                )
                
                logger.info(f"Generated forecast for user {user_id}")
                success_count += 1
                
            except Exception as e:
                logger.error(f"Failed to generate forecast for user {user_id}: {e}")
                error_count += 1
                continue  # Don't stop, process next user
        
        result = {
            'status': 'complete',
            'users_processed': success_count,
            'users_failed': error_count,
            'total_users': len(users)
        }
        
        logger.info(f"Forecast generation complete: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Error in forecast generation task: {exc}")
        return {'status': 'error', 'error': str(exc)}


# ==============================================================================
# TASK 5: Cleanup Old Data (Scheduled)
# ==============================================================================
@app.task(name='jarvis.cleanup_old_data', bind=True)
def cleanup_old_data_task(self, days=365):
    """
    Remove events, patterns, and interventions older than X days.
    Scheduled: Monthly on 1st at 3:00 AM UTC.
    Default: Remove data older than 365 days (1 year).
    
    Keeps database size manageable and complies with data retention policies.
    """
    try:
        logger.info(f"Starting data cleanup (removing data older than {days} days)")
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
        
        import sqlite3
        conn = sqlite3.connect(jarvis_db.db_path)
        cursor = conn.cursor()
        
        # Delete old events
        cursor.execute(
            "DELETE FROM events WHERE timestamp < ?",
            (cutoff_str,)
        )
        events_deleted = cursor.rowcount
        logger.info(f"Deleted {events_deleted} old events")
        
        # Delete old patterns
        cursor.execute(
            "DELETE FROM patterns WHERE last_seen < ?",
            (cutoff_str,)
        )
        patterns_deleted = cursor.rowcount
        logger.info(f"Deleted {patterns_deleted} old patterns")
        
        # Delete old interventions
        cursor.execute(
            "DELETE FROM interventions WHERE created_at < ?",
            (cutoff_str,)
        )
        interventions_deleted = cursor.rowcount
        logger.info(f"Deleted {interventions_deleted} old interventions")
        
        conn.commit()
        conn.close()
        
        result = {
            'status': 'success',
            'cutoff_date': cutoff_str,
            'events_deleted': events_deleted,
            'patterns_deleted': patterns_deleted,
            'interventions_deleted': interventions_deleted,
            'total_deleted': events_deleted + patterns_deleted + interventions_deleted
        }
        
        logger.info(f"Data cleanup complete: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Error in data cleanup task: {exc}")
        return {'status': 'error', 'error': str(exc)}


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_active_users(days=30):
    """
    Get list of users who have logged events in the last X days.
    
    Args:
        days: Number of days to look back (default: 30)
    
    Returns:
        List of user IDs
    """
    try:
        import sqlite3
        conn = sqlite3.connect(jarvis_db.db_path)
        cursor = conn.cursor()
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # Get distinct user IDs with recent events
        cursor.execute("""
            SELECT DISTINCT user_id 
            FROM events 
            WHERE timestamp > ?
            ORDER BY user_id
        """, (cutoff_str,))
        
        users = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        return users
        
    except Exception as e:
        logger.error(f"Error getting active users: {e}")
        return []


def send_notification(user_id: int, title: str, message: str):
    """
    Send push notification to user.
    
    Args:
        user_id: User ID to send notification to
        title: Notification title
        message: Notification message
    
    TODO: Implement push notification integration (Firebase, OneSignal, etc.)
    """
    logger.info(f"Notification for user {user_id}: {title} - {message}")
    # TODO: Integrate with push notification service
    pass


# ==============================================================================
# TASK 6: Health Check (Optional)
# ==============================================================================
@app.task(name='jarvis.health_check')
def health_check_task():
    """
    Simple health check to verify system is operational.
    Scheduled: Every hour.
    
    Verifies that:
    - Database is accessible
    - Agents can be imported
    - Redis is working (if this task runs, Redis is working!)
    """
    try:
        # Check database
        import sqlite3
        conn = sqlite3.connect(jarvis_db.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        event_count = cursor.fetchone()[0]
        conn.close()
        
        result = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'total_events': event_count,
            'agents': {
                'orchestrator': 'loaded',
                'pattern_detector': 'loaded',
                'forecaster': 'loaded',
                'interventionist': 'loaded'
            }
        }
        
        logger.info(f"Health check passed: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Health check failed: {exc}")
        return {
            'status': 'unhealthy',
            'error': str(exc),
            'timestamp': datetime.now().isoformat()
        }