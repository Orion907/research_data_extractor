# tests/test_prompt_versioning.py
"""
Test module for prompt versioning and analytics functionality
"""
import os
import sys
import logging
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.prompt_manager import PromptManager
from src.utils.analytics import PromptAnalytics
from src.utils.prompt_templates import PromptTemplate
from src.utils.data_extractor import DataExtractor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_prompt_versioning():
    """Test the prompt versioning functionality"""
    
    # Create a prompt manager
    manager = PromptManager()
    
    # Create a few test templates
    template1_id = "test_template_1"
    template1_text = "This is test template 1. Context: {text}"
    
    template2_id = "test_template_2"
    template2_text = "This is test template 2. Article: {text}"
    
    # Save the templates
    version1 = manager.save_template(template1_id, template1_text, "First test template")
    version2 = manager.save_template(template2_id, template2_text, "Second test template")
    
    print(f"Created template versions: {version1}, {version2}")
    
    # List available templates
    templates = manager.list_templates()
    print(f"Available templates: {templates}")
    
    # Create another version of the first template
    template1_updated = "This is an updated test template 1. Input: {text}"
    version1_updated = manager.save_template(template1_id, template1_updated, "Updated first template")
    
    print(f"Created updated template version: {version1_updated}")
    
    # List versions of template 1
    versions = manager.list_versions(template1_id)
    print(f"Versions of template 1: {versions}")
    
    # Retrieve different versions
    latest = manager.get_template_text(template1_id)
    original = manager.get_template_text(template1_id, version1)
    
    print(f"Latest version of template 1: {latest}")
    print(f"Original version of template 1: {original}")
    
    return True

def test_analytics():
    """Test the prompt analytics functionality"""
    
    # Create an analytics tracker
    analytics = PromptAnalytics()
    
    # Log some test extraction events
    analytics.log_extraction(
        template_id="test_template_1",
        version_id="test_template_1_v20240421123456",
        source_file="test_file.pdf",
        characteristics_found=10,
        start_time=datetime.now(),
        end_time=datetime.now(),
        success=True,
        metadata={"test": True}
    )
    
    analytics.log_extraction(
        template_id="test_template_2",
        version_id="test_template_2_v20240421123456",
        source_file="test_file2.pdf",
        characteristics_found=5,
        start_time=datetime.now(),
        end_time=datetime.now(),
        success=False,
        error="Test error",
        metadata={"test": True}
    )
    
    # Get summary
    summary = analytics.get_analytics_summary()
    print("Analytics summary:")
    for key, value in summary.items():
        if key != 'template_performance':
            print(f"  {key}: {value}")
    
    print("Template performance:")
    for template_id, metrics in summary.get('template_performance', {}).items():
        print(f"  {template_id}: {metrics}")
    
    # Export to CSV
    csv_path = analytics.export_analytics_csv()
    print(f"Exported analytics to CSV: {csv_path}")
    
    return True

def test_integrated_extraction():
    """Test the integrated extraction with versioning and analytics"""
    
    # Create a sample text
    sample_text = """
    The study included 75 patients with type 2 diabetes mellitus (T2DM). 
    Patients were aged between 45-70 years (mean age 58.3 years), with 60% being male. 
    Inclusion criteria were HbA1c > 7.5% and BMI > 25 kg/m².
    Exclusion criteria included pregnancy, severe renal impairment (eGFR < 30 mL/min), 
    and active cancer treatment.
    All patients were taking metformin, and 45% were on insulin therapy.
    """
    
    # Create a data extractor with simulated responses (no actual API calls)
    class MockLLMClient:
        def __init__(self, api_key=None, model_name="mock-model"):
            self.model_name = model_name
            
        def generate_completion(self, prompt, max_tokens=None, temperature=0.0):
            # Return a mock structured extraction
            return """
            {
                "sample_size": "75 patients",
                "condition": "type 2 diabetes mellitus (T2DM)",
                "age_range": "45-70 years",
                "mean_age": "58.3 years",
                "gender_distribution": "60% male, 40% female",
                "inclusion_criteria": [
                    "HbA1c > 7.5%",
                    "BMI > 25 kg/m²"
                ],
                "exclusion_criteria": [
                    "pregnancy",
                    "severe renal impairment (eGFR < 30 mL/min)",
                    "active cancer treatment"
                ],
                "medications": [
                    "all patients on metformin",
                    "45% on insulin therapy"
                ]
            }
            """
            
        def get_available_models(self):
            return ["mock-model"]
    
    # Mock the client factory to return our mock client
    from src.llm.client_factory import ClientFactory
    original_create_client = ClientFactory.create_client
    
    def mock_create_client(provider, api_key=None, model_name=None):
        return MockLLMClient(api_key, model_name)
    
    # Replace the method temporarily
    ClientFactory.create_client = mock_create_client
    
    try:
        # Now create the actual data extractor
        extractor = DataExtractor(provider="mock", model_name="mock-model")
        
        # First, create a custom template for extraction
        template_id = "diabetes_extraction"
        template_text = """
        You are an AI assistant specialized in extracting patient characteristic data from diabetes studies.
        
        Below is a section of a research article. Please extract all patient characteristics mentioned, including:
        - Sample size
        - Age information
        - Gender distribution
        - HbA1c levels
        - BMI values
        - Medications
        - Inclusion/exclusion criteria
        
        Format your response as a JSON object with appropriate keys and values.
        
        ARTICLE SECTION:
        {text}
        
        EXTRACTED PATIENT CHARACTERISTICS:
        """
        
        # Save the template through the PromptTemplate interface
        extractor.prompt_template.create_new_template(
            template_id=template_id,
            template_text=template_text,
            description="Template for extracting diabetes patient characteristics",
            metadata={"disease": "diabetes", "focus": "clinical_trials"}
        )
        
        # Test extraction with the new template
        print("\nExtracting patient characteristics with custom template...")
        result = extractor.extract_patient_characteristics(
            sample_text,
            template_id=template_id,
            source_file="sample_diabetes_study.pdf"
        )
        
        print("Extraction result:")
        for key, value in result.items():
            print(f"  {key}: {value}")
        
        # Get analytics
        print("\nExtraction analytics:")
        analytics = extractor.get_analytics_summary()
        for key, value in analytics.items():
            if key != 'template_performance':
                print(f"  {key}: {value}")
        
        return True
        
    finally:
        # Restore the original method
        ClientFactory.create_client = original_create_client

if __name__ == "__main__":
    print("\n=== Testing Prompt Versioning ===")
    test_prompt_versioning()
    
    print("\n=== Testing Analytics ===")
    test_analytics()
    
    print("\n=== Testing Integrated Extraction ===")
    test_integrated_extraction()
    
    print("\nAll tests completed!")