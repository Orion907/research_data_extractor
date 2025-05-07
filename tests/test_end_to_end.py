# tests/test_end_to_end.py
"""
End-to-end test script for the research data extractor pipeline.
This script tests the entire pipeline using a mock LLM client (no API calls).
"""
import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path

print("======== TEST STARTING ========")
# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Import components
from src.pdf_processor.pdf_processor import extract_text_from_pdf
from src.pdf_processor.text_chunker import chunk_text
from src.llm.mock_client import MockLLMClient
from src.utils.data_extractor import DataExtractor
from src.data_export.csv_exporter import save_to_csv
from src.utils.config_manager import ConfigManager

def setup_test_environment():
    """
    Set up the test environment, create necessary directories,
    and prepare a sample PDF file path.
    """
    logger.info("Setting up test environment")
    
    # Load configuration
    config = ConfigManager()
    
    # Create input/output directories if they don't exist
    data_dir = project_root / "data"
    input_dir = data_dir / "input"
    output_dir = data_dir / "output"
    test_output_dir = output_dir / "test_results"
    
    input_dir.mkdir(exist_ok=True, parents=True)
    test_output_dir.mkdir(exist_ok=True, parents=True)
    
    # Verify sample PDF exists
    sample_pdf_path = input_dir / "sample_research_article.pdf"
    
    if not sample_pdf_path.exists():
        logger.warning(f"Sample PDF not found at {sample_pdf_path}")
        logger.info("Please place a sample research article PDF in the data/input directory")
        return None
    
    # Output path for extracted data
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv_path = test_output_dir / f"extracted_data_{timestamp}.csv"
    
    return {
        "sample_pdf_path": sample_pdf_path,
        "output_csv_path": output_csv_path,
        "config": config
    }

def patch_llm_client():
    """
    Patch the LLM client factory to use the mock client.
    Returns the original create_client function for restoration.
    """
    from src.llm.client_factory import ClientFactory
    
    # Save original method
    original_create_client = ClientFactory.create_client
    
    # Define a patched method that returns our mock client
    def mock_create_client(provider, api_key=None, model_name=None):
        logger.info(f"Creating mock LLM client instead of {provider}")
        return MockLLMClient(api_key=api_key, model_name="mock-test-model")
    
    # Apply the patch
    ClientFactory.create_client = mock_create_client
    
    return original_create_client

def restore_llm_client(original_method):
    """
    Restore the original LLM client factory method.
    """
    from src.llm.client_factory import ClientFactory
    ClientFactory.create_client = original_method
    logger.info("Restored original LLM client factory")

def run_end_to_end_test():
    """
    Run the entire extraction pipeline from PDF to CSV output.
    """
    logger.info("=" * 50)
    logger.info("STARTING END-TO-END TEST OF RESEARCH DATA EXTRACTOR")
    logger.info("=" * 50)
    
    # Set up test environment
    env = setup_test_environment()
    if not env:
        return False
    
    # Track test metrics
    metrics = {
        "start_time": datetime.now(),
        "steps_completed": 0,
        "total_steps": 4,
        "errors": []
    }
    
    try:
        # Step 1: Extract text from PDF
        logger.info("\n== Step 1: Extracting text from PDF ==")
        try:
            extracted_text = extract_text_from_pdf(env["sample_pdf_path"])
            text_length = len(extracted_text)
            logger.info(f"Successfully extracted {text_length} characters from PDF")
            
            # Save a sample of the extracted text
            text_sample = extracted_text[:500] + ("..." if len(extracted_text) > 500 else "")
            logger.info(f"Text sample:\n{text_sample}")
            metrics["steps_completed"] += 1
            metrics["text_length"] = text_length
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            metrics["errors"].append({"step": "pdf_extraction", "error": str(e)})
            return False
        
        # Step 2: Chunk the text
        logger.info("\n== Step 2: Chunking text ==")
        try:
            # Get chunk size from config
            chunk_size = env["config"].get("pdf_processor.text_chunking.chunk_size", 1000)
            overlap = env["config"].get("pdf_processor.text_chunking.overlap", 150)
            
            chunks = chunk_text(
                extracted_text, 
                chunk_size=chunk_size, 
                overlap=overlap, 
                respect_paragraphs=True
            )
            
            logger.info(f"Created {len(chunks)} chunks")
            logger.info(f"First chunk sample:\n{chunks[0]['content'][:200]}...")
            metrics["steps_completed"] += 1
            metrics["chunks_count"] = len(chunks)
        except Exception as e:
            logger.error(f"Error chunking text: {str(e)}")
            metrics["errors"].append({"step": "text_chunking", "error": str(e)})
            return False
        
        # Step 3: Extract patient characteristics using mock LLM
        logger.info("\n== Step 3: Extracting patient characteristics using mock LLM ==")
        try:
            # Patch the LLM client factory to use mock client
            original_client_method = patch_llm_client()
            
            # Create data extractor with any provider (will be replaced with mock)
            extractor = DataExtractor(provider="anthropic")
            
            # Limit to first 3 chunks to keep the test quick
            chunk_contents = [chunk['content'] for chunk in chunks[:3]]
            metrics["chunks_processed"] = len(chunk_contents)
            
            # Extract data
            logger.info(f"Processing {len(chunk_contents)} chunks with mock LLM")
            patient_data = extractor.extract_from_chunks(chunk_contents)
            
            # Restore original client factory
            restore_llm_client(original_client_method)
            
            logger.info(f"Extracted {len(patient_data)} patient characteristics")
            logger.info(f"Extracted data sample:\n{json.dumps(patient_data, indent=2)}")
            metrics["steps_completed"] += 1
            metrics["characteristics_count"] = len(patient_data)
        except Exception as e:
            logger.error(f"Error extracting patient characteristics: {str(e)}")
            metrics["errors"].append({"step": "data_extraction", "error": str(e)})
            # Ensure we restore the client factory even if there's an error
            if "original_client_method" in locals():
                restore_llm_client(original_client_method)
            return False
        
        # Step 4: Save to CSV
        logger.info("\n== Step 4: Saving data to CSV ==")
        try:
            # Convert data to format suitable for CSV
            csv_data = [{"Characteristic": k, "Value": v} for k, v in patient_data.items()]
            
            # Save to CSV
            save_to_csv(csv_data, env["output_csv_path"])
            logger.info(f"Data successfully saved to {env['output_csv_path']}")
            metrics["steps_completed"] += 1
            metrics["output_path"] = str(env["output_csv_path"])
        except Exception as e:
            logger.error(f"Error saving data to CSV: {str(e)}")
            metrics["errors"].append({"step": "csv_export", "error": str(e)})
            return False
        
        # Calculate test duration
        metrics["end_time"] = datetime.now()
        metrics["duration_seconds"] = (metrics["end_time"] - metrics["start_time"]).total_seconds()
        
        # Print test summary
        logger.info("\n" + "=" * 50)
        logger.info("END-TO-END TEST COMPLETED SUCCESSFULLY")
        logger.info(f"Steps completed: {metrics['steps_completed']}/{metrics['total_steps']}")
        logger.info(f"Time taken: {metrics['duration_seconds']:.2f} seconds")
        logger.info(f"Text length: {metrics['text_length']} characters")
        logger.info(f"Chunks created: {metrics['chunks_count']}")
        logger.info(f"Chunks processed: {metrics['chunks_processed']}")
        logger.info(f"Characteristics extracted: {metrics['characteristics_count']}")
        logger.info(f"Output saved to: {metrics['output_path']}")
        logger.info("=" * 50)
        
        return True
    
    except Exception as e:
        logger.error(f"Unexpected error in end-to-end test: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = run_end_to_end_test()
    if not success:
        logger.error("End-to-end test failed")
        sys.exit(1)