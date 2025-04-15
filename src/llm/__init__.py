"""
LLM API integration module for the research data extraction project
"""
from .api_client import BaseLLMClient
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .client_factory import ClientFactory

# Make these classes directly importable
__all__ = ['BaseLLMClient', 'OpenAIClient', 'AnthropicClient', 'ClientFactory']