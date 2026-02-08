"""
Universal Insight Generator
Replaces hardcoded pattern detector with dynamic insight discovery.
Finds actionable correlations between ANY metrics.
"""

import statistics
import math
from collections import defaultdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json


class InsightGenerator:
    """
    Universal insight generator that:
    1. Compares ALL metrics to ALL metrics
    2. Finds strong correlations (>0.5)
    3. Filters for actionability
    4. Tracks novelty (no repeats)
    5. Ranks by impact
    """
    
    def __init__(self, db=None):
        self.db = db
        
        # Production thresholds (balanced for quality + quantity)
        self.min_correlation = 0.3  # 30%+ correlation (relaxed from 50%)
        self.min_sample_size = 10  # 10+ days minimum
        self.min_improvement = 20  # 20%+ improvement to report (relaxed from 30%)
        self.max_insights = 10  # Return top 10 comprehensive insights
        
        # Metric categorization for actionability filter
        self.input_metrics = [
            'workout', 'meditation', 'sleep_hours', 'sleep_quality',
            'workout_intensity', 'meditation_duration', 'reading',
            'study', 'nutrition_quality', 'hydration'
        ]
        
        self.output_metrics = [
            'completion_rate', 'tasks_completed', 'energy_avg', 'mood_avg',
            'productivity_avg', 'focus_avg', 'stress_avg', 'study_productivity',
            'high_priority_completion_rate'
        ]
    
    def generate_insights(self, user_id: int, days: int = 30) -> List[Dict]:
        """
        Main entry point: Generate actionable insights for user
        
        Returns: List of top 3-5 insights ranked by priority
        """
        
        # Get raw events (calculate date_from)
        from datetime import datetime, timedelta
        date_from = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        events = self.db.get_events(user_id, date_from=date_from, limit=1000)
        
        if len(events) < self.min_sample_size:
            return []
        
        # Aggregate into daily summaries
        from agents.daily_aggregator import DailyAggregator
        aggregator = DailyAggregator()
        daily_summaries = aggregator.aggregate_by_day(events)
        
        if len(daily_summaries) < self.min_sample_size:
            return []
        
        # Find all correlations
        all_insights = self._find_all_correlations(daily_summaries)
        print(f"🔍 Found {len(all_insights)} total correlations")
        
        # Filter for actionability
        actionable = self._filter_actionable(all_insights)
        print(f"✅ {len(actionable)} actionable insights (filtered from {len(all_insights)})")
        
        # Rank by impact BEFORE merging (so we keep the best ones)
        ranked = self._rank_by_impact(actionable)
        
        # Deduplicate and merge similar insights
        merged = self._merge_similar_insights(ranked)
        print(f"🔗 Merged similar insights: {len(ranked)} → {len(merged)}")
        
        # Filter for novelty (not already reported) - AFTER merging
        novel = self._filter_novel(merged, user_id)
        print(f"🆕 {len(novel)} novel insights (not previously reported, {len(merged) - len(novel)} already known)")
        
        # Re-rank after novelty filter
        final_ranked = self._rank_by_impact(novel)
        print(f"📊 Returning top {self.max_insights} of {len(final_ranked)}")
        
        # Generate natural language descriptions
        final = self._generate_descriptions(final_ranked[:self.max_insights])
        
        # Save to database as reported
        self._save_insights(final, user_id)
        
        return final
    
    def _find_all_correlations(self, daily_summaries: Dict) -> List[Dict]:
        """
        Universal correlation engine:
        Compare ALL metrics to ALL metrics
        """
        
        insights = []
        
        # Get all available metrics
        all_metrics = set()
        for date, summary in daily_summaries.items():
            all_metrics.update(summary.keys())
        
        all_metrics = list(all_metrics)
        
        # Compare every pair
        for metric_a in all_metrics:
            for metric_b in all_metrics:
                if metric_a == metric_b:
                    continue
                
                # Try to find correlation
                insight = self._calculate_correlation(
                    metric_a, metric_b, daily_summaries
                )
                
                if insight:
                    insights.append(insight)
        
        return insights
    
    def _calculate_correlation(self, metric_a: str, metric_b: str, 
                               daily_summaries: Dict) -> Optional[Dict]:
        """
        Calculate correlation between two metrics
        Handles both binary (True/False) and continuous metrics
        """
        
        # Extract values for both metrics
        pairs = []
        for date, summary in daily_summaries.items():
            if metric_a in summary and metric_b in summary:
                val_a = summary[metric_a]
                val_b = summary[metric_b]
                
                # Convert boolean to 1/0
                if isinstance(val_a, bool):
                    val_a = 1 if val_a else 0
                if isinstance(val_b, bool):
                    val_b = 1 if val_b else 0
                
                # Skip non-numeric
                if not isinstance(val_a, (int, float)) or not isinstance(val_b, (int, float)):
                    continue
                
                pairs.append((val_a, val_b))
        
        # Need minimum sample size
        if len(pairs) < self.min_sample_size:
            return None
        
        # Separate into series
        series_a = [p[0] for p in pairs]
        series_b = [p[1] for p in pairs]
        
        # Check if metric_a is binary (workout yes/no)
        unique_a = set(series_a)
        is_binary_a = unique_a.issubset({0, 1, 0.0, 1.0})
        
        if is_binary_a:
            # Compare: days with metric_a=1 vs metric_a=0
            return self._compare_binary_groups(metric_a, metric_b, pairs)
        else:
            # Continuous correlation (Pearson)
            corr = self._pearson_correlation(series_a, series_b)
            
            if abs(corr) < self.min_correlation:
                return None
            
            # Calculate improvement percentage
            avg_a = statistics.mean(series_a)
            avg_b = statistics.mean(series_b)
            
            # For continuous, use correlation strength as proxy for impact
            improvement = abs(corr) * 100
            
            return {
                'type': 'continuous_correlation',
                'metric_a': metric_a,
                'metric_b': metric_b,
                'correlation': corr,
                'improvement_percent': improvement,
                'sample_size': len(pairs),
                'avg_a': avg_a,
                'avg_b': avg_b,
                'confidence': min(0.95, 0.5 + len(pairs) / 60)
            }
    
    def _compare_binary_groups(self, binary_metric: str, outcome_metric: str,
                                pairs: List[tuple]) -> Optional[Dict]:
        """
        Compare outcome when binary metric is True vs False
        Example: task completion on workout days vs rest days
        """
        
        with_metric = []
        without_metric = []
        
        for val_a, val_b in pairs:
            if val_a == 1 or val_a == 1.0:
                with_metric.append(val_b)
            else:
                without_metric.append(val_b)
        
        # Need at least 3 of each
        if len(with_metric) < 3 or len(without_metric) < 3:
            return None
        
        avg_with = statistics.mean(with_metric)
        avg_without = statistics.mean(without_metric)
        
        # Calculate improvement percentage
        if avg_without == 0:
            return None
        
        improvement = ((avg_with - avg_without) / avg_without) * 100
        
        # Only report if significant improvement
        if abs(improvement) < self.min_improvement:
            return None
        
        # Calculate correlation for confidence
        series_a = [1] * len(with_metric) + [0] * len(without_metric)
        series_b = with_metric + without_metric
        corr = self._pearson_correlation(series_a, series_b)
        
        return {
            'type': 'binary_comparison',
            'metric_a': binary_metric,  # The input (workout)
            'metric_b': outcome_metric,  # The outcome (tasks)
            'correlation': corr,
            'improvement_percent': improvement,
            'avg_with': avg_with,
            'avg_without': avg_without,
            'sample_size_with': len(with_metric),
            'sample_size_without': len(without_metric),
            'sample_size': len(with_metric) + len(without_metric),
            'confidence': min(0.95, 0.5 + len(pairs) / 60),
            'direction': 'positive' if improvement > 0 else 'negative'
        }
    
    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(xi ** 2 for xi in x)
        sum_y2 = sum(yi ** 2 for yi in y)
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2))
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator
    
    def _filter_actionable(self, insights: List[Dict]) -> List[Dict]:
        """
        Filter for actionable insights only:
        - Input metrics → Output metrics (workout → tasks) ✅
        - Output → Output (tasks → energy) ❌
        - Obvious pairs (tasks_total → tasks_completed) ❌
        """
        
        actionable = []
        
        # Obvious pairs to skip
        obvious_pairs = [
            ('tasks_total', 'tasks_completed'),
            ('tasks_total', 'completion_rate'),
            ('tasks_completed', 'completion_rate'),
            ('workout', 'workout_duration'),
            ('workout', 'workout_intensity'),
            ('meditation', 'meditation_duration'),
            ('energy_avg', 'energy_max'),
            ('mood_avg', 'mood_max'),
            ('high_priority_tasks', 'high_priority_completed'),
        ]
        
        for insight in insights:
            metric_a = insight['metric_a']
            metric_b = insight['metric_b']
            
            # Skip obvious pairs
            if (metric_a, metric_b) in obvious_pairs or (metric_b, metric_a) in obvious_pairs:
                continue
            
            # Check if actionable (input → output)
            is_input = any(inp in metric_a for inp in self.input_metrics)
            is_output = any(out in metric_b for out in self.output_metrics)
            
            if is_input and is_output:
                actionable.append(insight)
        
        return actionable
    
    def _filter_novel(self, insights: List[Dict], user_id: int) -> List[Dict]:
        """
        Filter for novel insights:
        - Not already reported to user
        - Or correlation changed significantly (>15%)
        """
        
        # Get previously reported insights
        reported = self._get_reported_insights(user_id)
        
        novel = []
        
        for insight in insights:
            # Create signature based on insight type
            if insight['type'] in ['multi_output_insight', 'merged_insight']:
                # For merged insights, use base metric only
                signature = f"{insight['metric_a']}"
            else:
                # For simple insights, use full metric pair
                signature = f"{insight['metric_a']}→{insight.get('metric_b', 'unknown')}"
            
            # Check if already reported
            if signature in reported:
                old_corr = reported[signature].get('correlation', 0)
                new_corr = insight['correlation']
                
                # Only re-report if correlation changed significantly
                if abs(new_corr - old_corr) < 0.15:  # Less than 15% change
                    continue
                
                # Mark as updated
                insight['is_update'] = True
                insight['old_correlation'] = old_corr
            else:
                insight['is_update'] = False
            
            novel.append(insight)
        
        return novel
    
    def _rank_by_impact(self, insights: List[Dict]) -> List[Dict]:
        """
        Rank insights by priority:
        - Novelty (new insights first)
        - Impact (bigger improvement = higher)
        - Confidence (more data = higher)
        """
        
        for insight in insights:
            score = 0
            
            # Novelty boost
            if not insight.get('is_update', False):
                score += 50  # New insights get big boost
            else:
                score += 25  # Updates get smaller boost
            
            # Impact boost (improvement percentage)
            improvement = abs(insight.get('improvement_percent', 0))
            if improvement > 100:
                score += 40
            elif improvement > 75:
                score += 35
            elif improvement > 50:
                score += 25
            elif improvement > 30:
                score += 15
            
            # Confidence boost
            confidence = insight.get('confidence', 0)
            if confidence > 0.9:
                score += 15
            elif confidence > 0.7:
                score += 10
            elif confidence > 0.5:
                score += 5
            
            # Sample size boost (more data = better)
            sample = insight.get('sample_size', 0)
            if sample > 25:
                score += 10
            elif sample > 15:
                score += 5
            
            insight['priority_score'] = score
        
        # Sort by priority
        return sorted(insights, key=lambda x: x['priority_score'], reverse=True)
    
    def _merge_similar_insights(self, insights: List[Dict]) -> List[Dict]:
        """
        Merge similar insights to avoid duplicates
        Strategies:
        1. Same input → same output (sleep_hours + sleep_quality → productivity)
        2. Same input → multiple outputs (workout → mood, energy, productivity)
        """
        
        # First pass: Group by input base (workout, sleep, meditation)
        input_groups = defaultdict(list)
        
        for insight in insights:
            metric_a = insight['metric_a']
            input_base = self._get_base_metric(metric_a)
            input_groups[input_base].append(insight)
        
        # Second pass: For each input, group by output
        merged = []
        
        for input_base, input_insights in input_groups.items():
            if len(input_insights) == 1:
                # Only one insight for this input, keep as-is
                merged.append(input_insights[0])
            elif len(input_insights) <= 3:
                # 2-3 insights for same input: check if they can be merged
                output_groups = defaultdict(list)
                for ins in input_insights:
                    output_base = self._get_base_metric(ins['metric_b'])
                    output_groups[output_base].append(ins)
                
                # If all insights have same output, merge them
                if len(output_groups) == 1:
                    # All same output: merge into one
                    merged_insight = self._merge_insight_group(input_insights, f"{input_base}→single_output")
                    merged.append(merged_insight)
                else:
                    # Different outputs: create comprehensive multi-output insight
                    multi_insight = self._create_multi_output_insight(input_insights, input_base)
                    merged.append(multi_insight)
            else:
                # 4+ insights: create comprehensive multi-output insight
                multi_insight = self._create_multi_output_insight(input_insights, input_base)
                merged.append(multi_insight)
        
        # Re-sort by priority score
        merged.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return merged
    
    def _create_multi_output_insight(self, insights: List[Dict], input_base: str) -> Dict:
        """
        Create comprehensive insight when input affects multiple outputs
        Example: workout → mood, energy, productivity
        """
        
        # Group by output
        output_effects = {}
        for ins in insights:
            output = self._humanize_metric(self._get_base_metric(ins['metric_b']))
            improvement = abs(ins.get('improvement_percent', 0))
            output_effects[output] = improvement
        
        # Sort by improvement
        top_effects = sorted(output_effects.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate averages
        avg_improvement = sum(output_effects.values()) / len(output_effects)
        avg_correlation = sum(ins['correlation'] for ins in insights) / len(insights)
        total_samples = sum(ins['sample_size'] for ins in insights)
        avg_confidence = sum(ins['confidence'] * ins['sample_size'] for ins in insights) / total_samples
        
        # Boost priority significantly for multi-output insights
        base_score = max(ins['priority_score'] for ins in insights)
        boosted_score = base_score + (len(insights) - 1) * 15
        
        return {
            'type': 'multi_output_insight',
            'metric_a': input_base,
            'output_effects': output_effects,
            'top_effects': top_effects[:3],  # Top 3 effects
            'correlation': avg_correlation,
            'improvement_percent': avg_improvement,
            'confidence': avg_confidence,
            'sample_size': total_samples,
            'priority_score': boosted_score,
            'merged_count': len(insights),
            'sub_insights': insights,
            'direction': 'positive' if avg_correlation > 0 else 'negative'
        }
    
    def _get_base_metric(self, metric: str) -> str:
        """Extract base metric name (sleep_hours → sleep, productivity_avg → productivity)"""
        
        # Remove common suffixes
        base = metric.replace('_avg', '').replace('_max', '').replace('_min', '')
        base = base.replace('_hours', '').replace('_quality', '').replace('_duration', '')
        base = base.replace('_total', '').replace('_completed', '').replace('_rate', '')
        
        # Handle special cases
        if 'completion' in base:
            return 'task_completion'
        if 'high_priority' in base:
            return 'prioritization'
        
        return base
    
    def _merge_insight_group(self, group: List[Dict], group_key: str) -> Dict:
        """Merge multiple similar insights into one comprehensive insight"""
        
        # Take the highest priority insight as base
        base = group[0]
        
        # Collect all correlations and improvements
        correlations = [ins['correlation'] for ins in group]
        improvements = [abs(ins.get('improvement_percent', 0)) for ins in group]
        
        # Average the metrics
        avg_correlation = sum(correlations) / len(correlations)
        avg_improvement = sum(improvements) / len(improvements)
        
        # Collect all specific metrics mentioned
        input_metrics = list(set([ins['metric_a'] for ins in group]))
        output_metrics = list(set([ins['metric_b'] for ins in group]))
        
        # Calculate combined confidence (average weighted by sample size)
        total_samples = sum(ins['sample_size'] for ins in group)
        weighted_confidence = sum(ins['confidence'] * ins['sample_size'] for ins in group) / total_samples
        
        # Boost priority score for merged insights (they're stronger)
        boosted_score = base['priority_score'] + (len(group) - 1) * 10
        
        # Create merged insight
        merged = {
            'type': 'merged_insight',
            'original_type': base['type'],
            'metric_a': self._get_base_metric(base['metric_a']),  # Use base name
            'metric_b': self._get_base_metric(base['metric_b']),
            'correlation': avg_correlation,
            'improvement_percent': avg_improvement,
            'confidence': weighted_confidence,
            'sample_size': total_samples,
            'priority_score': boosted_score,
            'merged_count': len(group),
            'input_metrics': input_metrics,
            'output_metrics': output_metrics,
            'sub_insights': group,  # Keep originals for reference
            'direction': 'positive' if avg_correlation > 0 else 'negative'
        }
        
        return merged
    
    def _generate_descriptions(self, insights: List[Dict]) -> List[Dict]:
        """
        Generate natural language descriptions for insights
        Uses templates (can be enhanced with LLM later)
        """
        
        for insight in insights:
            insight['description'] = self._template_description(insight)
            insight['recommendation'] = self._template_recommendation(insight)
        
        return insights
    
    def _template_description(self, insight: Dict) -> str:
        """Generate description from template"""
        
        # Handle multi-output insights
        if insight['type'] == 'multi_output_insight':
            return self._template_multi_output_description(insight)
        
        # Handle merged insights
        if insight['type'] == 'merged_insight':
            return self._template_merged_description(insight)
        
        metric_a = self._humanize_metric(insight['metric_a'])
        metric_b = self._humanize_metric(insight['metric_b'])
        improvement = abs(insight['improvement_percent'])
        direction = insight.get('direction', 'positive')
        
        if insight['type'] == 'binary_comparison':
            if direction == 'positive':
                return f"You achieve {improvement:.0f}% better {metric_b} on days when you {metric_a}"
            else:
                return f"Your {metric_b} drops by {improvement:.0f}% on days when you {metric_a}"
        else:
            corr = insight['correlation']
            if corr > 0:
                return f"Higher {metric_a} correlates with {improvement:.0f}% better {metric_b}"
            else:
                return f"Higher {metric_a} correlates with {improvement:.0f}% lower {metric_b}"
    
    def _template_multi_output_description(self, insight: Dict) -> str:
        """Generate description for multi-output insights (workout affects mood, energy, productivity)"""
        
        input_base = self._humanize_metric(insight['metric_a'])
        top_effects = insight['top_effects']
        direction = insight['direction']
        
        # Build effect list
        effects_text = ", ".join([f"{improvement:.0f}% better {output}" for output, improvement in top_effects])
        
        if direction == 'positive':
            desc = f"On days when you {input_base}, you achieve: {effects_text}"
        else:
            desc = f"Higher {input_base} correlates with: {effects_text}"
        
        return desc
    
    def _template_merged_description(self, insight: Dict) -> str:
        """Generate description for merged insights"""
        
        input_base = self._humanize_metric(insight['metric_a'])
        output_base = self._humanize_metric(insight['metric_b'])
        improvement = abs(insight['improvement_percent'])
        direction = insight['direction']
        count = insight['merged_count']
        
        # Create comprehensive description
        if direction == 'positive':
            desc = f"Better {input_base} strongly correlates with {improvement:.0f}% better {output_base}"
        else:
            desc = f"Higher {input_base} correlates with {improvement:.0f}% lower {output_base}"
        
        # Add specifics if available
        if count > 1:
            desc += f" (found {count} related patterns)"
        
        return desc
    
    def _template_recommendation(self, insight: Dict) -> str:
        """Generate actionable recommendation"""
        
        # Handle multi-output insights
        if insight['type'] == 'multi_output_insight':
            metric_a = self._humanize_metric(insight['metric_a'])
            direction = insight['direction']
            top_effect = insight['top_effects'][0][0]  # Top affected metric
            
            if direction == 'positive':
                return f"Prioritize {metric_a} - it significantly improves your {top_effect} and overall performance"
            else:
                return f"Monitor your {metric_a} levels carefully - they impact multiple dimensions"
        
        # Handle merged insights
        if insight['type'] == 'merged_insight':
            metric_a = self._humanize_metric(insight['metric_a'])
            metric_b = self._humanize_metric(insight['metric_b'])
            direction = insight['direction']
            
            if direction == 'positive':
                return f"Prioritize improving your {metric_a} to boost {metric_b}"
            else:
                return f"Monitor your {metric_a} levels to maintain good {metric_b}"
        
        metric_a = self._humanize_metric(insight['metric_a'])
        metric_b = self._humanize_metric(insight['metric_b'])
        direction = insight.get('direction', 'positive')
        
        if insight['type'] == 'binary_comparison':
            if direction == 'positive':
                return f"Schedule {metric_a} on days when you need high {metric_b}"
            else:
                return f"Avoid {metric_a} before days requiring high {metric_b}, or reduce intensity"
        else:
            corr = insight['correlation']
            if corr > 0:
                return f"Increase {metric_a} to boost {metric_b}"
            else:
                return f"Reduce {metric_a} to improve {metric_b}"
    
    def _humanize_metric(self, metric: str) -> str:
        """Convert metric name to human-readable"""
        
        # Remove _avg, _max, _min suffixes
        metric = metric.replace('_avg', '').replace('_max', '').replace('_min', '')
        
        # Convert underscores to spaces
        metric = metric.replace('_', ' ')
        
        # Special cases
        replacements = {
            'completion rate': 'task completion',
            'tasks completed': 'completed tasks',
            'workout intensity': 'workout',
            'meditation duration': 'meditation time',
        }
        
        for old, new in replacements.items():
            if old in metric:
                metric = metric.replace(old, new)
        
        return metric
    
    def _get_reported_insights(self, user_id: int) -> Dict:
        """Get previously reported insights from database"""
        
        if not self.db:
            return {}
        
        # Query patterns table for user's insights
        query = """
            SELECT pattern_type, description, data 
            FROM patterns 
            WHERE user_id = ? AND pattern_type = 'insight'
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id,))
            results = cursor.fetchall()
        
        reported = {}
        for row in results:
            try:
                data = json.loads(row[2]) if isinstance(row[2], str) else row[2]
                if 'metric_a' in data:
                    # Handle both merged and simple insights
                    if data.get('type') in ['multi_output_insight', 'merged_insight']:
                        signature = f"{data['metric_a']}"
                    elif 'metric_b' in data:
                        signature = f"{data['metric_a']}→{data['metric_b']}"
                    else:
                        continue
                    
                    reported[signature] = data
            except Exception as e:
                continue
        
        return reported
    
    def _save_insights(self, insights: List[Dict], user_id: int):
        """Save insights to database as reported"""
        
        if not self.db:
            return
        
        for insight in insights:
            self.db.create_pattern(
                user_id=user_id,
                pattern_type='insight',
                description=insight['description'],
                confidence=insight['confidence'],
                data=insight
            )
