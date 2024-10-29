# Python Free-Threading Benchmarks

## Context

Free-threading support in Python 3.13 (PEP 703) is an experimental feature that allows the Global Interpreter Lock (GIL) to be released for certain operations, potentially improving performance for certain workloads.
- [PEP 703 – Making the Global Interpreter Lock Optional in CPython](https://peps.python.org/pep-0703/)
- [Python HOWTOs - Free Threading](https://docs.python.org/3/howto/free-threading-python.html)

## Key Areas of Focus mentioned on PEP 703 and Python HOWTOs

### 1. Single-Threaded Performance Impact
Current overhead: ~40% in Python 3.13 (pyperformance suite)
Target: 10% or less in future releases

Our benchmarks measure:
- Basic operation overhead
- Object creation/destruction patterns
- Reference counting impact
- Memory allocation patterns

### 2. Multi-Threaded Scaling
Baseline comparison between:
- Python 3.12 (with GIL)
- Python 3.13 (with GIL)
- Python 3.13t (no GIL)

Focus areas:
- Thread synchronization overhead
- Memory barrier effectiveness
- Cache-line contention
- Lock-free operations

### 3. Known Limitations Testing

#### Immortalization Impact
Testing memory usage patterns for:
- Module-level functions
- Method descriptors
- Code objects
- Module objects
- Class objects (type objects)
- String literals and interned strings

#### Frame Object Safety
Benchmarks to verify:
- Safe frame access patterns
- Cross-thread frame access issues
- Performance impact of frame restrictions

#### Iterator Safety
Tests covering:
- Single-thread iterator performance
- Multi-thread iterator behavior
- Safe vs unsafe iterator patterns

## Benchmark Categories

### Core Benchmarks
1. **Memory Management**
   - Reference counting overhead
   - Object immortalization impact
   - Memory barrier performance
   - Cache alignment effects

2. **Threading Behavior**
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

2. **Parallel Processing Patterns**
   - Thread pool usage
   - Process pool alternatives
   - Hybrid approaches
   - Scaling characteristics

## Performance Targets

### Single-Thread Overhead
| Python Version | Current | Target |
|---------------|---------|---------|
| 3.13.0t       | ~40%    | ≤10%    |

### Multi-Thread Scaling
Expected scaling patterns:
- Linear scaling for CPU-bound work
- Near-linear for mixed workloads
- I/O-bound limited by system resources

## Known Limitations

1. **Specialization Restrictions**
   - One-time bytecode specialization in multi-threaded code
   - Impact on hot path optimization
   - Workarounds and alternatives

2. **Memory Trade-offs**
   - Increased memory usage from immortalization
   - Reference counting overhead
   - Cache line padding costs

3. **Safety Constraints**
   - Frame object access limitations
   - Iterator sharing restrictions
   - Thread-local vs shared data patterns

## Future Improvements

Tracking areas for improvement in Python 3.14+:
1. Re-enabling specializing adaptive interpreter
2. Reduced immortalization scope
3. Improved thread-safety mechanisms
4. Better memory usage patterns

## References

- [PEP 703 – Making the Global Interpreter Lock Optional in CPython](https://peps.python.org/pep-0703/)
- [Python HOWTOs - Free Threading](https://docs.python.org/3/howto/free-threading-python.html)
- [CPython Issue Tracker - Free Threading Implementation](https://github.com/python/cpython/issues/tracker/free-threading) 