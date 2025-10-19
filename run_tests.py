#!/usr/bin/env python3
"""
Test runner script for the equity crisis alpha strategy.
"""

import argparse
import subprocess
import sys


def run_tests(test_type="all", verbose=False, coverage=False):
    """
    Run tests using pytest.

    Args:
        test_type: Type of tests to run (all, unit, functional, integration)
        verbose: Whether to run with verbose output
        coverage: Whether to run with coverage reporting
    """
    cmd = ["python", "-m", "pytest"]

    # Add test path based on type
    if test_type == "unit":
        cmd.append("tests/unit/")
    elif test_type == "functional":
        cmd.append("tests/functional/")
    elif test_type == "integration":
        cmd.append("tests/functional/test_config_integration.py")
    else:  # all
        cmd.append("tests/")

    # Add options
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")

    if coverage:
        cmd.extend(["--cov=strategies", "--cov-report=html", "--cov-report=term"])

    # Run the command
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run tests for equity crisis alpha strategy"
    )
    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=["all", "unit", "functional", "integration"],
        help="Type of tests to run",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Run with verbose output"
    )
    parser.add_argument(
        "-c", "--coverage", action="store_true", help="Run with coverage reporting"
    )

    args = parser.parse_args()

    print(f"Running {args.test_type} tests...")
    if args.coverage:
        print("Coverage reporting enabled...")

    exit_code = run_tests(args.test_type, args.verbose, args.coverage)

    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
