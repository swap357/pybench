"""
Test to measure lock acquisition patterns and contention scenarios.
Tests improvements in Python 3.13's Lock implementation.
"""
import time
import sys
import threading
import queue

def main():
    iterations = 10_000
    num_threads = 4
    results = queue.Queue()
    
    # Test 1: High Contention Lock
    start = time.time()
    
    shared_lock = threading.Lock()
    shared_counter = 0
    
    def high_contention_worker():
        nonlocal shared_counter
        local_count = 0
        
        for _ in range(iterations):
            with shared_lock:
                # Simulate some work under lock
                shared_counter += 1
                local_count += 1
                
        results.put(local_count)
    
    # Launch high contention threads
    threads = [
        threading.Thread(target=high_contention_worker)
        for _ in range(num_threads)
    ]
    
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    
    # Verify results
    total_count = 0
    while not results.empty():
        total_count += results.get()
    
    if total_count != iterations * num_threads:
        print(f"Error: Expected {iterations * num_threads}, got {total_count}")
        return 1
        
    # Test 2: Timeout Behavior
    timeout_lock = threading.Lock()
    timeout_results = []
    
    def timeout_worker():
        success_count = 0
        timeout_count = 0
        
        for _ in range(100):  # Fewer iterations for timeout test
            try:
                if timeout_lock.acquire(timeout=0.001):  # 1ms timeout
                    success_count += 1
                    # Simulate work
                    time.sleep(0.002)  # 2ms work
                    timeout_lock.release()
                else:
                    timeout_count += 1
            except RuntimeError:
                print("Unexpected lock state error")
                return
                
        timeout_results.append((success_count, timeout_count))
    
    # Launch timeout test threads
    timeout_threads = [
        threading.Thread(target=timeout_worker)
        for _ in range(num_threads)
    ]
    
    for t in timeout_threads:
        t.start()
    for t in timeout_threads:
        t.join()
    
    # Test 3: Lock/Unlock Pattern
    pattern_lock = threading.Lock()
    pattern_success = threading.Event()
    
    def lock_pattern_worker():
        try:
            # Test basic acquire/release
            assert pattern_lock.acquire()
            pattern_lock.release()
            
            # Test timeout
            assert pattern_lock.acquire(timeout=1.0)
            pattern_lock.release()
            
            # Test non-blocking
            assert pattern_lock.acquire(blocking=False)
            pattern_lock.release()
            
            # Test context manager
            with pattern_lock:
                pass
                
            pattern_success.set()
            
        except Exception as e:
            print(f"Lock pattern error: {e}")
            return
    
    pattern_thread = threading.Thread(target=lock_pattern_worker)
    pattern_thread.start()
    pattern_thread.join()
    
    if not pattern_success.is_set():
        print("Lock pattern test failed")
        return 1
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
