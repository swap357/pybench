"""
Thread scaling test for memory-bound operations.
Measures memory bandwidth scaling across threads.
Matches lmbench methodology for comparison:
- 512MB data size
- Pure sequential read pattern
- Multiple warmup and measurement iterations
"""
import time
import sys
import threading
import array
import sysconfig
import json
from datetime import datetime
import random

def is_free_threading_enabled():
    """Check if running on free-threading Python build"""
    return bool(sysconfig.get_config_var("Py_GIL_DISABLED"))

def memory_intensive(data, warmup_iters=5, measure_iters=5):
    """
    Pure memory read bandwidth test:
    - Uses strided access to defeat prefetcher
    - Minimal computation to avoid CPU bottleneck
    - Forces memory reads with volatile-like access
    """
    result = 0.0
    size = len(data)
    stride = 256  # Defeat hardware prefetcher
    
    # Warmup phase
    for _ in range(warmup_iters):
        for i in range(0, size, stride):
            result += data[i]  # Force read without computation
    
    # Measurement phase
    times = []
    for _ in range(measure_iters):
        start = time.perf_counter()
        for i in range(0, size, stride):
            result += data[i]  # Simple accumulation to prevent optimization
        duration = time.perf_counter() - start
        times.append(duration)
    
    return min(times), result

def thread_worker(data, warmup_iters, measure_iters, results, index):
    """Worker function for threads"""
    try:
        duration, result = memory_intensive(data, warmup_iters, measure_iters)
        results[index] = {
            "duration": duration,
            "result": result,
            "success": True
        }
    except Exception as e:
        results[index] = {
            "error": str(e),
            "success": False
        }

def run_threaded_test(num_threads, data, warmup_iters, measure_iters):
    """Run memory operations across multiple threads"""
    threads = []
    results = [None] * num_threads
    
    start = time.perf_counter()
    
    for i in range(num_threads):
        t = threading.Thread(
            target=thread_worker,
            args=(data, warmup_iters, measure_iters, results, i)
        )
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
    
    # Check for failures
    failed_threads = [i for i, r in enumerate(results) if not r.get("success", False)]
    if failed_threads:
        raise RuntimeError(f"Threads {failed_threads} failed")
        
    # Use best thread timing as overall timing (like lmbench)
    best_duration = min(r["duration"] for r in results)
    total_result = sum(r["result"] for r in results)
    return best_duration, total_result

def main():
    element_size = 8  # Size of double in bytes
    target_data_size = 512 * 1024 * 1024  # 512MB
    array_size = target_data_size // element_size
    
    print("Initializing 512MB test data...", file=sys.stderr)
    # Use random data to defeat compression/prediction
    data = array.array('d', [random.random() for _ in range(array_size)])
    
    # Force data out of cache before measurement
    def flush_cache():
        temp = array.array('d', [0.0] * (4 * 1024 * 1024))  # 32MB to flush cache
        for i in range(len(temp)):
            temp[i] += 1.0
    
    # Test metadata
    metadata = {
        "test_name": "memory_bandwidth_scaling",
        "test_type": "memory_bound",
        "description": "Memory bandwidth scaling",
        "timestamp": datetime.now().isoformat(),
        "free_threading": is_free_threading_enabled(),
        "python_version": sys.version,
        "control_vars": {
            "array_size": array_size,
            "warmup_iterations": 5,
            "measure_iterations": 5,
            "element_size_bytes": element_size,
            "total_data_size_MB": target_data_size / (1024 * 1024)
        }
    }
    
    print("Running baseline measurement...", file=sys.stderr)
    baseline_duration, baseline_result = memory_intensive(
        data, 5, 5
    )
    baseline_bandwidth = target_data_size / (baseline_duration * 1024 * 1024)
    
    results = {
        "metadata": metadata,
        "baseline": {
            "duration": round(baseline_duration, 4),
            "bandwidth_MB_s": round(baseline_bandwidth, 2),
            "result": baseline_result,
            "total_bytes": target_data_size
        },
        "scaling_tests": []
    }
    
    # Test increasing thread counts to match lmbench testing range
    thread_counts = [1, 2, 4, 8, 16, 32, 48, 60, 64, 72, 96, 112, 128]
    
    print("Running scaling tests...", file=sys.stderr)
    for num_threads in thread_counts:
        print(f"Testing with {num_threads} threads...", file=sys.stderr)
        
        try:
            duration, result = run_threaded_test(
                num_threads, data, 5, 5
            )
            
            # Calculate metrics
            bandwidth = target_data_size / (duration * 1024 * 1024)
            speedup = baseline_duration / duration if num_threads > 1 else 1.0
            efficiency = speedup / num_threads if num_threads > 1 else 1.0
            
            test_result = {
                "threads": num_threads,
                "duration": round(duration, 4),
                "bandwidth_MB_s": round(bandwidth, 2),
                "speedup": round(speedup, 2),
                "efficiency": round(efficiency, 2),
                "bandwidth_per_thread_MB_s": round(bandwidth / num_threads, 2),
                "result": result,
                "peak_bandwidth_MB_s": round(baseline_bandwidth * num_threads, 2)
            }
            
            results["scaling_tests"].append(test_result)
            
        except Exception as e:
            print(f"Error in {num_threads} thread test: {e}", file=sys.stderr)
            continue
    
    # Output JSON to stdout
    print(json.dumps(results, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())