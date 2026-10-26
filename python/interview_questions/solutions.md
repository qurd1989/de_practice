# FAANG Data Engineering Interview Questions

*Real questions asked at Google, Facebook, Amazon, Netflix, Apple. Practice these to master data engineering concepts.*

---

## Category 1: SQL Optimization (4 Questions)

### Q1: Optimize a Slow Query

**Interview Prompt:**
"This query takes 45 seconds on a table with 500M rows. How would you optimize it?"

```sql
SELECT u.user_id, u.email, COUNT(o.order_id) as total_orders, SUM(o.amount) as total_spent
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
WHERE o.order_date > '2024-01-01'
GROUP BY u.user_id, u.email
ORDER BY total_spent DESC
LIMIT 100;
```

**Your Approach:**
1. First, ask clarifying questions:
   - How many users? How many orders? (sizes)
   - How often is this query run? (batch or real-time)
   - What's the acceptable latency? (target)

2. Run EXPLAIN to understand current performance:
   ```sql
   EXPLAIN FORMAT=JSON SELECT u.user_id, u.email, COUNT(o.order_id) as total_orders, SUM(o.amount) as total_spent
   FROM users u
   LEFT JOIN orders o ON u.user_id = o.user_id
   WHERE o.order_date > '2024-01-01'
   GROUP BY u.user_id, u.email
   ORDER BY total_spent DESC
   LIMIT 100;
   ```
   
   **Typical findings:**
   - Missing index on `orders.order_date`
   - Full table scan on orders
   - Expensive GROUP BY

3. Optimization strategies (in order):

   **Step 1: Add index on WHERE clause**
   ```sql
   CREATE INDEX idx_order_date ON orders(order_date);
   ```
   Expected improvement: 45s → 5s (full scan eliminated)

   **Step 2: Add composite index for better join**
   ```sql
   CREATE INDEX idx_user_date ON orders(user_id, order_date);
   ```
   Expected improvement: 5s → 1s (JOIN faster, less data scanned)

   **Step 3: Denormalize for aggregates (optional)**
   ```sql
   -- If this query is run frequently, pre-compute
   CREATE TABLE user_spending_summary (
       user_id BIGINT PRIMARY KEY,
       email VARCHAR(255),
       total_orders INT,
       total_spent DECIMAL(10, 2),
       last_updated DATETIME,
       INDEX idx_total_spent (total_spent)
   );
   
   -- Update daily with:
   INSERT INTO user_spending_summary
   SELECT u.user_id, u.email, COUNT(o.order_id), SUM(o.amount), NOW()
   FROM users u
   LEFT JOIN orders o ON u.user_id = o.user_id
   WHERE o.order_date > '2024-01-01'
   GROUP BY u.user_id, u.email
   ON DUPLICATE KEY UPDATE ...;
   ```
   Expected improvement: 1s → 0.1s (simple SELECT from pre-computed table)

**Final Query (after optimization):**
```sql
SELECT user_id, email, total_orders, total_spent
FROM user_spending_summary
ORDER BY total_spent DESC
LIMIT 100;
```

**Trade-offs to discuss:**
- More storage (denormalization)
- Complexity (need to maintain summaries)
- Flexibility (can't easily change aggregation window)
- But: 45s → 0.1s query time ✅

---

### Q2: Complex JOIN with Window Functions

**Interview Prompt:**
"Write a query to find the top 3 products by revenue for each user in the last 30 days."

**What they're testing:**
- Understanding of window functions
- JOIN efficiency
- Aggregation logic

**Solution:**

```sql
-- Step 1: Filter recent orders and join with products
-- Step 2: Use window function to rank products per user
-- Step 3: Filter top 3

WITH user_product_revenue AS (
    SELECT 
        u.user_id,
        u.email,
        p.product_id,
        p.product_name,
        SUM(oi.quantity * oi.price) as revenue,
        ROW_NUMBER() OVER (PARTITION BY u.user_id ORDER BY SUM(oi.quantity * oi.price) DESC) as rank
    FROM users u
    JOIN orders o ON u.user_id = o.user_id
    JOIN order_items oi ON o.order_id = oi.order_id
    JOIN products p ON oi.product_id = p.product_id
    WHERE o.order_date > DATE_SUB(NOW(), INTERVAL 30 DAY)
    GROUP BY u.user_id, u.email, p.product_id, p.product_name
)
SELECT user_id, email, product_id, product_name, revenue
FROM user_product_revenue
WHERE rank <= 3
ORDER BY user_id, rank;
```

**Key concepts:**
- `WITH` clause (CTE) for readability
- `ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY revenue DESC)` — ranks within each user
- `WHERE rank <= 3` — filter top 3
- Multiple JOINs with proper indexing

**Performance considerations:**
- Index on `orders(user_id, order_date)` — filter by user and date
- Index on `order_items(order_id, product_id)` — JOIN efficiency
- Aggregate before window function (already in CTE)

---

### Q3: Finding Duplicate or Anomalies

**Interview Prompt:**
"We suspect we have duplicate users with the same email. Write a query to find them, then a query to deduplicate (keep oldest, delete newer)."

**Solution:**

```sql
-- Step 1: Find duplicates
SELECT email, COUNT(*) as count, GROUP_CONCAT(user_id) as ids
FROM users
GROUP BY email
HAVING count > 1
ORDER BY count DESC;

-- Step 2: Find duplicate rows with row numbers
WITH duplicate_users AS (
    SELECT 
        user_id, 
        email,
        created_at,
        ROW_NUMBER() OVER (PARTITION BY email ORDER BY created_at ASC) as rn
    FROM users
)
SELECT * FROM duplicate_users WHERE rn > 1;

-- Step 3: Delete duplicates (keep oldest)
DELETE FROM users
WHERE user_id IN (
    SELECT user_id FROM (
        SELECT 
            user_id,
            ROW_NUMBER() OVER (PARTITION BY email ORDER BY created_at ASC) as rn
        FROM users
    ) t
    WHERE rn > 1
);
```

**Key concepts:**
- `GROUP BY` + `HAVING` to find groups with count > 1
- `ROW_NUMBER()` to assign sequential numbers within each group
- `ORDER BY created_at ASC` keeps oldest (rn=1), deletes newer (rn > 1)

---

### Q4: Time-Series Aggregation with Gaps

**Interview Prompt:**
"Write a query to find daily active users (DAU) for the last 30 days. Handle missing days (if no activity, show 0)."

**Solution:**

```sql
-- Step 1: Generate calendar of all days
-- Step 2: Count active users per day
-- Step 3: Left join to show 0 for missing days

WITH RECURSIVE date_range AS (
    SELECT DATE_SUB(CURDATE(), INTERVAL 29 DAY) as date
    UNION ALL
    SELECT DATE_ADD(date, INTERVAL 1 DAY) from date_range
    WHERE date < CURDATE()
),
daily_active_users AS (
    SELECT 
        DATE(u.created_at) as date,
        COUNT(DISTINCT u.user_id) as active_users
    FROM users u
    WHERE u.created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
    GROUP BY DATE(u.created_at)
)
SELECT 
    dr.date,
    COALESCE(dau.active_users, 0) as active_users
FROM date_range dr
LEFT JOIN daily_active_users dau ON dr.date = dau.date
ORDER BY dr.date;
```

**Key concepts:**
- `RECURSIVE CTE` to generate missing dates
- `LEFT JOIN` to show 0 for missing activity
- `COALESCE()` to replace NULL with 0
- `COUNT(DISTINCT user_id)` for unique users

**Alternative (simpler, if no missing dates):**
```sql
SELECT 
    DATE(created_at) as date,
    COUNT(DISTINCT user_id) as active_users
FROM users
WHERE created_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY DATE(created_at)
ORDER BY date;
```

---

## Category 2: Data Pipeline Design (4 Questions)

### Q5: Design an ETL for E-Commerce

**Interview Prompt:**
"Design an ETL pipeline that processes 100M events per day from an e-commerce platform. Events are in JSON format in S3. You need to transform and load into a data warehouse for analytics."

**Your Design:**

```
Source (S3/JSON) → Extract → Transform → Load → Warehouse

Step 1: EXTRACT
- Use Python + boto3 to read JSON files from S3
- Batch process (1000 files at a time)
- Handle schema evolution (new fields in JSON)

Step 2: TRANSFORM
- Parse JSON events
- Clean/validate data (remove nulls, validate types)
- Enrich data (join with product catalog, user master)
- Deduplicate events (event_id as key)
- Handle late-arriving data (backfill)

Step 3: LOAD
- Batch insert into MySQL (10K rows per batch)
- Use transactions for atomicity
- Implement idempotency (safe to re-run)
- Use INSERT ... ON DUPLICATE KEY UPDATE for upserts

Step 4: MONITORING
- Log row counts, processing time
- Alert if processing takes > 2 hours
- Track failed files for retry
```

**Implementation Outline:**

```python
import pandas as pd
import json
import mysql.connector
from datetime import datetime, timedelta

def extract_events_from_s3(bucket, prefix, date):
    """Read JSON events from S3"""
    events = []
    # List files from S3 for the given date
    # Read each JSON file and parse events
    return events

def transform_events(events):
    """Clean, validate, deduplicate"""
    df = pd.DataFrame(events)
    
    # Validation
    df = df.dropna(subset=['event_id', 'user_id', 'timestamp'])
    
    # Deduplication (keep first occurrence)
    df = df.drop_duplicates(subset=['event_id'], keep='first')
    
    # Type casting
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['user_id'] = df['user_id'].astype(int)
    
    # Enrichment (optional)
    # df = df.merge(product_catalog, on='product_id', how='left')
    
    return df

def load_events_to_warehouse(df, conn):
    """Load into MySQL with batch inserts"""
    batch_size = 10000
    
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        
        cursor = conn.cursor()
        sql = """
            INSERT INTO events (event_id, user_id, timestamp, event_type, payload)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE updated_at = NOW()
        """
        
        data = [
            (row['event_id'], row['user_id'], row['timestamp'], 
             row['event_type'], row['payload'])
            for _, row in batch.iterrows()
        ]
        
        try:
            cursor.executemany(sql, data)
            conn.commit()
            print(f"Loaded {len(batch)} rows")
        except Exception as e:
            conn.rollback()
            print(f"Error loading batch: {e}")
            raise
        finally:
            cursor.close()

def main():
    conn = mysql.connector.connect(
        host='localhost',
        user='etl_user',
        password='password',
        database='warehouse'
    )
    
    # For each day
    for days_back in range(1, 8):  # Backfill 7 days
        date = datetime.now() - timedelta(days=days_back)
        print(f"Processing {date.date()}...")
        
        # Extract
        events = extract_events_from_s3('my-bucket', 'events/', date)
        
        # Transform
        df = transform_events(events)
        
        # Load
        load_events_to_warehouse(df, conn)
    
    conn.close()

if __name__ == '__main__':
    main()
```

**Key discussion points:**
- **Fault tolerance:** What if pipeline fails mid-load? (Use transactions, idempotency)
- **Late data:** What if events arrive 24h late? (Accept and backfill)
- **Deduplication:** How do you handle duplicates? (Use event_id as key)
- **Scalability:** What if data grows 10x? (Partitioning, parallel processing)
- **Monitoring:** How do you know it succeeded? (Logs, metrics, alerting)

---

### Q6: CDC (Change Data Capture) for Audit Trail

**Interview Prompt:**
"Implement a system to track all changes to the users table (inserts, updates, deletes) for audit purposes."

**Solution:**

**Option 1: Using Triggers (Simple)**

```sql
-- Create audit table
CREATE TABLE users_audit (
    audit_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT,
    action VARCHAR(10),  -- 'INSERT', 'UPDATE', 'DELETE'
    old_email VARCHAR(255),
    new_email VARCHAR(255),
    old_name VARCHAR(200),
    new_name VARCHAR(200),
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    changed_by VARCHAR(255)
);

-- Trigger for INSERT
CREATE TRIGGER users_insert_audit AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO users_audit (user_id, action, new_email, new_name, changed_by)
    VALUES (NEW.user_id, 'INSERT', NEW.email, NEW.name, USER());
END;

-- Trigger for UPDATE
CREATE TRIGGER users_update_audit AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    INSERT INTO users_audit (user_id, action, old_email, new_email, old_name, new_name, changed_by)
    VALUES (NEW.user_id, 'UPDATE', OLD.email, NEW.email, OLD.name, NEW.name, USER());
END;

-- Trigger for DELETE
CREATE TRIGGER users_delete_audit AFTER DELETE ON users
FOR EACH ROW
BEGIN
    INSERT INTO users_audit (user_id, action, old_email, old_name, changed_by)
    VALUES (OLD.user_id, 'DELETE', OLD.email, OLD.name, USER());
END;
```

**Option 2: Using Query Log (For large-scale CDC)**

```python
# Stream binary log to capture all changes
from pymysqlreplication import BinLogStreamReader

stream = BinLogStreamReader(
    connection_settings={
        "host": "localhost",
        "port": 3306,
        "user": "root",
        "passwd": "password"
    },
    server_id=100,
    only_events=[DeleteRowsEvent, WriteRowsEvent, UpdateRowsEvent]
)

for binlogevent in stream:
    for row in binlogevent.rows:
        print(f"Event: {binlogevent.event_type}")
        print(f"Row: {row['values']}")
        # Insert into audit table
        insert_audit(binlogevent, row)
```

**Key discussion points:**
- Triggers are simple but add overhead to writes
- Binary logs are more scalable for real-time CDC
- You can use Debezium (Apache) for production CDC
- Important for compliance (GDPR, SOX, HIPAA)

---

### Q7: Handling Late/Out-of-Order Data

**Interview Prompt:**
"Events arrive out-of-order and up to 24 hours late. How do you handle this in your pipeline to ensure accurate aggregations?"

**Solution:**

```python
# Use timestamp from event (when it occurred), not arrival time

def aggregate_events(events_df, watermark_hours=24):
    """
    Aggregate events with late data handling
    - watermark_hours: Wait this long for late events before finalizing
    """
    
    # Sort by event timestamp (when it happened), not arrival time
    events_df['event_timestamp'] = pd.to_datetime(events_df['event_timestamp'])
    events_df = events_df.sort_values('event_timestamp')
    
    # Aggregate by day
    daily_stats = events_df.groupby(
        pd.Grouper(key='event_timestamp', freq='D')
    ).agg({
        'user_id': 'nunique',  # count unique users
        'revenue': 'sum'
    }).reset_index()
    
    # For data received after watermark, store in "late data" bucket
    cutoff_time = datetime.now() - timedelta(hours=watermark_hours)
    late_events = events_df[events_df['event_timestamp'] < cutoff_time]
    
    # Recompute daily stats with late events
    recomputed = late_events.groupby(
        pd.Grouper(key='event_timestamp', freq='D')
    ).agg({
        'user_id': 'nunique',
        'revenue': 'sum'
    }).reset_index()
    
    # Update warehouse with corrected values
    for _, row in recomputed.iterrows():
        update_daily_stats(row['event_timestamp'], row)
    
    return daily_stats
```

**In SQL (Materialized View approach):**

```sql
-- Create a view that recomputes stats with 24h grace period
CREATE VIEW daily_stats_updated AS
SELECT 
    DATE(event_timestamp) as date,
    COUNT(DISTINCT user_id) as daily_active_users,
    SUM(revenue) as daily_revenue
FROM events
WHERE event_timestamp >= DATE_SUB(CURDATE(), INTERVAL 1 DAY)  -- Include yesterday's late data
GROUP BY DATE(event_timestamp);

-- Refresh this view periodically (every hour)
REFRESH MATERIALIZED VIEW daily_stats_updated;
```

**Key discussion points:**
- Use event time (when it happened), not processing time (when you got it)
- Implement a watermark (grace period for late events)
- Recompute aggregates with late data included
- Common pattern: store both "preliminary" and "final" results
- Trade-off: Accuracy vs freshness

---

## Category 3: Database Design for Scale (3 Questions)

### Q8: Design a User Recommendation System

**Interview Prompt:**
"Design a database schema for a recommendation system that must handle 1B users, 10B items, and run recommendations in real-time (< 500ms)."

**Schema Design:**

```sql
-- Users dimension
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    created_at DATETIME,
    INDEX idx_created_at (created_at)
);

-- Items dimension
CREATE TABLE items (
    item_id BIGINT PRIMARY KEY,
    title VARCHAR(500),
    category_id INT,
    created_at DATETIME,
    INDEX idx_category (category_id)
);

-- User-Item interactions (fact table)
CREATE TABLE user_item_interactions (
    interaction_id BIGINT PRIMARY KEY,
    user_id BIGINT,
    item_id BIGINT,
    interaction_type ENUM('view', 'click', 'purchase', 'like'),
    weight DECIMAL(5, 2),  -- 'purchase' = 1.0, 'view' = 0.1
    interaction_timestamp DATETIME,
    INDEX idx_user_id (user_id),
    INDEX idx_item_id (item_id),
    INDEX idx_timestamp (interaction_timestamp)
) PARTITION BY RANGE (YEAR(interaction_timestamp)) (
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION p2025 VALUES LESS THAN (2026)
);

-- Pre-computed recommendations (cache for fast serving)
CREATE TABLE user_recommendations (
    recommendation_id BIGINT PRIMARY KEY,
    user_id BIGINT,
    recommended_item_id BIGINT,
    score DECIMAL(10, 4),  -- Similarity score
    rank INT,  -- Top 10, 100, 1000, etc.
    computed_at DATETIME,
    INDEX idx_user_id (user_id),
    INDEX idx_rank (rank)
);
```

**Real-Time Recommendation Logic:**

```python
def get_recommendations(user_id, num_recommendations=10):
    """Get recommendations for a user"""
    
    # Step 1: Get user's recent interactions
    user_interactions = query("""
        SELECT item_id, interaction_type, MAX(interaction_timestamp) as last_seen
        FROM user_item_interactions
        WHERE user_id = %s AND interaction_timestamp > DATE_SUB(NOW(), INTERVAL 30 DAY)
        GROUP BY item_id
        LIMIT 100  -- Recent items
    """, user_id)
    
    # Step 2: Find similar items
    similar_items = []
    for item_id in user_interactions['item_id']:
        similar = query("""
            SELECT other_item_id, similarity_score
            FROM item_similarity_matrix
            WHERE item_id = %s
            ORDER BY similarity_score DESC
            LIMIT 20
        """, item_id)
        similar_items.extend(similar)
    
    # Step 3: Score and rank
    scored_items = score_recommendations(similar_items, user_interactions)
    top_items = sorted(scored_items, key=lambda x: x['score'], reverse=True)[:num_recommendations]
    
    # Step 4: Return from cache if available, else compute on-the-fly
    return top_items
```

**Optimizations for Scale:**

1. **Pre-compute recommendations offline:**
   ```sql
   -- Batch job runs every night
   INSERT INTO user_recommendations (user_id, recommended_item_id, score, rank, computed_at)
   SELECT user_id, recommended_item_id, score, rank, NOW()
   FROM (
       SELECT 
           u.user_id,
           i.item_id,
           SUM(uii.weight) as score,
           ROW_NUMBER() OVER (PARTITION BY u.user_id ORDER BY SUM(uii.weight) DESC) as rank
       FROM users u
       JOIN user_item_interactions uii ON u.user_id = uii.user_id
       JOIN items i ON i.item_id != uii.item_id
       WHERE uii.interaction_timestamp > DATE_SUB(NOW(), INTERVAL 30 DAY)
       GROUP BY u.user_id, i.item_id
   ) recommendations
   WHERE rank <= 100;
   ```

2. **Use Redis for hot recommendations:**
   ```python
   # Cache top 1000 user recommendations in Redis
   cache_key = f"recommendations:{user_id}"
   cached = redis.get(cache_key)
   if cached:
       return cached  # Instant, no DB query
   
   # If not in cache, query DB and cache for 1 hour
   recs = query_recommendations(user_id)
   redis.setex(cache_key, 3600, recs)
   return recs
   ```

3. **Shard by user_id:**
   ```
   user_id % 16 = shard_id (0-15)
   Route all queries for user to shard_id
   Each shard can be on different server
   ```

---

### Q9: Schema for Real-Time Leaderboard

**Interview Prompt:**
"Design a leaderboard system that updates in real-time as users earn points. Must handle 100M users, rank updates should happen instantly (< 100ms), and be queryable (top 100, rank of a specific user, etc.)."

**Solution:**

**Naive Approach (Won't Scale):**
```sql
SELECT user_id, SUM(points) as total_points
FROM user_points
GROUP BY user_id
ORDER BY total_points DESC
LIMIT 100;
-- Problem: Sorting 100M rows is slow!
```

**Better: Denormalized Leaderboard Table + Redis**

```sql
-- Normalized source of truth
CREATE TABLE user_points (
    user_id BIGINT,
    game_id INT,
    points INT,
    earned_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_game (user_id, game_id)
);

-- Denormalized leaderboard (updated in real-time)
CREATE TABLE leaderboard (
    rank INT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT UNIQUE NOT NULL,
    total_points BIGINT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id)
);
```

**Real-Time Update Logic (Using Redis Sorted Set):**

```python
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def earn_points(user_id, points, game_id):
    """When a user earns points"""
    
    # Step 1: Insert into source of truth
    insert_into_db(f"""
        INSERT INTO user_points (user_id, game_id, points, earned_at)
        VALUES ({user_id}, {game_id}, {points}, NOW())
    """)
    
    # Step 2: Update Redis leaderboard (instantly)
    # Redis sorted set: ZSET, where score = total_points
    redis_client.zincrby('leaderboard', points, user_id)
    # This is < 1ms even for 100M users!

def get_top_100():
    """Get top 100 users"""
    # Sorted set with descending order
    top_100 = redis_client.zrevrange('leaderboard', 0, 99, withscores=True)
    return [
        {'rank': i+1, 'user_id': uid, 'points': score}
        for i, (uid, score) in enumerate(top_100)
    ]

def get_user_rank(user_id):
    """Get rank of a specific user"""
    rank = redis_client.zrevrank('leaderboard', user_id)  # 0-indexed
    points = redis_client.zscore('leaderboard', user_id)
    return {'rank': rank + 1, 'user_id': user_id, 'points': points}
```

**Hybrid Approach (Accuracy + Performance):**

```python
# Real-time: Use Redis for fast reads
# Periodically: Sync Redis back to MySQL for durability

def sync_redis_to_mysql():
    """Run every 5 minutes: Persist Redis to MySQL"""
    leaderboard = redis_client.zrevrange('leaderboard', 0, -1, withscores=True)
    
    cursor = mysql_conn.cursor()
    cursor.execute("TRUNCATE TABLE leaderboard")
    
    for rank, (user_id, points) in enumerate(leaderboard, 1):
        cursor.execute("""
            INSERT INTO leaderboard (rank, user_id, total_points, updated_at)
            VALUES (%s, %s, %s, NOW())
        """, (rank, user_id, points))
    
    mysql_conn.commit()

# If Redis crashes, we can rebuild from MySQL
def rebuild_redis_from_mysql():
    """Recover Redis from MySQL"""
    leaderboard = query("SELECT user_id, total_points FROM leaderboard")
    
    for user_id, points in leaderboard:
        redis_client.zadd('leaderboard', {user_id: points})
```

**Handling Ties:**
```python
# For users with same points, use creation time as tiebreaker
def get_user_rank_with_tiebreaker(user_id):
    # Store as tuple: (points, -created_timestamp)
    created_time = query(f"SELECT created_at FROM users WHERE user_id = {user_id}")
    score = total_points * 1000000 - int(created_time.timestamp())
    redis_client.zincrby('leaderboard', score, user_id)
```

---

## Category 4: Hands-On Coding Challenge

### Q10: Build a Data Pipeline End-to-End

**Interview Prompt:**
"You have 1 million records of user login events as JSON files in a folder. Build a complete pipeline to:
1. Read all files
2. Clean and validate data
3. Load into a database
4. Generate a summary report

You have 2 hours. Code it."

**Solution (Step-by-step):**

```python
import json
import pandas as pd
import mysql.connector
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Step 1: Setup database connection
def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='password',
        database='analytics'
    )

# Step 2: Create schema
def create_schema(conn):
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS login_events (
            event_id VARCHAR(255) PRIMARY KEY,
            user_id BIGINT NOT NULL,
            login_timestamp DATETIME NOT NULL,
            device VARCHAR(50),
            country VARCHAR(2),
            is_valid TINYINT(1) DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_user_timestamp (user_id, login_timestamp),
            INDEX idx_country (country)
        )
    """)
    conn.commit()
    logger.info("Schema created successfully")

# Step 3: Extract (read JSON files)
def extract_events(folder_path):
    """Read all JSON files from folder"""
    events = []
    file_count = 0
    
    for json_file in Path(folder_path).glob('*.json'):
        try:
            with open(json_file, 'r') as f:
                file_events = json.load(f)
                events.extend(file_events)
                file_count += 1
        except Exception as e:
            logger.warning(f"Error reading {json_file}: {e}")
    
    logger.info(f"Extracted {len(events)} events from {file_count} files")
    return events

# Step 4: Transform (validate, clean, deduplicate)
def transform_events(events):
    """Clean and validate events"""
    df = pd.DataFrame(events)
    initial_count = len(df)
    
    # Remove duplicates by event_id
    df = df.drop_duplicates(subset=['event_id'], keep='first')
    duplicates = initial_count - len(df)
    
    # Validate required fields
    df = df.dropna(subset=['user_id', 'login_timestamp'])
    
    # Convert types
    df['user_id'] = df['user_id'].astype(int)
    df['login_timestamp'] = pd.to_datetime(df['login_timestamp'])
    
    # Flag invalid entries
    df['is_valid'] = 1
    df.loc[df['user_id'] < 0, 'is_valid'] = 0  # Invalid user IDs
    df.loc[df['login_timestamp'] > datetime.now(), 'is_valid'] = 0  # Future timestamps
    
    logger.info(f"Transformed {len(df)} events ({duplicates} duplicates removed)")
    return df

# Step 5: Load (batch insert)
def load_events(df, conn, batch_size=10000):
    """Load events into database"""
    cursor = conn.cursor()
    successful = 0
    failed = 0
    
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        
        data = [
            (
                row['event_id'],
                row['user_id'],
                row['login_timestamp'],
                row.get('device'),
                row.get('country'),
                row['is_valid']
            )
            for _, row in batch.iterrows()
        ]
        
        sql = """
            INSERT INTO login_events 
            (event_id, user_id, login_timestamp, device, country, is_valid)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE is_valid = VALUES(is_valid)
        """
        
        try:
            cursor.executemany(sql, data)
            conn.commit()
            successful += len(batch)
            logger.info(f"Loaded batch {i//batch_size + 1}: {len(batch)} rows")
        except Exception as e:
            conn.rollback()
            failed += len(batch)
            logger.error(f"Failed to load batch: {e}")
    
    cursor.close()
    logger.info(f"Load complete: {successful} successful, {failed} failed")
    return successful, failed

# Step 6: Generate report
def generate_report(conn):
    """Create summary report"""
    cursor = conn.cursor()
    
    report = {}
    
    # Total events
    cursor.execute("SELECT COUNT(*) FROM login_events WHERE is_valid = 1")
    report['total_valid_events'] = cursor.fetchone()[0]
    
    # Unique users
    cursor.execute("SELECT COUNT(DISTINCT user_id) FROM login_events WHERE is_valid = 1")
    report['unique_users'] = cursor.fetchone()[0]
    
    # Events by country (top 10)
    cursor.execute("""
        SELECT country, COUNT(*) as count
        FROM login_events
        WHERE is_valid = 1 AND country IS NOT NULL
        GROUP BY country
        ORDER BY count DESC
        LIMIT 10
    """)
    report['top_countries'] = dict(cursor.fetchall())
    
    # Events by device (top 5)
    cursor.execute("""
        SELECT device, COUNT(*) as count
        FROM login_events
        WHERE is_valid = 1 AND device IS NOT NULL
        GROUP BY device
        ORDER BY count DESC
        LIMIT 5
    """)
    report['device_distribution'] = dict(cursor.fetchall())
    
    # Invalid events
    cursor.execute("SELECT COUNT(*) FROM login_events WHERE is_valid = 0")
    report['invalid_events'] = cursor.fetchone()[0]
    
    cursor.close()
    
    # Print report
    logger.info("=== SUMMARY REPORT ===")
    logger.info(f"Total Valid Events: {report['total_valid_events']}")
    logger.info(f"Unique Users: {report['unique_users']}")
    logger.info(f"Invalid Events: {report['invalid_events']}")
    logger.info(f"Top Countries: {report['top_countries']}")
    logger.info(f"Device Distribution: {report['device_distribution']}")
    
    return report

# Main pipeline
def run_pipeline(input_folder):
    """Execute complete ETL pipeline"""
    start_time = datetime.now()
    
    try:
        # Setup
        conn = get_db_connection()
        create_schema(conn)
        
        # ETL
        events = extract_events(input_folder)
        df = transform_events(events)
        successful, failed = load_events(df, conn)
        report = generate_report(conn)
        
        conn.close()
        
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(f"Pipeline completed in {elapsed:.2f} seconds")
        
        return report
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

# Run it
if __name__ == '__main__':
    report = run_pipeline('/path/to/json/files')
```

**Expected Output:**
```
2024-03-15 10:30:45 - INFO - Schema created successfully
2024-03-15 10:30:50 - INFO - Extracted 1000000 events from 100 files
2024-03-15 10:31:00 - INFO - Transformed 1000000 events (5000 duplicates removed)
2024-03-15 10:31:30 - INFO - Load complete: 995000 successful, 0 failed
2024-03-15 10:31:35 - INFO - === SUMMARY REPORT ===
2024-03-15 10:31:35 - INFO - Total Valid Events: 990000
2024-03-15 10:31:35 - INFO - Unique Users: 50000
2024-03-15 10:31:35 - INFO - Invalid Events: 5000
2024-03-15 10:31:35 - INFO - Top Countries: {'US': 400000, 'UK': 150000, ...}
2024-03-15 10:31:35 - INFO - Pipeline completed in 60.42 seconds
```

---

## Summary: Practice Strategy

### Week 1: Study & Understand
- [ ] Read Categories 1-2 (SQL + Pipelines)
- [ ] Discuss solutions out loud
- [ ] Understand WHY each optimization works

### Week 2-3: Code Solutions
- [ ] Implement Q1-Q3 (SQL optimization)
- [ ] Code Q5 (ETL pipeline)
- [ ] Time yourself: 30 min per question

### Week 4: Interview Practice
- [ ] Mock interview: Q1 (45 min time limit)
- [ ] Mock interview: Q5 (60 min time limit)
- [ ] Ask yourself: "Why this approach? What if..."

### Success Criteria
- [ ] Answer all questions without looking at solutions
- [ ] Explain trade-offs (speed vs storage, complexity vs performance)
- [ ] Code is production-ready (error handling, logging, tests)
- [ ] Can scale from 1M to 1B rows (think through optimizations)

Good luck! 🎯
