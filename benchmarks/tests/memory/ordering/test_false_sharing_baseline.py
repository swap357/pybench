"""
Test demonstrating false sharing between threads.
Shows performance impact when threads modify adjacent memory locations.

Purpose:
- Demonstrate baseline false sharing case
- Show cache line contention impact
- Measure thread interference
- Baseline for padding comparison
"""
import time
import sys
import threading
import array

def main():
    iterations = 1_000_000
    num_threads = 4
    threads = []
    
    # Create adjacent counters in same cache line
    counters = array.array('Q', [0] * num_threads)
    
    def worker(index):
        # Each thread updates its own counter
        # But counters are adjacent causing false sharing
        for _ in range(iterations):
            counters[index] += 1
    
    start = time.time()
    
    # Create and start threads
    for i in range(num_threads):
        thread = threading.Thread(target=worker, args=(i,))
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