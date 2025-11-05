"""
Unit tests for AgentOrchestrator
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import asyncio
from agents.orchestrator import AgentOrchestrator


@pytest.fixture
def orchestrator():
    return AgentOrchestrator()


def test_orchestrator_initialization(orchestrator):
    """Test orchestrator initializes with all agents"""
    assert orchestrator.pattern_detector is not None
    assert orchestrator.forecaster is not None
    assert orchestrator.interventionist is not None
    assert orchestrator.jarvis_db is not None
    assert isinstance(orchestrator.workflow_cache, dict)
    assert isinstance(orchestrator.last_daily_run, dict)


def test_daily_workflow_smoke(orchestrator):
    """Test daily workflow runs without crashing (smoke test)"""
    # This will fail gracefully with no data, but should not crash
    result = asyncio.run(orchestrator.run_daily_workflow(user_id=99999))
    
    assert 'success' in result
    assert 'patterns_detected' in result
    assert 'forecast_generated' in result
    assert 'interventions_triggered' in result
    assert 'execution_time_ms' in result
    assert 'errors' in result
    
    # Should complete even with no data
    assert result['execution_time_ms'] > 0


def test_event_triggered_workflow_smoke(orchestrator):
    """Test event-triggered workflow runs without crashing"""
    event = {
        'event_type': 'workout',
        'feeling': 'great',
        'timestamp': '2024-01-01T10:00:00'
    }
    
    result = asyncio.run(orchestrator.run_event_triggered_workflow(user_id=99999, event=event))
    
    assert 'immediate_feedback' in result
    assert 'execution_time_ms' in result
    
    # Should be fast (<2 seconds = 2000ms)
    assert result['execution_time_ms'] < 2000


def test_get_workflow_status(orchestrator):
    """Test workflow status retrieval"""
    status = orchestrator.get_workflow_status(user_id=1)
    
    assert 'last_daily_run' in status
    assert 'cached_data_available' in status
    assert 'cache_age_hours' in status
    assert 'patterns_count' in status
    assert 'interventions_count' in status


def test_workflow_caching(orchestrator):
    """Test that workflow results are cached"""
    user_id = 12345
    
    # Run workflow
    asyncio.run(orchestrator.run_daily_workflow(user_id))
    
    # Check cache was populated
    assert user_id in orchestrator.workflow_cache
    cached_data = orchestrator.workflow_cache[user_id]
    
    assert 'patterns' in cached_data
    assert 'forecast' in cached_data
    assert 'interventions' in cached_data
    assert 'timestamp' in cached_data


def test_workflow_error_handling(orchestrator):
    """Test that workflow handles errors gracefully"""
    # Use a very large user_id that won't have data
    result = asyncio.run(orchestrator.run_daily_workflow(user_id=999999999))
    
    # Should not crash, should return result with errors
    assert isinstance(result, dict)
    assert 'errors' in result
    assert isinstance(result['errors'], list)
    
    # Even with errors, should have execution time
    assert result['execution_time_ms'] > 0


def test_event_triggered_latency(orchestrator):
    """Test that event-triggered workflow meets latency requirements"""
    event = {
        'event_type': 'meditation',
        'feeling': 'calm',
        'timestamp': '2024-01-01T08:00:00'
    }
    
    result = asyncio.run(orchestrator.run_event_triggered_workflow(user_id=1, event=event))
    
    # Must complete in under 2000ms (2 seconds)
    assert result['execution_time_ms'] < 2000, f"Event workflow too slow: {result['execution_time_ms']}ms"


def test_workflow_result_structure(orchestrator):
    """Test that daily workflow returns correct structure"""
    result = asyncio.run(orchestrator.run_daily_workflow(user_id=1))
    
    # Check all required keys
    required_keys = ['success', 'patterns_detected', 'forecast_generated', 
                     'interventions_triggered', 'execution_time_ms', 'errors']
    
    for key in required_keys:
        assert key in result, f"Missing key in result: {key}"
    
    # Check types
    assert isinstance(result['success'], bool)
    assert isinstance(result['patterns_detected'], int)
    assert isinstance(result['forecast_generated'], bool)
    assert isinstance(result['interventions_triggered'], int)
    assert isinstance(result['execution_time_ms'], int)
    assert isinstance(result['errors'], list)


def test_concurrent_workflows(orchestrator):
    """Test that multiple workflows can run concurrently"""
    async def run_multiple():
        # Run workflows for 3 different users concurrently
        tasks = [
            orchestrator.run_daily_workflow(user_id=1),
            orchestrator.run_daily_workflow(user_id=2),
            orchestrator.run_daily_workflow(user_id=3)
        ]
        results = await asyncio.gather(*tasks)
        return results
    
    results = asyncio.run(run_multiple())
    
    assert len(results) == 3
    for result in results:
        assert 'success' in result
        assert 'execution_time_ms' in result
