#!/usr/bin/env python3
"""
Test runner for Green-Ampt QGIS Plugin Test Suite
================================================

This script provides a convenient way to run the test suite with various options.

Usage:
    python run_tests.py [options]

Examples:
    # Run all tests
    python run_tests.py
    
    # Run only unit tests
    python run_tests.py --unit
    
    # Run with coverage
    python run_tests.py --coverage
    
    # Run specific test file
    python run_tests.py --file test_data_access.py
    
    # Run tests that don't require QGIS
    python run_tests.py --no-qgis
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(
        description="Run Green-Ampt Plugin Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Test selection options
    parser.add_argument(
        '--unit', 
        action='store_true',
        help='Run only unit tests'
    )
    parser.add_argument(
        '--integration',
        action='store_true', 
        help='Run only integration tests'
    )
    parser.add_argument(
        '--system',
        action='store_true',
        help='Run only system/end-to-end tests'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Run specific test file'
    )
    
    # Test environment options
    parser.add_argument(
        '--no-qgis',
        action='store_true',
        help='Skip tests that require QGIS environment'
    )
    parser.add_argument(
        '--no-ssurgo',
        action='store_true',
        help='Skip tests that require SSURGO data access'
    )
    parser.add_argument(
        '--mock-only',
        action='store_true',
        help='Run only tests with mocked dependencies'
    )
    
    # Output options
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Run tests with coverage reporting'
    )
    parser.add_argument(
        '--html-coverage',
        action='store_true',
        help='Generate HTML coverage report'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--quiet',
        '-q', 
        action='store_true',
        help='Quiet output'
    )
    
    # Performance options
    parser.add_argument(
        '--parallel',
        '-n',
        type=int,
        help='Run tests in parallel (requires pytest-xdist)'
    )
    parser.add_argument(
        '--fast',
        action='store_true',
        help='Skip slow tests'
    )
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd = ['python', '-m', 'pytest']
    
    # Add test selection
    if args.unit:
        cmd.append('tests/unit/')
    elif args.integration:
        cmd.append('tests/integration/')
    elif args.system:
        cmd.append('tests/system/')
    elif args.file:
        cmd.append(f'tests/{args.file}')
    else:
        cmd.append('tests/')
    
    # Add markers for filtering
    markers = []
    if args.no_qgis:
        markers.append('not requires_qgis')
    if args.no_ssurgo:
        markers.append('not requires_ssurgo')
    if args.mock_only:
        markers.append('mock_only')
    if args.fast:
        markers.append('not slow')
        
    if markers:
        cmd.extend(['-m', ' and '.join(markers)])
    
    # Add coverage options
    if args.coverage or args.html_coverage:
        cmd.extend(['--cov=green_ampt_plugin'])
        if args.html_coverage:
            cmd.extend(['--cov-report=html'])
        cmd.extend(['--cov-report=term-missing'])
    
    # Add output options
    if args.verbose:
        cmd.append('-v')
    elif args.quiet:
        cmd.append('-q')
    
    # Add performance options
    if args.parallel:
        cmd.extend(['-n', str(args.parallel)])
    
    # Set up environment
    setup_test_environment()
    
    # Run tests
    print(f"Running command: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\\nTests interrupted by user")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1


def setup_test_environment():
    """Set up the test environment."""
    # Add project root to Python path
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Set environment variables for testing
    os.environ['TESTING'] = 'true'
    os.environ['QGIS_TESTING'] = 'false'  # Default to no QGIS unless specified
    
    # Check for QGIS environment
    qgis_prefix = os.environ.get('QGIS_PREFIX_PATH')
    if qgis_prefix and Path(qgis_prefix).exists():
        os.environ['QGIS_TESTING'] = 'true'
        print(f"QGIS environment detected at: {qgis_prefix}")
    else:
        print("QGIS environment not detected - QGIS-dependent tests will be skipped")
    
    # Check for required dependencies
    check_dependencies()


def check_dependencies():
    """Check for required test dependencies."""
    required_packages = ['pytest', 'unittest']
    optional_packages = ['pytest-cov', 'pytest-xdist', 'psutil']
    
    missing_required = []
    missing_optional = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_required.append(package)
    
    for package in optional_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_optional.append(package)
    
    if missing_required:
        print(f"ERROR: Missing required packages: {missing_required}")
        print("Install with: pip install " + " ".join(missing_required))
        sys.exit(1)
    
    if missing_optional:
        print(f"INFO: Optional packages not found: {missing_optional}")
        print("Install for enhanced functionality: pip install " + " ".join(missing_optional))


def run_quick_tests():
    """Run a quick subset of tests for development.""" 
    cmd = [
        'python', '-m', 'pytest',
        'tests/unit/',
        '-m', 'not slow and not requires_qgis',
        '-v'
    ]
    
    setup_test_environment()
    return subprocess.run(cmd, check=False).returncode


def run_full_tests():
    """Run the complete test suite."""
    cmd = [
        'python', '-m', 'pytest',
        'tests/',
        '--cov=green_ampt_plugin',
        '--cov-report=html',
        '--cov-report=term-missing',
        '-v'
    ]
    
    setup_test_environment()
    return subprocess.run(cmd, check=False).returncode


if __name__ == '__main__':
    sys.exit(main())