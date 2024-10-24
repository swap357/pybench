"""
CPU-intensive benchmark testing matrix multiplication.
Particularly relevant for arithmetic optimization differences.
"""
import time
import sys
import random

def create_matrix(n):
    return [[random.random() for _ in range(n)] for _ in range(n)]

def matrix_multiply(A, B):
    n = len(A)
    result = [[0] * n for _ in range(n)]
    
    for i in range(n):
        for j in range(n):
            for k in range(n):
                result[i][j] += A[i][k] * B[k][j]
    
    return result

def main():
    start = time.time()
    
    # Create and multiply 200x200 matrices
    size = 200
    iterations = 3
    
    for _ in range(iterations):
        A = create_matrix(size)
        B = create_matrix(size)
        C = matrix_multiply(A, B)
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
