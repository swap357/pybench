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

def main():
    iterations = 100_000
    num_threads = 4
    
    # Test different lock patterns
    patterns = {
        'heavy_contention': threading.Lock(),
        'per_thread': [threading.Lock() for _ in range(num_threads)],
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
    
    # Test 1: Heavy contention
    threads = [
        threading.Thread(target=heavy_contention_worker)
        for _ in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Test 2: Per-thread locks
    threads = [
        threading.Thread(target=per_thread_worker, args=(i,))
        for i in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Test 3: Try-lock pattern
    threads = [
        threading.Thread(target=try_lock_worker)
        for _ in range(num_threads)
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 