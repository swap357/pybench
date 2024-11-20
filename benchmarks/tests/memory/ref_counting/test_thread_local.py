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
from benchmarks.utils import get_total_threads

class TestObject:
    """Test object with no special handling"""
    def __init__(self, value):
        self.value = value
        # List overhead: 56 bytes (empty list)
        # Integer array: 100 integers × 8 bytes = 800 bytes
        # Total object size: ~872 bytes (56 + 800 + object overhead + value attr)
        self.data = [i for i in range(100)]

def main():
    iterations = 100_000
    total_threads = get_total_threads()
    threads = []
    
    def worker():
        objects_pool = [TestObject(i) for i in range(100)]
        local_refs = [None] * 100
        
        num_passes = iterations // len(objects_pool)

        for _ in range(num_passes):
            for i in range(len(objects_pool)):
                local_refs[i] = objects_pool[i]  # INCREF
                local_refs[i] = None             # DECREF

    # Create and start threads
    for _ in range(total_threads):
        thread = threading.Thread(target=worker)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 