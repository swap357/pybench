"""
Test parallel matrix multiplication.
Demonstrates CPU-intensive parallel computation with minimal GIL impact.
"""
import time
import sys
import threading
import numpy as np
from typing import List, Tuple
import random

def multiply_slice(a: List[List[float]], b: List[List[float]], 
                  start_row: int, end_row: int, result: List[List[float]]):
    """Multiply a slice of matrices."""
    n = len(b[0])
    m = len(b)
    for i in range(start_row, end_row):
        for j in range(n):
            sum_val = 0
            for k in range(m):
                sum_val += a[i][k] * b[k][j]
            result[i][j] = sum_val

def main():
    size = 500  # Matrix size
    
    # Create random matrices
    matrix_a = [[random.random() for _ in range(size)] for _ in range(size)]
    matrix_b = [[random.random() for _ in range(size)] for _ in range(size)]
    result = [[0.0 for _ in range(size)] for _ in range(size)]
    
    start = time.time()
    
    # Split work among threads
    num_threads = 4
    chunk_size = size // num_threads
    threads = []
    
    for i in range(num_threads):
        start_row = i * chunk_size
        end_row = start_row + chunk_size if i < num_threads - 1 else size
        thread = threading.Thread(
            target=multiply_slice,
            args=(matrix_a, matrix_b, start_row, end_row, result)
        )
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
