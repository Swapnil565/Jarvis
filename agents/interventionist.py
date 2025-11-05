"""
=============================================================================
JARVIS 3.0 - INTERVENTIONIST AGENT (Agent 4: Proactive Recommendations) [DAY 4]
=============================================================================

PURPOSE:
--------
Agent 4 of the 4-agent system (TO BE IMPLEMENTED ON DAY 4). The "action layer"
that converts patterns and forecasts into actionable recommendations. Generates
warnings, suggestions, insights, and forecasts to help users avoid burnout and
optimize performance.

RESPONSIBILITY (When Implemented):
-----------------------------------
- Monitor real-time user state for intervention triggers
- Generate warnings when burnout risk detected (overtraining, energy debt)
- Create suggestions for optimal timing (energy above baseline → deep work)
- Deliver insights from detected patterns (workout → productivity boost)
- Prioritize interventions by urgency (critical warnings first)
- Learn from user feedback (rating, was_helpful) to improve recommendations
- Store interventions in interventions table via jarvis_db

DATA FLOW (Patterns + Forecasts → Intervention Logic → Recommendations):
-------------------------------------------------------------------------
INTERVENTION GENERATION FLOW (Day 4 Implementation):
1. Triggered by:
   - Real-time: After new event logged (check immediate state)
   - Scheduled: Celery job runs every 6 hours (Day 6)
   - Manual: POST /api/interventions/check
2. InterventionistAgent.check_intervention(user_id) called
3. Gather context:
   - Fetch last 7 days of events from jarvis_db
   - Get active patterns from PatternDetectorAgent
   - Get forecast from ForecasterAgent
   - Calculate current burnout score
4. Evaluate intervention rules (see RULE ENGINE below)
5. For each triggered rule:
   - Determine intervention type (warning/suggestion/insight/forecast)
   - Set urgency level (low/medium/high/critical)
   - Generate title + message (use LLM for natural language)
   - Add supporting data (metrics, pattern IDs, confidence scores)
   - Create Intervention object
   - Call jarvis_db.create_intervention()
6. Return list of new interventions
7. simple_main.py delivers to user (push notification, dashboard, email)

RULE ENGINE (Intervention Triggers):
------------------------------------
1. OVERTRAINING WARNING (Urgency: HIGH):
   - Trigger: 7+ consecutive workout days without rest
   - Message: "You've worked out 7 days straight. Rest day recommended."
   - Data: consecutive_days, fatigue_score, recovery_time_needed

2. BURNOUT FORECAST (Urgency: CRITICAL):
   - Trigger: Forecast shows >80% burnout probability within 3 days
   - Message: "Energy debt building. Predicted crash: Thursday."
   - Data: crash_date, probability, current_energy_debt

3. ENERGY DEBT WARNING (Urgency: HIGH):
   - Trigger: Energy debt score > 70
   - Message: "Energy debt at 75/100. Rest needed soon."
   - Data: debt_score, days_until_critical, recommended_rest_days

4. OPTIMAL TIMING SUGGESTION (Urgency: MEDIUM):
   - Trigger: Current energy > 20% above baseline
   - Message: "Energy at peak. Great time for deep work."
   - Data: current_energy, baseline, peak_duration_estimate

5. PATTERN INSIGHT (Urgency: LOW):
   - Trigger: New high-confidence pattern detected (confidence > 0.8)
   - Message: "You complete 2x more tasks after morning meditation."
   - Data: pattern_id, correlation, sample_size

6. MEDITATION REMINDER (Urgency: MEDIUM):
   - Trigger: 3+ days without meditation, stress increasing
   - Message: "Stress up 40% since last meditation. Time to reset?"
   - Data: days_since_meditation, stress_increase, avg_benefit

7. STREAK CELEBRATION (Urgency: LOW):
   - Trigger: 7+ day streak in any dimension
   - Message: "7-day meditation streak! Keep it up."
   - Data: streak_length, category, event_type

INTERVENTION PRIORITIZATION:
-----------------------------
1. Sort by urgency: CRITICAL > HIGH > MEDIUM > LOW
2. Within urgency: Sort by confidence score (forecast confidence, pattern strength)
3. Deduplicate: Don't send multiple similar interventions (e.g., 2 overtraining warnings)
4. Rate limit: Max 5 interventions per day (avoid notification fatigue)

LLM INTEGRATION (Natural Language Generation):
-----------------------------------------------
- Use GPT-4o-mini to generate personalized messages
- Input: Intervention type + data + user context
- Output: Natural, empathetic message (not robotic)
- Example:
  Input: {"type": "warning", "consecutive_workout_days": 8}
  Output: "Hey, I noticed you've been crushing it with 8 straight workout days! 💪 
           But your body's telling me it needs a break. How about a rest day tomorrow?"

LEARNING FROM FEEDBACK (Day 6+):
---------------------------------
- Track user_rating (1-5 stars) and was_helpful (boolean)
- Adjust intervention thresholds based on feedback:
  - If user rates "overtraining" warnings as unhelpful (rating < 3):
    → Increase threshold from 7 to 9 consecutive days
  - If "optimal timing" suggestions rated helpful (rating > 4):
    → Lower energy threshold from +20% to +15%
- Store feedback in interventions table for future ML training

EXAMPLE IMPLEMENTATION (Day 4):
--------------------------------
```python
async def check_intervention(self, user_id: int):
    interventions = []
    
    # Fetch context
    events = jarvis_db.get_events(user_id, days=7)
    forecast = forecaster.generate_forecast(user_id)
    
    # Rule 1: Overtraining check
    workout_events = [e for e in events if e['event_type'] == 'workout']
    consecutive_days = count_consecutive_days(workout_events)
    
    if consecutive_days >= 7:
        intervention = {
            "intervention_type": "warning",
            "urgency": "high",
            "title": "Overtraining Detected",
            "message": f"You've worked out {consecutive_days} days straight. Rest day recommended.",
            "data": {"consecutive_workout_days": consecutive_days}
        }
        jarvis_db.create_intervention(user_id, intervention)
        interventions.append(intervention)
    
    # Rule 2: Burnout forecast check
    if forecast['crash_prediction']['probability'] > 80:
        crash_date = forecast['crash_prediction']['predicted_date']
        intervention = {
            "intervention_type": "forecast",
            "urgency": "critical",
            "title": "Burnout Risk High",
            "message": f"Energy debt building. Predicted crash: {crash_date}.",
            "data": forecast['crash_prediction']
        }
        jarvis_db.create_intervention(user_id, intervention)
        interventions.append(intervention)
    
    return interventions
```

DEPENDENCIES (Day 4):
---------------------
- base_agent.py: LLM client for message generation
- simple_jarvis_db.py: Store interventions, fetch events
- agents/pattern_detector.py: Get detected patterns
- agents/forecaster.py: Get burnout predictions

INTEGRATION POINTS:
-------------------
- Receives from: PatternDetectorAgent (patterns), ForecasterAgent (forecasts)
- Feeds into: simple_main.py (deliver interventions to user)
- Called by: POST /api/interventions/check endpoint (Day 4)
- Scheduled by: Celery job (check every 6 hours on Day 6)

STATUS: ✅ IMPLEMENTED - DAY 4 COMPLETE
"""

from .base_agent import BaseAgent
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json


class InterventionistAgent(BaseAgent):
    """Agent 4: Interventionist - Proactive recommendations based on patterns and forecasts"""
    
    def __init__(self):
        super().__init__()
        self.logger.info("InterventionistAgent initialized")
        
        # Thresholds (can be adjusted based on user feedback)
        self.overtraining_threshold = 7  # consecutive workout days
        self.burnout_threshold = 70  # energy debt score
        self.meditation_gap_threshold = 3  # days without meditation
        self.energy_peak_threshold = 20  # % above baseline
        self.pattern_confidence_threshold = 0.8
        self.streak_celebration_threshold = 7  # days
        
    async def check_intervention(self, user_id: int, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Check if user needs any interventions based on current state.
        
        Args:
            user_id: User ID
            context: Optional context with events, forecast, patterns
            
        Returns:
            List of intervention dictionaries
        """
        from simple_jarvis_db import jarvis_db
        from agents.forecaster import forecaster
        from agents.pattern_detector import pattern_detector
        
        interventions = []
        
        try:
            # Gather context if not provided
            if context is None:
                context = {}
            
            if 'events' not in context:
                context['events'] = jarvis_db.get_events(user_id, limit=30)
            
            if 'forecast' not in context:
                try:
                    context['forecast'] = await forecaster.generate_forecast(user_id, days=7)
                except Exception as e:
                    self.logger.warning(f"Could not get forecast: {e}")
                    context['forecast'] = None
            
            if 'patterns' not in context:
                try:
                    context['patterns'] = await pattern_detector.detect_patterns(user_id)
                except Exception as e:
                    self.logger.warning(f"Could not get patterns: {e}")
                    context['patterns'] = {}
            
            # Run all intervention checks
            interventions.extend(await self._detect_overtraining(user_id, context['events']))
            interventions.extend(await self._detect_burnout_risk(user_id, context))
            interventions.extend(await self._detect_optimal_timing(user_id, context['events']))
            interventions.extend(await self._detect_meditation_gap(user_id, context['events']))
            interventions.extend(await self._detect_pattern_insight(user_id, context['patterns']))
            interventions.extend(await self._detect_streak(user_id, context['events']))
            
            # Prioritize and deduplicate
            interventions = self._prioritize_interventions(interventions)
            
            # Store in database
            for intervention in interventions:
                try:
                    jarvis_db.create_intervention(
                        user_id=user_id,
                        intervention_type=intervention['intervention_type'],
                        urgency=intervention['urgency'],
                        title=intervention['title'],
                        message=intervention['message'],
                        data=intervention.get('data', {})
                    )
                except Exception as e:
                    self.logger.error(f"Failed to store intervention: {e}")
            
            return interventions
            
        except Exception as e:
            self.logger.error(f"Intervention check failed for user {user_id}: {e}")
            return []
    
    async def _detect_overtraining(self, user_id: int, events: List[Dict]) -> List[Dict[str, Any]]:
        """Detect 7+ consecutive workout days without rest"""
        workout_events = [e for e in events if e.get('event_type') == 'workout']
        
        if not workout_events:
            return []
        
        # Sort by timestamp
        workout_events.sort(key=lambda x: x.get('timestamp', ''))
        
        # Count consecutive days
        consecutive_days = 1
        last_date = None
        
        for event in reversed(workout_events):
            event_date = event.get('timestamp', '')[:10]
            if last_date is None:
                last_date = event_date
                continue
            
            # Check if this is the day before
            last_dt = datetime.fromisoformat(last_date)
            event_dt = datetime.fromisoformat(event_date)
            
            if (last_dt - event_dt).days == 1:
                consecutive_days += 1
                last_date = event_date
            else:
                break
        
        if consecutive_days >= self.overtraining_threshold:
            message = await self._generate_intervention_message(
                'overtraining',
                {'consecutive_days': consecutive_days}
            )
            
            return [{
                'intervention_type': 'warning',
                'urgency': 'high',
                'title': 'Overtraining Detected',
                'message': message,
                'data': {
                    'consecutive_workout_days': consecutive_days,
                    'recovery_time_needed': '2-3 days'
                }
            }]
        
        return []
    
    async def _detect_burnout_risk(self, user_id: int, context: Dict) -> List[Dict[str, Any]]:
        """Detect high burnout risk from forecast"""
        forecast = context.get('forecast')
        if not forecast:
            return []
        
        burnout_score = forecast.get('burnout_score', 0)
        
        if burnout_score >= self.burnout_threshold:
            urgency = 'critical' if burnout_score >= 80 else 'high'
            
            message = await self._generate_intervention_message(
                'burnout',
                {'burnout_score': burnout_score}
            )
            
            return [{
                'intervention_type': 'forecast',
                'urgency': urgency,
                'title': 'Burnout Risk High',
                'message': message,
                'data': {
                    'burnout_score': burnout_score,
                    'recommended_action': 'Schedule rest day soon'
                }
            }]
        
        return []
    
    async def _detect_optimal_timing(self, user_id: int, events: List[Dict]) -> List[Dict[str, Any]]:
        """Detect when energy is above baseline (good time for deep work)"""
        # Get recent energy scores (last 3 days)
        recent_events = [e for e in events if self._is_within_days(e, 3)]
        
        if len(recent_events) < 3:
            return []
        
        # Calculate energy from feelings
        energy_scores = []
        for event in recent_events:
            feeling = event.get('feeling', '').lower()
            if feeling in ['great', 'amazing', 'energized']:
                energy_scores.append(3)
            elif feeling in ['good', 'okay', 'fine']:
                energy_scores.append(2)
            elif feeling in ['tired', 'exhausted', 'drained']:
                energy_scores.append(1)
        
        if not energy_scores:
            return []
        
        current_energy = energy_scores[-1] if energy_scores else 2
        baseline = sum(energy_scores) / len(energy_scores)
        
        # Check if 20% above baseline
        if current_energy > baseline * (1 + self.energy_peak_threshold / 100):
            message = await self._generate_intervention_message(
                'optimal_timing',
                {'current_energy': current_energy, 'baseline': baseline}
            )
            
            return [{
                'intervention_type': 'suggestion',
                'urgency': 'medium',
                'title': 'Energy at Peak',
                'message': message,
                'data': {
                    'current_energy_level': current_energy,
                    'baseline_energy': baseline,
                    'suggested_activity': 'deep work or challenging tasks'
                }
            }]
        
        return []
    
    async def _detect_meditation_gap(self, user_id: int, events: List[Dict]) -> List[Dict[str, Any]]:
        """Detect 3+ days without meditation"""
        meditation_events = [e for e in events if e.get('event_type') == 'meditation']
        
        if not meditation_events:
            # Check if user has ever meditated
            if len(events) > 10:  # Only suggest if user has some history
                return []
            return []
        
        # Get last meditation date
        meditation_events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        last_meditation = meditation_events[0].get('timestamp', '')
        
        if not last_meditation:
            return []
        
        last_date = datetime.fromisoformat(last_meditation[:19])
        days_since = (datetime.utcnow() - last_date).days
        
        if days_since >= self.meditation_gap_threshold:
            message = await self._generate_intervention_message(
                'meditation_gap',
                {'days_since': days_since}
            )
            
            return [{
                'intervention_type': 'suggestion',
                'urgency': 'medium',
                'title': 'Meditation Reminder',
                'message': message,
                'data': {
                    'days_since_meditation': days_since,
                    'suggested_duration': '10 minutes'
                }
            }]
        
        return []
    
    async def _detect_pattern_insight(self, user_id: int, patterns: Dict) -> List[Dict[str, Any]]:
        """Detect new high-confidence patterns"""
        interventions = []
        
        detected_patterns = patterns.get('patterns', [])
        
        for pattern in detected_patterns:
            confidence = pattern.get('confidence', 0)
            
            if confidence >= self.pattern_confidence_threshold:
                message = await self._generate_intervention_message(
                    'pattern_insight',
                    {'pattern': pattern}
                )
                
                interventions.append({
                    'intervention_type': 'insight',
                    'urgency': 'low',
                    'title': 'Pattern Detected',
                    'message': message,
                    'data': {
                        'pattern_type': pattern.get('pattern_type', 'unknown'),
                        'confidence': confidence,
                        'description': pattern.get('description', '')
                    }
                })
        
        return interventions[:2]  # Limit to 2 insights to avoid overwhelming
    
    async def _detect_streak(self, user_id: int, events: List[Dict]) -> List[Dict[str, Any]]:
        """Detect and celebrate 7+ day streaks"""
        # Group events by type
        event_types = {}
        for event in events:
            event_type = event.get('event_type')
            if event_type:
                if event_type not in event_types:
                    event_types[event_type] = []
                event_types[event_type].append(event)
        
        interventions = []
        
        for event_type, type_events in event_types.items():
            # Check for consecutive days
            type_events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            consecutive_days = 1
            last_date = None
            
            for event in type_events:
                event_date = event.get('timestamp', '')[:10]
                if last_date is None:
                    last_date = event_date
                    continue
                
                last_dt = datetime.fromisoformat(last_date)
                event_dt = datetime.fromisoformat(event_date)
                
                if (last_dt - event_dt).days == 1:
                    consecutive_days += 1
                    last_date = event_date
                else:
                    break
            
            if consecutive_days >= self.streak_celebration_threshold:
                message = await self._generate_intervention_message(
                    'streak',
                    {'event_type': event_type, 'days': consecutive_days}
                )
                
                interventions.append({
                    'intervention_type': 'insight',
                    'urgency': 'low',
                    'title': f'{consecutive_days}-Day Streak!',
                    'message': message,
                    'data': {
                        'streak_type': event_type,
                        'streak_length': consecutive_days
                    }
                })
        
        return interventions[:1]  # Only celebrate one streak at a time
    
    async def _generate_intervention_message(self, message_type: str, data: Dict) -> str:
        """Generate natural language intervention message using GPT-4o-mini"""
        
        # Fallback messages (used if LLM fails)
        fallback_messages = {
            'overtraining': f"You've worked out {data.get('consecutive_days', 7)} days straight! 💪 Your body needs rest to recover and build strength. Consider a rest day tomorrow.",
            'burnout': f"Energy debt is at {data.get('burnout_score', 70)}/100. You're running on fumes. Time to prioritize rest and recovery before you crash.",
            'optimal_timing': f"Your energy is at peak levels right now! ⚡ Perfect time to tackle that challenging task or deep work session.",
            'meditation_gap': f"It's been {data.get('days_since', 3)} days since your last meditation. Even 10 minutes can help reset your focus and reduce stress.",
            'pattern_insight': f"I noticed a pattern: {data.get('pattern', {}).get('description', 'interesting correlation detected')}",
            'streak': f"🎉 {data.get('days', 7)}-day {data.get('event_type', 'activity')} streak! You're building amazing habits. Keep it up!"
        }
        
        # Try to generate with LLM for more personalized message
        try:
            system_prompt = """You are JARVIS, an empathetic AI wellness copilot. Generate a brief, supportive intervention message based on the user's data. 
            Be warm, specific, and actionable. Use emojis sparingly. Keep it under 60 words."""
            
            user_prompt = f"Generate an intervention message for: {message_type}\nData: {json.dumps(data)}"
            
            response = await self.llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            message = response.choices[0].message.content.strip()
            return message if message else fallback_messages.get(message_type, "Heads up: something worth noting.")
            
        except Exception as e:
            self.logger.warning(f"LLM message generation failed, using fallback: {e}")
            return fallback_messages.get(message_type, "Heads up: something worth noting.")
    
    def _prioritize_interventions(self, interventions: List[Dict]) -> List[Dict]:
        """Prioritize interventions by urgency and deduplicate"""
        if not interventions:
            return []
        
        # Urgency priority map
        urgency_priority = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        
        # Sort by urgency
        interventions.sort(key=lambda x: urgency_priority.get(x['urgency'], 99))
        
        # Deduplicate by intervention type (keep highest urgency)
        seen_types = set()
        unique_interventions = []
        
        for intervention in interventions:
            int_type = intervention['intervention_type']
            if int_type not in seen_types:
                seen_types.add(int_type)
                unique_interventions.append(intervention)
        
        # Limit to 5 interventions to avoid fatigue
        return unique_interventions[:5]
    
    def _is_within_days(self, event: Dict, days: int) -> bool:
        """Check if event is within last N days"""
        timestamp = event.get('timestamp', '')
        if not timestamp:
            return False
        
        try:
            event_date = datetime.fromisoformat(timestamp[:19])
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            return event_date >= cutoff_date
        except:
            return False


# Global instance
interventionist = InterventionistAgent()
