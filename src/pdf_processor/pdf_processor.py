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
