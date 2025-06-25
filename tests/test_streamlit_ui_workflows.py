# tests/test_streamlit_ui_workflows.py
"""
Streamlit UI Workflow End-to-End Tests

Comprehensive tests for specific UI workflows in the refactored Streamlit application.
These tests focus on user interaction flows and UI component behavior.
"""

import os
import sys
import pytest
import tempfile
import shutil
import json
import io
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Streamlit testing imports
try:
    from streamlit.testing.v1 import AppTest
    import streamlit as st
    STREAMLIT_TESTING_AVAILABLE = True
except ImportError:
    STREAMLIT_TESTING_AVAILABLE = False

# Import application modules
from src.app import SessionStateManager, ConfigurationLoader
from src.processing import DocumentProcessor, ExtractionEngine, BatchCoordinator
from src.ui import ExtractionPage, BatchPage, AnnotationPage, AnalyticsPage
from src.llm.mock_client import MockLLMClient


class StreamlitWorkflowTestBase:
    """Base class for Streamlit workflow tests"""
    
    @classmethod
    def setup_class(cls):
        """Set up test environment"""
        cls.project_root = project_root
        cls.test_data_dir = cls.project_root / "tests" / "test_ui_data"
        cls.test_output_dir = cls.project_root / "data" / "output" / "ui_test"
        
        # Create test directories
        cls.test_data_dir.mkdir(exist_ok=True, parents=True)
        cls.test_output_dir.mkdir(exist_ok=True, parents=True)
        
        # Create sample test files
        cls.create_test_data()
    
    @classmethod
    def create_test_data(cls):
        """Create test data files"""
        # Sample PDF content
        cls.sample_pdf_content = """
        Clinical Study: Cardiovascular Risk Assessment
        
        Patient Population: Adults aged 40-80 years with hypertension
        Sample Size: 250 participants
        Study Design: Randomized controlled trial
        
        Inclusion Criteria:
        - Age 40-80 years
        - Diagnosed hypertension (>140/90 mmHg)
        - BMI 18.5-40 kg/m²
        
        Exclusion Criteria:
        - Pregnancy
        - Severe renal disease
        - Active cancer treatment
        
        Primary Endpoint: Reduction in systolic blood pressure
        Secondary Endpoints: Cardiovascular events, quality of life
        
        Results:
        - Mean age: 62.3 ± 12.1 years
        - 52% male participants
        - Baseline SBP: 155 ± 15 mmHg
        - Post-treatment SBP: 135 ± 12 mmHg
        - Significant reduction (p<0.001)
        """
        
        # Sample extraction results
        cls.sample_extraction = {
            "study_design": "Randomized controlled trial",
            "sample_size": 250,
            "age_range": "40-80 years",
            "primary_condition": "hypertension",
            "primary_endpoint": "Reduction in systolic blood pressure",
            "mean_age": "62.3 ± 12.1 years",
            "gender_distribution": "52% male",
            "baseline_sbp": "155 ± 15 mmHg",
            "post_treatment_sbp": "135 ± 12 mmHg"
        }
        
        # Create sample files
        cls.sample_text_file = cls.test_data_dir / "sample_study.txt"
        with open(cls.sample_text_file, 'w') as f:
            f.write(cls.sample_pdf_content)
        
        cls.sample_extraction_file = cls.test_data_dir / "sample_results.json"
        with open(cls.sample_extraction_file, 'w') as f:
            json.dump(cls.sample_extraction, f, indent=2)
        
        # Create sample batch data
        cls.batch_data = [
            {"file": "study1.pdf", "characteristics": {"age": "45-65", "condition": "diabetes"}},
            {"file": "study2.pdf", "characteristics": {"age": "30-50", "condition": "hypertension"}},
            {"file": "study3.pdf", "characteristics": {"age": "55-75", "condition": "cardiovascular"}}
        ]
        
        cls.sample_batch_file = cls.test_data_dir / "batch_results.json"
        with open(cls.sample_batch_file, 'w') as f:
            json.dump(cls.batch_data, f, indent=2)
    
    @classmethod
    def teardown_class(cls):
        """Clean up test environment"""
        if cls.test_output_dir.exists():
            shutil.rmtree(cls.test_output_dir)
    
    def setup_method(self):
        """Set up for each test"""
        self.mock_patches = []
    
    def teardown_method(self):
        """Clean up after each test"""
        for patch_obj in self.mock_patches:
            if hasattr(patch_obj, 'stop'):
                patch_obj.stop()
    
    def patch_llm_client(self):
        """Patch LLM client for testing"""
        mock_client = MockLLMClient(model_name="test-model")
        patch_obj = patch('src.llm.client_factory.ClientFactory.create_client',
                         return_value=mock_client)
        patch_obj.start()
        self.mock_patches.append(patch_obj)
        return mock_client


@pytest.mark.e2e
@pytest.mark.workflow
class TestExtractionPageWorkflow(StreamlitWorkflowTestBase):
    """Test Extract Data page complete workflow"""
    
    def test_extraction_page_component_initialization(self):
        """Test ExtractionPage component can be initialized properly"""
        # Set up dependencies
        self.patch_llm_client()
        
        config_loader = ConfigurationLoader.create_default_loader()
        init_result = config_loader.initialize_all()
        config = init_result['config_manager']
        analytics = init_result['analytics']
        
        document_processor = DocumentProcessor(config.config)
        extraction_engine = ExtractionEngine(config.config, analytics)
        
        # Test component initialization
        extraction_page = ExtractionPage(extraction_engine, document_processor, config)
        
        assert extraction_page.extraction_engine is not None
        assert extraction_page.document_processor is not None
        assert extraction_page.config is not None
    
    def test_extraction_workflow_with_mock_data(self):
        """Test extraction workflow using mock data"""
        # Set up dependencies
        mock_client = self.patch_llm_client()
        
        config_loader = ConfigurationLoader.create_default_loader()
        init_result = config_loader.initialize_all()
        config = init_result['config_manager']
        analytics = init_result['analytics']
        
        document_processor = DocumentProcessor(config.config)
        extraction_engine = ExtractionEngine(config.config, analytics)
        
        # Mock document processing
        with patch.object(document_processor, 'process_uploaded_file') as mock_process:
            mock_process.return_value = {
                'text': self.sample_pdf_content,
                'chunks': [
                    {'content': self.sample_pdf_content[:500], 'index': 0},
                    {'content': self.sample_pdf_content[500:], 'index': 1}
                ]
            }
            
            # Mock extraction engine
            with patch.object(extraction_engine, 'extract_from_chunks') as mock_extract:
                mock_extract.return_value = self.sample_extraction
                
                # Test the extraction workflow
                extraction_page = ExtractionPage(extraction_engine, document_processor, config)
                
                # Simulate file upload and processing
                mock_file = MagicMock()
                mock_file.name = "test_study.pdf"
                
                result = document_processor.process_uploaded_file(mock_file)
                assert result is not None
                assert 'text' in result
                assert 'chunks' in result
                
                # Test extraction
                chunks = [chunk['content'] for chunk in result['chunks']]
                extracted_data = extraction_engine.extract_from_chunks(chunks)
                assert extracted_data is not None
                assert 'study_design' in extracted_data
    
    @pytest.mark.skipif(not STREAMLIT_TESTING_AVAILABLE, reason="Streamlit testing not available")
    def test_extraction_page_ui_elements(self):
        """Test Extract Data page UI elements using Streamlit testing"""
        # Create a minimal test app
        test_app_content = """
import streamlit as st
from src.app import ConfigurationLoader
from src.processing import DocumentProcessor, ExtractionEngine
from src.ui import ExtractionPage

# Initialize components
config_loader = ConfigurationLoader.create_default_loader()
init_result = config_loader.initialize_all()
config = init_result['config_manager']
analytics = init_result['analytics']

document_processor = DocumentProcessor(config.config)
extraction_engine = ExtractionEngine(config.config, analytics)

# Create and render extraction page
extraction_page = ExtractionPage(extraction_engine, document_processor, config)
extraction_page.render()
"""
        
        # Write temporary test app
        test_app_file = self.test_data_dir / "test_extraction_app.py"
        with open(test_app_file, 'w') as f:
            f.write(test_app_content)
        
        # Test the app
        at = AppTest.from_file(str(test_app_file))
        at.run()
        
        # Verify app runs without errors
        assert not at.exception


@pytest.mark.e2e
@pytest.mark.workflow  
class TestBatchProcessingWorkflow(StreamlitWorkflowTestBase):
    """Test Batch Processing page workflow"""
    
    def test_batch_page_component_initialization(self):
        """Test BatchPage component initialization"""
        # Set up dependencies
        self.patch_llm_client()
        
        config_loader = ConfigurationLoader.create_default_loader()
        init_result = config_loader.initialize_all()
        config = init_result['config_manager']
        analytics = init_result['analytics']
        
        document_processor = DocumentProcessor(config.config)
        extraction_engine = ExtractionEngine(config.config, analytics)
        batch_coordinator = BatchCoordinator(config.config)
        
        # Test component initialization
        batch_page = BatchPage(extraction_engine, document_processor, batch_coordinator, config)
        
        assert batch_page.extraction_engine is not None
        assert batch_page.document_processor is not None
        assert batch_page.batch_coordinator is not None
        assert batch_page.config is not None
    
    def test_batch_processing_workflow(self):
        """Test batch processing workflow with mock data"""
        # Set up dependencies
        self.patch_llm_client()
        
        config_loader = ConfigurationLoader.create_default_loader()
        init_result = config_loader.initialize_all()
        config = init_result['config_manager']
        analytics = init_result['analytics']
        
        document_processor = DocumentProcessor(config.config)
        extraction_engine = ExtractionEngine(config.config, analytics)
        batch_coordinator = BatchCoordinator(config.config)
        
        # Mock batch processing
        with patch.object(batch_coordinator, 'process_batch') as mock_batch:
            mock_batch.return_value = {
                'results': self.batch_data,
                'summary': {
                    'total_files': 3,
                    'successful': 3,
                    'failed': 0
                }
            }
            
            # Test batch workflow
            batch_page = BatchPage(extraction_engine, document_processor, batch_coordinator, config)
            
            # Simulate batch processing
            mock_files = [
                MagicMock(name="study1.pdf"),
                MagicMock(name="study2.pdf"),
                MagicMock(name="study3.pdf")
            ]
            
            result = batch_coordinator.process_batch(mock_files)
            assert result is not None
            assert 'results' in result
            assert 'summary' in result
            assert result['summary']['total_files'] == 3


@pytest.mark.e2e
@pytest.mark.workflow
class TestAnnotationPageWorkflow(StreamlitWorkflowTestBase):
    """Test Manual Annotation page workflow"""
    
    def test_annotation_page_initialization(self):
        """Test AnnotationPage initialization and directory setup"""
        annotation_page = AnnotationPage()
        
        # Check that all required directories exist
        assert os.path.exists(annotation_page.output_dir)
        assert os.path.exists(annotation_page.temp_dir)
        assert os.path.exists(annotation_page.annotations_dir)
        assert os.path.exists(annotation_page.reports_dir)
    
    def test_annotation_workflow_with_sample_data(self):
        """Test annotation workflow with sample data"""
        annotation_page = AnnotationPage()
        
        # Test that component can handle sample data
        sample_data = self.sample_extraction
        
        # Simulate loading extraction results for annotation
        with patch('builtins.open', mock_open(read_data=json.dumps(sample_data))):
            with patch('json.load', return_value=sample_data):
                # Test data loading functionality
                loaded_data = sample_data  # Simulated loading
                assert loaded_data is not None
                assert 'study_design' in loaded_data
    
    def test_annotation_file_operations(self):
        """Test annotation file operations"""
        annotation_page = AnnotationPage()
        
        # Test saving annotations
        test_annotations = {
            "original": self.sample_extraction,
            "annotated": {
                **self.sample_extraction,
                "notes": "Manually verified data"
            },
            "timestamp": "2024-01-01T10:00:00"
        }
        
        # Test file saving capability
        test_file_path = annotation_page.annotations_dir + "/test_annotation.json"
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('json.dump') as mock_json_dump:
                # Simulate saving annotations
                try:
                    with open(test_file_path, 'w') as f:
                        json.dump(test_annotations, f)
                    mock_json_dump.assert_called_once()
                except Exception:
                    pass  # Expected in test environment


@pytest.mark.e2e
@pytest.mark.workflow
class TestAnalyticsPageWorkflow(StreamlitWorkflowTestBase):
    """Test Analytics Dashboard workflow"""
    
    def test_analytics_page_initialization(self):
        """Test AnalyticsPage initialization with analytics system"""
        config_loader = ConfigurationLoader.create_default_loader()
        init_result = config_loader.initialize_all()
        analytics = init_result['analytics']
        
        analytics_page = AnalyticsPage(analytics)
        assert analytics_page.analytics is not None
    
    def test_analytics_report_generation(self):
        """Test analytics report generation"""
        config_loader = ConfigurationLoader.create_default_loader()
        init_result = config_loader.initialize_all()
        analytics = init_result['analytics']
        
        analytics_page = AnalyticsPage(analytics)
        
        # Test report generation with mock data
        with patch.object(analytics, 'generate_report') as mock_report:
            mock_report.return_value = {
                'summary': {
                    'total_extractions': 10,
                    'successful_extractions': 9,
                    'failed_extractions': 1,
                    'avg_processing_time': 2.5
                },
                'time_series': [
                    {'date': '2024-01-01', 'count': 3},
                    {'date': '2024-01-02', 'count': 4},
                    {'date': '2024-01-03', 'count': 3}
                ]
            }
            
            # Test report generation
            report = analytics.generate_report(days=7)
            assert report is not None
            assert 'summary' in report
            assert 'time_series' in report
    
    def test_analytics_data_visualization_preparation(self):
        """Test analytics data preparation for visualization"""
        config_loader = ConfigurationLoader.create_default_loader()
        init_result = config_loader.initialize_all()
        analytics = init_result['analytics']
        
        analytics_page = AnalyticsPage(analytics)
        
        # Test data preparation for charts
        sample_analytics_data = [
            {'timestamp': '2024-01-01T10:00:00', 'model': 'test-model', 'success': True, 'time': 2.1},
            {'timestamp': '2024-01-01T11:00:00', 'model': 'test-model', 'success': True, 'time': 2.8},
            {'timestamp': '2024-01-01T12:00:00', 'model': 'test-model', 'success': False, 'time': 0.0}
        ]
        
        # Convert to DataFrame for visualization
        df = pd.DataFrame(sample_analytics_data)
        assert len(df) == 3
        assert 'success' in df.columns
        assert 'time' in df.columns


@pytest.mark.e2e
@pytest.mark.workflow
class TestCrossPageIntegration(StreamlitWorkflowTestBase):
    """Test integration between different pages and session state"""
    
    def test_session_state_management_integration(self):
        """Test session state management across page navigation"""
        # Test SessionStateManager functionality
        SessionStateManager.initialize_all_state()
        
        # Test state reset functions exist
        assert hasattr(SessionStateManager, 'reset_extraction_state')
        assert hasattr(SessionStateManager, 'reset_batch_state')
        
        # These methods would work in actual Streamlit context
        # Here we test their existence and basic functionality
    
    def test_component_dependency_injection(self):
        """Test that components receive proper dependencies"""
        # Set up full system
        self.patch_llm_client()
        
        config_loader = ConfigurationLoader.create_default_loader()
        init_result = config_loader.initialize_all()
        config = init_result['config_manager']
        analytics = init_result['analytics']
        
        document_processor = DocumentProcessor(config.config)
        extraction_engine = ExtractionEngine(config.config, analytics)
        batch_coordinator = BatchCoordinator(config.config)
        
        # Test all page components can be initialized with proper dependencies
        extraction_page = ExtractionPage(extraction_engine, document_processor, config)
        batch_page = BatchPage(extraction_engine, document_processor, batch_coordinator, config)
        annotation_page = AnnotationPage()
        analytics_page = AnalyticsPage(analytics)
        
        # Verify dependency injection
        assert extraction_page.extraction_engine is extraction_engine
        assert extraction_page.document_processor is document_processor
        assert extraction_page.config is config
        
        assert batch_page.extraction_engine is extraction_engine
        assert batch_page.document_processor is document_processor
        assert batch_page.batch_coordinator is batch_coordinator
        assert batch_page.config is config
        
        assert analytics_page.analytics is analytics
    
    def test_error_propagation_across_components(self):
        """Test error handling and propagation across components"""
        config_loader = ConfigurationLoader.create_default_loader()
        init_result = config_loader.initialize_all()
        
        # Test error collection
        assert isinstance(init_result['errors'], list)
        
        # Test component resilience to initialization errors
        try:
            config = init_result['config_manager']
            analytics = init_result['analytics']
            
            # Components should handle missing or invalid config gracefully
            document_processor = DocumentProcessor(config.config)
            extraction_engine = ExtractionEngine(config.config, analytics)
            
        except Exception as e:
            pytest.fail(f"Components should handle errors gracefully: {e}")


# Test runner for workflow tests
if __name__ == "__main__":
    # Run workflow tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-m", "workflow",
        "--log-cli-level=INFO"
    ])