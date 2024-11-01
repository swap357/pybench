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
    try:
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
    except Exception as e:
        return f"Error in process_batch: {str(e)}"

def worker_process(data_batch, result_queue):
    """Worker process function"""
    try:
        result = process_batch(data_batch)
        if isinstance(result, str):  # Error occurred
            result_queue.put(result)
        else:
            result_queue.put(float(result))
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
        
    # Test configuration
    total_samples = 100_000
    num_features = 10
    
    metadata = {
        "test_name": "np_column_compute_mp",
        "timestamp": datetime.now().isoformat(),
        "free_threading": is_free_threading_enabled(),
        "python_version": sys.version,
        "total_samples": total_samples,
        "num_features": num_features,
        "cpu_count": mp.cpu_count()
    }
    
    results = {
        "metadata": metadata,
        "baseline": {},
        "scaling_tests": []
    }
    
    try:
        # Baseline measurement (single process)
        data = np.random.randn(total_samples, num_features)
        start = time.time()
        baseline_result = process_batch(data)
        if isinstance(baseline_result, str):
            raise RuntimeError(baseline_result)
        baseline_duration = time.time() - start
        
        results["baseline"] = {
            "duration": baseline_duration,
            "ops_per_sec": total_samples/baseline_duration,
            "result": float(baseline_result)
        }
        
        # Scaling tests
        max_processes = min(32, mp.cpu_count())
        for num_processes in [n for n in [1, 2, 4, 8, 16, 32] if n <= max_processes]:
            duration, result = run_mp_test(
                num_processes, 
                total_samples, 
                num_features
            )
            
            speedup = baseline_duration / duration
            samples_per_sec = total_samples / duration
            
            test_result = {
                "threads": num_processes,  # Keep consistent with thread tests
                "duration": duration,
                "speedup": speedup,
                "ops_per_sec": samples_per_sec,
                "samples_per_process": total_samples // num_processes,
                "result": float(result),
                "process_to_cpu_ratio": num_processes / metadata["cpu_count"]
            }
            
            results["scaling_tests"].append(test_result)
        
        print(json.dumps(results))
        return 0
        
    except Exception as e:
        error_results = {
            "metadata": metadata,
            "error": str(e),
            "baseline": {},
            "scaling_tests": []
        }
        print(json.dumps(error_results))
        return 1

if __name__ == "__main__":
    mp.freeze_support()
    sys.exit(main())