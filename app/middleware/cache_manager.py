"""
=============================================================================
JARVIS 3.0 - REDIS CACHE MANAGER [DAY 7 - TASK 1]
=============================================================================

PURPOSE:
--------
Centralized Redis caching layer to speed up API responses by 100x.
Instead of hitting the database every time, we store frequently accessed
data in Redis (in-memory) and serve it instantly.

WHY DO WE NEED CACHING?
------------------------
Problem: Database queries are SLOW (100-500ms each)
Solution: Cache results in Redis (in-memory, 1-5ms response time)

Example:
- Without cache: User requests stats → DB query (500ms) → Response
- With cache: User requests stats → Redis lookup (5ms) → Response
- Speed improvement: 100x faster!

CACHING STRATEGIES:
-------------------

1. CACHE-ASIDE (Read-Through) - MOST COMMON ✅
   ```
   def get_user_stats(user_id):
       # Step 1: Check cache first
       cached = cache.get(f"stats:{user_id}")
       if cached:
           return cached  # ⚡ Fast path (5ms)
       
       # Step 2: Cache miss - query database
       stats = db.get_stats(user_id)  # 🐌 Slow (500ms)
       
       # Step 3: Store in cache for next time
       cache.set(f"stats:{user_id}", stats, ttl=300)
       
       return stats
   ```

2. WRITE-THROUGH (Update cache on write)
   ```
   def update_event(event_id, data):
       # Step 1: Update database
       db.update_event(event_id, data)
       
       # Step 2: Update cache immediately
       cache.set(f"event:{event_id}", data, ttl=3600)
   ```

3. CACHE INVALIDATION (Delete stale cache)
   ```
   def create_event(user_id, data):
       # Step 1: Create in database
       event_id = db.create_event(user_id, data)
       
       # Step 2: Invalidate related caches
       cache.delete(f"stats:{user_id}")  # Stats changed
       cache.delete(f"events:{user_id}")  # Event list changed
   ```

CACHE KEY NAMING CONVENTION:
-----------------------------
Use descriptive, hierarchical keys:
- User stats: "stats:user:{user_id}"
- User events: "events:user:{user_id}"
- Patterns: "patterns:user:{user_id}"
- Forecast: "forecast:user:{user_id}:7days"
- Interventions: "interventions:user:{user_id}"

TTL (Time-To-Live) GUIDELINES:
-------------------------------
How long should we keep cached data?

- User stats: 5 minutes (300s) - Changes frequently
- Patterns: 1 hour (3600s) - Changes less often
- Forecasts: 6 hours (21600s) - Generated daily
- User profile: 24 hours (86400s) - Rarely changes
- System health: 1 minute (60s) - Need fresh data

WHEN TO INVALIDATE CACHE:
--------------------------
Clear cache when underlying data changes:

Event created → Invalidate:
  - stats:{user_id}
  - events:{user_id}
  - today:{user_id}

Pattern detected → Invalidate:
  - patterns:{user_id}

Forecast generated → Invalidate:
  - forecast:{user_id}

DATA FLOW WITH CACHE:
---------------------
┌──────────────┐
│   Client     │
└──────┬───────┘
       │ 1. GET /api/stats
       ▼
┌──────────────┐
│   FastAPI    │
└──────┬───────┘
       │ 2. Check cache
       ▼
┌──────────────┐
│    Redis     │─────▶ Cache HIT (5ms) → Return ✅
│   (Cache)    │
└──────┬───────┘
       │ Cache MISS
       │ 3. Query DB
       ▼
┌──────────────┐
│   SQLite     │
│  (Database)  │
└──────┬───────┘
       │ 4. Return data (500ms)
       ▼
┌──────────────┐
│    Redis     │ 5. Store in cache
│   (Cache)    │    for next time
└──────────────┘

CACHE PERFORMANCE METRICS:
---------------------------
Monitor these metrics:
- Cache Hit Rate: % of requests served from cache (target: >80%)
- Cache Miss Rate: % of requests going to DB (target: <20%)
- Average Response Time: With cache vs without (target: 10x faster)
- Cache Memory Usage: Keep under Redis memory limit

REDIS DATA TYPES FOR CACHING:
------------------------------
1. STRING (most common):
   cache.set("key", json.dumps(data))
   cache.get("key") → json.loads()

2. HASH (for objects):
   cache.hset("user:123", "name", "John")
   cache.hset("user:123", "email", "john@example.com")

3. LIST (for ordered data):
   cache.lpush("recent_events", event_id)

4. SET (for unique items):
   cache.sadd("active_users", user_id)

5. SORTED SET (for rankings):
   cache.zadd("leaderboard", {user_id: score})

YOUR TASK:
----------
Implement these functions:

1. get(key: str) → dict | None
   - Get cached data by key
   - Return None if not found

2. set(key: str, value: dict, ttl: int = 3600)
   - Store data in cache with expiration
   - Serialize dict to JSON string

3. delete(key: str)
   - Remove specific cache entry
   - Use when data changes

4. invalidate_user_cache(user_id: int)
   - Clear ALL cache for a user
   - Use after major changes

5. get_cache_stats() → dict
   - Return cache hit/miss statistics
   - For monitoring dashboard

DEPENDENCIES:
-------------
- redis: Python Redis client
- json: Serialize/deserialize Python objects

INTEGRATION:
------------
Used by: simple_main.py (API endpoints)
Uses: Redis (port 6379)
"""

# TODO: Import redis and json
# TODO: Initialize Redis connection
# TODO: Implement get() function
# TODO: Implement set() function
# TODO: Implement delete() function
# TODO: Implement invalidate_user_cache() function
# TODO: Implement get_cache_stats() function

# YOUR CODE STARTS HERE:
# ----------------------

import redis
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("cache")

# Initialize Redis connection
# Make sure Redis is running: redis-server
try:
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,  # Use database 0 for cache (database 1 used by Celery for results)
        decode_responses=True,  # Automatically decode bytes to strings
        socket_timeout=5,
        socket_connect_timeout=5
    )
    # Test connection
    redis_client.ping()
    logger.info("✅ Redis cache connected successfully")
except redis.ConnectionError:
    logger.warning("⚠️ Redis not available - caching disabled")
    redis_client = None

# Cache statistics
cache_hits = 0
cache_misses = 0


def get(key: str) -> Optional[Dict[str, Any]]:
    """
    Get cached data by key
    
    Args:
        key: Cache key (e.g., "stats:user:123")
    
    Returns:
        dict if found, None if not found or Redis unavailable
    """
    global cache_hits, cache_misses
    
    if not redis_client:
        return None
    
    try:
        data = redis_client.get(key)
        if data:
            cache_hits += 1
            logger.debug(f"✅ Cache HIT: {key}")
            return json.loads(data)
        else:
            cache_misses += 1
            logger.debug(f"❌ Cache MISS: {key}")
            return None
    except Exception as e:
        logger.error(f"Cache get error for key {key}: {e}")
        cache_misses += 1
        return None


def set(key: str, value: Dict[str, Any], ttl: int = 3600) -> bool:
    """
    Store data in cache with expiration
    
    Args:
        key: Cache key
        value: Data to cache (will be JSON serialized)
        ttl: Time-to-live in seconds (default: 1 hour)
    
    Returns:
        True if successful, False otherwise
    """
    if not redis_client:
        return False
    
    try:
        redis_client.setex(key, ttl, json.dumps(value))
        logger.debug(f"✅ Cache SET: {key} (TTL: {ttl}s)")
        return True
    except Exception as e:
        logger.error(f"Cache set error for key {key}: {e}")
        return False


def delete(key: str) -> bool:
    """
    Remove specific cache entry
    
    Args:
        key: Cache key to delete
    
    Returns:
        True if deleted, False otherwise
    """
    if not redis_client:
        return False
    
    try:
        result = redis_client.delete(key)
        logger.debug(f"✅ Cache DELETE: {key}")
        return bool(result)
    except Exception as e:
        logger.error(f"Cache delete error for key {key}: {e}")
        return False


def invalidate_user_cache(user_id: int) -> bool:
    """
    Clear ALL cache entries for a specific user
    
    Args:
        user_id: User ID
    
    Returns:
        True if successful, False otherwise
    
    Example:
        When user creates new event, invalidate their stats/events cache
    """
    if not redis_client:
        return False
    
    try:
        # Find all keys containing this user_id
        patterns = [
            f"stats:user:{user_id}*",
            f"events:user:{user_id}*",
            f"patterns:user:{user_id}*",
            f"forecast:user:{user_id}*",
            f"interventions:user:{user_id}*",
            f"today:user:{user_id}*"
        ]
        
        deleted_count = 0
        for pattern in patterns:
            keys = redis_client.keys(pattern)
            if keys:
                deleted_count += redis_client.delete(*keys)
        
        logger.info(f"✅ Invalidated {deleted_count} cache entries for user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Cache invalidation error for user {user_id}: {e}")
        return False


def get_cache_stats() -> Dict[str, Any]:
    """
    Return cache hit/miss statistics
    
    Returns:
        dict with cache statistics
    """
    total_requests = cache_hits + cache_misses
    hit_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0
    
    stats = {
        "cache_hits": cache_hits,
        "cache_misses": cache_misses,
        "total_requests": total_requests,
        "hit_rate_percent": round(hit_rate, 2),
        "redis_connected": redis_client is not None
    }
    
    # Get Redis info if available
    if redis_client:
        try:
            info = redis_client.info("stats")
            stats["redis_total_commands"] = info.get("total_commands_processed", 0)
            stats["redis_keyspace_hits"] = info.get("keyspace_hits", 0)
            stats["redis_keyspace_misses"] = info.get("keyspace_misses", 0)
        except Exception as e:
            logger.error(f"Error getting Redis stats: {e}")
    
    return stats


def clear_all_cache() -> bool:
    """
    Clear ALL cache entries (use with caution!)
    
    Returns:
        True if successful, False otherwise
    """
    if not redis_client:
        return False
    
    try:
        redis_client.flushdb()
        logger.warning("⚠️ ALL cache cleared")
        return True
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        return False


# HOW TO USE IN simple_main.py:
# ------------------------------
# from app.middleware.cache_manager import get, set, delete, invalidate_user_cache
#
# @app.get("/api/stats")
# async def get_stats(user_id: int):
#     # Check cache first
#     cache_key = f"stats:user:{user_id}"
#     cached = get(cache_key)
#     if cached:
#         return cached  # Fast! (5ms)
#     
#     # Cache miss - query database
#     stats = jarvis_db.get_stats(user_id)  # Slow (500ms)
#     
#     # Store in cache for 5 minutes
#     set(cache_key, stats, ttl=300)
#     
#     return stats
#
# @app.post("/api/events")
# async def create_event(event: Event, user_id: int):
#     event_id = jarvis_db.create_event(...)
#     
#     # Invalidate user's cache since data changed
#     invalidate_user_cache(user_id)
#     
#     return {"id": event_id}

