"""
Test to measure GIL contention patterns in different Python versions.
Particularly relevant for 3.13.0t (no-GIL) comparison.
"""
import time
import sys
import threading

def cpu_work():
    x = 0
    for i in range(1_000_000):
        x += i * i
    return x

def main():
    start = time.time()
    
    # Create multiple threads doing CPU work
    threads = []
    for _ in range(4):  # Use 4 threads
        t = threading.Thread(target=cpu_work)
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
        
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
