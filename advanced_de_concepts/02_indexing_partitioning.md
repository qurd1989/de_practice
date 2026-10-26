# Indexing & Partitioning Strategy

*Why this matters in FAANG interviews: The difference between a query taking 0.1s vs 30s is often an index.*

---

## Part 1: Indexing Fundamentals

### What is an Index?

An **index** is a data structure that enables faster data retrieval. Without indexes, databases must scan every row (slow). With indexes, databases can jump directly to relevant rows.

**Analogy:** 
- Without index = Reading every page of a book to find a topic
- With index = Looking up the topic in the book's index, then jumping to pages

---

## Index Types

### 1. Primary Key Index (Clustered)

**Definition:** Unique identifier for each row; data is physically sorted by this key

**Example:**
```sql
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY AUTO_INCREMENT,  -- Primary key index
    email VARCHAR(255),
    name VARCHAR(200)
);
```

**Characteristics:**
- ✅ One per table (data physically sorted by primary key)
- ✅ Fastest lookups by primary key
- ❌ Slower writes (must maintain sort order)
- ✅ Automatically created when you define PRIMARY KEY

**Query Performance:**
```sql
-- FAST: Directly uses primary key index
SELECT * FROM users WHERE user_id = 123;  -- O(log n)

-- SLOW: Must scan all rows
SELECT * FROM users WHERE email = 'john@example.com';  -- O(n)
```

---

### 2. Secondary Index (Non-Clustered)

**Definition:** Additional indexes on non-primary-key columns to speed up queries

**Example:**
```sql
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    email VARCHAR(255),
    created_at DATETIME,
    INDEX idx_email (email),              -- Secondary index
    INDEX idx_created_at (created_at)
);
```

**Characteristics:**
- ✅ Multiple per table
- ✅ Faster lookups on indexed columns
- ✅ Smaller than primary index (only stores key + pointer)
- ❌ Slower writes (must update indexes too)
- ❌ Uses extra storage

**Query Performance:**
```sql
-- FAST: Uses idx_email index
SELECT * FROM users WHERE email = 'john@example.com';  -- O(log n)

-- FAST: Uses idx_created_at index
SELECT * FROM users WHERE created_at > '2024-01-01';  -- O(log n)

-- SLOW: Must scan all rows (no index on name)
SELECT * FROM users WHERE name = 'John';  -- O(n)
```

---

### 3. Composite Index (Multi-Column)

**Definition:** Index on multiple columns; useful for queries filtering on multiple columns

**Example:**
```sql
CREATE TABLE orders (
    order_id BIGINT PRIMARY KEY,
    user_id BIGINT,
    order_date DATETIME,
    status VARCHAR(50),
    INDEX idx_user_date (user_id, order_date)  -- Composite index
);
```

**When it helps:**
```sql
-- FAST: Index matches (user_id, order_date)
SELECT * FROM orders 
WHERE user_id = 5 AND order_date > '2024-01-01';

-- FAST: Uses first column of index
SELECT * FROM orders 
WHERE user_id = 5;

-- SLOW: Doesn't use index (order_date without user_id)
SELECT * FROM orders 
WHERE order_date > '2024-01-01';  -- Index is (user_id, order_date), not helpful
```

**Order matters!**
- Good: `INDEX (user_id, order_date)` — filters by user first, then date
- Better for some queries: `INDEX (order_date, user_id)` — depends on query patterns

---

### 4. Unique Index

**Definition:** Ensures all values in the indexed column(s) are unique

**Example:**
```sql
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    email VARCHAR(255) UNIQUE,  -- Unique index
    ssn VARCHAR(11) UNIQUE
);
```

**Use Cases:**
- Email addresses (must be unique per user)
- Username (must be unique)
- Social security numbers (must be unique)

---

## When to Add Indexes

### ✅ ADD index if:
- Column is in WHERE clause frequently
- Column is used in JOIN conditions
- Column is used for sorting (ORDER BY)
- Column has low cardinality (few distinct values) used in filters

### ❌ DON'T ADD index if:
- Column has high cardinality with random distribution
- Table is small (< 10K rows)
- Column is rarely queried
- Write performance is critical (indexes slow down INSERTs/UPDATEs)

### Trade-off: Read vs Write

```
More indexes = Faster reads, slower writes
Fewer indexes = Slower reads, faster writes
```

**Decision:** Depends on your workload
- **Read-heavy (analytics, reporting):** Add many indexes
- **Write-heavy (real-time transactions):** Minimize indexes
- **Mixed:** Add indexes on frequently filtered columns only

---

## EXPLAIN Plans (Your Best Friend)

### Reading EXPLAIN Output

```sql
EXPLAIN FORMAT=JSON SELECT * 
FROM orders o
JOIN users u ON o.user_id = u.user_id
WHERE o.order_date > '2024-01-01';
```

**Key metrics:**
- `rows`: Estimated rows scanned (lower is better)
- `type`: Access method (best to worst: system, const, eq_ref, ref, range, index, ALL)
- `key`: Index used (NULL means no index)
- `key_len`: Bytes used from index
- `Extra`: Additional info (e.g., "Using where", "Using temporary")

**Before optimization:**
```
id | select_type | table | type | key  | rows   | Extra
1  | SIMPLE      | o     | ALL  | NULL | 500000 | Using where
1  | SIMPLE      | u     | ALL  | NULL | 100000 | Using where
```
⚠️ Full table scan on both tables!

**After adding indexes:**
```
id | select_type | table | type | key              | rows | Extra
1  | SIMPLE      | o     | range| idx_order_date   | 5000 | Using where
1  | SIMPLE      | u     | eq_ref| PRIMARY         | 1    | Using join buffer
```
✅ Much better — only 5K rows scanned instead of 500K!

---

## Part 2: Partitioning Strategy

### What is Partitioning?

**Partitioning** splits a large table into smaller, more manageable pieces based on a column value.

**Analogy:** Instead of one giant phone book, split into A-F, G-M, N-Z sections.

---

## Partitioning Types

### 1. Range Partitioning

**Split by value range:** Data is partitioned by column values in ranges

**Example: Partition orders by year**
```sql
CREATE TABLE orders (
    order_id BIGINT,
    user_id BIGINT,
    order_date DATE,
    amount DECIMAL(10, 2)
) PARTITION BY RANGE (YEAR(order_date)) (
    PARTITION p2021 VALUES LESS THAN (2022),
    PARTITION p2022 VALUES LESS THAN (2023),
    PARTITION p2023 VALUES LESS THAN (2024),
    PARTITION p2024 VALUES LESS THAN (2025),
    PARTITION future VALUES LESS THAN MAXVALUE
);
```

**Benefits:**
- ✅ Easy to archive old data (drop partition)
- ✅ Queries on recent data are faster
- ✅ Maintenance faster (operate on partition)

---

### 2. Hash Partitioning

**Split by hash function:** Data is distributed evenly based on hash of column

**Example: Partition users evenly across 4 partitions**
```sql
CREATE TABLE users (
    user_id BIGINT,
    email VARCHAR(255),
    name VARCHAR(200)
) PARTITION BY HASH(user_id) PARTITIONS 4;
```

**Benefits:**
- ✅ Even data distribution
- ✅ Scales well to many servers (sharding)
- ✅ Good for load balancing

---

### 3. List Partitioning

**Split by explicit values:** Data is partitioned by discrete values

**Example: Partition by region**
```sql
CREATE TABLE orders (
    order_id BIGINT,
    region VARCHAR(50),
    amount DECIMAL(10, 2)
) PARTITION BY LIST (region) (
    PARTITION p_us VALUES IN ('CA', 'TX', 'NY'),
    PARTITION p_eu VALUES IN ('UK', 'DE', 'FR'),
    PARTITION p_asia VALUES IN ('JP', 'IN', 'CN')
);
```

**Benefits:**
- ✅ Logical organization by category
- ✅ Easy to understand
- ✅ Good for regional data

---

## When to Partition

### ✅ Partition if:
- Table is very large (> 100M rows)
- You have time-series data (events, logs, orders)
- You want to archive old data
- You need to distribute data across servers (sharding)
- You have a clear partitioning key

### ❌ Don't partition if:
- Table is small (< 10M rows)
- Queries access data across partitions
- Partitioning key isn't obvious
- Operational complexity not worth it

---

## Indexing vs Partitioning

| Aspect | Indexing | Partitioning |
|--------|----------|--------------|
| **Purpose** | Speed up queries | Scale to large datasets |
| **Scope** | Column-level | Table-level |
| **Overhead** | Extra storage | Extra disk I/O, complexity |
| **Best for** | Filtering, sorting | Time-series, large tables |
| **Example** | INDEX on email | PARTITION BY date |

**Pro tip:** Use both! Index columns within partitions for best performance.

---

## FAANG Interview Question: Indexing & Performance

### Q: "We have a 500M row orders table. Queries are slow. How do you fix it?"

**Answer Strategy:**

1. **Understand the problem:**
   - What queries are slow? (Ask for query patterns)
   - What's the current schema?
   - Are there indexes? What columns?

2. **Diagnose with EXPLAIN:**
   - Run EXPLAIN on slow queries
   - Look for: full table scans, missing indexes, bad joins

3. **Optimize in phases:**
   ```sql
   -- Phase 1: Add missing indexes on WHERE clauses
   CREATE INDEX idx_user_id ON orders(user_id);
   CREATE INDEX idx_order_date ON orders(order_date);
   
   -- Phase 2: Add composite indexes for common query patterns
   CREATE INDEX idx_user_date ON orders(user_id, order_date);
   
   -- Phase 3: Consider partitioning if indexes aren't enough
   -- Partition by date, keep recent data (hot) and archive old (cold)
   ALTER TABLE orders PARTITION BY RANGE (YEAR(order_date)) ...
   
   -- Phase 4: Denormalize if needed
   -- Pre-compute aggregates to avoid joins
   ```

4. **Measure & validate:**
   ```sql
   -- Before
   SELECT * FROM orders WHERE user_id = 5 AND order_date > '2024-01-01';
   -- Result: Full table scan, 500M rows, 30 seconds
   
   -- After indexes
   -- Result: 1000 rows from index, 0.1 seconds (300x faster!)
   
   -- After partitioning
   -- Result: Only scan 2024 partition (100M rows), 0.05 seconds
   ```

---

## Practice Exercise

**Scenario:** E-commerce platform with 1B orders

**Current schema (no indexes):**
```sql
CREATE TABLE orders (
    order_id BIGINT PRIMARY KEY,
    user_id BIGINT,
    order_date DATETIME,
    product_id BIGINT,
    amount DECIMAL(10, 2),
    status VARCHAR(50)
);
```

**Common queries:**
```sql
-- Q1: Get all orders for a user
SELECT * FROM orders WHERE user_id = 123;

-- Q2: Get orders from last month
SELECT * FROM orders WHERE order_date > DATE_SUB(NOW(), INTERVAL 1 MONTH);

-- Q3: Get user's recent orders
SELECT * FROM orders 
WHERE user_id = 123 AND order_date > '2024-01-01'
ORDER BY order_date DESC;

-- Q4: Get revenue by product
SELECT product_id, SUM(amount) FROM orders GROUP BY product_id;
```

**Questions:**
1. What indexes would you add? Why?
2. Would you partition? On what column? Why?
3. What's your trade-off between storage and query speed?
4. How would you monitor index effectiveness?

---

**Next:** Read `03_query_optimization.md` to learn advanced query optimization techniques.
