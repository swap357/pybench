"""
Test thread-local object reference counting.
Shows performance of reference counting for thread-local objects.

Purpose:
- Measure thread-local ref counting overhead
- Test biased reference counting benefits
- Evaluate object lifecycle in single thread
- Baseline for cross-thread comparison
"""
import time
import sys
import threading

class TestObject:
    """Test object with no special handling"""
    def __init__(self, value):
        self.value = value
        self.data = [i for i in range(100)]  # Some data to make object substantial

def main():
    iterations = 100_000
    num_threads = 4
    threads = []
    start = time.time()
    
    def worker():
        # Create and manipulate objects in thread-local context
        local_objects = []
        for i in range(iterations):
            obj = TestObject(i)
            local_objects.append(obj)
            if len(local_objects) > 100:
                local_objects.pop(0)  # Force deallocation
    
    # Create and start threads
    for _ in range(num_threads):
        thread = threading.Thread(target=worker)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 