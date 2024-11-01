"""
Thread scaling test for memory-bound operations.
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
    
    start = time.time()
    
    for i in range(num_threads):
        t = threading.Thread(
            target=thread_worker,
            args=(data, iterations_per_thread, results, i)
        )
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
        
    duration = time.time() - start
    return duration, sum(results)

def main():
    # Test configuration
    array_size = 100_000
    base_iterations = 100
    element_size = 8  # size of double
    
    metadata = {
        "test_name": "memory_bandwidth_scaling",
        "timestamp": datetime.now().isoformat(),
        "free_threading": is_free_threading_enabled(),
        "python_version": sys.version,
        "array_size": array_size,
        "base_iterations": base_iterations,
        "element_size_bytes": element_size
    }
    
    results = {
        "metadata": metadata,
        "baseline": {},
        "scaling_tests": []
    }
    
    # Create test data
    data = array.array('d', range(array_size))
    total_bytes = array_size * element_size * base_iterations
    
    # Baseline measurement
    start = time.time()
    baseline_result = memory_intensive(data, base_iterations)
    baseline_duration = time.time() - start
    
    results["baseline"] = {
        "duration": baseline_duration,
        "bandwidth_MB_s": total_bytes / (baseline_duration * 1024 * 1024),
        "result": baseline_result
    }
    
    # Scaling tests
    for num_threads in [1, 2, 4, 8, 16, 32]:
        iterations_per_thread = base_iterations // num_threads
        duration, result = run_threaded_test(num_threads, data, iterations_per_thread)
        
        speedup = baseline_duration / duration
        bandwidth = total_bytes / (duration * 1024 * 1024)
        
        test_result = {
            "threads": num_threads,
            "duration": duration,
            "speedup": speedup,
            "bandwidth_MB_s": bandwidth,
            "iterations_per_thread": iterations_per_thread,
            "total_bytes": total_bytes,
            "result": result
        }
        
        results["scaling_tests"].append(test_result)
    
    # Output JSON to stdout
    print(json.dumps(results))
    return 0

if __name__ == "__main__":
    sys.exit(main()) 