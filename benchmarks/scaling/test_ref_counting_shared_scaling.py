"""
Thread scaling test for cross-thread reference counting.
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
    
    start = time.time()
    
    for i in range(num_threads):
        t = threading.Thread(
            target=thread_worker,
            args=(iterations_per_thread, object_pool, results, i)
        )
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
        
    duration = time.time() - start
    return duration, sum(results)

def main():
    base_iterations = 1_000_000
    pool_size = 10_000
    
    metadata = {
        "test_name": "ref_counting_shared_scaling",
        "timestamp": datetime.now().isoformat(),
        "free_threading": is_free_threading_enabled(),
        "python_version": sys.version,
        "base_iterations": base_iterations,
        "pool_size": pool_size,
        "object_attributes": ["value", "data", "text"],
        "ref_counting_type": "shared"
    }
    
    results = {
        "metadata": metadata,
        "baseline": {},
        "scaling_tests": []
    }
    
    # Baseline measurement
    object_pool = SharedObjectPool(pool_size)
    start = time.time()
    baseline_result = object_intensive_shared(base_iterations, object_pool)
    baseline_duration = time.time() - start
    
    results["baseline"] = {
        "duration": baseline_duration,
        "refs_per_sec": base_iterations/baseline_duration,
        "result": baseline_result
    }
    
    # Scaling tests
    for num_threads in [1, 2, 4, 8, 16, 32]:
        iterations_per_thread = base_iterations // num_threads
        duration, result = run_threaded_test(
            num_threads, 
            iterations_per_thread,
            pool_size
        )
        
        speedup = baseline_duration / duration
        refs_per_sec = (iterations_per_thread * num_threads) / duration
        
        test_result = {
            "threads": num_threads,
            "duration": duration,
            "speedup": speedup,
            "ops_per_sec": refs_per_sec,
            "iterations_per_thread": iterations_per_thread,
            "total_refs": iterations_per_thread * num_threads,
            "result": result,
            "refs_per_object": (iterations_per_thread * num_threads) / pool_size
        }
        
        results["scaling_tests"].append(test_result)
    
    print(json.dumps(results))
    return 0

if __name__ == "__main__":
    sys.exit(main()) 