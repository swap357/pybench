"""
Test chunked parallel computation of Fibonacci numbers.
Demonstrates true parallel execution in no-GIL Python.
"""
import time
import sys
import threading
from queue import Queue
from typing import List, Tuple

def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def worker(numbers: List[int], results: Queue):
    """Process a chunk of numbers in parallel."""
    for n in numbers:
        result = fibonacci(n)
        results.put((n, result))

def chunk_list(lst: List[int], chunk_size: int) -> List[List[int]]:
    """Split list into chunks for parallel processing."""
    return [
        lst[i:i + chunk_size] 
        for i in range(0, len(lst), chunk_size)
    ]

def main():
    start = time.time()
    
    # Generate larger workload
    numbers = list(range(47))  # Increased workload
    num_threads = 4
    chunk_size = len(numbers) // num_threads
    chunks = chunk_list(numbers, chunk_size)
    
    # Create result queue and threads
    results: Queue = Queue()
    threads = []
    
    # Start worker threads
    for chunk in chunks:
        thread = threading.Thread(
            target=worker,
            args=(chunk, results)
        )
        threads.append(thread)
        thread.start()
    
    # Wait for completion
    for thread in threads:
        thread.join()
        
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
