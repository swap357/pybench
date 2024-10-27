"""
Test to measure performance of type-specialized operations.
Better performance expected with type hints enabling specialization.
"""
import time
import sys

def main():
    iterations = 10_000_000
    
    start = time.time()
    def specialized_add(x: int, y: int) -> int:
        return x + y
    
    result = 0
    for i in range(iterations):
        result = specialized_add(i, result)
        
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
