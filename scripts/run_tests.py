#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test runner script with coverage reporting.

This script runs all tests and generates coverage reports in multiple formats.
"""

import sys
import subprocess
from pathlib import Path


def run_tests_with_coverage():
    """Run all tests with coverage measurement and reporting."""
    
    print("=" * 70)
    print("FastAPI AWS Lambda Integration - Test Suite with Coverage")
    print("=" * 70)
    
    # Change to project root
    project_root = Path(__file__).parent
    
    # Test commands
    commands = [
        # Run tests with coverage
        [
            sys.executable, "-m", "pytest",
            "src/",
            "--cov=src",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-report=xml",
            "-v",
            "--tb=short"
        ]
    ]
    
    for cmd in commands:
        print(f"\nRunning: {' '.join(cmd)}")
        print("-" * 70)
        
        result = subprocess.run(cmd, cwd=project_root)
        
        if result.returncode != 0:
            print(f"\nError: Command failed with return code {result.returncode}")
            return result.returncode
    
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print("\nTest Files:")
    test_files = list(project_root.glob("src/test_*.py"))
    for test_file in sorted(test_files):
        print(f"  ✓ {test_file.name}")
    
    print("\nCoverage Reports Generated:")
    print("  ✓ Terminal report (above)")
    print("  ✓ HTML report: htmlcov/index.html")
    print("  ✓ XML report: coverage.xml")
    
    print("\nNext Steps:")
    print("  1. Open htmlcov/index.html in a browser to view detailed coverage")
    print("  2. Review any uncovered lines")
    print("  3. Add tests for uncovered code")
    
    return 0


if __name__ == "__main__":
    sys.exit(run_tests_with_coverage())
