"""
Test parallel processing using multiprocessing.
Demonstrates same workload using process-based parallelism.
"""
import time
import sys
import multiprocessing as mp
import array
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
    
    # Create and start processes
    with mp.Pool(processes=num_processes) as pool:
        pool.starmap(process_chunk, chunks)
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 