"""
Test to measure performance of thread-local object operations.
Higher performance expected due to biased reference counting.
"""
import time
import sys

def main():
    iterations = 1_000_000
    objects = []
    
    start = time.time()
    # Create and manipulate objects in single thread
    for _ in range(iterations):
        obj = [i for i in range(100)]  # Create local object
        objects.append(obj)
        if len(objects) > 100:
            objects.pop(0)  # Keep memory usage constant
            
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
