from typing import List, Dict
import subprocess
import sys
import platform
from pathlib import Path
import time
import os
import tempfile

class PythonEnvironment:
    def __init__(self, version: str, path: str = None):
        self.version = version
        self.path = path or self._get_python_path(version)
        self._validate_interpreter()
        self.is_free_threaded = self._check_free_threading()
        self._ensure_dependencies()

    def _get_python_path(self, version: str) -> str:
        """Get the Python interpreter path using pyenv."""
        try:
            # First try to get all pyenv versions
            versions_result = subprocess.run(
                ['pyenv', 'versions', '--bare'],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Find the matching version
            available_versions = versions_result.stdout.strip().split('\n')
            matching_version = next(
                (v for v in available_versions if v.startswith(version)), 
                None
            )
            
            if not matching_version:
                raise RuntimeError(f"Python {version} not found in pyenv versions")
            
            # Get the full path for the matching version
            result = subprocess.run(
                ['pyenv', 'prefix', matching_version],
                capture_output=True,
                text=True,
                check=True
            )
            
            python_path = Path(result.stdout.strip()) / 'bin' / 'python'
            if not python_path.exists():
                raise RuntimeError(f"Python executable not found at {python_path}")
                
            return str(python_path)
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to get Python {version} path: {e.stderr}")
        except Exception as e:
            raise RuntimeError(f"Error finding Python {version}: {str(e)}")

    def _check_free_threading(self) -> bool:
        """Check if this Python build supports free threading"""
        try:
            check_script = """
import sysconfig
gil_disabled = sysconfig.get_config_var("Py_GIL_DISABLED")
print(f"{gil_disabled}")
            """
            
            result = subprocess.run(
                [self.path, '-c', check_script],
                capture_output=True,
                text=True,
                check=True
            )
            
            return result.stdout.strip() == '1'
        except subprocess.CalledProcessError:
            return False
        except Exception:
            return False

    def _ensure_dependencies(self):
        """Install required dependencies if missing."""
        dependencies = {
            'numpy': ['np_column_compute'],
            'psutil': ['test_contention', 'test_lock_patterns']
        }

        for package, test_patterns in dependencies.items():
            # Check if any relevant tests are present in both scaling and regular tests
            has_matching_test = any(
                pattern in test 
                for pattern in test_patterns 
                for test in (
                    os.listdir('benchmarks/scaling') + 
                    os.listdir('benchmarks/tests/gil')
                )
            )
            
            if has_matching_test:
                try:
                    # Try importing the package
                    subprocess.run(
                        [self.path, '-c', f'import {package}'],
                        capture_output=True,
                        check=True
                    )
                except subprocess.CalledProcessError:
                    # Install if import fails
                    print(f"Installing {package} for Python {self.version}")
                    subprocess.run(
                        [self.path, '-m', 'pip', 'install', package],
                        check=True
                    )

    def run_benchmark(self, benchmark_path: str) -> Dict:
        """Run a benchmark and return results."""
        try:
            # Create a temporary file for output capture
            with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_out:
                start_time = time.time()
                
                # Run the benchmark with output redirection
                process = subprocess.Popen(
                    [self.path, benchmark_path],
                    stdout=temp_out,
                    stderr=subprocess.PIPE,
                    text=True,
                    env=os.environ.copy()
                )
                
                _, stderr = process.communicate()
                duration = time.time() - start_time
                
                # Read the captured output
                temp_out.seek(0)
                output = temp_out.read()
                
                if process.returncode != 0:
                    return {
                        'success': False,
                        'error': stderr.strip() or 'Process failed',
                        'duration': duration,
                        'output': output
                    }
                
                return {
                    'success': True,
                    'duration': duration,
                    'output': output
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'duration': 0,
                'output': ''
            }

    def _validate_interpreter(self):
        """Validate Python interpreter and check free-threading support"""
        try:
            check_script = """
import sys
import sysconfig
version = sys.version
gil_disabled = sysconfig.get_config_var("Py_GIL_DISABLED")
print(f"{version}|{gil_disabled}")
            """
            
            result = subprocess.run(
                [self.path, '-c', check_script],
                capture_output=True,
                text=True,
                check=True
            )
            
            version_str, gil_disabled_str = result.stdout.strip().split('|')
            gil_disabled = gil_disabled_str.strip() == '1'
            
            # Validate version and free-threading status
            if self.version.endswith('t'):
                if not gil_disabled:
                    raise RuntimeError(
                        f"Version {self.version} requires free-threading support, "
                        "but interpreter does not support it"
                    )
            
            if not self.version.endswith('t'):
                base_version = self.version
            else:
                base_version = self.version[:-1]
                
            if base_version not in version_str:
                raise RuntimeError(
                    f"Python version mismatch. Expected {base_version}, "
                    f"got {version_str}"
                )
                
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to execute Python interpreter at {self.path}")
        except Exception as e:
            raise RuntimeError(f"Unexpected error during interpreter validation: {e}")
