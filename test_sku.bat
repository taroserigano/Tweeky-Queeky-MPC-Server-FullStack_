@echo off
REM Quick Test Script for SKU Functionality (Windows)

echo ==================================
echo   SKU Functionality Test Runner
echo ==================================
echo.

REM Run all tests
echo Running all SKU tests...
python tests\run_all_sku_tests.py

REM Check exit code
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==================================
    echo   ✅ ALL TESTS PASSED!
    echo ==================================
    echo.
    echo SKU functionality is working correctly.
    echo.
    echo Next steps:
    echo   1. Start backend: python start.py
    echo   2. Open browser: http://localhost:3000
    echo   3. View any product to see SKU displayed
    echo.
) else (
    echo.
    echo ==================================
    echo   ❌ SOME TESTS FAILED
    echo ==================================
    echo.
    echo Please review the test output above.
    echo.
)

pause
