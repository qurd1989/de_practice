# Project 1: Build a Complete ETL Pipeline

## Objective
Build an end-to-end ETL (Extract → Transform → Load) pipeline that processes e-commerce data from CSV files into a database. This mirrors real-world data engineering work.

## What You'll Learn
- ✅ Reading data from multiple sources (CSV files)
- ✅ Data validation & cleaning (handling nulls, duplicates, invalid data)
- ✅ Batch processing (loading 10K+ rows efficiently)
- ✅ Error handling & recovery (transactions, rollbacks)
- ✅ Idempotency (safe to re-run without duplicates)
- ✅ Monitoring & logging (track progress, errors, metrics)

## Timeline
**Duration:** 4-6 hours  
**Difficulty:** Intermediate

## Business Context
**Scenario:** E-commerce company receives daily sales data as CSV files. You need to:
1. Read CSVs from a local folder
2. Clean and validate the data
3. Load into MySQL
4. Generate a summary report

**Data Schema:**
- `users.csv` — User profiles (user_id, email, name, signup_date)
- `products.csv` — Product catalog (product_id, name, price, category)
- `orders.csv` — Order transactions (order_id, user_id, product_id, order_date, quantity, total)

---

## Part 1: Setup

### Prerequisites
```powershell
# Activate venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install pandas mysql-connector-python
```

### Create Database Schema
```sql
-- Run in MySQL
USE analytics;

CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(200),
    signup_date DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    product_id BIGINT PRIMARY KEY,
    name VARCHAR(255),
    price DECIMAL(10, 2),
    category VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    order_id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    order_date DATE,
    quantity INT,
    total DECIMAL(10, 2),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id),
    INDEX idx_user_id (user_id),
    INDEX idx_order_date (order_date)
);
```

### Generate Sample Data
```python
# Run: python datasets/generate_ecommerce_data.py
# This creates CSV files in data/raw/
```

---

## Part 2: Your Task (STARTER)

Create `projects/01_etl_pipeline/starter/etl_pipeline.py` with these TODOs:

```python
import pandas as pd
import mysql.connector
import logging
from pathlib import Path
from datetime import datetime

# TODO 1: Configure logging
logger = logging.getLogger(__name__)
# Set up logging to console and file

# TODO 2: Create get_db_connection() function
def get_db_connection():
    """
    Connect to MySQL database
    Return: mysql.connector.MySQLConnection
    """
    pass

# TODO 3: Create extract_csv() function
def extract_csv(file_path):
    """
    Read CSV file and return as list of rows
    - Handle file not found errors
    - Return empty list if file missing
    """
    pass

# TODO 4: Create transform_users() function
def transform_users(df):
    """
    Clean and validate user data
    - Remove duplicates by email
    - Drop rows with missing user_id
    - Convert signup_date to DATE format
    - Return cleaned DataFrame
    """
    pass

# TODO 5: Create transform_products() function
def transform_products(df):
    """
    Clean and validate product data
    - Remove duplicates by product_id
    - Ensure price > 0
    - Drop missing required fields
    """
    pass

# TODO 6: Create transform_orders() function
def transform_orders(df):
    """
    Clean and validate order data
    - Remove duplicates by order_id
    - Ensure quantity > 0 and total > 0
    - Validate user_id and product_id exist
    """
    pass

# TODO 7: Create load_batch() function
def load_batch(conn, table_name, df, batch_size=1000):
    """
    Load DataFrame rows into database in batches
    - Use transactions for atomicity
    - Handle duplicates (INSERT ... ON DUPLICATE KEY UPDATE)
    - Log progress
    - Return: (successful_count, failed_count)
    """
    pass

# TODO 8: Create generate_report() function
def generate_report(conn):
    """
    Query database and generate summary report
    - Total rows in each table
    - Date range of orders
    - Top 5 products by order count
    - Return as dictionary
    """
    pass

# TODO 9: Create main() function
def main(data_folder='data/raw'):
    """
    Main ETL pipeline orchestration
    1. Extract: Read CSVs
    2. Transform: Clean data
    3. Load: Insert into database
    4. Report: Generate summary
    """
    start_time = datetime.now()
    
    # TODO: Implement the full pipeline
    # Hint: Extract → Transform → Load for each CSV file
    # Handle errors gracefully
    
    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info(f"Pipeline completed in {elapsed:.2f} seconds")

if __name__ == '__main__':
    main()
```

---

## Part 3: Testing Checklist

Before submitting, verify:

- [ ] Script runs without errors
- [ ] All CSVs are read successfully
- [ ] Database is populated with data
- [ ] Duplicates are handled correctly
- [ ] Invalid records are skipped or logged
- [ ] Summary report is generated
- [ ] Logging shows progress and errors
- [ ] Can re-run script without duplicating data (idempotency)

**Run test:**
```powershell
python projects/01_etl_pipeline/starter/etl_pipeline.py
```

**Expected output:**
```
2024-03-15 10:30:00 - INFO - Starting ETL pipeline...
2024-03-15 10:30:05 - INFO - Extracted users.csv: 10000 rows
2024-03-15 10:30:08 - INFO - Transformed users: 9950 valid, 50 duplicates removed
2024-03-15 10:30:15 - INFO - Loaded users: 9950 rows in 1.5 seconds
...
2024-03-15 10:31:00 - INFO - === SUMMARY REPORT ===
2024-03-15 10:31:00 - INFO - Total Users: 9950
2024-03-15 10:31:00 - INFO - Total Products: 500
2024-03-15 10:31:00 - INFO - Total Orders: 50000
2024-03-15 10:31:00 - INFO - Pipeline completed in 60.42 seconds
```

---

## Part 4: Learning Questions

After completing, answer these (verbally or written):

1. **Idempotency:** Why is `ON DUPLICATE KEY UPDATE` important? What happens if you re-run without it?

2. **Batch Size:** Why do we batch inserts (1000 rows at a time) instead of inserting all rows at once?

3. **Error Handling:** What should happen if one product in an order doesn't exist in the products table? (Foreign key violation)

4. **Performance:** How would you optimize this pipeline for 100M rows? (Parallel processing? Streaming?)

5. **Data Quality:** How do you detect that 50 duplicate users were removed? How would you investigate why?

---

## Bonus Challenges (If time allows)

### Challenge 1: Parallel Loading
Currently, you load users, then products, then orders sequentially.  
**Goal:** Load all three in parallel using threading or async.  
**Benefit:** ~3x faster for 3 independent tables

### Challenge 2: Data Quality Validation
Add a validation step that checks:
- All user_ids in orders exist in users table
- All product_ids in orders exist in products table
- No negative quantities or prices
- Order dates are within valid range

### Challenge 3: Incremental Loading
Modify to support incremental loads:
- Track "last_load_timestamp"
- Only process files modified since last load
- Append new orders, update existing user info

### Challenge 4: Cloud Storage
Instead of reading from local CSV files, read from S3:
```python
import boto3
s3 = boto3.client('s3')
obj = s3.get_object(Bucket='my-bucket', Key='data/users.csv')
df = pd.read_csv(obj['Body'])
```

---

## Next Steps

After completing this project:
1. Compare your solution with `solution/etl_pipeline.py`
2. Learn what you did differently (and why)
3. Discuss during mock interview: "Walk me through your ETL pipeline"

Good luck! 💪
