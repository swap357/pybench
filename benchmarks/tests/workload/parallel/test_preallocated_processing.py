"""
Test parallel processing with pre-allocated arrays.
Demonstrates reduced object allocation optimization.
"""
import time
import sys
import array
from concurrent.futures import ThreadPoolExecutor

def main():
    data_size = 1_000_000
    num_threads = 4
    
    # Pre-allocate arrays
    results = array.array('i', [0] * data_size)
    data = array.array('i', range(data_size))
    chunk_size = data_size // num_threads
    
    def process_chunk(start: int, end: int):
        """Process data chunk using array slices"""
        for i in range(start, end):
            results[i] = data[i] * data[i] + 1
    
    start = time.time()
    
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(process_chunk, i * chunk_size, 
                          min((i + 1) * chunk_size, data_size))
            for i in range(num_threads)
        ]
        for f in futures:
            f.result()
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 