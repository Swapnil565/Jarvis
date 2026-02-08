"""
JARVIS 3.0 - FORECASTER AGENT
Predicts future capacity, energy, burnout risk, and optimal timing
"""

from .base_agent import BaseAgent
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
import json
import statistics


class ForecasterAgent(BaseAgent):
    """
    The Crystal Ball Agent - Predicts future capacity and burnout risk
    
    Core Functions:
    1. calculate_energy_debt() - Current burnout score (0-100)
    2. generate_7day_forecast() - Predict capacity/demand for next 7 days
    3. predict_crash_risk() - When will burnout occur
    """
    
    def __init__(self, db=None):
        super().__init__()
        self.db = db
        self.logger.info("ForecasterAgent initialized")
        
        # Thresholds
        self.energy_debt_threshold = 80
        self.crash_risk_threshold = 70
        self.high_capacity_threshold = 7.0
        self.low_capacity_threshold = 4.0
        
    def process(self, data):
        """Main entry point for forecasting"""
        user_id = data.get('user_id')
        if not user_id:
            return {"error": "Missing user_id"}
        
        energy_debt = self.calculate_energy_debt(user_id)
        forecast = self.generate_7day_forecast(user_id)
        crash_risk = self.predict_crash_risk(user_id)
        
        return {
            'energy_debt': energy_debt,
            'forecast': forecast,
            'crash_prediction': crash_risk,
            'recommendations': self._generate_recommendations(energy_debt, forecast, crash_risk)
        }
    
    # ==================== CORE FORECASTING METHODS ====================
    
    def calculate_energy_debt(self, user_id):
        """
        Calculate current energy debt (burnout score 0-100)
        
        Formula:
        - CNS Fatigue: consecutive_workout_days × intensity
        - Work Pressure: study intensity × workload
        - Recovery Deficit: days_without_meditation × stress
        - Sleep Debt: sleep deficit hours × multiplier
        
        Returns: 0 (fully recovered) to 100 (burnout imminent)
        """
        if not self.db:
            return 0.0
        
        # Get last 14 days of events
        events = self._get_recent_events(user_id, days=14)
        if not events:
            return 0.0
        
        # 1. CNS Fatigue (consecutive high-intensity days)
        cns_fatigue = self._calculate_cns_fatigue(events)
        
        # 2. Work Pressure (study/work intensity)
        work_pressure = self._calculate_work_pressure(events)
        
        # 3. Recovery Deficit (lack of recovery activities)
        recovery_deficit = self._calculate_recovery_deficit(events)
        
        # 4. Sleep Debt (insufficient sleep)
        sleep_debt = self._calculate_sleep_debt(events)
        
        # Total energy debt (weighted sum)
        total_debt = (
            cns_fatigue * 0.25 +
            work_pressure * 0.30 +
            recovery_deficit * 0.25 +
            sleep_debt * 0.20
        )
        
        return min(100, max(0, round(total_debt, 2)))
    
    def generate_7day_forecast(self, user_id):
        """
        Generate 7-day forecast with capacity, demand, and category
        
        Returns: List of 7 daily forecasts with:
        - date: ISO date string
        - capacity: "high" | "medium" | "low"
        - demand: "high" | "medium" | "low"
        - category: 1-5 (1=optimal, 5=crash imminent)
        - details: Additional metrics
        """
        if not self.db:
            return []
        
        # Get historical data
        events = self._get_recent_events(user_id, days=30)
        insights = self._get_active_insights(user_id)
        
        if not events:
            return self._generate_default_forecast()
        
        # Calculate baselines from historical data
        baselines = self._calculate_baselines(events)
        
        # Predict next 7 days
        forecast = []
        today = date.today()
        
        for day_offset in range(1, 8):
            forecast_date = today + timedelta(days=day_offset)
            
            # Predict capacity for this day
            capacity_score = self._predict_capacity(events, insights, baselines, day_offset)
            capacity_level = self._score_to_level(capacity_score, self.high_capacity_threshold, self.low_capacity_threshold)
            
            # Predict demand for this day
            demand_score = self._predict_demand(events, forecast_date, day_offset)
            demand_level = self._score_to_level(demand_score, 7.0, 4.0)
            
            # Calculate category (1-5)
            category = self._calculate_category(capacity_level, demand_level)
            
            forecast.append({
                'date': forecast_date.isoformat(),
                'capacity': capacity_level,
                'demand': demand_level,
                'category': category,
                'details': {
                    'capacity_score': round(capacity_score, 2),
                    'demand_score': round(demand_score, 2),
                    'predicted_energy': round(capacity_score, 1),
                    'predicted_workload': round(demand_score, 1)
                }
            })
        
        return forecast
    
    def predict_crash_risk(self, user_id):
        """
        Predict burnout crash risk
        
        Returns: {
            risk_level: "low" | "medium" | "high" | "critical"
            probability: 0-100
            predicted_date: ISO date or None
            days_until_crash: int or None
            severity: "low" | "medium" | "high"
            confidence: 0-1
        }
        """
        if not self.db:
            return self._default_crash_risk()
        
        energy_debt = self.calculate_energy_debt(user_id)
        forecast = self.generate_7day_forecast(user_id)
        
        # Find first high-risk day (Cat 4 or 5)
        crash_day = None
        days_until = None
        
        for i, day in enumerate(forecast):
            if day['category'] >= 4:
                crash_day = day
                days_until = i + 1
                break
        
        # Calculate risk level based on energy debt
        if energy_debt >= 85:
            risk_level = 'critical'
            probability = 95
            severity = 'high'
        elif energy_debt >= 70:
            risk_level = 'high'
            probability = 75
            severity = 'high'
        elif energy_debt >= 50:
            risk_level = 'medium'
            probability = 45
            severity = 'medium'
        else:
            risk_level = 'low'
            probability = 15
            severity = 'low'
        
        # Adjust probability based on forecast
        if crash_day:
            probability = min(100, probability + 15)
        
        # Calculate confidence based on data availability
        events = self._get_recent_events(user_id, days=30)
        confidence = min(1.0, len(events) / 200.0) if events else 0.0
        
        return {
            'risk_level': risk_level,
            'probability': probability,
            'predicted_date': crash_day['date'] if crash_day else None,
            'days_until_crash': days_until,
            'severity': severity,
            'confidence': round(confidence, 2),
            'energy_debt': energy_debt
        }
    
    # ==================== HELPER METHODS ====================
    
    def _get_recent_events(self, user_id, days=30):
        """Get events from last N days"""
        if not self.db:
            return []
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            since = (datetime.now() - timedelta(days=days)).isoformat()
            cursor.execute(
                "SELECT event_type, data, timestamp FROM events WHERE user_id = ? AND timestamp >= ? ORDER BY timestamp DESC",
                (user_id, since)
            )
            rows = cursor.fetchall()
            
            events = []
            for row in rows:
                data = json.loads(row[1]) if row[1] else {}
                events.append({
                    'event_type': row[0],
                    'data': data,
                    'timestamp': row[2]
                })
            return events
    
    def _get_active_insights(self, user_id):
        """Get active insights for better predictions"""
        if not self.db:
            return []
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, pattern_type, description, confidence, data FROM patterns WHERE user_id = ? AND is_active = 1 ORDER BY confidence DESC",
                (user_id,)
            )
            rows = cursor.fetchall()
            
            insights = []
            for row in rows:
                data = json.loads(row[4]) if row[4] else {}
                insights.append({
                    'id': row[0],
                    'pattern_type': row[1],
                    'description': row[2],
                    'confidence': row[3],
                    'data': data
                })
            return insights
    
    # ==================== ENERGY DEBT CALCULATIONS ====================
    
    def _calculate_cns_fatigue(self, events):
        """Calculate CNS (Central Nervous System) fatigue from consecutive high-intensity days"""
        # Find consecutive workout days
        workout_events = [e for e in events if 'workout' in e['event_type'].lower()]
        
        if not workout_events:
            return 0.0
        
        # Sort by date
        workout_events.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Count consecutive days
        consecutive_days = 0
        last_date = None
        
        for event in workout_events:
            event_date = datetime.fromisoformat(event['timestamp']).date()
            
            if last_date is None:
                consecutive_days = 1
            elif (last_date - event_date).days == 1:
                consecutive_days += 1
            else:
                break
            
            last_date = event_date
        
        # Calculate fatigue score (0-100)
        # 7+ consecutive days = high fatigue
        fatigue_score = min(100, consecutive_days * 12)
        
        return fatigue_score
    
    def _calculate_work_pressure(self, events):
        """Calculate work pressure from study/work intensity"""
        # Get study sessions
        study_events = [e for e in events if 'study' in e['event_type'].lower()]
        
        if not study_events:
            return 0.0
        
        # Calculate average productivity and duration
        recent_7_days = [e for e in study_events[:14]]  # Last 2 weeks of sessions
        
        if not recent_7_days:
            return 0.0
        
        # Count high-intensity sessions (productivity > 7)
        high_intensity_count = sum(
            1 for e in recent_7_days
            if e.get('data', {}).get('productivity_score', 0) > 7
        )
        
        # Calculate pressure score
        # More high-intensity sessions = higher pressure
        pressure_score = min(100, (high_intensity_count / max(1, len(recent_7_days))) * 100)
        
        return pressure_score
    
    def _calculate_recovery_deficit(self, events):
        """Calculate recovery deficit from lack of recovery activities"""
        # Get meditation/recovery events
        meditation_events = [e for e in events if 'meditation' in e['event_type'].lower()]
        
        # Calculate days since last meditation
        if not meditation_events:
            days_since_meditation = 14  # Max tracked
        else:
            last_meditation = datetime.fromisoformat(meditation_events[0]['timestamp'])
            days_since_meditation = (datetime.now() - last_meditation).days
        
        # Get average stress from mood_check events
        mood_events = [e for e in events if 'mood_check' in e['event_type'].lower()]
        
        if mood_events:
            energy_levels = [e.get('data', {}).get('energy', 5) for e in mood_events[:7]]
            avg_energy = statistics.mean(energy_levels) if energy_levels else 5
            stress_multiplier = max(0, (10 - avg_energy) / 10)  # Low energy = high stress
        else:
            stress_multiplier = 0.5
        
        # Calculate deficit score
        # More days without recovery × stress level
        deficit_score = min(100, days_since_meditation * stress_multiplier * 15)
        
        return deficit_score
    
    def _calculate_sleep_debt(self, events):
        """Calculate sleep debt from insufficient sleep"""
        sleep_events = [e for e in events if 'sleep' in e['event_type'].lower()]
        
        if not sleep_events:
            return 0.0
        
        # Get last 7 sleep durations
        recent_sleep = sleep_events[:7]
        durations = [
            e.get('data', {}).get('duration', 7)
            for e in recent_sleep
        ]
        
        if not durations:
            return 0.0
        
        # Calculate average sleep
        avg_sleep = statistics.mean(durations)
        
        # Sleep debt calculation (target: 7-8 hours)
        optimal_sleep = 7.5
        sleep_deficit = max(0, optimal_sleep - avg_sleep)
        
        # Convert to 0-100 score
        debt_score = min(100, sleep_deficit * 30)
        
        return debt_score
    
    # ==================== FORECASTING CALCULATIONS ====================
    
    def _calculate_baselines(self, events):
        """Calculate baseline metrics from historical data"""
        baselines = {
            'energy': 5.0,
            'mood': 5.0,
            'productivity': 5.0,
            'workout_frequency': 0.3,
            'meditation_frequency': 0.2,
            'study_frequency': 0.5
        }
        
        # Calculate from mood_check events
        mood_events = [e for e in events if 'mood_check' in e['event_type'].lower()]
        if mood_events:
            energy_vals = [e.get('data', {}).get('energy', 5) for e in mood_events]
            mood_vals = [e.get('data', {}).get('mood', 5) for e in mood_events]
            
            if energy_vals:
                baselines['energy'] = statistics.mean(energy_vals)
            if mood_vals:
                baselines['mood'] = statistics.mean(mood_vals)
        
        # Calculate activity frequencies
        total_days = min(30, len(set(e['timestamp'][:10] for e in events)))
        if total_days > 0:
            workout_count = len([e for e in events if 'workout' in e['event_type'].lower()])
            meditation_count = len([e for e in events if 'meditation' in e['event_type'].lower()])
            study_count = len([e for e in events if 'study' in e['event_type'].lower()])
            
            baselines['workout_frequency'] = workout_count / total_days
            baselines['meditation_frequency'] = meditation_count / total_days
            baselines['study_frequency'] = study_count / total_days
        
        return baselines
    
    def _predict_capacity(self, events, insights, baselines, day_offset):
        """Predict capacity for a specific future day"""
        # Start with baseline energy
        capacity = baselines['energy']
        
        # Adjust based on recent trend
        recent_energy = self._get_recent_energy_trend(events, days=7)
        if recent_energy:
            trend = self._calculate_trend(recent_energy)
            capacity += trend * day_offset * 0.3  # Trend impact increases with distance
        
        # Adjust based on insights (workout/sleep boost capacity)
        for insight in insights:
            metric = insight.get('data', {}).get('metric_a', '')
            effects = insight.get('data', {}).get('output_effects', {})
            
            if metric in ['workout', 'sleep', 'meditation']:
                if 'energy' in effects:
                    # If user likely to do this activity, boost capacity
                    boost = effects['energy'] / 100 * baselines.get(f'{metric}_frequency', 0)
                    capacity += boost * 0.5
        
        # Apply decay for future days (uncertainty increases)
        decay_factor = 1.0 - (day_offset * 0.05)
        capacity *= decay_factor
        
        # Ensure within 0-10 range
        return max(0, min(10, capacity))
    
    def _predict_demand(self, events, forecast_date, day_offset):
        """Predict demand/workload for a specific future day"""
        # Base demand on historical study frequency
        study_events = [e for e in events if 'study' in e['event_type'].lower()]
        
        if not study_events:
            return 5.0  # Medium demand
        
        # Calculate average daily study sessions
        total_days = min(30, len(set(e['timestamp'][:10] for e in events)))
        study_frequency = len(study_events) / max(1, total_days)
        
        # Base demand score
        demand = study_frequency * 10  # Convert frequency to 0-10 scale
        
        # Check day of week (weekdays typically higher demand)
        day_of_week = forecast_date.weekday()
        if day_of_week < 5:  # Monday-Friday
            demand += 1.5
        else:  # Weekend
            demand -= 1.0
        
        # Add some variability for realism
        import random
        random.seed(day_offset)  # Consistent randomness
        demand += random.uniform(-0.5, 0.5)
        
        # Ensure within 0-10 range
        return max(0, min(10, demand))
    
    def _get_recent_energy_trend(self, events, days=7):
        """Get recent energy levels for trend analysis"""
        mood_events = [e for e in events if 'mood_check' in e['event_type'].lower()]
        
        if not mood_events:
            return []
        
        # Get last N days of energy levels
        recent = mood_events[:days]
        energy_levels = [e.get('data', {}).get('energy', 5) for e in recent]
        
        return energy_levels
    
    def _calculate_trend(self, series):
        """Calculate simple linear trend from a series"""
        if len(series) < 2:
            return 0.0
        
        # Simple slope calculation
        n = len(series)
        x_mean = (n - 1) / 2
        y_mean = statistics.mean(series)
        
        numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(series))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        return slope
    
    def _score_to_level(self, score, high_threshold, low_threshold):
        """Convert numerical score to categorical level"""
        if score >= high_threshold:
            return 'high'
        elif score <= low_threshold:
            return 'low'
        else:
            return 'medium'
    
    def _calculate_category(self, capacity, demand):
        """
        Calculate category (1-5) based on capacity and demand
        
        Cat 1: Low demand, high capacity (green light)
        Cat 2: Medium demand, high capacity (optimal)
        Cat 3: High demand, medium capacity (caution)
        Cat 4: High demand, low capacity (red alert)
        Cat 5: Overload (crash imminent)
        """
        if capacity == 'high':
            if demand == 'low':
                return 1
            elif demand == 'medium':
                return 2
            else:  # high demand
                return 3
        elif capacity == 'medium':
            if demand == 'low':
                return 2
            elif demand == 'medium':
                return 3
            else:  # high demand
                return 4
        else:  # low capacity
            if demand == 'low':
                return 3
            elif demand == 'medium':
                return 4
            else:  # high demand
                return 5
    
    def _generate_default_forecast(self):
        """Generate default forecast when no data available"""
        forecast = []
        today = date.today()
        
        for day_offset in range(1, 8):
            forecast_date = today + timedelta(days=day_offset)
            forecast.append({
                'date': forecast_date.isoformat(),
                'capacity': 'medium',
                'demand': 'medium',
                'category': 3,
                'details': {
                    'capacity_score': 5.0,
                    'demand_score': 5.0,
                    'predicted_energy': 5.0,
                    'predicted_workload': 5.0
                }
            })
        
        return forecast
    
    def _default_crash_risk(self):
        """Default crash risk when no data available"""
        return {
            'risk_level': 'low',
            'probability': 10,
            'predicted_date': None,
            'days_until_crash': None,
            'severity': 'low',
            'confidence': 0.0,
            'energy_debt': 0.0
        }
    
    def _generate_recommendations(self, energy_debt, forecast, crash_risk):
        """Generate actionable recommendations based on forecast"""
        recommendations = []
        
        # High energy debt recommendations
        if energy_debt >= 70:
            recommendations.append({
                'priority': 'critical',
                'action': 'Take a rest day immediately',
                'reason': f'Energy debt at {energy_debt}% - burnout risk is high'
            })
        elif energy_debt >= 50:
            recommendations.append({
                'priority': 'high',
                'action': 'Schedule a recovery day this week',
                'reason': f'Energy debt at {energy_debt}% - trending toward burnout'
            })
        
        # Category-based recommendations
        cat4_days = [d for d in forecast if d['category'] >= 4]
        if cat4_days:
            first_critical = cat4_days[0]
            recommendations.append({
                'priority': 'high',
                'action': f'Reduce workload on {first_critical["date"]}',
                'reason': f'Category {first_critical["category"]} day predicted - high demand with low capacity'
            })
        
        # Crash risk recommendations
        if crash_risk['risk_level'] in ['high', 'critical']:
            recommendations.append({
                'priority': 'critical',
                'action': 'Implement recovery protocol now',
                'reason': f'{crash_risk["risk_level"].title()} crash risk - {crash_risk["probability"]}% probability'
            })
        
        # Positive recommendations for Cat 1-2 days
        optimal_days = [d for d in forecast if d['category'] <= 2]
        if optimal_days:
            first_optimal = optimal_days[0]
            recommendations.append({
                'priority': 'low',
                'action': f'Schedule important tasks on {first_optimal["date"]}',
                'reason': f'Category {first_optimal["category"]} day - optimal capacity and manageable demand'
            })
        
        return recommendations

