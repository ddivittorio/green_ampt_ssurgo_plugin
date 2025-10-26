#!/bin/bash
#
# Test runner script for Green-Ampt Estimation Toolkit
# 
# This script runs the complete test suite and generates a summary report.
# It can output results to both the console and a log file.
#
# Usage:
#   ./scripts/run_tests.sh [OPTIONS]
#
# Options:
#   --log-file FILE    Write test results to specified log file
#   --verbose          Show detailed test output
#   --coverage         Generate coverage report (requires pytest-cov)
#   --help             Display this help message
#

set -e

# Default values
LOG_FILE=""
VERBOSE=""
COVERAGE=""

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --log-file)
            LOG_FILE="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE="-v"
            shift
            ;;
        --coverage)
            COVERAGE="--cov=green_ampt_tool --cov-report=term --cov-report=html"
            shift
            ;;
        --help)
            grep '^#' "$0" | grep -v '#!/bin/bash' | sed 's/^# //'
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Change to repository root
cd "$(dirname "$0")/.."

# Display header
echo "========================================"
echo "Green-Ampt Estimation Test Suite"
echo "========================================"
echo ""

# Check if pytest is available
if ! python -m pytest --version >/dev/null 2>&1; then
    echo "Error: pytest is not installed"
    echo "Install it with: pip install pytest"
    exit 1
fi

# Check if dependencies are installed
if ! python -c "import geopandas, pandas, numpy" >/dev/null 2>&1; then
    echo "Error: Required dependencies not installed"
    echo "Install them with: pip install -r requirements.txt"
    exit 1
fi

# Build pytest command as array
PYTEST_ARGS=(python -m pytest green_ampt_tool/tests/ --tb=short)
if [ -n "$VERBOSE" ]; then
    PYTEST_ARGS+=(-v)
fi
if [ -n "$COVERAGE" ]; then
    PYTEST_ARGS+=(--cov=green_ampt_tool --cov-report=term --cov-report=html)
fi

# Run tests
echo "Running tests..."
echo ""

if [ -n "$LOG_FILE" ]; then
    # Run tests and output to both console and log file
    "${PYTEST_ARGS[@]}" 2>&1 | tee "$LOG_FILE"
    EXIT_CODE=${PIPESTATUS[0]}
    echo ""
    echo "Test results written to: $LOG_FILE"
else
    # Run tests with console output only
    "${PYTEST_ARGS[@]}"
    EXIT_CODE=$?
fi

echo ""
echo "========================================"

# Exit with pytest's exit code
exit $EXIT_CODE
