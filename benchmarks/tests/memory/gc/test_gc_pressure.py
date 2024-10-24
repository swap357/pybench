"""
Test garbage collector behavior under pressure.
Important for understanding GC differences between versions.
"""
import time
import sys
import gc

class CircularRef:
    def __init__(self):
        self.next = None

def main():
    start = time.time()
    
    # Create circular references to stress GC
    for _ in range(100):
        objects = [CircularRef() for _ in range(10_000)]
        for i in range(len(objects)-1):
            objects[i].next = objects[i+1]
        objects[-1].next = objects[0]
        
        # Force collection
        gc.collect()
        
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
