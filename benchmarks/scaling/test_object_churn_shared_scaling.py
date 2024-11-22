"""
Thread scaling test for cross-thread object churn patterns.
Measures scaling of object operations across threads with shared resources.
"""
import time
import sys
import threading
import sysconfig
import json
from datetime import datetime

def is_free_threading_enabled():
    return bool(sysconfig.get_config_var("Py_GIL_DISABLED"))

class TestObject:
    """Test object with no special handling"""
    def __init__(self, value):
        self.value = value
        # List overhead: 56 bytes (empty list)
        # Integer array: 100 integers × 8 bytes = 800 bytes
        # Total object size: ~872 bytes (56 + 800 + object overhead + value attr)
        self.data = [i for i in range(100)]

class SharedObjectPool:
    """Pool of shared objects accessed by multiple threads"""
    def __init__(self, size):
        self.objects = [TestObject(i) for i in range(size)]
        self.refs = [None] * size  # Shared reference array
        self.lock = threading.Lock()

def thread_worker(iterations, shared_pool, results, index):
    """Worker function that exercises shared object churn patterns"""
    pool_size = len(shared_pool.objects)
    num_passes = iterations // pool_size
    
    start = time.perf_counter()
    
    # Pure reference counting test with shared objects
    for _ in range(num_passes):
        for i in range(pool_size):
            with shared_pool.lock:
                shared_pool.refs[i] = shared_pool.objects[i]  # Cross-thread INCREF
                shared_pool.refs[i] = None                    # Cross-thread DECREF
            
    duration = time.perf_counter() - start
    results[index] = duration

def run_threaded_test(num_threads, iterations_per_thread, pool_size):
    """Run reference counting operations across threads"""
    threads = []
    results = [0] * num_threads
    shared_pool = SharedObjectPool(pool_size)
    
    start = time.perf_counter()
    
    for i in range(num_threads):
        t = threading.Thread(
            target=thread_worker,
            args=(iterations_per_thread, shared_pool, results, i)
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
    pool_size = 100  # Same as local test for comparison
    
    metadata = {
        "test_name": "object_churn_shared_scaling",
        "test_type": "object_churn",
        "description": "Measures cross-thread object churn overhead scaling",
        "timestamp": datetime.now().isoformat(),
        "free_threading": is_free_threading_enabled(),
        "python_version": sys.version,
        "control_vars": {
            "base_iterations": base_iterations,
            "object_pool_size": pool_size,
            "object_size": "~872 bytes",
            "churn_type": "shared",
            "shared_resources": ["object_pool", "refs_array", "lock"]
        }
    }
    
    # Baseline measurement (single thread)
    results = [0]
    shared_pool = SharedObjectPool(pool_size)
    thread_worker(base_iterations, shared_pool, results, 0)
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
    thread_counts = [1, 2, 4, 8, 16, 32]
    
    for num_threads in thread_counts:
        iterations_per_thread = base_iterations // num_threads
        duration, thread_times = run_threaded_test(
            num_threads, 
            iterations_per_thread,
            pool_size
        )
        
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
            "ops_per_sec": round(refs_per_sec, 2),
            "ops_per_thread": round(refs_per_sec / num_threads, 2),
            "total_ops": total_ref_ops,
            "contention_factor": baseline_ops_per_sec / (refs_per_sec / num_threads),
            "lock_overhead_ratio": duration / baseline_duration
        }
        
        results["scaling_tests"].append(test_result)
    
    print(json.dumps(results))
    return 0

if __name__ == "__main__":
    sys.exit(main())