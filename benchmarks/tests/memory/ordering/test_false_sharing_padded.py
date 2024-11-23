"""
Test demonstrating false sharing mitigation using padding.
Shows performance improvement when counters are cache-line padded.

Purpose:
- Show false sharing mitigation
- Demonstrate padding effectiveness
- Measure isolated thread performance
- Compare with baseline version
"""
import time
import sys
import threading
import array
import ctypes
from benchmarks.utils import get_total_threads

def main():
    iterations = 1_000_000
    # Use environment variable or default to 4
    num_threads = get_total_threads()
    threads = []
    
    # Calculate padding to align with cache lines
    cache_line = 64  # Common cache line size
    padding = cache_line // ctypes.sizeof(ctypes.c_ulonglong)
    padded_size = num_threads * padding
    
    # Create padded array with counters separated by cache line size
    counters = array.array('Q', [0] * padded_size)
    
    def worker(index):
        # Each thread updates its own counter
        # Counters are separated by cache line size
        counter_index = index * padding
        for _ in range(iterations):
            counters[counter_index] += 1
    
    # Create and start threads
    for i in range(num_threads):
        thread = threading.Thread(target=worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())