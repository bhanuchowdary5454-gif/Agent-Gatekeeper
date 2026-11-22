"""
AirGuard AI - Top-Level Test Runner
Runs all unit and integration test scenarios.
"""

import unittest
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tests.test_scenarios import TestAirGuardGatekeeper

if __name__ == "__main__":
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAirGuardGatekeeper)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
