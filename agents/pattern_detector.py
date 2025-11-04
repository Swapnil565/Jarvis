"""
=============================================================================
JARVIS 3.0 - PATTERN DETECTOR AGENT (Agent 2: Correlation Discovery) [DAY 3]
=============================================================================

PURPOSE:
--------
Agent 2 of the 4-agent system (TO BE IMPLEMENTED ON DAY 3). Analyzes historical
event data to discover meaningful correlations, trends, and anomalies across the
3 dimensions (physical, mental, spiritual). The "intelligence layer" that finds
hidden patterns in user behavior.

RESPONSIBILITY (When Implemented):
-----------------------------------
- Analyze events table for statistical correlations
- Detect positive patterns (workout → task completion boost)
- Detect negative patterns (overtraining → energy crash)
- Find optimal timing patterns (morning meditation → focused day)
- Identify anomalies (sudden activity drops, unusual behavior)
- Calculate confidence scores for pattern reliability
- Store patterns in patterns table via jarvis_db

DATA FLOW (Event Analysis → Pattern Detection → Storage):
----------------------------------------------------------
PATTERN DETECTION FLOW (Day 3 Implementation):
1. Scheduled job runs every 24 hours (Celery task on Day 6)
2. Or manual trigger: POST /api/insights/generate
3. PatternDetectorAgent.detect_patterns(user_id) called
4. Fetch user's events from jarvis_db.get_events()
5. Run statistical analysis:
   - Correlation: Do workouts correlate with task completion?
   - Frequency: How often does meditation → calm feeling?
   - Temporal: Are certain activities better at specific times?
   - Anomaly: Detect unusual deviations from baseline
6. For each significant pattern found:
   - Calculate confidence score (statistical significance)
   - Generate human-readable description
   - Create Pattern object with metadata
   - Call jarvis_db.create_pattern()
7. Return list of detected patterns

PATTERN TYPES TO DETECT:
-------------------------
1. CORRELATION PATTERNS:
   - "Workout days → 85% more tasks completed"
   - "Meditation → 60% reduction in stress reports"
   - "Less than 6h sleep → 3x more overwhelm"

2. TREND PATTERNS:
   - "Energy declining 15% over past 2 weeks"
   - "Task completion rate increasing 30% this month"
   - "Meditation frequency dropping (5/week → 2/week)"

3. TEMPORAL PATTERNS:
   - "Morning workouts → 40% more productive day"
   - "Evening meditation → better sleep quality"
   - "Workday task completion peaks at 10-11am"

4. ANOMALY PATTERNS:
   - "Sudden 70% drop in physical activity"
   - "Unusual energy spike (3 std deviations above mean)"
   - "Meditation streak broken after 45 days"

STATISTICAL METHODS (Day 3):
-----------------------------
- Pearson correlation coefficient for linear relationships
- Chi-square test for categorical associations
- Time series analysis for trend detection
- Z-score for anomaly detection
- Minimum sample size: 10-15 events for reliability

EXAMPLE IMPLEMENTATION (Day 3):
--------------------------------
```python
async def detect_patterns(self, user_id: int):
    # Fetch events
    events = jarvis_db.get_events(user_id, limit=1000)
    
    # Analyze workout → task correlation
    workout_days = [e for e in events if e['event_type'] == 'workout']
    task_days = [e for e in events if e['event_type'] == 'task']
    
    # Calculate correlation
    correlation = pearson_correlation(workout_days, task_days)
    
    if correlation > 0.7:  # Strong positive correlation
        pattern = {
            "pattern_type": "correlation",
            "description": f"Workout days → {correlation*100:.0f}% more tasks completed",
            "confidence": correlation,
            "data": {"coefficient": correlation, "sample_size": len(workout_days)}
        }
        jarvis_db.create_pattern(user_id, pattern)
    
    return detected_patterns
```

DEPENDENCIES (Day 3):
---------------------
- base_agent.py: LLM client for natural language descriptions
- simple_jarvis_db.py: Fetch events, store patterns
- pandas/numpy: Statistical analysis libraries
- scipy: Advanced correlation/significance testing

INTEGRATION POINTS:
-------------------
- Called by: simple_main.py POST /api/insights/generate endpoint (Day 3)
- Scheduled by: Celery background job (Day 6)
- Feeds into: ForecasterAgent (Day 4) for predictive modeling

STATUS: PLACEHOLDER - TO BE IMPLEMENTED ON DAY 3
"""

from .base_agent import BaseAgent

from typing import List, Dict, Any, Tuple
from collections import defaultdict, OrderedDict
from datetime import datetime
import math
import statistics

try:
   # Optional; provide better numeric tools when available
   import numpy as _np
except Exception:
   _np = None

from simple_jarvis_db import jarvis_db


class PatternDetectorAgent(BaseAgent):
   """Agent 2: Pattern Detector

   Implements lightweight statistical detectors for Day 3:
   - Pearson correlation between daily workout counts and completed task counts
   - Z-score based anomaly detection for sudden spikes/drops
   - Simple linear trend detection (slope over time)

   Notes:
   - This implementation avoids heavy external dependencies where possible and
     falls back to pure-Python calculations when numpy/scipy are not present.
   - Detected patterns are persisted to `jarvis_db` via `create_pattern`.
   """

   def __init__(self):
      super().__init__()
      # Tunable thresholds - adjusted for development sensitivity
      self.min_samples = 6
      self.correlation_threshold = 0.2  # lower threshold to surface more hypotheses
      self.anomaly_z_threshold = 1.5
      self.chi_square_threshold = 3.84  # ~p=0.05 for df=1
      self.logger.info("PatternDetectorAgent initialized")

   # ----------------- Utility helpers -----------------
   def _date_key(self, iso_ts: str) -> str:
      try:
         return iso_ts.split("T")[0]
      except Exception:
         try:
            return datetime.fromisoformat(iso_ts).date().isoformat()
         except Exception:
            return iso_ts

   def _events_to_daily_counts(self, events: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
      """Convert raw event rows to daily aggregated counts for event types.

      Returns a dict keyed by date (YYYY-MM-DD) mapping to counters like:
      { '2025-11-04': {'workout': 1, 'task_completed': 3, 'meditation': 0} }
      """
      daily = defaultdict(lambda: defaultdict(int))

      for e in events:
         ts = e.get('timestamp') or e.get('created_at') or datetime.utcnow().isoformat()
         day = self._date_key(ts)
         etype = e.get('event_type') or e.get('type')
         category = e.get('category')

         # Count workouts
         if etype == 'workout' or (category == 'physical' and etype):
            daily[day]['workout'] += 1

         # Count meditations
         if etype == 'meditation' or (category == 'spiritual' and etype == 'meditation'):
            daily[day]['meditation'] += 1

         # Count completed tasks (data.completed == True) or task events
         if etype == 'task' or (category == 'mental' and etype == 'task'):
            data = e.get('data') or {}
            # data may be dict or json string (but jarvis_db returns dicts)
            try:
               completed = bool(data.get('completed'))
            except Exception:
               completed = False

            if completed:
               daily[day]['task_completed'] += 1
            else:
               # count as task even if not marked complete (optional)
               daily[day]['task_uncompleted'] += 1

      # Ensure integer zeros exist for common keys
      for day_counts in daily.values():
         for k in ('workout', 'task_completed', 'meditation'):
            day_counts.setdefault(k, 0)

      # Return an ordered dict by date ascending
      ordered = OrderedDict(sorted(daily.items()))
      return ordered

   def _to_aligned_lists(self, daily: Dict[str, Dict[str, int]], key_x: str, key_y: str) -> Tuple[List[float], List[float]]:
      xs, ys = [], []
      for day, counts in daily.items():
         xs.append(float(counts.get(key_x, 0)))
         ys.append(float(counts.get(key_y, 0)))
      return xs, ys

   def _pearson(self, x: List[float], y: List[float]) -> float:
      """Compute Pearson correlation coefficient (r). Falls back to pure-Python.

      Returns 0.0 if not enough variance or samples.
      """
      if not x or not y or len(x) != len(y) or len(x) < 2:
         return 0.0

      n = len(x)
      try:
         if _np is not None:
            rx = _np.array(x); ry = _np.array(y)
            if rx.std() == 0 or ry.std() == 0:
               return 0.0
            return float(_np.corrcoef(rx, ry)[0, 1])
      except Exception:
         pass

      # pure python
      mean_x = statistics.mean(x)
      mean_y = statistics.mean(y)
      num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
      den_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
      den_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
      denom = den_x * den_y
      if denom == 0:
         return 0.0
      return num / denom

   def _z_score(self, values: List[float]) -> List[float]:
      if not values:
         return []
      mean_v = statistics.mean(values)
      stdev_v = statistics.pstdev(values) if len(values) > 1 else 0.0
      if stdev_v == 0:
         return [0.0 for _ in values]
      return [(v - mean_v) / stdev_v for v in values]

   def _linear_trend_slope(self, values: List[float]) -> float:
      """Compute simple linear slope (least-squares) of values over time.
      Returns slope per-step. Falls back if not enough samples.
      """
      if len(values) < 2:
         return 0.0
      n = len(values)
      xs = list(range(n))
      mean_x = statistics.mean(xs)
      mean_y = statistics.mean(values)
      num = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(xs, values))
      den = sum((xi - mean_x) ** 2 for xi in xs)
      if den == 0:
         return 0.0
      return num / den

   def _chi_square_binary(self, x: List[int], y: List[int]) -> float:
      """Compute chi-square statistic for two binary series (lists of 0/1).

      Returns chi2 value. Does not compute p-value; caller can compare against
      a threshold (e.g., 3.84 for p=0.05, df=1).
      """
      if len(x) != len(y) or len(x) == 0:
         return 0.0
      a = b = c = d = 0
      for xi, yi in zip(x, y):
         if xi and yi:
            a += 1
         elif xi and not yi:
            b += 1
         elif not xi and yi:
            c += 1
         else:
            d += 1

      obs = [a, b, c, d]
      total = sum(obs)
      if total == 0:
         return 0.0

      # Expected counts under independence
      row1 = a + b
      row2 = c + d
      col1 = a + c
      col2 = b + d

      # If any expected cell is zero, chi2 not defined
      exp = []
      for r in (row1, row2):
         for cval in (col1, col2):
            exp.append((r * cval) / total if total else 0)

      chi2 = 0.0
      for o, e in zip(obs, exp):
         if e > 0:
            chi2 += (o - e) ** 2 / e

      return chi2

   # ----------------- Detection routines -----------------
   async def detect_patterns(self, user_id: int, limit: int = 365) -> List[Dict[str, Any]]:
      """Main orchestrator: fetch events, run detectors, persist and return patterns."""
      detected = []

      # Fetch recent events from DB (descending by timestamp)
      events = jarvis_db.get_events(user_id, limit=limit)
      if not events or len(events) < self.min_samples:
         self.logger.info("Not enough events to detect patterns (need at least %d)", self.min_samples)
         return detected

      # Aggregate daily counts
      daily = self._events_to_daily_counts(events)

      # Prepare aligned series
      workout_series, task_series = self._to_aligned_lists(daily, 'workout', 'task_completed')

      # Correlation detection: Workout days -> Task completion
      if len(workout_series) >= self.min_samples:
         corr = self._pearson(workout_series, task_series)
         self.logger.debug("Workout-task Pearson r=%.4f (n=%d)", corr, len(workout_series))
         if abs(corr) >= self.correlation_threshold:
            confidence = min(1.0, abs(corr))
            pct = abs(corr) * 100
            direction = 'more' if corr > 0 else 'fewer'
            description = f"Workout frequency correlates with {direction} tasks completed (r={corr:.2f})"
            pdata = {
               'coefficient': corr,
               'sample_size': len(workout_series),
               'series': {'workout': workout_series, 'tasks': task_series}
            }
            pattern_id = jarvis_db.create_pattern(user_id, 'correlation', description, confidence, pdata)
            detected.append({'id': pattern_id, 'type': 'correlation', 'description': description, 'confidence': confidence, 'data': pdata})

      # Chi-square categorical detector: workout presence vs 'energized' feeling
      # Build binary series for workout presence and energized feeling per day
      feelings_daily = defaultdict(lambda: defaultdict(int))
      for e in events:
         day = self._date_key(e.get('timestamp') or e.get('created_at') or datetime.utcnow().isoformat())
         feeling = (e.get('feeling') or '').lower() if e.get('feeling') else ''
         if feeling:
            feelings_daily[day][feeling] += 1

      energized_series = []
      workout_presence = []
      for day, counts in daily.items():
         workout_presence.append(1 if counts.get('workout', 0) > 0 else 0)
         energized_series.append(1 if feelings_daily.get(day, {}).get('energized', 0) > 0 else 0)

      chi2 = self._chi_square_binary(workout_presence, energized_series)
      self.logger.debug('Chi-square workout vs energized = %.3f', chi2)
      if chi2 >= self.chi_square_threshold and sum(workout_presence) >= 2:
         description = f"Association detected between workout days and feeling 'energized' (chi2={chi2:.2f})"
         confidence = min(1.0, chi2 / (self.chi_square_threshold * 4))
         pdata = {'chi2': chi2, 'sample_size': len(workout_presence)}
         pattern_id = jarvis_db.create_pattern(user_id, 'association', description, confidence, pdata)
         detected.append({'id': pattern_id, 'type': 'association', 'description': description, 'confidence': confidence, 'data': pdata})

      # Trend detection (simple slope) for workouts
      slope = self._linear_trend_slope(workout_series)
      if abs(slope) > 0.01:  # arbitrary small slope threshold
         direction = 'increasing' if slope > 0 else 'decreasing'
         description = f"Workout frequency is {direction} (slope={slope:.3f} per day)"
         confidence = min(1.0, min(1.0, abs(slope) * 10))
         pdata = {'slope': slope, 'series': {'workout': workout_series}}
         pattern_id = jarvis_db.create_pattern(user_id, 'trend', description, confidence, pdata)
         detected.append({'id': pattern_id, 'type': 'trend', 'description': description, 'confidence': confidence, 'data': pdata})

      # Moving-average change detection (window=3)
      try:
         window = 3
         if len(workout_series) >= window * 2:
            def ma(series, w):
               return [statistics.mean(series[i - w + 1:i + 1]) for i in range(w - 1, len(series))]

            ma_vals = ma(workout_series, window)
            # compare last MA to previous MA
            if len(ma_vals) >= 2:
               delta = ma_vals[-1] - ma_vals[-2]
               if abs(delta) >= 0.5:
                  desc = f"Workout moving average changed by {delta:.2f} (window={window})"
                  conf = min(1.0, abs(delta) / 3.0)
                  pdata = {'moving_average_delta': delta, 'window': window}
                  pid = jarvis_db.create_pattern(user_id, 'trend_ma', desc, conf, pdata)
                  detected.append({'id': pid, 'type': 'trend_ma', 'description': desc, 'confidence': conf, 'data': pdata})
      except Exception:
         self.logger.exception('Moving-average detection failed')

      # Anomaly detection: check last day's z-score for workouts and tasks
      workout_z = self._z_score(workout_series)
      task_z = self._z_score(task_series)
      if workout_z:
         last_z = workout_z[-1]
         if abs(last_z) >= self.anomaly_z_threshold:
            description = f"Anomaly in workouts: last day z={last_z:.2f}"
            confidence = min(1.0, abs(last_z) / 3.0)
            pdata = {'z_score': last_z, 'series': {'workout': workout_series}}
            pattern_id = jarvis_db.create_pattern(user_id, 'anomaly', description, confidence, pdata)
            detected.append({'id': pattern_id, 'type': 'anomaly', 'description': description, 'confidence': confidence, 'data': pdata})

      if task_z:
         last_z = task_z[-1]
         if abs(last_z) >= self.anomaly_z_threshold:
            description = f"Anomaly in tasks completed: last day z={last_z:.2f}"
            confidence = min(1.0, abs(last_z) / 3.0)
            pdata = {'z_score': last_z, 'series': {'tasks': task_series}}
            pattern_id = jarvis_db.create_pattern(user_id, 'anomaly', description, confidence, pdata)
            detected.append({'id': pattern_id, 'type': 'anomaly', 'description': description, 'confidence': confidence, 'data': pdata})

      self.logger.info("Pattern detection finished, found %d patterns for user %s", len(detected), user_id)
      return detected


# Global instance
pattern_detector = PatternDetectorAgent()
