"""
Test recursive implementation of Fibonacci.
Tests function call overhead and stack operations.
"""
import time
import sys

def fibonacci(n: int) -> int:
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def main():
    start = time.time()
    
    # Calculate first 32 Fibonacci numbers
    for n in range(32):
        _ = fibonacci(n)
        
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
