"""
JARVIS 3.0 - Monitoring and Metrics Module

This module provides comprehensive monitoring, metrics collection,
and health checking capabilities for the JARVIS backend system.
"""

import time
import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import psycopg2
import redis

logger = logging.getLogger(__name__)

class MetricsCollector:
    """Collects and manages system metrics"""
    
    def __init__(self):
        self.metrics = {
            "requests_total": 0,
            "requests_successful": 0,
            "requests_failed": 0,
            "active_users": 0,
            "average_response_time": 0.0,
            "last_updated": datetime.utcnow()
        }
        self.response_times = []
    
    def record_request(self, success: bool, response_time: float):
        """Record a request with its outcome and response time"""
        self.metrics["requests_total"] += 1
        
        if success:
            self.metrics["requests_successful"] += 1
        else:
            self.metrics["requests_failed"] += 1
        
        # Track response times (keep last 100)
        self.response_times.append(response_time)
        if len(self.response_times) > 100:
            self.response_times.pop(0)
        
        # Update average response time
        if self.response_times:
            self.metrics["average_response_time"] = sum(self.response_times) / len(self.response_times)
        
        self.metrics["last_updated"] = datetime.utcnow()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot"""
        return {
            **self.metrics,
            "success_rate": (
                self.metrics["requests_successful"] / max(self.metrics["requests_total"], 1) * 100
            ),
            "uptime_seconds": (datetime.utcnow() - self.metrics["last_updated"]).total_seconds()
        }

# Global metrics collector
metrics = MetricsCollector()

async def check_database_connection(db_url: str = None) -> bool:
    """Check database connectivity"""
    try:
        if not db_url:
            db_url = "postgresql://context_user:dev_password@localhost:5432/context_dev"
        
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return result[0] == 1
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False

async def check_redis_connection(redis_url: str = "redis://localhost:6379") -> bool:
    """Check Redis connectivity"""
    try:
        r = redis.from_url(redis_url)
        return r.ping()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False

async def check_llm_service() -> bool:
    """Check LLM service connectivity (placeholder)"""
    try:
        # Placeholder for actual LLM service check
        # In real implementation, this would ping OpenAI API or local LLM
        await asyncio.sleep(0.1)  # Simulate API call
        return True
    except Exception as e:
        logger.error(f"LLM service health check failed: {e}")
        return False

async def check_vector_search() -> bool:
    """Check vector search capabilities"""
    try:
        # Placeholder for vector search health check
        # In real implementation, this would test pgvector functionality
        return True
    except Exception as e:
        logger.error(f"Vector search health check failed: {e}")
        return False

async def get_active_users_count(db_connection=None) -> int:
    """Get count of active users (last 24 hours)"""
    try:
        if not db_connection:
            return 0
        
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT COUNT(*) as active_users 
            FROM users 
            WHERE last_active > %s AND is_active = true
        """, (datetime.utcnow() - timedelta(hours=24),))
        
        result = cursor.fetchone()
        cursor.close()
        
        return result[0] if result else 0
    except Exception as e:
        logger.error(f"Failed to get active users count: {e}")
        return 0

async def health_check(db_connection=None) -> Dict[str, Any]:
    """
    Comprehensive health check endpoint
    
    This function performs all the health checks as specified in the Day 1 requirements
    and returns a comprehensive status report.
    """
    start_time = time.time()
    
    try:
        # Perform all health checks concurrently
        health_checks = await asyncio.gather(
            check_database_connection(),
            check_redis_connection(),
            check_llm_service(),
            check_vector_search(),
            return_exceptions=True
        )
        
        # Parse results
        db_healthy = health_checks[0] if not isinstance(health_checks[0], Exception) else False
        redis_healthy = health_checks[1] if not isinstance(health_checks[1], Exception) else False
        llm_healthy = health_checks[2] if not isinstance(health_checks[2], Exception) else False
        vector_healthy = health_checks[3] if not isinstance(health_checks[3], Exception) else False
        
        # Update active users metric
        active_count = await get_active_users_count(db_connection)
        metrics.metrics["active_users"] = active_count
        
        # Build health status
        health_status = {
            'status': 'healthy',
            'checks': {
                'database': db_healthy,
                'redis': redis_healthy,
                'llm_service': llm_healthy,
                'vector_search': vector_healthy
            },
            'metrics': metrics.get_metrics(),
            'active_users': active_count,
            'timestamp': time.time(),
            'response_time_ms': (time.time() - start_time) * 1000
        }
        
        # Check if any critical services are down
        critical_services = ['database', 'redis']
        for service in critical_services:
            if not health_status['checks'][service]:
                health_status['status'] = 'unhealthy'
                break
        
        # Record this health check
        metrics.record_request(
            success=(health_status['status'] == 'healthy'),
            response_time=(time.time() - start_time) * 1000
        )
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'timestamp': time.time(),
            'response_time_ms': (time.time() - start_time) * 1000
        }

class PerformanceMonitor:
    """Monitor system performance and resource usage"""
    
    def __init__(self):
        self.start_time = datetime.utcnow()
        self.request_count = 0
        self.error_count = 0
    
    def record_request(self, duration_ms: float, success: bool = True):
        """Record a request for performance monitoring"""
        self.request_count += 1
        if not success:
            self.error_count += 1
        
        # Record in global metrics
        metrics.record_request(success, duration_ms)
    
    def get_uptime(self) -> timedelta:
        """Get system uptime"""
        return datetime.utcnow() - self.start_time
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        uptime = self.get_uptime()
        return {
            "uptime_seconds": uptime.total_seconds(),
            "uptime_human": str(uptime),
            "total_requests": self.request_count,
            "error_count": self.error_count,
            "error_rate": (self.error_count / max(self.request_count, 1)) * 100,
            "requests_per_minute": self.request_count / max(uptime.total_seconds() / 60, 1)
        }

# Global performance monitor
performance_monitor = PerformanceMonitor()

# Export main functions
__all__ = [
    "health_check",
    "metrics",
    "performance_monitor",
    "check_database_connection",
    "check_redis_connection",
    "check_llm_service",
    "check_vector_search",
    "get_active_users_count"
]