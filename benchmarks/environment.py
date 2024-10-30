from typing import List, Dict
import subprocess
import sys
import platform
from pathlib import Path
import time
import os

class PythonEnvironment:
    def __init__(self, version: str, path: str = None):
        self.version = version
        self.path = path or self._get_python_path(version)
        self._validate_interpreter()
        self.is_free_threaded = self._check_free_threading()

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

    def run_benchmark(self, script_path: str, args: List[str] = None) -> Dict:
        """Run a benchmark script with this Python interpreter."""
        cmd = [self.path]
        
        # For free-threaded builds, disable GIL
        if self.is_free_threaded:
            if self.version.endswith('t'):
                # Disable GIL using command line option
                cmd.extend(['-X', 'nogil'])
        
        # Add script and any additional args
        cmd.append(script_path)
        if args:
            cmd.extend(args)

        try:
            # Set environment variables
            env = os.environ.copy()
            if self.is_free_threaded:
                if self.version.endswith('t'):
                    env['PYTHON_GIL'] = '0'  # Disable GIL
                else:
                    env['PYTHON_GIL'] = '1'  # Enable GIL
            
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                env=env
            )
            end_time = time.time()
            
            return {
                'output': result.stdout,
                'duration': end_time - start_time,
                'version': self.version,
                'success': True,
                'free_threaded': self.is_free_threaded
            }
        except subprocess.CalledProcessError as e:
            return {
                'output': e.stderr,
                'duration': None,
                'version': self.version,
                'success': False,
                'free_threaded': self.is_free_threaded
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
