"""
Test module for the updated data extractor with template system integration
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.utils.template_system import TemplateSystem
from src.utils.data_extractor import DataExtractor
from src.llm.mock_client import MockLLMClient
from src.llm.client_factory import ClientFactory

def test_data_extractor_with_template_system():
    """Test the updated DataExtractor with the TemplateSystem integration"""
    
    try:
        # Override the ClientFactory's create_client method temporarily
        original_create_client = ClientFactory.create_client
        
        def mock_create_client(provider, api_key=None, model_name=None):
            return MockLLMClient(api_key=api_key, model_name=model_name)
        
        # Apply the patch
        ClientFactory.create_client = mock_create_client
        
        # Create a template system
        logger.info("Creating template system...")
        template_system = TemplateSystem()
        
        # Create a specialized diabetes template
        diabetes_template_id = "test_diabetes_extraction"
        diabetes_template_text = """
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
        
        # Save the template
        logger.info("Creating diabetes extraction template...")
        version_id = template_system.create_template(
            diabetes_template_id,
            diabetes_template_text,
            "Template for extracting diabetes patient characteristics",
            {"disease": "diabetes", "focus": "clinical_trials"}
        )
        
        logger.info(f"Created template with version: {version_id}")
        
        # Create a DataExtractor with mock client and our template system
        logger.info("Creating DataExtractor with template system...")
        extractor = DataExtractor(
            provider="mock", 
            model_name="test-model",
            template_system=template_system
        )
        
        # Sample text to analyze
        sample_text = """
        The study included 75 patients with type 2 diabetes mellitus (T2DM). 
        Patients were aged between 45-70 years (mean age 58.3 years), with 60% being male. 
        Inclusion criteria were HbA1c > 7.5% and BMI > 25 kg/m².
        Exclusion criteria included pregnancy, severe renal impairment (eGFR < 30 mL/min), 
        and active cancer treatment.
        All patients were taking metformin, and 45% were on insulin therapy.
        """
        
        # Extract patient characteristics with our template
        logger.info("Extracting patient characteristics...")
        result = extractor.extract_patient_characteristics(
            sample_text,
            template_id=diabetes_template_id,
            source_file="test_diabetes_study.pdf"
        )
        
        logger.info("Extraction result:")
        for key, value in result.items():
            logger.info(f"  {key}: {value}")
        
        # Test extraction with a different template version
        logger.info("Creating an updated version of the template...")
        updated_template_text = """
        You are an AI assistant specialized in extracting patient characteristic data from diabetes studies.
        
        Below is a section of a research article. Please extract all patient characteristics mentioned, including:
        - Sample size and demographics
        - Age information (mean, median, range)
        - Gender distribution (percentage male/female)
        - Laboratory values (HbA1c, glucose levels)
        - Anthropometric data (BMI, weight)
        - Current medications
        - Inclusion and exclusion criteria
        
        Format your response as a JSON object with appropriate keys and values.
        
        ARTICLE SECTION:
        {text}
        
        EXTRACTED PATIENT CHARACTERISTICS:
        """
        
        updated_version_id = template_system.create_template(
            diabetes_template_id,
            updated_template_text,
            "Updated diabetes extraction template with more detailed instructions",
            {"disease": "diabetes", "focus": "clinical_trials", "version": "detailed"}
        )
        
        logger.info(f"Created updated template with version: {updated_version_id}")
        
        # Extract using the updated template
        logger.info("Extracting with updated template...")
        updated_result = extractor.extract_patient_characteristics(
            sample_text,
            template_id=diabetes_template_id,
            version_id=updated_version_id,
            source_file="test_diabetes_study.pdf"
        )
        
        logger.info("Updated extraction result:")
        for key, value in updated_result.items():
            logger.info(f"  {key}: {value}")
        
        # Test extraction from multiple chunks
        logger.info("Testing extraction from multiple chunks...")
        chunks = [
            sample_text,
            """
            The study measured fasting glucose levels and conducted oral glucose tolerance tests.
            Mean baseline HbA1c was 8.3% (±0.9%).
            Patients with diabetic neuropathy (n=25, 33%) had significantly higher HbA1c levels (8.9% vs 8.0%, p<0.05).
            """
        ]
        
        multi_result = extractor.extract_from_chunks(
            chunks,
            template_id=diabetes_template_id,
            source_file="test_multi_chunk_diabetes_study.pdf"
        )
        
        logger.info("Multi-chunk extraction result:")
        for key, value in multi_result.items():
            logger.info(f"  {key}: {value}")
        
        # Get analytics summary
        logger.info("Getting analytics summary...")
        summary = extractor.get_analytics_summary()
        
        logger.info("Analytics summary:")
        for key, value in summary.items():
            if key != 'template_performance':
                logger.info(f"  {key}: {value}")
        
        if 'template_performance' in summary:
            logger.info("Template performance:")
            for template_id, metrics in summary['template_performance'].items():
                logger.info(f"  {template_id}: {metrics}")
        
        # Restore the original method
        ClientFactory.create_client = original_create_client
        
        return True
        
    except Exception as e:
        logger.error(f"Error in test_data_extractor_with_template_system: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Restore the original method if it exists
        if 'original_create_client' in locals():
            ClientFactory.create_client = original_create_client
        return False

if __name__ == "__main__":
    test_data_extractor_with_template_system()
    logger.info("DataExtractor with TemplateSystem test completed!")