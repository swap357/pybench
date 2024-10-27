"""
Test parallel map implementation for Fibonacci.
Demonstrates parallel processing capability in no-GIL Python.
"""
import time
import sys
import threading
from queue import Queue
from typing import TypeVar, Callable, List, Any
from dataclasses import dataclass

T = TypeVar('T')
R = TypeVar('R')

@dataclass
class WorkItem:
    index: int
    item: Any

class ParallelMap:
    """Thread-safe parallel map implementation."""
    def __init__(self, num_workers: int):
        self.input_queue: Queue = Queue()
        self.output_queue: Queue = Queue()
        self.num_workers = num_workers
    
    def worker(self, func: Callable[[T], R]):
        """Worker thread applying function to queue items."""
        while True:
            work_item = self.input_queue.get()
            if work_item is None:
                self.input_queue.task_done()
                break
            
            result = func(work_item.item)
            self.output_queue.put((work_item.index, result))
            self.input_queue.task_done()
    
    def map(self, func: Callable[[T], R], items: List[T]) -> List[R]:
        """Map function over items in parallel."""
        # Start workers
        threads = []
        for _ in range(self.num_workers):
            t = threading.Thread(target=self.worker, args=(func,))
            t.daemon = True
            t.start()
            threads.append(t)
        
        # Feed items
        for i, item in enumerate(items):
            self.input_queue.put(WorkItem(i, item))
        
        # Send stop signals
        for _ in range(self.num_workers):
            self.input_queue.put(None)
        
        # Wait for completion
        self.input_queue.join()
        
        # Collect and order results
        results = []
        while not self.output_queue.empty():
            results.append(self.output_queue.get())
        
        return [r[1] for r in sorted(results)]

def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def main():
    start = time.time()
    
    # Create larger workload
    numbers = list(range(40))  # Increased workload
    
    # Process in parallel
    parallel_map = ParallelMap(num_workers=4)
    results = parallel_map.map(fibonacci, numbers)
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
