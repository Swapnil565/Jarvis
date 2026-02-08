"""
Celery Configuration for Jarvis Backend
Production-ready configuration with Redis broker and result backend
"""

from kombu import Queue
from datetime import timedelta
from celery.schedules import crontab
import os

from config import settings


class CeleryConfig:
    """Production Celery configuration"""
    
    # ==================== BROKER SETTINGS ====================
    # Redis as message broker (change to your Redis URL in production)
    broker_url = os.getenv('CELERY_BROKER_URL') or settings.CELERY_BROKER_URL or (settings.REDIS_URL + '/0')
    
    # Broker connection settings
    broker_connection_retry_on_startup = True
    broker_connection_retry = True
    broker_connection_max_retries = 10
    broker_pool_limit = 10  # Max connections to broker
    
    # ==================== RESULT BACKEND ====================
    # Redis as result backend
    result_backend = os.getenv('CELERY_RESULT_BACKEND') or settings.CELERY_RESULT_BACKEND or (settings.REDIS_URL + '/1')
    
    # Result settings
    result_expires = 86400  # Results expire after 24 hours
    result_persistent = True  # Persist results
    result_compression = 'gzip'  # Compress results
    
    # ==================== SERIALIZATION ====================
    # Use JSON for security (pickle can execute arbitrary code)
    task_serializer = 'json'
    result_serializer = 'json'
    accept_content = ['json']
    
    # ==================== TIMEZONE ====================
    timezone = 'Asia/Kolkata'  # Indian timezone
    enable_utc = False
    
    # ==================== TASK SETTINGS ====================
    # Task execution settings
    task_acks_late = True  # Acknowledge after task completes (safer)
    task_reject_on_worker_lost = True  # Reject if worker dies
    task_track_started = True  # Track when tasks start
    task_time_limit = 600  # 10 minutes max per task
    task_soft_time_limit = 540  # Soft limit at 9 minutes (sends warning)
    
    # Retry settings
    task_autoretry_for = (Exception,)  # Retry on any exception
    task_retry_kwargs = {'max_retries': 3}  # Retry up to 3 times
    task_retry_backoff = True  # Exponential backoff
    task_retry_backoff_max = 600  # Max 10 minutes between retries
    task_retry_jitter = True  # Add randomness to prevent thundering herd
    
    # ==================== WORKER SETTINGS ====================
    # Worker prefetch settings (how many tasks to prefetch)
    worker_prefetch_multiplier = int(os.getenv('CELERY_PREFETCH_MULTIPLIER', settings.CELERY_PREFETCH_MULTIPLIER))
    worker_max_tasks_per_child = int(os.getenv('CELERY_MAX_TASKS_PER_CHILD', settings.CELERY_MAX_TASKS_PER_CHILD))
    worker_disable_rate_limits = False  # Enable rate limiting
    
    # ==================== LOGGING ====================
    # Worker log settings
    worker_redirect_stdouts = True
    worker_redirect_stdouts_level = os.getenv('LOG_LEVEL', 'INFO')
    
    # ==================== BEAT SCHEDULE ====================
    # Celery Beat schedule for periodic tasks
    beat_schedule = {
        # Health check every 5 minutes
        'health-check-5min': {
            'task': 'celery_tasks.health_check',
            'schedule': crontab(minute='*/5'),  # Every 5 minutes
        },
        
        # Daily agent tasks at 2 AM IST (8:30 PM UTC previous day)
        'daily-all-agents': {
            'task': 'celery_tasks.run_all_agents',
            'schedule': crontab(hour=20, minute=30),  # 2 AM IST = 8:30 PM UTC
        },
        
        # Weekly cleanup on Sunday at 3 AM IST
        'weekly-cleanup': {
            'task': 'celery_tasks.cleanup_old_data',
            'schedule': crontab(hour=21, minute=30, day_of_week=6),  # 3 AM IST Sunday = 9:30 PM UTC Saturday
        },
    }
    
    # Beat schedule type (use database scheduler for dynamic schedules)
    beat_scheduler = 'celery.beat:PersistentScheduler'
    beat_schedule_filename = 'celerybeat-schedule'
    
    # ==================== MONITORING ====================
    # Send events for monitoring
    worker_send_task_events = True
    task_send_sent_event = True
    
    # ==================== TASK ROUTES ====================
    # Route different tasks to different queues
    task_routes = {
        'celery_tasks.run_insight_generator': {'queue': 'agents'},
        'celery_tasks.run_forecaster': {'queue': 'agents'},
        'celery_tasks.run_interventionist': {'queue': 'agents'},
        'celery_tasks.health_check': {'queue': 'monitoring'},
        'celery_tasks.cleanup_old_data': {'queue': 'maintenance'},
    }
    
    # Define queues
    task_queues = (
        Queue('agents', routing_key='agents'),
        Queue('monitoring', routing_key='monitoring'),
        Queue('maintenance', routing_key='maintenance'),
        Queue('default', routing_key='default'),
    )
    
    task_default_queue = 'default'
    task_default_exchange = 'tasks'
    task_default_routing_key = 'default'
    
    # ==================== SECURITY ====================
    # Security settings
    task_always_eager = False  # Never run tasks synchronously in production
    task_eager_propagates = False
    task_ignore_result = False  # Store results
    task_store_errors_even_if_ignored = True
    
    # ==================== RATE LIMITS ====================
    # Rate limiting (tasks per second)
    task_annotations = {
        'celery_tasks.run_insight_generator': {'rate_limit': '10/m'},  # Max 10 per minute
        'celery_tasks.run_forecaster': {'rate_limit': '10/m'},
        'celery_tasks.run_interventionist': {'rate_limit': '10/m'},
        'celery_tasks.health_check': {'rate_limit': '1/s'},
    }
    
    # ==================== DATABASE TASK RESULT BACKEND (OPTIONAL) ====================
    # Uncomment to use database backend instead of Redis for results
    # result_backend = 'db+sqlite:///celery_results.db'
    # result_backend_transport_options = {
    #     'echo': False,
    # }


# Simplified config for development
class DevelopmentConfig(CeleryConfig):
    """Development Celery configuration (less strict)"""
    
    # Simpler broker for local dev
    broker_url = 'redis://localhost:6379/0'
    result_backend = 'redis://localhost:6379/1'
    
    # Faster task expiration
    result_expires = 3600  # 1 hour
    
    # Less retries in dev
    task_retry_kwargs = {'max_retries': 1}
    
    # Simplified beat schedule (more frequent for testing)
    beat_schedule = {
        'test-insight-generation': {
            'task': 'celery_tasks.run_insight_generator',
            'schedule': timedelta(minutes=5),  # Every 5 minutes for testing
        },
        'test-forecast-generation': {
            'task': 'celery_tasks.run_forecaster',
            'schedule': timedelta(minutes=6),
        },
        'test-intervention-check': {
            'task': 'celery_tasks.run_interventionist',
            'schedule': timedelta(minutes=7),
        },
    }


# Config selector
def get_config():
    """Get config based on environment"""
    env = os.getenv('JARVIS_ENV', 'development')
    
    if env == 'production':
        return CeleryConfig()
    else:
        return DevelopmentConfig()
