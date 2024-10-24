"""
CPU-intensive recursive benchmark testing function call overhead and stack operations.
Based on discussion showing significant differences in free-threading build.
"""
import time
import sys

def fibonacci(n: int) -> int:
    if n < 3:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

def main():
    start = time.time()
    # Calculate 30th fibonacci number 16 times
    for _ in range(16):
        result = fibonacci(30)
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
