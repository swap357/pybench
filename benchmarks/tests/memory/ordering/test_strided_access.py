"""
Test strided memory access patterns.
Shows impact of cache-unfriendly access patterns.

Purpose:
- Measure strided access overhead
- Show cache miss patterns
- Demonstrate prefetcher limitations
- Compare with sequential access
"""
import time
import sys
import ctypes

def main():
    data_size = 1_000_000
    iterations = 100
    cache_line = 64  # Typical cache line size
    
    # Create aligned array
    aligned = (ctypes.c_long * data_size)()
    
    # Initialize data
    for i in range(data_size):
        aligned[i] = i
    
    # Strided access (cache-unfriendly)
    sum_strided = 0
    stride = cache_line // ctypes.sizeof(ctypes.c_long)
    for _ in range(iterations):
        for i in range(0, data_size, stride):
            sum_strided += aligned[i]
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 