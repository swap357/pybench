"""
Thread scaling test for memory-bound operations.
Measures memory bandwidth scaling across threads.
"""
import time
import sys
import threading
import array
import sysconfig
import json
from datetime import datetime

def is_free_threading_enabled():
    """Check if running on free-threading Python build"""
    return bool(sysconfig.get_config_var("Py_GIL_DISABLED"))

def memory_intensive(data, iterations):
    """Memory-intensive operation"""
    result = 0
    for _ in range(iterations):
        for x in data:
            result += x
    return result

def thread_worker(data, iterations, results, index):
    """Worker function for threads"""
    result = memory_intensive(data, iterations)
    results[index] = result

def run_threaded_test(num_threads, data, iterations_per_thread):
    """Run memory operations across multiple threads"""
    threads = []
    results = [0] * num_threads
    
    start = time.perf_counter()
    
    for i in range(num_threads):
        t = threading.Thread(
            target=thread_worker,
            args=(data, iterations_per_thread, results, i)
        )
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
        
    duration = time.perf_counter() - start
    return duration, sum(results)

def main():
    # Test configuration - control variables
    array_size = 100_000  # Size of data array
    base_iterations = 100  # Base number of iterations
    element_size = 8  # Size of double in bytes
    
    # Test metadata
    metadata = {
        "test_name": "memory_bandwidth_scaling",
        "test_type": "memory_bound",
        "description": "Measures memory bandwidth scaling with thread count",
        "timestamp": datetime.now().isoformat(),
        "free_threading": is_free_threading_enabled(),
        "python_version": sys.version,
        
        # Control variables
        "control_vars": {
            "array_size": array_size,
            "base_iterations": base_iterations,
            "element_size_bytes": element_size,
            "total_array_size_MB": (array_size * element_size) / (1024 * 1024)
        }
    }
    
    # Create test data
    data = array.array('d', range(array_size))
    total_bytes = array_size * element_size * base_iterations
    
    # Baseline measurement
    start = time.perf_counter()
    baseline_result = memory_intensive(data, base_iterations)
    baseline_duration = time.perf_counter() - start
    
    baseline_bandwidth = total_bytes / (baseline_duration * 1024 * 1024)
    
    results = {
        "metadata": metadata,
        "baseline": {
            "duration": round(baseline_duration, 4),
            "bandwidth_MB_s": baseline_bandwidth,
            "result": baseline_result,
            "total_bytes": total_bytes
        },
        "scaling_tests": []
    }
    
    # Scaling tests
    thread_counts = [1, 2, 4, 8, 16, 32]  # Independent variable
    
    for num_threads in thread_counts:
        iterations_per_thread = base_iterations // num_threads
        duration, result = run_threaded_test(num_threads, data, iterations_per_thread)
        
        # Calculate dependent variables
        speedup = baseline_duration / duration
        bandwidth = total_bytes / (duration * 1024 * 1024)
        bandwidth_per_thread = bandwidth / num_threads
        efficiency = speedup / num_threads
        
        test_result = {
            # Independent variables
            "threads": num_threads,
            "iterations_per_thread": iterations_per_thread,
            
            # Primary dependent variables
            "duration": round(duration, 4),
            "speedup": speedup,
            
            # Memory bandwidth metrics
            "bandwidth_MB_s": bandwidth,
            "bandwidth_per_thread_MB_s": bandwidth_per_thread,
            "efficiency": efficiency,
            
            # Control/validation variables
            "total_bytes": total_bytes,
            "result": result,
            
            # Additional metrics
            "bytes_per_thread": total_bytes / num_threads,
            "theoretical_max_bandwidth_MB_s": baseline_bandwidth * num_threads
        }
        
        results["scaling_tests"].append(test_result)
    
    # Output JSON to stdout
    print(json.dumps(results))
    return 0

if __name__ == "__main__":
    sys.exit(main())