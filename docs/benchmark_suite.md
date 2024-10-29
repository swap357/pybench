# Python Interpreter Benchmark Suite

## Overview
This benchmark suite is designed to measure and compare performance characteristics across different Python versions, with a particular focus on Python 3.13's free-threading support (PEP 703) and its impact on performance.

For detailed context about free-threading and specific areas being tested, see [Free Threading Context](free_threading_context.md).

## Key Performance Targets

### Single-Thread Performance
- Baseline: Python 3.12.7
- Current overhead in 3.13.0t: ~40%
- Target overhead: ≤10%

### Multi-Thread Scaling
- Thread synchronization efficiency
- Memory barrier performance
- Cache-line contention handling
- Lock-free operation costs

## Benchmark Categories

### Core Benchmarks
Tests that measure fundamental Python interpreter behaviors:

#### Memory Management
- Reference counting overhead
- Object immortalization impact
- Memory barrier performance
- Cache alignment effects

#### Threading
- Lock acquisition patterns
- Thread synchronization costs
- Memory ordering guarantees
- Thread-local vs shared data access

#### Interpreter Features
- Specialization limitations
- Bytecode execution overhead
- Frame object handling
- Iterator behavior

### Workload Benchmarks
Real-world inspired workloads demonstrating practical performance patterns:

#### Parallel Processing
1. **Baseline Implementation**
   - No specific optimizations
   - Standard Python operations
   - Thread synchronization overhead

2. **Memory Optimized**
   - Pre-allocated arrays
   - Cache-friendly access
   - Reduced object creation

3. **Process-Based**
   - Multiprocessing alternatives
   - IPC overhead comparison
   - True parallelism benefits

## Implementation Details

### Benchmark Structure
Each benchmark follows these principles:
1. Single responsibility - tests one specific aspect
2. Consistent measurement - uses standardized timing approach
3. Reproducible results - controls for system variables
4. Clear documentation - explains what is being tested and why

### Key Features
- Automated test discovery and execution
- Statistical analysis of results
- System information collection
- HTML report generation with visualizations
- Support for multiple Python versions

## Running Benchmarks

### Basic Usage
```bash
python benchmark_runner.py
```

### Options
- `--iterations N`: Number of iterations for each benchmark
- `--profile [basic|detailed|none]`: Profiling level
- `--benchmarks [test names]`: Run specific benchmarks
- `--report-format [text|json|both]`: Output format

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

### Known Limitations
See [Free Threading Context](free_threading_context.md#known-limitations) for details about:
- Immortalization impact
- Frame object safety
- Iterator limitations
- Single-threaded performance overhead

## Contributing
Contributions are welcome! When adding new benchmarks:
1. Follow the single-responsibility principle
2. Add appropriate documentation
3. Place in the correct category directory
4. Include baseline and optimized versions if applicable
5. Add test description to this documentation

## References
- [PEP 703 – Making the Global Interpreter Lock Optional in CPython](https://peps.python.org/pep-0703/)
- [Python HOWTOs - Free Threading](https://docs.python.org/3/howto/free-threading-python.html)
- [Free Threading Context](free_threading_context.md)