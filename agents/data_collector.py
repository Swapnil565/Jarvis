"""
=============================================================================
JARVIS 3.0 - DATA COLLECTOR AGENT (Agent 1: Natural Language Parser)
=============================================================================

PURPOSE:
--------
Agent 1 of the 4-agent system. Converts natural language input into structured
event data using LLM (GPT-4o-mini). This is the ENTRY POINT for all user inputs
before they're stored in the database.

RESPONSIBILITY:
---------------
- Parse casual user text (e.g., "ran 5k today felt amazing") into structured JSON
- Classify events into categories: physical, mental, spiritual
- Extract event types: workout, task, meditation, mood, recovery
- Validate parsed data with Pydantic schemas
- Extract metadata: intensity, duration, priority, completion status
- Handle voice input (after Whisper transcription)

DATA FLOW (Natural Language → Structured Event):
-------------------------------------------------
PARSE TEXT FLOW:
1. User sends POST /api/events/parse with {"text": "upper body heavy felt great"}
2. simple_main.py calls data_collector.parse(text)
3. This agent builds system prompt with examples and schemas
4. Send to GPT-4o-mini with response_format=json_object (forces JSON output)
5. LLM returns structured JSON:
   {
     "category": "physical",
     "event_type": "workout",
     "feeling": "great",
     "data": {
       "workout_type": "upper_body",
       "intensity": "heavy",
       "duration": null
     }
   }
6. Validate 'data' field with Pydantic schema (WorkoutData/TaskData/MeditationData)
7. Return parsed dict to simple_main.py
8. simple_main.py calls jarvis_db.create_event(parsed_data)
9. Event stored in SQLite database

VOICE INPUT FLOW:
1. User sends POST /api/events/voice with audio file
2. simple_main.py transcribes audio with OpenAI Whisper API → text
3. Call data_collector.parse(transcribed_text)
4. Same flow as above from step 3

QUICK-TAP FLOW (No LLM):
1. User sends POST /api/events/quick with category + event_type only
2. simple_main.py bypasses DataCollectorAgent (instant response)
3. Direct insertion to database without parsing

LLM OPTIMIZATION:
-----------------
- Model: GPT-4o-mini (200x cheaper than GPT-4, $0.15 per 1M input tokens)
- Temperature: 0.0 (deterministic, consistent parsing)
- Max tokens: 200 (short responses, cost-efficient)
- response_format: json_object (guaranteed valid JSON)
- Typical cost: <$0.00002 per parse (150 tokens input + 50 tokens output)

PYDANTIC SCHEMAS:
-----------------
WorkoutData: workout_type, intensity, duration
TaskData: title, completed, priority
MeditationData: duration, method

These ensure type safety and validation before database insertion.

DEPENDENCIES:
-------------
- base_agent.py: LLM client initialization, error handling
- openai: GPT-4o-mini API client
- pydantic: Data validation schemas
- json: Parse LLM response

USED BY:
--------
- simple_main.py: POST /api/events/parse, POST /api/events/voice endpoints
"""

import json
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from .base_agent import BaseAgent

# Pydantic schemas for structured data validation
class WorkoutData(BaseModel):
    """Physical dimension - workout data"""
    workout_type: str = Field(..., description="Type: upper_body, lower_body, full_body, cardio")
    intensity: Optional[str] = Field(None, description="Intensity: light, moderate, heavy")
    duration: Optional[int] = Field(None, description="Duration in minutes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "workout_type": "upper_body",
                "intensity": "heavy",
                "duration": 60
            }
        }

class TaskData(BaseModel):
    """Mental dimension - task/work data"""
    title: str = Field(..., description="Task title or description")
    completed: bool = Field(True, description="Is task completed?")
    priority: Optional[str] = Field(None, description="Priority: low, medium, high")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "client proposal",
                "completed": True,
                "priority": "high"
            }
        }

class MeditationData(BaseModel):
    """Spiritual dimension - meditation/recovery data"""
    duration: int = Field(..., description="Duration in minutes")
    method: Optional[str] = Field(None, description="Method: breathing, guided, mindfulness")
    
    class Config:
        json_schema_extra = {
            "example": {
                "duration": 10,
                "method": "breathing"
            }
        }


class DataCollectorAgent(BaseAgent):
    """
    Agent 1: Data Collector
    Converts raw user inputs (voice, text) into structured event data
    """
    
    def __init__(self):
        super().__init__()
        self.system_prompt = """You are a data parser for JARVIS, an AI copilot that tracks physical, mental, and spiritual activities.

Your job: Parse natural language input into structured JSON.

**Output Format:**
{
    "dimension": "physical" | "mental" | "spiritual",
    "type": "workout" | "task" | "meditation",
    "data": {...},
    "feeling": "energized" | "tired" | "calm" | "stressed" | "focused" | null
}

**Rules:**
1. Return ONLY valid JSON (no explanations)
2. Dimension detection:
   - "workout", "gym", "training", "exercise" → physical
   - "task", "work", "finished", "completed", "deadline" → mental
   - "meditation", "meditated", "breathwork", "mindfulness" → spiritual

3. Extract specific data based on type:
   - Physical: workout_type (upper_body/lower_body/full_body/cardio), intensity (light/moderate/heavy), duration
   - Mental: title, completed (true/false), priority (low/medium/high)
   - Spiritual: duration, method

4. Extract feeling if mentioned (great, tired, exhausted, calm, stressed, focused, etc.)
5. If you can't parse, return: {"error": "Could not parse input"}

**Examples:**
Input: "upper body heavy felt great"
Output: {"dimension": "physical", "type": "workout", "data": {"workout_type": "upper_body", "intensity": "heavy"}, "feeling": "great"}

Input: "finished client proposal high priority"
Output: {"dimension": "mental", "type": "task", "data": {"title": "client proposal", "completed": true, "priority": "high"}}

Input: "meditated 10 minutes breathing exercises"
Output: {"dimension": "spiritual", "type": "meditation", "data": {"duration": 10, "method": "breathing exercises"}}

Input: "leg day 45 minutes felt exhausted"
Output: {"dimension": "physical", "type": "workout", "data": {"workout_type": "lower_body", "duration": 45}, "feeling": "exhausted"}

Input: "3 tasks done today feeling productive"
Output: {"dimension": "mental", "type": "task", "data": {"title": "3 tasks", "completed": true}, "feeling": "focused"}
"""
    
    async def parse(self, raw_input: str) -> Dict[str, Any]:
        """
        Parse raw natural language input into structured event data
        
        Args:
            raw_input: Natural language string (e.g., "upper body heavy felt great")
            
        Returns:
            Structured event data or error dict
        """
        try:
            import os
            import google.generativeai as genai
            
            # Configure Google Gemini API
            gemini_key = os.getenv("GEMINI_API_KEY")
            if not gemini_key:
                raise ValueError("GEMINI_API_KEY not found in environment")
            
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel(
                'models/gemini-2.5-flash',
                safety_settings={
                    'HARASSMENT': 'block_none',
                    'HATE_SPEECH': 'block_none',
                    'SEXUALLY_EXPLICIT': 'block_none',
                    'DANGEROUS_CONTENT': 'block_none'
                }
            )  
            
            # Construct prompt
            full_prompt = f"{self.system_prompt}\n\nUser input: {raw_input}\n\nYour response (JSON only):"
            
            # Generate response
            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    max_output_tokens=200
                )
            )
            
            # Check if response was blocked
            if not response.candidates or not response.text:
                self.logger.warning(f"Response blocked: {response.prompt_feedback}")
                # Return a fallback error
                return {"error": "Response blocked by safety filters"}
            
            # Extract text from response
            result_text = response.text.strip()
            
            # Extract JSON if wrapped in markdown
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            
            # Check for parsing error
            if "error" in result:
                self.log_agent_action("parse_failed", {"input": raw_input, "error": result["error"]})
                return result
            
            # Validate with Pydantic based on dimension
            if result.get('dimension') == 'physical':
                result['data'] = WorkoutData(**result['data']).model_dump()
            elif result.get('dimension') == 'mental':
                result['data'] = TaskData(**result['data']).model_dump()
            elif result.get('dimension') == 'spiritual':
                result['data'] = MeditationData(**result['data']).model_dump()
            
            self.log_agent_action("parse_success", {
                "input_length": len(raw_input),
                "dimension": result.get('dimension'),
                "type": result.get('type')
            })
            
            return result
            
        except json.JSONDecodeError as e:
            return self.handle_error(e, "JSON parsing failed")
        
        except Exception as e:
            return self.handle_error(e, "Data collection failed")
    
    def parse_sync(self, raw_input: str) -> Dict[str, Any]:
        """Synchronous version of parse for non-async contexts"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.parse(raw_input))


data_collector = DataCollectorAgent()
