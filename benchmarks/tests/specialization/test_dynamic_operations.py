"""
Test to measure performance of dynamic operations.
Lower performance expected due to disabled specialization.
"""
import sys
from typing import Any

def main():
    iterations = 10_000_000
    
    
    def dynamic_add(x: Any, y: Any) -> Any:
        return x + y
    
    result = 0
    for i in range(iterations):
        result = dynamic_add(i, result)

    return 0

if __name__ == "__main__":
    sys.exit(main())
