"""
=============================================================================
JARVIS 3.0 - DATABASE OPTIMIZER [DAY 7 - TASK 3]
=============================================================================

PURPOSE:
--------
Optimize database performance through indexing, query optimization,
and connection pooling. Make database queries 10-100x faster.

WHY DO WE NEED DATABASE OPTIMIZATION?
--------------------------------------
Problem: Full table scans are SLOW
Example: Finding events for user_id=123

WITHOUT INDEX:
- SQLite scans EVERY row in events table
- 100,000 events = scan 100,000 rows
- Time: 500ms

WITH INDEX:
- SQLite uses B-tree index
- Direct lookup to matching rows
- Time: 5ms (100x faster!)

WHAT ARE INDEXES?
-----------------
Think of a book:
- Without index: Read every page to find "Celery" (slow)
- With index: Check index at back, jump to page 42 (fast)

Database index:
- Data structure (B-tree) that maps column values to row locations
- Trade-off: Faster reads, slower writes (must update index)

WHEN TO ADD INDEXES:
--------------------
Add index on columns used in:
1. WHERE clauses (filtering)
   ```sql
   SELECT * FROM events WHERE user_id = 123
   → CREATE INDEX idx_events_user_id ON events(user_id);
   ```

2. JOIN conditions
   ```sql
   SELECT * FROM events e JOIN users u ON e.user_id = u.id
   → CREATE INDEX idx_events_user_id ON events(user_id);
   ```

3. ORDER BY clauses (sorting)
   ```sql
   SELECT * FROM events WHERE user_id = 123 ORDER BY timestamp DESC
   → CREATE INDEX idx_events_user_timestamp ON events(user_id, timestamp);
   ```

4. Unique constraints
   ```sql
   → CREATE UNIQUE INDEX idx_users_email ON users(email);
   ```

WHEN NOT TO INDEX:
------------------
Don't index:
- Small tables (<1000 rows) - full scan is fast enough
- Columns rarely used in queries
- Columns with low cardinality (few unique values)
  Example: gender (only 2-3 values) - index won't help much
- Write-heavy tables - indexes slow down INSERTs

TYPES OF INDEXES:
-----------------
1. SINGLE COLUMN INDEX (most common)
   ```sql
   CREATE INDEX idx_events_user_id ON events(user_id);
   ```

2. COMPOSITE INDEX (multiple columns)
   ```sql
   CREATE INDEX idx_events_user_timestamp 
   ON events(user_id, timestamp);
   ```
   Use for queries with multiple WHERE conditions

3. UNIQUE INDEX (enforce uniqueness)
   ```sql
   CREATE UNIQUE INDEX idx_users_email ON users(email);
   ```
   Faster than UNIQUE constraint

4. PARTIAL INDEX (filter condition)
   ```sql
   CREATE INDEX idx_events_physical 
   ON events(user_id) 
   WHERE category = 'physical';
   ```
   Smaller index, faster lookups

JARVIS DATABASE INDEXES TO CREATE:
-----------------------------------

EVENTS TABLE (most queried):
```sql
-- User's events
CREATE INDEX idx_events_user_id ON events(user_id);

-- User's events by date
CREATE INDEX idx_events_user_timestamp 
ON events(user_id, timestamp DESC);

-- Events by category
CREATE INDEX idx_events_user_category 
ON events(user_id, category);

-- Recent events (for cleanup)
CREATE INDEX idx_events_timestamp ON events(timestamp);
```

PATTERNS TABLE:
```sql
-- User's patterns
CREATE INDEX idx_patterns_user_id ON patterns(user_id);

-- Active patterns
CREATE INDEX idx_patterns_user_active 
ON patterns(user_id) 
WHERE is_active = 1;

-- Pattern lookup by type
CREATE INDEX idx_patterns_user_type 
ON patterns(user_id, pattern_type);
```

INTERVENTIONS TABLE:
```sql
-- User's interventions
CREATE INDEX idx_interventions_user_id ON interventions(user_id);

-- Unacknowledged interventions
CREATE INDEX idx_interventions_user_pending 
ON interventions(user_id) 
WHERE acknowledged = 0;

-- Interventions by priority
CREATE INDEX idx_interventions_user_priority 
ON interventions(user_id, priority DESC);
```

FORECASTS TABLE:
```sql
-- User's forecasts
CREATE INDEX idx_forecasts_user_id ON forecasts(user_id);

-- Latest forecast
CREATE INDEX idx_forecasts_user_date 
ON forecasts(user_id, forecast_date DESC);
```

USERS TABLE:
```sql
-- Unique email for login
CREATE UNIQUE INDEX idx_users_email ON users(email);

-- User ID lookup (already primary key, no need)
```

QUERY OPTIMIZATION TECHNIQUES:
-------------------------------

1. USE EXPLAIN QUERY PLAN
   ```sql
   EXPLAIN QUERY PLAN
   SELECT * FROM events WHERE user_id = 123;
   
   Result:
   SCAN TABLE events  ❌ Slow (no index)
   
   vs
   
   SEARCH TABLE events USING INDEX idx_events_user_id ✅ Fast
   ```

2. SELECT ONLY NEEDED COLUMNS
   ```sql
   -- Bad (slow)
   SELECT * FROM events WHERE user_id = 123;
   
   -- Good (fast)
   SELECT id, timestamp, event_type FROM events WHERE user_id = 123;
   ```

3. LIMIT RESULTS
   ```sql
   -- Bad (returns all rows)
   SELECT * FROM events WHERE user_id = 123;
   
   -- Good (returns only needed rows)
   SELECT * FROM events WHERE user_id = 123 LIMIT 100;
   ```

4. USE COVERING INDEXES
   ```sql
   -- Query needs: user_id, timestamp, event_type
   CREATE INDEX idx_events_covering 
   ON events(user_id, timestamp, event_type);
   
   -- SQLite can answer from index alone (no table lookup!)
   ```

5. AVOID OR IN WHERE CLAUSE
   ```sql
   -- Bad (slow)
   SELECT * FROM events WHERE user_id = 123 OR user_id = 456;
   
   -- Good (fast)
   SELECT * FROM events WHERE user_id IN (123, 456);
   ```

CONNECTION POOLING:
-------------------
Reuse database connections instead of creating new ones:

WITHOUT POOLING:
- Each request: Open connection (10ms) → Query (5ms) → Close (5ms)
- Total: 20ms per request
- 100 requests = 2000ms overhead!

WITH POOLING:
- First request: Open connection (10ms) → Keep open
- Next requests: Reuse connection → Query (5ms)
- Total: 5ms per request
- 100 requests = 510ms (4x faster!)

VACUUM COMMAND:
---------------
SQLite fragmentation over time:
```sql
-- Compact database, rebuild indexes
VACUUM;

-- Analyze statistics for query optimizer
ANALYZE;
```

Run monthly for optimal performance.

MONITORING QUERIES:
-------------------
Track slow queries:
```python
def log_slow_query(query, duration, threshold=100):
    if duration > threshold:
        logger.warning(f"SLOW QUERY ({duration}ms): {query}")
```

YOUR TASK:
----------
Implement these functions:

1. create_indexes()
   - Create all indexes defined above
   - Run on database initialization
   - Skip if indexes already exist

2. analyze_query_performance(query: str)
   - Use EXPLAIN QUERY PLAN
   - Return optimization suggestions

3. vacuum_database()
   - Run VACUUM command
   - Rebuild indexes
   - Schedule monthly

4. get_table_stats()
   - Return row counts, index usage
   - For monitoring

5. optimize_query(query: str)
   - Suggest index improvements
   - Detect missing indexes

INTEGRATION:
------------
Run create_indexes() on:
- First app startup
- After database migrations
- After restoring from backup

TESTING PERFORMANCE:
--------------------
Before and after benchmark:
```python
import time

# Before optimization
start = time.time()
result = db.execute("SELECT * FROM events WHERE user_id = 123")
print(f"Without index: {time.time() - start:.3f}s")

# Add index
db.execute("CREATE INDEX idx_events_user_id ON events(user_id)")

# After optimization
start = time.time()
result = db.execute("SELECT * FROM events WHERE user_id = 123")
print(f"With index: {time.time() - start:.3f}s")
```

DEPENDENCIES:
-------------
- sqlite3: Database connection
- logging: Log slow queries

STATUS: TO BE IMPLEMENTED
"""

# TODO: Import sqlite3
# TODO: Implement create_indexes() function
# TODO: Implement analyze_query_performance() function
# TODO: Implement vacuum_database() function
# TODO: Implement get_table_stats() function
# TODO: Add to simple_jarvis_db.py initialization

# YOUR CODE STARTS HERE:
# ----------------------


import sqlite3
import time 
import logging 

logger = logging.getLogger("db_optimizer")
logger.setLevel(logging.INFO)

def create_indexes(db: sqlite3.Connection):
    cursor = db.cursor()

    indexes = [
        # EVENTS TABLE
        "CREATE INDEX IF NOT EXISTS idx_events_user_id ON events(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_events_user_timestamp ON events(user_id, timestamp DESC);",
        "CREATE INDEX IF NOT EXISTS idx_events_user_category ON events(user_id, category);",
        "CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events(timestamp);",

        # PATTERNS TABLE
        "CREATE INDEX IF NOT EXISTS idx_patterns_user_id ON patterns(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_patterns_user_active ON patterns(user_id) WHERE is_active = 1;",
        "CREATE INDEX IF NOT EXISTS idx_patterns_user_type ON patterns(user_id, pattern_type);",

        # INTERVENTIONS TABLE
        "CREATE INDEX IF NOT EXISTS idx_interventions_user_id ON interventions(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_interventions_user_pending ON interventions(user_id) WHERE acknowledged = 0;",
        "CREATE INDEX IF NOT EXISTS idx_interventions_user_priority ON interventions(user_id, priority DESC);",

        # FORECASTS TABLE
        "CREATE INDEX IF NOT EXISTS idx_forecasts_user_id ON forecasts(user_id);",
        "CREATE INDEX IF NOT EXISTS idx_forecasts_user_date ON forecasts(user_id, forecast_date DESC);",

        # USERS TABLE
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email);",
    ]


    for index_sql in indexes: 
        cursor.execute(index_sql)
    
    db.commit()
    logger.info("✅ All indexes created successfully")

def analyze_query_performance(db: sqlite3.Connection, query: str):
    cursor = db.cursor()
    cursor.execute(f"EXPLAIN QUERY PLAN {query}")
    plan = cursor.fetchall()

    suggestions = []

    plan_text = "\n".join(str(p) for p in plan)

    if "SCAN" in plan_text.upper():
        suggestions.append("Full table scan detected - add an index.")
    else: 
        suggestions.append("using index - query optimizer")

    return {
        "query_plan": plan_text,
        "suggestions": suggestions
    }


def vacuum_database(db: sqlite3.Connection):
    cursor = db.cursor()
    cursor.execute("VACUUM;")
    cursor.execute("ANALYZE;")  # Updates index statistics
    db.commit()
    logger.info("✅ VACUUM + ANALYZE completed — DB compacted & optimized.")


def get_table_stats(db: sqlite3.Connection): 
    cursor = db.cursor()

    tables = ["events", "patterns", "interventions", "users"]
    stats = {}

    for table in tables: 
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_count = cursor.fetchone()[0]
            stats[table] = {"rows": row_count}
        except sqlite3.OperationalError:
            stats[table] = {"rows": 0, "error": "Table doesn't exist"}
    
    return stats

def optimize_query(db: sqlite3.Connection, query: str):
    """Automatically suggests missing indexes."""
    analysis = analyze_query_performance(db, query)
    plan = analysis["query_plan"]

    suggestions = analysis["suggestions"]

    if "SCAN TABLE events" in plan:
        suggestions.append("👉 Suggestion: CREATE INDEX ON events(user_id) or other filters.")

    if "SCAN TABLE users" in plan:
        suggestions.append("👉 Suggestion: CREATE INDEX ON users(email).")

    return {
        "query": query,
        "plan": plan,
        "suggestions": suggestions
    }

def benchmark_query(db: sqlite3.Connection, query: str):
    cursor = db.cursor()

    start = time.time()
    cursor.execute(query)
    cursor.fetchall()
    duration = (time.time() - start) * 1000  # ms

    return {
        "query": query,
        "time_ms": round(duration, 2)
    }
