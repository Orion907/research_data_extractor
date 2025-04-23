# src/llm/client_factory.py
"""
Factory for creating LLM API clients
"""
import logging
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .mock_client import MockLLMClient  # Add this import

# Configure logging
logger = logging.getLogger(__name__)

class ClientFactory:
    """Factory for creating appropriate LLM clients"""
    
    # Supported provider types
    PROVIDER_OPENAI = "openai"
    PROVIDER_ANTHROPIC = "anthropic"
    PROVIDER_MOCK = "mock"  # Add this constant
    
    @staticmethod
    def create_client(provider, api_key=None, model_name=None):
        """
        Create an LLM client for the specified provider
        
        Args:
            provider (str): Provider name ('openai', 'anthropic', or 'mock')
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
        elif provider == ClientFactory.PROVIDER_MOCK:  # Add this condition
            return MockLLMClient(api_key=api_key, model_name=model_name)
        else:
            error_msg = f"Unsupported provider: {provider}. Supported providers are: {ClientFactory.PROVIDER_OPENAI}, {ClientFactory.PROVIDER_ANTHROPIC}, {ClientFactory.PROVIDER_MOCK}"
            logger.error(error_msg)
            raise ValueError(error_msg)