"""
Mixed I/O and CPU benchmark testing file operations with processing.
Tests both I/O performance and data processing overhead.
"""
import time
import sys
import tempfile
import os

def process_chunk(chunk):
    """CPU-intensive processing of data."""
    result = 0
    for line in chunk:
        numbers = [int(x) for x in line.split()]
        result += sum(x * x for x in numbers)
    return result

def main():
    start = time.time()
    
    # Create temporary file with test data
    with tempfile.NamedTemporaryFile(mode='w+', delete=False) as f:
        # Generate 1M lines of test data
        for i in range(1_000_000):
            f.write(f"{i} {i+1} {i+2}\n")
        f.flush()
        
        # Read and process in chunks
        f.seek(0)
        chunk_size = 10000
        chunk = []
        total = 0
        
        for line in f:
            chunk.append(line)
            if len(chunk) >= chunk_size:
                total += process_chunk(chunk)
                chunk = []
        
        if chunk:
            total += process_chunk(chunk)
    
    # Cleanup
    os.unlink(f.name)
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
