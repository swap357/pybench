"""
Thread scaling test for local object churn patterns.
Measures scaling of object creation/destruction in thread-local scope.
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

class TestObject:
    """Test object with no special handling"""
    def __init__(self, value):
        self.value = value
        # List overhead: 56 bytes (empty list)
        # Integer array: 100 integers × 8 bytes = 800 bytes
        # Total object size: 920 bytes (56 + 800 + object overhead + value attr)
        self.data = [i for i in range(100)]

def thread_worker(iterations, results, index):
    """Worker function that exercises object churn patterns"""
    # Pre-allocate objects to separate allocation costs
    objects_pool = [TestObject(i) for i in range(100)]
    local_refs = [None] * 100
    
    num_passes = iterations // len(objects_pool)
    
    start = time.perf_counter()
    
    # Pure reference counting test
    for _ in range(num_passes):
        for i in range(len(objects_pool)):
            local_refs[i] = objects_pool[i]  # INCREF
            local_refs[i] = None             # DECREF
            
    duration = time.perf_counter() - start
    results[index] = duration

def run_threaded_test(num_threads, iterations_per_thread):
    """Run reference counting operations across threads"""
    threads = []
    results = [0] * num_threads
    
    start = time.perf_counter()
    
    for i in range(num_threads):
        t = threading.Thread(
            target=thread_worker,
            args=(iterations_per_thread, results, i)
        )
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
        
    duration = time.perf_counter() - start
    return duration, results

def main():
    # Test configuration
    base_iterations = 1_000_000
    
    metadata = {
        "test_name": "object_churn_local_scaling",
        "test_type": "object_churn",
        "description": "Measures thread-local object churn overhead scaling",
        "timestamp": datetime.now().isoformat(),
        "free_threading": is_free_threading_enabled(),
        "python_version": sys.version,
        "control_vars": {
            "base_iterations": base_iterations,
            "object_pool_size": 100,
            "object_size": "~872 bytes",
            "churn_type": "local"
        }
    }
    
    # Baseline measurement (single thread)
    results = [0]
    thread_worker(base_iterations, results, 0)
    baseline_duration = results[0]
    
    baseline_ops_per_sec = (base_iterations * 2) / baseline_duration  # 2 ops per iteration
    
    results = {
        "metadata": metadata,
        "baseline": {
            "duration": round(baseline_duration, 4),
            "ops_per_sec": baseline_ops_per_sec,
            "total_ops": base_iterations * 2
        },
        "scaling_tests": []
    }
    
    # Scaling tests
    thread_counts = [2, 4, 8, 16, 32, 48, 64, 96, 112, 128]
    
    for num_threads in thread_counts:
        iterations_per_thread = base_iterations // num_threads
        duration, thread_times = run_threaded_test(num_threads, iterations_per_thread)
        
        total_ref_ops = iterations_per_thread * num_threads * 2  # INCREF + DECREF
        refs_per_sec = total_ref_ops / duration
        speedup = baseline_duration / duration
        efficiency = speedup / num_threads
        
        test_result = {
            "threads": num_threads,
            "duration": round(duration, 4),
            "thread_times": [round(t, 4) for t in thread_times],
            "speedup": round(speedup, 4),
            "efficiency": round(efficiency, 4),
            "refs_per_sec": round(refs_per_sec, 2),
            "refs_per_thread": round(refs_per_sec / num_threads, 2),
            "total_ref_ops": total_ref_ops
        }
        
        results["scaling_tests"].append(test_result)
    
    print(json.dumps(results))
    return 0

if __name__ == "__main__":
    sys.exit(main())
