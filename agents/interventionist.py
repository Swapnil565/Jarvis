from .base_agent import BaseAgent
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

class InterventionistAgent(BaseAgent):
    def __init__(self, db=None):
        super().__init__()
        self.db = db
        self.logger.info("InterventionistAgent initialized")
        self.overtraining_threshold = 7
        self.low_energy_threshold = 4
        self.sleep_deficit_hours = 6.5
        self.meditation_gap_days = 3
        self.insight_confidence_min = 0.7
        self.streak_celebration_days = 7
    
    def process(self, data):
        user_id = data.get('user_id')
        if not user_id:
            return {"interventions": [], "error": "Missing user_id"}
        
        insights = self._get_active_insights(user_id)
        recent_events = self._get_recent_events(user_id, days=7)
        interventions = []
        
        for insight in insights:
            intervention = self._convert_insight_to_intervention(insight, recent_events, user_id)
            if intervention:
                interventions.append(intervention)
        
        state_interventions = self._detect_state_based_interventions(recent_events, user_id)
        interventions.extend(state_interventions)
        prioritized = self._prioritize_interventions(interventions)
        
        for intervention in prioritized[:5]:
            self._store_intervention(intervention, user_id)
        
        return {"interventions": prioritized[:5], "total_generated": len(interventions)}

    def _get_active_insights(self, user_id):
        if not self.db:
            return []
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT id, pattern_type, description, confidence, data FROM patterns WHERE user_id = ? AND is_active = 1 AND confidence >= ? ORDER BY confidence DESC"
            cursor.execute(query, (user_id, self.insight_confidence_min))
            rows = cursor.fetchall()
            insights = []
            for row in rows:
                data = json.loads(row[4]) if row[4] else {}
                insights.append({
                    'id': row[0],
                    'pattern_type': row[1],
                    'description': row[2],
                    'confidence': row[3],
                    'impact_metrics': data.get('output_effects', {}),
                    'supporting_data': {
                        'metric_a': data.get('metric_a'),
                        'correlation_direction': data.get('direction', 'positive'),
                        'type': data.get('type')
                    }
                })
            return insights
    
    def _get_recent_events(self, user_id, days=7):
        if not self.db:
            return []
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            since = (datetime.now() - timedelta(days=days)).isoformat()
            query = "SELECT event_type, data, timestamp FROM events WHERE user_id = ? AND timestamp >= ? ORDER BY timestamp DESC"
            cursor.execute(query, (user_id, since))
            rows = cursor.fetchall()
            events = []
            for row in rows:
                data = json.loads(row[1]) if row[1] else {}
                events.append({'event_type': row[0], 'metrics': data, 'timestamp': row[2]})
            return events

    def _convert_insight_to_intervention(self, insight, recent_events, user_id):
        metric_a = insight['supporting_data'].get('metric_a', '')
        impact = insight['impact_metrics']
        supporting = insight.get('supporting_data', {})
        is_negative = supporting.get('correlation_direction') == 'negative'
        behavior = metric_a.replace('_', ' ')
        is_doing_behavior = self._is_user_doing_behavior(metric_a, recent_events)
        
        if is_negative:
            if is_doing_behavior:
                return self._create_warning_intervention(insight, behavior, impact, user_id)
        else:
            if not is_doing_behavior:
                return self._create_recommendation_intervention(insight, behavior, impact, user_id)
        return None
    
    def _is_user_doing_behavior(self, metric_a, events):
        behavior_map = {'workout': 'workout', 'sleep': 'sleep', 'meditation': 'meditation', 'reading': 'reading', 'study': 'study'}
        behavior_key = None
        for key, event_type in behavior_map.items():
            if key in metric_a.lower():
                behavior_key = event_type
                break
        if not behavior_key:
            return False
        recent_3_days = [e for e in events[:21]]
        behavior_count = sum(1 for e in recent_3_days if behavior_key in e['event_type'].lower())
        return behavior_count >= 2

    def _create_warning_intervention(self, insight, behavior, impact, user_id):
        top_impact = max(impact.items(), key=lambda x: abs(x[1]))
        impact_metric = top_impact[0]
        impact_value = abs(top_impact[1])
        
        return {
            'type': 'warning',
            'urgency': 'high',
            'title': f'⚠️ {behavior.title()} Affecting Your {impact_metric.replace("_", " ").title()}',
            'message': f'Your {behavior} is associated with {impact_value:.0f}% worse {impact_metric.replace("_", " ")}. Consider reducing or adjusting this activity.',
            'confidence': insight['confidence'],
            'insight_id': insight['id']
        }

    def _create_recommendation_intervention(self, insight, behavior, impact, user_id):
        top_impact = max(impact.items(), key=lambda x: x[1])
        impact_metric = top_impact[0]
        impact_value = top_impact[1]
        
        return {
            'type': 'suggestion',
            'urgency': 'medium',
            'title': f'💡 Try {behavior.title()} to Boost {impact_metric.replace("_", " ").title()}',
            'message': f'Based on your patterns, {behavior} can improve your {impact_metric.replace("_", " ")} by {impact_value:.0f}%. You haven\'t done this recently.',
            'confidence': insight['confidence'],
            'insight_id': insight['id']
        }

    def _detect_state_based_interventions(self, events, user_id):
        interventions = []
        
        overtraining = self._detect_overtraining(events)
        if overtraining:
            interventions.append(overtraining)
        
        low_energy = self._detect_low_energy_streak(events)
        if low_energy:
            interventions.append(low_energy)
        
        sleep_deficit = self._detect_sleep_deficit(events)
        if sleep_deficit:
            interventions.append(sleep_deficit)
        
        meditation_gap = self._detect_meditation_gap(events)
        if meditation_gap:
            interventions.append(meditation_gap)
        
        streak = self._detect_streak(events)
        if streak:
            interventions.append(streak)
        
        optimal_timing = self._detect_optimal_timing(events)
        if optimal_timing:
            interventions.append(optimal_timing)
        
        return interventions

    def _detect_overtraining(self, events):
        workout_events = [e for e in events if 'workout' in e['event_type'].lower()]
        if len(workout_events) < self.overtraining_threshold:
            return None
        
        consecutive_days = 0
        last_date = None
        for event in sorted(workout_events, key=lambda x: x['timestamp'], reverse=True):
            event_date = datetime.fromisoformat(event['timestamp']).date()
            if last_date is None:
                consecutive_days = 1
            elif (last_date - event_date).days == 1:
                consecutive_days += 1
            else:
                break
            last_date = event_date
        
        if consecutive_days >= self.overtraining_threshold:
            return {
                'type': 'warning',
                'urgency': 'critical',
                'title': '🔴 Overtraining Alert',
                'message': f'You\'ve worked out {consecutive_days} consecutive days. Consider taking a rest day to prevent burnout and injury.',
                'confidence': 0.9,
                'insight_id': None
            }
        return None

    def _detect_low_energy_streak(self, events):
        energy_events = [e for e in events if e.get('metrics', {}).get('energy_level') is not None]
        if len(energy_events) < 2:
            return None
        
        recent_energy = energy_events[:2]
        low_energy_count = sum(1 for e in recent_energy if e['metrics']['energy_level'] <= self.low_energy_threshold)
        
        if low_energy_count >= 2:
            avg_energy = sum(e['metrics']['energy_level'] for e in recent_energy) / len(recent_energy)
            return {
                'type': 'warning',
                'urgency': 'high',
                'title': '⚠️ Low Energy Detected',
                'message': f'Your energy has been low (avg {avg_energy:.1f}/10) for {low_energy_count} days. Consider more sleep or light exercise.',
                'confidence': 0.85,
                'insight_id': None
            }
        return None

    def _detect_sleep_deficit(self, events):
        sleep_events = [e for e in events if 'sleep' in e['event_type'].lower() and e.get('metrics', {}).get('duration') is not None]
        if len(sleep_events) < 3:
            return None
        
        recent_sleep = sleep_events[:3]
        avg_sleep = sum(e['metrics']['duration'] for e in recent_sleep) / len(recent_sleep)
        
        if avg_sleep < self.sleep_deficit_hours:
            return {
                'type': 'warning',
                'urgency': 'critical',
                'title': '🔴 Sleep Deficit Alert',
                'message': f'You\'re averaging {avg_sleep:.1f} hours of sleep. Aim for 7-8 hours to improve energy and productivity.',
                'confidence': 0.95,
                'insight_id': None
            }
        return None

    def _detect_meditation_gap(self, events):
        meditation_events = [e for e in events if 'meditation' in e['event_type'].lower()]
        if not meditation_events:
            days_since = 7
        else:
            last_meditation = datetime.fromisoformat(meditation_events[0]['timestamp'])
            days_since = (datetime.now() - last_meditation).days
        
        if days_since >= self.meditation_gap_days:
            return {
                'type': 'suggestion',
                'urgency': 'low',
                'title': '🧘 Meditation Reminder',
                'message': f'It\'s been {days_since} days since your last meditation. A short session could boost your mood and energy.',
                'confidence': 0.75,
                'insight_id': None
            }
        return None

    def _detect_streak(self, events):
        for behavior in ['workout', 'sleep', 'meditation', 'reading']:
            behavior_events = [e for e in events if behavior in e['event_type'].lower()]
            if len(behavior_events) < self.streak_celebration_days:
                continue
            
            consecutive_days = 0
            last_date = None
            for event in sorted(behavior_events, key=lambda x: x['timestamp'], reverse=True):
                event_date = datetime.fromisoformat(event['timestamp']).date()
                if last_date is None:
                    consecutive_days = 1
                elif (last_date - event_date).days == 1:
                    consecutive_days += 1
                else:
                    break
                last_date = event_date
            
            if consecutive_days >= self.streak_celebration_days:
                return {
                    'type': 'insight',
                    'urgency': 'low',
                    'title': f'🎉 {consecutive_days}-Day {behavior.title()} Streak!',
                    'message': f'Amazing! You\'ve maintained your {behavior} habit for {consecutive_days} consecutive days. Keep it up!',
                    'confidence': 1.0,
                    'insight_id': None
                }
        return None

    def _detect_optimal_timing(self, events):
        study_events = [e for e in events if 'study' in e['event_type'].lower() and e.get('metrics', {}).get('productivity_score') is not None]
        if len(study_events) < 3:
            return None
        
        time_productivity = {}
        for event in study_events:
            hour = datetime.fromisoformat(event['timestamp']).hour
            time_slot = 'morning' if 6 <= hour < 12 else 'afternoon' if 12 <= hour < 18 else 'evening' if 18 <= hour < 22 else 'night'
            if time_slot not in time_productivity:
                time_productivity[time_slot] = []
            time_productivity[time_slot].append(event['metrics']['productivity_score'])
        
        best_time = max(time_productivity.items(), key=lambda x: sum(x[1])/len(x[1]) if x[1] else 0)
        if len(best_time[1]) >= 2:
            avg_productivity = sum(best_time[1]) / len(best_time[1])
            return {
                'type': 'insight',
                'urgency': 'low',
                'title': f'⏰ You\'re Most Productive in the {best_time[0].title()}',
                'message': f'Your {best_time[0]} study sessions average {avg_productivity:.1f}/10 productivity. Try scheduling important tasks then.',
                'confidence': 0.8,
                'insight_id': None
            }
        return None

    def _prioritize_interventions(self, interventions):
        urgency_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        return sorted(interventions, key=lambda x: (urgency_order.get(x['urgency'], 999), -x['confidence']))

    def _store_intervention(self, intervention, user_id):
        if not self.db:
            return
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            data = json.dumps({
                'confidence': intervention.get('confidence'),
                'insight_id': intervention.get('insight_id')
            })
            cursor.execute(
                "INSERT INTO interventions (user_id, intervention_type, title, message, urgency, data, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, intervention['type'], intervention['title'], intervention['message'], intervention['urgency'], data, datetime.now().isoformat())
            )
            conn.commit()
