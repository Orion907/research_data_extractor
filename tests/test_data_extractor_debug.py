# tests/test_data_extractor_debug.py

import os
import sys
import logging
import traceback

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_initialization():
    """Debug the initialization of DataExtractor."""
    try:
        # Import for inspection
        import inspect
        from src.llm.mock_client import MockLLMClient
        from src.llm.client_factory import ClientFactory
        from src.utils.data_extractor import DataExtractor
        
        # Print the DataExtractor class source
        logger.info("DataExtractor class source:")
        logger.info(inspect.getsource(DataExtractor))
        
        # Debug the initialization step by step
        logger.info("Step 1: Creating mock client")
        mock_client = MockLLMClient(model_name="test-model")
        
        # Override client factory to use mock
        original_create_client = ClientFactory.create_client
        
        def mock_create_client(provider, api_key=None, model_name=None):
            logger.info("Mock create_client called")
            return mock_client
        
        ClientFactory.create_client = mock_create_client
        
        logger.info("Step 2: Creating DataExtractor")
        try:
            # Just create the instance
            extractor = DataExtractor(provider="mock", model_name="test-model")
            logger.info("DataExtractor created successfully")
        except Exception as e:
            logger.error(f"Error creating DataExtractor: {e}")
            logger.error(traceback.format_exc())
        
        # Restore original method
        ClientFactory.create_client = original_create_client
        
        return True
    except Exception as e:
        logger.error(f"Debugging error: {e}")
        return False

if __name__ == "__main__":
    debug_initialization()