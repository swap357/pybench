"""
Baseline thread creation test.
Measures basic threading overhead.

Purpose:
- Measure thread creation cost
- Evaluate thread lifecycle overhead
- Test basic thread management
- No synchronization or shared data
"""
import time
import sys
import threading

def no_op_worker():
    """Thread worker that does minimal work"""
    time.sleep(0.001)  # Tiny sleep to ensure thread actually runs

def main():
    num_threads = 1000  # Create enough threads to measure overhead
    threads = []
    start = time.time()
    
    # Create and start threads
    for _ in range(num_threads):
        thread = threading.Thread(target=no_op_worker)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 