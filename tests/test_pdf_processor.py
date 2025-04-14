"""
Test module for PDF extraction functionality
"""
import os
import sys
import logging

# Add the src directory to the Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import functions from your project
from src.pdf_processing.pdf_processor import extract_text_from_pdf

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_extract_text_from_pdf():
    """
    Test the PDF extraction functionality with a sample PDF.
    """
    # Path to a sample PDF file - adjust path for new directory structure
    sample_pdf_path = os.path.join(os.path.dirname(__file__), "..", "data", "input", "sample_research_article.pdf")
    
    # Check if the sample file exists
    if not os.path.exists(sample_pdf_path):
        logger.error(f"Sample PDF file not found: {sample_pdf_path}")
        print("Please ensure a sample PDF file is available for testing.")
        return False
    
    try:
        # Extract text from the sample PDF
        logger.info(f"Testing extraction with: {sample_pdf_path}")
        extracted_text = extract_text_from_pdf(sample_pdf_path)
        
        # Check if text was extracted successfully
        if not extracted_text:
            logger.warning("No text was extracted from the sample PDF.")
            print("Test failed: No text extracted.")
            return False
        
        # Print a preview of the extracted text
        preview_length = min(500, len(extracted_text))
        print(f"Preview of extracted text ({preview_length} characters):")
        print("-" * 50)
        print(extracted_text[:preview_length] + "...")
        print("-" * 50)
        
        # Save the extracted text to a file for inspection
        output_file = os.path.join(os.path.dirname(__file__), "..", "data", "output", "extracted_text_sample.txt")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(extracted_text)
        
        logger.info(f"Extracted text saved to: {output_file}")
        print(f"Full extracted text saved to: {output_file}")
        
        return True
    
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        print(f"Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    # Run the test function if this script is executed directly
    test_successful = test_extract_text_from_pdf()
    print(f"Test completed. Success: {test_successful}")