"""
Test object pool churn patterns in thread-local context.
Measures performance of managing multiple objects with fixed-size pools.

Purpose:
- Evaluate object pool management overhead
- Test memory churn with multiple objects
- Measure thread-local pool access patterns
- Compare pool-based vs single-object patterns
"""
import sys
import threading
from benchmarks.utils import get_total_threads

class TestObject:
    """Test object with substantial memory footprint"""
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
        # Create fixed-size object pool
        objects_pool = [TestObject(i) for i in range(100)]
        local_refs = [None] * 100
        
        # Calculate passes to maintain total iteration count
        num_passes = iterations // len(objects_pool)
        
        # Pool churn loop - cycle through all objects
        for _ in range(num_passes):
            for i in range(len(objects_pool)):
                local_refs[i] = objects_pool[i]
                local_refs[i] = None
    
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