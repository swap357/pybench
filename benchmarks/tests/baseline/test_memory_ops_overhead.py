"""
Baseline memory operations test.
Establishes baseline metrics for memory operations.

Purpose:
- Measure object creation/destruction overhead
- Test memory allocation patterns
- Exercise garbage collection
- Evaluate object lifecycle costs
"""
import time
import sys

def memory_intensive():
    """Memory operations with object creation"""
    objects = []
    for i in range(10_000):
        obj = [j * j for j in range(100)]
        objects.append(obj)
        if len(objects) > 100:
            objects.pop(0)
    return len(objects)

def main():
    memory_intensive()
    return 0

if __name__ == "__main__":
    sys.exit(main()) 