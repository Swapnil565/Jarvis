"""
=============================================================================
JARVIS 3.0 - RATE LIMITER [DAY 7 - TASK 2]
=============================================================================

PURPOSE:
--------
Protect API from abuse by limiting requests per user/IP address.
Prevents DDoS attacks, brute force attempts, and excessive API usage.

WHY DO WE NEED RATE LIMITING?
------------------------------
Problem: Users/bots can spam API with unlimited requests
Consequences:
  - Server overload and crashes
  - Database exhaustion
  - Increased costs (if using cloud)
  - Poor experience for legitimate users

Solution: Limit requests per time window
Example: "100 requests per minute per user"

RATE LIMITING ALGORITHMS:
--------------------------

1. FIXED WINDOW (Simple but has edge case)
   ```
   Window: 00:00 - 01:00 (1 hour)
   Limit: 100 requests
   
   Problem: User can make 100 requests at 00:59 
            and 100 more at 01:01 = 200 in 2 minutes!
   ```

2. SLIDING WINDOW (Better, more accurate) ✅
   ```
   Check last 60 seconds of requests
   If count < 100 → Allow
   If count >= 100 → Block with 429 status
   
   Advantage: No edge case, accurate limiting
   ```

3. TOKEN BUCKET (Allow bursts)
   ```
   Bucket capacity: 100 tokens
   Refill rate: 10 tokens/second
   
   Request consumes 1 token
   If tokens available → Allow
   If no tokens → Block
   
   Advantage: Allows temporary bursts
   ```

RATE LIMIT TIERS:
-----------------
Different endpoints need different limits:

PUBLIC ENDPOINTS (No auth):
- /health → 1000/minute (monitoring systems)
- /api/v1/auth/login → 5/minute (prevent brute force)
- /api/v1/auth/register → 3/minute (prevent spam accounts)

AUTHENTICATED ENDPOINTS:
- /api/events → 100/minute (normal usage)
- /api/events/parse → 50/minute (LLM calls are expensive)
- /api/stats → 200/minute (read-heavy, cached)
- /api/workflow/daily → 10/minute (heavy operation)

ADMIN ENDPOINTS:
- /api/tasks/trigger/* → 5/minute (manual triggers only)

RATE LIMIT RESPONSE:
--------------------
When limit exceeded, return:
```json
HTTP 429 Too Many Requests

{
    "error": "rate_limit_exceeded",
    "message": "Too many requests. Please try again later.",
    "retry_after": 45,  // Seconds until limit resets
    "limit": 100,
    "remaining": 0,
    "reset": 1699276800  // Unix timestamp
}
```

RATE LIMIT HEADERS:
-------------------
Add these headers to ALL responses:
- X-RateLimit-Limit: 100
- X-RateLimit-Remaining: 73
- X-RateLimit-Reset: 1699276800

This helps clients implement backoff strategies.

STORAGE OPTIONS:
----------------
Store rate limit counters in Redis (fast, supports TTL):

Key format: "rate_limit:{user_id}:{endpoint}:{window}"
Example: "rate_limit:123:/api/events:2024-01-15-10-30"

SLIDING WINDOW IMPLEMENTATION:
-------------------------------
Use Redis Sorted Set:
```
Key: "rate_limit:{user_id}:{endpoint}"
Value: Sorted set of timestamps

For each request:
1. Current time = now()
2. Window start = now() - 60 seconds
3. Remove old entries: ZREMRANGEBYSCORE key -inf window_start
4. Count remaining: ZCARD key
5. If count < limit:
     Add current request: ZADD key now() now()
     Allow request
   Else:
     Block with 429
```

BYPASS RATE LIMITS:
-------------------
Some users might need higher limits:
- Premium users: 500/minute
- Admin users: Unlimited
- Internal services: Unlimited

Check user tier before applying limits.

RATE LIMIT MONITORING:
----------------------
Track these metrics:
- Total requests blocked
- Requests per user
- Most rate-limited endpoints
- Peak usage times

DATA FLOW WITH RATE LIMITING:
------------------------------
┌──────────────┐
│   Client     │
└──────┬───────┘
       │ 1. API Request
       ▼
┌──────────────┐
│  Rate Limit  │
│  Middleware  │
└──────┬───────┘
       │ 2. Check Redis
       ▼
┌──────────────┐
│    Redis     │
│ (Counters)   │
└──────┬───────┘
       │
       ├──▶ Under limit → Allow → 3. Process request
       │
       └──▶ Over limit → Block → Return 429

INTEGRATION WITH FASTAPI:
--------------------------
Use dependency injection:
```python
from fastapi import Depends

@app.get("/api/events")
async def get_events(
    rate_limit: None = Depends(check_rate_limit(limit=100))
):
    return events
```

Or use decorator:
```python
from slowapi import Limiter

limiter = Limiter(key_func=get_user_id)

@app.get("/api/events")
@limiter.limit("100/minute")
async def get_events():
    return events
```

YOUR TASK:
----------
Implement these functions:

1. check_rate_limit(user_id: str, endpoint: str, limit: int, window: int)
   - Check if user exceeded rate limit
   - Return True if allowed, False if blocked
   - Store request in Redis

2. get_rate_limit_info(user_id: str, endpoint: str)
   - Return current rate limit status
   - Include: limit, remaining, reset_time

3. reset_rate_limit(user_id: str, endpoint: str)
   - Clear rate limit for debugging
   - Admin function only

4. RateLimitMiddleware (FastAPI middleware)
   - Apply rate limiting to all requests
   - Add rate limit headers to responses

DEPENDENCIES:
-------------
- redis: Store counters
- slowapi: FastAPI rate limiting library (optional)
- time: Timestamps

CONFIGURATION:
--------------
Store limits in config:
```python
RATE_LIMITS = {
    "/api/events": 100,
    "/api/events/parse": 50,
    "/api/stats": 200,
    "/api/v1/auth/login": 5
}
```
"""

# TODO: Import redis, time, slowapi
# TODO: Initialize Redis connection
# TODO: Implement check_rate_limit() function
# TODO: Implement get_rate_limit_info() function
# TODO: Implement RateLimitMiddleware class
# TODO: Define RATE_LIMITS configuration

# YOUR CODE STARTS HERE:
# ----------------------
from slowapi import Limiter 
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse

# Rate limit configuration per endpoint
RATE_LIMITS = {
    "/health": "1000/minute",
    "/api/v1/auth/login": "5/minute",
    "/api/v1/auth/register": "3/minute",
    "/api/events/parse": "50/minute",
    "/api/events": "100/minute",
    "/api/stats": "200/minute",
    "/api/workflow/daily": "10/minute",
}

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"]   # Global limit 
)

def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom 429 response with helpful error message"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": 60,  # Seconds until limit resets
            "limit": 100,
            "remaining": 0
        },
        headers={
            "Retry-After": "60"
        }
    )

def init_rate_limiter(app): 
    """Initialize rate limiter with FastAPI app"""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    
    @app.middleware("http")
    async def rate_limit_middleware(request, call_next):
        response = await call_next(request)
        return response

# ✅ Limiter → the engine
# ✅ key_func → identifies each client (default: IP address)
# ✅ default_limits → global rate limit


# HOW TO USE IN simple_main.py:
# ------------------------------
# from app.middleware.rate_limiter import init_rate_limiter, limiter
# 
# app = FastAPI(...)
# init_rate_limiter(app)
#
# @app.get("/api/events")
# @limiter.limit("100/minute")  # Specific limit for this endpoint
# async def get_events():
#     return events

