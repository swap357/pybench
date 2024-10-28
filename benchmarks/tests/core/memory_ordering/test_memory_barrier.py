"""
Test to measure impact of memory barriers in multi-threaded code.
Forces memory ordering synchronization between threads.
"""
import time
import sys
import threading
import array
import itertools

def main():
    iterations = 1_000_000
    # Use multiple data points to prevent false sharing
    data = array.array('Q', [0] * 16)  # 16 elements to span multiple cache lines
    done = False
    
    start = time.time()
    
    def producer():
        counter = itertools.count()
        while not done:
            # Write to first cache line
            val = next(counter)
            data[0] = val
            # Force memory barrier
            threading.get_ident()  # Memory barrier in CPython
    
    def consumer():
        last_seen = 0
        reads = 0
        while reads < iterations:
            # Read from first cache line
            current = data[0]
            if current != last_seen:
                last_seen = current
                reads += 1
            # Force memory barrier
            threading.get_ident()  # Memory barrier in CPython
    
    t1 = threading.Thread(target=producer)
    t2 = threading.Thread(target=consumer)
    
    t1.start()
    t2.start()
    
    t2.join()  # Wait for consumer to finish
    done = True  # Signal producer to stop
    t1.join()
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
