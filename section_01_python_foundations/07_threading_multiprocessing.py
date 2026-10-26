import os
import json
import gzip
import time
import random
import hashlib
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from faker import Faker

fake = Faker()


# ══════════════════════════════════════════════════════════════
# SETUP — Generate fake JSON log files to process
# SRP: this function only generates test data
# ══════════════════════════════════════════════════════════════

def generate_log_files(output_dir, num_files=8, lines_per_file=10_000):
    """
    Creates multiple JSON log files simulating
    logs from different servers.
    Each file = one server's logs for one hour.
    """
    os.makedirs(output_dir, exist_ok=True)
    filepaths = []

    endpoints = [
        "/api/users", "/api/orders", "/api/products",
        "/api/payments", "/api/search", "/api/checkout"
    ]
    levels  = ["INFO", "INFO", "INFO", "WARNING", "ERROR"]
    base    = datetime(2024, 1, 1)

    print(f"Generating {num_files} log files ({lines_per_file:,} lines each)...")

    for file_num in range(num_files):
        filepath = os.path.join(output_dir, f"server_{file_num:02d}.json")
        records  = []

        for i in range(lines_per_file):
            records.append({
                "timestamp": (base + timedelta(seconds=i)).isoformat(),
                "server_id": f"server_{file_num:02d}",
                "level":     random.choice(levels),
                "endpoint":  random.choice(endpoints),
                "status":    random.choice([200, 200, 200, 400, 500]),
                "duration":  round(random.uniform(10, 5000), 2),
                "user_id":   random.randint(1, 100_000),
                "request_id": fake.uuid4()
            })

        # Write as JSON lines format (one JSON object per line)
        # This is a real production format — used by Kafka, Spark, dbt
        with open(filepath, "w") as f:
            for record in records:
                f.write(json.dumps(record) + "\n")

        filepaths.append(filepath)

    print(f"Generated {num_files} files in {output_dir}/\n")
    return filepaths


# ══════════════════════════════════════════════════════════════
# CORE PROCESSING FUNCTION
# SRP: does ONE thing — process a single file
# DIP: takes filepath as input, doesn't hardcode paths
# This is the function all three approaches will call
# ══════════════════════════════════════════════════════════════

def process_file(filepath):
    """
    Processes one log file:
    1. Read raw JSON lines        (I/O bound)
    2. Parse and transform each   (CPU bound)
    3. Compute a checksum         (CPU bound — simulates heavy computation)
    4. Compress to gzip           (CPU bound)
    5. Write compressed output    (I/O bound)

    Returns a dict with processing stats.
    SRP: only processes one file — doesn't know about
         threading, multiprocessing, or orchestration.
    """
    start = time.time()

    # ── Step 1: Read raw file (I/O bound) ──────────────────
    with open(filepath, "r") as f:
        lines = f.readlines()

    # ── Step 2: Parse and transform (CPU bound) ────────────
    transformed = []
    error_count = 0

    for line in lines:
        try:
            record = json.loads(line.strip())

            # Transform: add computed fields
            # This simulates real transformation work
            record["processed_at"] = datetime.now().isoformat()
            record["is_error"]     = record["status"] >= 400
            record["duration_bucket"] = (
                "fast"   if record["duration"] < 100  else
                "medium" if record["duration"] < 1000 else
                "slow"
            )

            # Simulate CPU-intensive work:
            # compute a hash of the request_id
            # In real pipelines: JSON parsing, type casting,
            # regex matching, ML feature computation
            record["checksum"] = hashlib.md5(
                record["request_id"].encode()
            ).hexdigest()

            if record["is_error"]:
                error_count += 1

            transformed.append(record)

        except Exception:
            continue

    # ── Step 3: Compress output (CPU bound) ────────────────
    # gzip compression is CPU-intensive
    # In production: Parquet files are compressed this way
    output_path = filepath.replace(".json", ".jsonl.gz")
    compressed_data = json.dumps(transformed).encode("utf-8")

    with gzip.open(output_path, "wb") as f:
        f.write(compressed_data)

    elapsed = time.time() - start

    return {
        "file":        os.path.basename(filepath),
        "records":     len(transformed),
        "errors":      error_count,
        "output":      os.path.basename(output_path),
        "time":        round(elapsed, 3)
    }


# ══════════════════════════════════════════════════════════════
# APPROACH 1: Sequential — one file at a time (baseline)
# ══════════════════════════════════════════════════════════════

def run_sequential(filepaths):
    print("─" * 55)
    print("APPROACH 1: Sequential")
    print("─" * 55)
    start   = time.time()
    results = [process_file(fp) for fp in filepaths]
    elapsed = time.time() - start

    for r in results:
        print(f"  {r['file']:<20} {r['records']:>7,} records "
              f"| {r['errors']:>4} errors "
              f"| {r['time']}s")

    print(f"\n  Total time: {elapsed:.2f}s")
    return elapsed


# ══════════════════════════════════════════════════════════════
# APPROACH 2: ThreadPoolExecutor
# Good for I/O-bound work — limited by Python's GIL for CPU work
# ══════════════════════════════════════════════════════════════

def run_threaded(filepaths, max_workers=4):
    print("\n" + "─" * 55)
    print(f"APPROACH 2: ThreadPoolExecutor (workers={max_workers})")
    print("─" * 55)
    start = time.time()

    # ThreadPoolExecutor manages a pool of threads
    # .map() distributes filepaths across threads automatically
    # Results come back in the same order as inputs
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_file, filepaths))

    elapsed = time.time() - start

    for r in results:
        print(f"  {r['file']:<20} {r['records']:>7,} records "
              f"| {r['errors']:>4} errors "
              f"| {r['time']}s")

    print(f"\n  Total time: {elapsed:.2f}s")
    return elapsed


# ══════════════════════════════════════════════════════════════
# APPROACH 3: ProcessPoolExecutor
# True parallelism — each process has its own Python interpreter
# Best for CPU-bound work like parsing, transforming, compressing
# ══════════════════════════════════════════════════════════════

def run_multiprocess(filepaths, max_workers=4):
    print("\n" + "─" * 55)
    print(f"APPROACH 3: ProcessPoolExecutor (workers={max_workers})")
    print("─" * 55)
    start = time.time()

    # ProcessPoolExecutor spawns separate Python processes
    # Each process has its own GIL — true CPU parallelism
    # Overhead: spawning processes takes time
    # Worth it when: CPU work per task is significant
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_file, filepaths))

    elapsed = time.time() - start

    for r in results:
        print(f"  {r['file']:<20} {r['records']:>7,} records "
              f"| {r['errors']:>4} errors "
              f"| {r['time']}s")

    print(f"\n  Total time: {elapsed:.2f}s")
    return elapsed


# ══════════════════════════════════════════════════════════════
# MAIN — Run all three and compare
# ══════════════════════════════════════════════════════════════

# Required on Windows — multiprocessing needs this guard
if __name__ == "__main__":

    # Generate test files
    LOG_DIR   = "data/logs"
    filepaths = generate_log_files(LOG_DIR, num_files=8, lines_per_file=10_000)

    # Run all three approaches
    seq_time    = run_sequential(filepaths)
    thread_time = run_threaded(filepaths, max_workers=4)
    proc_time   = run_multiprocess(filepaths, max_workers=4)

    # ── Summary ────────────────────────────────────────────
    print("\n" + "═" * 55)
    print("SUMMARY")
    print("═" * 55)
    print(f"  Sequential:       {seq_time:.2f}s  (baseline)")
    print(f"  Threading:        {thread_time:.2f}s  "
          f"({seq_time/thread_time:.1f}x faster)")
    print(f"  Multiprocessing:  {proc_time:.2f}s  "
          f"({seq_time/proc_time:.1f}x faster)")
    print()
    print("  WHAT THE RESULTS TELL YOU:")
    print(f"  → Threading speedup shows I/O benefit")
    print(f"  → Multiprocessing speedup shows CPU parallelism")
    print(f"  → Gap between them = GIL impact on CPU work")
    print("═" * 55)