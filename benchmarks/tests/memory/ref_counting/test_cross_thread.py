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
import os
from benchmarks.utils import get_total_threads

def main():
    iterations = 100_000
    # Get total threads based on cores and thread limit
    total_threads = get_total_threads()
    
    # Scale queue size with total thread count
    queue_size = max(100, total_threads * 10)
    shared_queue = Queue(maxsize=queue_size)
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
    
    # Create and start threads based on total available threads
    producer_threads = []
    consumer_threads = []
    
    # Split threads between producers and consumers
    num_pairs = total_threads // 2  # Each pair has 1 producer and 1 consumer
    
    for _ in range(num_pairs):
        producer_thread = threading.Thread(target=producer)
        consumer_thread = threading.Thread(target=consumer)
        
        producer_threads.append(producer_thread)
        consumer_threads.append(consumer_thread)
        
        producer_thread.start()
        consumer_thread.start()
    
    # Wait for completion
    for t in producer_threads:
        t.join()
    for t in consumer_threads:
        t.join()
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())