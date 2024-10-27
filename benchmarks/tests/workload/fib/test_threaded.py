"""
Test threaded implementation of Fibonacci.
Tests thread creation and GIL behavior.
"""
import time
import sys
import threading
from queue import Queue

def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def worker(n: int, result_queue: Queue):
    result = fibonacci(n)
    result_queue.put((n, result))

def main():
    start = time.time()
    
    threads = []
    result_queue = Queue()
    
    # Create thread for each Fibonacci number
    for n in range(32):
        thread = threading.Thread(
            target=worker,
            args=(n, result_queue)
        )
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
