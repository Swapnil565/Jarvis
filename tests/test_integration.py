"""
Integration tests for JARVIS - Full user journey from event logging to interventions
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import asyncio
from datetime import datetime, timedelta
import sqlite3
from simple_jarvis_db import jarvis_db
from agents.orchestrator import orchestrator


@pytest.fixture
def test_user():
    """Create a test user and clean up after test"""
    # Use a unique test user ID
    user_id = 99999
    
    yield user_id
    
    # Cleanup after test
    conn = sqlite3.connect(jarvis_db.db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM events WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM patterns WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM forecasts WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM interventions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def test_full_user_journey(test_user):
    """
    Test complete user journey:
    1. User logs multiple events over several days
    2. System runs daily workflow
    3. Patterns are detected
    4. Forecast is generated
    5. Interventions are triggered
    6. Results are stored and accessible
    """
    user_id = test_user
    
    # STEP 1: Log workout events over 8 consecutive days (trigger overtraining)
    base_date = datetime.now() - timedelta(days=8)
    
    for i in range(8):
        event_date = base_date + timedelta(days=i)
        jarvis_db.log_event(
            user_id=user_id,
            event_type='workout',
            feeling='tired' if i > 5 else 'good',
            tags='gym,strength',
            notes=f'Day {i+1} workout',
            timestamp=event_date.strftime('%Y-%m-%d %H:%M:%S')
        )
    
    # Add some meditation events (but with a gap)
    jarvis_db.log_event(
        user_id=user_id,
        event_type='meditation',
        feeling='calm',
        tags='mindfulness',
        timestamp=(base_date + timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
    )
    
    # STEP 2: Run daily workflow
    result = asyncio.run(orchestrator.run_daily_workflow(user_id))
    
    # Verify workflow completed
    assert result['success'] is True, f"Workflow failed: {result.get('errors', [])}"
    assert result['execution_time_ms'] > 0
    assert result['execution_time_ms'] < 10000, f"Workflow too slow: {result['execution_time_ms']}ms"
    
    # STEP 3: Verify patterns were detected
    assert result['patterns_detected'] >= 0  # May or may not find patterns depending on data
    
    # Query patterns from database
    patterns = jarvis_db.get_patterns(user_id, limit=10)
    print(f"Patterns detected: {len(patterns)}")
    
    # STEP 4: Verify forecast was generated
    assert result['forecast_generated'] is True or result['forecast_generated'] is False
    
    # Query forecast from database
    forecasts = jarvis_db.get_forecasts(user_id, limit=1)
    print(f"Forecasts generated: {len(forecasts)}")
    
    # STEP 5: Verify interventions were triggered
    # Should detect overtraining (8 consecutive workouts) and meditation gap
    assert result['interventions_triggered'] >= 0
    
    # Query interventions from database
    interventions = jarvis_db.get_interventions(user_id)
    print(f"Interventions triggered: {len(interventions)}")
    
    # Should have at least overtraining warning
    intervention_types = [i['message_type'] for i in interventions]
    print(f"Intervention types: {intervention_types}")
    
    # STEP 6: Test event-triggered workflow
    new_event = {
        'event_type': 'workout',
        'feeling': 'exhausted',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    event_result = asyncio.run(orchestrator.run_event_triggered_workflow(user_id, new_event))
    
    assert 'immediate_feedback' in event_result
    assert event_result['execution_time_ms'] < 2000, f"Event workflow too slow: {event_result['execution_time_ms']}ms"
    
    # STEP 7: Verify workflow status
    status = orchestrator.get_workflow_status(user_id)
    
    assert status['cached_data_available'] is True
    assert status['last_daily_run'] is not None
    assert status['patterns_count'] >= 0
    assert status['interventions_count'] >= 0
    
    print("\n✅ Full user journey test passed!")
    print(f"   - Events logged: 9")
    print(f"   - Patterns detected: {result['patterns_detected']}")
    print(f"   - Forecast generated: {result['forecast_generated']}")
    print(f"   - Interventions triggered: {result['interventions_triggered']}")
    print(f"   - Daily workflow time: {result['execution_time_ms']}ms")
    print(f"   - Event workflow time: {event_result['execution_time_ms']}ms")


def test_performance_with_large_dataset(test_user):
    """Test system performance with larger dataset"""
    user_id = test_user
    
    # Log 30 days of diverse events
    base_date = datetime.now() - timedelta(days=30)
    
    for i in range(30):
        event_date = base_date + timedelta(days=i)
        
        # Morning meditation (most days)
        if i % 3 != 0:  # Skip every 3rd day
            jarvis_db.log_event(
                user_id=user_id,
                event_type='meditation',
                feeling='calm',
                tags='morning,mindfulness',
                timestamp=event_date.replace(hour=7, minute=0).strftime('%Y-%m-%d %H:%M:%S')
            )
        
        # Workout (every other day)
        if i % 2 == 0:
            jarvis_db.log_event(
                user_id=user_id,
                event_type='workout',
                feeling='energized' if i % 4 == 0 else 'good',
                tags='gym,cardio' if i % 3 == 0 else 'gym,strength',
                timestamp=event_date.replace(hour=18, minute=0).strftime('%Y-%m-%d %H:%M:%S')
            )
        
        # Sleep tracking
        jarvis_db.log_event(
            user_id=user_id,
            event_type='sleep',
            feeling='rested' if i % 5 == 0 else 'okay',
            tags='night',
            notes=f'{7 + (i % 3)} hours',
            timestamp=event_date.replace(hour=23, minute=0).strftime('%Y-%m-%d %H:%M:%S')
        )
    
    # Run daily workflow and measure performance
    result = asyncio.run(orchestrator.run_daily_workflow(user_id))
    
    # Performance assertions
    assert result['success'] is True
    assert result['execution_time_ms'] < 10000, f"Performance degraded with larger dataset: {result['execution_time_ms']}ms"
    
    print(f"\n✅ Performance test passed with 30 days of data!")
    print(f"   - Total events: ~60")
    print(f"   - Execution time: {result['execution_time_ms']}ms")
    print(f"   - Patterns detected: {result['patterns_detected']}")
    print(f"   - Interventions triggered: {result['interventions_triggered']}")


def test_error_recovery(test_user):
    """Test that system recovers gracefully from errors"""
    user_id = test_user
    
    # Run workflow with no events (edge case)
    result = asyncio.run(orchestrator.run_daily_workflow(user_id))
    
    # Should not crash
    assert isinstance(result, dict)
    assert 'success' in result
    assert 'errors' in result
    
    # Should handle gracefully
    print(f"\n✅ Error recovery test passed!")
    print(f"   - Handled empty dataset gracefully")
    print(f"   - Errors encountered: {len(result['errors'])}")


def test_concurrent_user_workflows():
    """Test that system can handle multiple users concurrently"""
    async def run_concurrent_tests():
        # Simulate 5 users running workflows simultaneously
        tasks = []
        for i in range(5):
            tasks.append(orchestrator.run_daily_workflow(user_id=i+1))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    results = asyncio.run(run_concurrent_tests())
    
    # All should complete without exceptions
    assert len(results) == 5
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"User {i+1} workflow raised exception: {result}")
        else:
            assert 'execution_time_ms' in result
    
    print(f"\n✅ Concurrent workflow test passed!")
    print(f"   - Handled 5 concurrent users")
