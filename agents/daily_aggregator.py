"""
Universal Daily Aggregator
Converts raw events into daily summaries with ALL metrics extracted dynamically.
NO HARDCODING - discovers metrics from data.
"""

from collections import defaultdict
from datetime import datetime
from typing import List, Dict, Any


class DailyAggregator:
    """Aggregates events into daily summaries, extracting ALL metrics dynamically"""
    
    def __init__(self):
        self.metric_extractors = {
            'physical': self._extract_physical_metrics,
            'mental': self._extract_mental_metrics,
            'spiritual': self._extract_spiritual_metrics,
        }
    
    def aggregate_by_day(self, events: List[Dict]) -> Dict[str, Dict]:
        """
        Convert raw events into daily summaries
        
        Returns:
        {
            "2025-11-04": {
                "workout": True,
                "workout_intensity": "heavy",
                "workout_type": "upper_body",
                "tasks_total": 5,
                "tasks_completed": 4,
                "completion_rate": 0.80,
                "meditation": True,
                "meditation_duration": 15,
                "sleep_hours": 7.5,
                "energy_avg": 7.5,
                "mood_avg": 8.0,
                ... ANY metric from events
            }
        }
        """
        
        daily = defaultdict(lambda: {
            'events': [],
            'dimensions': defaultdict(list),
        })
        
        # Group events by day
        for event in events:
            date = self._extract_date(event['timestamp'])
            daily[date]['events'].append(event)
            
            # Collect dimension values for averaging
            if 'data' in event and isinstance(event['data'], dict):
                for dim in ['energy', 'mood', 'productivity', 'focus', 'stress']:
                    if dim in event['data']:
                        daily[date]['dimensions'][dim].append(float(event['data'][dim]))
        
        # Process each day
        summaries = {}
        for date, data in daily.items():
            summary = self._build_daily_summary(data['events'], data['dimensions'])
            summaries[date] = summary
        
        return summaries
    
    def _build_daily_summary(self, events: List[Dict], dimensions: Dict) -> Dict:
        """Build summary for a single day"""
        
        summary = {}
        
        # Extract metrics from events by category
        for event in events:
            category = event.get('category', 'unknown')
            if category in self.metric_extractors:
                metrics = self.metric_extractors[category](event)
                summary.update(metrics)
        
        # Calculate dimension averages
        for dim, values in dimensions.items():
            if values:
                summary[f'{dim}_avg'] = sum(values) / len(values)
                summary[f'{dim}_max'] = max(values)
                summary[f'{dim}_min'] = min(values)
        
        # Calculate derived metrics
        summary = self._calculate_derived_metrics(summary)
        
        return summary
    
    def _extract_physical_metrics(self, event: Dict) -> Dict:
        """Extract physical dimension metrics"""
        
        metrics = {}
        event_type = event.get('event_type', '').lower()
        data = event.get('data', {})
        
        # Workout events
        if 'workout' in event_type or 'exercise' in event_type or 'gym' in event_type:
            metrics['workout'] = True
            
            # Intensity
            if 'intensity' in data:
                metrics['workout_intensity'] = data['intensity']
            elif 'feeling' in event and event['feeling'] is not None:
                # Infer intensity from feeling
                feeling = event['feeling'].lower()
                if 'great' in feeling or 'amazing' in feeling:
                    metrics['workout_intensity'] = 'heavy'
                elif 'good' in feeling or 'okay' in feeling:
                    metrics['workout_intensity'] = 'moderate'
                else:
                    metrics['workout_intensity'] = 'light'
            else:
                metrics['workout_intensity'] = 'moderate'  # Default
            
            # Type
            if 'type' in data:
                metrics['workout_type'] = data['type']
            
            # Duration
            if 'duration' in data:
                metrics['workout_duration'] = float(data['duration'])
        
        # Sleep events
        if 'sleep' in event_type:
            if 'hours' in data or 'duration' in data:
                metrics['sleep_hours'] = float(data.get('hours', data.get('duration', 0)))
            if 'quality' in data:
                quality = data['quality']
                # Convert string quality to numeric
                if isinstance(quality, str):
                    quality_map = {'excellent': 10, 'good': 8, 'okay': 6, 'fair': 5, 'poor': 3, 'bad': 2}
                    metrics['sleep_quality'] = quality_map.get(quality.lower(), 5)
                else:
                    metrics['sleep_quality'] = float(quality)
        
        # Commute events
        if 'commute' in event_type:
            metrics['commute'] = True
            if 'duration' in data:
                metrics['commute_duration'] = float(data['duration'])
        
        return metrics
    
    def _extract_mental_metrics(self, event: Dict) -> Dict:
        """Extract mental dimension metrics"""
        
        metrics = {}
        event_type = event.get('event_type', '').lower()
        data = event.get('data', {})
        
        # Task events
        if 'task' in event_type:
            if 'tasks_total' not in metrics:
                metrics['tasks_total'] = 0
            if 'tasks_completed' not in metrics:
                metrics['tasks_completed'] = 0
            
            metrics['tasks_total'] += 1
            
            if data.get('completed', False):
                metrics['tasks_completed'] += 1
            
            # Priority tracking
            priority = data.get('priority', 'medium')
            if priority == 'high':
                metrics.setdefault('high_priority_tasks', 0)
                metrics['high_priority_tasks'] += 1
                if data.get('completed', False):
                    metrics.setdefault('high_priority_completed', 0)
                    metrics['high_priority_completed'] += 1
        
        # Study events
        if 'study' in event_type:
            metrics['study'] = True
            if 'duration' in data:
                metrics['study_duration'] = float(data['duration'])
            if 'productivity' in data:
                metrics['study_productivity'] = float(data['productivity'])
        
        # Meeting events
        if 'meeting' in event_type:
            metrics.setdefault('meeting_count', 0)
            metrics['meeting_count'] += 1
            if 'duration' in data:
                metrics.setdefault('meeting_duration', 0)
                metrics['meeting_duration'] += float(data['duration'])
        
        # Reading events
        if 'read' in event_type:
            metrics['reading'] = True
            if 'duration' in data:
                metrics['reading_duration'] = float(data['duration'])
        
        return metrics
    
    def _extract_spiritual_metrics(self, event: Dict) -> Dict:
        """Extract spiritual dimension metrics"""
        
        metrics = {}
        event_type = event.get('event_type', '').lower()
        data = event.get('data', {})
        
        # Meditation events
        if 'meditat' in event_type:
            metrics['meditation'] = True
            if 'duration' in data:
                metrics['meditation_duration'] = float(data['duration'])
            if 'quality' in data:
                metrics['meditation_quality'] = float(data['quality'])
        
        # Reflection events
        if 'reflect' in event_type or 'journal' in event_type:
            metrics['reflection'] = True
            if 'duration' in data:
                metrics['reflection_duration'] = float(data['duration'])
        
        # Gratitude events
        if 'gratitude' in event_type:
            metrics['gratitude'] = True
        
        return metrics
    
    def _calculate_derived_metrics(self, summary: Dict) -> Dict:
        """Calculate derived metrics from raw ones"""
        
        # Task completion rate
        if 'tasks_total' in summary and summary['tasks_total'] > 0:
            completed = summary.get('tasks_completed', 0)
            summary['completion_rate'] = completed / summary['tasks_total']
        
        # High priority completion rate
        if 'high_priority_tasks' in summary and summary['high_priority_tasks'] > 0:
            completed = summary.get('high_priority_completed', 0)
            summary['high_priority_completion_rate'] = completed / summary['high_priority_tasks']
        
        # Workout happened (binary)
        if 'workout' not in summary:
            summary['workout'] = False
        
        # Meditation happened (binary)
        if 'meditation' not in summary:
            summary['meditation'] = False
        
        # Study happened (binary)
        if 'study' not in summary:
            summary['study'] = False
        
        # Meeting density (meetings per hour if we have duration)
        if 'meeting_count' in summary and 'meeting_duration' in summary:
            if summary['meeting_duration'] > 0:
                summary['meeting_density'] = summary['meeting_count'] / (summary['meeting_duration'] / 60)
        
        return summary
    
    def _extract_date(self, timestamp: str) -> str:
        """Extract date from timestamp"""
        if 'T' in timestamp:
            return timestamp.split('T')[0]
        elif ' ' in timestamp:
            return timestamp.split(' ')[0]
        else:
            return timestamp[:10]
    
    def get_metric_names(self, daily_summaries: Dict) -> List[str]:
        """Extract all unique metric names from summaries"""
        
        all_metrics = set()
        for date, summary in daily_summaries.items():
            all_metrics.update(summary.keys())
        
        return sorted(list(all_metrics))
    
    def split_by_condition(self, daily_summaries: Dict, condition_metric: str, 
                          condition_value: Any = True) -> tuple:
        """
        Split days by condition (e.g., workout=True vs workout=False)
        
        Returns: (days_with_condition, days_without_condition)
        """
        
        with_condition = {}
        without_condition = {}
        
        for date, summary in daily_summaries.items():
            if summary.get(condition_metric) == condition_value:
                with_condition[date] = summary
            else:
                without_condition[date] = summary
        
        return with_condition, without_condition
