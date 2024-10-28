"""
Test ThreadPoolExecutor submit() performance.
Tests task scheduling and execution using executor.submit().
"""
import time
import sys
import math
from concurrent.futures import ThreadPoolExecutor

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
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(cpu_task, task) for task in tasks]
        results = [f.result() for f in futures]
        
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 