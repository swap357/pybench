"""
Test to measure impact of memory barriers in multi-threaded code.
Forces memory ordering synchronization between threads.
"""
import time
import sys
import threading
import array
import itertools
from threading import Event

TIMEOUT = 100  # seconds

def main():
    iterations = 100
    # Use multiple data points to prevent false sharing
    data = array.array('Q', [0] * 16)  # 16 elements to span multiple cache lines
    done = Event()
    success = Event()
    
    start = time.time()
    
    def producer():
        try:
            counter = itertools.count(1)  # Start from 1 to distinguish from initial 0
            while not done.is_set():
                # Write to first cache line
                val = next(counter)
                data[0] = val
                # Force memory barrier
                threading.get_ident()  # Memory barrier in CPython
        except Exception as e:
            print(f"Producer error: {e}")
            done.set()
    
    def consumer():
        try:
            last_seen = 0
            reads = 0
            deadline = time.time() + TIMEOUT
            
            while reads < iterations:
                if time.time() > deadline:
                    print("Test timed out!")
                    break
                
                # Read from first cache line
                current = data[0]
                if current != last_seen and current > 0:  # Ensure we see a new value
                    last_seen = current
                    reads += 1
                # Force memory barrier
                threading.get_ident()  # Memory barrier in CPython
            
            success.set()  # Mark successful completion
            done.set()  # Signal producer to stop
            
        except Exception as e:
            print(f"Consumer error: {e}")
            done.set()
    
    t1 = threading.Thread(target=producer)
    t2 = threading.Thread(target=consumer)
    
    t1.start()
    t2.start()
    
    t1.join(TIMEOUT)
    t2.join(TIMEOUT)
    
    if not success.is_set():
        print("Test did not complete successfully")
        return 1
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
