"""
Test to measure performance with padded counters to avoid false sharing.
Better performance expected due to eliminated cache line bouncing.
"""
import time
import sys
import threading
import array

def main():
    iterations = 10_000_000
    
    class PaddedCounter:
        def __init__(self):
            self.value = 0
            self._pad = array.array('Q', [0] * 7)  # 56 bytes padding
    
    counters = [PaddedCounter() for _ in range(4)]
    
    start = time.time()
    
    def worker(counter):
        for _ in range(iterations):
            counter.value += 1
    
    threads = [
        threading.Thread(target=worker, args=(counters[i],))
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
