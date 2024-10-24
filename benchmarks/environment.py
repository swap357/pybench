from typing import List, Dict
import subprocess
import sys
import platform
from pathlib import Path
import time

class PythonEnvironment:
    def __init__(self, version: str, path: str = None):
        self.version = version
        self.path = path or self._get_python_path(version)
        self._validate_interpreter()

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

    def _validate_interpreter(self):
        """Validate that the Python interpreter exists and is the correct version."""
        try:
            # First get the version string
            result = subprocess.run(
                [self.path, '-c', 'import sys; print(sys.version)'],
                capture_output=True,
                text=True,
                check=True
            )
            version_str = result.stdout.strip()
            
            # Special handling for free-threading build
            if self.version.endswith('t'):
                if 'free-threading' not in version_str:
                    raise RuntimeError(
                        f"Expected free-threading Python build, but got: {version_str}"
                    )
                # Remove 't' suffix for version comparison
                base_version = self.version[:-1]
                if base_version not in version_str:
                    raise RuntimeError(
                        f"Python version mismatch. Expected {base_version}, got {version_str}"
                    )
            else:
                # Regular Python version validation
                if self.version not in version_str:
                    raise RuntimeError(
                        f"Python version mismatch. Expected {self.version}, got {version_str}"
                    )
        except subprocess.CalledProcessError:
            raise RuntimeError(f"Failed to execute Python interpreter at {self.path}")

    def run_benchmark(self, script_path: str, args: List[str] = None) -> Dict:
        """Run a benchmark script with this Python interpreter."""
        cmd = [self.path, script_path] + (args or [])
        try:
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            end_time = time.time()
            return {
                'output': result.stdout,
                'duration': end_time - start_time,
                'version': self.version,
                'success': True
            }
        except subprocess.CalledProcessError as e:
            return {
                'output': e.stderr,
                'duration': None,
                'version': self.version,
                'success': False
            }
