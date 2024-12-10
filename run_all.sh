#!/bin/bash
# run_all.sh - Main script to run everything
# Usage: ./run_all.sh [--iterations N] [--no-build] [--arch armv8|armv9]

# Set default values
ITERATIONS=5
BUILD_FROM_SOURCE=true
TARGET_ARCH="native"  # Default to native architecture

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --iterations) ITERATIONS="$2"; shift ;;
        --no-build) BUILD_FROM_SOURCE=false ;;
        --arch) 
            case "$2" in
                armv8|armv9) TARGET_ARCH="$2" ;;
                *) echo "Invalid architecture. Use armv8 or armv9"; exit 1 ;;
            esac
            shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Show configuration
echo "Running with configuration:"
echo "- Iterations: $ITERATIONS"
echo "- Build from source: $BUILD_FROM_SOURCE"
echo "- Target architecture: $TARGET_ARCH"

# Run setup
echo "Setting up environment..."
./scripts/setup_env.sh

# Install Python versions with target architecture
echo "Installing Python versions..."
./scripts/install_python.sh $TARGET_ARCH

# Run benchmarks
echo "Running benchmarks..."
./scripts/run_benchmarks.sh --iterations $ITERATIONS ${BUILD_FROM_SOURCE:+--no-build}

echo "Benchmark run complete!" 