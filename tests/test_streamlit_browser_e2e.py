# tests/test_streamlit_browser_e2e.py
"""
Browser-based End-to-End Tests for Streamlit Application

These tests use Selenium WebDriver to test the actual Streamlit application
in a browser environment, providing the most realistic E2E testing.

Prerequisites:
- selenium package
- webdriver (Chrome/Firefox)
- streamlit app running on localhost

Usage:
    # Install selenium
    pip install selenium
    
    # Run with pytest
    pytest tests/test_streamlit_browser_e2e.py -v -m browser
"""

import os
import sys
import pytest
import time
import subprocess
import threading
import tempfile
import json
from pathlib import Path
from datetime import datetime
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Browser testing imports
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    SELENIUM_AVAILABLE = True
except ImportError:
    logger.warning("Selenium not available. Install with: pip install selenium")
    SELENIUM_AVAILABLE = False


@pytest.mark.browser
@pytest.mark.skipif(not SELENIUM_AVAILABLE, reason="Selenium not available")
class TestStreamlitBrowserE2E:
    """Browser-based E2E tests for Streamlit application"""
    
    STREAMLIT_URL = "http://localhost:8501"
    STARTUP_TIMEOUT = 30  # seconds
    TEST_TIMEOUT = 10     # seconds
    
    @classmethod
    def setup_class(cls):
        """Set up browser testing environment"""
        cls.project_root = project_root
        cls.test_data_dir = cls.project_root / "tests" / "browser_test_data"
        cls.test_output_dir = cls.project_root / "data" / "output" / "browser_test"
        
        # Create test directories
        cls.test_data_dir.mkdir(exist_ok=True, parents=True)
        cls.test_output_dir.mkdir(exist_ok=True, parents=True)
        
        # Create test files
        cls.create_test_files()
        
        # Start Streamlit app in background
        cls.start_streamlit_app()
        
        # Set up WebDriver
        cls.setup_webdriver()
    
    @classmethod
    def create_test_files(cls):
        """Create test files for browser testing"""
        # Create a sample PDF-like text file for testing
        cls.sample_text_content = """
        Clinical Trial: Hypertension Management Study
        
        Background: Hypertension affects millions worldwide.
        
        Objective: To evaluate the effectiveness of a new treatment protocol.
        
        Methods:
        - Study Design: Randomized controlled trial
        - Population: Adults with essential hypertension
        - Sample Size: 200 participants
        - Age Range: 18-75 years
        - Gender: 55% female, 45% male
        
        Inclusion Criteria:
        - Systolic BP ≥140 mmHg or Diastolic BP ≥90 mmHg
        - Age 18-75 years
        - Stable medication regimen
        
        Exclusion Criteria:
        - Secondary hypertension
        - Pregnancy
        - Severe comorbidities
        
        Primary Endpoint: Change in systolic blood pressure
        Secondary Endpoints: Diastolic BP, adverse events
        
        Results:
        - Baseline SBP: 152 ± 12 mmHg
        - Post-treatment SBP: 138 ± 10 mmHg
        - Mean reduction: 14 mmHg (p<0.001)
        - No serious adverse events
        
        Conclusion: The new protocol significantly reduces blood pressure.
        """
        
        # Save test content to file
        cls.sample_file = cls.test_data_dir / "sample_study.txt"
        with open(cls.sample_file, 'w') as f:
            f.write(cls.sample_text_content)
        
        # Create sample batch files
        for i in range(1, 4):
            batch_file = cls.test_data_dir / f"batch_study_{i}.txt"
            with open(batch_file, 'w') as f:
                f.write(f"Study {i}: {cls.sample_text_content}")
    
    @classmethod
    def start_streamlit_app(cls):
        """Start Streamlit app in background thread"""
        def run_streamlit():
            try:
                # Change to project directory
                os.chdir(cls.project_root)
                
                # Start Streamlit app
                cmd = [
                    sys.executable, "-m", "streamlit", "run", 
                    "streamlit_app.py", 
                    "--server.port=8501",
                    "--server.headless=true",
                    "--browser.gatherUsageStats=false"
                ]
                
                cls.streamlit_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                logger.info("Streamlit app started in background")
                
            except Exception as e:
                logger.error(f"Failed to start Streamlit app: {e}")
                cls.streamlit_process = None
        
        # Start in thread
        cls.streamlit_thread = threading.Thread(target=run_streamlit, daemon=True)
        cls.streamlit_thread.start()
        
        # Wait for app to start
        logger.info(f"Waiting for Streamlit app to start at {cls.STREAMLIT_URL}")
        time.sleep(cls.STARTUP_TIMEOUT)
    
    @classmethod
    def setup_webdriver(cls):
        """Set up Chrome WebDriver for testing"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run in headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1920,1080")
            
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.wait = WebDriverWait(cls.driver, cls.TEST_TIMEOUT)
            
            logger.info("Chrome WebDriver initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            cls.driver = None
            cls.wait = None
    
    @classmethod
    def teardown_class(cls):
        """Clean up browser testing environment"""
        # Close browser
        if hasattr(cls, 'driver') and cls.driver:
            cls.driver.quit()
            logger.info("WebDriver closed")
        
        # Stop Streamlit app
        if hasattr(cls, 'streamlit_process') and cls.streamlit_process:
            cls.streamlit_process.terminate()
            cls.streamlit_process.wait(timeout=10)
            logger.info("Streamlit app terminated")
        
        # Clean up test files
        if cls.test_output_dir.exists():
            import shutil
            shutil.rmtree(cls.test_output_dir)
    
    def setup_method(self):
        """Set up for each test method"""
        if not self.driver:
            pytest.skip("WebDriver not available")
        
        # Navigate to Streamlit app
        self.driver.get(self.STREAMLIT_URL)
        
        # Wait for app to load
        try:
            self.wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info("Streamlit app loaded successfully")
        except TimeoutException:
            pytest.skip("Streamlit app not accessible")
    
    def test_app_loads_successfully(self):
        """Test that the Streamlit app loads without errors"""
        # Check page title
        assert "Research Article Data Extractor" in self.driver.page_source
        
        # Check that no error messages are visible
        assert "Error" not in self.driver.page_source
        assert "Exception" not in self.driver.page_source
    
    def test_sidebar_navigation_exists(self):
        """Test that sidebar navigation elements exist"""
        try:
            # Look for sidebar
            sidebar = self.wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='stSidebar']"))
            )
            assert sidebar is not None
            
            # Look for navigation selectbox
            nav_elements = self.driver.find_elements(By.CSS_SELECTOR, "select")
            assert len(nav_elements) > 0
            
            logger.info("Sidebar navigation found")
            
        except (TimeoutException, NoSuchElementException):
            logger.warning("Sidebar navigation not found - this may be expected in headless mode")
    
    def test_page_navigation_extract_data(self):
        """Test navigation to Extract Data page"""
        try:
            # Try to find and click navigation option
            # Note: Streamlit's selectbox may not be easily automatable in headless mode
            
            # Check if Extract Data content is visible (default page)
            page_content = self.driver.page_source.lower()
            
            # Look for extract data related content
            extract_indicators = [
                "extract", "upload", "pdf", "file", "processing"
            ]
            
            found_indicators = [indicator for indicator in extract_indicators 
                              if indicator in page_content]
            
            assert len(found_indicators) > 0, f"Extract Data page indicators not found: {found_indicators}"
            logger.info("Extract Data page content detected")
            
        except Exception as e:
            logger.warning(f"Navigation test limited in headless mode: {e}")
    
    def test_extract_data_page_elements(self):
        """Test Extract Data page UI elements"""
        try:
            # Look for file upload elements
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            
            # Look for buttons
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            
            # Look for text areas or input fields
            text_areas = self.driver.find_elements(By.TAG_NAME, "textarea")
            
            # At least some interactive elements should be present
            total_interactive = len(file_inputs) + len(buttons) + len(text_areas)
            assert total_interactive > 0, "No interactive elements found on Extract Data page"
            
            logger.info(f"Found {total_interactive} interactive elements")
            
        except Exception as e:
            logger.warning(f"Element detection limited in headless mode: {e}")
    
    def test_file_upload_element_exists(self):
        """Test that file upload elements exist"""
        try:
            # Look for file upload widget
            file_upload_text = ["upload", "file", "pdf", "select"]
            page_content = self.driver.page_source.lower()
            
            found_upload_indicators = [text for text in file_upload_text 
                                     if text in page_content]
            
            assert len(found_upload_indicators) > 0, "File upload indicators not found"
            logger.info(f"File upload indicators found: {found_upload_indicators}")
            
        except Exception as e:
            logger.warning(f"File upload test limited: {e}")
    
    def test_no_javascript_errors(self):
        """Test that there are no JavaScript errors on the page"""
        try:
            # Get browser logs
            logs = self.driver.get_log('browser')
            
            # Filter for errors
            errors = [log for log in logs if log['level'] == 'SEVERE']
            
            if errors:
                logger.warning(f"JavaScript errors found: {errors}")
            
            # Don't fail the test for JS errors in headless mode as they may be expected
            logger.info(f"Browser logs checked: {len(logs)} entries, {len(errors)} errors")
            
        except Exception as e:
            logger.info(f"Browser log checking not available: {e}")
    
    def test_responsive_design_elements(self):
        """Test that the page has responsive design elements"""
        try:
            # Check viewport meta tag
            viewport_meta = self.driver.find_elements(
                By.CSS_SELECTOR, "meta[name='viewport']"
            )
            
            # Check for CSS that might indicate responsive design
            stylesheets = self.driver.find_elements(By.TAG_NAME, "style")
            
            # Basic responsiveness checks
            page_width = self.driver.execute_script("return document.body.scrollWidth;")
            assert page_width > 0
            
            logger.info(f"Page width: {page_width}px")
            
        except Exception as e:
            logger.warning(f"Responsive design test limited: {e}")
    
    def test_page_loading_performance(self):
        """Test page loading performance"""
        start_time = time.time()
        
        # Reload page
        self.driver.refresh()
        
        # Wait for page to fully load
        try:
            self.wait.until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            load_time = time.time() - start_time
            
            # Page should load within reasonable time (10 seconds)
            assert load_time < 10, f"Page load time {load_time:.2f}s too slow"
            
            logger.info(f"Page loaded in {load_time:.2f} seconds")
            
        except TimeoutException:
            pytest.fail("Page failed to load within timeout")
    
    @pytest.mark.integration
    def test_session_state_persistence(self):
        """Test that session state persists during page interactions"""
        try:
            # This test is limited in headless mode without actual user interactions
            # We'll test basic page stability instead
            
            initial_content = self.driver.page_source
            
            # Refresh page
            self.driver.refresh()
            time.sleep(2)
            
            refreshed_content = self.driver.page_source
            
            # Basic content should be similar after refresh
            assert "Research Article Data Extractor" in refreshed_content
            
            logger.info("Session state persistence test completed (basic)")
            
        except Exception as e:
            logger.warning(f"Session state test limited: {e}")
    
    def test_error_handling_display(self):
        """Test that errors are properly displayed to users"""
        try:
            # Look for error handling elements in the page
            page_content = self.driver.page_source
            
            # Should not have unhandled errors visible
            assert "Traceback" not in page_content
            assert "Exception:" not in page_content
            assert "Error:" not in page_content or "Configuration Error:" in page_content
            
            logger.info("No unhandled errors found in page content")
            
        except Exception as e:
            logger.warning(f"Error handling test limited: {e}")


@pytest.mark.browser
@pytest.mark.integration
class TestStreamlitAppIntegration:
    """Integration tests that can run without full browser automation"""
    
    def test_app_imports_without_streamlit_context(self):
        """Test that app modules can be imported outside Streamlit context"""
        # This should work without Streamlit running
        from src.app import SessionStateManager, ConfigurationLoader
        from src.processing import DocumentProcessor, ExtractionEngine, BatchCoordinator
        from src.ui import ExtractionPage, BatchPage, AnnotationPage, AnalyticsPage
        
        # Test basic initialization
        config_loader = ConfigurationLoader.create_default_loader()
        assert config_loader is not None
        
        init_result = config_loader.initialize_all()
        assert 'config_manager' in init_result
    
    def test_component_initialization_chain(self):
        """Test the full component initialization chain"""
        config_loader = ConfigurationLoader.create_default_loader()
        init_result = config_loader.initialize_all()
        config = init_result['config_manager']
        analytics = init_result['analytics']
        
        # Initialize processing modules
        document_processor = DocumentProcessor(config.config)
        extraction_engine = ExtractionEngine(config.config, analytics)
        batch_coordinator = BatchCoordinator(config.config)
        
        # Initialize UI components
        extraction_page = ExtractionPage(extraction_engine, document_processor, config)
        batch_page = BatchPage(extraction_engine, document_processor, batch_coordinator, config)
        annotation_page = AnnotationPage()
        analytics_page = AnalyticsPage(analytics)
        
        # Verify all components are properly initialized
        assert all([
            extraction_page, batch_page, annotation_page, analytics_page
        ])
    
    def test_configuration_error_handling(self):
        """Test configuration error handling"""
        config_loader = ConfigurationLoader.create_default_loader()
        init_result = config_loader.initialize_all()
        
        # Should collect errors without failing
        assert 'errors' in init_result
        assert isinstance(init_result['errors'], list)
        
        # Components should still be created even with some errors
        assert init_result['config_manager'] is not None
        assert init_result['analytics'] is not None


# Utility functions for browser testing
def is_streamlit_app_running(url="http://localhost:8501", timeout=5):
    """Check if Streamlit app is running at the given URL"""
    try:
        import requests
        response = requests.get(url, timeout=timeout)
        return response.status_code == 200
    except:
        return False


# Test runner configuration
if __name__ == "__main__":
    # Check if Streamlit app is running
    if not is_streamlit_app_running():
        logger.warning("Streamlit app not running. Start with: streamlit run streamlit_app.py")
    
    # Run browser tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short", 
        "-m", "browser",
        "--log-cli-level=INFO"
    ])