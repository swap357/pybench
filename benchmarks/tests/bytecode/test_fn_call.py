"""
Test bytecode dispatch overhead differences between interpreters.
Focus on function call overhead and basic operations.

Description: Function call overhead.
Bytecode Analysis:
Instructions count: 8
Instruction types: CALL, LOAD_CONST, LOAD_FAST, MAKE_FUNCTION, PUSH_NULL, RESUME, RETURN_VALUE, STORE_FAST

Purpose:
- Measure function call overhead
- Compare interpreter dispatch costs
- Evaluate nested function performance
- Baseline for call optimization
"""


import sys

def tiny_function_call():
    """Function call overhead."""
    def helper_function():
        return 42
    
    return helper_function()

def main():
    for _ in range(10_000_000):
        tiny_function_call()

    return 0

if __name__ == "__main__":
    sys.exit(main())