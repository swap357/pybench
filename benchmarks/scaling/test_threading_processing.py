"""
RL Benchmark - multi-threaded vs multi-process scaling test
Measures CPU-bound RL environment step simulation scaling across threads and processes.
"""
import time
import sys
import json
import threading
import multiprocessing
import sysconfig
from datetime import datetime
from typing import List, Dict, Any

def is_free_threading_enabled() -> bool:
    """Check if Python was built with free threading enabled"""
    return bool(sysconfig.get_config_var("Py_GIL_DISABLED"))

def rl_env_step(num_steps: int = 10_000) -> float:
    """
    Pure CPU-bound RL environment step simulation.
    Uses only basic arithmetic operations to avoid GIL release points.
    """
    state = 0
    total_reward = 0.0
    
    for _ in range(num_steps):
        # Simple integer arithmetic
        action = (state % 6)  # Deterministic action in [0, 5]
        state = (state + action * 13) % 999983  # Large prime for mixing
        
        # Basic floating point ops
        total_reward += (state + action) * 0.01
        
    return total_reward

def thread_worker(iterations: int, results: List[float], index: int) -> None:
    """Thread worker that runs pure CPU-bound operations"""
    start = time.perf_counter()
    
    for _ in range(iterations):
        rl_env_step()
        
    duration = time.perf_counter() - start
    results[index] = duration

def process_worker(iterations: int, results: Any, index: int) -> None:
    """Process worker that runs pure CPU-bound operations"""
    start = time.perf_counter()
    
    for _ in range(iterations):
        rl_env_step()
        
    duration = time.perf_counter() - start
    results[index] = duration

def run_threaded_test(num_threads: int, iterations_per_thread: int) -> tuple[float, List[float]]:
    """Run CPU-bound operations across threads"""
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

def run_process_test(num_processes: int, iterations_per_process: int) -> tuple[float, List[float]]:
    """Run CPU-bound operations across processes"""
    processes = []
    manager = multiprocessing.Manager()
    results = manager.list([0] * num_processes)
    
    start = time.perf_counter()
    
    for i in range(num_processes):
        p = multiprocessing.Process(
            target=process_worker,
            args=(iterations_per_process, results, i)
        )
        processes.append(p)
        p.start()
    
    for p in processes:
        p.join()
        
    duration = time.perf_counter() - start
    return duration, list(results)

def main():
    """Run scaling benchmark suite with JSON output"""
    # Test configuration
    base_iterations = 10_000
    
    metadata = {
        "test_name": "rl_env_step_scaling",
        "test_type": "cpu_bound",
        "description": "Measures RL environment step simulation scaling across threads and processes",
        "timestamp": datetime.now().isoformat(),
        "free_threading": is_free_threading_enabled(),
        "python_version": sys.version,
        "control_vars": {
            "base_iterations": base_iterations,
            "env_steps": 10_000,
            "computation_type": "arithmetic_only"
        }
    }
    
    # Baseline measurement (single thread)
    results = [0]
    thread_worker(base_iterations, results, 0)
    baseline_duration = results[0]
    baseline_steps_per_sec = (base_iterations) / baseline_duration
    
    results = {
        "metadata": metadata,
        "baseline": {
            "duration": round(baseline_duration, 4),
            "steps_per_sec": round(baseline_steps_per_sec, 2),
            "total_steps": base_iterations
        },
        "scaling_tests": []
    }
    
    # Scaling tests
    worker_counts = [1, 2, 4, 8, 16, 32, 48, 64, 96]
    
    for n_workers in worker_counts:
        iterations_per_worker = base_iterations // n_workers
        
        # Thread benchmark
        thread_duration, thread_worker_times = run_threaded_test(n_workers, iterations_per_worker)
        total_steps = iterations_per_worker * n_workers
        thread_steps_per_sec = total_steps / thread_duration
        thread_speedup = baseline_duration / thread_duration
        thread_efficiency = thread_speedup / n_workers
        
        # Process benchmark
        process_duration, process_worker_times = run_process_test(n_workers, iterations_per_worker)
        process_steps_per_sec = total_steps / process_duration
        process_speedup = baseline_duration / process_duration
        process_efficiency = process_speedup / n_workers
        
        test_result = {
            "threads": n_workers,
            "thread_results": {
                "duration": round(thread_duration, 4),
                "worker_times": [round(t, 4) for t in thread_worker_times],
                "speedup": round(thread_speedup, 4),
                "efficiency": round(thread_efficiency, 4),
                "steps_per_sec": round(thread_steps_per_sec, 2),
                "steps_per_worker": round(thread_steps_per_sec / n_workers, 2)
            },
            "process_results": {
                "duration": round(process_duration, 4),
                "worker_times": [round(t, 4) for t in process_worker_times],
                "speedup": round(process_speedup, 4),
                "efficiency": round(process_efficiency, 4),
                "steps_per_sec": round(process_steps_per_sec, 2),
                "steps_per_worker": round(process_steps_per_sec / n_workers, 2)
            },
            "total_steps": total_steps
        }
        
        results["scaling_tests"].append(test_result)
    
    print(json.dumps(results))
    return 0

if __name__ == "__main__":
    sys.exit(main())