# src/llm/anthropic_client.py
"""
Anthropic API client implementation
"""
import os
import logging
from anthropic import Anthropic
from .api_client import BaseLLMClient

# Configure logging
logger = logging.getLogger(__name__)

class AnthropicClient(BaseLLMClient):
    """Client for Anthropic's Claude API"""
    
    # Default model to use if none specified
    DEFAULT_MODEL = "claude-3-sonnet-20240229"
    
    def __init__(self, api_key=None, model_name=None):
        """
        Initialize the Anthropic client
        
        Args:
            api_key (str, optional): Anthropic API key, if not provided will try to get from ANTHROPIC_API_KEY environment variable
            model_name (str, optional): Model to use, defaults to claude-3-sonnet-20240229
        """
        # Get API key from environment if not provided
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            logger.warning("Anthropic API key not provided and not found in environment variables")
            
        self.model_name = model_name or self.DEFAULT_MODEL
        self.client = Anthropic(api_key=self.api_key)
        
        logger.info(f"Initialized Anthropic client with model: {self.model_name}")
    
    def generate_completion(self, prompt, max_tokens=None, temperature=0.0):
        """
        Generate a completion using Anthropic's API
    
        Args:
            prompt (str): The prompt to send to the model
            max_tokens (int, optional): Maximum tokens to generate 
            temperature (float, optional): Sampling temperature
        
        Returns:
            str: Generated text completion
        """
        try:
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens or 4096,
                temperature=temperature,
                system="You are a helpful assistant that extracts patient characteristic data from medical research articles. Follow the exact JSON schema specified in the prompt, using the exact field names provided. Always respond with valid JSON format.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
        
            # Extract the completion text
            completion = response.content[0].text
            return completion
        
        except Exception as e:
            logger.error(f"Error generating completion with Anthropic: {str(e)}")
            raise
    
    def get_available_models(self):
        """
        Get list of available Anthropic models
        
        Returns:
            list: List of commonly available Claude models
        """
        # Anthropic doesn't have a direct API to list models, so we return common ones
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229", 
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0"
        ]