# Python Free-Threading Benchmarks

## Overview

analysis of performance characteristics in Python's experimental free-threading support (PEP 703) for Python 3.13+.

## Reference notes:
- [Thread Concepts](docs/understanding_thread_concepts.md) (thread affinity, ref counting, false sharing and specialization)
- [Memory Barriers](docs/understanding_memory_barriers.md) (memory ordering, false sharing and padded memory)
- [PEP 703: Making the GIL Optional](https://peps.python.org/pep-0703/)
- [Free Threading HOWTO](https://docs.python.org/3/howto/free-threading-python.html)


## Test Structure

### 1. Baseline Tests
Establish baseline performance metrics:
- [cpu-intensive performance](benchmarks/tests/baseline/test_cpu_ops_analysis.md)
- [mem-io performance](benchmarks/tests/baseline/test_memory_ops_analysis.md)
- [thread creation](benchmarks/tests/baseline/test_thread_mgmt_analysis.md)

### 2. Core Interpreter Tests

#### Bytecode Behavior
- [dispatch overhead](benchmarks/tests/bytecode/bytecode_dispatch_analysis.md)

#### GIL Impact
- [thread contention](benchmarks/tests/gil/test_contention.py)
- [lock patterns](benchmarks/tests/gil/test_lock_patterns.py)

#### Memory Management
Memory Ordering:
- [sequential access](benchmarks/tests/memory/ordering/test_memory_access_patterns_analysis.md)
- [strided access](benchmarks/tests/memory/ordering/test_memory_access_patterns_analysis.md)
- [memory alignment](benchmarks/tests/memory/ordering/test_memory_access_patterns_analysis.md)
- [false sharing (baseline)](benchmarks/tests/memory/ordering/test_false_sharing_analysis.md)
- [false sharing (padded)](benchmarks/tests/memory/ordering/test_false_sharing_analysis.md)

Reference Counting:
- [thread-local objects](benchmarks/tests/memory/ref_counting/ref_counting_patterns_analysis.md)
- [cross-thread objects](benchmarks/tests/memory/ref_counting/ref_counting_patterns_analysis.md)

#### Specialization
- [dynamic operations](benchmarks/tests/specialization/test_dynamic_operations.py)
- [typed operations](benchmarks/tests/specialization/test_dynamic_operations.py)

## Benchmark Setup - Github Actions

Runners:
- Github actions runner: 
  - CPU: 4 cores @ 2923.43 MHz
  - CPU affinity: All 4 cores
  - Memory: 15.61 GB
  - OS: Linux 6.5.0-1025-azure

- Local machine:
  - CPU: 20 cores @ 2022.67 MHz (Intel i7-14700K)
  - CPU affinity: 2-7 (6 isolated P-cores, refer to [this article](https://manuel.bernhardt.io/posts/2023-11-16-core-pinning/) for details on isolation and cpu-pinning)
  - Memory: 62.57 GB
  - OS: Linux 6.8.0-47-generic

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
- [benchmark-results](https://swap357.github.io/pybench)

## Future Work

study more after the following areas are addressed in Python 3.14+:
1. Re-enabling specializing adaptive interpreter
2. Reduced immortalization scope
3. Improved thread-safety mechanisms
4. Better memory usage patterns

