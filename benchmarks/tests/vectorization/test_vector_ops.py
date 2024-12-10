"""
Test to measure vector operation performance differences between ARMv8 and ARMv9.
Focuses on dot product operations that benefit from:
- ARMv8: NEON 128-bit vectors
- ARMv9: SVE wider vectors and predicated execution
"""
import sys
import array

def main():
    # Test configuration
    size = 1_000_000   # Large enough to show vector differences
    iterations = 100    # Number of dot products to perform
    
    # Create test arrays
    a = array.array('d', [1.0] * size)
    b = array.array('d', [2.0] * size)
    
    # Warmup
    result = 0.0
    for i in range(size):
        result += a[i] * b[i]
    
    # Multiple iterations of dot product to amplify differences
    for _ in range(iterations):
        result = 0.0
        for i in range(size):
            result += a[i] * b[i]
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 