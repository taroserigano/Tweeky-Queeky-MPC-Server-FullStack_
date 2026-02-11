"""
Master Test Runner - Runs all SKU functionality tests
"""

import asyncio
import subprocess
import sys
from pathlib import Path


def print_header(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def run_test_file(test_file, description):
    """Run a test file and return True if all tests passed"""
    print_header(description)
    
    try:
        result = subprocess.run(
            [sys.executable, test_file],
            capture_output=False,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"❌ Error running {test_file}: {e}")
        return False


def main():
    print_header("SKU FUNCTIONALITY - MASTER TEST SUITE")
    print("This will run all SKU functionality tests\n")
    
    results = {}
    
    # Test 1: Unit Tests
    unit_test_file = Path(__file__).parent / "test_sku_functionality.py"
    results["Unit Tests"] = run_test_file(
        str(unit_test_file),
        "UNIT TESTS - SKU Functionality"
    )
    
    # Test 2: Integration Tests (may skip if backend not running)
    integration_test_file = Path(__file__).parent / "test_sku_integration.py"
    results["Integration Tests"] = run_test_file(
        str(integration_test_file),
        "INTEGRATION TESTS - API Endpoints"
    )
    
    # Final Summary
    print_header("FINAL TEST SUMMARY")
    
    total_suites = len(results)
    passed_suites = sum(1 for v in results.values() if v)
    failed_suites = total_suites - passed_suites
    
    print(f"Test Suites Run: {total_suites}")
    print(f"Suites Passed: {passed_suites}")
    print(f"Suites Failed: {failed_suites}\n")
    
    for suite_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {suite_name}")
    
    print("\n" + "="*70)
    
    if all(results.values()):
        print("✅ ALL TESTS PASSED!")
        print("="*70)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("="*70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
