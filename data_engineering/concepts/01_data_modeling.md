# Data Modeling Fundamentals

*Why this matters in FAANG interviews: How you model data determines query performance, scalability, and maintainability.*

---

## What is Data Modeling?

**Data modeling** is the process of designing how data is organized, stored, and related in a database. It answers:
- What entities do we have? (Users, Orders, Products)
- How do they relate? (One user has many orders)
- What properties does each entity have? (User has email, phone, name)
- How do we query this efficiently?

---

## Three Levels of Data Modeling

### 1. Conceptual Model (What exists?)
High-level entities and relationships, **no implementation details**

```
User ───────── [has many] ─────── Order
  │                                  │
  │                          [contains many]
  │                                  │
  └────── [has many] ──────── Product
```

### 2. Logical Model (How are they related?)
Detailed attributes, relationships, and constraints, **DB-agnostic**

```
User (user_id, email, name, phone, created_at)
  ├─ PK: user_id
  └─ Relationship: 1 User → N Orders

Order (order_id, user_id, order_date, total_amount)
  ├─ PK: order_id
  ├─ FK: user_id → User
  └─ Relationship: 1 Order → N OrderItems

OrderItem (order_item_id, order_id, product_id, quantity, price)
  ├─ PK: order_item_id
  ├─ FK: order_id → Order
  └─ FK: product_id → Product

Product (product_id, name, price, category)
  ├─ PK: product_id
```

### 3. Physical Model (How is it stored?)
Implementation in a specific database (MySQL, PostgreSQL, etc.), data types, indexes

```sql
CREATE TABLE users (
    user_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    phone VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_created_at (created_at)
);

CREATE TABLE orders (
    order_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_id (user_id),
    INDEX idx_order_date (order_date)
);
```

---

## Normalization vs Denormalization

### Normalization (3NF) — "Reduce Redundancy"

**Goal:** Minimize data duplication, ensure data integrity

**Normal Forms:**
- **1NF:** Atomic values only (no arrays/objects)
- **2NF:** Remove partial dependencies (non-key attributes depend on full primary key)
- **3NF:** Remove transitive dependencies (non-key attributes don't depend on other non-keys)

**Example - Normalized:**
```sql
-- Separate tables, no duplication
users: user_id, email, name
orders: order_id, user_id, order_date
order_items: order_item_id, order_id, product_id, quantity
products: product_id, name, price
```

**Pros:** ✅ Reduced storage, ✅ Easy updates (single place of truth), ✅ Fewer anomalies  
**Cons:** ❌ Slower reads (more joins), ❌ More complex queries, ❌ Higher query latency

---

### Denormalization — "Optimize for Reads"

**Goal:** Improve query performance by trading storage for speed

**Example - Denormalized:**
```sql
-- Pre-join data for faster reads
orders_with_user_details:
  order_id, order_date, total_amount,
  user_id, user_email, user_name,  -- Duplicated from users
  product_name, product_price       -- Duplicated from products
```

**Pros:** ✅ Faster reads (fewer joins), ✅ Simpler queries, ✅ Lower latency  
**Cons:** ❌ Increased storage, ❌ Update anomalies (must update multiple places), ❌ Complex write logic

---

## When to Normalize vs Denormalize

| Scenario | Approach | Reason |
|----------|----------|--------|
| **User management system** | Normalize | Frequent updates, write-heavy |
| **Analytics warehouse** | Denormalize | Read-heavy, complex queries |
| **Real-time transactional system** | Normalize | ACID compliance, consistency |
| **Data lake** | Denormalize | Fast queries on immutable data |
| **NoSQL (MongoDB)** | Denormalize | Natural denormalization model |

**FAANG Rule of Thumb:**
- Start normalized (correctness)
- Denormalize strategically (performance)
- Profile & measure before optimizing

---

## FAANG Interview Questions on Data Modeling

### Q1: "Design a schema for an e-commerce platform"

**What they're looking for:**
- Identify key entities (User, Product, Order, Payment, etc.)
- Define relationships (1:1, 1:N, M:N)
- Show normalization understanding
- Consider scale & performance

**Example Answer:**
```sql
-- Users
CREATE TABLE users (
    user_id BIGINT PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(20),
    created_at DATETIME
);

-- Products
CREATE TABLE products (
    product_id BIGINT PRIMARY KEY,
    name VARCHAR(255),
    price DECIMAL(10, 2),
    category_id INT,
    inventory INT
);

-- Orders (1 user → N orders)
CREATE TABLE orders (
    order_id BIGINT PRIMARY KEY,
    user_id BIGINT,
    order_date DATETIME,
    total DECIMAL(10, 2),
    status ENUM('pending', 'shipped', 'delivered'),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_id (user_id)
);

-- Order Items (M:N relationship between orders & products)
CREATE TABLE order_items (
    order_item_id BIGINT PRIMARY KEY,
    order_id BIGINT,
    product_id BIGINT,
    quantity INT,
    price DECIMAL(10, 2),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);
```

**Discussion Points:**
- Why separate `orders` and `order_items`? (Normalize item details)
- Why store `price` in `order_items`? (Historical pricing, not always current)
- What about `customers`? (Could be same as `users` or separate)
- How do you handle denormalization for analytics? (Fact tables in warehouse)

---

### Q2: "This query is slow. How would you model the data differently?"

**What they're looking for:**
- Understanding of access patterns
- Ability to optimize schema for specific queries
- Trade-off analysis

**Slow Query Example:**
```sql
SELECT u.user_id, u.email, COUNT(o.order_id) as order_count
FROM users u
LEFT JOIN orders o ON u.user_id = o.user_id
GROUP BY u.user_id, u.email;
```

**Optimization Strategies:**
1. **Add an index:** Speed up JOIN
   ```sql
   CREATE INDEX idx_orders_user_id ON orders(user_id);
   ```

2. **Denormalize:** Store aggregate in users table
   ```sql
   ALTER TABLE users ADD COLUMN order_count INT DEFAULT 0;
   -- Update when orders are added (trigger or batch job)
   ```

3. **Use materialized view:** Pre-compute and cache
   ```sql
   CREATE TABLE user_order_stats AS
   SELECT u.user_id, u.email, COUNT(o.order_id) as order_count
   FROM users u
   LEFT JOIN orders o ON u.user_id = o.user_id
   GROUP BY u.user_id, u.email;
   ```

---

## Key Takeaways

| Concept | Remember |
|---------|----------|
| **Normalization** | Reduces redundancy, ensures consistency, best for transactional systems |
| **Denormalization** | Improves query speed, increases storage, best for analytics |
| **Entities & Relationships** | Identify clearly before implementation |
| **Keys** | Primary keys identify rows; foreign keys create relationships |
| **Normal Forms** | 3NF is standard for transactional databases |
| **Grain** | In dimensional modeling, fact table grain determines query patterns |

---

## Practice Exercise

**Design a schema for a social media platform (like Twitter):**

What entities do you need?
- [ ] Users (followers, profile)
- [ ] Tweets/Posts
- [ ] Likes
- [ ] Comments
- [ ] Follows

How are they related?
- [ ] 1 user → N tweets
- [ ] M:N relationship between users (followers)
- [ ] 1 tweet → N likes/comments

What's your normalization approach?
- [ ] Fully normalized? Why/why not?
- [ ] Where might you denormalize? (e.g., retweet count, favorite count)

---

**Next:** Read `02_indexing_partitioning.md` to learn how indexes improve query performance on normalized schemas.
