"""
Thread scaling test for local reference counting.
Measures scaling of object creation/destruction in thread-local scope.
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
    # Test configuration - control variables
    base_iterations = 1_000_000
    
    # Test metadata
    metadata = {
        "test_name": "ref_counting_local_scaling",
        "test_type": "ref_counting",
        "description": "Measures scaling of object creation/destruction in thread-local scope",
        "timestamp": datetime.now().isoformat(),
        "free_threading": is_free_threading_enabled(),
        "python_version": sys.version,
        
        # Control variables
        "control_vars": {
            "base_iterations": base_iterations,
            "object_type": "TestObject",
            "object_attributes": ["value", "data", "text"],
            "ref_counting_type": "local",
            "shared_resources": "none"
        }
    }
    
    # Baseline measurement
    start = time.time()
    baseline_result = object_intensive_local(base_iterations)
    baseline_duration = time.time() - start
    
    baseline_objects_per_sec = base_iterations / baseline_duration
    
    results = {
        "metadata": metadata,
        "baseline": {
            "duration": baseline_duration,
            "objects_per_sec": baseline_objects_per_sec,
            "result": baseline_result,
            "total_objects": base_iterations
        },
        "scaling_tests": []
    }
    
    # Scaling tests
    thread_counts = [1, 2, 4, 8, 16, 32]  # Independent variable
    
    for num_threads in thread_counts:
        iterations_per_thread = base_iterations // num_threads
        duration, result = run_threaded_test(num_threads, iterations_per_thread)
        
        # Calculate dependent variables
        speedup = baseline_duration / duration
        total_objects = iterations_per_thread * num_threads
        objects_per_sec = total_objects / duration
        objects_per_thread = objects_per_sec / num_threads
        efficiency = speedup / num_threads
        
        test_result = {
            # Independent variables
            "threads": num_threads,
            "iterations_per_thread": iterations_per_thread,
            
            # Primary dependent variables
            "duration": duration,
            "speedup": speedup,
            
            # Reference counting metrics
            "objects_per_sec": objects_per_sec,
            "objects_per_thread": objects_per_thread,
            "efficiency": efficiency,
            
            # Control/validation variables
            "total_objects": total_objects,
            "result": result,
            
            # Additional metrics
            "theoretical_max_objects": baseline_objects_per_sec * num_threads,
            "scaling_efficiency": objects_per_thread / baseline_objects_per_sec,
            "memory_overhead_ratio": 1.0,  # Local objects, no sharing overhead
            "ref_count_operations": total_objects * 2  # Create + destroy
        }
        
        results["scaling_tests"].append(test_result)
    
    # Output JSON to stdout
    print(json.dumps(results))
    return 0

if __name__ == "__main__":
    sys.exit(main())