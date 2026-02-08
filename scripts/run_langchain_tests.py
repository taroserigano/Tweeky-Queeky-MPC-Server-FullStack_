"""
Master Test Runner for LangChain + LangGraph Implementation

Runs all test suites and provides aggregate results.

Usage: python scripts/run_langchain_tests.py
"""

import subprocess
import sys
import time
from datetime import datetime


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    BOLD = '\033[1m'
    END = '\033[0m'


def run_test_file(name: str, path: str) -> tuple[int, int, float, bool]:
    """Run a test file and return (passed, failed, time, success)"""
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD} Running: {name}{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")
    
    start = time.time()
    result = subprocess.run(
        [sys.executable, path],
        capture_output=True,
        text=True,
        cwd="c:/Users/taro/Documents/TEMP/PORTFOLIO/tweak-py/TweekySqueeky-FastAPI-Ecommer-App"
    )
    elapsed = time.time() - start
    
    # Parse output for pass/fail counts
    output = result.stdout + result.stderr
    
    passed = 0
    failed = 0
    
    # Look for summary lines - different formats in different test files
    for line in output.split('\n'):
        # Format: "Passed: X (Y%) | Failed: Z"
        if 'Passed:' in line and '|' in line:
            try:
                parts = line.split('|')
                for part in parts:
                    if 'Passed:' in part:
                        passed = int(part.split(':')[1].strip().split()[0])
                    elif 'Failed:' in part:
                        failed = int(part.split(':')[1].strip().split()[0])
            except:
                pass
        # Format: "Passed: X (Y%)"
        elif 'Passed:' in line and '(' in line and '|' not in line:
            try:
                passed = int(line.split('Passed:')[1].split('(')[0].strip())
            except:
                pass
        # Format: "Failed: X"
        elif 'Failed:' in line and '|' not in line:
            try:
                failed = int(line.split('Failed:')[1].strip().split()[0])
            except:
                pass
    
    # Print status
    success = result.returncode == 0 and failed == 0
    if success:
        status_str = f"{Colors.GREEN}✓ PASSED{Colors.END}"
    else:
        status_str = f"{Colors.RED}✗ FAILED{Colors.END}"
    
    print(f"   Status: {status_str}")
    print(f"   Tests: {Colors.GREEN}{passed} passed{Colors.END}, {Colors.RED if failed > 0 else ''}{failed} failed{Colors.END if failed > 0 else ''}")
    print(f"   Time: {elapsed:.1f}s")
    
    # If failed, show some output
    if failed > 0 or result.returncode != 0:
        print(f"\n   {Colors.YELLOW}Output:{Colors.END}")
        for line in output.split('\n')[-20:]:
            if line.strip():
                print(f"   {line}")
    
    return passed, failed, elapsed, success


def main():
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("=" * 70)
    print(" MASTER TEST RUNNER - LANGCHAIN + LANGGRAPH".center(70))
    print(f" Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".center(70))
    print("=" * 70)
    print(Colors.END)
    
    test_suites = [
        ("Comprehensive Tests (50 tests)", "scripts/test_comprehensive.py"),
        ("Edge Case Tests (41 tests)", "scripts/test_edge_cases.py"),
        ("API Endpoint Tests (25 tests)", "scripts/test_api_endpoints.py"),
    ]
    
    total_passed = 0
    total_failed = 0
    total_time = 0
    
    results = []
    
    for name, path in test_suites:
        passed, failed, elapsed, success = run_test_file(name, path)
        total_passed += passed
        total_failed += failed
        total_time += elapsed
        results.append((name, passed, failed, elapsed, success))
    
    # Final Summary
    print(f"\n{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD} FINAL SUMMARY{Colors.END}")
    print(f"{Colors.BLUE}{'='*70}{Colors.END}")
    
    print(f"\n{'Test Suite':<40} {'Passed':<10} {'Failed':<10} {'Time':<10}")
    print("-" * 70)
    for name, passed, failed, elapsed, success in results:
        if success:
            status = f"{Colors.GREEN}✓{Colors.END}"
        else:
            status = f"{Colors.RED}✗{Colors.END}"
        
        failed_str = f"{Colors.RED}{failed}{Colors.END}" if failed > 0 else str(failed)
        print(f"{status} {name:<38} {passed:<10} {failed_str:<10} {elapsed:.1f}s")
    
    print("-" * 70)
    total_failed_str = f"{Colors.RED}{total_failed}{Colors.END}" if total_failed > 0 else str(total_failed)
    print(f"  {'TOTAL':<38} {total_passed:<10} {total_failed_str:<10} {total_time:.1f}s")
    
    print(f"\n{'='*70}")
    if total_failed == 0:
        print(f"{Colors.BOLD}{Colors.GREEN}")
        print(" ✓✓✓ ALL TEST SUITES PASSED! ✓✓✓".center(70))
        print(f"   Total: {total_passed} tests in {total_time:.1f}s".center(70))
        print(Colors.END)
    else:
        print(f"{Colors.BOLD}{Colors.RED}")
        print(f" ✗ {total_failed} TESTS FAILED".center(70))
        print(f"   {total_passed} passed, {total_failed} failed in {total_time:.1f}s".center(70))
        print(Colors.END)
    print("=" * 70)
    
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
