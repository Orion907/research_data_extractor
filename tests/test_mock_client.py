# tests/test_mock_client.py
"""
Test module for mock LLM client
"""
import os
import sys
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Now you can import from src
from src.llm.mock_client import MockLLMClient
from src.llm.client_factory import ClientFactory

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_mock_client_directly():
    """Test the mock client directly."""
    try:
        # Initialize the mock client
        client = MockLLMClient(model_name="test-model")
        
        # Simple test prompt
        test_prompt = """
        Below is a short medical text sample. Extract patient age and gender.
        
        ARTICLE SECTION:
        The patient, a 65-year-old male with a history of hypertension,
        presented with chest pain and shortness of breath.
        
        EXTRACTED PATIENT CHARACTERISTICS:
        """
        
        # Generate a completion
        logger.info("Sending test prompt to mock client...")
        completion = client.generate_completion(test_prompt)
        
        # Log the result
        logger.info("Received response from mock client")
        logger.info("-" * 40)
        logger.info(completion)
        logger.info("-" * 40)
        
        # Get available models
        models = client.get_available_models()
        logger.info(f"Available models: {models}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing mock client: {str(e)}")
        return False

def test_mock_client_factory():
    """Test getting the mock client via the factory."""
    try:
        # First, let's modify the ClientFactory to support our mock client
        ClientFactory.PROVIDER_MOCK = "mock"
        
        # Save the original create_client method
        original_create_client = ClientFactory.create_client
        
        # Define a new create_client method that includes our mock client
        def new_create_client(provider, api_key=None, model_name=None):
            provider = provider.lower()
            
            if provider == ClientFactory.PROVIDER_MOCK:
                from src.llm.mock_client import MockLLMClient
                return MockLLMClient(api_key=api_key, model_name=model_name)
            else:
                # Call the original method for other providers
                return original_create_client(provider, api_key, model_name)
        
        # Replace the method temporarily
        ClientFactory.create_client = new_create_client
        
        # Now test getting the client via the factory
        logger.info("Getting mock client via factory...")
        client = ClientFactory.create_client("mock", model_name="factory-test-model")
        
        # Test a simple prompt
        test_prompt = "Extract the patient demographics."
        completion = client.generate_completion(test_prompt)
        
        logger.info("Received response via factory method")
        logger.info("-" * 40)
        logger.info(completion)
        logger.info("-" * 40)
        
        # Restore the original method to avoid side effects
        ClientFactory.create_client = original_create_client
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing mock client via factory: {str(e)}")
        # Make sure to restore the original method even if there's an error
        if 'original_create_client' in locals():
            ClientFactory.create_client = original_create_client
        return False

def test_data_extractor_with_mock():
    """Test using the mock client with the DataExtractor class."""
    try:
        from src.utils.data_extractor import DataExtractor
        
        # Temporarily modify ClientFactory to include mock support
        ClientFactory.PROVIDER_MOCK = "mock"
        original_create_client = ClientFactory.create_client
        
        def new_create_client(provider, api_key=None, model_name=None):
            provider = provider.lower()
            
            if provider == "mock":
                from src.llm.mock_client import MockLLMClient
                return MockLLMClient(api_key=api_key, model_name=model_name)
            else:
                return original_create_client(provider, api_key, model_name)
        
        # Apply the patch
        ClientFactory.create_client = new_create_client
        
        # Create a DataExtractor with the mock client
        logger.info("Creating DataExtractor with mock client...")
        extractor = DataExtractor(provider="mock", model_name="mock-model")
        
        # Sample text to analyze
        sample_text = """
        The study included 50 patients with heart failure.
        The mean age was 67 years (range 45-85), and 60% were male.
        All patients had NYHA class III or IV heart failure with a mean ejection fraction of 30%.
        """
        
        # Extract patient characteristics
        logger.info("Extracting patient characteristics...")
        result = extractor.extract_patient_characteristics(sample_text)
        
        logger.info("Extraction result:")
        logger.info("-" * 40)
        logger.info(result)
        logger.info("-" * 40)
        
        # Restore the original method
        ClientFactory.create_client = original_create_client
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing DataExtractor with mock client: {str(e)}")
        # Make sure to restore the original method even if there's an error
        if 'original_create_client' in locals():
            ClientFactory.create_client = original_create_client
        return False
    
def test_data_extractor_with_mock_simplified():
    """Test using the mock client with the DataExtractor class (simplified)."""
    try:
        from src.llm.mock_client import MockLLMClient
        from src.utils.data_extractor import DataExtractor
        from src.llm.client_factory import ClientFactory
        
        # Save original method
        original_create_client = ClientFactory.create_client
        
        # Define a patched method that returns our mock client
        def mock_create_client(provider, api_key=None, model_name=None):
            return MockLLMClient(api_key=api_key, model_name=model_name)
        
        # Apply the patch
        ClientFactory.create_client = mock_create_client
        
        # Create a DataExtractor with the patched factory
        logger.info("Creating DataExtractor with mock client...")
        extractor = DataExtractor(provider="doesn't-matter", model_name="mock-model")
        
        # Sample text to analyze
        sample_text = """
        The study included 50 patients with heart failure.
        The mean age was 67 years (range 45-85), and 60% were male.
        All patients had NYHA class III or IV heart failure with a mean ejection fraction of 30%.
        """
        
        # Extract patient characteristics
        logger.info("Extracting patient characteristics...")
        result = extractor.extract_patient_characteristics(sample_text)
        
        logger.info("Extraction result:")
        logger.info("-" * 40)
        logger.info(result)
        logger.info("-" * 40)
        
        # Restore the original method
        ClientFactory.create_client = original_create_client
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing DataExtractor with mock client: {str(e)}")
        # Make sure to restore the original method even if there's an error
        if 'original_create_client' in locals():
            ClientFactory.create_client = original_create_client
        return False   

def test_data_extractor_manual():
    """Test using the mock client directly with DataExtractor-style operations."""
    try:
        from src.llm.mock_client import MockLLMClient
        from src.utils.prompt_templates import PromptTemplate
        
        # Create mock client directly
        logger.info("Creating mock client directly...")
        mock_client = MockLLMClient(model_name="test-model")
        
        # Sample text to analyze
        sample_text = """
        The study included 50 patients with heart failure.
        The mean age was 67 years (range 45-85), and 60% were male.
        All patients had NYHA class III or IV heart failure with a mean ejection fraction of 30%.
        """
        
        # Get prompt using static method
        prompt = PromptTemplate.get_extraction_prompt(sample_text)
        
        # Generate completion directly
        logger.info("Generating completion with mock client...")
        completion = mock_client.generate_completion(prompt)
        
        logger.info("Completion result:")
        logger.info("-" * 40)
        logger.info(completion)
        logger.info("-" * 40)
        
        return True
        
    except Exception as e:
        logger.error(f"Error in manual test: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n=== Testing Mock Client Directly ===")
    success1 = test_mock_client_directly()
    
    print("\n=== Testing Mock Client via Factory ===")
    success2 = test_mock_client_factory()
    
    print("\n=== Testing with Manual DataExtractor-style Operation ===")
    success3 = test_data_extractor_manual()  # Use the new function
    
    print(f"\nAll tests completed. Success: {success1 and success2 and success3}")