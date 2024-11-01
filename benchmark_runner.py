from typing import List, Dict, Optional, Union
from benchmarks.environment import PythonEnvironment
from benchmarks.base import BenchmarkResult
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn, TaskID
from rich.panel import Panel
from rich.text import Text
import statistics
from dataclasses import dataclass
import psutil
import json
import argparse
import multiprocessing
import glob
from datetime import datetime
import sys

@dataclass
class SystemMetrics:
    cpu_count: int
    memory_total: int
    os_info: str
    cpu_freq: Dict
    load_avg: tuple
    cpu_affinity: Optional[str] = None

@dataclass
class StatisticalResult:
    mean: float
    median: float
    stddev: float
    min: float
    max: float
    iterations: List[float]

@dataclass
class RegularBenchmarkResult:
    status: str  # 'baseline', 'improved', 'degraded', 'similar'
    duration: float
    relative_performance: Optional[str] = None
    statistical_data: Optional[StatisticalResult] = None

@dataclass
class ScalingDataPoint:
    thread_count: int
    duration: float
    throughput: float
    cpu_usage: float
    memory_usage: float

@dataclass
class ScalingBenchmarkResult:
    status: str  # 'baseline', 'improved', 'degraded', 'similar'
    base_duration: float
    scaling_factor: float
    max_threads: int
    efficiency: float  # Parallel efficiency (0-1)
    relative_performance: Optional[str] = None
    statistical_data: Optional[StatisticalResult] = None
    scaling_data: List[ScalingDataPoint] = None

@dataclass
class BenchmarkSuite:
    regular_tests: Dict[str, Dict[str, RegularBenchmarkResult]]
    scaling_tests: Dict[str, Dict[str, ScalingBenchmarkResult]]
    system_info: SystemMetrics
    versions_info: Dict[str, any]

class BenchmarkRunner:
    # Define interpreter versions here as a class variable
    PYTHON_VERSIONS = {
        "3.12.7": {"type": "baseline"},  # Marking baseline version
        "3.13.0": {"type": "release"},
        "3.13.0t": {"type": "experimental"},
        # "3.14.0a1": {"type": "experimental"},
        # "3.14.0a1t": {"type": "experimental"},
    }
    BASELINE_VERSION = "3.12.7"

    def __init__(self, iterations: int = 5, profile: bool = True):
        self.environments = []
        self._init_environments()
        self._init_directories()
        self._init_thread_config()
        
        self.console = Console()
        self.iterations = iterations
        self.profile = profile
        self.system_info = self._collect_system_info()

    def _init_environments(self):
        """Initialize Python environments with GIL configuration."""
        for version, info in self.PYTHON_VERSIONS.items():
            env = PythonEnvironment(version)
            if env.is_free_threaded:
                gil_status = "disabled" if version.endswith('t') else "enabled"
                print(f"Running {version} with GIL {gil_status}")
            self.environments.append(env)

    def _init_directories(self):
        """Initialize directory paths."""
        self.test_dir = Path("benchmarks/tests")
        self.scaling_dir = Path("benchmarks/scaling") 
        self.baseline_version = self.BASELINE_VERSION

    def _init_thread_config(self):
        """Initialize thread and CPU configuration."""
        # Set number of threads based on CPU affinity or count
        try:
            process = psutil.Process()
            self.num_threads = len(process.cpu_affinity())
        except (AttributeError, psutil.Error):
            self.num_threads = multiprocessing.cpu_count()

        # Handle CPU core limits
        self.cpu_cores = os.environ.get('BENCHMARK_CPU_CORES', 'all')
        if self.cpu_cores != 'all':
            try:
                self.num_threads = min(int(self.cpu_cores), self.num_threads)
            except ValueError:
                pass

        # Handle thread limits
        self._configure_thread_limits()

    def _configure_thread_limits(self):
        """Configure thread limits based on environment variables."""
        thread_limit = os.environ.get('BENCHMARK_THREAD_LIMIT', '1')
        try:
            if thread_limit != '0':
                self.thread_limit = int(thread_limit)
                self.total_threads = self.num_threads * self.thread_limit
            else:
                self.thread_limit = 0
                self.total_threads = None
        except ValueError:
            self.thread_limit = 1
            self.total_threads = self.num_threads

    def _collect_system_info(self) -> SystemMetrics:
        """Collect system-wide metrics."""
        try:
            cpu_freq = psutil.cpu_freq()
            cpu_freq_dict = dict(cpu_freq._asdict()) if cpu_freq else {}
        except FileNotFoundError:
            cpu_freq_dict = {"current": "N/A", "min": "N/A", "max": "N/A"}

        # Get CPU affinity if available
        try:
            process = psutil.Process()
            affinity = process.cpu_affinity()
            cpu_affinity = f"cores {min(affinity)}-{max(affinity)}" if affinity else None
        except (AttributeError, psutil.Error):
            cpu_affinity = None

        return SystemMetrics(
            cpu_count=psutil.cpu_count(logical=True),
            memory_total=psutil.virtual_memory().total,
            os_info=f"{os.uname().sysname} {os.uname().release}",
            cpu_freq=cpu_freq_dict,
            load_avg=os.getloadavg() if hasattr(os, 'getloadavg') else (0.0, 0.0, 0.0),
            cpu_affinity=cpu_affinity
        )

    def discover_tests(self) -> Dict[str, List[str]]:
        """Discover both regular and scaling tests."""
        return {
            "regular": self._discover_regular_tests(),
            "scaling": self._discover_scaling_tests()
        }

    def _discover_regular_tests(self) -> List[str]:
        """Discover regular benchmark tests."""
        tests = []
        categories = [
            "baseline/", "gil/", "memory/ordering/",
            "memory/ref_counting/", "specialization/", "bytecode/"
        ]

        # Discover categorized tests
        for category in categories:
            category_dir = self.test_dir / category
            if category_dir.exists():
                tests.extend(
                    str(file.relative_to(self.test_dir))
                    for file in category_dir.glob("test_*.py")
                )

        # Discover tests in root test directory
        tests.extend(
            str(file.relative_to(self.test_dir))
            for file in self.test_dir.glob("test_*.py")
        )

        return tests

    def _discover_scaling_tests(self) -> List[str]:
        """Discover scaling benchmark tests."""
        if not self.scaling_dir.exists():
            return []
            
        return [
            str(file.relative_to(self.scaling_dir))
            for file in self.scaling_dir.glob("test_*.py")
        ]

    def get_versions_info(self):
        """Return information about Python versions for other scripts"""
        return {
            "versions": list(self.PYTHON_VERSIONS.keys()),
            "baseline": self.BASELINE_VERSION,
            "metadata": self.PYTHON_VERSIONS
        }

    def _set_thread_limits(self):
        """Set thread limits for benchmarks based on configuration"""
        if self.total_threads is not None:
            os.environ['OMP_NUM_THREADS'] = str(self.total_threads)
            os.environ['MKL_NUM_THREADS'] = str(self.total_threads)
            os.environ['OPENBLAS_NUM_THREADS'] = str(self.total_threads)
            os.environ['VECLIB_MAXIMUM_THREADS'] = str(self.total_threads)
            os.environ['NUMEXPR_NUM_THREADS'] = str(self.total_threads)

    def run_all(self) -> BenchmarkSuite:
        """Run all discovered benchmarks and collect results."""
        self._set_thread_limits()
        discovered_tests = self.discover_tests()
        results = {"regular": {}, "scaling": {}}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console
        ) as progress:
            # Calculate total based on filtered tests
            total_tests = 0
            if hasattr(self, 'test_filter'):
                if self.test_filter:
                    total_tests = len([t for t in discovered_tests["scaling"] 
                                     if any(f in t for f in self.test_filter)])
                else:
                    total_tests = len(discovered_tests["scaling"])
            else:
                total_tests = len(discovered_tests["regular"]) + len(discovered_tests["scaling"])
                
            overall_task = progress.add_task(
                "[yellow]Overall progress",
                total=total_tests * len(self.environments) * self.iterations
            )

            # Run only filtered scaling tests
            for test_path in discovered_tests["scaling"]:
                test_name = str(test_path).replace('.py', '')
                if hasattr(self, 'test_filter') and self.test_filter:
                    if not any(f in test_path for f in self.test_filter):
                        continue
                results["scaling"][test_name] = self._run_scaling_test(
                    test_path, progress, overall_task
                )
                self.display_scaling_results({test_name: results["scaling"][test_name]})

        return BenchmarkSuite(
            regular_tests=results["regular"],
            scaling_tests=results["scaling"],
            system_info=self.system_info,
            versions_info=self.get_versions_info()
        )

    def _run_regular_test(self, test_path: str, progress: Progress, overall_task: TaskID) -> Dict:
        """Run a regular benchmark test."""
        results = {}
        test_name = str(test_path).replace('.py', '')
        
        benchmark_task = progress.add_task(
            f"[cyan]Running {test_name}", 
            total=len(self.environments) * self.iterations
        )
        
        for env in self.environments:
            env_results = []
            for i in range(self.iterations):
                try:
                    progress.update(
                        benchmark_task,
                        description=f"[cyan]{test_name} - Python {env.version} (iteration {i+1}/{self.iterations})"
                    )
                    
                    # Fix path resolution
                    full_path = self.test_dir / test_path
                    result = env.run_benchmark(str(full_path))
                    
                    if result['success']:
                        env_results.append(result['duration'])
                    else:
                        self.console.print(f"[red]Benchmark {test_name} failed on Python {env.version} (iteration {i+1}): {result.get('error', 'Unknown error')}[/red]")

                except Exception as e:
                    self.console.print(f"[red]Error running {test_name} on Python {env.version}: {e}[/red]")

                progress.advance(overall_task)
                progress.advance(benchmark_task)

            if env_results:
                results[env.version] = env_results

        progress.remove_task(benchmark_task)
        return self._process_benchmark_results(results, "regular")

    def _run_scaling_test(self, test_path: str, progress: Progress, overall_task: TaskID) -> Dict:
        """Run a scaling benchmark test."""
        results = {}
        test_name = str(test_path).replace('.py', '')
        
        benchmark_task = progress.add_task(
            f"[cyan]Running scaling test {test_name}", 
            total=len(self.environments) * self.iterations
        )
        
        for env in self.environments:
            env_results = []
            scaling_data = []
            
            for i in range(self.iterations):
                try:
                    progress.update(
                        benchmark_task,
                        description=f"[cyan]{test_name} - Python {env.version} (iteration {i+1}/{self.iterations})"
                    )
                    
                    # Fix path resolution
                    full_path = self.scaling_dir / test_path
                    result = env.run_benchmark(str(full_path))
                    
                    if result['success']:
                        try:
                            data = json.loads(result['output'])
                            
                            # Check for error in output
                            if 'error' in data['metadata']:
                                self.console.print(f"[red]Test error: {data['metadata']['error']}[/red]")
                                continue
                                
                            # Store baseline duration
                            env_results.append(data['baseline']['duration'])
                            # Store scaling data
                            scaling_data.append(data)
                            
                        except json.JSONDecodeError as e:
                            self.console.print(f"[yellow]Warning: Invalid JSON output: {e}[/yellow]")
                        except KeyError as e:
                            self.console.print(f"[yellow]Warning: Missing key in output: {e}[/yellow]")
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        if isinstance(error_msg, str) and len(error_msg) > 200:
                            # Truncate long error messages that might be JSON output
                            error_msg = error_msg[:200] + "..."
                        self.console.print(f"[red]Benchmark {test_name} failed on Python {env.version} (iteration {i+1}): {error_msg}[/red]")

                except Exception as e:
                    self.console.print(f"[red]Error running {test_name} on Python {env.version}: {e}[/red]")

                progress.advance(overall_task)
                progress.advance(benchmark_task)

            if env_results:
                results[env.version] = {
                    'durations': env_results,
                    'scaling_data': scaling_data
                }

        progress.remove_task(benchmark_task)
        return self._process_scaling_results(results)

    def _process_scaling_results(self, version_results: Dict) -> Dict:
        """Process scaling benchmark results."""
        processed_results = {}
        baseline_stats = None

        for version, data in version_results.items():
            durations = data['durations']
            scaling_data = data['scaling_data']
            
            if not durations or not scaling_data:
                continue

            # Calculate statistics for baseline runs
            stats = StatisticalResult(
                mean=statistics.mean(durations),
                median=statistics.median(durations),
                stddev=statistics.stdev(durations) if len(durations) > 1 else 0,
                min=min(durations),
                max=max(durations),
                iterations=durations
            )

            # Process scaling metrics from the last successful run
            latest_run = scaling_data[-1]
            max_test = latest_run['scaling_tests'][-1]
            
            scaling_result = ScalingBenchmarkResult(
                status='baseline' if version == self.baseline_version else 'comparison',
                base_duration=stats.mean,
                scaling_factor=max_test['speedup'],
                max_threads=max_test['threads'],
                efficiency=max_test['speedup'] / max_test['threads'],
                statistical_data=stats,
                scaling_data=[
                    ScalingDataPoint(
                        thread_count=test['threads'],
                        duration=test['duration'],
                        throughput=test.get('ops_per_sec', 0),
                        cpu_usage=test.get('cpu_usage', 0.0),
                        memory_usage=test.get('memory_usage', 0.0)
                    )
                    for test in latest_run['scaling_tests']
                ]
            )
            
            if version == self.baseline_version:
                baseline_stats = scaling_result
                processed_results[version] = scaling_result
            else:
                # Calculate relative performance
                if baseline_stats:
                    relative_perf = (scaling_result.scaling_factor / baseline_stats.scaling_factor) * 100
                    scaling_result.relative_performance = f"{relative_perf:.2f}%"
                    scaling_result.status = self._determine_performance_status(relative_perf, is_scaling=True)
                processed_results[version] = scaling_result

        return processed_results

    def _process_benchmark_results(self, version_results: Dict, test_type: str = "regular") -> Dict:
        """Process results for all versions of a benchmark."""
        processed_results = {}
        baseline_stats = None

        # Skip processing if no results
        if not version_results:
            return processed_results

        for version, data in version_results.items():
            if test_type == "regular":
                durations = data
            else:  # scaling
                durations = data['durations']
                scaling_data = data.get('scaling_data', [])

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
                if test_type == "regular":
                    processed_results[version] = RegularBenchmarkResult(
                        status='baseline',
                        duration=stats.mean,
                        statistical_data=stats
                    )
                else:  # scaling
                    processed_results[version] = self._process_scaling_result(
                        stats, scaling_data, 'baseline', None
                    )
            else:
                if baseline_stats:
                    relative_perf = (stats.mean / baseline_stats.mean) * 100
                    perf_status = self._determine_performance_status(relative_perf)
                else:
                    relative_perf = 100
                    perf_status = 'no_baseline'

                if test_type == "regular":
                    processed_results[version] = RegularBenchmarkResult(
                        status=perf_status,
                        duration=stats.mean,
                        relative_performance=f"{relative_perf:.2f}%",
                        statistical_data=stats
                    )
                else:  # scaling
                    processed_results[version] = self._process_scaling_result(
                        stats, scaling_data, perf_status, f"{relative_perf:.2f}%"
                    )

        return processed_results

    def _process_scaling_result(
        self, 
        stats: StatisticalResult, 
        status: str, 
        relative_performance: Optional[str]
    ) -> ScalingBenchmarkResult:
        """Process scaling benchmark results."""
        scaling_data = []
        
        try:
            # Find the most recent scaling test output file
            test_files = glob.glob("*_scaling_*.json")
            if not test_files:
                raise FileNotFoundError("No scaling test output files found")
                
            latest_file = max(test_files, key=os.path.getctime)
            
            with open(latest_file) as f:
                raw_data = json.load(f)
                
            baseline_data = raw_data["baseline"]
            scaling_tests = raw_data["scaling_tests"]
            
            # Convert scaling test data points
            for point in scaling_tests:
                scaling_data.append(ScalingDataPoint(
                    thread_count=point["threads"],
                    duration=point["duration"],
                    throughput=point.get("ops_per_sec", 
                                      point.get("refs_per_sec",
                                              point.get("objects_per_sec", 0))),
                    cpu_usage=point.get("cpu_usage", 0.0),
                    memory_usage=point.get("memory_usage", 0.0)
                ))
                
            # Calculate scaling metrics
            base_duration = baseline_data["duration"]
            max_threads = scaling_tests[-1]["threads"]
            max_speedup = scaling_tests[-1]["speedup"]
            efficiency = max_speedup / max_threads
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not process scaling data: {e}")
            # Fallback if detailed scaling data isn't available
            base_duration = stats.mean
            max_threads = self.num_threads
            max_speedup = 1.0
            efficiency = 1.0
            scaling_data = []

        return ScalingBenchmarkResult(
            status=status,
            base_duration=base_duration,
            scaling_factor=max_speedup,
            max_threads=max_threads,
            efficiency=efficiency,
            relative_performance=relative_performance,
            statistical_data=stats,
            scaling_data=scaling_data
        )

    def _determine_performance_status(self, relative_perf: float, is_scaling: bool = False) -> str:
        """Determine performance status based on relative performance."""
        if is_scaling:
            # For scaling tests: higher numbers are better
            if relative_perf > 110:  # More than 10% better scaling
                return 'improved'
            elif relative_perf < 90:  # More than 10% worse scaling
                return 'degraded'
            else:  # Within ±10%
                return 'similar'
        else:
            # For regular tests: lower numbers are better
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

    def display_scaling_results(self, results: Dict[str, Dict]):
        """Display scaling benchmark results in a rich table format."""
        self.console.print()
        title = Text(f"Python Interpreter Scaling Benchmark Results ({self.iterations} iterations)", 
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
            table.add_column("Base Duration", style="green")
            table.add_column("Max Speedup", style="magenta")
            table.add_column("Efficiency", style="blue")
            table.add_column("Max Threads", style="cyan")

            for version, data in versions.items():
                status_style = "bold blue" if data.status == "baseline" else "white"
                
                # Format efficiency as percentage
                efficiency_pct = f"{data.efficiency * 100:.1f}%"
                
                # Determine speedup color
                speedup_style = "white"
                if data.scaling_factor > 0.9 * data.max_threads:
                    speedup_style = "bold green"
                elif data.scaling_factor > 0.5 * data.max_threads:
                    speedup_style = "bold yellow"
                else:
                    speedup_style = "bold red"

                table.add_row(
                    version,
                    Text(data.status, style=status_style),
                    f"{data.base_duration:.4f}s",
                    Text(f"{data.scaling_factor:.2f}x", style=speedup_style),
                    efficiency_pct,
                    str(data.max_threads)
                )

            self.console.print(table)
            self.console.print()

class BenchmarkJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for benchmark data classes."""
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        if isinstance(obj, (StatisticalResult, SystemMetrics)):
            return obj.__dict__
        return super().default(obj)

if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(
            description='Python Interpreter Benchmark Suite',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Run all tests
  python benchmark_runner.py

  # Run only scaling tests
  python benchmark_runner.py --category scaling

  # Run specific scaling tests
  python benchmark_runner.py --category scaling --tests contention memory_bandwidth

  # Run specific regular tests from gil category
  python benchmark_runner.py --category gil --tests lock_patterns contention

Categories:
  - scaling       : Thread/process scaling tests
  - gil          : GIL-related tests
  - memory       : Memory-related tests
  - baseline     : Basic performance tests
  - specialization: Type specialization tests
  - bytecode     : Bytecode-related tests
  - all          : All test categories (default)
            """
        )
        
        parser.add_argument(
            '--category', 
            choices=['all', 'scaling', 'gil', 'memory', 'baseline', 'specialization', 'bytecode'],
            default='all',
            help='Test category to run'
        )
        
        parser.add_argument(
            '--tests',
            nargs='*',
            help='Specific tests to run (without test_ prefix)'
        )
        
        parser.add_argument(
            '--iterations', 
            type=int, 
            default=5,
            help='Number of iterations for each benchmark'
        )
        
        parser.add_argument(
            '--report',
            choices=['text', 'json', 'both'],
            default='text',
            help='Output format for results'
        )
        
        parser.add_argument(
            '--threads',
            type=str,
            default='auto',
            help='Thread configuration (auto, max, or number)'
        )
        
        parser.add_argument(
            '--list',
            action='store_true',
            help='List available tests in specified category'
        )

        args = parser.parse_args()

        # Configure thread settings
        if args.threads != 'auto':
            if args.threads == 'max':
                os.environ['BENCHMARK_CPU_CORES'] = 'all'
                os.environ['BENCHMARK_THREAD_LIMIT'] = '0'
            else:
                try:
                    thread_count = int(args.threads)
                    os.environ['BENCHMARK_CPU_CORES'] = str(thread_count)
                    os.environ['BENCHMARK_THREAD_LIMIT'] = '1'
                except ValueError:
                    print(f"Invalid thread count: {args.threads}")
                    sys.exit(1)

        runner = BenchmarkRunner(iterations=args.iterations)

        # Set test filter if specific tests requested
        if args.tests:
            runner.test_filter = [
                f"test_{t}" if not t.startswith("test_") else t 
                for t in args.tests
            ]
        else:
            runner.test_filter = None

        # Run benchmarks
        results = runner.run_all()

        # Save results if needed
        if args.report in ('json', 'both'):
            output_file = (f"benchmark_results_{args.category}_"
                         f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(output_file, 'w') as f:
                json.dump({
                    'results': results,
                    'system_info': runner.system_info.__dict__,
                    'run_config': {
                        'category': args.category,
                        'tests': args.tests,
                        'iterations': args.iterations,
                        'threads': args.threads
                    }
                }, f, indent=2, cls=BenchmarkJSONEncoder)
            print(f"\nResults saved to: {output_file}")

    except KeyboardInterrupt:
        print("\nBenchmark run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
