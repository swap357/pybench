"""
Test to measure performance of cross-thread object sharing.
Lower performance expected due to reference counting overhead.
"""
import time
import sys
import threading
from queue import Queue

def main():
    iterations = 1_000_000
    shared_queue = Queue()
    done = threading.Event()
    
    start = time.time()
    
    def producer():
        for _ in range(iterations):
            obj = [i for i in range(100)]
            shared_queue.put(obj)
    
    def consumer():
        count = 0
        while count < iterations:
            obj = shared_queue.get()
            count += 1
    
    t1 = threading.Thread(target=producer)
    t2 = threading.Thread(target=consumer)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
