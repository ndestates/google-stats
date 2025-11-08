#!/usr/bin/env python3
"""
Test runner script for Google Analytics reporting platform
Run tests with various options and configurations
"""

import os
import sys
import subprocess
import argparse


def run_tests(test_type=None, coverage=False, verbose=False, fail_fast=False):
    """Run the test suite with specified options"""

    cmd = [sys.executable, "-m", "pytest"]

    if test_type:
        if test_type == "unit":
            cmd.append("tests/test_ga4_client.py")
            cmd.append("tests/test_scripts/")
        elif test_type == "integration":
            cmd.append("tests/test_integration/")
        elif test_type == "scripts":
            cmd.append("tests/test_scripts/")
        else:
            cmd.append(f"tests/test_{test_type}.py")

    if coverage:
        cmd.extend(["--cov=src", "--cov=scripts", "--cov-report=term-missing"])

    if verbose:
        cmd.append("-v")

    if fail_fast:
        cmd.append("--tb=short")
        cmd.append("-x")

    print(f"Running command: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=os.path.dirname(__file__))


def run_specific_script_test(script_name):
    """Run tests for a specific script"""
    test_file = f"tests/test_scripts/test_{script_name}.py"
    if os.path.exists(test_file):
        cmd = [sys.executable, "-m", "pytest", test_file, "-v"]
        print(f"Running tests for {script_name}")
        return subprocess.run(cmd, cwd=os.path.dirname(__file__))
    else:
        print(f"No test file found for {script_name}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Run Google Analytics tests")
    parser.add_argument(
        "test_type",
        nargs="?",
        choices=["unit", "integration", "scripts", "all"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--script",
        help="Run tests for specific script (e.g., content_performance)"
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Run with coverage reporting"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--fail-fast", "-x",
        action="store_true",
        help="Stop on first failure"
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick tests only (skip slow/API tests)"
    )

    args = parser.parse_args()

    if args.script:
        result = run_specific_script_test(args.script)
        if result:
            sys.exit(result.returncode)
        else:
            sys.exit(1)

    # Run tests based on type
    if args.test_type == "all":
        # Run all tests
        result = run_tests(coverage=args.coverage, verbose=args.verbose, fail_fast=args.fail_fast)
    else:
        result = run_tests(args.test_type, args.coverage, args.verbose, args.fail_fast)

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()