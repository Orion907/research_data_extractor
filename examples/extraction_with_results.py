# examples/extraction_with_results.py
"""
Example script demonstrating the extraction and results management workflow
"""
import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Import from src
from src.pdf_processor.pdf_processor import extract_text_from_pdf
from src.pdf_processor.text_chunker import chunk_text
from src.utils.data_extractor import DataExtractor
from src.llm.mock_client import MockLLMClient
from src.llm.client_factory import ClientFactory
from src.utils.results_manager import ResultsManager

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_extraction_demo():
    """
    Run an extraction demo with results management
    """
    try:
        # Setup paths
        pdf_path = os.path.join(project_root, "data", "input", "sample_research_article.pdf")
        
        # Use mock client for testing without API calls
        # Override the ClientFactory's create_client method temporarily
        original_create_client = ClientFactory.create_client
        
        def mock_create_client(provider, api_key=None, model_name=None):
            logger.info("Using mock LLM client for testing")
            return MockLLMClient(api_key=api_key, model_name=model_name)
        
        # Apply the patch
        ClientFactory.create_client = mock_create_client
        
        # Extract text from PDF
        logger.info(f"Extracting text from {pdf_path}")
        text = extract_text_from_pdf(pdf_path)
        logger.info(f"Extracted {len(text)} characters from PDF")
        
        # Chunk the text
        logger.info("Chunking text...")
        chunks = chunk_text(text, chunk_size=1000, overlap=100)
        logger.info(f"Created {len(chunks)} chunks")
        
        # Create a DataExtractor with mock client and result management
        extractor = DataExtractor(provider="mock", model_name="test-extraction-model")
        
        # Extract data from chunks
        all_characteristics = {}
        for i, chunk in enumerate(chunks[:3]):  # Process first 3 chunks for brevity
            logger.info(f"Processing chunk {i+1}/{len(chunks[:3])}")
            
            # Extract from this chunk
            chunk_data = extractor.extract_patient_characteristics(
                chunk['content'],
                template_id="patient_characteristics",
                source_file=pdf_path
            )
            
            # Combine with previous results
            for key, value in chunk_data.items():
                if key not in all_characteristics:
                    all_characteristics[key] = value
            
            logger.info(f"Extracted {len(chunk_data)} characteristics from chunk {i+1}")
        
        # Use the ResultsManager to analyze results
        results_manager = ResultsManager()
        
        # List all results
        all_results = results_manager.list_results()
        logger.info(f"Total stored results: {len(all_results)}")
        
        # Export all results to CSV
        csv_path = results_manager.export_to_csv()
        logger.info(f"Exported all results to {csv_path}")
        
        # Get statistics
        stats = results_manager.get_result_stats()
        logger.info("Result Statistics:")
        logger.info(f"Total results: {stats['total_results']}")
        logger.info(f"Results by source: {stats['by_source']}")
        logger.info(f"Results by model: {stats['by_model']}")
        logger.info(f"Field frequency: {stats['field_frequency']}")
        
        # Restore the original method
        ClientFactory.create_client = original_create_client
        
        logger.info("Demo completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in extraction demo: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Restore the original method if there was an error
        if 'original_create_client' in locals():
            ClientFactory.create_client = original_create_client
            
        return False
    
    return True

if __name__ == "__main__":
    run_extraction_demo()