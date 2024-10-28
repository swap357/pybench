"""
Test ThreadPool apply() performance.
Tests task scheduling and execution using pool.apply().
"""
import time
import sys
import math
from multiprocessing.pool import ThreadPool

def cpu_task(n):
    """CPU-bound computation"""
    result = 0
    for i in range(n):
        result += math.sin(i) * math.cos(i)
    return result

def main():
    num_threads = 4
    iterations = 10000
    tasks = [iterations] * 100  # 100 tasks of equal size
    
    start = time.time()
    with ThreadPool(num_threads) as pool:
        results = [pool.apply(cpu_task, (task,)) for task in tasks]
        
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 