from typing import List, Dict, Optional
from benchmarks.environment import PythonEnvironment
from benchmarks.base import BenchmarkResult
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import (
    Progress, 
    SpinnerColumn, 
    TextColumn, 
    BarColumn,
    TimeRemainingColumn
)
from rich.panel import Panel
from rich.text import Text
import statistics
from dataclasses import dataclass
import psutil
import tracemalloc
import json
import argparse

@dataclass
class SystemMetrics:
    cpu_count: int
    memory_total: int
    os_info: str
    cpu_freq: Dict
    load_avg: tuple

@dataclass
class StatisticalResult:
    mean: float
    median: float
    stddev: float
    min: float
    max: float
    iterations: List[float]

@dataclass
class ProfilingData:
    calls: int
    total_time: float
    cumulative_time: float
    per_call: float
    callers: List[str]
    callees: List[str]

@dataclass
class MemorySnapshot:
    peak_usage: int
    allocated_blocks: int
    size_by_line: Dict[str, int]
    peak_frame: Optional[tracemalloc.Snapshot] = None

class BenchmarkRunner:
    def __init__(self, iterations: int = 5, profile: bool = True):
        self.environments = [
            PythonEnvironment("3.12.7"),
            PythonEnvironment("3.13.0"),
            PythonEnvironment("3.13.0t")
        ]
        self.benchmark_dir = Path("benchmarks/tests")
        self.baseline_version = "3.12.7"
        self.console = Console()
        self.iterations = iterations
        self.profile = profile
        self.system_info = self._collect_system_info()
        
    def _collect_system_info(self) -> SystemMetrics:
        """Collect system-wide metrics."""
        return SystemMetrics(
            cpu_count=psutil.cpu_count(logical=True),
            memory_total=psutil.virtual_memory().total,
            os_info=f"{os.uname().sysname} {os.uname().release}",
            cpu_freq=dict(psutil.cpu_freq()._asdict()),
            load_avg=os.getloadavg()
        )

    def discover_benchmarks(self) -> List[str]:
        """Discover all benchmark modules in the benchmarks/tests directory."""
        benchmark_files = []
        categories = [
            'cpu/recursive',
            'cpu/arithmetic',
            'memory/allocation',
            'memory/gc',
            'object/dict',
            'object/list',
            'object/string',
            'interpreter/gil',
            'interpreter/bytecode',
            'interpreter/imports',
            'mixed/mem_cpu',
            'mixed/io_cpu'
        ]
        
        for category in categories:
            category_dir = self.benchmark_dir / category
            if category_dir.exists():
                for file in category_dir.glob("*.py"):
                    if file.name.startswith("test_"):
                        # Store as category/test_name (e.g., 'cpu/recursive/test_fibonacci')
                        relative_path = file.relative_to(self.benchmark_dir).with_suffix('')
                        benchmark_files.append(str(relative_path))
        
        # Also check root tests directory for any tests not yet categorized
        for file in self.benchmark_dir.glob("*.py"):
            if file.name.startswith("test_"):
                benchmark_files.append(file.stem)
                
        return benchmark_files

    def run_all(self) -> Dict[str, Dict]:
        """Run all discovered benchmarks and collect results."""
        results = {}
        benchmarks = self.discover_benchmarks()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console
        ) as progress:
            overall_task = progress.add_task(
                "[yellow]Overall progress", 
                total=len(benchmarks) * len(self.environments) * self.iterations
            )
            
            for benchmark in benchmarks:
                benchmark_task = progress.add_task(
                    f"[cyan]Running {benchmark}", 
                    total=len(self.environments) * self.iterations
                )
                
                results[benchmark] = {}
                for env in self.environments:
                    env_results = []
                    for i in range(self.iterations):
                        progress.update(
                            benchmark_task,
                            description=f"[cyan]{benchmark} - Python {env.version} (iteration {i+1}/{self.iterations})"
                        )
                        
                        result = env.run_benchmark(f"benchmarks/tests/{benchmark}.py")
                        if result['success']:
                            env_results.append(result['duration'])
                        
                        progress.advance(overall_task)
                        progress.advance(benchmark_task)
                    
                    # Store results for this environment
                    results[benchmark][env.version] = env_results
                
                # Process results after all environments have completed
                results[benchmark] = self._process_benchmark_results(results[benchmark])
                progress.remove_task(benchmark_task)
        
        return results

    def _process_benchmark_results(self, version_results: Dict) -> Dict:
        """Process results for all versions of a benchmark."""
        processed_results = {}
        baseline_stats = None
        
        for version, durations in version_results.items():
            if not durations:  # Skip if no successful iterations
                continue
                
            stats = StatisticalResult(
                mean=statistics.mean(durations),
                median=statistics.median(durations),
                stddev=statistics.stdev(durations) if len(durations) > 1 else 0,
                min=min(durations),
                max=max(durations),
                iterations=durations
            )
            
            if version == self.baseline_version:
                baseline_stats = stats
                processed_results[version] = BenchmarkResult(
                    status='baseline',
                    duration=stats.mean,
                    statistical_data=stats
                )
            else:
                relative_perf = (stats.mean / baseline_stats.mean) * 100
                perf_status = self._determine_performance_status(relative_perf)
                
                processed_results[version] = BenchmarkResult(
                    status=perf_status,
                    duration=stats.mean,
                    relative_performance=f"{relative_perf:.2f}%",
                    statistical_data=stats
                )
        
        return processed_results

    def _determine_performance_status(self, relative_perf: float) -> str:
        """Determine performance status based on relative performance."""
        if relative_perf < 90:  # More than 10% improvement
            return 'improved'
        elif relative_perf > 110:  # More than 10% degradation
            return 'degraded'
        else:  # Within ±10%
            return 'similar'

    def display_results(self, results: Dict[str, Dict]):
        """Display benchmark results in a rich table format."""
        self.console.print()
        title = Text(f"Python Interpreter Benchmark Results ({self.iterations} iterations)", 
                    style="bold magenta")
        self.console.print(Panel(title, expand=False))
        self.console.print()

        for benchmark_name, versions in results.items():
            table = Table(
                title=Text(f"Benchmark: {benchmark_name}", style="bold cyan"),
                show_header=True,
                header_style="bold green"
            )
            
            table.add_column("Python Version", style="cyan")
            table.add_column("Status", style="yellow")
            table.add_column("Mean Duration", style="green")
            table.add_column("Relative Perf", style="magenta")
            table.add_column("Std Dev", style="blue")
            table.add_column("Min/Max", style="cyan")
            
            for version, data in versions.items():
                # Status remains simple
                status_style = "bold blue" if data.status == "baseline" else "white"
                
                # Determine performance color based on relative performance
                perf_style = "white"
                if data.relative_performance:
                    perf_value = float(data.relative_performance.rstrip('%'))
                    if perf_value < 90:  # >10% improvement
                        perf_style = "bold green"
                    elif perf_value > 110:  # >10% degradation
                        perf_style = "bold red"
                    else:  # Within ±10%
                        perf_style = "bold yellow"
                
                stats = data.statistical_data
                table.add_row(
                    version,
                    Text(data.status, style=status_style),
                    f"{stats.mean:.4f}s",
                    Text(data.relative_performance or "N/A", style=perf_style),
                    f"±{stats.stddev:.4f}s",
                    f"{stats.min:.4f}s/{stats.max:.4f}s"
                )
            
            self.console.print(table)
            self.console.print()

    def run_profiling(self, env: PythonEnvironment, script_path: str) -> Dict:
        """Run lightweight profiling for a benchmark."""
        profiling_code = """
import sys
import time
from collections import defaultdict
from typing import Dict

class LightProfiler:
    def __init__(self):
        self.call_stats = defaultdict(lambda: {'calls': 0, 'total_time': 0})
        self.stack = []
        self.start_times = {}
        
    def callback(self, code, event, arg):
        now = time.perf_counter_ns()
        
        if event == "call":
            self.stack.append(code)
            self.start_times[code] = now
        elif event == "return" and self.stack:
            if code != self.stack[-1]:
                return  # Mismatched call/return
            
            start_time = self.start_times.pop(code, None)
            if start_time is not None:
                duration = (now - start_time) / 1e9  # Convert to seconds
                func_name = f"{code.co_filename}:{code.co_name}"
                self.call_stats[func_name]['calls'] += 1
                self.call_stats[func_name]['total_time'] += duration
            
            self.stack.pop()

profiler = LightProfiler()
sys.monitoring.use_tool_id(1)  # Use a custom tool ID
sys.monitoring.set_events(1, ["call", "return"])
sys.monitoring.set_local_events(1, ["call", "return"])
sys.monitoring.register_callback(1, "call", profiler.callback)
sys.monitoring.register_callback(1, "return", profiler.callback)
"""
        
        # Run benchmark with monitoring
        result = env.run_benchmark(
            script_path, 
            preload_code=profiling_code,
            get_profiler_data=True
        )
        
        if not result.get('success'):
            return {}
            
        profiler_data = result.get('profiler_data', {})
        return {
            'call_stats': profiler_data.get('call_stats', {}),
            'memory': self._collect_memory_stats(env, script_path)
        }

    def _collect_memory_stats(self, env: PythonEnvironment, script_path: str) -> Dict:
        """Collect memory statistics without using tracemalloc."""
        memory_code = """
import sys
import gc
from collections import defaultdict

class MemoryStats:
    def __init__(self):
        self.allocation_count = defaultdict(int)
        self.total_allocated = 0
        self.peak_memory = 0
        
    def update(self, size):
        self.allocation_count[size] += 1
        self.total_allocated += size
        self.peak_memory = max(self.peak_memory, self.total_allocated)

memory_stats = MemoryStats()
def memory_callback(event_type, size):
    if event_type == "malloc":
        memory_stats.update(size)

sys.monitoring.set_events(1, ["mem_alloc"])
sys.monitoring.register_callback(1, "mem_alloc", memory_callback)
"""
        
        result = env.run_benchmark(
            script_path,
            preload_code=memory_code,
            get_memory_stats=True
        )
        
        if not result.get('success'):
            return {}
            
        memory_data = result.get('memory_stats', {})
        return {
            'peak_memory': memory_data.get('peak_memory', 0),
            'allocation_patterns': dict(memory_data.get('allocation_count', {}))
        }

    def generate_technical_report(self, results: Dict, profile_data: Dict):
        """Generate a detailed technical report."""
        report = {
            'system_info': self.system_info.__dict__,
            'benchmarks': {}
        }
        
        for benchmark_name, versions in results.items():
            report['benchmarks'][benchmark_name] = {
                'summary': {
                    version: {
                        'mean': data.statistical_data.mean,
                        'stddev': data.statistical_data.stddev,
                        'median': data.statistical_data.median,
                        'min': data.statistical_data.min,
                        'max': data.statistical_data.max,
                        'relative_perf': data.relative_performance
                    }
                    for version, data in versions.items()
                },
                'profiling': {
                    version: profile_data.get(f"{benchmark_name}_{version}", {})
                    for version in versions.keys()
                }
            }
        
        # Save detailed report using custom encoder
        with open('benchmark_report.json', 'w') as f:
            json.dump(report, f, indent=2, cls=BenchmarkJSONEncoder)
        
        # Display critical findings
        self._display_critical_metrics(report)

    def _display_critical_metrics(self, report: Dict):
        """Display the most relevant metrics for technical analysis."""
        # First show system context
        sys_table = Table(title="[bold red]System Context[/bold red]")
        sys_table.add_column("Metric", style="cyan")
        sys_table.add_column("Value", style="green")
        sys_table.add_row("CPU", f"{self.system_info.os_info} - {self.system_info.cpu_count} cores")
        sys_table.add_row("CPU Freq", f"{self.system_info.cpu_freq['current']/1000:.2f} GHz")
        sys_table.add_row("System Load", f"{self.system_info.load_avg[0]:.2f} (1m)")
        self.console.print(sys_table)
        self.console.print()

        for benchmark_name, data in report['benchmarks'].items():
            table = Table(title=f"[bold]{benchmark_name} - Performance Analysis[/bold]")
            
            table.add_column("Metric", style="cyan")
            for version in self.environments:
                table.add_column(f"Python {version.version}", style="green")
            
            # Run-to-run variance (key for stability analysis)
            cv_values = []
            for version in self.environments:
                stats = data['summary'][version.version]
                cv = (stats['stddev'] / stats['mean']) * 100
                cv_values.append(f"{cv:.2f}%")
            table.add_row("Run Variance", *cv_values)
            
            # Thread behavior for 3.13.0t
            if '3.13.0t' in data['summary']:
                thread_metrics = data.get('thread_metrics', {})
                if thread_metrics:
                    table.add_row(
                        "Thread Switches/sec",
                        "N/A",
                        "N/A",
                        f"{thread_metrics.get('thread_switches', 'N/A')}"
                    )
                    table.add_row(
                        "Peak Thread Count",
                        "N/A",
                        "N/A",
                        f"{thread_metrics.get('peak_threads', 'N/A')}"
                    )
            
            # Cache behavior
            if 'cache_stats' in data:
                for version in self.environments:
                    stats = data['cache_stats'].get(version.version, {})
                    cache_misses = [
                        f"{stats.get('l1_misses', 'N/A')}",
                        f"{stats.get('l2_misses', 'N/A')}",
                        f"{stats.get('l3_misses', 'N/A')}"
                    ]
                table.add_row("Cache Misses (L1/L2/L3)", *cache_misses)
            
            # Memory allocation patterns
            if 'memory_patterns' in data:
                for version in self.environments:
                    stats = data['memory_patterns'].get(version.version, {})
                    alloc_pattern = [
                        f"{stats.get('small_allocs', 'N/A')}",
                        f"{stats.get('large_allocs', 'N/A')}"
                    ]
                table.add_row("Alloc Pattern (small/large)", *alloc_pattern)
            
            # Add memory churn metrics
            if 'memory_churn' in data:
                churn_rates = []
                for version in self.environments:
                    stats = data['memory_churn'].get(version.version, {})
                    rate = stats.get('churn_rate', 0) / (1024 * 1024)  # Convert to MB/s
                    churn_rates.append(f"{rate:.1f}MB/s")
                table.add_row("Memory Churn", *churn_rates)
                
                # Add allocation size distribution if significant differences
                if any(abs(float(r.strip('MB/s')) - float(churn_rates[0].strip('MB/s'))) > 5 
                   for r in churn_rates[1:]):
                    for version in self.environments:
                        stats = data['memory_churn'].get(version.version, {})
                        sizes = stats.get('allocation_sizes', {})
                        small = sum(count for size, count in sizes.items() if size < 1024)
                        large = sum(count for size, count in sizes.items() if size >= 1024)
                        table.add_row(
                            "Alloc Distribution (S/L)",
                            f"{small}/{large}",
                            f"{small}/{large}",
                            f"{small}/{large}"
                        )
            
            self.console.print(table)
            self.console.print()

    def collect_threading_metrics(self, env: PythonEnvironment, script_path: str) -> Dict:
        """Collect threading-specific metrics for no-GIL Python."""
        if not env.version.endswith('t'):
            return {}
            
        # Run with thread stats collection
        thread_stats_code = """
import sys, threading, time
from _thread import _count
start_time = time.time()
old_count = _count()
result = None

def monitor_threads():
    global result
    thread_counts = []
    while time.time() - start_time < 1.0:  # Monitor for 1 second
        thread_counts.append(_count() - old_count)
        time.sleep(0.001)
    result = {
        'peak_threads': max(thread_counts),
        'avg_threads': sum(thread_counts)/len(thread_counts),
        'thread_switches': len([x for x in thread_counts if x != thread_counts[0]])
    }

monitor = threading.Thread(target=monitor_threads)
monitor.start()
"""
        env.run_benchmark(script_path, preload_code=thread_stats_code)
        return result

    def collect_memory_churn(self, env: PythonEnvironment, script_path: str) -> Dict:
        """Collect memory churn metrics."""
        memory_tracking_code = """
import gc, sys, time
from collections import defaultdict

class MemoryChurnTracker:
    def __init__(self):
        self.allocs = defaultdict(int)
        self.deallocs = defaultdict(int)
        self.start_time = time.time()
        
    def callback(self, phase, info):
        if phase == "malloc":
            self.allocs[info["size"]] += 1
        elif phase == "free":
            self.deallocs[info["size"]] += 1

    @property
    def churn_rate(self):
        duration = time.time() - self.start_time
        total_alloc_bytes = sum(size * count for size, count in self.allocs.items())
        return total_alloc_bytes / duration  # bytes/second

tracker = MemoryChurnTracker()
gc.callbacks.append(tracker.callback)
sys.monitoring.set_events({"mem"})  # Python 3.12+ feature
"""
        result = env.run_benchmark(script_path, preload_code=memory_tracking_code)
        return {
            'churn_rate': result.get('churn_rate', 0),
            'allocation_sizes': result.get('allocs', {}),
            'deallocation_sizes': result.get('deallocs', {})
        }

    def run_benchmark(self, benchmark_path: str) -> Dict:
        """Run a specific benchmark across all Python environments."""
        # Handle both categorized and root-level tests
        if '/' in benchmark_path:
            full_path = self.benchmark_dir / f"{benchmark_path}.py"
        else:
            full_path = self.benchmark_dir / f"{benchmark_path}.py"
            
        if not full_path.exists():
            raise FileNotFoundError(f"Benchmark not found: {full_path}")
            
        results = []
        for env in self.environments:
            result = env.run_benchmark(str(full_path))
            results.append(result)
        
        return self._process_benchmark_results(results)

class BenchmarkJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for benchmark data classes."""
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        if isinstance(obj, (ProfilingData, MemorySnapshot, StatisticalResult, SystemMetrics)):
            return obj.__dict__
        if isinstance(obj, tracemalloc.Snapshot):
            return None  # Skip tracemalloc snapshots
        return super().default(obj)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Python Interpreter Benchmark Suite')
    parser.add_argument(
        '--iterations', 
        type=int, 
        default=5,
        help='Number of iterations for each benchmark'
    )
    parser.add_argument(
        '--profile', 
        choices=['basic', 'detailed', 'none'],
        default='basic',
        help='Profiling level (basic=timing only, detailed=full profiling, none=no profiling)'
    )
    parser.add_argument(
        '--benchmarks',
        nargs='*',
        help='Specific benchmarks to run (default: all)'
    )
    parser.add_argument(
        '--report-format',
        choices=['text', 'json', 'both'],
        default='text',
        help='Output format for the results'
    )

    args = parser.parse_args()
    
    runner = BenchmarkRunner(
        iterations=args.iterations,
        profile=(args.profile != 'none')
    )

    # Filter benchmarks if specified
    if args.benchmarks:
        runner.benchmark_dir = Path("benchmarks/tests")
        available = set(runner.discover_benchmarks())
        requested = set(b if b.startswith('test_') else f'test_{b}' for b in args.benchmarks)
        invalid = requested - available
        if invalid:
            print(f"Warning: Unknown benchmarks: {', '.join(invalid)}")
        runner.discover_benchmarks = lambda: list(requested & available)

    # Run benchmarks
    results = runner.run_all()
    
    # Run profiling if requested
    profile_data = {}
    if args.profile == 'detailed':
        with runner.console.status("[bold yellow]Running detailed profiling..."):
            for benchmark in runner.discover_benchmarks():
                for env in runner.environments:
                    profile_data[f"{benchmark}_{env.version}"] = runner.run_profiling(
                        env, 
                        f"benchmarks/tests/{benchmark}.py"
                    )
    
    # Display results based on format
    if args.report_format in ('text', 'both'):
        runner.display_results(results)
    
    if args.profile == 'detailed':
        runner.generate_technical_report(results, profile_data)
    
    if args.report_format in ('json', 'both'):
        with open('benchmark_results.json', 'w') as f:
            json.dump({
                'results': results,
                'profile_data': profile_data if args.profile == 'detailed' else None,
                'system_info': runner.system_info.__dict__,
                'run_config': {
                    'iterations': args.iterations,
                    'profile_level': args.profile,
                    'benchmarks': args.benchmarks
                }
            }, f, indent=2, cls=BenchmarkJSONEncoder)

