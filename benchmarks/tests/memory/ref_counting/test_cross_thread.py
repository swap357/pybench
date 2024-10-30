"""
Test to measure performance of cross-thread object sharing.
Lower performance expected due to reference counting overhead.

Purpose:
- Measure cross-thread ref counting overhead
- Test reference counting contention
- Evaluate shared object lifecycle
- Compare with thread-local performance
"""
import time
import sys
import threading
from queue import Queue

def main():
    iterations = 100_000
    shared_queue = Queue(maxsize=1000)  # Bounded queue to prevent memory explosion
    done = threading.Event()
    
    start = time.time()
    
    def producer():
        try:
            for _ in range(iterations):
                obj = [i for i in range(100)]  # Create substantial object
                shared_queue.put(obj)
        finally:
            done.set()  # Signal completion
    
    def consumer():
        count = 0
        while count < iterations:
            try:
                obj = shared_queue.get(timeout=10.0)  # Timeout to prevent deadlock
                count += 1
                shared_queue.task_done()
            except Queue.Empty:
                if done.is_set() and shared_queue.empty():
                    break
    
    # Create and start threads
    producer_thread = threading.Thread(target=producer)
    consumer_thread = threading.Thread(target=consumer)
    
    producer_thread.start()
    consumer_thread.start()
    
    # Wait for completion
    producer_thread.join()
    consumer_thread.join()
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())