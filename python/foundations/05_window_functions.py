from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()


# ── Generate sales data ───────────────────────────────────────────────
def generate_sales(num_reps=5, num_sales=20):
    reps = [f"rep_{i}" for i in range(num_reps)]
    regions = ["North", "South", "East", "West"]
    sales = []
    base = datetime(2024, 1, 1)

    for _ in range(num_sales):
        sales.append({
            "sale_id":    fake.uuid4()[:8],
            "rep_id":     random.choice(reps),
            "region":     random.choice(regions),
            "amount":     round(random.uniform(100, 10000), 2),
            "sale_date":  base + timedelta(days=random.randint(0, 90))
        })

    return sorted(sales, key=lambda x: x["sale_date"])


sales = generate_sales()


# ════════════════════════════════════════════════════════════════════
# WINDOW FUNCTION 1: ROW_NUMBER
# "For each rep, number their sales from first to most recent"
# Real use: find each customer's most recent order
# ════════════════════════════════════════════════════════════════════

def row_number(records, partition_by, order_by):
    """
    Assigns a sequential number to each row within a partition.
    Equivalent to: ROW_NUMBER() OVER (PARTITION BY x ORDER BY y)
    """
    from collections import defaultdict
    groups = defaultdict(list)

    for record in records:
        key = record[partition_by]
        groups[key].append(record)

    result = []
    for key, group in groups.items():
        group.sort(key=lambda x: x[order_by])
        for i, record in enumerate(group):
            result.append({**record, "row_number": i + 1})

    return result


numbered = row_number(sales, partition_by="rep_id", order_by="sale_date")

print("═" * 65)
print("WINDOW 1: ROW_NUMBER — Sales numbered per rep by date")
print("═" * 65)
print(f"{'rep_id':<10} {'sale_date':<15} {'amount':>10} {'row_num':>8}")
print("-" * 65)
for row in sorted(numbered, key=lambda x: (x["rep_id"], x["row_number"])):
    print(f"{row['rep_id']:<10} "
          f"{str(row['sale_date'].date()):<15} "
          f"${row['amount']:>9,.2f} "
          f"{row['row_number']:>8}")


# ════════════════════════════════════════════════════════════════════
# WINDOW FUNCTION 2: RUNNING TOTAL
# "For each rep, show cumulative sales as of each transaction"
# Real use: running revenue totals on dashboards
# ════════════════════════════════════════════════════════════════════

def running_total(records, partition_by, order_by, value_col):
    """
    Cumulative sum within each partition ordered by a column.
    Equivalent to: SUM(amount) OVER (PARTITION BY x ORDER BY y
                   ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
    """
    from collections import defaultdict
    groups = defaultdict(list)

    for record in records:
        groups[record[partition_by]].append(record)

    result = []
    for key, group in groups.items():
        group.sort(key=lambda x: x[order_by])
        cumulative = 0
        for record in group:
            cumulative += record[value_col]
            result.append({**record, "running_total": round(cumulative, 2)})

    return result


totals = running_total(sales, partition_by="rep_id",
                       order_by="sale_date", value_col="amount")

print("\n" + "═" * 75)
print("WINDOW 2: RUNNING TOTAL — Cumulative sales per rep")
print("═" * 75)
print(f"{'rep_id':<10} {'sale_date':<15} {'amount':>10} {'running_total':>15}")
print("-" * 75)
for row in sorted(totals, key=lambda x: (x["rep_id"], x["sale_date"])):
    print(f"{row['rep_id']:<10} "
          f"{str(row['sale_date'].date()):<15} "
          f"${row['amount']:>9,.2f} "
          f"${row['running_total']:>13,.2f}")


# ════════════════════════════════════════════════════════════════════
# WINDOW FUNCTION 3: LAG
# "For each rep, what was their PREVIOUS sale amount?"
# Real use: detect drops in sales, calculate day-over-day change
# ════════════════════════════════════════════════════════════════════

def lag(records, partition_by, order_by, value_col, offset=1):
    """
    Returns the value from N rows BEFORE the current row in the partition.
    Equivalent to: LAG(amount, 1) OVER (PARTITION BY x ORDER BY y)
    """
    from collections import defaultdict
    groups = defaultdict(list)

    for record in records:
        groups[record[partition_by]].append(record)

    result = []
    for key, group in groups.items():
        group.sort(key=lambda x: x[order_by])
        for i, record in enumerate(group):
            prev_value = group[i - offset][value_col] if i >= offset else None
            change = None
            if prev_value is not None:
                change = round(record[value_col] - prev_value, 2)
            result.append({
                **record,
                "prev_amount": prev_value,
                "change":      change
            })

    return result


lagged = lag(sales, partition_by="rep_id",
             order_by="sale_date", value_col="amount")

print("\n" + "═" * 80)
print("WINDOW 3: LAG — Previous sale and change per rep")
print("═" * 80)
print(f"{'rep_id':<10} {'date':<12} {'amount':>10} {'prev':>10} {'change':>10}")
print("-" * 80)
for row in sorted(lagged, key=lambda x: (x["rep_id"], x["sale_date"])):
    prev  = f"${row['prev_amount']:>8,.2f}" if row['prev_amount'] else "     N/A"
    chng  = f"${row['change']:>+8,.2f}"     if row['change']      else "     N/A"
    print(f"{row['rep_id']:<10} "
          f"{str(row['sale_date'].date()):<12} "
          f"${row['amount']:>9,.2f} "
          f"{prev:>10} "
          f"{chng:>10}")


# ════════════════════════════════════════════════════════════════════
# WINDOW FUNCTION 4: RANK
# "Rank each rep by total sales — who is #1?"
# Real use: leaderboards, top-N analysis, percentile bucketing
# ════════════════════════════════════════════════════════════════════

def rank_by_total(records, partition_by, value_col):
    """
    Ranks groups by their total value, highest first.
    Equivalent to: RANK() OVER (ORDER BY SUM(amount) DESC)
    """
    from collections import defaultdict
    totals = defaultdict(float)

    for record in records:
        totals[record[partition_by]] += record[value_col]

    ranked = sorted(totals.items(), key=lambda x: x[1], reverse=True)

    print("\n" + "═" * 45)
    print("WINDOW 4: RANK — Reps by total revenue")
    print("═" * 45)
    print(f"{'rank':<6} {'rep_id':<12} {'total_sales':>12}")
    print("-" * 45)
    for rank, (rep, total) in enumerate(ranked, 1):
        print(f"{rank:<6} {rep:<12} ${total:>11,.2f}")


rank_by_total(sales, partition_by="rep_id", value_col="amount")