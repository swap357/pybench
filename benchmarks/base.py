from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .environment import PythonEnvironment

class Benchmark(ABC):
    def __init__(self, name: str):
        self.name = name
        self.environments = [
            PythonEnvironment("3.12"),
            PythonEnvironment("3.13"),
            PythonEnvironment("3.13t")
        ]

    @abstractmethod
    def run(self) -> Dict:
        """Run the benchmark and return results."""
        pass

    def compare_results(self, results: List[Dict]) -> Dict:
        """Compare results between different Python versions."""
        baseline = next(r for r in results if r['version'] == '3.12')
        comparisons = {}
        
        for result in results:
            if not result['success']:
                comparisons[result['version']] = {
                    'status': 'failed',
                    'error': result['output']
                }
                continue
                
            if result['version'] == '3.12':
                comparisons[result['version']] = {
                    'status': 'baseline',
                    'duration': result['duration']
                }
            else:
                relative_perf = (result['duration'] / baseline['duration']) * 100
                comparisons[result['version']] = {
                    'status': 'success',
                    'duration': result['duration'],
                    'relative_performance': f"{relative_perf:.2f}%"
                }
        
        return comparisons

@dataclass
class BenchmarkResult:
    status: str
    duration: Optional[float] = None
    error: Optional[str] = None
    relative_performance: Optional[str] = None
    statistical_data: Optional[Any] = None

    def __str__(self):
        if self.status == 'failed':
            return f"Status: {self.status}, Error: {self.error}"
        elif self.status == 'baseline':
            return f"Status: {self.status}, Mean Duration: {self.duration:.4f}s"
        else:
            return f"Status: {self.status}, Mean Duration: {self.duration:.4f}s, Relative: {self.relative_performance}"
