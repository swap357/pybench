"""
Test impact of memory alignment on access patterns.
Shows performance difference between aligned and unaligned access.

Purpose:
- Compare aligned vs unaligned access
- Measure alignment impact
- Show memory boundary effects
- Demonstrate hardware alignment handling
"""
import time
import sys
import array

def main():
    data_size = 1_000_000
    iterations = 100
    
    # Create unaligned array
    unaligned = array.array('l', [0] * data_size)
    
    # Initialize data
    for i in range(data_size):
        unaligned[i] = i
    
    start = time.time()
    
    # Unaligned access
    sum_unaligned = 0
    for _ in range(iterations):
        for i in range(0, data_size):
            sum_unaligned += unaligned[i]
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 