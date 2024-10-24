"""
Dictionary operations benchmark testing hash tables and lookups.
Tests creation, access, modification, and deletion patterns.
Particularly relevant for Python's dict implementation differences.
"""
import time
import sys
import random
import string

def generate_random_string(length: int) -> str:
    """Generate a random string of fixed length."""
    return ''.join(random.choices(string.ascii_letters, k=length))

def main():
    start = time.time()
    
    # Test 1: Dictionary creation and insertion
    d = {}
    for i in range(1_000_000):
        d[f"key_{i}"] = i
    
    # Test 2: Random key creation and lookup
    random_keys = [generate_random_string(10) for _ in range(100_000)]
    for key in random_keys:
        d[key] = len(key)
    
    for key in random_keys:
        _ = d[key]
    
    # Test 3: Dictionary resizing behavior
    resize_dict = {}
    for i in range(1000):
        # Add items to trigger multiple resizes
        for j in range(100):
            key = f"resize_{i}_{j}"
            resize_dict[key] = j
        # Remove half to test resize-down
        if i % 2 == 0:
            for j in range(50):
                del resize_dict[f"resize_{i}_{j}"]
    
    # Test 4: Dictionary update and merge
    d1 = {str(i): i for i in range(10_000)}
    d2 = {str(i): i*2 for i in range(5_000, 15_000)}
    d1.update(d2)
    
    # Test 5: Dictionary comprehension
    squares = {str(x): x*x for x in range(10_000)}
    
    # Test 6: Key collision handling
    class BadHash:
        def __init__(self, value):
            self.value = value
        def __hash__(self):
            return 1  # Force collisions
        def __eq__(self, other):
            return isinstance(other, BadHash) and self.value == other.value

    collision_dict = {}
    for i in range(1000):  # Create many collisions
        collision_dict[BadHash(i)] = i
    
    # Test 7: Dictionary iteration
    for k, v in d1.items():
        _ = k + str(v)
    
    # Test 8: Dictionary clear and rebuild
    d1.clear()
    for i in range(10_000):
        d1[str(i)] = i * 3
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
