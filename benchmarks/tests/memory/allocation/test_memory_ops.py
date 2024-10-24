"""
Memory operations benchmark testing object creation and destruction
"""
import time
import sys

def main():
    start = time.time()
    
    # Create and destroy lots of objects
    for _ in range(1_000_000):
        x = [i for i in range(100)]
        del x
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
