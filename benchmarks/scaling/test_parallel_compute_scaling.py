"""
Thread scaling test for pure parallel computation without contention.
Measures ideal scaling behavior with independent CPU-bound work.
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
    # Test configuration - control variables
    base_iterations = 1_000_000
    
    # Test metadata
    metadata = {
        "test_name": "parallel_compute_scaling",
        "test_type": "cpu_bound",
        "description": "Measures pure parallel computation scaling without contention",
        "timestamp": datetime.now().isoformat(),
        "free_threading": is_free_threading_enabled(),
        "python_version": sys.version,
        
        # Control variables
        "control_vars": {
            "base_iterations": base_iterations,
            "operation_type": "integer_arithmetic",
            "workload": "cpu_intensive",
            "shared_resources": "none"
        }
    }
    
    # Baseline measurement (single-threaded)
    start = time.time()
    baseline_results = [0]
    thread_worker(base_iterations, baseline_results, 0)
    baseline_duration = time.time() - start
    
    baseline_ops_per_sec = base_iterations / baseline_duration
    
    results = {
        "metadata": metadata,
        "baseline": {
            "duration": baseline_duration,
            "ops_per_sec": baseline_ops_per_sec,
            "result": baseline_results[0],
            "total_ops": base_iterations
        },
        "scaling_tests": []
    }
    
    # Scaling tests
    thread_counts = [1, 2, 4, 8, 16, 32]  # Independent variable
    
    for num_threads in thread_counts:
        iterations_per_thread = base_iterations // num_threads
        duration, result = run_parallel_test(num_threads, iterations_per_thread)
        
        # Calculate dependent variables
        speedup = baseline_duration / duration
        total_ops = iterations_per_thread * num_threads
        ops_per_sec = total_ops / duration
        ops_per_thread = ops_per_sec / num_threads
        efficiency = speedup / num_threads
        
        test_result = {
            # Independent variables
            "threads": num_threads,
            "iterations_per_thread": iterations_per_thread,
            
            # Primary dependent variables
            "duration": duration,
            "speedup": speedup,
            
            # Performance metrics
            "ops_per_sec": ops_per_sec,
            "ops_per_thread": ops_per_thread,
            "efficiency": efficiency,
            
            # Control/validation variables
            "total_ops": total_ops,
            "result": result,
            
            # Additional metrics
            "theoretical_max_ops": baseline_ops_per_sec * num_threads,
            "scaling_efficiency": ops_per_thread / baseline_ops_per_sec,
            "parallelization_overhead": (duration * num_threads / baseline_duration) - 1,
            "ideal_scaling_ratio": speedup / num_threads  # 1.0 means perfect scaling
        }
        
        results["scaling_tests"].append(test_result)
    
    # Output JSON to stdout
    print(json.dumps(results))
    return 0

if __name__ == "__main__":
    sys.exit(main())