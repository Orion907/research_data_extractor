"""
Test module for configuration management
"""
import os
import sys

# Add the src directory to the Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.config_manager import ConfigManager
from src.utils import config

def test_config_manager():
    """Test the configuration manager functionality"""
    
    # Test default configuration
    print("\n=== Testing Default Configuration ===")
    default_config = ConfigManager(env="development")
    
    # Print some configuration values
    print(f"App name: {default_config.get('app.name')}")
    print(f"Debug mode: {default_config.get('app.debug')}")
    print(f"LLM provider: {default_config.get('llm.provider')}")
    print(f"Chunk size: {default_config.get('pdf_processor.text_chunking.chunk_size')}")
    
    # Test production configuration
    print("\n=== Testing Production Configuration ===")
    prod_config = ConfigManager(env="production")
    
    # Print some configuration values that should be different in production
    print(f"Debug mode: {prod_config.get('app.debug')}")
    print(f"Chunk size: {prod_config.get('pdf_processor.text_chunking.chunk_size')}")
    print(f"Output directory: {prod_config.get('output.directory')}")
    
    # Test global configuration
    print("\n=== Testing Global Configuration ===")
    print(f"App name: {config.get('app.name')}")
    print(f"Debug mode: {config.get('app.debug')}")
    
    # Test getting a non-existent value with a default
    non_existent = config.get('some.non.existent.key', 'default_value')
    print(f"Non-existent key: {non_existent}")
    
    return True

if __name__ == "__main__":
    test_config_manager()
    print("\nConfiguration test completed!")