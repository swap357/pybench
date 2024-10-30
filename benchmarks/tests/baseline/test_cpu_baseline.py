"""
Baseline CPU performance test.
Establishes baseline metrics for pure computation.

Purpose:
- Measure pure computational overhead
- No memory allocation
- No object creation
- Arithmetic and math operations only
"""
import time
import sys
import math

def compute_intensive():
    """Pure computation without object creation"""
    result = 0
    for i in range(1_000_000):
        result += math.sin(i) * math.cos(i)
    return result

def main():
    start = time.time()
    result = compute_intensive()
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 