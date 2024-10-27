"""
Test to measure impact of memory barriers in multi-threaded code.
Forces memory ordering synchronization between threads.
"""
import time
import sys
import threading
import array
from threading import Event

def main():
    iterations = 1_000_000
    data = array.array('Q', [0] * 8)
    barrier = Event()
    
    start = time.time()
    
    def producer():
        for i in range(iterations):
            # Write data
            data[0] = i
            # Memory barrier (Event.set forces memory ordering)
            barrier.set()
    
    def consumer():
        for _ in range(iterations):
            # Wait for barrier (forces memory ordering)
            barrier.wait()
            # Read data
            _ = data[0]
            barrier.clear()
    
    t1 = threading.Thread(target=producer)
    t2 = threading.Thread(target=consumer)
    
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
