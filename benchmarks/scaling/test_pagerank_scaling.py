"""
RL Benchmark - PageRank scaling test
Measures CPU-bound PageRank computation scaling across threads and processes.
"""
import time
import sys
import json
import numpy as np
import threading
import multiprocessing
import concurrent.futures
import sysconfig
from datetime import datetime
from typing import List, Dict, Any, Tuple

# PageRank damping factor
DAMPING = 0.85

def is_free_threading_enabled() -> bool:
    """Check if Python is running with free threading (GIL disabled)"""
    # Use runtime check for GIL status
    try:
        return not sys._is_gil_enabled()  # Returns True if GIL is disabled
    except AttributeError:
        return False  # If _is_gil_enabled doesn't exist, GIL is enabled

def generate_test_matrix(size: int = 1000) -> np.ndarray:
    """Generate a sparse test matrix for PageRank"""
    # Create sparse matrix with ~10 links per page
    matrix = np.zeros((size, size))
    for i in range(size):
        # Add random outgoing links
        n_links = np.random.randint(5, 15)
        targets = np.random.choice(size, n_links, replace=False)
        matrix[i, targets] = 1
    return matrix

def pagerank_single(matrix: np.ndarray, num_iterations: int = 50) -> np.ndarray:
    """Single-threaded PageRank implementation"""
    size = matrix.shape[0]
    scores = np.ones(size) / size
    
    for _ in range(num_iterations):
        new_scores = np.zeros(size)
        for i in range(size):
            incoming = np.where(matrix[:, i])[0]
            for j in incoming:
                new_scores[i] += scores[j] / np.sum(matrix[j])
        scores = (1 - DAMPING) / size + DAMPING * new_scores
    
    return scores

def _thread_worker(
    matrix: np.ndarray,
    scores: np.ndarray,
    new_scores: np.ndarray,
    start_idx: int,
    end_idx: int,
    lock: threading.Lock,
) -> None:
    """Thread worker for parallel PageRank computation"""
    size = matrix.shape[0]
    local_scores = np.zeros(size)

    for i in range(start_idx, end_idx):
        incoming = np.where(matrix[:, i])[0]
        for j in incoming:
            local_scores[i] += scores[j] / np.sum(matrix[j])

    with lock:
        new_scores += local_scores

def pagerank_threaded(matrix: np.ndarray, num_threads: int, num_iterations: int = 50) -> np.ndarray:
    """Multi-threaded PageRank implementation"""
    size = matrix.shape[0]
    scores = np.ones(size) / size
    
    # Compute chunk sizes for parallel processing
    chunk_size = size // num_threads
    chunks = [(i, min(i + chunk_size, size)) for i in range(0, size, chunk_size)]
    
    for _ in range(num_iterations):
        new_scores = np.zeros(size)
        lock = threading.Lock()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = list(executor.map(
                lambda args: _thread_worker(*args),
                [
                    (matrix, scores, new_scores, start_idx, end_idx, lock)
                    for start_idx, end_idx in chunks
                ],
            ))
            
        scores = (1 - DAMPING) / size + DAMPING * new_scores
    
    return scores

def _process_chunk(matrix: np.ndarray, scores: np.ndarray, start_idx: int, end_idx: int) -> np.ndarray:
    """Process worker for parallel PageRank computation"""
    size = matrix.shape[0]
    local_scores = np.zeros(size)

    for i in range(start_idx, end_idx):
        incoming = np.where(matrix[:, i])[0]
        for j in incoming:
            local_scores[i] += scores[j] / np.sum(matrix[j])

    return local_scores

def pagerank_multiprocess(matrix: np.ndarray, num_processes: int, num_iterations: int = 50) -> np.ndarray:
    """Multi-process PageRank implementation"""
    size = matrix.shape[0]
    scores = np.ones(size) / size
    
    # Compute chunk sizes for parallel processing
    chunk_size = size // num_processes
    chunks = [
        (matrix, scores, i, min(i + chunk_size, size))
        for i in range(0, size, chunk_size)
    ]
    
    for _ in range(num_iterations):
        with multiprocessing.Pool(processes=num_processes) as pool:
            chunk_results = pool.starmap(_process_chunk, chunks)
            new_scores = sum(chunk_results)
            scores = (1 - DAMPING) / size + DAMPING * new_scores
    
    return scores

def run_threaded_test(matrix: np.ndarray, num_threads: int) -> Tuple[float, List[float]]:
    """Run threaded PageRank benchmark"""
    start = time.perf_counter()
    pagerank_threaded(matrix, num_threads)
    duration = time.perf_counter() - start
    return duration, [duration]  # Single duration since we can't easily measure per-thread times

def run_process_test(matrix: np.ndarray, num_processes: int) -> Tuple[float, List[float]]:
    """Run multi-process PageRank benchmark"""
    start = time.perf_counter()
    pagerank_multiprocess(matrix, num_processes)
    duration = time.perf_counter() - start
    return duration, [duration]  # Single duration since we can't easily measure per-process times

def main():
    """Run PageRank scaling benchmark suite with JSON output"""
    # Test configuration
    matrix_size = 1000
    num_iterations = 50
    test_matrix = generate_test_matrix(matrix_size)
    
    metadata = {
        "test_name": "pagerank_scaling",
        "test_type": "cpu_bound",
        "description": "Measures PageRank computation scaling across threads and processes",
        "timestamp": datetime.now().isoformat(),
        "free_threading": is_free_threading_enabled(),
        "python_version": sys.version,
        "control_vars": {
            "matrix_size": matrix_size,
            "num_iterations": num_iterations,
            "damping_factor": DAMPING
        }
    }
    
    # Baseline measurement (single thread)
    start = time.perf_counter()
    pagerank_single(test_matrix)
    baseline_duration = time.perf_counter() - start
    
    results = {
        "metadata": metadata,
        "baseline": {
            "duration": round(baseline_duration, 4),
            "graph_traversals_per_sec": round(num_iterations / baseline_duration, 2),  # One traversal per iteration
            "matrix_size": matrix_size,
            "total_steps": num_iterations
        },
        "scaling_tests": []
    }
    
    # Scaling tests
    worker_counts = [2, 4, 8, 16, 32, 48, 64, 96]
    
    for n_workers in worker_counts:
        # Thread benchmark
        thread_duration, thread_worker_times = run_threaded_test(test_matrix, n_workers)
        thread_speedup = baseline_duration / thread_duration
        thread_efficiency = thread_speedup / n_workers
        
        # Process benchmark
        process_duration, process_worker_times = run_process_test(test_matrix, n_workers)
        process_speedup = baseline_duration / process_duration
        process_efficiency = process_speedup / n_workers
        
        test_result = {
            "threads": n_workers,
            "duration": round(thread_duration, 4),
            "speedup": round(thread_speedup, 4),
            "thread_results": {
                "duration": round(thread_duration, 4),
                "speedup": round(thread_speedup, 4),
                "efficiency": round(thread_efficiency, 4),
                "graph_traversals_per_sec": round(num_iterations / thread_duration, 2)
            },
            "process_results": {
                "duration": round(process_duration, 4),
                "speedup": round(process_speedup, 4),
                "efficiency": round(process_efficiency, 4),
                "graph_traversals_per_sec": round(num_iterations / process_duration, 2)
            }
        }
        
        results["scaling_tests"].append(test_result)
    
    print(json.dumps(results))
    return 0

if __name__ == "__main__":
    sys.exit(main()) 