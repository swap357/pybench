#!/bin/bash
# run_all.sh - Main script to run everything

# Set default values
ITERATIONS=5
BUILD_FROM_SOURCE=true

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --iterations) ITERATIONS="$2"; shift ;;
        --no-build) BUILD_FROM_SOURCE=false ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Run setup
echo "Setting up environment..."
./scripts/setup_env.sh

# Install Python versions
echo "Installing Python versions..."
./scripts/install_python.sh

# Run benchmarks
echo "Running benchmarks..."
./scripts/run_benchmarks.sh --iterations $ITERATIONS ${BUILD_FROM_SOURCE:+--no-build}

echo "Benchmark run complete!" 