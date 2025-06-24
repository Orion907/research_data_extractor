"""
Document processing module for PDF text extraction and chunking.

This module provides a centralized interface for document processing operations
including PDF text extraction, text chunking, file validation, and batch processing.
"""

import os
import tempfile
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from pathlib import Path

from src.pdf_processor.pdf_processor import extract_text_from_pdf
from src.pdf_processor.text_chunker import chunk_text
from src.utils.zip_processor import ZipProcessor
from src.app.file_handlers import FileHandlerUtils

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Handles document processing operations including PDF extraction,
    text chunking, file validation, and batch processing.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the DocumentProcessor.
        
        Args:
            config: Configuration dictionary for processing parameters
        """
        self.config = config or {}
        self.zip_processor = ZipProcessor(
            max_files=self.config.get('batch_processing.max_files', 50),
            max_file_size_mb=self.config.get('batch_processing.max_file_size_mb', 100)
        )
    
    def extract_text(self, file_path: str, keep_page_breaks: bool = True) -> str:
        """
        Extract text from a PDF file.
        
        Args:
            file_path: Path to the PDF file
            keep_page_breaks: Whether to preserve page breaks in the text
            
        Returns:
            Extracted text content
            
        Raises:
            FileNotFoundError: If the PDF file doesn't exist
            ValueError: If no text could be extracted
            Exception: For other processing errors
        """
        logger.info(f"Extracting text from PDF: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")
        
        text = extract_text_from_pdf(file_path, keep_page_breaks)
        
        if not text.strip():
            raise ValueError("No text could be extracted from PDF")
        
        logger.info(f"Successfully extracted {len(text)} characters from {file_path}")
        return text
    
    def chunk_document_text(
        self, 
        text: str, 
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None,
        respect_paragraphs: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        """
        Chunk text into smaller segments for processing.
        
        Args:
            text: Text to chunk
            chunk_size: Maximum size of each chunk (uses config default if None)
            overlap: Overlap between chunks (uses config default if None)
            respect_paragraphs: Whether to respect paragraph boundaries (uses config default if None)
            
        Returns:
            List of chunk dictionaries with content, index, start_char, end_char
        """
        # Use provided values or fall back to config defaults
        chunk_size = chunk_size or self.config.get('pdf_processor.text_chunking.chunk_size', 1000)
        overlap = overlap or self.config.get('pdf_processor.text_chunking.overlap', 100)
        respect_paragraphs = (
            respect_paragraphs 
            if respect_paragraphs is not None 
            else self.config.get('pdf_processor.text_chunking.respect_paragraphs', True)
        )
        
        logger.info(f"Chunking text with size={chunk_size}, overlap={overlap}, respect_paragraphs={respect_paragraphs}")
        
        chunks = chunk_text(
            text=text,
            chunk_size=chunk_size,
            overlap=overlap,
            respect_paragraphs=respect_paragraphs
        )
        
        logger.info(f"Created {len(chunks)} text chunks")
        return chunks
    
    def process_uploaded_file(
        self, 
        uploaded_file, 
        temp_dir: str = "data/input",
        filename_prefix: str = "temp_"
    ) -> Tuple[str, str, List[Dict[str, Any]]]:
        """
        Process an uploaded PDF file through the complete workflow.
        
        Args:
            uploaded_file: Streamlit uploaded file object
            temp_dir: Directory to save temporary file
            filename_prefix: Prefix for temporary filename
            
        Returns:
            Tuple of (temp_file_path, extracted_text, chunks)
            
        Raises:
            Exception: If file processing fails
        """
        logger.info(f"Processing uploaded file: {uploaded_file.name}")
        
        # Save uploaded file temporarily
        temp_path = FileHandlerUtils.save_uploaded_file(
            uploaded_file, temp_dir, filename_prefix
        )
        
        if not temp_path:
            raise Exception("Failed to save uploaded file")
        
        try:
            # Extract text from PDF
            text = self.extract_text(temp_path)
            
            # Chunk the text
            chunks = self.chunk_document_text(text)
            
            logger.info(f"Successfully processed {uploaded_file.name}: {len(text)} chars, {len(chunks)} chunks")
            return temp_path, text, chunks
            
        except Exception as e:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                os.remove(temp_path)
            logger.error(f"Error processing {uploaded_file.name}: {str(e)}")
            raise
    
    def validate_pdf_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a PDF file for processing.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not os.path.exists(file_path):
                return False, f"File does not exist: {file_path}"
            
            if not file_path.lower().endswith('.pdf'):
                return False, "File is not a PDF"
            
            # Try to extract text to validate
            text = self.extract_text(file_path)
            if not text.strip():
                return False, "PDF contains no extractable text"
                
            return True, None
            
        except Exception as e:
            return False, f"PDF validation failed: {str(e)}"
    
    def process_zip_archive(
        self, 
        zip_data: bytes, 
        temp_dir: str = "data/input"
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Validate and extract PDFs from a ZIP archive.
        
        Args:
            zip_data: ZIP file data as bytes
            temp_dir: Directory to extract files to
            
        Returns:
            Tuple of (is_valid, validation_errors, zip_info)
        """
        logger.info("Processing ZIP archive for PDF extraction")
        
        # Validate ZIP file
        is_valid, validation_errors, zip_info = self.zip_processor.validate_zip_file(zip_data)
        
        if not is_valid:
            return False, validation_errors, zip_info
        
        # Extract PDFs if validation passed
        try:
            extracted_files = self.zip_processor.extract_pdfs(zip_data, temp_dir)
            zip_info.update({
                'extracted_files': extracted_files,
                'extraction_successful': True
            })
            
            logger.info(f"Successfully extracted {len(extracted_files)} PDFs from ZIP")
            return True, [], zip_info
            
        except Exception as e:
            logger.error(f"Error extracting ZIP archive: {str(e)}")
            zip_info.update({
                'extraction_error': str(e),
                'extraction_successful': False
            })
            return False, [f"Extraction failed: {str(e)}"], zip_info
    
    def process_batch_files(
        self, 
        files: List, 
        chunk_size: Optional[int] = None,
        overlap: Optional[int] = None,
        temp_dir: str = "data/input"
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process multiple PDF files in batch.
        
        Args:
            files: List of file objects to process
            chunk_size: Chunk size for text processing
            overlap: Overlap between chunks
            temp_dir: Directory for temporary files
            
        Returns:
            Tuple of (successful_results, failed_files)
        """
        logger.info(f"Starting batch processing of {len(files)} files")
        
        successful_results = []
        failed_files = []
        
        # Use provided values or config defaults
        chunk_size = chunk_size or self.config.get('pdf_processor.text_chunking.chunk_size', 1000)
        overlap = overlap or self.config.get('pdf_processor.text_chunking.overlap', 100)
        
        for file_obj in files:
            try:
                logger.info(f"Processing batch file: {file_obj.name}")
                
                # Save file temporarily
                temp_path = os.path.join(temp_dir, f"batch_temp_{file_obj.name}")
                os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                
                with open(temp_path, "wb") as f:
                    f.write(file_obj.getbuffer())
                
                # Extract text from PDF
                text = self.extract_text(temp_path)
                
                # Chunk the text
                chunks = self.chunk_document_text(text, chunk_size, overlap)
                
                # Store successful result
                result = {
                    'file_name': file_obj.name,
                    'temp_path': temp_path,
                    'text': text,
                    'chunks': chunks,
                    'chunk_count': len(chunks),
                    'character_count': len(text)
                }
                successful_results.append(result)
                
                logger.info(f"Successfully processed {file_obj.name}: {len(chunks)} chunks")
                
            except Exception as e:
                error_msg = str(e)
                failed_files.append({
                    'file_name': file_obj.name,
                    'error': error_msg
                })
                logger.error(f"Failed to process {file_obj.name}: {error_msg}")
                
                # Clean up temp file if it exists
                temp_path = os.path.join(temp_dir, f"batch_temp_{file_obj.name}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to clean up temp file {temp_path}: {cleanup_error}")
        
        logger.info(f"Batch processing complete: {len(successful_results)} successful, {len(failed_files)} failed")
        return successful_results, failed_files
    
    def cleanup_temp_files(self, file_paths: List[str]) -> None:
        """
        Clean up temporary files.
        
        Args:
            file_paths: List of file paths to remove
        """
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"Cleaned up temp file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temp file {file_path}: {str(e)}")
    
    def get_processing_stats(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate processing statistics from batch results.
        
        Args:
            results: List of processing results
            
        Returns:
            Dictionary of processing statistics
        """
        if not results:
            return {
                'total_files': 0,
                'total_chunks': 0,
                'total_characters': 0,
                'average_chunks_per_file': 0,
                'average_characters_per_file': 0
            }
        
        total_chunks = sum(result.get('chunk_count', 0) for result in results)
        total_characters = sum(result.get('character_count', 0) for result in results)
        
        return {
            'total_files': len(results),
            'total_chunks': total_chunks,
            'total_characters': total_characters,
            'average_chunks_per_file': total_chunks / len(results),
            'average_characters_per_file': total_characters / len(results)
        }