"""
Factory for creating LLM API clients
"""
import logging
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient

# Configure logging
logger = logging.getLogger(__name__)

class ClientFactory:
    """Factory for creating appropriate LLM clients"""
    
    # Supported provider types
    PROVIDER_OPENAI = "openai"
    PROVIDER_ANTHROPIC = "anthropic"
    
    @staticmethod
    def create_client(provider, api_key=None, model_name=None):
        """
        Create an LLM client for the specified provider
        
        Args:
            provider (str): Provider name ('openai' or 'anthropic')
            api_key (str, optional): API key for the service
            model_name (str, optional): Model name to use
            
        Returns:
            BaseLLMClient: An instance of the appropriate client
            
        Raises:
            ValueError: If provider is not supported
        """
        provider = provider.lower()
        
        if provider == ClientFactory.PROVIDER_OPENAI:
            return OpenAIClient(api_key=api_key, model_name=model_name)
        elif provider == ClientFactory.PROVIDER_ANTHROPIC:
            return AnthropicClient(api_key=api_key, model_name=model_name)
        else:
            error_msg = f"Unsupported provider: {provider}. Supported providers are: {ClientFactory.PROVIDER_OPENAI}, {ClientFactory.PROVIDER_ANTHROPIC}"
            logger.error(error_msg)
            raise ValueError(error_msg)