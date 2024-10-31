"""
Test to measure lock acquisition patterns under GIL.
Shows how GIL affects different locking strategies.

Purpose:
- Measure lock acquisition overhead
- Compare different lock patterns
- Evaluate GIL interaction with locks
- Test lock contention scenarios
"""
import time
import sys
import threading
from benchmarks.utils import get_total_threads

def main():
    iterations = 100_000
    total_threads = get_total_threads()
    
    # Test different lock patterns
    patterns = {
        'heavy_contention': threading.Lock(),
        'per_thread': [threading.Lock() for _ in range(total_threads)],
        'try_lock': threading.Lock()
    }
    
    results = {
        'heavy_contention': 0,
        'per_thread': 0,
        'try_lock': 0
    }
    
    def heavy_contention_worker():
        for _ in range(iterations):
            with patterns['heavy_contention']:
                results['heavy_contention'] += 1
    
    def per_thread_worker(thread_id):
        for _ in range(iterations):
            with patterns['per_thread'][thread_id]:
                results['per_thread'] += 1
    
    def try_lock_worker():
        count = 0
        while count < iterations:
            if patterns['try_lock'].acquire(blocking=False):
                try:
                    results['try_lock'] += 1
                    count += 1
                finally:
                    patterns['try_lock'].release()
    
    start = time.time()
    
    # Run all lock pattern tests with proper thread count
    for test_func, args in [
        (heavy_contention_worker, ()),
        (per_thread_worker, range(total_threads)),
        (try_lock_worker, ())
    ]:
        threads = []
        if args:
            for arg in args:
                thread = threading.Thread(target=test_func, args=(arg,))
                threads.append(thread)
        else:
            for _ in range(total_threads):
                thread = threading.Thread(target=test_func)
                threads.append(thread)
                
        for t in threads:
            t.start()
        for t in threads:
            t.join()
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 