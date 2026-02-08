try:
    # Pydantic v2 split BaseSettings into pydantic-settings
    from pydantic_settings import BaseSettings
except Exception:
    from pydantic import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Centralized application settings loaded from environment or .env file."""

    # Environment
    JARVIS_ENV: str = 'development'

    # Secrets
    SECRET_KEY: str = 'change-me-in-production'

    # Database / Broker
    DATABASE_URL: str = 'sqlite:///jarvis_dev.db'
    REDIS_URL: str = 'redis://localhost:6379'
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    # API
    API_HOST: str = '0.0.0.0'
    API_PORT: int = 8000
    DEBUG: bool = True

    # Logging
    LOG_LEVEL: str = 'INFO'
    LOG_FORMAT: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_DIR: str = './logs'

    # Celery runtime tuning (can be overridden in env)
    CELERY_WORKER_CONCURRENCY: int = 2
    CELERY_PREFETCH_MULTIPLIER: int = 4
    CELERY_MAX_TASKS_PER_CHILD: int = 1000

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
    # We'll configure pydantic behavior after class definition depending on
    # the installed pydantic major version. This avoids defining both
    # `Config` and `model_config` simultaneously which is invalid.


# Post-class configuration: adapt for pydantic v1 vs v2
import pydantic as _pyd
def _apply_pydantic_config():
    try:
        ver = tuple(int(x) for x in _pyd.__version__.split('.')[:2])
    except Exception:
        ver = (2, 0)

    if ver >= (2, 0):
        # pydantic v2+: set model_config
        Settings.model_config = {
            'extra': 'ignore',
            'env_file': '.env',
            'env_file_encoding': 'utf-8'
        }
    else:
        # pydantic v1: provide Config inner class
        class _Cfg:
            env_file = '.env'
            env_file_encoding = 'utf-8'
            extra = 'ignore'

        Settings.Config = _Cfg


_apply_pydantic_config()


def _fallback_settings():
    """Create a lightweight settings object from environment variables if
    pydantic Settings cannot be instantiated (avoids failing on extra keys).
    """
    from types import SimpleNamespace
    try:
        # Load .env if present
        from dotenv import load_dotenv
        load_dotenv()
    except Exception:
        pass

    import os
    env = os.environ

    return SimpleNamespace(
        JARVIS_ENV=env.get('JARVIS_ENV', 'development'),
        SECRET_KEY=env.get('SECRET_KEY', 'change-me-in-production'),
        DATABASE_URL=env.get('DATABASE_URL', 'sqlite:///jarvis_dev.db'),
        REDIS_URL=env.get('REDIS_URL', 'redis://localhost:6379'),
        CELERY_BROKER_URL=env.get('CELERY_BROKER_URL') or None,
        CELERY_RESULT_BACKEND=env.get('CELERY_RESULT_BACKEND') or None,
        API_HOST=env.get('API_HOST', '0.0.0.0'),
        API_PORT=int(env.get('API_PORT', '8000')),
        DEBUG=env.get('DEBUG', 'True').lower() in ('1', 'true', 'yes'),
        LOG_LEVEL=env.get('LOG_LEVEL', 'INFO'),
        LOG_FORMAT=env.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        LOG_DIR=env.get('LOG_DIR', './logs'),
        CELERY_WORKER_CONCURRENCY=int(env.get('CELERY_WORKER_CONCURRENCY', '2')),
        CELERY_PREFETCH_MULTIPLIER=int(env.get('CELERY_PREFETCH_MULTIPLIER', '4')),
        CELERY_MAX_TASKS_PER_CHILD=int(env.get('CELERY_MAX_TASKS_PER_CHILD', '1000')),
    )


# Instantiate settings, falling back to a simple loader if Pydantic validation fails
try:
    settings = Settings()
except Exception:
    settings = _fallback_settings()

# Ensure log dir exists when imported
Path(settings.LOG_DIR).mkdir(parents=True, exist_ok=True)
