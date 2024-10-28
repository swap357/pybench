"""
Test to measure performance impact of false sharing using adjacent counters.
Lower performance expected due to cache line bouncing.
"""
import time
import sys
import threading
import array

def main():
    iterations = 1_000_000
    counters = array.array('Q', [0] * 4)
    
    start = time.time()
    
    def worker(index):
        for _ in range(iterations):
            counters[index] += 1
    
    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(4)
    ]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
