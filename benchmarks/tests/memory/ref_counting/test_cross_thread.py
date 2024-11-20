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
from benchmarks.utils import get_total_threads

def main():
    iterations = 100_000
    total_threads = get_total_threads()
    
    # Scale queue size with total thread count but cap it
    queue_size = min(1000, max(100, total_threads * 10))
    shared_queue = Queue(maxsize=queue_size)
    
    # Use multiple events for better synchronization
    producer_done = threading.Event()
    consumer_done = threading.Event()
    stop_signal = threading.Event()
    
    def producer():
        produced = 0
        try:
            while produced < iterations and not stop_signal.is_set():
                try:
                    obj = [i for i in range(100)]  # Create substantial object
                    shared_queue.put(obj, timeout=1.0)  # Add timeout to prevent deadlock
                    produced += 1
                except Queue.Full:
                    if stop_signal.is_set():
                        break
                    continue
        finally:
            producer_done.set()
    
    def consumer():
        consumed = 0
        while consumed < iterations:
            try:
                obj = shared_queue.get(timeout=1.0)  # Shorter timeout
                consumed += 1
                shared_queue.task_done()
            except Queue.Empty:
                # Check if we should exit
                if producer_done.is_set() and shared_queue.empty():
                    break
                if stop_signal.is_set():
                    break
                continue
        consumer_done.set()
    
    # Create and start threads
    producer_threads = []
    consumer_threads = []
    num_pairs = total_threads // 2
    
    try:
        # Start threads with error handling
        for _ in range(num_pairs):
            producer_thread = threading.Thread(target=producer)
            consumer_thread = threading.Thread(target=consumer)
            
            producer_threads.append(producer_thread)
            consumer_threads.append(consumer_thread)
            
            producer_thread.start()
            consumer_thread.start()
        
        # Monitor progress and handle deadlocks
        timeout = 60  # Maximum runtime in seconds
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if producer_done.is_set() and consumer_done.is_set():
                break
            time.sleep(0.1)
        else:
            # Timeout reached, signal threads to stop
            stop_signal.set()
            
        # Wait for threads with timeout
        for t in producer_threads + consumer_threads:
            t.join(timeout=1.0)
            
    except Exception as e:
        print(f"Error during benchmark: {e}", file=sys.stderr)
        stop_signal.set()  # Signal all threads to stop
        raise
    
    return 0

if __name__ == "__main__":
    sys.exit(main())