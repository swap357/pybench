"""
String operations benchmark testing memory allocation and deallocation patterns.
String operations often reveal differences in memory management strategies.
"""
import time
import sys

def main():
    start = time.time()
    
    strings = []
    base = "x" * 100
    
    # String concatenation and manipulation
    for i in range(100_000):
        s = base + str(i)
        s = s.upper()
        s = s.replace('X', 'Y')
        strings.append(s[:50])
        
    # Force some garbage collection
    strings = strings[::2]
    strings.extend(strings)
    strings.sort()
    
    duration = time.time() - start
    print(f"Duration: {duration:.4f}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
