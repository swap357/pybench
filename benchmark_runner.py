from typing import List, Dict, Optional
from benchmarks.environment import PythonEnvironment
from benchmarks.base import BenchmarkResult
import os
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.panel import Panel
from rich.text import Text
import statistics
from dataclasses import dataclass
import psutil
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

class BenchmarkRunner:
    # Define interpreter versions here as a class variable
    PYTHON_VERSIONS = {
        "3.12.7": {"type": "baseline"},  # Marking baseline version
        "3.13.0": {"type": "release"},
        "3.13.0t": {"type": "experimental"},
        "3.14.0a1": {"type": "experimental"},
        "3.14.0a1t": {"type": "experimental"},
    }
    BASELINE_VERSION = "3.12.7"

    def __init__(self, iterations: int = 5, profile: bool = True):
        self.environments = [
            PythonEnvironment(version) for version in self.PYTHON_VERSIONS.keys()
        ]
        self.benchmark_dir = Path("benchmarks/tests")
        self.baseline_version = self.BASELINE_VERSION
        self.console = Console()
        self.iterations = iterations
        self.profile = profile
        self.system_info = self._collect_system_info()

    def _collect_system_info(self) -> SystemMetrics:
        """Collect system-wide metrics."""
        try:
            cpu_freq = psutil.cpu_freq()
            cpu_freq_dict = dict(cpu_freq._asdict()) if cpu_freq else {}
        except FileNotFoundError:
            cpu_freq_dict = {"current": "N/A", "min": "N/A", "max": "N/A"}

        return SystemMetrics(
            cpu_count=psutil.cpu_count(logical=True),
            memory_total=psutil.virtual_memory().total,
            os_info=f"{os.uname().sysname} {os.uname().release}",
            cpu_freq=cpu_freq_dict,
            load_avg=os.getloadavg() if hasattr(os, 'getloadavg') else (0.0, 0.0, 0.0)
        )

    def discover_benchmarks(self) -> List[str]:
        """Discover all benchmark modules in the benchmarks/tests directory."""
        benchmark_files = []
        categories = [
            # 'core/memory_ordering',
            # 'core/refcounting',
            # 'core/specialization'
            # 'cpu/recursive', 'cpu/arithmetic', 'memory/allocation', 'memory/gc',
            # 'object/dict', 'object/list', 'object/string', 'interpreter/gil',
            # 'interpreter/bytecode', 'interpreter/imports', 'mixed/mem_cpu', 'mixed/io_cpu'
            'workload/'
        ]

        for category in categories:
            category_dir = self.benchmark_dir / category
            if category_dir.exists():
                benchmark_files.extend(
                    str(file.relative_to(self.benchmark_dir).with_suffix(''))
                    for file in category_dir.glob("test_*.py")
                )

        # Check root tests directory for any tests not yet categorized
        benchmark_files.extend(
            file.stem for file in self.benchmark_dir.glob("test_*.py")
        )

        return benchmark_files

    def get_versions_info(self):
        """Return information about Python versions for other scripts"""
        return {
            "versions": list(self.PYTHON_VERSIONS.keys()),
            "baseline": self.BASELINE_VERSION,
            "metadata": self.PYTHON_VERSIONS
        }

    def run_all(self) -> Dict[str, Dict]:
        """Run all discovered benchmarks and collect results."""
        results = {}
        benchmarks = self.discover_benchmarks()

        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"),
            BarColumn(), TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(), console=self.console
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
                        try:
                            progress.update(
                                benchmark_task,
                                description=f"[cyan]{benchmark} - Python {env.version} (iteration {i+1}/{self.iterations})"
                            )

                            result = env.run_benchmark(f"benchmarks/tests/{benchmark}.py")
                            if result['success']:
                                env_results.append(result['duration'])
                            else:
                                self.console.print(f"[red]Benchmark {benchmark} failed on Python {env.version} (iteration {i+1})[/red]")

                        except Exception as e:
                            self.console.print(f"[red]Error running {benchmark} on Python {env.version}: {e}[/red]")

                        progress.advance(overall_task)
                        progress.advance(benchmark_task)

                    # Store results for this environment
                    results[benchmark][env.version] = env_results

                # Process results after all environments have completed
                results[benchmark] = self._process_benchmark_results(results[benchmark])
                progress.remove_task(benchmark_task)

                # Display results for the current benchmark
                self.display_results({benchmark: results[benchmark]})

        results['versions_info'] = self.get_versions_info()  # Add versions info to results
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
        parser = argparse.ArgumentParser(description='Python Interpreter Benchmark Suite')
        parser.add_argument('--iterations', type=int, default=5, help='Number of iterations for each benchmark')
        parser.add_argument('--profile', choices=['basic', 'detailed', 'none'], default='basic', help='Profiling level (basic=timing only, detailed=full profiling, none=no profiling)')
        parser.add_argument('--benchmarks', nargs='*', help='Specific benchmarks to run (default: all)')
        parser.add_argument('--report-format', choices=['text', 'json', 'both'], default='text', help='Output format for the results')

        args = parser.parse_args()

        runner = BenchmarkRunner(iterations=args.iterations, profile=(args.profile != 'none'))

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

        # Save results to JSON if needed
        if args.report_format in ('json', 'both'):
            with open('benchmark_results.json', 'w') as f:
                json.dump({
                    'results': results,
                    'system_info': runner.system_info.__dict__,
                    'run_config': {
                        'iterations': args.iterations,
                        'profile_level': args.profile,
                        'benchmarks': args.benchmarks
                    }
                }, f, indent=2, cls=BenchmarkJSONEncoder)

    except Exception as e:
        console = Console()
        console.print(f"[red]An unexpected error occurred: {e}[/red]")
