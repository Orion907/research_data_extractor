"""
Module for processing PDF files and extracting text.
"""
import os
import PyPDF2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') 
logger = logging.getLogger(__name__)

def extract_text_from_pdf(pdf_path, keep_page_breaks=True):
    """
    Extract text content from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        keep_page_breaks (bool): Whether to include page break newlines in output
        
    Returns:
        str: Extracted text content
    """
    try:
        with open(pdf_path, 'rb') as file:
            # Create a PDF reader object
            reader = PyPDF2.PdfReader(file)
            
            # Check if PDF has pages
            total_pages = len(reader.pages)
            if total_pages == 0:
                logger.warning(f"PDF file has no pages: {pdf_path}")
                return ""
                
            logger.info(f"Starting extraction from {pdf_path} ({total_pages} pages)")

            # Extract all text from the PDF
            text_parts = []
            for page_num in range(total_pages):
                page_text = reader.pages[page_num].extract_text()
                text_parts.append(page_text)
            
            # Join text with or without page breaks
            page_separator = '\n' if keep_page_breaks else ' '
            text = page_separator.join(text_parts)
            
            # Check if any text was extracted
            if not text.strip():
                logger.warning(f"No text could be extracted from {pdf_path}")
            else:
                logger.info(f"Successfully extracted {len(text)} characters from {pdf_path}")
                
            return text
    
    except FileNotFoundError:
        logger.error(f"PDF file not found: {pdf_path}")
        raise
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
        raise

def test_pdf_extraction():
    """
    Test the PDF extraction functionality with a sample PDF.
    """
    # Path to a sample PDF file
    sample_pdf_path = "sample_research_article.pdf"
    
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
        output_file = "extracted_text_sample.txt"
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
    test_successful = test_pdf_extraction()
    print(f"Test completed. Success: {test_successful}")

def chunk_text(text, chunk_size=1000, overlap=100):
    """
    Split text into chunks for processing by LLM.
    
    Args:
        text (str): Text to chunk
        chunk_size (int): Size of each chunk
        overlap (int): Overlap between chunks
        
    Returns:
        list: List of text chunks
    """
    # TODO: Implement chunking logic
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i + chunk_size]
        chunks.append(chunk)
    return chunks