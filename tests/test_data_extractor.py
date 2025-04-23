# tests/test_data_extractor.py
"""
Test module for data extraction functionality
"""
import os
import sys
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Import from src
from src.utils.data_extractor import DataExtractor
from src.llm.mock_client import MockLLMClient

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_data_extractor():
    """Test the DataExtractor class with a mock client."""
    try:
        # Override the ClientFactory's create_client method temporarily
        from src.llm.client_factory import ClientFactory
        original_create_client = ClientFactory.create_client
        
        def mock_create_client(provider, api_key=None, model_name=None):
            return MockLLMClient(api_key=api_key, model_name=model_name)
        
        # Apply the patch
        ClientFactory.create_client = mock_create_client
        
        # Create a DataExtractor with mock client
        logger.info("Creating DataExtractor...")
        extractor = DataExtractor(provider="mock", model_name="test-model")
        
        # Sample text to analyze
        sample_text = """
        The study included 50 patients with heart failure.
        The mean age was 67 years (range 45-85), and 60% were male.
        All patients had NYHA class III or IV heart failure with a mean ejection fraction of 30%.
        """
        
        # Use a try-except block to identify the exact line causing the error
        try:
            logger.info("Attempting to extract patient characteristics...")
            result = extractor.extract_patient_characteristics(sample_text)
            logger.info(f"Extraction successful: {result}")
        except Exception as e:
            logger.error(f"Error during extraction: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Restore the original method
        ClientFactory.create_client = original_create_client
        
        return True
        
    except Exception as e:
        logger.error(f"Error in test_data_extractor: {str(e)}")
        # Restore the original method if it exists
        if 'original_create_client' in locals():
            ClientFactory.create_client = original_create_client
        return False

if __name__ == "__main__":
    test_data_extractor()