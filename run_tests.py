import unittest
import os
import sys
import logging

# Disable logging during tests
logging.disable(logging.CRITICAL)

def run_tests():
    """Run all tests in the tests directory"""
    # Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add the script directory to the Python path
    sys.path.insert(0, script_dir)
    
    # Discover and run tests
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    
    # Run tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return exit code based on test result
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())
