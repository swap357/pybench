"""Multiprocessing scaling test for NumPy column computations."""
import time
import sys
import multiprocessing as mp
import sysconfig
import json
from datetime import datetime

try:
    import numpy as np
except ImportError:
    print(json.dumps({
        "metadata": {
            "test_name": "np_column_compute_mp",
            "error": "NumPy not installed"
        },
        "baseline": {},
        "scaling_tests": []
    }))
    sys.exit(1)

def is_free_threading_enabled():
    """Check if running on free-threading Python build"""
    return bool(sysconfig.get_config_var("Py_GIL_DISABLED"))

def normalize_features(features):
    """Normalize features (standardization)"""
    mean = np.mean(features, axis=0)
    std = np.std(features, axis=0)
    std[std == 0] = 1
    return (features - mean) / std

def process_batch(data_batch):
    """Process a batch of data with typical ML operations"""
    features = []
    for col in range(data_batch.shape[1]):
        mean = np.mean(data_batch[:, col])
        std = np.std(data_batch[:, col])
        skew = np.mean(((data_batch[:, col] - mean) / std) ** 3) if std > 0 else 0
        
        window_size = 3
        rolling_mean = np.convolve(data_batch[:, col], 
                                 np.ones(window_size)/window_size, 
                                 mode='valid')
        
        poly_features = np.column_stack([
            data_batch[:, col],
            data_batch[:, col] ** 2,
            np.log1p(np.abs(data_batch[:, col]))
        ])
        
        features.append(np.concatenate([
            [mean, std, skew],
            rolling_mean[:3],
            poly_features.mean(axis=0)
        ]))
    
    features = np.array(features)
    normalized = normalize_features(features)
    return float(np.sum(normalized ** 2))

def worker_process(data_batch, result_queue):
    """Worker process function"""
    try:
        result = process_batch(data_batch)
        result_queue.put(result)
    except Exception as e:
        result_queue.put(f"Error in worker: {str(e)}")

def run_mp_test(num_processes, total_samples, num_features):
    """Run ML preprocessing across processes"""
    try:
        # Generate synthetic dataset
        data = np.random.randn(total_samples, num_features)
        samples_per_process = total_samples // num_processes
        
        # Create process pool and result queue
        result_queue = mp.Queue()
        processes = []
        
        start = time.time()
        
        # Start processes
        for i in range(num_processes):
            start_idx = i * samples_per_process
            end_idx = start_idx + samples_per_process
            batch = data[start_idx:end_idx].copy()
            
            p = mp.Process(
                target=worker_process,
                args=(batch, result_queue)
            )
            processes.append(p)
            p.start()
        
        # Collect results
        results = []
        for _ in range(num_processes):
            result = result_queue.get()
            if isinstance(result, str):
                raise RuntimeError(result)
            results.append(result)
        
        # Wait for completion
        for p in processes:
            p.join()
            
        duration = time.time() - start
        return duration, sum(results)
        
    except Exception as e:
        # Clean up processes
        for p in processes:
            if p.is_alive():
                p.terminate()
        raise e

def main():
    if mp.get_start_method() != 'spawn':
        mp.set_start_method('spawn', force=True)
        
    # Test configuration - control variables
    total_samples = 100_000
    num_features = 10
    
    # Test metadata
    metadata = {
        "test_name": "np_column_compute_mp",
        "test_type": "numpy_compute",
        "description": "Measures process scaling of ML feature preprocessing",
        "timestamp": datetime.now().isoformat(),
        "free_threading": is_free_threading_enabled(),
        "python_version": sys.version,
        
        # Control variables
        "control_vars": {
            "total_samples": total_samples,
            "num_features": num_features,
            "operations": [
                "mean", "std", "skew", "rolling_mean",
                "polynomial_features", "normalization"
            ],
            "process_method": "spawn",
            "cpu_count": mp.cpu_count()
        }
    }
    
    # Baseline measurement
    data = np.random.randn(total_samples, num_features)
    start = time.time()
    baseline_result = process_batch(data)
    baseline_duration = time.time() - start
    
    baseline_samples_per_sec = total_samples / baseline_duration
    
    results = {
        "metadata": metadata,
        "baseline": {
            "duration": baseline_duration,
            "samples_per_sec": baseline_samples_per_sec,
            "result": float(baseline_result),
            "total_samples": total_samples
        },
        "scaling_tests": []
    }
    
    # Scaling tests
    max_processes = min(32, mp.cpu_count())
    process_counts = [n for n in [1, 2, 4, 8, 16, 32] if n <= max_processes]
    
    for num_processes in process_counts:
        samples_per_process = total_samples // num_processes
        duration, result = run_mp_test(num_processes, total_samples, num_features)
        
        # Calculate dependent variables
        speedup = baseline_duration / duration
        samples_per_sec = total_samples / duration
        samples_per_process_sec = samples_per_sec / num_processes
        efficiency = speedup / num_processes
        
        test_result = {
            # Independent variables
            "threads": num_processes,  # Keep consistent with thread tests
            "samples_per_process": samples_per_process,
            
            # Primary dependent variables
            "duration": duration,
            "speedup": speedup,
            
            # Throughput metrics
            "samples_per_sec": samples_per_sec,
            "samples_per_process_sec": samples_per_process_sec,
            "efficiency": efficiency,
            
            # Control/validation variables
            "total_samples": total_samples,
            "result": float(result),
            
            # Additional metrics
            "theoretical_max_samples": baseline_samples_per_sec * num_processes,
            "scaling_efficiency": samples_per_process_sec / baseline_samples_per_sec,
            "process_to_cpu_ratio": num_processes / metadata["control_vars"]["cpu_count"],
            "memory_overhead_GB": (total_samples * num_features * 8 * num_processes) / (1024**3)
        }
        
        results["scaling_tests"].append(test_result)
    
    # Output JSON to stdout
    print(json.dumps(results))
    return 0

if __name__ == "__main__":
    mp.freeze_support()
    sys.exit(main())