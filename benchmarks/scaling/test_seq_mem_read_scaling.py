"""
Thread scaling test for memory-bound operations.
Measures memory bandwidth using data accounting.
"""
import time
import sys
import threading
import numpy as np
from datetime import datetime
import json

def memory_intensive(src, dst, iterations):
    """Memory-intensive operation with explicit data dependency"""
    # Use np.copyto for guaranteed memory movement
    tmp = np.empty_like(dst)
    for _ in range(iterations):
        np.copyto(tmp, src)  # Force actual copy
        np.copyto(dst, tmp)  # Maintain data dependency
    return dst.sum()  # Prevent dead code elimination

def thread_worker(src, dst, start_idx, end_idx, iterations, results, index):
    """Worker function with proper memory access"""
    # Create views to avoid temporary copies
    src_view = src[start_idx:end_idx]
    dst_view = dst[start_idx:end_idx]
    result = memory_intensive(src_view, dst_view, iterations)
    results[index] = result

def run_threaded_test(num_threads, src, dst, iterations):
    """Run test with proper work distribution"""
    threads = []
    results = [0] * num_threads
    chunk_size = len(src) // num_threads
    
    start = time.perf_counter()
    
    for i in range(num_threads):
        start_idx = i * chunk_size
        end_idx = (i+1) * chunk_size if i < num_threads-1 else len(src)
        t = threading.Thread(
            target=thread_worker,
            args=(src, dst, start_idx, end_idx, iterations, results, i)
        )
        threads.append(t)
        t.start()
    
    for t in threads:
        t.join()
        
    duration = time.perf_counter() - start
    return duration, sum(results)

def main():
    # Configuration matching system capabilities
    array_size = 2 * 1024**3 // 8  # 2GB per array (exceeds cache)
    base_iterations = 5  # Reduced to match realistic execution time
    
    print(f"Initializing test arrays...", file=sys.stderr)
    
    # Create aligned arrays to maximize memory throughput
    src = np.ones(array_size, dtype=np.float64)
    dst = np.empty_like(src)
    
    # Calculate PROPER data movement accounting:
    # 2 copies per iteration (src->tmp + tmp->dst) × 8 bytes × iterations
    bytes_per_iter = array_size * 8 * 2 * 2  # 2 copies × 2 arrays (read+write)
    total_bytes = bytes_per_iter * base_iterations
    
    metadata = {
        "test_name": "memory_bandwidth_scaling_fixed",
        "array_size_gb": array_size * 8 / 1024**3,
        "total_data_moved_tb": total_bytes / 1024**4,
        "iterations": base_iterations,
        "rationale": "Proper accounting: 2 copies per iteration × 8 bytes × read/write"
    }
    
    # Baseline measurement
    print("Running baseline...", file=sys.stderr)
    start = time.perf_counter()
    baseline_result = memory_intensive(src, dst, base_iterations)
    baseline_duration = time.perf_counter() - start
    baseline_bw = total_bytes / baseline_duration / 1024**3  # GB/s
    
    results = {
        "metadata": metadata,
        "baseline": {
            "duration": baseline_duration,
            "bandwidth_gb_s": baseline_bw,
        },
        "scaling_tests": []
    }
    
    # Thread scaling tests
    thread_counts = [2, 4, 8, 16, 32, 48, 64, 96, 112, 128]
    
    print("\nRunning valid scaling tests...", file=sys.stderr)
    for num_threads in thread_counts:
        print(f"Testing {num_threads} threads...", file=sys.stderr)
        
        best_bw = 0
        best_duration = float('inf')
        for _ in range(3):
            duration, _ = run_threaded_test(num_threads, src, dst, base_iterations)
            thread_bw = total_bytes / duration / 1024**3
            if thread_bw > best_bw:
                best_bw = thread_bw
                best_duration = duration
        
        speedup = baseline_duration / best_duration
        
        results["scaling_tests"].append({
            "threads": num_threads,
            "bandwidth_gb_s": best_bw,
            "duration": best_duration,
            "speedup": speedup
        })
        print(f"Bandwidth: {best_bw:.2f} GB/s (duration: {best_duration:.3f}s, speedup: {speedup:.2f}x)",
              file=sys.stderr)
    
    print(json.dumps(results, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
