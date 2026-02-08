"""
Celery Tasks for Jarvis Backend
All agent tasks with proper error handling, logging, and monitoring
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List
import traceback

from celery import Task
from celery.utils.log import get_task_logger

# Import agents
from agents.insight_generator import InsightGenerator
from agents.forecaster import ForecasterAgent
from agents.interventionist import InterventionistAgent
from core.simple_jarvis_db import SimpleJarvisDB

# Import Celery app (will be created in celery_app.py)
from celery_app import app

# Set up logging
logger = get_task_logger(__name__)


# ==================== BASE TASK CLASS ====================

class AgentTask(Task):
    """
    Base task class with common functionality for all agent tasks.
    Handles database connections, error logging, and result tracking.
    """
    
    def __init__(self):
        self._db = None
    
    @property
    def db(self):
        """Lazy database connection (created per task)"""
        if self._db is None:
            self._db = SimpleJarvisDB()
        return self._db
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        logger.info(f"✅ Task {self.name} succeeded: {task_id}")
        logger.info(f"   Result: {retval}")
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        logger.error(f"❌ Task {self.name} failed: {task_id}")
        logger.error(f"   Error: {exc}")
        logger.error(f"   Traceback: {einfo}")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        logger.warning(f"🔄 Task {self.name} retrying: {task_id}")
        logger.warning(f"   Reason: {exc}")
    
    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        """Called after task returns (cleanup)"""
        # Close database connection
        if self._db is not None:
            # SimpleJarvisDB uses context managers, no explicit close needed
            self._db = None


# ==================== AGENT TASKS ====================

@app.task(base=AgentTask, bind=True, name='celery_tasks.run_insight_generator')
def run_insight_generator(self, user_ids: List[int] = None):
    """
    Run InsightGenerator for specified users or all users.
    
    Args:
        user_ids: List of user IDs to process. If None, process all users.
    
    Returns:
        Dict with results per user
    """
    try:
        logger.info(f"🧠 Starting InsightGenerator task at {datetime.now()}")
        
        # Get user IDs if not provided
        if user_ids is None:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT user_id FROM events")
                user_ids = [row[0] for row in cursor.fetchall()]
        
        if not user_ids:
            logger.warning("⚠️  No users found to process")
            return {'status': 'no_users', 'users_processed': 0}
        
        logger.info(f"   Processing {len(user_ids)} users")
        
        # Process each user
        results = {}
        agent = InsightGenerator(db=self.db)
        
        for user_id in user_ids:
            try:
                logger.info(f"   Processing user {user_id}...")
                result = agent.process({'user_id': user_id})
                
                insights_count = len(result.get('insights', []))
                logger.info(f"   ✅ User {user_id}: {insights_count} insights generated")
                
                results[user_id] = {
                    'status': 'success',
                    'insights_count': insights_count,
                    'insights': result.get('insights', [])
                }
                
            except Exception as e:
                logger.error(f"   ❌ User {user_id} failed: {e}")
                logger.error(f"   {traceback.format_exc()}")
                results[user_id] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Summary
        total_insights = sum(r.get('insights_count', 0) for r in results.values() if r.get('status') == 'success')
        success_count = sum(1 for r in results.values() if r.get('status') == 'success')
        
        logger.info(f"🎉 InsightGenerator completed:")
        logger.info(f"   Users processed: {success_count}/{len(user_ids)}")
        logger.info(f"   Total insights: {total_insights}")
        
        return {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'users_processed': success_count,
            'total_users': len(user_ids),
            'total_insights': total_insights,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"❌ InsightGenerator task failed: {e}")
        logger.error(f"   {traceback.format_exc()}")
        raise


@app.task(base=AgentTask, bind=True, name='celery_tasks.run_forecaster')
def run_forecaster(self, user_ids: List[int] = None):
    """
    Run ForecasterAgent for specified users or all users.
    
    Args:
        user_ids: List of user IDs to process. If None, process all users.
    
    Returns:
        Dict with results per user
    """
    try:
        logger.info(f"🔮 Starting Forecaster task at {datetime.now()}")
        
        # Get user IDs if not provided
        if user_ids is None:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT user_id FROM events")
                user_ids = [row[0] for row in cursor.fetchall()]
        
        if not user_ids:
            logger.warning("⚠️  No users found to process")
            return {'status': 'no_users', 'users_processed': 0}
        
        logger.info(f"   Processing {len(user_ids)} users")
        
        # Process each user
        results = {}
        agent = ForecasterAgent(db=self.db)
        
        for user_id in user_ids:
            try:
                logger.info(f"   Processing user {user_id}...")
                result = agent.process({'user_id': user_id})
                
                energy_debt = result.get('energy_debt', 0)
                forecast_days = len(result.get('forecast', []))
                crash_risk = result.get('crash_risk', {}).get('risk_level', 'unknown')
                
                logger.info(f"   ✅ User {user_id}: Energy debt {energy_debt:.1f}%, Crash risk: {crash_risk}")
                
                results[user_id] = {
                    'status': 'success',
                    'energy_debt': energy_debt,
                    'forecast_days': forecast_days,
                    'crash_risk': crash_risk,
                    'forecast': result.get('forecast', [])
                }
                
            except Exception as e:
                logger.error(f"   ❌ User {user_id} failed: {e}")
                logger.error(f"   {traceback.format_exc()}")
                results[user_id] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Summary
        success_count = sum(1 for r in results.values() if r.get('status') == 'success')
        avg_energy_debt = sum(r.get('energy_debt', 0) for r in results.values() if r.get('status') == 'success') / max(success_count, 1)
        
        logger.info(f"🎉 Forecaster completed:")
        logger.info(f"   Users processed: {success_count}/{len(user_ids)}")
        logger.info(f"   Avg energy debt: {avg_energy_debt:.1f}%")
        
        return {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'users_processed': success_count,
            'total_users': len(user_ids),
            'avg_energy_debt': avg_energy_debt,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"❌ Forecaster task failed: {e}")
        logger.error(f"   {traceback.format_exc()}")
        raise


@app.task(base=AgentTask, bind=True, name='celery_tasks.run_interventionist')
def run_interventionist(self, user_ids: List[int] = None):
    """
    Run InterventionistAgent for specified users or all users.
    
    Args:
        user_ids: List of user IDs to process. If None, process all users.
    
    Returns:
        Dict with results per user
    """
    try:
        logger.info(f"💊 Starting Interventionist task at {datetime.now()}")
        
        # Get user IDs if not provided
        if user_ids is None:
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT DISTINCT user_id FROM events")
                user_ids = [row[0] for row in cursor.fetchall()]
        
        if not user_ids:
            logger.warning("⚠️  No users found to process")
            return {'status': 'no_users', 'users_processed': 0}
        
        logger.info(f"   Processing {len(user_ids)} users")
        
        # Process each user
        results = {}
        agent = InterventionistAgent(db=self.db)
        
        for user_id in user_ids:
            try:
                logger.info(f"   Processing user {user_id}...")
                result = agent.process({'user_id': user_id})
                
                interventions_count = len(result.get('interventions', []))
                warnings_count = len(result.get('warnings', []))
                recommendations_count = len(result.get('recommendations', []))
                
                logger.info(f"   ✅ User {user_id}: {interventions_count} interventions, {warnings_count} warnings")
                
                results[user_id] = {
                    'status': 'success',
                    'interventions_count': interventions_count,
                    'warnings_count': warnings_count,
                    'recommendations_count': recommendations_count,
                    'interventions': result.get('interventions', [])
                }
                
            except Exception as e:
                logger.error(f"   ❌ User {user_id} failed: {e}")
                logger.error(f"   {traceback.format_exc()}")
                results[user_id] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        # Summary
        total_interventions = sum(r.get('interventions_count', 0) for r in results.values() if r.get('status') == 'success')
        total_warnings = sum(r.get('warnings_count', 0) for r in results.values() if r.get('status') == 'success')
        success_count = sum(1 for r in results.values() if r.get('status') == 'success')
        
        logger.info(f"🎉 Interventionist completed:")
        logger.info(f"   Users processed: {success_count}/{len(user_ids)}")
        logger.info(f"   Total interventions: {total_interventions}")
        logger.info(f"   Total warnings: {total_warnings}")
        
        return {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'users_processed': success_count,
            'total_users': len(user_ids),
            'total_interventions': total_interventions,
            'total_warnings': total_warnings,
            'results': results
        }
        
    except Exception as e:
        logger.error(f"❌ Interventionist task failed: {e}")
        logger.error(f"   {traceback.format_exc()}")
        raise


# ==================== MONITORING TASKS ====================

@app.task(name='celery_tasks.health_check')
def health_check():
    """
    Health check task to verify Celery is running properly.
    Runs every 5 minutes.
    """
    try:
        logger.info("❤️  Health check running...")
        
        # Check database connection
        db = SimpleJarvisDB()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM events")
            event_count = cursor.fetchone()[0]
        
        logger.info(f"   ✅ Database accessible: {event_count} events")
        
        return {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'event_count': event_count
        }
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return {
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }


@app.task(name='celery_tasks.cleanup_old_data')
def cleanup_old_data(days_to_keep: int = 90):
    """
    Clean up old data from database.
    Runs weekly on Sunday at 3am.
    
    Args:
        days_to_keep: Number of days of data to keep (default: 90)
    """
    try:
        logger.info(f"🧹 Starting database cleanup (keeping {days_to_keep} days)...")
        
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        
        db = SimpleJarvisDB()
        deleted_counts = {}
        
        with db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Clean old events
            cursor.execute(
                "DELETE FROM events WHERE timestamp < ?",
                (cutoff_date,)
            )
            deleted_counts['events'] = cursor.rowcount
            
            # Clean old patterns (keep insights)
            cursor.execute(
                "DELETE FROM patterns WHERE last_seen < ?",
                (cutoff_date,)
            )
            deleted_counts['patterns'] = cursor.rowcount
            
            # Clean old interventions
            cursor.execute(
                "DELETE FROM interventions WHERE timestamp < ?",
                (cutoff_date,)
            )
            deleted_counts['interventions'] = cursor.rowcount
            
            conn.commit()
        
        logger.info(f"✅ Cleanup completed:")
        logger.info(f"   Events deleted: {deleted_counts['events']}")
        logger.info(f"   Patterns deleted: {deleted_counts['patterns']}")
        logger.info(f"   Interventions deleted: {deleted_counts['interventions']}")
        
        return {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'cutoff_date': cutoff_date,
            'deleted_counts': deleted_counts
        }
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        logger.error(f"   {traceback.format_exc()}")
        raise


# ==================== UTILITY TASKS ====================

@app.task(name='celery_tasks.run_all_agents')
def run_all_agents(user_ids: List[int] = None):
    """
    Convenience task to run all agents in sequence.
    Useful for manual triggers or API endpoints.
    
    Args:
        user_ids: List of user IDs to process. If None, process all users.
    """
    try:
        logger.info("🚀 Running all agents in sequence...")
        
        # Run in order: Insights → Forecast → Interventions
        insights_result = run_insight_generator(user_ids=user_ids)
        forecast_result = run_forecaster(user_ids=user_ids)
        interventions_result = run_interventionist(user_ids=user_ids)
        
        return {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'insights': insights_result,
            'forecast': forecast_result,
            'interventions': interventions_result
        }
        
    except Exception as e:
        logger.error(f"❌ Run all agents failed: {e}")
        raise


@app.task(name='celery_tasks.run_single_user_analysis')
def run_single_user_analysis(user_id: int):
    """
    Run complete analysis for a single user.
    Used for event-triggered workflows (e.g., after user logs event).
    
    Args:
        user_id: User ID to analyze
    """
    try:
        logger.info(f"👤 Running single user analysis for user {user_id}...")
        
        results = {}
        
        # Run InsightGenerator
        agent = InsightGenerator(db=SimpleJarvisDB())
        results['insights'] = agent.process({'user_id': user_id})
        
        # Run Forecaster
        agent = ForecasterAgent(db=SimpleJarvisDB())
        results['forecast'] = agent.process({'user_id': user_id})
        
        # Run Interventionist
        agent = InterventionistAgent(db=SimpleJarvisDB())
        results['interventions'] = agent.process({'user_id': user_id})
        
        logger.info(f"✅ Single user analysis completed for user {user_id}")
        
        return {
            'status': 'completed',
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"❌ Single user analysis failed for user {user_id}: {e}")
        raise
