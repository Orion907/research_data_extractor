"""
Base module for LLM API clients
"""
import logging
from abc import ABC, abstractmethod

# Configure logging
logger = logging.getLogger(__name__)

class BaseLLMClient(ABC):
    """Base abstract class that all LLM API clients should implement"""
    
    @abstractmethod
    def __init__(self, api_key=None, model_name=None):
        """
        Initialize the client with API key and model
        
        Args:
            api_key (str, optional): API key for the service
            model_name (str, optional): Name of the model to use
        """
        pass
    
    @abstractmethod
    def generate_completion(self, prompt, max_tokens=None, temperature=0.0):
        """
        Generate a completion from the LLM
        
        Args:
            prompt (str): The prompt to send to the LLM
            max_tokens (int, optional): Maximum number of tokens to generate
            temperature (float, optional): Sampling temperature, defaults to 0.0 for most deterministic response
            
        Returns:
            str: The generated text completion
        """
        pass
    
    @abstractmethod
    def get_available_models(self):
        """
        Get list of available models from this provider
        
        Returns:
            list: List of available model names
        """
        pass