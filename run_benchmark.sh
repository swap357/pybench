#!/bin/bash
set -e

# Load pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"

# Get CPU info
TOTAL_CORES=$(nproc)

# Set CPU cores
if [ "$1" = "all" ]; then
  CORES_TO_USE=$TOTAL_CORES
else
  CORES_TO_USE=$1
  [ $CORES_TO_USE -gt $TOTAL_CORES ] && CORES_TO_USE=$TOTAL_CORES
fi

# Set thread limits
if [ "$2" != "0" ]; then
  THREAD_COUNT=$(( CORES_TO_USE * $2 ))
  export OMP_NUM_THREADS=$THREAD_COUNT
  export MKL_NUM_THREADS=$THREAD_COUNT
  export OPENBLAS_NUM_THREADS=$THREAD_COUNT
  export VECLIB_MAXIMUM_THREADS=$THREAD_COUNT
  export NUMEXPR_NUM_THREADS=$THREAD_COUNT
fi

cd ~/pybench

# Run benchmark
if [ "$3" = "yes" ]; then
  echo "Running with CPU pinning on cores 0-$((CORES_TO_USE - 1))"
  taskset -c 0-$((CORES_TO_USE - 1)) python benchmark_runner.py \
    --profile "$4" \
    --report-format both \
    --iterations "$5"
else
  echo "Running without CPU pinning, using $CORES_TO_USE cores"
  python benchmark_runner.py \
    --profile "$4" \
    --report-format both \
    --iterations "$5"
fi
