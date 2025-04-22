import os
import sys
import logging
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

# Now you can import from src
from src.llm.anthropic_client import AnthropicClient

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_anthropic_api():
    """Test the Anthropic API connection and basic completion."""
    try:
        # Initialize the Anthropic client
        client = AnthropicClient()
        
        # Simple test prompt
        test_prompt = """
        Below is a short medical text sample. Extract patient age and gender.
        
        ARTICLE SECTION:
        The patient, a 65-year-old male with a history of hypertension,
        presented with chest pain and shortness of breath.
        
        EXTRACTED PATIENT CHARACTERISTICS:
        """
        
        # Generate a completion
        logger.info("Sending test prompt to Anthropic API...")
        completion = client.generate_completion(test_prompt)
        
        # Log the result
        logger.info("Received response from Anthropic API")
        logger.info("-" * 40)
        logger.info(completion)
        logger.info("-" * 40)
        
        return True
    
    except Exception as e:
        logger.error(f"Error testing Anthropic API: {str(e)}")
        return False

if __name__ == "__main__":
    test_successful = test_anthropic_api()
    print(f"Test completed. Success: {test_successful}")