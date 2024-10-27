"""
Test ThreadPoolExecutor implementation of Fibonacci.
Tests thread pool overhead and reuse.
"""
import time
import sys
from concurrent.futures import ThreadPoolExecutor

def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def main():
    start = time.time()
    
    # Use ThreadPoolExecutor with max_workers=4
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Submit all numbers and gather results
        futures = [
            executor.submit(fibonacci, n)
            for n in range(32)
        ]
        
        # Wait for all results
        results = [f.result() for f in futures]
        
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
