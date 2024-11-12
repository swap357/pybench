#!/bin/bash
# run_benchmarks.sh - Run benchmarks and generate reports

export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Default values
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

# Install dependencies for reporting
pip install plotly kaleido beautifulsoup4

# Run benchmarks
echo "Running benchmarks with $ITERATIONS iterations..."
python benchmark_runner.py --report both --iterations $ITERATIONS

# Generate timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="benchmark_results/${TIMESTAMP}"

# Create results directory
mkdir -p "$RESULTS_DIR"
cp benchmark_results.json "$RESULTS_DIR/"
cp -r scripts "$RESULTS_DIR/"

# Generate HTML report
python scripts/json_to_html.py \
    --input-file "$RESULTS_DIR/benchmark_results.json" \
    --output-dir "$RESULTS_DIR" \
    --run-id "${TIMESTAMP}"

echo "Benchmark results saved to: $RESULTS_DIR" 