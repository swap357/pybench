"""
Test iterative implementation of Fibonacci.
Tests basic loop and variable operations.
"""
import time
import sys

def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

def main():
    start = time.time()
    
    # Calculate first 42 Fibonacci numbers
    for n in range(42):
        _ = fibonacci(n)
        
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())