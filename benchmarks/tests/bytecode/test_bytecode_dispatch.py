"""
Test bytecode dispatch overhead differences between interpreters.
Focus on function call overhead and basic operations.
"""
import time
import sys

def tiny_function():
    return 42

def main():
    # Many small function calls to stress bytecode dispatch
    result = 0
    for _ in range(10_000_000):
        result += tiny_function()

    return 0

if __name__ == "__main__":
    sys.exit(main())
