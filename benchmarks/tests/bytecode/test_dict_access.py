"""
Test bytecode dispatch overhead differences between interpreters.
Focus on function call overhead and basic operations.

Function: tiny_dict_access
Description: Accessing a dictionary value.
Bytecode Analysis:
Instructions count: 9
Instruction types: BINARY_SUBSCR, BUILD_MAP, LOAD_CONST, LOAD_FAST, RESUME, RETURN_VALUE, STORE_FAST
"""

import sys

def tiny_dict_access():
    """Accessing a dictionary value."""
    d = {"key": 42}
    return d["key"]

def main():
    for _ in range(10_000_000):
        tiny_dict_access()

    return 0

if __name__ == "__main__":
    sys.exit(main())
