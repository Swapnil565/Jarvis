# ✅ 1. Sentry automatically records:
# - endpoint name
# - time taken
# - status code
# - input/output size
# - database queries
# - ORM execution time
# - exceptions
# - internal errors

# ✅ 2. Sentry sends this data to their dashboard
# (no effect on your backend speed)

# ✅ 3. You log in to Sentry dashboard
# You see:
# ✅ Slowest endpoints
# ✅ Latency graphs
# ✅ 500 errors
# ✅ Bottlenecks
# ✅ Slow SQL queries
# ✅ Performance flame graphs

# ✅ 4. For errors
# Sentry shows:
# - line number
# - file name
# - stack trace
# - local variables
# - request body
# - user ID
# - environment (prod/dev)
# This is GOLD for debugging.

import sentry_sdk
from sentry_sdk.integrations.fastapi import FastAPIIntegration
from sentry_sdk.integrations.sqlalchemy import SQLAlchemyIntegration
import time
import logging
from fastapi import Request

logger = logging.getLogger("performance")

def init_monitoring_with_sentry():
    """Initialize Sentry monitoring (requires Sentry account)"""
    sentry_sdk.init(
        dsn="YOUR_SENTRY_DSN_HERE",  # Get from sentry.io after signing up
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
        integrations=[
            FastAPIIntegration(),
            SQLAlchemyIntegration(),
        ]
    )

# Alternative: Simple local logging (no Sentry needed)
async def performance_logging_middleware(request: Request, call_next):
    """
    Simple performance logging middleware
    Use this if you don't want to set up Sentry
    """
    start = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = (time.time() - start) * 1000  # milliseconds
    
    # Log based on duration
    if duration > 1000:  # >1 second
        logger.error(f"🔴 VERY SLOW: {request.method} {request.url.path} - {duration:.0f}ms")
    elif duration > 500:  # >500ms
        logger.warning(f"🟡 SLOW: {request.method} {request.url.path} - {duration:.0f}ms")
    else:
        logger.info(f"✅ {request.method} {request.url.path} - {duration:.0f}ms - {response.status_code}")
    
    # Add response time header
    response.headers["X-Response-Time"] = f"{duration:.2f}ms"
    
    return response

# HOW TO USE IN simple_main.py:
# ------------------------------
# Option 1: Use Sentry (production-grade)
# from app.middleware.performance_monitor import init_monitoring_with_sentry
# init_monitoring_with_sentry()
#
# Option 2: Use simple logging (development/testing)
# from app.middleware.performance_monitor import performance_logging_middleware
# app.middleware("http")(performance_logging_middleware)
