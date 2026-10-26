import asyncio
import aiohttp
import requests
import time
import random

# ══════════════════════════════════════════════════════════════
# We'll use a free public API that returns fake user data
# https://jsonplaceholder.typicode.com/users/{id}
# It returns a JSON object for each user ID (1-10)
# ══════════════════════════════════════════════════════════════

USER_IDS = list(range(1, 11)) * 10  # 100 requests (IDs 1-10 repeated 10 times)
BASE_URL = "https://jsonplaceholder.typicode.com/users"


# ══════════════════════════════════════════════════════════════
# APPROACH 1: Synchronous — one request at a time
# ══════════════════════════════════════════════════════════════

def fetch_user_sync(user_id):
    """Fetch one user synchronously using requests library"""
    response = requests.get(f"{BASE_URL}/{user_id}")
    return response.json()


def fetch_all_sync(user_ids):
    """Fetch all users one by one — sequential, blocking"""
    results = []
    for uid in user_ids:
        user = fetch_user_sync(uid)
        results.append(user)
    return results


# ══════════════════════════════════════════════════════════════
# APPROACH 2: Asynchronous — all requests simultaneously
# ══════════════════════════════════════════════════════════════

async def fetch_user_async(session, user_id):
    """
    Fetch one user asynchronously.
    'async def' means this function can be paused.
    'await' means pause here while the HTTP request is in flight.
    While paused, other fetch_user_async calls can run.
    """
    async with session.get(f"{BASE_URL}/{user_id}") as response:
        return await response.json()


async def fetch_all_async(user_ids):
    """
    Fetch all users simultaneously.
    aiohttp.ClientSession is the async version of requests.Session
    asyncio.gather() fires all coroutines at the same time
    """
    async with aiohttp.ClientSession() as session:
        # Build a list of coroutines — not started yet, just defined
        tasks = [fetch_user_async(session, uid) for uid in user_ids]

        # Fire ALL tasks simultaneously and wait for all to complete
        results = await asyncio.gather(*tasks)
        return results


# ══════════════════════════════════════════════════════════════
# APPROACH 3: Async with error handling — production ready
# ══════════════════════════════════════════════════════════════

async def fetch_user_safe(session, user_id):
    """
    Same as fetch_user_async but handles failures gracefully.
    In production APIs fail — timeouts, rate limits, server errors.
    We catch the error and return None instead of crashing.
    """
    try:
        async with session.get(
            f"{BASE_URL}/{user_id}",
            timeout=aiohttp.ClientTimeout(total=5)  # 5 second timeout
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                print(f"  ⚠ User {user_id} returned status {response.status}")
                return None
    except asyncio.TimeoutError:
        print(f"  ⚠ User {user_id} timed out")
        return None
    except Exception as e:
        print(f"  ⚠ User {user_id} failed: {e}")
        return None


async def fetch_all_safe(user_ids):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_user_safe(session, uid) for uid in user_ids]
        results = await asyncio.gather(*tasks)
        # Filter out None results
        return [r for r in results if r is not None]


# ══════════════════════════════════════════════════════════════
# RUN ALL THREE AND COMPARE
# ══════════════════════════════════════════════════════════════

print("=" * 55)
print("APPROACH 1: Synchronous")
print("=" * 55)
start = time.time()
sync_results = fetch_all_sync(USER_IDS)
sync_time = time.time() - start
print(f"Fetched:    {len(sync_results)} users")
print(f"Time taken: {sync_time:.2f} seconds")

print()
print("=" * 55)
print("APPROACH 2: Asynchronous")
print("=" * 55)
start = time.time()
async_results = asyncio.run(fetch_all_async(USER_IDS))
async_time = time.time() - start
print(f"Fetched:    {len(async_results)} users")
print(f"Time taken: {async_time:.2f} seconds")

print()
print("=" * 55)
print("APPROACH 3: Async with error handling")
print("=" * 55)
start = time.time()
safe_results = asyncio.run(fetch_all_safe(USER_IDS))
safe_time = time.time() - start
print(f"Fetched:    {len(safe_results)} users")
print(f"Time taken: {safe_time:.2f} seconds")

print()
print("=" * 55)
print("SUMMARY")
print("=" * 55)
print(f"Sync time:       {sync_time:.2f}s")
print(f"Async time:      {async_time:.2f}s")
print(f"Safe async time: {safe_time:.2f}s")
print(f"Speedup:         {sync_time / async_time:.1f}x faster with async")