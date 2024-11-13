#!/bin/bash
# install_python.sh - Install required Python versions

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Detect architecture
ARCH=$(uname -m)
echo "Installing Python versions for architecture: $ARCH"

# Install baseline Python first
BASELINE_VERSION="3.12.7"
if ! pyenv versions | grep "$BASELINE_VERSION" > /dev/null; then
    echo "Installing Python $BASELINE_VERSION..."
    if [ "$ARCH" = "aarch64" ]; then
        PYTHON_CONFIGURE_OPTS="--enable-optimizations --with-lto" pyenv install -s $BASELINE_VERSION
    else
        PYTHON_CONFIGURE_OPTS="--enable-optimizations" pyenv install -s $BASELINE_VERSION
    fi
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
        if [ "$ARCH" = "aarch64" ]; then
            PYTHON_CONFIGURE_OPTS="--enable-optimizations --with-lto" pyenv install -s $version --force
        else
            PYTHON_CONFIGURE_OPTS="--enable-optimizations" pyenv install -s $version --force
        fi
    fi
done

pyenv rehash 