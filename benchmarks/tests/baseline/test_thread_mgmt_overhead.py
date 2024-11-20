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
    time.sleep(0.001)

def main():
    num_threads = 1000 
    threads = []
    
    for _ in range(num_threads):
        thread = threading.Thread(target=no_op_worker)
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 