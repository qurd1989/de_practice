import os
import random
import tracemalloc
from datetime import datetime, timedelta

from faker import Faker

fake = Faker()


# ══════════════════════════════════════════════════════════════
# PART A: Generate the log file
# ══════════════════════════════════════════════════════════════
# We write one line at a time to disk.
# At no point do we hold the entire file in memory.
# This is itself a memory-safe pattern.
# ══════════════════════════════════════════════════════════════

def generate_log_file(filepath, num_lines=500_000):
    levels = ["INFO", "INFO", "INFO", "WARNING", "ERROR"]
    endpoints = [
        "/api/users", "/api/orders", "/api/products",
        "/api/payments", "/api/search", "/api/checkout",
        "/api/inventory", "/api/recommendations"
    ]
    methods = ["GET", "POST", "PUT", "DELETE"]
    base_time = datetime(2024, 1, 1, 0, 0, 0)

    print(f"Generating {num_lines:,} log lines...")

    # 'with open' ensures the file closes automatically even if an error occurs
    # 'w' means write mode — creates the file if it doesn't exist
    with open(filepath, "w", encoding="utf-8") as f:
        for i in range(num_lines):
            timestamp = base_time + timedelta(seconds=i * random.uniform(0.1, 2.0))
            level = random.choice(levels)
            method = random.choice(methods)
            endpoint = random.choice(endpoints)
            status = random.choice([400, 500]) if level == "ERROR" else 200
            duration = round(random.uniform(10, 5000), 2)

            # Build one log line as a string
            # \n at the end means "new line" — each log entry on its own line
            line = (
                f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} "
                f"{level} "
                f"{method} "
                f"{endpoint} "
                f"{status} "
                f"{duration}ms\n"
            )

            # Write this ONE line to disk immediately
            # We don't store it in any list — it's gone from memory
            f.write(line)

    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"Log file created: {filepath} ({size_mb:.1f} MB)\n")


# Create the data folder if it doesn't exist
os.makedirs("data", exist_ok=True)
log_file = "data/server.log"
generate_log_file(log_file)


# ══════════════════════════════════════════════════════════════
# PART B: Parse a single log line into a structured dict
# ══════════════════════════════════════════════════════════════
# A raw log line looks like this:
# "2024-01-01 00:00:01 ERROR POST /api/payments 500 234.5ms"
#
# After line.strip().split() we get a list:
# index 0  → "2024-01-01"       date
# index 1  → "00:00:01"         time
# index 2  → "ERROR"            log level
# index 3  → "POST"             HTTP method
# index 4  → "/api/payments"    endpoint
# index 5  → "500"              HTTP status code
# index 6  → "234.5ms"          duration with "ms" at the end
# ══════════════════════════════════════════════════════════════

def parse_line(line):
    """
    Takes one raw string log line.
    Returns a structured dict, or None if the line is broken/empty.
    """
    try:

        parts = line.strip().split()  # Remove whitespace and split into parts
        if len(parts) < 7:
            return None  # This line is malformed — skip it
        timestamp = datetime(f"{parts[0]} {parts[1]}")  # Placeholder — we won't use it in this problem
        level = parts[2]
        method = parts[3]
        endpoint = parts[4]
        status = int(parts[5])
        duration = float(parts[6].replace("ms"))  # Remove "ms"
        return {
           "timestamp": timestamp,
           "level": level,
           "method": method,
           "endpoint": endpoint,
           "status": status,
           "duration_ms": duration
         }

    except Exception:
      return None  # If any parsing step fails, skip this line


# ══════════════════════════════════════════════════════════════
# PART C: Generator that reads the file in chunks
# ══════════════════════════════════════════════════════════════
# This is the core memory-saving pattern.
#
# Instead of:
#   lines = open(file).readlines()  ← entire file in RAM at once
#
# We do:
#   yield chunk                     ← only chunk_size lines in RAM
#
# The 'yield' keyword is what makes this a generator.
# When Python hits 'yield', it:
#   1. Hands the chunk to whoever called this function
#   2. PAUSES here — remembers exactly where it stopped
#   3. Waits until the caller asks for the next value
#   4. RESUMES from exactly where it paused
#
# This means only ONE chunk exists in memory at any time.
# The previous chunk is garbage collected before the next one loads.
# ══════════════════════════════════════════════════════════════

def read_log_chunks(filepath, chunk_size=1000):
    """
    Opens a file and yields lists of lines, chunk_size at a time.
    Memory usage stays constant no matter how large the file is.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        chunk = []
        # We read the file line by line using a for loop — this is memory efficient
        for line in f:
            chunk.append(line)  # Add this line to our current chunk
            if len(chunk) >= chunk_size:
                yield chunk  # Yield this chunk to the caller
                chunk = []  # Clear the chunk to start fresh
        if chunk:
            yield chunk


# ══════════════════════════════════════════════════════════════
# PART D: Process the entire log file memory-safely
# ══════════════════════════════════════════════════════════════
# This function orchestrates everything:
# - Calls read_log_chunks to get one chunk at a time
# - Parses each line in the chunk
# - Filters for ERROR lines only
# - Counts errors per endpoint
# - Tracks memory throughout
# ══════════════════════════════════════════════════════════════

def process_logs(filepath):
    # Start the memory tracker
    # From this point, Python tracks every byte allocated
    tracemalloc.start()

    # This dict will store our results: { "/api/payments": 1234, ... }
    # This is the ONLY data structure that grows — everything else is temporary
    error_counts = {}

    # Counters for the summary report
    total_lines = 0
    total_errors = 0
    chunks_processed = 0

    print("Processing logs...")

    # read_log_chunks is a generator — this loop asks it for one chunk at a time
    # After each iteration, the previous chunk is discarded from memory
    for chunk in read_log_chunks(filepath, chunk_size=1000):
        chunks_processed += 1

        # Process every line in this chunk
        for line in chunk:
            total_lines += 1

            # Parse the raw string into a structured dict
            record = parse_line(line)

            # If parse_line returned None, skip this line
            if record is None:
                continue

            # We only care about ERROR level logs
            if record["level"] == "ERROR":
                total_errors += 1
                endpoint = record["endpoint"]

                # Initialize the counter for this endpoint if we haven't seen it
                # This is the same pattern from Problem #1
                if endpoint not in error_counts:
                    error_counts[endpoint] = 0

                # Increment the error count for this endpoint
                error_counts[endpoint] += 1

    # Ask tracemalloc for the memory stats
    # current = memory in use RIGHT NOW
    # peak    = highest memory usage we hit during processing
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Print the processing summary
    print(f"Chunks processed:  {chunks_processed:,}")
    print(f"Lines processed:   {total_lines:,}")
    print(f"Errors found:      {total_errors:,}")
    print(f"Peak memory used:  {peak / 1024 / 1024:.2f} MB")

    # Return the error counts dict for further analysis
    return error_counts


# ══════════════════════════════════════════════════════════════
# PART E: Run everything and display results
# ══════════════════════════════════════════════════════════════

# This calls process_logs which internally calls read_log_chunks
# which internally calls parse_line — the full pipeline runs here
error_counts = process_logs(log_file)

# Sort the dict by value (error count) in descending order
# .items() gives us (endpoint, count) pairs
# key=lambda x: x[1] sorts by the count (index 1 of each pair)
# reverse=True means highest first
# [:5] takes only the first 5 results
top_5 = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]

print("\nTop 5 Failing Endpoints:")
print("━" * 42)
print(f"{'Rank':<6} {'Endpoint':<25} {'Errors':>8}")
print("━" * 42)
for rank, (endpoint, count) in enumerate(top_5, 1):
    # enumerate(top_5, 1) gives us (1, first_item), (2, second_item) etc.
    # We unpack: rank=1, (endpoint, count) = ("/api/payments", 1234)
    print(f"{rank:<6} {endpoint:<25} {count:>8,}")
