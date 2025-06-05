# src/utils/zip_processor.py
"""
Module for processing ZIP archives containing PDF files
"""
import os
import zipfile
import logging
import tempfile
from typing import List, Dict, Tuple
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class ZipProcessor:
    """
    Processes ZIP archives to extract PDF files for batch processing
    """
    
    def __init__(self, max_files=50, max_file_size_mb=100):
        """
        Initialize the ZIP processor
        
        Args:
            max_files (int): Maximum number of PDF files to extract
            max_file_size_mb (int): Maximum size per PDF file in MB
        """
        self.max_files = max_files
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        logger.info(f"Initialized ZipProcessor with max {max_files} files, {max_file_size_mb}MB per file")
    
    def extract_pdfs_from_zip(self, zip_file_data, temp_dir=None) -> Tuple[List[Dict], List[str]]:
        """
        Extract PDF files from a ZIP archive
        
        Args:
            zip_file_data: Binary data of the ZIP file
            temp_dir (str, optional): Directory to extract files to
            
        Returns:
            Tuple[List[Dict], List[str]]: (extracted_files, errors)
                - extracted_files: List of dicts with 'name', 'path', 'size' keys
                - errors: List of error messages
        """
        extracted_files = []
        errors = []
        
        # Create temporary directory if not provided
        if temp_dir is None:
            temp_dir = tempfile.mkdtemp()
        
        try:
            # Create a temporary file for the ZIP data
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
                temp_zip.write(zip_file_data)
                temp_zip_path = temp_zip.name
            
            # Extract ZIP contents
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                # Get list of files in ZIP
                file_list = zip_ref.namelist()
                logger.info(f"Found {len(file_list)} files in ZIP archive")
                
                # Filter for PDF files
                pdf_files = [f for f in file_list if f.lower().endswith('.pdf')]
                
                if not pdf_files:
                    errors.append("No PDF files found in ZIP archive")
                    return extracted_files, errors
                
                if len(pdf_files) > self.max_files:
                    errors.append(f"Too many PDF files ({len(pdf_files)}). Maximum allowed: {self.max_files}")
                    pdf_files = pdf_files[:self.max_files]
                
                # Extract each PDF file
                for pdf_file in pdf_files:
                    try:
                        # Skip directories and hidden files
                        if pdf_file.endswith('/') or os.path.basename(pdf_file).startswith('.'):
                            continue
                        
                        # Get file info
                        file_info = zip_ref.getinfo(pdf_file)
                        
                        # Check file size
                        if file_info.file_size > self.max_file_size_bytes:
                            errors.append(f"File {pdf_file} too large ({file_info.file_size / (1024*1024):.1f}MB). Maximum: {self.max_file_size_bytes / (1024*1024)}MB")
                            continue
                        
                        # Extract file
                        zip_ref.extract(pdf_file, temp_dir)
                        
                        # Get the extracted file path
                        extracted_path = os.path.join(temp_dir, pdf_file)
                        
                        # Verify file was extracted and is readable
                        if os.path.exists(extracted_path) and os.path.getsize(extracted_path) > 0:
                            extracted_files.append({
                                'name': os.path.basename(pdf_file),
                                'path': extracted_path,
                                'size': file_info.file_size,
                                'original_path': pdf_file
                            })
                            logger.debug(f"Successfully extracted: {pdf_file}")
                        else:
                            errors.append(f"Failed to extract or verify file: {pdf_file}")
                    
                    except Exception as e:
                        error_msg = f"Error extracting {pdf_file}: {str(e)}"
                        errors.append(error_msg)
                        logger.error(error_msg)
            
            # Clean up temporary ZIP file
            os.unlink(temp_zip_path)
            
            logger.info(f"Successfully extracted {len(extracted_files)} PDF files from ZIP archive")
            
        except zipfile.BadZipFile:
            errors.append("Invalid ZIP file format")
        except Exception as e:
            error_msg = f"Error processing ZIP file: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
        
        return extracted_files, errors
    
    def validate_zip_file(self, zip_file_data) -> Tuple[bool, List[str], Dict]:
        """
        Validate ZIP file without extracting
        
        Args:
            zip_file_data: Binary data of the ZIP file
            
        Returns:
            Tuple[bool, List[str], Dict]: (is_valid, errors, info)
                - is_valid: Whether the ZIP file is valid
                - errors: List of validation errors
                - info: Dictionary with ZIP file information
        """
        errors = []
        info = {}
        
        try:
            # Create a temporary file for validation
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
                temp_zip.write(zip_file_data)
                temp_zip_path = temp_zip.name
            
            with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                # Test ZIP integrity
                bad_files = zip_ref.testzip()
                if bad_files:
                    errors.append(f"ZIP file contains corrupted files: {bad_files}")
                
                # Get file information
                file_list = zip_ref.namelist()
                pdf_files = [f for f in file_list if f.lower().endswith('.pdf')]
                
                info = {
                    'total_files': len(file_list),
                    'pdf_files': len(pdf_files),
                    'pdf_file_names': [os.path.basename(f) for f in pdf_files],
                    'total_size': sum(zip_ref.getinfo(f).file_size for f in pdf_files)
                }
                
                # Validation checks
                if info['pdf_files'] == 0:
                    errors.append("No PDF files found in ZIP archive")
                
                if info['pdf_files'] > self.max_files:
                    errors.append(f"Too many PDF files ({info['pdf_files']}). Maximum allowed: {self.max_files}")
                
                # Check individual file sizes
                oversized_files = []
                for pdf_file in pdf_files:
                    file_info = zip_ref.getinfo(pdf_file)
                    if file_info.file_size > self.max_file_size_bytes:
                        oversized_files.append(f"{os.path.basename(pdf_file)} ({file_info.file_size / (1024*1024):.1f}MB)")
                
                if oversized_files:
                    errors.append(f"Files exceed size limit: {', '.join(oversized_files)}")
            
            # Clean up
            os.unlink(temp_zip_path)
            
        except zipfile.BadZipFile:
            errors.append("Invalid ZIP file format")
        except Exception as e:
            errors.append(f"Error validating ZIP file: {str(e)}")
        
        is_valid = len(errors) == 0
        return is_valid, errors, info