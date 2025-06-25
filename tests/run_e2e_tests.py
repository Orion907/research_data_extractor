#!/usr/bin/env python3
# tests/run_e2e_tests.py
"""
Comprehensive E2E Test Runner for Refactored Streamlit Application

This script orchestrates running all E2E tests and provides detailed reporting
on the health of the modular Streamlit architecture.

Usage:
    # Run all E2E tests
    python tests/run_e2e_tests.py
    
    # Run specific test suite
    python tests/run_e2e_tests.py --suite=integration
    
    # Run with coverage
    python tests/run_e2e_tests.py --coverage
    
    # Run browser tests (requires selenium)
    python tests/run_e2e_tests.py --browser
"""

import os
import sys
import argparse
import subprocess
import time
import logging
import json
from pathlib import Path
from datetime import datetime
import tempfile

# Add project root to path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(project_root / "tests" / "e2e_test.log")
    ]
)
logger = logging.getLogger(__name__)


class E2ETestRunner:
    """Comprehensive E2E test runner for the refactored Streamlit application"""
    
    def __init__(self):
        self.project_root = project_root
        self.test_dir = self.project_root / "tests"
        self.results = {
            'start_time': datetime.now(),
            'test_suites': {},
            'summary': {},
            'errors': []
        }
        
        # Test configurations
        self.test_suites = {
            'integration': {
                'description': 'Module integration and component tests',
                'files': ['test_streamlit_e2e.py'],
                'markers': ['e2e'],
                'timeout': 300
            },
            'workflow': {
                'description': 'UI workflow and user interaction tests', 
                'files': ['test_streamlit_ui_workflows.py'],
                'markers': ['workflow'],
                'timeout': 300
            },
            'browser': {
                'description': 'Browser-based UI tests with Selenium',
                'files': ['test_streamlit_browser_e2e.py'],
                'markers': ['browser'],
                'timeout': 600,
                'requires': ['selenium']
            },
            'performance': {
                'description': 'Performance and resource usage tests',
                'files': ['test_streamlit_e2e.py'],
                'markers': ['performance'],
                'timeout': 180
            }
        }
    
    def check_dependencies(self, suite_name):
        """Check if dependencies for a test suite are available"""
        suite = self.test_suites.get(suite_name, {})
        requires = suite.get('requires', [])
        
        missing_deps = []
        for dep in requires:
            try:
                __import__(dep)
            except ImportError:
                missing_deps.append(dep)
        
        if missing_deps:
            logger.warning(f"Missing dependencies for {suite_name}: {missing_deps}")
            return False
        
        return True
    
    def run_pytest_suite(self, suite_name, coverage=False):
        """Run a specific pytest suite"""
        suite = self.test_suites.get(suite_name)
        if not suite:
            logger.error(f"Unknown test suite: {suite_name}")
            return False
        
        # Check dependencies
        if not self.check_dependencies(suite_name):
            logger.info(f"Skipping {suite_name} due to missing dependencies")
            self.results['test_suites'][suite_name] = {
                'status': 'skipped',
                'reason': 'missing dependencies'
            }
            return True
        
        logger.info(f"Running {suite_name} test suite: {suite['description']}")
        
        # Build pytest command
        cmd = [sys.executable, '-m', 'pytest']
        
        # Add test files
        for test_file in suite['files']:
            test_path = self.test_dir / test_file
            if test_path.exists():
                cmd.append(str(test_path))
        
        # Add markers
        if suite.get('markers'):
            markers = ' or '.join(suite['markers'])
            cmd.extend(['-m', markers])
        
        # Add coverage if requested
        if coverage:
            cmd.extend([
                '--cov=src',
                '--cov-report=term-missing',
                '--cov-report=html:htmlcov'
            ])
        
        # Add verbose output
        cmd.extend(['-v', '--tb=short'])
        
        # Set timeout
        timeout = suite.get('timeout', 300)
        
        try:
            start_time = time.time()
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            end_time = time.time()
            
            # Record results
            self.results['test_suites'][suite_name] = {
                'status': 'passed' if result.returncode == 0 else 'failed',
                'duration': end_time - start_time,
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
            if result.returncode == 0:
                logger.info(f"✅ {suite_name} tests passed ({end_time - start_time:.1f}s)")
            else:
                logger.error(f"❌ {suite_name} tests failed ({end_time - start_time:.1f}s)")
                logger.error(f"Error output: {result.stderr}")
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            logger.error(f"❌ {suite_name} tests timed out after {timeout}s")
            self.results['test_suites'][suite_name] = {
                'status': 'timeout',
                'timeout': timeout
            }
            return False
        
        except Exception as e:
            logger.error(f"❌ Error running {suite_name} tests: {e}")
            self.results['test_suites'][suite_name] = {
                'status': 'error',
                'error': str(e)
            }
            return False
    
    def run_module_import_test(self):
        """Test that all refactored modules can be imported"""
        logger.info("Testing module imports...")
        
        modules_to_test = [
            'src.app.session_state',
            'src.app.config_loader', 
            'src.processing.document_processor',
            'src.processing.extraction_engine',
            'src.processing.batch_coordinator',
            'src.ui.pages.extraction_page',
            'src.ui.pages.batch_page',
            'src.ui.pages.annotation_page',
            'src.ui.pages.analytics_page'
        ]
        
        import_results = {}
        for module in modules_to_test:
            try:
                __import__(module)
                import_results[module] = 'success'
                logger.info(f"✅ {module}")
            except Exception as e:
                import_results[module] = str(e)
                logger.error(f"❌ {module}: {e}")
        
        self.results['module_imports'] = import_results
        
        success_count = sum(1 for status in import_results.values() if status == 'success')
        total_count = len(import_results)
        
        logger.info(f"Module import test: {success_count}/{total_count} successful")
        return success_count == total_count
    
    def run_streamlit_syntax_check(self):
        """Check Streamlit app syntax without running it"""
        logger.info("Checking Streamlit app syntax...")
        
        try:
            cmd = [sys.executable, '-m', 'py_compile', str(self.project_root / 'streamlit_app.py')]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Streamlit app syntax is valid")
                self.results['syntax_check'] = 'passed'
                return True
            else:
                logger.error(f"❌ Streamlit app syntax error: {result.stderr}")
                self.results['syntax_check'] = f'failed: {result.stderr}'
                return False
                
        except Exception as e:
            logger.error(f"❌ Error checking syntax: {e}")
            self.results['syntax_check'] = f'error: {e}'
            return False
    
    def check_test_environment(self):
        """Check test environment setup"""
        logger.info("Checking test environment...")
        
        env_checks = {
            'python_version': sys.version,
            'project_root': str(self.project_root),
            'test_directory': str(self.test_dir),
            'streamlit_app_exists': (self.project_root / 'streamlit_app.py').exists(),
            'config_exists': (self.project_root / 'config').exists(),
            'src_directory_exists': (self.project_root / 'src').exists()
        }
        
        # Check required packages
        required_packages = ['streamlit', 'pytest', 'pandas', 'pathlib']
        package_status = {}
        
        for package in required_packages:
            try:
                __import__(package)
                package_status[package] = 'available'
            except ImportError:
                package_status[package] = 'missing'
        
        env_checks['packages'] = package_status
        self.results['environment'] = env_checks
        
        # Report environment status
        for check, status in env_checks.items():
            if check == 'packages':
                continue
            if isinstance(status, bool):
                status_icon = "✅" if status else "❌"
                logger.info(f"{status_icon} {check}: {status}")
            else:
                logger.info(f"ℹ️  {check}: {status}")
        
        # Report package status
        for package, status in package_status.items():
            status_icon = "✅" if status == 'available' else "❌"
            logger.info(f"{status_icon} {package}: {status}")
        
        return True
    
    def generate_report(self):
        """Generate comprehensive test report"""
        self.results['end_time'] = datetime.now()
        self.results['duration'] = (self.results['end_time'] - self.results['start_time']).total_seconds()
        
        # Calculate summary
        total_suites = len(self.results['test_suites'])
        passed_suites = sum(1 for suite in self.results['test_suites'].values() 
                           if suite.get('status') == 'passed')
        failed_suites = sum(1 for suite in self.results['test_suites'].values()
                           if suite.get('status') == 'failed') 
        skipped_suites = sum(1 for suite in self.results['test_suites'].values()
                            if suite.get('status') == 'skipped')
        
        self.results['summary'] = {
            'total_suites': total_suites,
            'passed_suites': passed_suites,
            'failed_suites': failed_suites,
            'skipped_suites': skipped_suites,
            'success_rate': (passed_suites / total_suites * 100) if total_suites > 0 else 0
        }
        
        # Print summary
        logger.info("\n" + "="*60)
        logger.info("E2E TEST SUMMARY")
        logger.info("="*60)
        logger.info(f"Duration: {self.results['duration']:.1f} seconds")
        logger.info(f"Test Suites: {total_suites}")
        logger.info(f"✅ Passed: {passed_suites}")
        logger.info(f"❌ Failed: {failed_suites}")
        logger.info(f"⏭️  Skipped: {skipped_suites}")
        logger.info(f"Success Rate: {self.results['summary']['success_rate']:.1f}%")
        
        # Module import summary
        if 'module_imports' in self.results:
            import_success = sum(1 for status in self.results['module_imports'].values() 
                               if status == 'success')
            import_total = len(self.results['module_imports'])
            logger.info(f"Module Imports: {import_success}/{import_total}")
        
        # Syntax check summary
        if 'syntax_check' in self.results:
            syntax_status = "✅ Passed" if self.results['syntax_check'] == 'passed' else "❌ Failed"
            logger.info(f"Syntax Check: {syntax_status}")
        
        logger.info("="*60)
        
        # Save detailed report
        report_file = self.project_root / "tests" / "e2e_test_report.json"
        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        logger.info(f"Detailed report saved to: {report_file}")
        
        return self.results['summary']['success_rate'] == 100.0
    
    def run_all_tests(self, suites=None, coverage=False, browser=False):
        """Run all E2E tests"""
        logger.info("Starting comprehensive E2E test run...")
        
        # Check environment
        self.check_test_environment()
        
        # Test module imports
        self.run_module_import_test()
        
        # Check syntax
        self.run_streamlit_syntax_check()
        
        # Determine which suites to run
        if suites:
            suites_to_run = [s for s in suites if s in self.test_suites]
        else:
            suites_to_run = ['integration', 'workflow', 'performance']
            if browser:
                suites_to_run.append('browser')
        
        # Run test suites
        for suite_name in suites_to_run:
            self.run_pytest_suite(suite_name, coverage=coverage)
        
        # Generate report
        return self.generate_report()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Run E2E tests for refactored Streamlit app')
    parser.add_argument('--suite', choices=['integration', 'workflow', 'browser', 'performance'],
                       action='append', help='Specific test suite to run')
    parser.add_argument('--coverage', action='store_true', help='Run with coverage reporting')
    parser.add_argument('--browser', action='store_true', help='Include browser tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create test runner
    runner = E2ETestRunner()
    
    # Run tests
    success = runner.run_all_tests(
        suites=args.suite,
        coverage=args.coverage,
        browser=args.browser
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()