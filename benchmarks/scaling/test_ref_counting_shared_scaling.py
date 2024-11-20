"""
Thread scaling test for cross-thread reference counting.
Measures scaling of object reference operations across threads.
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

class TestObject:
    """Test object with some attributes to make it realistic"""
    def __init__(self, value):
        self.value = value
        self.data = [1, 2, 3]
        self.text = "test" * 10

class SharedObjectPool:
    """Pool of shared objects accessed by multiple threads"""
    def __init__(self, size):
        self.objects = [TestObject(i) for i in range(size)]
        self.lock = threading.Lock()
        
    def get_object(self, index):
        """Get object from pool - creates cross-thread reference"""
        with self.lock:
            return self.objects[index % len(self.objects)]

def object_intensive_shared(iterations, object_pool):
    """Work with shared objects across threads"""
    result = 0
    for i in range(iterations):
        obj = object_pool.get_object(i)
        result += obj.value
    return result

def thread_worker(iterations, object_pool, results, index):
    """Worker function for threads - using shared objects"""
    result = object_intensive_shared(iterations, object_pool)
    results[index] = result

def run_threaded_test(num_threads, iterations_per_thread, pool_size):
    """Run object operations across threads"""
    threads = []
    results = [0] * num_threads
    object_pool = SharedObjectPool(pool_size)
    
    start = time.perf_counter()
    
    for i in range(num_threads):
        t = threading.Thread(
            target=thread_worker,
            args=(iterations_per_thread, object_pool, results, i)
        )
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
        
    duration = time.perf_counter() - start
    return duration, sum(results)

def main():
    # Test configuration - control variables
    base_iterations = 1_000_000
    pool_size = 10_000
    
    # Test metadata
    metadata = {
        "test_name": "ref_counting_shared_scaling",
        "test_type": "ref_counting",
        "description": "Measures scaling of object reference operations across threads",
        "timestamp": datetime.now().isoformat(),
        "free_threading": is_free_threading_enabled(),
        "python_version": sys.version,
        
        # Control variables
        "control_vars": {
            "base_iterations": base_iterations,
            "pool_size": pool_size,
            "object_type": "TestObject",
            "object_attributes": ["value", "data", "text"],
            "ref_counting_type": "shared",
            "shared_resources": ["object_pool", "lock"]
        }
    }
    
    # Baseline measurement
    object_pool = SharedObjectPool(pool_size)
    start = time.perf_counter()
    baseline_result = object_intensive_shared(base_iterations, object_pool)
    baseline_duration = time.perf_counter() - start
    
    baseline_refs_per_sec = base_iterations / baseline_duration
    
    results = {
        "metadata": metadata,
        "baseline": {
            "duration": round(baseline_duration, 4),
            "refs_per_sec": baseline_refs_per_sec,
            "result": baseline_result,
            "total_refs": base_iterations,
            "refs_per_object": base_iterations / pool_size
        },
        "scaling_tests": []
    }
    
    # Scaling tests
    thread_counts = [1, 2, 4, 8, 16, 32]  # Independent variable
    
    for num_threads in thread_counts:
        iterations_per_thread = base_iterations // num_threads
        duration, result = run_threaded_test(
            num_threads, 
            iterations_per_thread,
            pool_size
        )
        
        # Calculate dependent variables
        speedup = baseline_duration / duration
        total_refs = iterations_per_thread * num_threads
        refs_per_sec = total_refs / duration
        refs_per_thread = refs_per_sec / num_threads
        efficiency = speedup / num_threads
        
        test_result = {
            # Independent variables
            "threads": num_threads,
            "iterations_per_thread": iterations_per_thread,
            
            # Primary dependent variables
            "duration": round(duration, 4),
            "speedup": speedup,
            
            # Reference counting metrics
            "refs_per_sec": refs_per_sec,
            "refs_per_thread": refs_per_thread,
            "efficiency": efficiency,
            "refs_per_object": total_refs / pool_size,
            
            # Control/validation variables
            "total_refs": total_refs,
            "result": result,
            
            # Additional metrics
            "theoretical_max_refs": baseline_refs_per_sec * num_threads,
            "scaling_efficiency": refs_per_thread / baseline_refs_per_sec,
            "contention_factor": baseline_refs_per_sec / refs_per_thread,
            "memory_sharing_ratio": pool_size / (pool_size * num_threads),
            "ref_count_operations": total_refs * 2  # Increment + decrement
        }
        
        results["scaling_tests"].append(test_result)
    
    # Output JSON to stdout
    print(json.dumps(results))
    return 0

if __name__ == "__main__":
    sys.exit(main())