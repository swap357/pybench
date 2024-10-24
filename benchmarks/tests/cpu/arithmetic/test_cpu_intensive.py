"""
CPU-intensive benchmark testing basic arithmetic operations
"""
import time
import sys

def main():
    # Simple CPU-intensive calculation
    start = time.time()
    result = 0
    for i in range(10_000_000):
        result += i * i
    duration = time.time() - start
    
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
