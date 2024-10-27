"""
Test parallel hash computation.
Demonstrates CPU-intensive work with minimal thread synchronization.
"""
import time
import sys
import threading
import hashlib
from queue import Queue
import random
import string

def generate_data(size: int) -> bytes:
    """Generate random data for hashing."""
    return ''.join(random.choices(string.ascii_letters, k=size)).encode()

def hash_worker(queue: Queue, chunk_size: int, iterations: int):
    """Compute hashes of random data."""
    for _ in range(iterations):
        data = generate_data(chunk_size)
        # Compute multiple hash algorithms
        sha256 = hashlib.sha256(data).digest()
        sha512 = hashlib.sha512(data).digest()
        blake2 = hashlib.blake2b(data).digest()
        queue.put((sha256, sha512, blake2))

def main():
    chunk_size = 10000
    iterations = 1000
    num_threads = 4
    result_queue = Queue()
    
    start = time.time()
    
    threads = []
    for _ in range(num_threads):
        thread = threading.Thread(
            target=hash_worker,
            args=(result_queue, chunk_size, iterations)
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
