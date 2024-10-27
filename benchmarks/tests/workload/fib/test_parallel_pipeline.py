"""
Test pipelined parallel computation of Fibonacci.
Shows benefits of no-GIL in producer-consumer pattern.
"""
import time
import sys
import threading
from queue import Queue
from typing import List, Optional

def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

class Pipeline:
    def __init__(self, num_workers: int):
        self.input_queue = Queue(maxsize=100)
        self.output_queue = Queue()
        self.workers: List[threading.Thread] = []
        self.num_workers = num_workers
        
    def worker(self):
        """Worker thread computing Fibonacci numbers."""
        while True:
            n = self.input_queue.get()
            if n is None:
                self.input_queue.task_done()
                break
                
            result = fibonacci(n)
            self.output_queue.put((n, result))
            self.input_queue.task_done()
    
    def start(self):
        """Start worker threads."""
        for _ in range(self.num_workers):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()
            self.workers.append(t)
    
    def process(self, numbers: List[int]):
        """Process numbers through pipeline."""
        # Feed numbers to workers
        for n in numbers:
            self.input_queue.put(n)
            
        # Send stop signals
        for _ in range(self.num_workers):
            self.input_queue.put(None)
            
        # Wait for completion
        self.input_queue.join()
        
        # Collect results
        results = []
        while not self.output_queue.empty():
            results.append(self.output_queue.get())
        
        return results

def main():
    start = time.time()
    
    # Create larger workload
    numbers = list(range(40))  # Increased workload
    
    # Create and run pipeline
    pipeline = Pipeline(num_workers=4)
    pipeline.start()
    results = pipeline.process(numbers)
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
