# End-to-End Testing for Refactored Streamlit Application

This document describes the comprehensive E2E testing suite for the modular Streamlit application created during the 5-phase refactoring project.

## Overview

The E2E testing suite validates that the refactored modular architecture works correctly end-to-end, ensuring:
- All modules integrate properly
- UI workflows function correctly
- Session state management works across pages
- Performance meets expectations
- Zero breaking changes from the refactoring

## Test Architecture

### Test Levels

1. **Module Integration Tests** (`test_streamlit_e2e.py`)
   - Tests module imports and initialization
   - Validates component dependency injection
   - Checks configuration loading and error handling
   - Performance and memory usage validation

2. **UI Workflow Tests** (`test_streamlit_ui_workflows.py`)
   - Tests individual page component functionality
   - Validates data flow between components
   - Checks file upload/download workflows
   - Tests annotation and analytics workflows

3. **Browser E2E Tests** (`test_streamlit_browser_e2e.py`)
   - Full browser automation with Selenium
   - Tests actual user interactions
   - Validates page navigation and UI elements
   - Checks responsive design and performance

## Quick Start

### Prerequisites

```bash
# Required packages
pip install pytest pytest-cov selenium

# Optional: Chrome WebDriver for browser tests
# Download from: https://chromedriver.chromium.org/
```

### Running Tests

```bash
# Run all E2E tests (except browser tests)
python tests/run_e2e_tests.py

# Run specific test suite
python tests/run_e2e_tests.py --suite=integration

# Run with coverage reporting
python tests/run_e2e_tests.py --coverage

# Run including browser tests (requires selenium + webdriver)
python tests/run_e2e_tests.py --browser

# Run individual test files
pytest tests/test_streamlit_e2e.py -v
pytest tests/test_streamlit_ui_workflows.py -v -m workflow
```

## Test Suites

### 1. Integration Test Suite

**File:** `test_streamlit_e2e.py`  
**Markers:** `@pytest.mark.e2e`

Tests the core modular architecture:

- **ApplicationStartup**: Module imports, configuration loading, component initialization
- **StreamlitAppNavigation**: Page navigation using Streamlit testing framework  
- **ModularComponentIntegration**: Component integration without full UI
- **WorkflowIntegration**: Document processing and extraction workflows
- **DataFlowIntegration**: Data flow between annotation and analytics components
- **PerformanceIntegration**: Startup performance and memory usage

```bash
# Run integration tests
pytest tests/test_streamlit_e2e.py -m e2e -v
```

### 2. Workflow Test Suite

**File:** `test_streamlit_ui_workflows.py`  
**Markers:** `@pytest.mark.workflow`

Tests specific UI workflows:

- **ExtractionPageWorkflow**: PDF upload, processing, and results display
- **BatchProcessingWorkflow**: Multiple file processing and progress tracking
- **AnnotationPageWorkflow**: Manual annotation and data editing
- **AnalyticsPageWorkflow**: Dashboard and report generation
- **CrossPageIntegration**: Session state and component communication

```bash
# Run workflow tests
pytest tests/test_streamlit_ui_workflows.py -m workflow -v
```

### 3. Browser Test Suite

**File:** `test_streamlit_browser_e2e.py`  
**Markers:** `@pytest.mark.browser`

Full browser automation tests:

- **StreamlitBrowserE2E**: Complete browser-based testing
- **StreamlitAppIntegration**: Integration tests without browser automation

```bash
# Run browser tests (requires Streamlit app running on localhost:8501)
streamlit run streamlit_app.py --server.port=8501 &
pytest tests/test_streamlit_browser_e2e.py -m browser -v
```

## Test Markers

Use pytest markers to run specific test categories:

```bash
# Run only integration tests
pytest -m e2e

# Run only workflow tests  
pytest -m workflow

# Run only browser tests
pytest -m browser

# Run only performance tests
pytest -m performance

# Exclude slow tests
pytest -m "not slow"

# Run multiple markers
pytest -m "e2e or workflow"
```

## Configuration

### pytest.ini

The `pytest.ini` file configures:
- Test discovery patterns
- Timeout settings
- Logging configuration
- Warning filters
- Coverage integration

### .coveragerc

The `.coveragerc` file configures:
- Source code coverage analysis
- File exclusions
- Report generation
- HTML and XML output

## Mock Data and Fixtures

The test suite includes comprehensive mock data:

- **Sample Research Articles**: Realistic clinical study content
- **Extraction Results**: Expected output from data extraction
- **Batch Processing Data**: Multiple document processing scenarios
- **Analytics Data**: Time series and performance metrics

Test fixtures are created in each test class's `setup_class()` method.

## Browser Testing Setup

### Prerequisites

1. **Install Selenium**:
   ```bash
   pip install selenium
   ```

2. **Install Chrome WebDriver**:
   - Download from: https://chromedriver.chromium.org/
   - Add to PATH or place in project directory

3. **Start Streamlit App**:
   ```bash
   streamlit run streamlit_app.py --server.port=8501
   ```

### Browser Test Features

- **Headless Mode**: Tests run without visible browser
- **Automatic Timeout**: Configurable timeouts for page loads
- **Error Detection**: JavaScript error monitoring
- **Performance Testing**: Page load time validation
- **Responsive Design**: Mobile/desktop layout testing

## Performance Testing

Performance tests validate:

- **Startup Time**: < 5 seconds for full initialization
- **Memory Usage**: < 100MB increase during initialization  
- **Page Load Time**: < 10 seconds for page navigation
- **Module Import Time**: Efficient module loading

```bash
# Run only performance tests
pytest -m performance -v
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run E2E tests
      run: python tests/run_e2e_tests.py --coverage
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Troubleshooting

### Common Issues

1. **Streamlit Import Errors**:
   ```bash
   # Install streamlit testing framework
   pip install streamlit>=1.28.0
   ```

2. **Module Import Failures**:
   ```bash
   # Ensure project root is in Python path
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   ```

3. **Browser Test Failures**:
   ```bash
   # Check Chrome WebDriver installation
   chromedriver --version
   
   # Ensure Streamlit app is running
   curl http://localhost:8501
   ```

4. **Configuration Errors**:
   ```bash
   # Check config files exist
   ls config/default.yaml config/development.yaml
   ```

### Debug Mode

Run tests with verbose output and debugging:

```bash
# Maximum verbosity
pytest tests/test_streamlit_e2e.py -vvv --tb=long --log-cli-level=DEBUG

# Capture output
pytest tests/test_streamlit_e2e.py -s --capture=no
```

## Test Coverage

Generate coverage reports:

```bash
# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term-missing

# View HTML report
open htmlcov/index.html
```

Expected coverage targets:
- **Module Integration**: > 90%
- **Component Initialization**: > 95%
- **Error Handling**: > 80%

## Reporting

### Test Results

The test runner generates:
- **Console Output**: Real-time test progress
- **JSON Report**: `tests/e2e_test_report.json`
- **Coverage Report**: `htmlcov/index.html`
- **Log File**: `tests/e2e_test.log`

### Report Contents

- Execution summary and success rates
- Performance metrics and timing
- Module import validation results
- Error details and stack traces
- Environment and dependency status

## Maintenance

### Adding New Tests

1. **Create test method** with appropriate marker:
   ```python
   @pytest.mark.e2e
   def test_new_feature(self):
       # Test implementation
   ```

2. **Update test suites** in `run_e2e_tests.py`:
   ```python
   'new_suite': {
       'description': 'New feature tests',
       'files': ['test_new_feature.py'],
       'markers': ['new_feature']
   }
   ```

3. **Add marker** to `pytest.ini`:
   ```ini
   markers =
       new_feature: Tests for new feature
   ```

### Updating for Architecture Changes

When modifying the modular architecture:

1. Update import paths in test files
2. Modify component initialization tests
3. Update mock data and fixtures
4. Adjust performance expectations
5. Update documentation

## Best Practices

1. **Isolation**: Each test should be independent
2. **Mocking**: Use mock LLM clients to avoid API calls
3. **Cleanup**: Remove test artifacts in teardown methods
4. **Timeouts**: Set appropriate timeouts for async operations
5. **Assertions**: Use descriptive assertion messages
6. **Documentation**: Document complex test scenarios

## Support

For questions or issues with the E2E testing suite:

1. Check the troubleshooting section above
2. Review test logs in `tests/e2e_test.log`
3. Run individual tests with verbose output
4. Verify environment setup and dependencies

The E2E testing suite ensures the refactored Streamlit application maintains high quality and reliability while providing confidence in the modular architecture.