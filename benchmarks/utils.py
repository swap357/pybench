"""Utility functions for benchmarks."""
import os
import psutil

def get_available_cores():
    """Get number of available CPU cores respecting taskset and affinity"""
    try:
        process = psutil.Process()
        affinity = process.cpu_affinity()
        available_cores = len(affinity)
    except (AttributeError, psutil.Error):
        # If we can't get affinity, check CPU_SET environment variable
        cpu_set = os.environ.get('CPU_SET', '')
        if cpu_set:
            # Parse CPU range like "0-3" or "0,1,2,3"
            cores = set()
            for part in cpu_set.split(','):
                if '-' in part:
                    start, end = map(int, part.split('-'))
                    cores.update(range(start, end + 1))
                else:
                    cores.add(int(part))
            available_cores = len(cores)
        else:
            # Fallback to all cores
            available_cores = os.cpu_count()
    
    # Apply BENCHMARK_CPU_CORES limit if specified
    cpu_cores = os.environ.get('BENCHMARK_CPU_CORES', 'all')
    if cpu_cores != 'all':
        try:
            available_cores = min(int(cpu_cores), available_cores)
        except ValueError:
            pass
            
    return available_cores

def get_total_threads():
    """Calculate total threads based on available cores and thread limit"""
    num_cores = get_available_cores()
    thread_limit = int(os.environ.get('BENCHMARK_THREAD_LIMIT', '1'))
    return num_cores * thread_limit if thread_limit > 0 else num_cores 