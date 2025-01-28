"""
Thread scaling test measuring impact of lock contention.
"""
import time
import sys
import threading
import sysconfig
import json
from datetime import datetime

def is_free_threading_enabled() -> bool:
    """Check if Python is running with free threading (GIL disabled)"""
    # Use runtime check for GIL status
    try:
        return not sys._is_gil_enabled()  # Returns True if GIL is disabled
    except AttributeError:
        return False  # If _is_gil_enabled doesn't exist, GIL is enabled

def cpu_intensive(iterations):
    """Pure CPU work under lock"""
    result = 0
    for i in range(iterations):
        result += i * i
    return result

def thread_worker(iterations, results, index, shared_lock):
    """Worker function that always uses lock"""
    with shared_lock:
        result = cpu_intensive(iterations)
    results[index] = result

def run_contention_test(num_threads, iterations_per_thread):
    """Run test with explicit lock contention"""
    threads = []
    results = [0] * num_threads
    shared_lock = threading.Lock()
    
    start = time.perf_counter()
    
    # Create and start threads
    for i in range(num_threads):
        t = threading.Thread(
            target=thread_worker,
            args=(iterations_per_thread, results, i, shared_lock)
        )
        threads.append(t)
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
        
    duration = time.perf_counter() - start
    return duration, sum(results)

def main():
    # Test configuration - control variables
    base_iterations = 1_000_000
    
    # Test metadata
    metadata = {
        "test_name": "lock_contention_scaling",
        "test_type": "lock_contention",
        "description": "Measures impact of lock contention on parallel scaling",
        "timestamp": datetime.now().isoformat(),
        "free_threading": is_free_threading_enabled(),
        "python_version": sys.version,
        
        # Control variables
        "control_vars": {
            "base_iterations": base_iterations,
            "lock_type": "threading.Lock",
            "workload": "cpu_intensive"
        }
    }
    
    # Baseline measurement (single-threaded with lock)
    start = time.perf_counter()
    baseline_results = [0]
    lock = threading.Lock()
    with lock:
        baseline_results[0] = cpu_intensive(base_iterations)
    baseline_duration = time.perf_counter() - start
    
    baseline_ops_per_sec = base_iterations / baseline_duration
    
    results = {
        "metadata": metadata,
        "baseline": {
            "duration": round(baseline_duration, 4),
            "ops_per_sec": baseline_ops_per_sec,
            "result": baseline_results[0],
            "total_ops": base_iterations
        },
        "scaling_tests": []
    }
    
    # Scaling tests
    thread_counts = [2, 4, 8, 16, 32, 48, 64, 96, 112, 128]
    
    for num_threads in thread_counts:
        iterations_per_thread = base_iterations // num_threads
        duration, result = run_contention_test(num_threads, iterations_per_thread)
        
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
            "duration": round(duration, 4),
            "speedup": speedup,
            
            # Lock contention metrics
            "ops_per_sec": ops_per_sec,
            "ops_per_thread": ops_per_thread,
            "efficiency": efficiency,
            "contention_factor": baseline_ops_per_sec / ops_per_thread,
            
            # Control/validation variables
            "total_ops": total_ops,
            "result": result,
            
            # Additional metrics
            "theoretical_max_ops": baseline_ops_per_sec * num_threads,
            "contention_overhead": (duration * num_threads / baseline_duration) - 1
        }
        
        results["scaling_tests"].append(test_result)
    
    # Output JSON to stdout
    print(json.dumps(results))
    return 0

if __name__ == "__main__":
    sys.exit(main())