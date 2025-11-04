"""
=============================================================================
JARVIS 3.0 - AGENTS PACKAGE (4-Agent System for Burnout Prevention)
=============================================================================

PURPOSE:
--------
Package entry point for JARVIS's multi-agent system. Provides clean imports
for all agents and orchestrates the agent hierarchy. This is the "brain" of
JARVIS composed of 4 specialized AI agents working together.

AGENT ARCHITECTURE:
-------------------
The 4-Agent System (following the 7-day roadmap):

1. DataCollectorAgent (Day 2) - ✅ IMPLEMENTED
   - Role: Parse natural language → structured events
   - Input: "upper body heavy felt great"
   - Output: {category: "physical", event_type: "workout", data: {...}}
   - Status: OPERATIONAL

2. PatternDetectorAgent (Day 3) - 🔨 TODO
   - Role: Analyze events → discover correlations
   - Input: Historical events from database
   - Output: Patterns (workout → task completion correlation)
   - Status: PLACEHOLDER

3. ForecasterAgent (Day 4) - 🔨 TODO
   - Role: Predict capacity → forecast burnout risk
   - Input: Events + patterns
   - Output: 7-day forecast, crash predictions
   - Status: PLACEHOLDER

4. InterventionistAgent (Day 4) - 🔨 TODO
   - Role: Generate recommendations → prevent burnout
   - Input: Patterns + forecasts + current state
   - Output: Warnings, suggestions, insights
   - Status: PLACEHOLDER

DATA FLOW (Complete System):
-----------------------------
USER INPUT → DataCollectorAgent (parse) → DATABASE (store) →
PatternDetectorAgent (analyze) → DATABASE (patterns) →
ForecasterAgent (predict) → InterventionistAgent (recommend) →
DATABASE (interventions) → USER NOTIFICATION

WORKFLOW EXAMPLE:
-----------------
1. User: "ran 5k this morning felt amazing"
2. DataCollectorAgent: Parses → {category: "physical", event_type: "workout", ...}
3. Database: Stores event
4. PatternDetectorAgent (nightly): Analyzes → "Cardio → 60% better mood"
5. ForecasterAgent (nightly): Predicts → "Energy trending up, capacity high"
6. InterventionistAgent (6-hourly): Checks → "No interventions needed, user doing great!"

ORCHESTRATION (Day 5):
-----------------------
Agent coordination workflow:
- Real-time: DataCollectorAgent on every event
- Daily: PatternDetectorAgent + ForecasterAgent (scheduled)
- 6-hourly: InterventionistAgent (check current state)
- Manual: All agents via API endpoints

USAGE:
------
```python
from agents import DataCollectorAgent

# Initialize agent
collector = DataCollectorAgent()

# Parse natural language
result = await collector.parse("upper body heavy felt great")
# Returns: {"category": "physical", "event_type": "workout", ...}
```

DEPENDENCIES:
-------------
- base_agent.py: Shared utilities for all agents
- OpenAI/Groq/Cerebras: LLM providers
- simple_jarvis_db.py: Database operations

PACKAGE EXPORTS:
----------------
Currently exports: DataCollectorAgent (Day 2)
Future exports: PatternDetectorAgent, ForecasterAgent, InterventionistAgent (Days 3-4)
"""

from .data_collector import DataCollectorAgent

__all__ = [
    "DataCollectorAgent",
]
