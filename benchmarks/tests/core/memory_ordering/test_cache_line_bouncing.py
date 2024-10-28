"""
Test to measure impact of cache line bouncing between CPU cores.
Tests frequent modifications to shared data from different threads.
"""
import time
import sys
import threading
import array

def main():
    iterations = 1_000_000
    shared_data = array.array('Q', [0] * 8)  # 64 bytes (typical cache line)
    
    start = time.time()
    
    def worker(index):
        # Each thread updates its own element but reads neighbor's
        next_index = (index + 1) % 8
        local = 0
        for _ in range(iterations):
            shared_data[index] += 1
            local += shared_data[next_index]  # Force cache line transfer
    
    threads = [
        threading.Thread(target=worker, args=(i,))
        for i in range(8)
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
