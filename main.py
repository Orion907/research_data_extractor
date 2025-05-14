# main.py - modified for testing with mock client
"""
Main entry point for the PDF Data Extraction application.
"""
import os
import logging
from dotenv import load_dotenv

# Update imports to match your actual project structure
from src.pdf_processor.pdf_processor import extract_text_from_pdf
from src.pdf_processor.text_chunker import chunk_text
from src.utils.data_extractor import DataExtractor
from src.data_export.csv_exporter import save_to_csv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to orchestrate the data extraction process."""
    # Sample usage
    pdf_path = os.path.join("data", "input", "sample_research_article.pdf")
    output_path = os.path.join("data", "output", "patient_data.csv")
    
    # Step 1: Extract text from PDF
    logger.info(f"Extracting text from PDF: {pdf_path}")
    try:
        text = extract_text_from_pdf(pdf_path)
        logger.info(f"Successfully extracted {len(text)} characters of text")
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return
    
    # Step 2: Chunk the text for LLM processing
    logger.info("Chunking text for LLM processing")
    try:
        chunks = chunk_text(text, chunk_size=1000, overlap=100)
        logger.info(f"Created {len(chunks)} text chunks")
    except Exception as e:
        logger.error(f"Error chunking text: {str(e)}")
        return
    
    # Step 3: Extract patient data using LLM
    logger.info("Extracting patient data using LLM")
    try:
        # Initialize the DataExtractor with the mock client instead of Anthropic
        extractor = DataExtractor(provider="mock")  # Changed from "anthropic" to "mock"
        
        # Process all chunks to get a more complete extraction (not just the first 3)
        chunk_contents = [chunk['content'] for chunk in chunks]
        patient_data = extractor.extract_from_chunks(chunk_contents)
        
        logger.info(f"Successfully extracted patient data with {len(patient_data)} characteristics")
    except Exception as e:
        logger.error(f"Error extracting patient data: {str(e)}")
        return
    
    # Step 4: Save data to CSV
    logger.info(f"Saving patient data to CSV: {output_path}")
    try:
        # Convert patient_data dict to a format suitable for CSV
        csv_data = [{"Characteristic": k, "Value": v} for k, v in patient_data.items()]
        save_to_csv(csv_data, output_path)
        logger.info("Data successfully saved to CSV")
    except Exception as e:
        logger.error(f"Error saving data to CSV: {str(e)}")
        return
    
    logger.info("Process completed successfully!")

if __name__ == "__main__":
    main()