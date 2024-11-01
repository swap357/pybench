"""Thread scaling test for NumPy column computations."""
import time
import sys
import threading
import sysconfig
import json
from datetime import datetime

try:
    import numpy as np
except ImportError:
    print(json.dumps({
        "metadata": {
            "test_name": "np_column_compute_thread",
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
    try:
        mean = np.mean(features, axis=0)
        std = np.std(features, axis=0)
        std[std == 0] = 1
        return (features - mean) / std
    except Exception as e:
        print(json.dumps({
            "metadata": {
                "test_name": "np_column_compute_thread",
                "error": f"Normalization failed: {str(e)}"
            },
            "baseline": {},
            "scaling_tests": []
        }))
        sys.exit(1)

def process_batch(data_batch, results, index):
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
        results[index] = float(np.sum(normalized ** 2))
    except Exception as e:
        print(json.dumps({
            "metadata": {
                "test_name": "np_column_compute_thread",
                "error": f"Processing failed: {str(e)}"
            },
            "baseline": {},
            "scaling_tests": []
        }))
        sys.exit(1)

def run_threaded_test(num_threads, total_samples, num_features):
    """Run ML preprocessing across threads"""
    try:
        threads = []
        results = [0] * num_threads
        
        data = np.random.randn(total_samples, num_features)
        samples_per_thread = total_samples // num_threads
        
        start = time.time()
        
        for i in range(num_threads):
            start_idx = i * samples_per_thread
            end_idx = start_idx + samples_per_thread
            batch = data[start_idx:end_idx].copy()  # Create copy for thread safety
            
            t = threading.Thread(
                target=process_batch,
                args=(batch, results, i)
            )
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
            
        duration = time.time() - start
        return duration, sum(results)
    except Exception as e:
        print(json.dumps({
            "metadata": {
                "test_name": "np_column_compute_thread",
                "error": f"Thread test failed: {str(e)}"
            },
            "baseline": {},
            "scaling_tests": []
        }))
        sys.exit(1)

def main():
    try:
        total_samples = 100_000
        num_features = 10
        
        metadata = {
            "test_name": "np_column_compute_thread",
            "timestamp": datetime.now().isoformat(),
            "free_threading": is_free_threading_enabled(),
            "python_version": sys.version,
            "total_samples": total_samples,
            "num_features": num_features
        }
        
        results = {
            "metadata": metadata,
            "baseline": {},
            "scaling_tests": []
        }
        
        # Baseline measurement
        data = np.random.randn(total_samples, num_features)
        baseline_results = [0]
        start = time.time()
        process_batch(data, baseline_results, 0)
        baseline_duration = time.time() - start
        
        results["baseline"] = {
            "duration": baseline_duration,
            "ops_per_sec": total_samples/baseline_duration,
            "result": float(baseline_results[0])  # Convert numpy types to native Python
        }
        
        # Scaling tests
        for num_threads in [1, 2, 4, 8, 16, 32]:
            duration, result = run_threaded_test(
                num_threads, 
                total_samples, 
                num_features
            )
            
            speedup = baseline_duration / duration
            samples_per_sec = total_samples / duration
            
            test_result = {
                "threads": num_threads,
                "duration": duration,
                "speedup": speedup,
                "ops_per_sec": samples_per_sec,
                "samples_per_thread": total_samples // num_threads,
                "result": float(result)  # Convert numpy types to native Python
            }
            
            results["scaling_tests"].append(test_result)
        
        print(json.dumps(results))
        return 0
        
    except Exception as e:
        print(json.dumps({
            "metadata": {
                "test_name": "np_column_compute_thread",
                "error": f"Test failed: {str(e)}"
            },
            "baseline": {},
            "scaling_tests": []
        }))
        return 1

if __name__ == "__main__":
    sys.exit(main())