"""
Test cross-thread object reference counting.
Shows overhead of reference counting for shared objects.

Purpose:
- Measure cross-thread ref counting overhead
- Test reference counting contention
- Evaluate shared object lifecycle
- Compare with thread-local performance
"""
import time
import sys
import threading
import queue

class TestObject:
    """Test object that will be shared between threads"""
    def __init__(self, value):
        self.value = value
        self.data = [i for i in range(100)]  # Some data to make object substantial

def main():
    iterations = 1_000_000
    num_threads = 4
    threads = []
    shared_queue = queue.Queue()
    start = time.time()
    
    def producer():
        # Create objects and share them
        for i in range(iterations):
            obj = TestObject(i)
            shared_queue.put(obj)
    
    def consumer():
        # Process shared objects
        received = 0
        while received < iterations:
            obj = shared_queue.get()
            # Force some ref count operations
            local_ref = obj
            received += 1
            if received % 100 == 0:
                shared_queue.task_done()
    
    # Start producer
    producer_thread = threading.Thread(target=producer)
    producer_thread.start()
    
    # Start consumers
    for _ in range(num_threads - 1):  # -1 because we have one producer
        thread = threading.Thread(target=consumer)
        threads.append(thread)
        thread.start()
    
    # Wait for completion
    producer_thread.join()
    for thread in threads:
        thread.join()
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 