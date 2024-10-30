# Python Free-Threading Benchmarks

## Overview

A systematic analysis of performance characteristics in Python's experimental free-threading support (PEP 703) for Python 3.13+.

## Test Structure

### 1. Baseline Tests
Establish baseline performance metrics:
- [CPU Performance](tests/baseline/test_cpu_baseline.py)
- [Memory Operations](tests/baseline/test_memory_baseline.py)
- [Thread Creation](tests/baseline/test_thread_baseline.py)

### 2. Core Interpreter Tests

#### Bytecode Behavior
- [Dispatch Overhead](tests/bytecode/test_bytecode_dispatch.py)

#### GIL Impact
- [Thread Contention](tests/gil/test_contention.py)
- [Lock Patterns](tests/gil/test_lock_patterns.py)

#### Memory Management
Memory Ordering:
- [Sequential Access](tests/memory/ordering/test_sequential_access.py)
- [Strided Access](tests/memory/ordering/test_strided_access.py)
- [Memory Alignment](tests/memory/ordering/test_alignment.py)
- [False Sharing (Baseline)](tests/memory/ordering/test_false_sharing_baseline.py)
- [False Sharing (Padded)](tests/memory/ordering/test_false_sharing_padded.py)

Reference Counting:
- [Thread-Local Objects](tests/memory/ref_counting/test_thread_local.py)
- [Cross-Thread Objects](tests/memory/ref_counting/test_cross_thread.py)

#### Specialization
- [Dynamic Operations](tests/specialization/test_dynamic_operations.py)
- [Typed Operations](tests/specialization/test_typed_operations.py)

## Key Findings


## Running Benchmarks

```bash
# Run all tests
python benchmark_runner.py

# Run specific category
python benchmark_runner.py --benchmarks memory/ordering/*

# Run with profiling
python benchmark_runner.py --profile detailed
```

## System Requirements

- Linux kernel 5.10+
- Python versions:
  - 3.12.7 (baseline)
  - 3.13.0 (with GIL)
  - 3.13.0t (no GIL)

## Results Dashboard
- [Benchmark Results](https://swap357.github.io/pybench)

## Future Work

Areas for improvement in Python 3.14+:
1. Re-enabling specializing adaptive interpreter
2. Reduced immortalization scope
3. Improved thread-safety mechanisms
4. Better memory usage patterns

## References

- [PEP 703: Making the GIL Optional](https://peps.python.org/pep-0703/)
- [Free Threading HOWTO](https://docs.python.org/3/howto/free-threading-python.html)
- [Free Threading Context](docs/free_threading_context.md)
- [Core Concepts](docs/core_concepts.md)
