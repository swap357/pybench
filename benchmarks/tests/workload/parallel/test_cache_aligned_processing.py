"""
Test parallel processing with cache-aligned arrays.
Demonstrates memory access pattern optimization.
"""
import time
import sys
import ctypes
from concurrent.futures import ThreadPoolExecutor

def main():
    data_size = 1_000_000
    num_threads = 4
    
    # Cache line size alignment
    cache_line = 64
    padding = cache_line // ctypes.sizeof(ctypes.c_long)
    padded_size = data_size + num_threads * padding
    
    # Aligned arrays
    data = (ctypes.c_long * padded_size)()
    results = (ctypes.c_long * padded_size)()
    
    # Initialize data
    for i in range(data_size):
        data[i] = i
    
    def process_chunk(start: int, end: int, thread_id: int):
        """Process data in cache-friendly chunks"""
        chunk_size = 16  # Process 16 elements at a time
        thread_offset = thread_id * padding
        
        for base in range(start, end, chunk_size):
            chunk_end = min(base + chunk_size, end)
            for i in range(base, chunk_end):
                results[i + thread_offset] = data[i] * data[i] + 1
    
    start = time.time()
    chunk_size = data_size // num_threads
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(process_chunk, 
                          i * chunk_size,
                          min((i + 1) * chunk_size, data_size),
                          i)
            for i in range(num_threads)
        ]
        for f in futures:
            f.result()
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 