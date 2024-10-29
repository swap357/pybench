"""
Test naive parallel processing implementation.
Demonstrates baseline performance with no optimizations.
"""
import time
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import List

def process_chunk(chunk: List[int]) -> List[int]:
    """Process data chunk with heavy object creation and Python operations"""
    processed = []
    for item in chunk:
        processed.append(item * item + 1)
    return processed

def main():
    data_size = 1_000_000
    num_threads = 4
    results = []
    lock = threading.Lock()
    
    # Create data (causing GC pressure)
    data = list(range(data_size))
    chunk_size = data_size // num_threads
    chunks = [
        data[i:i + chunk_size]
        for i in range(0, data_size, chunk_size)
    ]
    
    def worker(chunk: List[int]):
        result = process_chunk(chunk)
        with lock:
            results.extend(result)
    
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        executor.map(worker, chunks)
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 