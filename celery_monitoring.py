"""
Celery Monitoring and Logging Setup
Production-ready logging, monitoring, and error tracking
"""

import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

from config import settings

# Create logs directory (from settings)
LOGS_DIR = Path(os.getenv('LOG_DIR', settings.LOG_DIR))
LOGS_DIR.mkdir(parents=True, exist_ok=True)


def setup_celery_logging():
    """
    Set up production logging for Celery tasks.
    Creates separate log files for different severity levels.
    """
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Get root logger
    root_logger = logging.getLogger()
    root_level = os.getenv('LOG_LEVEL', settings.LOG_LEVEL)
    root_logger.setLevel(getattr(logging, root_level.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # ==================== CONSOLE HANDLER ====================
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, root_level.upper(), logging.INFO))
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)
    
    # ==================== FILE HANDLER (ALL LOGS) ====================
    all_logs_file = LOGS_DIR / 'celery_all.log'
    all_handler = logging.handlers.RotatingFileHandler(
        all_logs_file,
        maxBytes=10_000_000,  # 10MB
        backupCount=5,  # Keep 5 old files
        encoding='utf-8'
    )
    # All logs should capture debug locally; production may override via LOG_LEVEL
    all_handler.setLevel(logging.DEBUG)
    all_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(all_handler)
    
    # ==================== FILE HANDLER (ERRORS ONLY) ====================
    error_logs_file = LOGS_DIR / 'celery_errors.log'
    error_handler = logging.handlers.RotatingFileHandler(
        error_logs_file,
        maxBytes=5_000_000,  # 5MB
        backupCount=10,  # Keep more error logs
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(error_handler)
    
    # ==================== FILE HANDLER (TASKS ONLY) ====================
    task_logs_file = LOGS_DIR / 'celery_tasks.log'
    task_handler = logging.handlers.RotatingFileHandler(
        task_logs_file,
        maxBytes=10_000_000,  # 10MB
        backupCount=3,
        encoding='utf-8'
    )
    task_handler.setLevel(getattr(logging, root_level.upper(), logging.INFO))
    task_handler.setFormatter(detailed_formatter)
    
    # Only log celery_tasks module
    task_logger = logging.getLogger('celery_tasks')
    task_logger.addHandler(task_handler)
    
    # ==================== AGENT LOGS ====================
    agents_logs_file = LOGS_DIR / 'agents.log'
    agents_handler = logging.handlers.RotatingFileHandler(
        agents_logs_file,
        maxBytes=10_000_000,
        backupCount=3,
        encoding='utf-8'
    )
    agents_handler.setLevel(getattr(logging, root_level.upper(), logging.INFO))
    agents_handler.setFormatter(detailed_formatter)
    
    # Log all agents
    for agent_module in ['agents.insight_generator', 'agents.forecaster', 'agents.interventionist']:
        agent_logger = logging.getLogger(agent_module)
        agent_logger.addHandler(agents_handler)
    
    logging.info(f"📝 Logging configured - Logs directory: {LOGS_DIR}")
    
    return root_logger


def setup_celery_monitoring():
    """
    Set up monitoring for Celery tasks.
    Creates monitoring hooks and metrics collection.
    """
    from celery import signals
    
    # Task execution metrics
    task_metrics = {
        'total_tasks': 0,
        'successful_tasks': 0,
        'failed_tasks': 0,
        'retried_tasks': 0,
        'task_durations': []
    }
    
    @signals.task_prerun.connect
    def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
        """Called before task execution"""
        logger = logging.getLogger(__name__)
        logger.info(f"⏳ Task starting: {task.name} [{task_id}]")
        
        # Store start time
        task.request.started_at = datetime.now()
        task_metrics['total_tasks'] += 1
    
    @signals.task_postrun.connect
    def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, **extra):
        """Called after task execution"""
        logger = logging.getLogger(__name__)
        
        # Calculate duration
        if hasattr(task.request, 'started_at'):
            duration = (datetime.now() - task.request.started_at).total_seconds()
            task_metrics['task_durations'].append(duration)
            logger.info(f"✅ Task completed: {task.name} [{task_id}] in {duration:.2f}s")
        else:
            logger.info(f"✅ Task completed: {task.name} [{task_id}]")
    
    @signals.task_success.connect
    def task_success_handler(sender=None, **kwargs):
        """Called when task succeeds"""
        task_metrics['successful_tasks'] += 1
    
    @signals.task_failure.connect
    def task_failure_handler(sender=None, task_id=None, exception=None, args=None, kwargs=None, traceback=None, einfo=None, **extra):
        """Called when task fails"""
        logger = logging.getLogger(__name__)
        logger.error(f"❌ Task failed: {sender.name} [{task_id}]")
        logger.error(f"   Exception: {exception}")
        logger.error(f"   Traceback: {einfo}")
        
        task_metrics['failed_tasks'] += 1
    
    @signals.task_retry.connect
    def task_retry_handler(sender=None, task_id=None, reason=None, einfo=None, **extra):
        """Called when task is retried"""
        logger = logging.getLogger(__name__)
        logger.warning(f"🔄 Task retrying: {sender.name} [{task_id}]")
        logger.warning(f"   Reason: {reason}")
        
        task_metrics['retried_tasks'] += 1
    
    @signals.worker_ready.connect
    def worker_ready_handler(sender=None, **kwargs):
        """Called when worker is ready"""
        logger = logging.getLogger(__name__)
        logger.info(f"🚀 Celery worker ready: {sender.hostname}")
    
    @signals.worker_shutdown.connect
    def worker_shutdown_handler(sender=None, **kwargs):
        """Called when worker shuts down"""
        logger = logging.getLogger(__name__)
        logger.info(f"🛑 Celery worker shutting down: {sender.hostname}")
        
        # Log final metrics
        logger.info(f"📊 Final metrics:")
        logger.info(f"   Total tasks: {task_metrics['total_tasks']}")
        logger.info(f"   Successful: {task_metrics['successful_tasks']}")
        logger.info(f"   Failed: {task_metrics['failed_tasks']}")
        logger.info(f"   Retried: {task_metrics['retried_tasks']}")
        
        if task_metrics['task_durations']:
            avg_duration = sum(task_metrics['task_durations']) / len(task_metrics['task_durations'])
            logger.info(f"   Avg duration: {avg_duration:.2f}s")
    
    logging.info("📊 Monitoring configured")


def get_task_metrics():
    """
    Get current task metrics.
    Can be called from API endpoint to view metrics.
    """
    from celery import current_app
    
    # Get task stats from Celery
    stats = current_app.control.inspect().stats()
    active = current_app.control.inspect().active()
    scheduled = current_app.control.inspect().scheduled()
    
    return {
        'stats': stats,
        'active_tasks': active,
        'scheduled_tasks': scheduled
    }


def export_metrics_to_file():
    """
    Export current metrics to JSON file.
    Can be used for external monitoring tools.
    """
    import json
    
    metrics = get_task_metrics()
    
    metrics_file = LOGS_DIR / f'metrics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2, default=str)
    
    logging.info(f"📈 Metrics exported to {metrics_file}")
    return metrics_file


# Initialize logging on import
setup_celery_logging()


if __name__ == '__main__':
    # Test logging
    logger = logging.getLogger(__name__)
    
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    print(f"\n✅ Logging test complete. Check logs in: {LOGS_DIR}")
