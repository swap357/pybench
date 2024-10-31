"""
Test to measure GIL contention patterns.
Shows how GIL affects CPU-bound threads competing for execution.

Purpose:
- Measure GIL contention overhead
- Compare thread scheduling patterns
- Evaluate CPU-bound thread competition
- Baseline for no-GIL comparison
"""
import time
import sys
import threading
from benchmarks.utils import get_total_threads

def cpu_intensive():
    """Pure CPU work to force GIL contention"""
    result = 0
    for i in range(1_000_000):
        result += i * i
    return result

def main():
    total_threads = get_total_threads()
    threads = []
    results = []
    start = time.time()
    
    def worker():
        result = cpu_intensive()
        results.append(result)
    
    # Create and start CPU-bound threads
    for _ in range(total_threads):
        thread = threading.Thread(target=worker)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())