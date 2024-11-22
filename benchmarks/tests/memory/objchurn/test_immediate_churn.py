"""
Test immediate object churn pattern.
Creates and destroys objects in rapid succession.

Purpose:
- Measure object creation/destruction overhead
- Test rapid memory allocation/deallocation
- Evaluate immediate garbage collection patterns
- Benchmark basic list operations
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
    total_threads = get_total_threads()
    threads = []
    
    def worker():
        objects = []
        for i in range(iterations):
            obj = TestObject(i)
            objects.append(obj)
            objects.pop()

    for _ in range(total_threads):
        thread = threading.Thread(target=worker)
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()

    return 0

if __name__ == "__main__":
    sys.exit(main())