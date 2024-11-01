"""
Thread scaling test for local reference counting.
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

def object_intensive_local(iterations):
    """Create and destroy objects in thread-local scope"""
    result = 0
    for i in range(iterations):
        obj = TestObject(i)
        result += obj.value
    return result

def thread_worker(iterations, results, index):
    """Worker function for threads - local objects only"""
    result = object_intensive_local(iterations)
    results[index] = result

def run_threaded_test(num_threads, iterations_per_thread):
    """Run object operations across threads"""
    threads = []
    results = [0] * num_threads
    
    start = time.time()
    
    for i in range(num_threads):
        t = threading.Thread(
            target=thread_worker,
            args=(iterations_per_thread, results, i)
        )
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
        
    duration = time.time() - start
    return duration, sum(results)

def main():
    base_iterations = 1_000_000
    
    metadata = {
        "test_name": "ref_counting_local_scaling",
        "timestamp": datetime.now().isoformat(),
        "free_threading": is_free_threading_enabled(),
        "python_version": sys.version,
        "base_iterations": base_iterations,
        "object_attributes": ["value", "data", "text"],
        "ref_counting_type": "local"
    }
    
    results = {
        "metadata": metadata,
        "baseline": {},
        "scaling_tests": []
    }
    
    # Baseline measurement
    start = time.time()
    baseline_result = object_intensive_local(base_iterations)
    baseline_duration = time.time() - start
    
    results["baseline"] = {
        "duration": baseline_duration,
        "objects_per_sec": base_iterations/baseline_duration,
        "result": baseline_result
    }
    
    # Scaling tests
    for num_threads in [1, 2, 4, 8, 16, 32]:
        iterations_per_thread = base_iterations // num_threads
        duration, result = run_threaded_test(num_threads, iterations_per_thread)
        
        speedup = baseline_duration / duration
        objects_per_sec = (iterations_per_thread * num_threads) / duration
        
        test_result = {
            "threads": num_threads,
            "duration": duration,
            "speedup": speedup,
            "ops_per_sec": objects_per_sec,
            "iterations_per_thread": iterations_per_thread,
            "total_objects": iterations_per_thread * num_threads,
            "result": result
        }
        
        results["scaling_tests"].append(test_result)
    
    print(json.dumps(results))
    return 0

if __name__ == "__main__":
    sys.exit(main()) 