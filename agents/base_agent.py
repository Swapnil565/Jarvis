"""
=============================================================================
JARVIS 3.0 - BASE AGENT CLASS (Shared Agent Utilities)
=============================================================================

PURPOSE:
--------
Provides shared functionality for all JARVIS agents (DataCollector, PatternDetector,
Forecaster, Interventionist). This is the parent class that all agents inherit from
to avoid code duplication and ensure consistent behavior.

RESPONSIBILITY:
---------------
- Initialize LLM API clients (OpenAI, Groq, Cerebras)
- Load API keys from environment variables (.env file)
- Provide standardized logging for agent actions
- Offer consistent error handling across all agents
- Abstract LLM provider selection (switch between OpenAI/Groq/Cerebras easily)

DATA FLOW (Agent Initialization):
----------------------------------
AGENT CREATION FLOW:
1. Child agent (e.g., DataCollectorAgent) calls super().__init__()
2. BaseAgent loads .env file with API keys
3. Store OPENAI_API_KEY, GROQ_API_KEY, CEREBRAS_API_KEY in instance variables
4. Initialize logger for the specific agent class name
5. Check if at least one API key is available (warn if none found)

LLM CLIENT FLOW:
1. Child agent needs LLM (e.g., DataCollectorAgent.parse() needs GPT-4o-mini)
2. Agent calls self.get_llm_client(provider="openai")
3. BaseAgent checks if openai_api_key exists
4. Import OpenAI client library dynamically
5. Return initialized OpenAI(api_key=...) client
6. If provider unavailable: raise ValueError with helpful message

ERROR HANDLING FLOW:
1. Agent encounters exception during operation (e.g., LLM API error)
2. Agent calls self.handle_error(error, context="parsing workout data")
3. BaseAgent logs error with context for debugging
4. Return standardized error dict: {"success": False, "error": "...", "context": "..."}
5. Agent returns this to simple_main.py for HTTP response

LOGGING FLOW:
1. Agent performs action (e.g., "Parsed natural language to structured event")
2. Agent calls self.log_agent_action("parse_complete", {"tokens_used": 150})
3. BaseAgent logs to console/file with timestamp and agent name
4. Useful for debugging and monitoring agent performance

INHERITANCE HIERARCHY:
----------------------
BaseAgent (this file)
├── DataCollectorAgent (agents/data_collector.py)
├── PatternDetectorAgent (agents/pattern_detector.py) - Day 3
├── ForecasterAgent (agents/forecaster.py) - Day 4
└── InterventionistAgent (agents/interventionist.py) - Day 4

DEPENDENCIES:
-------------
- dotenv: Load .env file with API keys
- logging: Python logging framework
- openai/groq/cerebras: LLM client libraries (imported dynamically when needed)

USED BY:
--------
- All agents in agents/ directory inherit from this class
"""

import os
import logging
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for all JARVIS agents with shared utilities"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # API keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.cerebras_api_key = os.getenv("CEREBRAS_API_KEY")
        
        if not any([self.openai_api_key, self.groq_api_key, self.cerebras_api_key]):
            self.logger.warning("No LLM API keys configured")
    
    def get_llm_client(self, provider: str = "openai"):
        """Get LLM client for specified provider"""
        try:
            if provider == "openai" and self.openai_api_key:
                from openai import OpenAI
                return OpenAI(api_key=self.openai_api_key)
            
            elif provider == "groq" and self.groq_api_key:
                from groq import Groq
                return Groq(api_key=self.groq_api_key)
            
            elif provider == "cerebras" and self.cerebras_api_key:
                from cerebras.cloud.sdk import Cerebras
                return Cerebras(api_key=self.cerebras_api_key)
            
            else:
                raise ValueError(f"Provider {provider} not available or API key missing")
                
        except ImportError as e:
            self.logger.error(f"Failed to import {provider} client: {e}")
            raise
    
    def log_agent_action(self, action: str, details: Dict[str, Any]):
        """Log agent action for monitoring"""
        self.logger.info(f"Agent Action: {action}", extra=details)
    
    def handle_error(self, error: Exception, context: str) -> Dict[str, Any]:
        """Standard error handling for agents"""
        self.logger.error(f"Agent error in {context}: {str(error)}")
        return {
            "success": False,
            "error": str(error),
            "context": context
        }
