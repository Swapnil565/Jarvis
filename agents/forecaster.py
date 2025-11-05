"""
=============================================================================
JARVIS 3.0 - FORECASTER AGENT (Agent 3: Predictive Capacity Modeling) [DAY 4]
=============================================================================

PURPOSE:
--------
Agent 3 of the 4-agent system (TO BE IMPLEMENTED ON DAY 4). Predicts future
capacity, energy levels, and burnout risk based on historical patterns and
current trajectory. The "crystal ball" that forecasts where the user is headed.

RESPONSIBILITY (When Implemented):
-----------------------------------
- Generate 7-day capacity forecast (energy levels, productivity, burnout risk)
- Predict energy debt accumulation (unsustainable pace detection)
- Forecast crash dates (when burnout will likely occur)
- Calculate recovery time needed (how many rest days to recover)
- Model "what-if" scenarios (if continue current pace, if add rest day, etc.)
- Provide confidence scores for predictions
- Feed predictions to InterventionistAgent for recommendation generation

DATA FLOW (Historical Data → Forecasting Model → Predictions):
---------------------------------------------------------------
FORECASTING FLOW (Day 4 Implementation):
1. Triggered by: POST /api/forecast (manual) or scheduled Celery job (Day 6)
2. ForecasterAgent.generate_forecast(user_id) called
3. Fetch data:
   - Last 30 days of events from jarvis_db
   - Detected patterns from PatternDetectorAgent
   - Current energy/stress/activity levels
4. Build forecasting model:
   - Time series analysis (ARIMA/Prophet for trends)
   - Moving averages (energy baseline calculation)
   - Burnout scoring (weighted sum of fatigue indicators)
5. Generate predictions:
   - Daily capacity scores for next 7 days (0-10 scale)
   - Energy debt trajectory (cumulative fatigue)
   - Crash probability (% likelihood of burnout)
   - Optimal intervention timing (when to rest)
6. Return forecast dict with predictions + confidence scores

PREDICTION TYPES:
-----------------
1. CAPACITY FORECAST:
   - Daily energy levels for next 7 days
   - Predicted task completion capacity
   - Expected recovery curve after rest

2. ENERGY DEBT TRACKING:
   - Cumulative fatigue score (0-100)
   - Sustainable vs. unsustainable pace detection
   - Debt accumulation rate (how fast burning out)

3. CRASH PREDICTION:
   - Burnout probability (0-100%)
   - Predicted crash date (if current trajectory continues)
   - Severity forecast (minor slump vs. major crash)

4. RECOVERY MODELING:
   - How many rest days needed to recover
   - Optimal rest timing (when to take break)
   - Recovery curve (how fast energy will restore)

FORECASTING ALGORITHMS (Day 4):
--------------------------------
1. BASELINE CALCULATION:
   - 30-day moving average for energy/activity/mood
   - Identify personal "normal" levels

2. TREND ANALYSIS:
   - Linear regression for short-term trends (7 days)
   - Exponential smoothing for volatility adjustment

3. BURNOUT SCORING:
   - Weighted formula:
     burnout_score = (consecutive_work_days * 10) + 
                     (energy_below_baseline * 15) + 
                     (sleep_debt * 20) - 
                     (recovery_activities * 8)
   - Score > 70: High burnout risk
   - Score > 85: Critical burnout risk

4. CONFIDENCE SCORING:
   - Based on data availability (more data = higher confidence)
   - Pattern strength (stronger correlations = better predictions)
   - Recent data recency (last 7 days weighted higher)

EXAMPLE OUTPUT (Day 4):
-----------------------
```python
{
  "forecast": {
    "next_7_days": [
      {"date": "2025-06-16", "capacity": 7.5, "energy": 8.0, "burnout_risk": 15},
      {"date": "2025-06-17", "capacity": 6.8, "energy": 7.2, "burnout_risk": 25},
      {"date": "2025-06-18", "capacity": 5.5, "energy": 6.0, "burnout_risk": 45},
      {"date": "2025-06-19", "capacity": 3.2, "energy": 4.5, "burnout_risk": 75},  # CRASH PREDICTED
      {"date": "2025-06-20", "capacity": 2.0, "energy": 3.0, "burnout_risk": 90},
      {"date": "2025-06-21", "capacity": 5.0, "energy": 6.5, "burnout_risk": 60},  # With rest day
      {"date": "2025-06-22", "capacity": 7.0, "energy": 7.8, "burnout_risk": 30}
    ],
    "energy_debt": {
      "current": 65,
      "rate": "+8/day",
      "threshold": 80,
      "days_until_critical": 2
    },
    "crash_prediction": {
      "probability": 82,
      "predicted_date": "2025-06-19",
      "severity": "high",
      "confidence": 0.78
    },
    "recommendations": {
      "rest_days_needed": 2,
      "optimal_rest_date": "2025-06-18",
      "recovery_time": "3-4 days"
    }
  },
  "confidence": 0.78,
  "based_on_events": 180
}
```

DEPENDENCIES (Day 4):
---------------------
- base_agent.py: LLM client for forecast narration
- simple_jarvis_db.py: Fetch events/patterns for analysis
- pandas/numpy: Time series data manipulation
- statsmodels/prophet: Time series forecasting models

INTEGRATION POINTS:
-------------------
- Receives from: PatternDetectorAgent (detected patterns for better predictions)
- Feeds into: InterventionistAgent (forecasts → intervention urgency)
- Called by: simple_main.py POST /api/forecast endpoint (Day 4)
- Scheduled by: Celery job (daily forecast generation on Day 6)

STATUS: PLACEHOLDER - TO BE IMPLEMENTED ON DAY 4
"""

from .base_agent import BaseAgent
import statistics

# Optional advanced backends
try:
    import pandas as pd
    import numpy as np
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from statsmodels.tsa.arima.model import ARIMA
    HAS_ARIMA = True
except ImportError:
    HAS_ARIMA = False

try:
    from prophet import Prophet
    HAS_PROPHET = True
except ImportError:
    HAS_PROPHET = False


class ForecasterAgent(BaseAgent):
    """Agent 3: 
    Provides simple forecasting helpers (moving average, exponential
    smoothing) and a primitive burnout score used by the API endpoint.
    """

    def __init__(self):
        super().__init__()
        self.logger.info("ForecasterAgent initialized")
        # Tunable parameters
        self.lookback_days = 30
        self.forecast_days = 7
        self.alpha = 0.3  # smoothing factor for exponential smoothing

    # ----------------- numeric helpers -----------------
    def moving_average(self, series: list, window: int = 3) -> list:
        if not series or window <= 0:
            return []
        if len(series) < window:
            return [statistics.mean(series)] * len(series)
        ma = []
        for i in range(len(series)):
            start = max(0, i - window + 1)
            ma.append(statistics.mean(series[start:i+1]))
        return ma

    def exp_smoothing_forecast(self, series: list, alpha: float = None, steps: int = 1) -> list:
        """Simple exponential smoothing forecast: produce `steps` future points."""
        if alpha is None:
            alpha = self.alpha
        if not series:
            return [0.0] * steps
        s = series[0]
        for val in series:
            s = alpha * val + (1 - alpha) * s
        return [s] * steps

    def burnout_score(self, recent_energy: list, consecutive_work_days: int, sleep_debt: float = 0.0) -> float:
        """Compute a simple burnout score (0-100)."""
        if not recent_energy:
            return 0.0
        baseline = statistics.mean(recent_energy)
        last = recent_energy[-1]
        energy_deficit = max(0.0, baseline - last)
        score = (consecutive_work_days * 8) + (energy_deficit * 12) + (sleep_debt * 15)
        return max(0.0, min(100.0, score))

    def arima_forecast(self, series: list, steps: int = 7) -> list:
        """ARIMA forecast (optional, falls back to exp smoothing if unavailable)."""
        if not HAS_ARIMA or not HAS_PANDAS or len(series) < 10:
            return self.exp_smoothing_forecast(series, steps=steps)
        try:
            model = ARIMA(series, order=(1,1,1))
            fitted = model.fit()
            forecast = fitted.forecast(steps=steps)
            return forecast.tolist()
        except Exception:
            return self.exp_smoothing_forecast(series, steps=steps)

    def prophet_forecast(self, series: list, dates: list, steps: int = 7) -> list:
        """Prophet forecast (optional, falls back if unavailable)."""
        if not HAS_PROPHET or not HAS_PANDAS or len(series) < 10:
            return self.exp_smoothing_forecast(series, steps=steps)
        try:
            df = pd.DataFrame({'ds': pd.to_datetime(dates), 'y': series})
            model = Prophet(daily_seasonality=False, weekly_seasonality=False, yearly_seasonality=False)
            model.fit(df)
            future = model.make_future_dataframe(periods=steps)
            forecast = model.predict(future)
            return forecast['yhat'].tail(steps).tolist()
        except Exception:
            return self.exp_smoothing_forecast(series, steps=steps)

    # ----------------- orchestration -----------------
    async def generate_forecast(self, user_id: int, days: int = None) -> dict:
        """Generate a simple n-day forecast based on recent events.

        The forecast is lightweight: it builds a daily energy series from events
        (counts and feelings) and uses moving average + exponential smoothing to
        project the next `days` days. Also computes a burnout score.
        """
        from simple_jarvis_db import jarvis_db
        from agents.pattern_detector import pattern_detector

        days = days or self.forecast_days

        # Fetch recent events
        events = jarvis_db.get_events(user_id, limit=self.lookback_days)
        if not events:
            return {
                "forecast": [], 
                "confidence": 0.0, 
                "based_on_events": 0,
                "burnout_score": 0,
                "detected_patterns": {}
            }

        # Aggregate daily energy metric: start with zeros and add +1 for workout, +0 for task, -1 for low feeling
        daily = {}
        for e in events:
            day = e.get('timestamp', '')[:10]
            if not day:
                continue
            if day not in daily:
                daily[day] = {'score': 0.0, 'count': 0}
            val = 0.0
            if e.get('event_type') == 'workout':
                val += 1.0
            if e.get('event_type') == 'meditation':
                val += 0.8
            feeling = (e.get('feeling') or '').lower()
            if feeling in ('energized', 'great', 'focused'):
                val += 1.0
            if feeling in ('tired', 'exhausted', 'stressed'):
                val -= 1.0
            daily[day]['score'] += val
            daily[day]['count'] += 1

        # Build series sorted by date
        days_sorted = sorted(daily.keys())
        energy_series = [daily[d]['score'] / max(1, daily[d]['count']) for d in days_sorted]

        # Forecast using moving average and exponential smoothing (or advanced if available)
        ma = self.moving_average(energy_series, window=3)
        # Try ARIMA first if available, fallback to exponential smoothing
        if HAS_ARIMA and len(energy_series) >= 10:
            forecast_vals = self.arima_forecast(energy_series, steps=days)
        else:
            forecast_vals = self.exp_smoothing_forecast(energy_series, steps=days)

        # Burnout score: assume consecutive work days equals recent workout days streak
        consecutive_work_days = 0
        for d in reversed(days_sorted[-7:]):
            # if average > 0.5 consider it a work-like day
            if (daily[d]['score'] / max(1, daily[d]['count'])) > 0.5:
                consecutive_work_days += 1
            else:
                break

        sleep_debt = 0.0  # placeholder (not tracked yet)
        last7 = energy_series[-7:] if len(energy_series) >= 1 else energy_series
        bscore = self.burnout_score(last7, consecutive_work_days, sleep_debt)

        # Build result
        from datetime import date, timedelta
        last_date = date.fromisoformat(days_sorted[-1]) if days_sorted else date.today()
        next_days = []
        for i in range(1, days + 1):
            d = last_date + timedelta(days=i)
            val = forecast_vals[i - 1] if i - 1 < len(forecast_vals) else forecast_vals[-1]
            next_days.append({
                'date': d.isoformat(),
                'capacity': round(max(0.0, val * 5 + 5), 2),  # scale roughly to 0-10
                'energy': round(val, 3),
                'burnout_risk': round(bscore, 2)
            })

        confidence = min(1.0, len(energy_series) / float(self.lookback_days))

        # Fully async pattern detection call
        detected_patterns = await pattern_detector.detect_patterns(user_id)

        return {
            'forecast': next_days,
            'confidence': confidence,
            'based_on_events': len(energy_series),
            'burnout_score': bscore,
            'detected_patterns': detected_patterns
        }


# Global instance
forecaster = ForecasterAgent()
