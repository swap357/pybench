"""
Test parallel processing using ProcessPoolExecutor.
Demonstrates same workload using concurrent.futures with processes.
"""
import time
import sys
import array
from concurrent.futures import ProcessPoolExecutor
import multiprocessing as mp
from typing import List

def process_chunk(chunk_data: List[int], start_idx: int, 
                 shared_results: mp.Array) -> None:
    """Process data chunk and store in shared array"""
    for i, item in enumerate(chunk_data):
        shared_results[start_idx + i] = item * item + 1

def main():
    data_size = 1_000_000
    num_processes = mp.cpu_count()
    
    # Create data
    data = list(range(data_size))
    chunk_size = data_size // num_processes
    
    # Create shared result array
    shared_results = mp.Array('i', data_size)
    
    # Split data into chunks
    chunks = []
    for i in range(0, data_size, chunk_size):
        end = min(i + chunk_size, data_size)
        chunks.append((
            data[i:end],  # chunk data
            i,            # start index in result array
            shared_results # shared result array
        ))
    
    start = time.time()
    
    # Use ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=num_processes) as executor:
        list(executor.map(lambda x: process_chunk(*x), chunks))
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 