#!/bin/bash
# install_python.sh - Install required Python versions
# Usage: ./install_python.sh [armv8|armv9]

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Detect architecture and handle target ISA
ARCH=$(uname -m)
TARGET_ISA=${1:-"native"}  # Use provided ISA or 'native' as default

echo "Installing Python versions for architecture: $ARCH"
echo "Target ISA: $TARGET_ISA"

# Set ISA-specific compiler flags if target is specified
if [ "$TARGET_ISA" = "armv8" ]; then
    export PYTHON_CFLAGS="-O3 -march=armv8-a+crypto+simd -mtune=generic"
    echo "Building for ARMv8 ISA"
elif [ "$TARGET_ISA" = "armv9" ]; then
    export PYTHON_CFLAGS="-O3 -march=armv9-a+sve2+sve -mtune=native"
    echo "Building for ARMv9 ISA"
fi

# Install baseline Python first
BASELINE_VERSION="3.12.7"
if ! pyenv versions | grep "$BASELINE_VERSION" > /dev/null; then
    echo "Installing Python $BASELINE_VERSION..."
    PYTHON_CONFIGURE_OPTS="--enable-optimizations" pyenv install -v -s $BASELINE_VERSION
fi

pyenv global $BASELINE_VERSION
python --version

# Install package
pip install -e .

# Get versions from benchmark runner
VERSIONS=$(python -c "from benchmark_runner import BenchmarkRunner; print(' '.join(BenchmarkRunner.PYTHON_VERSIONS.keys()))")

# Install all required versions
for version in $VERSIONS; do
    if ! pyenv versions | grep "$version" > /dev/null; then
        echo "Installing Python $version..."
        if [[ $version == *"t"* ]]; then
            # No-GIL Python build
            PYTHON_CONFIGURE_OPTS="--enable-optimizations --enable-shared --with-gil=disabled" pyenv install -v -s $version --force
        else
            PYTHON_CONFIGURE_OPTS="--enable-optimizations --enable-shared" pyenv install -v -s $version --force
        fi
    fi
done

# Verify builds
echo "Verifying Python builds:"
for version in $VERSIONS; do
    if pyenv versions | grep "$version" > /dev/null; then
        echo "Python $version:"
        pyenv shell $version
        python -c "
import sys
import platform
import sysconfig
print(f'Python {sys.version}')
print(f'Architecture: {platform.machine()}')
print(f'CFLAGS: {sysconfig.get_config_var(\"CFLAGS\")}')
"
    fi
done

pyenv rehash 