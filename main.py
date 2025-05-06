# main.py (modified)
"""
Main entry point for the PDF Data Extraction application.
"""
import os
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Update imports to match your project structure
from src.pdf_processor.pdf_processor import extract_text_from_pdf
from src.pdf_processor.text_chunker import chunk_text
from src.utils.data_extractor import DataExtractor
from src.data_export.csv_exporter import save_to_csv
from src.utils.data_validator import DataValidator  # Import the new validator

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to orchestrate the data extraction process."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Extract patient data from research PDFs')
    parser.add_argument('--pdf', default='data/input/sample_research_article.pdf', 
                       help='Path to the PDF file')
    parser.add_argument('--output', default='data/output/patient_data.csv',
                       help='Path to the output CSV file')
    parser.add_argument('--provider', default='anthropic',
                       help='LLM provider to use (openai, anthropic, mock)')
    parser.add_argument('--model', default=None,
                       help='Model name to use (provider-specific)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode with mock LLM client')
    args = parser.parse_args()
    
    # Use mock client in debug mode
    if args.debug:
        args.provider = 'mock'
        logger.info("Debug mode enabled, using mock LLM client")
    
    pdf_path = args.pdf
    output_path = args.output
    
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
    
    # Step 3: Extract patient data using LLM with validation
    logger.info("Extracting patient data using LLM")
    try:
        # Initialize the DataValidator
        validator = DataValidator()
        
        # Initialize the DataExtractor with validation
        extractor = DataExtractor(
            provider=args.provider, 
            model_name=args.model,
            validator=validator
        )
        
        # Extract data from the chunks
        chunk_contents = [chunk['content'] for chunk in chunks[:3]]  # Limit to first 3 chunks for testing
        
        # Process with source file information for analytics
        patient_data = extractor.extract_from_chunks(
            chunk_contents,
            merge=True,
            source_file=os.path.basename(pdf_path)
        )
        
        # Log validation statistics
        logger.info(f"Successfully extracted patient data with {len(patient_data)} characteristics")
        
        # Add metadata about the extraction
        patient_data['_metadata'] = {
            'source_file': os.path.basename(pdf_path),
            'extraction_date': datetime.now().isoformat(),
            'model_used': extractor.model_name,
            'chunks_processed': len(chunk_contents)
        }
        
    except Exception as e:
        logger.error(f"Error extracting patient data: {str(e)}")
        return
    
    # Step 4: Save data to CSV
    logger.info(f"Saving patient data to CSV: {output_path}")
    try:
        # Process metadata separately
        metadata = patient_data.pop('_metadata', {})
        
        # Convert patient_data dict to a format suitable for CSV
        csv_data = []
        
        # Add a row for each characteristic
        for k, v in patient_data.items():
            # Handle list values by joining with commas
            if isinstance(v, list):
                value = "; ".join(str(item) for item in v)
            else:
                value = v
                
            csv_data.append({"Characteristic": k, "Value": value})
        
        # Add metadata at the end
        for k, v in metadata.items():
            csv_data.append({"Characteristic": f"_meta_{k}", "Value": v})
        
        # Save to CSV
        save_to_csv(csv_data, output_path)
        logger.info("Data successfully saved to CSV")
    except Exception as e:
        logger.error(f"Error saving data to CSV: {str(e)}")
        return
    
    logger.info("Process completed successfully!")

if __name__ == "__main__":
    main()