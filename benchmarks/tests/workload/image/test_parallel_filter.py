"""
Test parallel image processing.
Demonstrates memory and CPU intensive operations.
"""
import time
import sys
import threading
from typing import List
import array

def apply_filter_chunk(pixels: List[int], start: int, end: int, 
                      kernel: List[float], result: List[int]):
    """Apply convolution filter to image chunk."""
    kernel_size = len(kernel)
    half_size = kernel_size // 2
    width = 1000  # Image width
    
    for i in range(start, end):
        if i < half_size or i >= len(pixels) - half_size:
            continue
        
        sum_val = 0.0
        for k in range(-half_size, half_size + 1):
            sum_val += pixels[i + k] * kernel[k + half_size]
        result[i] = int(sum_val)

def main():
    # Create large 1D image (1000x1000 grayscale)
    width = height = 1000
    image = array.array('I', [i % 256 for i in range(width * height)])
    result = array.array('I', [0] * (width * height))
    
    # Gaussian blur kernel
    kernel = [0.1, 0.2, 0.4, 0.2, 0.1]
    
    start = time.time()
    
    # Process image in parallel chunks
    num_threads = 4
    chunk_size = len(image) // num_threads
    threads = []
    
    for i in range(num_threads):
        start_idx = i * chunk_size
        end_idx = start_idx + chunk_size if i < num_threads - 1 else len(image)
        thread = threading.Thread(
            target=apply_filter_chunk,
            args=(image, start_idx, end_idx, kernel, result)
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
