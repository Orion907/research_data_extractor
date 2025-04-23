# Create a new file: src/llm/mock_client.py
import logging
from .api_client import BaseLLMClient

logger = logging.getLogger(__name__)

class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing without API access"""
    
    def __init__(self, api_key=None, model_name="mock-model"):
        self.model_name = model_name
        logger.info(f"Initialized Mock LLM client with model: {model_name}")
    
    def generate_completion(self, prompt, max_tokens=None, temperature=0.0):
        """Return a mock response based on the prompt"""
        logger.info("Generating mock completion")
        
        # Check if prompt contains certain keywords to return appropriate responses
        if "age" in prompt.lower() and "gender" in prompt.lower():
            return """
            {
                "Age": "65 years old",
                "Gender": "Male"
            }
            """
        
        # Default response
        return """
        {
            "Extracted Data": "This is a mock response for testing without API access"
        }
        """
    
    def get_available_models(self):
        """Return mock available models"""
        return ["mock-model-basic", "mock-model-advanced"]