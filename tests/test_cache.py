"""Test resort caching — first run fetches, second run loads from cache."""

import sys
import time
sys.path.insert(0, "src")

from resorts import load_resorts, get_resort, CACHE_FILE
import os

# --- Run 1: fetch from Overpass (or use existing cache) ---
start = time.time()
resorts = load_resorts()
elapsed = time.time() - start
print(f"Run 1: {len(resorts)} resorts loaded in {elapsed:.1f}s")

# Verify cache file was created
cache_exists = os.path.exists(CACHE_FILE)
cache_size = os.path.getsize(CACHE_FILE) if cache_exists else 0
print(f"Cache file exists: {cache_exists} ({cache_size / 1024:.0f} KB)")

# --- Run 2: should load from cache (fast) ---
start = time.time()
resorts = load_resorts()
elapsed = time.time() - start
print(f"Run 2: {len(resorts)} resorts loaded in {elapsed:.1f}s (from cache)")

# Verify lookups still work from cached data
r = get_resort("Vail")
print(f"Lookup test: {r.name} -> {r.nearest_airport}" if r else "Lookup test: FAILED")
