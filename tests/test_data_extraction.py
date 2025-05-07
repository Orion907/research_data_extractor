# tests/test_data_extraction.py
import os
import sys
import logging
import unittest
from unittest.mock import patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.data_extractor import DataExtractor
from src.llm.mock_client import MockLLMClient
from src.llm.client_factory import ClientFactory

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestDataExtraction(unittest.TestCase):
    """Tests for data extraction functionality"""
    
    def setUp(self):
        """Set up test case - create mock client and patch the factory"""
        # Create a patch for the ClientFactory to always return our mock client
        self.factory_patcher = patch('src.llm.client_factory.ClientFactory.create_client')
        self.mock_create_client = self.factory_patcher.start()
        
        # Set up a mock client to return controlled responses
        self.mock_client = MockLLMClient(model_name="test-model")
        self.mock_create_client.return_value = self.mock_client
    
    def tearDown(self):
        """Clean up after test case - stop all patches"""
        self.factory_patcher.stop()
    
    def test_extraction_from_single_chunk(self):
        """Test extracting data from a single text chunk"""
        # Create a sample text chunk
        test_chunk = """
        The study included 50 patients with heart failure.
        The mean age was 67 years (range 45-85), and 60% were male.
        All patients had NYHA class III or IV heart failure with a mean ejection fraction of 30%.
        Patients with a history of myocardial infarction within 3 months were excluded.
        """
        
        # Mock the client's generate_completion method to return a specific response
        mock_response = """
        {
            "sample_size": "50 patients",
            "condition": "heart failure",
            "age": {
                "mean": "67 years",
                "range": "45-85 years"
            },
            "gender": "60% male",
            "disease_characteristics": {
                "NYHA_class": "III or IV",
                "mean_ejection_fraction": "30%"
            },
            "exclusion_criteria": ["myocardial infarction within 3 months"]
        }
        """
        self.mock_client.generate_completion = MagicMock(return_value=mock_response)
        
        # Create a DataExtractor with the mocked client
        extractor = DataExtractor(provider="mock", model_name="test-model")
        
        # Extract data from the test chunk
        result = extractor.extract_patient_characteristics(test_chunk)
        
        # Verify the extraction results
        self.assertIsInstance(result, dict)
        self.assertIn("sample_size", result)
        self.assertEqual(result["sample_size"], "50 patients")
        
        logger.info(f"Extraction result: {result}")
    
    def test_extraction_from_multiple_chunks(self):
        """Test extracting data from multiple text chunks"""
        # Create sample text chunks
        chunks = [
            """
            The study included 50 patients with heart failure.
            The mean age was 67 years (range 45-85), and 60% were male.
            """,
            """
            All patients had NYHA class III or IV heart failure with a mean ejection fraction of 30%.
            Patients with a history of myocardial infarction within 3 months were excluded.
            """,
            """
            At baseline, 65% of patients were taking ACE inhibitors and 48% were on beta-blockers.
            The average follow-up period was 24 months.
            """
        ]
        
        # Set up different responses for each chunk
        responses = [
            """
            {
                "sample_size": "50 patients",
                "condition": "heart failure",
                "age": {
                    "mean": "67 years",
                    "range": "45-85 years"
                },
                "gender": "60% male"
            }
            """,
            """
            {
                "disease_characteristics": {
                    "NYHA_class": "III or IV",
                    "mean_ejection_fraction": "30%"
                },
                "exclusion_criteria": ["myocardial infarction within 3 months"]
            }
            """,
            """
            {
                "medications": {
                    "ACE_inhibitors": "65% of patients",
                    "beta_blockers": "48% of patients"
                },
                "follow_up_period": "24 months"
            }
            """
        ]
        
        # Create a side effect function to return different responses for each call
        self.mock_client.generate_completion = MagicMock(side_effect=responses)
        
        # Create a DataExtractor with the mocked client
        extractor = DataExtractor(provider="mock", model_name="test-model")
        
        # Extract data from multiple chunks
        result = extractor.extract_from_chunks(chunks)
        
        # Verify the merged extraction results
        self.assertIsInstance(result, dict)
        self.assertIn("sample_size", result)
        self.assertIn("disease_characteristics", result)
        self.assertIn("medications", result)
        
        logger.info(f"Multi-chunk extraction result: {result}")
    
    def test_extraction_with_invalid_response(self):
        """Test handling of invalid JSON responses"""
        # Create a sample text chunk
        test_chunk = """
        The study included 50 patients with heart failure.
        """
        
        # Mock an invalid JSON response
        invalid_response = """
        This is not valid JSON
        - Sample size: 50 patients
        - Condition: heart failure
        """
        self.mock_client.generate_completion = MagicMock(return_value=invalid_response)
        
        # Create a DataExtractor with the mocked client
        extractor = DataExtractor(provider="mock", model_name="test-model")
        
        # Extract data - should not raise an exception despite invalid JSON
        result = extractor.extract_patient_characteristics(test_chunk)
        
        # Verify the result is a dict with key-value pairs
        self.assertIsInstance(result, dict)
        self.assertGreater(len(result), 0)
        
        logger.info(f"Extraction result from invalid JSON: {result}")

if __name__ == "__main__":
    unittest.main()