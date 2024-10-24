"""
Mixed workload testing both memory and CPU operations.
Tests dictionary operations with computation.
"""
import time
import sys

def main():
    start = time.time()
    
    # Dictionary operations mixed with computation
    d = {}
    for i in range(1_000_000):
        # Memory: dict operations
        d[f"key_{i}"] = i
        
        # CPU: computation
        x = sum(j * j for j in range(i % 100))
        d[f"key_{i}"] = x
        
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
