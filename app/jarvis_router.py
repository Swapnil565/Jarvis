"""
JARVIS Simple LLM Router - Minimal Viable Architecture
Single file solution for quick deployment and easy debugging.

Author: JARVIS Team
Date: September 2025
"""

import os
import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dotenv import load_dotenv

import httpx
from cerebras.cloud.sdk import Cerebras

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """Simple task categorization"""
    CONTEXT_SEARCH = "context_search"    # Complex reasoning, document QA
    GENERAL_TASK = "general_task"        # Quick responses, simple questions
    EMERGENCY = "emergency"              # When all else fails


class Provider(str, Enum):
    """Available LLM providers"""
    A4F = "a4f"
    GROK = "grok" 
    OPENROUTER = "openrouter"
    CEREBRAS = "cerebras"


class RateLimitTracker:
    """Simple in-memory rate limiting - resets every hour"""
    
    def __init__(self):
        self.limits = {
            Provider.A4F: {"count": 0, "reset_hour": self._current_hour(), "max": 200},
            Provider.GROK: {"count": 0, "reset_hour": self._current_hour(), "max": 100},
            Provider.OPENROUTER: {"count": 0, "reset_hour": self._current_hour(), "max": 50},
            Provider.CEREBRAS: {"count": 0, "reset_hour": self._current_hour(), "max": 1000},
        }
    
    def _current_hour(self) -> int:
        """Get current hour for rate limit reset"""
        return datetime.now().hour
    
    def is_available(self, provider: Provider) -> bool:
        """Check if provider is under rate limit"""
        current_hour = self._current_hour()
        limit_info = self.limits[provider]
        
        # Reset counter if new hour
        if current_hour != limit_info["reset_hour"]:
            limit_info["count"] = 0
            limit_info["reset_hour"] = current_hour
        
        return limit_info["count"] < limit_info["max"]
    
    def record_usage(self, provider: Provider):
        """Record API call for rate limiting"""
        self.limits[provider]["count"] += 1
        logger.info(f"Rate limit: {provider} used {self.limits[provider]['count']}/{self.limits[provider]['max']}")


class PromptFormatter:
    """Simple prompt templates for different tasks"""
    
    @staticmethod
    def format_for_reasoning(query: str, context: str = "") -> List[Dict[str, str]]:
        """Format prompt for complex reasoning tasks (Deepseek, Llama)"""
        system_prompt = """You are JARVIS, a digital memory assistant with advanced context resurrection capabilities. 
Find and synthesize information from the user's context with precision and clarity."""
        
        user_prompt = f"""Context: {context}

Question: {query}

Provide a clear, comprehensive response based on the available context."""
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    
    @staticmethod
    def format_for_quick_task(query: str, context: str = "") -> List[Dict[str, str]]:
        """Format prompt for quick tasks (Gemini, GPT)"""
        system_prompt = "You're JARVIS. Be helpful, concise, and accurate."
        
        user_prompt = f"Help with: {query}"
        if context:
            user_prompt += f"\n\nContext: {context}"
        
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]


class SimpleRouter:
    """Main LLM router - keeps it simple and focused"""
    
    def __init__(self):
        self.rate_tracker = RateLimitTracker()
        self.formatter = PromptFormatter()
        self.session_cache = {}  # Simple in-memory user sessions
        
        # API clients
        self.cerebras_client = None
        self._init_clients()
    
    def _init_clients(self):
        """Initialize API clients"""
        try:
            cerebras_key = os.getenv("CEREBRAS_API_KEY")
            if cerebras_key:
                self.cerebras_client = Cerebras(api_key=cerebras_key)
                logger.info("Cerebras client initialized")
            else:
                logger.warning("CEREBRAS_API_KEY not found")
                
            # Store API keys for other providers
            self.api_keys = {
                "gemini": os.getenv("GEMINI_API_KEY"),
                "groq": os.getenv("GROQ_API_KEY"),
                "a4f": os.getenv("A4F_API_KEY"),
                "openrouter": os.getenv("OPENROUTER_API_KEY")
            }
            
            logger.info(f"Initialized API keys for: {[k for k, v in self.api_keys.items() if v]}")
            
        except Exception as e:
            logger.error(f"Failed to initialize clients: {e}")
    
    def get_models_for_task(self, task_type: TaskType) -> List[Dict[str, str]]:
        """Get ordered list of models to try for each task type"""
        
        if task_type == TaskType.CONTEXT_SEARCH:
            return [
                {"provider": Provider.A4F, "model": "provider-3/deepseek-v3"},
                {"provider": Provider.GROK, "model": "llama-3.3-70b-versatile"},
                {"provider": Provider.OPENROUTER, "model": "deepseek/deepseek-chat-v3-0324:free"},
                {"provider": Provider.CEREBRAS, "model": "qwen-3-235b-a22b-instruct-2507"}
            ]
        
        elif task_type == TaskType.GENERAL_TASK:
            return [
                {"provider": Provider.A4F, "model": "provider-3/gemini-2.0-flash"},
                {"provider": Provider.GROK, "model": "openai/gpt-oss-120b"},
                {"provider": Provider.OPENROUTER, "model": "google/gemini-2.0-flash-exp:free"},
                {"provider": Provider.CEREBRAS, "model": "qwen-3-235b-a22b-instruct-2507"}
            ]
        
        else:  # EMERGENCY
            return [
                {"provider": Provider.OPENROUTER, "model": "deepseek/deepseek-chat-v3-0324:free"},
                {"provider": Provider.CEREBRAS, "model": "qwen-3-235b-a22b-instruct-2507"}
            ]
    
    def classify_task(self, query: str) -> TaskType:
        """Simple task classification"""
        reasoning_keywords = [
            "analyze", "compare", "explain why", "what caused", "how does",
            "relationship between", "summarize", "find information about"
        ]
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in reasoning_keywords):
            return TaskType.CONTEXT_SEARCH
        
        return TaskType.GENERAL_TASK
    
    async def call_cerebras(self, model: str, messages: List[Dict[str, str]]) -> Optional[str]:
        """Call Cerebras API"""
        if not self.cerebras_client:
            return None
        
        try:
            stream = self.cerebras_client.chat.completions.create(
                messages=messages,
                model=model,
                stream=True,
                max_completion_tokens=20000,
                temperature=0.7,
                top_p=0.8
            )
            
            response_text = ""
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    response_text += chunk.choices[0].delta.content
            
            return response_text.strip()
            
        except Exception as e:
            logger.error(f"Cerebras API error: {e}")
            return None
    
    async def call_a4f(self, model: str, messages: List[Dict[str, str]]) -> Optional[str]:
        """Call A4F API"""
        if not self.api_keys.get("a4f"):
            logger.error("A4F API key not found")
            return None
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.a4f.co/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_keys['a4f']}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": 2000,
                        "temperature": 0.7,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    logger.error(f"A4F API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"A4F API error: {e}")
            return None
    
    async def call_grok(self, model: str, messages: List[Dict[str, str]]) -> Optional[str]:
        """Call Groq API"""
        if not self.api_keys.get("groq"):
            logger.error("Groq API key not found")
            return None
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_keys['groq']}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": 2000,
                        "temperature": 0.7,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    logger.error(f"Groq API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return None
    
    async def call_openrouter(self, model: str, messages: List[Dict[str, str]]) -> Optional[str]:
        """Call OpenRouter API"""
        if not self.api_keys.get("openrouter"):
            logger.error("OpenRouter API key not found")
            return None
            
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_keys['openrouter']}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://jarvis-ai.dev",
                        "X-Title": "JARVIS AI Assistant"
                    },
                    json={
                        "model": model,
                        "messages": messages,
                        "max_tokens": 2000,
                        "temperature": 0.7,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            return None
    
    async def call_model(self, provider: Provider, model: str, messages: List[Dict[str, str]]) -> Optional[str]:
        """Route API call to appropriate provider"""
        
        if provider == Provider.CEREBRAS:
            return await self.call_cerebras(model, messages)
        elif provider == Provider.A4F:
            return await self.call_a4f(model, messages)
        elif provider == Provider.GROK:
            return await self.call_grok(model, messages)
        elif provider == Provider.OPENROUTER:
            return await self.call_openrouter(model, messages)
        
        return None
    
    async def get_response(self, query: str, context: str = "", user_id: str = "default") -> Dict[str, Any]:
        """Main entry point - get response from best available model"""
        start_time = time.time()
        
        # Classify the task
        task_type = self.classify_task(query)
        logger.info(f"Task classified as: {task_type}")
        
        # Get ordered models to try
        models_to_try = self.get_models_for_task(task_type)
        
        # Format prompt based on task type
        if task_type == TaskType.CONTEXT_SEARCH:
            messages = self.formatter.format_for_reasoning(query, context)
        else:
            messages = self.formatter.format_for_quick_task(query, context)
        
        # Try each model until one works
        for model_config in models_to_try:
            provider = model_config["provider"]
            model = model_config["model"]
            
            # Check rate limits
            if not self.rate_tracker.is_available(provider):
                logger.warning(f"Rate limit exceeded for {provider}")
                continue
            
            try:
                # Attempt API call
                response = await self.call_model(provider, model, messages)
                
                if response:
                    # Success!
                    self.rate_tracker.record_usage(provider)
                    processing_time = time.time() - start_time
                    
                    # Cache this interaction
                    self.session_cache[user_id] = {
                        "last_query": query,
                        "last_response": response,
                        "timestamp": datetime.now(),
                        "context": context
                    }
                    
                    return {
                        "success": True,
                        "response": response,
                        "model_used": f"{provider}/{model}",
                        "task_type": task_type,
                        "processing_time": processing_time,
                        "timestamp": datetime.now().isoformat()
                    }
            
            except Exception as e:
                logger.error(f"Error with {provider}/{model}: {e}")
                continue
        
        # All models failed
        processing_time = time.time() - start_time
        return {
            "success": False,
            "response": "JARVIS is at capacity. All AI providers are currently unavailable. Please try again in an hour.",
            "model_used": "none",
            "task_type": task_type,
            "processing_time": processing_time,
            "timestamp": datetime.now().isoformat(),
            "error": "All providers exhausted"
        }
    
    def get_user_context(self, user_id: str) -> str:
        """Get simple user context from session cache"""
        if user_id in self.session_cache:
            session = self.session_cache[user_id]
            return f"Previous query: {session.get('last_query', 'None')}"
        return ""
    
    def get_status(self) -> Dict[str, Any]:
        """Get router status for debugging"""
        return {
            "rate_limits": self.rate_tracker.limits,
            "active_sessions": len(self.session_cache),
            "cerebras_available": self.cerebras_client is not None,
            "current_hour": self.rate_tracker._current_hour()
        }


# Global router instance
router = SimpleRouter()


# FastAPI Integration Functions
async def process_jarvis_query(query: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Main function to integrate with JARVIS system"""
    
    user_id = str(user_context.get("user_id", "anonymous")) if user_context else "anonymous"
    
    # Build context string
    context_parts = []
    
    if user_context:
        if user_context.get("user_email"):
            context_parts.append(f"User: {user_context['user_email']}")
        
        if user_context.get("authenticated"):
            context_parts.append("Authenticated user with full access")
        
        # Add any additional context
        additional_context = user_context.get("context", {})
        if additional_context:
            context_parts.append(f"Additional context: {additional_context}")
    
    # Add previous session context
    session_context = router.get_user_context(user_id)
    if session_context:
        context_parts.append(session_context)
    
    context_string = " | ".join(context_parts)
    
    # Get response from router
    result = await router.get_response(query, context_string, user_id)
    
    return result


# Simple test function
async def test_router():
    """Test the router with a simple query"""
    print("🧪 Testing JARVIS Simple LLM Router...")
    
    test_queries = [
        "What is artificial intelligence?",
        "Analyze the relationship between machine learning and AI",
        "How does context resurrection work?"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        result = await process_jarvis_query(query, {"user_id": "test_user", "authenticated": True})
        
        print(f"✅ Success: {result['success']}")
        print(f"🤖 Model: {result['model_used']}")
        print(f"⏱️ Time: {result['processing_time']:.2f}s")
        print(f"📄 Response: {result['response'][:200]}...")
        print("-" * 50)
    
    # Show status
    status = router.get_status()
    print(f"\n📊 Router Status:")
    print(json.dumps(status, indent=2, default=str))


if __name__ == "__main__":
    # Set up Cerebras API key for testing
    os.environ["CEREBRAS_API_KEY"] = "csk-44c3n6nehvh63vmw4r3n8hmkr5hx6pcdrdtt6fnem3cetpeh"
    
    # Run test
    asyncio.run(test_router())