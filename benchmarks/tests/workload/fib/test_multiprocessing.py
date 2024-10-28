"""
Test multiprocessing implementation of Fibonacci.
Tests process creation and inter-process communication.
"""
import time
import sys
from multiprocessing import Pool

def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def main():
    start = time.time()
    
    # Use process pool with CPU count workers
    with Pool() as pool:
        # Map fibonacci to all numbers
        results = pool.map(fibonacci, range(42))
        
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
