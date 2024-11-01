"""
Thread scaling test for pure parallel computation without contention.
"""
import time
import sys
import threading
import sysconfig
import json
from datetime import datetime

def is_free_threading_enabled():
    """Check if running on free-threading Python build"""
    return bool(sysconfig.get_config_var("Py_GIL_DISABLED"))

def cpu_intensive(iterations):
    """Pure CPU work"""
    result = 0
    for i in range(iterations):
        result += i * i
    return result

def thread_worker(iterations, results, index):
    """Worker function for threads"""
    result = cpu_intensive(iterations)
    results[index] = result

def run_parallel_test(num_threads, iterations_per_thread):
    """Run parallel computation test"""
    threads = []
    results = [0] * num_threads
    
    start = time.time()
    
    # Create and start threads
    for i in range(num_threads):
        t = threading.Thread(
            target=thread_worker,
            args=(iterations_per_thread, results, i)
        )
        threads.append(t)
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
        
    duration = time.time() - start
    return duration, sum(results)

def main():
    base_iterations = 1_000_000
    
    metadata = {
        "test_name": "parallel_compute_scaling",
        "description": "Measures pure parallel computation scaling without contention",
        "timestamp": datetime.now().isoformat(),
        "free_threading": is_free_threading_enabled(),
        "python_version": sys.version,
        "base_iterations": base_iterations,
    }
    
    results = {
        "metadata": metadata,
        "baseline": {},
        "scaling_tests": []
    }
    
    # Baseline measurement (single-threaded)
    start = time.time()
    baseline_results = [0]
    thread_worker(base_iterations, baseline_results, 0)
    baseline_duration = time.time() - start
    
    results["baseline"] = {
        "duration": baseline_duration,
        "ops_per_sec": base_iterations/baseline_duration,
        "result": baseline_results[0]
    }
    
    # Scaling tests
    for num_threads in [1, 2, 4, 8, 16, 32]:
        iterations_per_thread = base_iterations // num_threads
        duration, result = run_parallel_test(num_threads, iterations_per_thread)
        
        speedup = baseline_duration / duration
        ops_per_sec = (iterations_per_thread * num_threads) / duration
        
        test_result = {
            "threads": num_threads,
            "duration": duration,
            "speedup": speedup,
            "ops_per_sec": ops_per_sec,
            "iterations_per_thread": iterations_per_thread,
            "total_ops": iterations_per_thread * num_threads,
            "result": result
        }
        
        results["scaling_tests"].append(test_result)
    
    print(json.dumps(results))
    return 0

if __name__ == "__main__":
    sys.exit(main()) 