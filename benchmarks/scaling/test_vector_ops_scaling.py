"""
Thread scaling test for vector operations.
Measures scaling behavior of vectorized computations to highlight
differences between:
- ARMv8: NEON (128-bit vectors)
- ARMv9: SVE2 (scalable vectors with enhanced instructions)
"""
import time
import sys
import threading
import sysconfig
import json
from datetime import datetime
import numpy as np

def is_free_threading_enabled():
    """Check if running on free-threading Python build"""
    return bool(sysconfig.get_config_var("Py_GIL_DISABLED"))

def vector_intensive(size, iterations):
    """
    Vector operations chosen to highlight ARMv8 vs ARMv9 differences:
    - Fused multiply-add (NEON vs SVE2 FMLA)
    - Dot product (SVE2 optimized)
    - Vector comparisons (SVE2 predicates)
    """
    results = []
    
    for _ in range(iterations):
        # Create input arrays
        a = np.random.random(size).astype(np.float32)
        b = np.random.random(size).astype(np.float32)
        c = np.random.random(size).astype(np.float32)
        
        start = time.perf_counter()
        
        # 1. Fused multiply-add operations
        d = np.multiply(a, b)
        d = np.add(d, c)
        
        # 2. Dot product - benefits from SVE2
        e = np.dot(a, b)
        
        # 3. Vector comparisons
        f = np.maximum(a, b)
        g = np.minimum(a, b)
        
        # 4. Final reduction to prevent optimization
        result = float(e + np.sum(d) + np.sum(f) + np.sum(g))
        
        duration = time.perf_counter() - start
        results.append((duration, result))
    
    # Return average duration and final result
    avg_duration = sum(r[0] for r in results) / len(results)
    final_result = results[-1][1]
    return avg_duration, final_result

def thread_worker(size, iterations, results, index):
    """Worker function for threads"""
    duration, result = vector_intensive(size, iterations)
    results[index] = {"duration": duration, "result": result}

def main():
    # Test configuration
    array_size = 10_000_000  # Large enough to show vector differences
    base_iterations = 5
    
    # Baseline measurement (single-threaded)
    start = time.perf_counter()
    baseline_results = [{}]
    thread_worker(array_size, base_iterations, baseline_results, 0)
    baseline_duration = time.perf_counter() - start
    
    # Run scaling tests
    thread_counts = [2, 4, 8, 16, 32]
    results = []
    
    for num_threads in thread_counts:
        threads = []
        test_results = [{} for _ in range(num_threads)]
        iterations_per_thread = base_iterations // num_threads
        
        start = time.perf_counter()
        
        for i in range(num_threads):
            t = threading.Thread(
                target=thread_worker,
                args=(array_size, iterations_per_thread, test_results, i)
            )
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
            
        duration = time.perf_counter() - start
        speedup = baseline_duration / duration
        
        # Calculate average thread duration
        thread_durations = [r["duration"] for r in test_results]
        avg_thread_duration = sum(thread_durations) / len(thread_durations)
        
        results.append({
            "threads": num_threads,
            "duration": round(duration, 4),
            "avg_thread_duration": round(avg_thread_duration, 4),
            "speedup": speedup,
            "efficiency": speedup / num_threads,
            "operations_per_thread": {
                "array_size": array_size,
                "iterations": iterations_per_thread,
                "vector_ops": [
                    "fused_multiply_add",
                    "dot_product",
                    "vector_maximum",
                    "vector_minimum"
                ]
            }
        })
    
    # Output results
    print(json.dumps({
        "metadata": {
            "test_name": "vector_ops_scaling",
            "description": "Vector operations scaling test (NEON vs SVE2)",
            "timestamp": datetime.now().isoformat(),
            "free_threading": is_free_threading_enabled(),
            "array_size": array_size,
            "base_iterations": base_iterations
        },
        "baseline": {
            "duration": baseline_duration,
            "thread_duration": baseline_results[0]["duration"],
            "result": baseline_results[0]["result"]
        },
        "scaling_results": results
    }, indent=2))
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 