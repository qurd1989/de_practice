# 🚀 Quick Start: FAANG Data Engineering Interview Prep

Welcome! This is your complete, local learning environment for mastering data engineering. No cloud account needed — everything runs on your machine.

---

## 📋 Setup (5 minutes)

### Step 1: Install Dependencies
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install all dependencies
pip install -r requirements.txt
```

### Step 2: Verify Database Connection
```powershell
# Test MySQL
python -c "import mysql.connector; print('MySQL ✓')"

# Or if using SQL Server
python -c "import pyodbc; print('SQL Server ✓')"
```

### Step 3: Create Database
```sql
-- In MySQL Workbench or MySQL shell
CREATE DATABASE analytics;
USE analytics;

-- Load schema
SOURCE sql/schema_mysql.sql;
```

---

## 🎓 Your 4-Week Learning Plan

### Week 1: Core Concepts (5-6 hours)
**Goal:** Understand fundamental data engineering concepts

**Read these guides (in order):**
1. `advanced_de_concepts/01_data_modeling.md` (1-2 hours)
   - Learn normalized vs denormalized schemas
   - Understand entities, relationships, keys
   - Practice the design exercise at the end

2. `advanced_de_concepts/02_indexing_partitioning.md` (1-2 hours)
   - Learn why indexes matter for query performance
   - Understand when to add indexes vs partition
   - Study the FAANG question at the end

3. Study `faang_interview_questions/solutions.md` Categories 1-2 (SQL + Pipelines)
   - Q1: SQL Optimization (30 min)
   - Q2: Complex JOINs (30 min)
   - Q5: ETL Design (30 min)

**Success Check:**
- [ ] Can you explain normalization vs denormalization?
- [ ] Can you design a schema for a new business problem?
- [ ] Do you understand how indexes speed up queries?

---

### Week 2: Build Project 1 — ETL Pipeline (6-8 hours)
**Goal:** Write production-quality data pipeline code

**Steps:**
1. Generate sample data:
   ```powershell
   python datasets/generate_ecommerce_data.py --users 10000 --output data/raw/
   ```

2. Read the project description:
   ```
   projects/01_etl_pipeline/README.md
   ```

3. Write your ETL pipeline:
   ```powershell
   # Edit this file and implement all TODOs
   projects/01_etl_pipeline/starter/etl_pipeline.py
   ```

4. Test it:
   ```powershell
   python projects/01_etl_pipeline/starter/etl_pipeline.py
   ```

5. Verify:
   - [ ] All CSVs loaded successfully
   - [ ] Data is clean (duplicates removed)
   - [ ] Summary report generated
   - [ ] No errors in logs
   - [ ] Can re-run without creating duplicates (idempotency)

**Self-Check Questions:**
- Why do we batch inserts instead of one big INSERT?
- What happens if the pipeline fails mid-way?
- How do you ensure data quality?

---

### Week 3: Project 2 — Query Optimization (6-8 hours)
**Goal:** Master SQL performance tuning

**Steps:**
1. Create a large dataset:
   ```powershell
   python datasets/generate_ecommerce_data.py --users 100000 --orders 500000
   ```

2. Read `projects/02_query_optimization/README.md` (when I create it)

3. Write slow queries, then optimize them:
   ```sql
   -- Before: Slow (full table scan)
   SELECT * FROM orders WHERE total > 1000;
   
   -- After: Fast (with index)
   CREATE INDEX idx_total ON orders(total);
   SELECT * FROM orders WHERE total > 1000;
   ```

4. Use EXPLAIN to analyze:
   ```sql
   EXPLAIN FORMAT=JSON SELECT ...
   ```

**Success Criteria:**
- [ ] 10-50x faster queries with proper indexes
- [ ] Understand every line in EXPLAIN output
- [ ] Know when to index vs denormalize

---

### Week 4: Project 3 — Data Warehouse Design (6-8 hours)
**Goal:** Design analytics-optimized schemas

**What You'll Build:**
- Fact tables (transactions, events)
- Dimension tables (users, products, time)
- Aggregation queries
- Handle slowly changing dimensions (SCD Type 2)

**Example Fact Table:**
```sql
CREATE TABLE fact_orders (
    order_id BIGINT PRIMARY KEY,
    user_id BIGINT,          -- FK to dim_users
    product_id BIGINT,       -- FK to dim_products
    date_id INT,            -- FK to dim_date
    quantity INT,
    revenue DECIMAL(10, 2),
    INDEX idx_user_date (user_id, date_id)
);
```

---

## 🎯 Practice FAANG Interview Questions

Open `faang_interview_questions/solutions.md` and practice these (in order):

### Tier 1: Warm-up (30 min each)
- Q1: SQL Optimization
- Q3: Duplicate Detection

### Tier 2: Medium (45 min each)
- Q2: Complex JOINs with Window Functions
- Q4: Time-Series with Missing Data
- Q5: Design ETL Pipeline

### Tier 3: Hard (60+ min)
- Q8: Recommendation System Schema
- Q9: Real-Time Leaderboard (Redis)
- Q10: End-to-End Pipeline Coding

**Practice Approach:**
1. Read the question
2. Close the solution file
3. Code for 30-60 minutes
4. Check solution and compare
5. Discuss: What did you do differently? Why?

---

## 📚 File Structure

```
de_practice/
├── LEARNING_PATH.md                          ← You are here
├── README_FAKER.md                           ← Faker guide (already done)
├── requirements.txt                          ← Dependencies
│
├── advanced_de_concepts/
│   ├── 01_data_modeling.md                   ← Week 1
│   ├── 02_indexing_partitioning.md           ← Week 1
│   ├── 03_query_optimization.md              ← Week 3 (TODO)
│   ├── 04_etl_vs_elt.md                      ← Week 1 (TODO)
│   ├── 05_cdc_idempotency.md                 ← Bonus (TODO)
│
├── faang_interview_questions/
│   └── solutions.md                          ← 10 detailed questions + solutions
│
├── projects/
│   ├── 01_etl_pipeline/
│   │   ├── README.md                         ← Project description
│   │   ├── starter/
│   │   │   └── etl_pipeline.py               ← Code with TODOs
│   │   ├── solution/
│   │   │   └── etl_pipeline.py               ← Reference solution
│   │   └── data/                             ← Sample input files
│   │
│   ├── 02_query_optimization/
│   │   ├── README.md                         ← Project description (TODO)
│   │   ├── starter/
│   │   └── solution/
│   │
│   └── 03_warehouse_design/
│       ├── README.md                         ← Project description (TODO)
│       ├── starter/
│       └── solution/
│
├── datasets/
│   ├── generate_ecommerce_data.py            ← Generate sample CSVs
│   ├── generate_large_dataset.py             ← For optimization practice (TODO)
│   └── generate_events_data.py               ← For real-time projects (TODO)
│
├── sql/
│   ├── schema_mysql.sql                      ← Database schema
│   └── schema_mssql.sql                      ← SQL Server schema
│
└── scripts/
    ├── generate_fake_data.py                 ← Insert fake data into DB
    └── benchmark_queries.py                  ← Measure query performance (TODO)
```

---

## 🏃 Quick Commands

### Generate Sample Data
```powershell
# Small (for quick testing)
python datasets/generate_ecommerce_data.py --users 1000 --products 100 --orders 5000 --output data/raw/

# Large (for optimization practice)
python datasets/generate_ecommerce_data.py --users 100000 --products 1000 --orders 500000 --output data/raw/
```

### Load Data into Database
```powershell
# MySQL: Insert 10K fake users
python scripts/generate_fake_data.py --db mysql --host localhost --user root --password pwd --database analytics --rows 10000 --dry-run

# Real insert
python scripts/generate_fake_data.py --db mysql --host localhost --user root --password pwd --database analytics --rows 10000 --confirm-target
```

### Run ETL Pipeline
```powershell
python projects/01_etl_pipeline/starter/etl_pipeline.py
```

---

## 💡 Study Tips

### For Interviews
1. **Think out loud** — Explain your reasoning as you code
2. **Ask clarifying questions** — "Scale? Latency? How often?" matter
3. **Start simple** — Get it working correctly first, optimize later
4. **Discuss trade-offs** — "This is faster but uses more storage..."
5. **Use EXPLAIN** — Show you understand query performance

### For Learning
1. **Don't memorize** — Understand the WHY behind each concept
2. **Experiment locally** — Change code, see what breaks, learn why
3. **Code from scratch** — Don't copy-paste; type everything out
4. **Teach someone** — Explain concepts to a friend (best way to learn)
5. **Build projects** — Hands-on learning beats reading

### For Retention
- Review Week 1 concepts every week
- Redo projects from memory (no notes)
- Time yourself on practice questions
- Increase complexity: 1K rows → 1M rows → 1B rows

---

## ✅ Pre-Interview Checklist

Before your actual interviews, verify:

- [ ] Can design a normalized schema for any problem
- [ ] Can optimize slow queries (add indexes, rewrite, denormalize)
- [ ] Can explain trade-offs (speed vs storage, consistency vs availability)
- [ ] Can code an ETL pipeline end-to-end (30 min, production quality)
- [ ] Know window functions, CTEs, and complex JOINs
- [ ] Can discuss scaling: 1M → 1B rows, what changes?
- [ ] Can explain 5+ concepts without notes
- [ ] Can solve 10+ interview questions without solutions

---

## 🎓 Interview Day Tips

### System Design Questions
1. Clarify requirements (QPS, data volume, latency)
2. Propose a simple solution first
3. Identify bottlenecks
4. Optimize with indexes, caching, partitioning, sharding
5. Discuss trade-offs and alternatives

### Coding Questions
1. Ask for constraints (time limit, data size)
2. Write pseudocode first
3. Implement with error handling
4. Test with edge cases
5. Optimize if time allows

### Common Interview Patterns
- "Our X query is slow, how do you optimize it?"
- "Design a schema for Y business problem"
- "How would you handle Z at 1B scale?"
- "Walk me through your ETL pipeline"
- "Explain your approach to data quality"

---

## 📞 Need Help?

### Concepts Are Unclear?
- Re-read the concept guide
- Google for additional articles
- Try examples locally

### Projects Are Hard?
- Read the README again
- Check the solution file
- Modify the solution, don't copy it

### Practice Questions Too Hard?
- Start with Tier 1 (easier questions)
- Spend more time on Week 1 concepts
- Build confidence before hard questions

---

## 🎉 You're Ready!

This learning environment has everything you need to become interview-ready. The key is:

1. ✅ **Learn concepts** (Week 1)
2. ✅ **Build projects** (Weeks 2-3)
3. ✅ **Practice questions** (All weeks)
4. ✅ **Review & iterate** (All weeks)

**Start now:**
1. Read `advanced_de_concepts/01_data_modeling.md` (1-2 hours)
2. Answer the practice exercise at the end
3. Move to the next concept

Good luck! You've got this! 💪

---

**Last updated:** March 2026  
**Next steps:** Start with Week 1 concepts, build consistency, practice regularly.
