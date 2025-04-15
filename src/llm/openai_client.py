"""
OpenAI API client implementation
"""
import os
import logging
from openai import OpenAI
from .api_client import BaseLLMClient

# Configure logging
logger = logging.getLogger(__name__)

class OpenAIClient(BaseLLMClient):
    """Client for OpenAI's API"""
    
    # Default model to use if none specified
    DEFAULT_MODEL = "gpt-3.5-turbo"
    
    def __init__(self, api_key=None, model_name=None):
        """
        Initialize the OpenAI client
        
        Args:
            api_key (str, optional): OpenAI API key, if not provided will try to get from OPENAI_API_KEY environment variable
            model_name (str, optional): Model to use, defaults to gpt-3.5-turbo
        """
        # Get API key from environment if not provided
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        
        if not self.api_key:
            logger.warning("OpenAI API key not provided and not found in environment variables")
            
        self.model_name = model_name or self.DEFAULT_MODEL
        self.client = OpenAI(api_key=self.api_key)
        
        logger.info(f"Initialized OpenAI client with model: {self.model_name}")
    
    def generate_completion(self, prompt, max_tokens=None, temperature=0.0):
        """
        Generate a completion using OpenAI's API
        
        Args:
            prompt (str): The prompt to send to the model
            max_tokens (int, optional): Maximum tokens to generate
            temperature (float, optional): Sampling temperature
            
        Returns:
            str: Generated text completion
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that extracts patient characteristic data from medical research articles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Extract the completion text
            completion = response.choices[0].message.content
            return completion
            
        except Exception as e:
            logger.error(f"Error generating completion with OpenAI: {str(e)}")
            raise
    
    def get_available_models(self):
        """
        Get list of available OpenAI models
        
        Returns:
            list: List of available model names
        """
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            logger.error(f"Error fetching available models from OpenAI: {str(e)}")
            return [self.DEFAULT_MODEL]  # Fallback to default model