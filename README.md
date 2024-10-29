# Python Free-Threading Performance Benchmarks

A comprehensive benchmark suite measuring performance characteristics of Python's experimental free-threading support (PEP 703) in Python 3.13+.

## Overview

This benchmark suite focuses on measuring and analyzing performance impacts of Python's free-threading implementation, particularly:

### Single-Thread Performance
- Current overhead: ~40% in Python 3.13
- Target overhead: ≤10% in future releases
- Impact of disabled specializing adaptive interpreter
- Reference counting overhead

### Multi-Thread Scaling
- Thread synchronization patterns
- Memory barrier effectiveness
- Cache-line contention
- Lock-free operations

### Known Limitations
- Object immortalization impact
- Frame object safety constraints
- Iterator sharing restrictions
- Memory management trade-offs

## Documentation

### Core Concepts
- [Free Threading Context](docs/free_threading_context.md) - Overview of PEP 703 and its implications
- [Memory Barriers](docs/memory_barriers_explained.md) - Understanding memory ordering and barriers
- [Core Concepts](docs/core_concepts.md) - Thread affinity, reference counting, and specialization

## Benchmark Categories

### Core Benchmarks
1. **Memory Management**
   - Reference counting overhead
   - Object immortalization impact
   - Memory barrier performance
   - Cache alignment effects

2. **Threading**
   - Lock acquisition patterns
   - Thread synchronization costs
   - Memory ordering guarantees
   - Thread-local vs shared data access

3. **Interpreter Features**
   - Specialization limitations
   - Bytecode execution overhead
   - Frame object handling
   - Iterator behavior

### Workload Benchmarks
Real-world inspired scenarios showing:

1. **Optimization Progression**
   - Naive implementation (baseline)
   - Memory-optimized version
   - Thread-safe optimized version
   - Fully optimized implementation

2. **Parallel Processing**
   - Thread pool usage
   - Process pool alternatives
   - Hybrid approaches
   - Scaling characteristics

## Results from CI runs 
[swap357.github.io/pybench](https://swap357.github.io/pybench)

## Quick Start

1. Clone the repository:
```bash
git clone https://github.com/yourusername/python-interpreter-benchmarks.git
cd python-interpreter-benchmarks
```

2. Run benchmarks:
```bash
python benchmark_runner.py
```


## Understanding Results

### Performance Metrics
- Mean duration: Average execution time
- Standard deviation: Variation in measurements
- Relative performance: Comparison to baseline version
- Min/Max times: Range of measurements

### Status Categories
- Baseline: Reference measurement (Python 3.12)
- Improved: >10% faster than baseline
- Similar: Within ±10% of baseline
- Degraded: >10% slower than baseline

## Requirements

### Python Versions
- Python 3.12.7 (baseline)
- Python 3.13.0 (with GIL)
- Python 3.13.0t (no GIL)

Use pyenv to install and switch between versions.
```bash
curl https://pyenv.run | bash
echo 'eval "$(pyenv init -)"' >> ~/.bashrc
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
        echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

```bash
pyenv install -s 3.12.7
pyenv install -s 3.13.0
pyenv install -s 3.13.0t
```

## References

- [PEP 703 – Making the Global Interpreter Lock Optional in CPython](https://peps.python.org/pep-0703/)
- [Python HOWTOs - Free Threading](https://docs.python.org/3/howto/free-threading-python.html)
- [CPython Issue Tracker - Free Threading Implementation](https://github.com/python/cpython/issues/tracker/free-threading)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

