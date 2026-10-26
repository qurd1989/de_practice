# 🎯 FAANG Data Engineering Interview Prep — 4-Week Learning Path

**Goal:** Master advanced data engineering concepts and solve real FAANG-style problems locally.

**Duration:** 4 weeks (20-30 hours commitment)  
**Difficulty:** Intermediate → Advanced  
**Tech Stack:** Python, Faker, MySQL, SQL, pandas, asyncio

---

## 📅 Weekly Breakdown

### Week 1: Core Concepts + Interview Questions (5-6 hours)
Focus: Understand the fundamentals deeply

**Monday-Tuesday:** Read core concepts (2-3 hours)
- [ ] `advanced_de_concepts/01_data_modeling.md` — Understand schemas, normalization, relationships
- [ ] `advanced_de_concepts/02_indexing_partitioning.md` — Why indexes matter, types, trade-offs

**Wednesday-Thursday:** Read more concepts (2-3 hours)
- [ ] `advanced_de_concepts/03_query_optimization.md` — EXPLAIN plans, execution strategies
- [ ] `advanced_de_concepts/04_etl_vs_elt.md` — Batch vs streaming, data pipelines

**Friday:** Study FAANG interview questions (2 hours)
- [ ] `faang_interview_questions/sql_optimization.md` — Practice 3-4 questions
- [ ] `faang_interview_questions/database_design.md` — Practice 3-4 questions

**Self-Check:**
- Can you explain the difference between normalization and denormalization?
- Can you write an optimized query using proper joins and indexes?
- Can you design a schema for a given business problem?

---

### Week 2: Project 1 — ETL Pipeline (6-8 hours)
Build a complete data pipeline from source to warehouse

**Objective:** Extract → Transform → Load data, understand data quality

**Tasks:**
1. Generate realistic multi-table dataset using `datasets/generate_ecommerce_data.py`
2. Create raw data files (CSV)
3. Implement ETL pipeline (`projects/01_etl_pipeline/solution/`)
   - Parse CSV files
   - Clean & validate data
   - Load into MySQL with error handling
4. Add audit logging & error recovery
5. Measure performance metrics

**Success Criteria:**
- ✅ Load 100K+ records without errors
- ✅ Handle duplicate detection
- ✅ Add data quality checks
- ✅ Pipeline runs idempotently (safe to re-run)

**Interview Practice:**
- "Design an ETL for 1B records — how would you handle it?"
- "What happens if your pipeline fails mid-execution?"
- "How do you ensure data quality?"

---

### Week 3: Project 2 — Query Optimization (6-8 hours)
Take a slow query and make it fast using indexes, joins, and query rewriting

**Objective:** Understand query execution, EXPLAIN plans, optimization techniques

**Tasks:**
1. Generate large dataset (1M+ records) with `datasets/generate_large_dataset.py`
2. Write intentionally slow queries (`projects/02_query_optimization/starter/`)
3. Analyze with EXPLAIN plans
4. Optimize:
   - Add strategic indexes
   - Rewrite joins
   - Use window functions
   - Partition data
5. Compare before/after performance & execution plans

**Success Criteria:**
- ✅ Reduce query time by 10-50x
- ✅ Understand every line in EXPLAIN plan
- ✅ Know when to add indexes vs denormalize

**Interview Practice:**
- "This query takes 30 seconds. How do you optimize it?"
- "When should you NOT use an index?"
- "How do you handle hot partitions?"

---

### Week 4: Project 3 — Data Warehouse Design (6-8 hours)
Design a star schema for analytics; implement fact & dimension tables

**Objective:** Understand dimensional modeling, slowly changing dimensions, grain

**Tasks:**
1. Business context: E-commerce company, 10M daily events
2. Design star schema:
   - Identify facts (transactions, events)
   - Identify dimensions (customer, product, time, geography)
3. Implement in MySQL:
   - Create fact & dimension tables
   - Handle slowly changing dimensions (SCD Type 2)
4. Build aggregation queries for common analytics use cases
5. Optimize with denormalization

**Success Criteria:**
- ✅ Schema supports 100+ concurrent queries
- ✅ Query response time < 500ms for standard reports
- ✅ Dimensions update correctly (SCD Type 2)

**Interview Practice:**
- "Design a data warehouse for Uber — what are your facts and dimensions?"
- "How do you handle SCD Type 2?"
- "Should this be a fact or dimension?"

---

## 🚀 Quick Start

### Prerequisites
```powershell
# Activate venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Verify database connection
python -c "import mysql.connector; print('MySQL OK')"
```

### First Time Setup
```powershell
# Create database schema
mysql -h localhost -u root -p < sql/schema_mysql.sql

# Generate sample data
python datasets/generate_ecommerce_data.py --rows 10000

# Run first project
cd projects/01_etl_pipeline
python starter/etl_pipeline.py --dry-run
```

---

## 📚 Learning Resources Structure

```
projects/
├── 01_etl_pipeline/
│   ├── README.md              # Problem statement, learning goals
│   ├── starter/               # Skeleton code with TODOs
│   │   └── etl_pipeline.py
│   ├── solution/              # Complete solution
│   │   ├── etl_pipeline.py
│   │   └── validate.py        # Verification script
│   └── data/                  # Sample input files
│
├── 02_query_optimization/
│   ├── README.md
│   ├── starter/
│   │   ├── slow_queries.sql   # Queries to optimize
│   │   └── analysis.py
│   └── solution/
│       ├── optimized_queries.sql
│       ├── explain_plans.txt
│       └── benchmark.py
│
├── 03_warehouse_design/
│   ├── README.md
│   ├── starter/
│   │   ├── schema_design.sql  # TODOs for dimensions/facts
│   │   └── sample_queries.sql
│   └── solution/
│       ├── complete_schema.sql
│       ├── load_dimensions.py
│       └── scd_type2_handler.py
```

---

## 🎓 Advanced Topics (Bonus - Week 5+)

- **Change Data Capture (CDC):** Track data changes, audit trails
- **Real-time Processing:** Async event aggregation, windowing
- **Sharding & Partitioning:** Horizontal scaling strategies
- **Data Quality Frameworks:** Great Expectations, dbt tests
- **System Design:** Data lake vs warehouse vs lakehouse

---

## 💡 Interview Tips

### SQL Optimization Interview
1. **Ask clarifying questions:** Scale? Latency? Concurrent users?
2. **Think out loud:** Explain your reasoning
3. **Start simple:** Write correct query first, then optimize
4. **EXPLAIN is your friend:** Show the execution plan
5. **Trade-offs matter:** Discuss pros/cons of different approaches

### System Design Interview
1. **Define the problem:** What are we storing? How much data? Query patterns?
2. **Scale dimensions:** RPS, data volume, latency requirements
3. **Choose tech:** SQL vs NoSQL, batch vs streaming, single region vs geo-distributed
4. **Trade-offs:** Consistency vs availability, latency vs throughput
5. **Validate:** "Does this design handle 10x growth?"

### Project Interview
1. **End-to-end thinking:** How does data flow? Where could it break?
2. **Error handling:** What if this fails? How do you recover?
3. **Monitoring:** How do you know the pipeline is healthy?
4. **Performance:** How fast? How many resources?

---

## 📊 Success Metrics

By end of Week 4, you should be able to:

- [ ] **Explain 5+ data modeling concepts** without looking at notes
- [ ] **Write optimized SQL** that executes efficiently
- [ ] **Design a schema** for a new business problem
- [ ] **Solve 10+ FAANG-style questions** with clear reasoning
- [ ] **Build a complete data pipeline** from scratch
- [ ] **Debug query performance** using EXPLAIN plans
- [ ] **Understand trade-offs:** When to denormalize, shard, index, etc.

---

## 🔗 Next Steps

1. **Read:** Start with `advanced_de_concepts/01_data_modeling.md`
2. **Explore:** Check out `faang_interview_questions/` for realistic scenarios
3. **Code:** Begin `projects/01_etl_pipeline/` by Week 2
4. **Practice:** Work through questions; time yourself on project solutions
5. **Iterate:** Revisit concepts as you encounter them in projects

---

## ❓ FAQ

**Q: Can I skip a week?**  
A: Not recommended. Each week builds on the previous. Week 2 applies concepts from Week 1, etc.

**Q: Should I memorize all questions?**  
A: No. Focus on understanding *why* solutions work. Memorize trade-offs, not code.

**Q: How do I know if I'm ready for FAANG interviews?**  
A: You can explain any project end-to-end, answer questions without notes, and design systems from scratch.

**Q: Can I use this for preparation if I'm not targeting FAANG?**  
A: Absolutely. This is solid data engineering knowledge applicable anywhere.

---

## 🎯 Your FAANG Interview Journey Starts Now

Good luck! 💪
