# tests/run_integration_tests.py
import os
import sys
import unittest
import logging
import importlib
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('integration_test_results.log')
    ]
)
logger = logging.getLogger(__name__)

def run_integration_tests():
    """Run all integration tests for the project"""
    # Record start time
    start_time = datetime.now()
    logger.info(f"Starting integration tests at {start_time}")
    
    # Create a test suite
    suite = unittest.TestSuite()
    
    # Define test modules to run
    test_modules = [
        'test_project_structure',
        'test_pdf_integration',
        'test_llm_clients',
        'test_data_extraction',
        'test_csv_export',
        'test_prompt_management',
        'test_analytics',
        'test_integration_workflow'
    ]
    
    # Load and add tests from each module
    for module_name in test_modules:
        try:
            # Import the module from tests package
            module_path = f'tests.{module_name}'
            module = importlib.import_module(module_path)
            
            # Find all test cases in the module
            for name in dir(module):
                obj = getattr(module, name)
                if isinstance(obj, type) and issubclass(obj, unittest.TestCase) and obj is not unittest.TestCase:
                    # Add all test methods from this test case
                    tests = unittest.defaultTestLoader.loadTestsFromTestCase(obj)
                    suite.addTests(tests)
                    logger.info(f"Added tests from {module_path}.{name}")
        except ImportError as e:
            logger.error(f"Error importing test module {module_name}: {str(e)}")
            logger.error("Skipping this module")
    
    # Run the tests
    logger.info(f"Running {suite.countTestCases()} tests from {len(test_modules)} modules")
    
    # Create a test runner that writes results to a file
    result_file = os.path.join('test_results.txt')
    with open(result_file, 'w') as f:
        runner = unittest.TextTestRunner(verbosity=2, stream=f)
        result = runner.run(suite)
    
    # Log the results
    logger.info(f"Tests run: {result.testsRun}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Skipped: {len(result.skipped)}")
    
    # Calculate and log duration
    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"Completed integration tests in {duration}")
    
    # Log details of any failures or errors
    if result.failures:
        logger.error("Test failures:")
        for test, traceback in result.failures:
            logger.error(f"  {test}")
            logger.error(f"  {traceback}")
    
    if result.errors:
        logger.error("Test errors:")
        for test, traceback in result.errors:
            logger.error(f"  {test}")
            logger.error(f"  {traceback}")
    
    # Return True if all tests passed
    return len(result.failures) == 0 and len(result.errors) == 0

if __name__ == "__main__":
    success = run_integration_tests()
    
    if success:
        logger.info("INTEGRATION TESTS PASSED! 🎉")
        sys.exit(0)
    else:
        logger.error("INTEGRATION TESTS FAILED! 😱")
        sys.exit(1)