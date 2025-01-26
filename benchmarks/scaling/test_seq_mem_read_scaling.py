"""
Thread scaling test for memory-bound operations.
Measures memory bandwidth scaling across threads.
"""
import time
import sys
import threading
import array
import sysconfig
from datetime import datetime
import json

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
    # Test configuration - targeting 512MB to match lmbench
    element_size = 8  # Size of double in bytes
    target_size_mb = 512  # Target size in MB
    array_size = int((target_size_mb * 1024 * 1024) / element_size)
    base_iterations = 10  # Number of times to read through data
    
    print(f"Initializing {target_size_mb}MB test array...", file=sys.stderr)
    
    # Create test data
    data = array.array('d', range(array_size))
    total_bytes = array_size * element_size * base_iterations
    
    # Test metadata
    metadata = {
        "test_name": "memory_bandwidth_scaling",
        "timestamp": datetime.now().isoformat(),
        "array_size_bytes": array_size * element_size,
        "array_size_mb": target_size_mb,
        "iterations": base_iterations,
        "element_size_bytes": element_size,
        "python_version": sys.version,
        "free_threading": bool(sysconfig.get_config_var("Py_GIL_DISABLED"))
    }
    
    # Baseline measurement (single thread)
    print("Running baseline single-thread test...", file=sys.stderr)
    start = time.perf_counter()
    baseline_result = memory_intensive(data, base_iterations)
    baseline_duration = time.perf_counter() - start
    
    baseline_throughput = total_bytes / (baseline_duration * 1024 * 1024)  # MB/s
    print(f"Baseline throughput: {baseline_throughput:.2f} MB/s", file=sys.stderr)
    
    results = {
        "metadata": metadata,
        "baseline": {
            "duration": baseline_duration,
            "throughput_MB_s": baseline_throughput,
            "result": baseline_result
        },
        "scaling_tests": []
    }
    
    # Scaling tests
    thread_counts = [1, 2, 4, 8, 16, 32, 48, 60, 64, 72, 96, 112, 128]
    
    print("\nRunning scaling tests...", file=sys.stderr)
    for num_threads in thread_counts:
        print(f"Testing with {num_threads} threads...", file=sys.stderr)
        
        # Run multiple times and take best result
        best_throughput = 0
        for run in range(3):
            iterations_per_thread = base_iterations // num_threads
            duration, result = run_threaded_test(num_threads, data, iterations_per_thread)
            
            throughput = total_bytes / (duration * 1024 * 1024)  # MB/s
            best_throughput = max(best_throughput, throughput)
        
        speedup = baseline_duration / duration
        print(f"Throughput: {best_throughput:.2f} MB/s (speedup: {speedup:.2f}x)", file=sys.stderr)
        
        results["scaling_tests"].append({
            "threads": num_threads,
            "throughput_MB_s": best_throughput,
            "speedup": speedup,
            "duration": duration
        })
    
    # Output JSON results to stdout
    print(json.dumps(results, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())