"""
Test sequential memory access patterns.
Shows performance of cache-friendly sequential access.

Purpose:
- Measure sequential access performance
- Demonstrate cache line utilization
- Show prefetcher effectiveness
- Baseline for memory access patterns
"""
import time
import sys
import ctypes

def main():
    data_size = 1_000_000
    iterations = 100
    
    # Create aligned array
    aligned = (ctypes.c_long * data_size)()
    
    # Initialize data
    for i in range(data_size):
        aligned[i] = i
    
    # Sequential access (cache-friendly)
    sum_aligned = 0
    for _ in range(iterations):
        for i in range(0, data_size):
            sum_aligned += aligned[i]
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 