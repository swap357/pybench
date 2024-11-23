"""
Test bytecode dispatch overhead differences between interpreters.
Focus on function call overhead and basic operations.
"""
import sys

def tiny_load_const():
    """Single LOAD_CONST instruction."""
    return 42

def main():
    for _ in range(10_000_000):
        tiny_load_const()

    return 0

if __name__ == "__main__":
    sys.exit(main())
