# tests/test_integration_workflow.py
import os
import sys
import logging
import unittest
from unittest.mock import patch, MagicMock
import shutil

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pdf_processor.pdf_processor import extract_text_from_pdf
from src.pdf_processor.text_chunker import chunk_text
from src.utils.data_extractor import DataExtractor
from src.data_export.csv_exporter import save_to_csv
from src.llm.mock_client import MockLLMClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestIntegrationWorkflow(unittest.TestCase):
    """Integration test for the full data extraction workflow"""
    
    def setUp(self):
        """Set up test case - prepare directories and mock client"""
        # Get project root directory
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Set up paths
        self.data_dir = os.path.join(self.project_root, "data")
        self.input_dir = os.path.join(self.data_dir, "input")
        self.output_dir = os.path.join(self.data_dir, "output", "integration_test")
        
        # Ensure directories exist
        os.makedirs(self.input_dir, exist_ok=True)
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Path to sample PDF
        self.sample_pdf_path = os.path.join(self.input_dir, "sample_research_article.pdf")
        
        # Set up a patch for the ClientFactory to return our mock client
        self.factory_patcher = patch('src.llm.client_factory.ClientFactory.create_client')
        self.mock_create_client = self.factory_patcher.start()
        
        # Create a mock client with predetermined responses
        self.mock_client = MockLLMClient(model_name="test-model")
        
        # Configure the mock to return a specific response
        mock_response = """
        {
            "sample_size": "50 patients",
            "age": {
                "mean": "67 years",
                "range": "45-85 years"
            },
            "gender": "60% male, 40% female",
            "condition": "heart failure",
            "disease_characteristics": {
                "NYHA_class": "III or IV",
                "ejection_fraction": "30%"
            },
            "exclusion_criteria": ["myocardial infarction within 3 months"],
            "medications": {
                "ACE_inhibitors": "65% of patients",
                "beta_blockers": "48% of patients"
            }
        }
        """
        
        self.mock_client.generate_completion = MagicMock(return_value=mock_response)
        self.mock_create_client.return_value = self.mock_client
    
    def tearDown(self):
        """Clean up after test case - stop patches and clean output directory"""
        self.factory_patcher.stop()
    
    def test_full_extraction_workflow(self):
        """Test the full extraction workflow from PDF to CSV output"""
        # If sample PDF doesn't exist, create a synthetic text file for testing
        if not os.path.exists(self.sample_pdf_path):
            test_text = """
            Abstract
            
            Background: Previous studies have shown that patient characteristics can influence treatment outcomes.
            
            Methods: We conducted a randomized controlled trial with 50 patients with heart failure.
            The mean age was 67 years (range 45-85), and 60% were male.
            All patients had NYHA class III or IV heart failure with a mean ejection fraction of 30%.
            Patients with a history of myocardial infarction within 3 months were excluded.
            At baseline, 65% of patients were taking ACE inhibitors and 48% were on beta-blockers.
            
            Results: The treatment group showed a significant reduction in systolic blood pressure.
            
            Conclusion: Age should be considered when prescribing medication X.
            """
            
            # Create a text file instead of PDF for testing
            text_file_path = os.path.join(self.output_dir, "synthetic_text.txt")
            with open(text_file_path, "w", encoding="utf-8") as f:
                f.write(test_text)
                
            # Use this text directly instead of PDF extraction
            extracted_text = test_text
            logger.info("Using synthetic text for testing (no sample PDF available)")
        else:
            # Extract text from the PDF
            extracted_text = extract_text_from_pdf(self.sample_pdf_path)
            logger.info(f"Extracted {len(extracted_text)} characters from {self.sample_pdf_path}")
        
        # Verify text was extracted
        self.assertIsNotNone(extracted_text)
        self.assertGreater(len(extracted_text), 0)
        
        # Chunk the text
        chunks = chunk_text(
            text=extracted_text,
            chunk_size=800,
            overlap=100,
            respect_paragraphs=True
        )
        
        # Verify chunking
        self.assertGreater(len(chunks), 0)
        logger.info(f"Created {len(chunks)} chunks from the text")
        
        # Create a DataExtractor with our mocked client
        extractor = DataExtractor(provider="mock", model_name="test-model")
        
        # Extract data from chunks
        chunk_contents = [chunk['content'] for chunk in chunks[:3]]  # Limit to first 3 chunks for testing
        patient_data = extractor.extract_from_chunks(chunk_contents)
        
        # Verify extraction results
        self.assertIsInstance(patient_data, dict)
        self.assertGreater(len(patient_data), 0)
        logger.info(f"Extracted {len(patient_data)} patient characteristics")
        
        # Convert to CSV format
        csv_data = [{"Characteristic": k, "Value": str(v)} for k, v in patient_data.items()]
        
        # Save to CSV
        csv_path = os.path.join(self.output_dir, "patient_data.csv")
        save_to_csv(csv_data, csv_path)
        
        # Verify CSV was created
        self.assertTrue(os.path.exists(csv_path))
        logger.info(f"Saved patient data to CSV: {csv_path}")
        
        # Verify end-to-end workflow
        logger.info("Successfully completed end-to-end extraction workflow")

if __name__ == "__main__":
    unittest.main()