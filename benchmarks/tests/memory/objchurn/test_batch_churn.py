"""
Test batch object churn pattern.
Creates and destroys objects in batches.

Purpose:
- Measure batch allocation/deallocation overhead
- Test memory usage patterns with batches
- Evaluate bulk cleanup efficiency
- Compare against immediate churn pattern
"""
import sys
import threading
from benchmarks.utils import get_total_threads

class TestObject:
    def __init__(self, value):
        self.value = value
        self.data = [i for i in range(100)]

def main():
    iterations = 100_000
    batch_size = 100
    total_threads = get_total_threads()
    threads = []
    
    def worker():
        for _ in range(iterations // batch_size):
            objects = []
            
            for i in range(batch_size):
                obj = TestObject(i)
                objects.append(obj)
            
            objects.clear()
    

    for _ in range(total_threads):
        thread = threading.Thread(target=worker)
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())