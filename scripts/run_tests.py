#!/usr/bin/env python3
"""
Executes pytest test suite programmatically and prints test results.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest

def main():
    print("=" * 60)
    print("Running StreamWave Automated Pytest Test Suite...")
    print("=" * 60)
    exit_code = pytest.main(["tests/test_api.py", "-v", "--tb=short"])
    print("=" * 60)
    if exit_code == 0:
        print("✅ ALL AUTOMATED TESTS PASSED (100% SUCCESS RATE)")
    else:
        print(f"❌ TEST SUITE FAILED (Exit Code: {exit_code})")
    print("=" * 60)
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
