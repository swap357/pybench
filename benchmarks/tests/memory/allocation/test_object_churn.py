"""
Test object creation and destruction patterns.
Particularly relevant for memory management differences.
"""
import time
import sys

class SmallObject:
    def __init__(self, x, y):
        self.x = x
        self.y = y

def main():
    start = time.time()
    
    # Create and destroy many small objects
    for _ in range(100_000):
        objects = [SmallObject(i, i*2) for i in range(100)]
        # Let objects go out of scope for GC
        
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
