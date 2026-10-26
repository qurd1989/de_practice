# file: undervalued_stocks/config.py
from pathlib import Path

# output / cache
OUTPUT_FILE = Path("undervalued_stocks.csv")
CACHE_FILE = Path("ticker_fundamentals_cache.parquet")

# screener params
TOP_N = 100
MIN_MARKET_CAP   = 2_000_000_000
MAX_FORWARD_PE   = 35
MIN_OFF_HIGH_PCT = 0.15    # must be at least 15% off 52w high
MAX_3MO_RETURN   = 0.0     # must be flat or down over last 3 months
BATCH_SIZE       = 25
SLEEP_BETWEEN    = 0.3
MIN_VALID_ROWS   = 50

# Web fetch user-agent (Wikipedia blocks default urllib UA)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"