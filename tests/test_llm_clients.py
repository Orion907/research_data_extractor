# tests/test_llm_clients.py
import os
import sys
import logging
import unittest
from unittest.mock import patch

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm.client_factory import ClientFactory
from src.llm.mock_client import MockLLMClient
from src.llm.api_client import BaseLLMClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestLLMClients(unittest.TestCase):
    """Tests for LLM client interfaces"""
    
    def test_mock_client_initialization(self):
        """Test that the mock client initializes correctly"""
        client = MockLLMClient(model_name="test-model")
        self.assertEqual(client.model_name, "test-model")
    
    def test_mock_client_completion(self):
        """Test that the mock client generates completions"""
        client = MockLLMClient(model_name="test-model")
        
        # Test with different types of prompts
        test_prompts = [
            """Extract patient age and gender from: The patient is a 45-year-old female.""",
            """Extract medical conditions from: The patient has hypertension and type 2 diabetes.""",
            """Extract medications from: The patient is taking metformin 500mg twice daily."""
        ]
        
        for prompt in test_prompts:
            completion = client.generate_completion(prompt)
            self.assertIsNotNone(completion)
            self.assertGreater(len(completion), 0)
            logger.info(f"Generated completion for prompt: {prompt[:30]}...\nResponse: {completion[:100]}...")
    
    def test_client_factory(self):
        """Test the client factory creates appropriate clients"""
        
        # Test creating a mock client
        client = ClientFactory.create_client("mock", model_name="test-model")
        self.assertIsInstance(client, MockLLMClient)
        self.assertEqual(client.model_name, "test-model")
        
        # Test with invalid provider - should raise ValueError
        with self.assertRaises(ValueError):
            ClientFactory.create_client("invalid-provider")
    
    def test_client_factory_environment_vars(self):
        """Test the client factory using environment variables for API keys"""
        
        # Test with a mock environment variable
        with patch.dict('os.environ', {'MOCK_API_KEY': 'test-api-key'}):
            client = ClientFactory.create_client("mock")
            # The mock client doesn't use API keys, but we want to test the factory
            self.assertIsInstance(client, MockLLMClient)
    
    def test_available_models(self):
        """Test getting available models from the mock client"""
        client = MockLLMClient()
        models = client.get_available_models()
        
        self.assertIsInstance(models, list)
        self.assertGreater(len(models), 0)
        logger.info(f"Available models: {models}")
    
    def test_client_interface_conformance(self):
        """Test that the mock client conforms to the base client interface"""
        client = MockLLMClient()
        
        # Check that client implements all required methods from the base class
        self.assertTrue(hasattr(client, 'generate_completion'))
        self.assertTrue(hasattr(client, 'get_available_models'))
        
        # Check method signatures
        self.assertEqual(client.generate_completion.__code__.co_argcount, 4)  # self, prompt, max_tokens, temperature
        self.assertEqual(client.get_available_models.__code__.co_argcount, 1)  # self

if __name__ == "__main__":
    unittest.main()