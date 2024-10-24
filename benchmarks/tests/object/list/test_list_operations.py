"""
List operation benchmarks testing common list manipulations.
Tests sorting, slicing, and element access patterns.
"""
import time
import sys
import random

def main():
    start = time.time()
    
    # Create large list
    data = list(range(1_000_000))
    random.shuffle(data)
    
    # Test various operations
    for _ in range(5):
        # Sorting
        sorted_data = sorted(data)
        
        # Slicing
        slices = [
            data[i:i+1000] 
            for i in range(0, len(data), 1000)
        ]
        
        # Reversing
        reversed_data = data[::-1]
        
        # List comprehension
        squares = [x*x for x in data[:10000]]
        
        # Extend and clear
        temp = []
        temp.extend(squares)
        temp.clear()
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
