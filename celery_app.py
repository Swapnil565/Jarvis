"""
Celery App Initialization for Jarvis Backend
Creates and configures the Celery application instance
"""

from celery import Celery
import os

# Import configuration
from celery_config import get_config

# Get configuration based on environment
config = get_config()

# Create Celery app
app = Celery('jarvis')

# Load configuration from config object
app.config_from_object(config)

# Import tasks explicitly (since celery_tasks.py is a module, not a package)
# This ensures tasks are registered with the Celery app
try:
    import celery_tasks
    # Tasks are registered via decorators when the module is imported
except ImportError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import celery_tasks: {e}")

# Optional: Configure Celery to use JSON for datetime
app.conf.update(
    enable_utc=False,
    timezone='Asia/Kolkata',
)

# Log configuration on startup
@app.on_after_configure.connect
def setup_logging(sender, **kwargs):
    """Configure logging after Celery is configured"""
    import logging
    logger = logging.getLogger(__name__)
    
    env = os.getenv('JARVIS_ENV', 'development')
    logger.info(f"🚀 Celery app started in {env} mode")
    logger.info(f"   Broker: {app.conf.broker_url}")
    logger.info(f"   Backend: {app.conf.result_backend}")
    logger.info(f"   Timezone: {app.conf.timezone}")
    logger.info(f"   Tasks discovered: {len(app.tasks)}")


if __name__ == '__main__':
    # Start Celery worker when running this file directly
    app.start()
