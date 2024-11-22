"""
Test thread-local object reference counting and memory churn.
Measures interpreter's handling of thread-local object lifecycle.

Purpose:
- Measure thread-local memory churn overhead
- Test object creation/destruction patterns
- Compare interpreter memory management efficiency
"""
import time
import sys
import threading
import gc
from benchmarks.utils import get_total_threads
import dis
class TestObject:
    """Test object with realistic memory overhead"""
    __slots__ = ['value', 'data']
    def __init__(self, value):
        self.value = value
        # Fixed-size list to maintain similar memory footprint
        self.data = list(range(100))

def main():
    iterations = 100_000
    total_threads = get_total_threads()
    threads = []
    def worker():
        # Pre-create single object to test ref counting
        obj = TestObject(42)
        
        # Disable GC for cleaner measurements
        gc.disable()
        
        # Single reference slot
        ref = None
        
        # Pure ref counting loop
        for _ in range(iterations):
            ref = obj       # INCREF
            ref = None     # DECREF
        
        gc.enable()

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