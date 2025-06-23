"""
File handling utilities for Streamlit app

Provides safe file upload, download, and temporary file management
with proper cleanup and error handling.
"""

import os
import tempfile
import shutil
from typing import Optional, List, Tuple, Dict, Any, Union
from pathlib import Path
import streamlit as st


class FileHandlerUtils:
    """
    Utilities for safe file handling in Streamlit applications.
    
    Provides consistent patterns for file upload/download operations,
    temporary file management, and cleanup with proper error handling.
    """
    
    @staticmethod
    def save_uploaded_file(uploaded_file, target_dir: str, 
                          prefix: str = "temp_") -> Optional[str]:
        """
        Safely save an uploaded file to a target directory.
        
        Args:
            uploaded_file: Streamlit uploaded file object
            target_dir: Directory to save the file
            prefix: Prefix for the saved filename
            
        Returns:
            Path to saved file, or None if failed
        """
        try:
            # Ensure target directory exists
            os.makedirs(target_dir, exist_ok=True)
            
            # Create safe filename
            safe_filename = f"{prefix}{uploaded_file.name}"
            file_path = os.path.join(target_dir, safe_filename)
            
            # Save the file
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            return file_path
            
        except Exception as e:
            st.error(f"Error saving uploaded file: {str(e)}")
            return None
    
    @staticmethod
    def create_download_button(file_path: str, label: str, 
                             download_filename: Optional[str] = None,
                             mime_type: str = "application/octet-stream",
                             key: Optional[str] = None) -> bool:
        """
        Create a download button for a file with proper error handling.
        
        Args:
            file_path: Path to file to download
            label: Button label
            download_filename: Name for downloaded file (defaults to original name)
            mime_type: MIME type for download
            key: Unique key for button
            
        Returns:
            True if button was successfully created, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                st.error(f"File not found: {file_path}")
                return False
            
            # Use original filename if download name not provided
            if download_filename is None:
                download_filename = os.path.basename(file_path)
            
            # Read file and create download button
            with open(file_path, 'rb') as f:
                file_data = f.read()
                
            st.download_button(
                label=label,
                data=file_data,
                file_name=download_filename,
                mime=mime_type,
                key=key
            )
            return True
            
        except Exception as e:
            st.error(f"Error creating download button: {str(e)}")
            return False
    
    @staticmethod
    def get_temp_directory(suffix: str = "research_extractor") -> str:
        """
        Create a temporary directory with proper naming.
        
        Args:
            suffix: Suffix for directory name
            
        Returns:
            Path to temporary directory
        """
        return tempfile.mkdtemp(suffix=f"_{suffix}")
    
    @staticmethod
    def cleanup_temp_directory(temp_dir: str) -> bool:
        """
        Safely clean up a temporary directory.
        
        Args:
            temp_dir: Path to temporary directory
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return True
        except Exception:
            return False
    
    @staticmethod
    def ensure_output_directory(base_dir: str = "data/output") -> str:
        """
        Ensure output directory exists and return the path.
        
        Args:
            base_dir: Base directory path
            
        Returns:
            Full path to output directory
        """
        os.makedirs(base_dir, exist_ok=True)
        return base_dir
    
    @staticmethod
    def generate_output_filename(base_name: str, suffix: str = "", 
                                extension: str = ".csv",
                                include_timestamp: bool = False) -> str:
        """
        Generate a consistent output filename.
        
        Args:
            base_name: Base name for the file
            suffix: Optional suffix to append
            extension: File extension (including dot)
            include_timestamp: Whether to include timestamp
            
        Returns:
            Generated filename
        """
        from datetime import datetime
        
        # Clean base name
        clean_base = base_name.replace('.pdf', '').replace(' ', '_')
        
        # Build filename components
        parts = [clean_base]
        
        if suffix:
            parts.append(suffix)
        
        if include_timestamp:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            parts.append(timestamp)
        
        return "_".join(parts) + extension
    
    @staticmethod
    def validate_file_size(file_path: str, max_size_mb: int = 100) -> Tuple[bool, str]:
        """
        Validate file size is within limits.
        
        Args:
            file_path: Path to file to check
            max_size_mb: Maximum size in MB
            
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            size_bytes = os.path.getsize(file_path)
            size_mb = size_bytes / (1024 * 1024)
            
            if size_mb > max_size_mb:
                return False, f"File size ({size_mb:.1f}MB) exceeds limit ({max_size_mb}MB)"
            
            return True, f"File size OK ({size_mb:.1f}MB)"
            
        except Exception as e:
            return False, f"Error checking file size: {str(e)}"
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """
        Get comprehensive information about a file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with file information
        """
        try:
            if not os.path.exists(file_path):
                return {"exists": False, "error": "File not found"}
            
            stat = os.stat(file_path)
            
            return {
                "exists": True,
                "name": os.path.basename(file_path),
                "size_bytes": stat.st_size,
                "size_mb": stat.st_size / (1024 * 1024),
                "modified": stat.st_mtime,
                "extension": Path(file_path).suffix.lower()
            }
            
        except Exception as e:
            return {"exists": False, "error": str(e)}


class BatchFileHandler:
    """
    Specialized file handler for batch processing operations.
    
    Handles multiple files, ZIP archives, and temporary file management
    with proper cleanup and error handling.
    """
    
    def __init__(self, temp_base_dir: Optional[str] = None):
        """
        Initialize batch file handler.
        
        Args:
            temp_base_dir: Base directory for temporary files
        """
        self.temp_base_dir = temp_base_dir or tempfile.gettempdir()
        self.active_temp_dirs: List[str] = []
    
    def create_batch_temp_dir(self) -> str:
        """
        Create a temporary directory for batch processing.
        
        Returns:
            Path to temporary directory
        """
        temp_dir = FileHandlerUtils.get_temp_directory("batch_processing")
        self.active_temp_dirs.append(temp_dir)
        return temp_dir
    
    def save_batch_files(self, uploaded_files, temp_dir: str) -> List[Dict[str, Any]]:
        """
        Save multiple uploaded files to temporary directory.
        
        Args:
            uploaded_files: List of Streamlit uploaded file objects
            temp_dir: Directory to save files
            
        Returns:
            List of file info dictionaries
        """
        saved_files = []
        
        for i, uploaded_file in enumerate(uploaded_files):
            file_path = FileHandlerUtils.save_uploaded_file(
                uploaded_file, temp_dir, f"batch_{i:03d}_"
            )
            
            if file_path:
                file_info = FileHandlerUtils.get_file_info(file_path)
                file_info.update({
                    "original_name": uploaded_file.name,
                    "temp_path": file_path,
                    "batch_index": i
                })
                saved_files.append(file_info)
        
        return saved_files
    
    def cleanup_all_temp_dirs(self) -> int:
        """
        Clean up all active temporary directories.
        
        Returns:
            Number of directories successfully cleaned up
        """
        cleaned_count = 0
        
        for temp_dir in self.active_temp_dirs:
            if FileHandlerUtils.cleanup_temp_directory(temp_dir):
                cleaned_count += 1
        
        self.active_temp_dirs.clear()
        return cleaned_count
    
    def __del__(self):
        """Cleanup on destruction."""
        self.cleanup_all_temp_dirs()


class DownloadManager:
    """
    Manager for handling multiple download operations and file generation.
    
    Provides consistent patterns for creating downloadable results
    from processing operations.
    """
    
    @staticmethod
    def create_results_download(results_data: Any, filename: str, 
                               format_type: str = "csv") -> bool:
        """
        Create a download for results data in specified format.
        
        Args:
            results_data: Data to save (list, dict, DataFrame, etc.)
            filename: Base filename
            format_type: Format type ("csv", "json", "txt")
            
        Returns:
            True if download created successfully
        """
        try:
            output_dir = FileHandlerUtils.ensure_output_directory()
            
            if format_type.lower() == "csv":
                return DownloadManager._create_csv_download(
                    results_data, output_dir, filename
                )
            elif format_type.lower() == "json":
                return DownloadManager._create_json_download(
                    results_data, output_dir, filename
                )
            else:
                st.error(f"Unsupported format type: {format_type}")
                return False
                
        except Exception as e:
            st.error(f"Error creating download: {str(e)}")
            return False
    
    @staticmethod
    def _create_csv_download(data, output_dir: str, filename: str) -> bool:
        """Create CSV download from data."""
        import pandas as pd
        from src.data_export import save_extraction_results_to_csv
        
        try:
            full_path = os.path.join(output_dir, 
                                   FileHandlerUtils.generate_output_filename(
                                       filename, extension=".csv"
                                   ))
            
            # Use existing CSV export function if data is extraction results
            if isinstance(data, list) and all(isinstance(item, dict) for item in data):
                if all('extraction' in item for item in data):
                    save_extraction_results_to_csv(data, full_path, include_chunks=False)
                else:
                    # Generic list of dicts to CSV
                    pd.DataFrame(data).to_csv(full_path, index=False)
            else:
                # Try to convert to DataFrame
                df = pd.DataFrame(data) if not isinstance(data, pd.DataFrame) else data
                df.to_csv(full_path, index=False)
            
            return FileHandlerUtils.create_download_button(
                full_path, "Download CSV", mime_type="text/csv"
            )
            
        except Exception as e:
            st.error(f"Error creating CSV download: {str(e)}")
            return False
    
    @staticmethod 
    def _create_json_download(data, output_dir: str, filename: str) -> bool:
        """Create JSON download from data."""
        import json
        
        try:
            full_path = os.path.join(output_dir,
                                   FileHandlerUtils.generate_output_filename(
                                       filename, extension=".json"
                                   ))
            
            with open(full_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            return FileHandlerUtils.create_download_button(
                full_path, "Download JSON", mime_type="application/json"
            )
            
        except Exception as e:
            st.error(f"Error creating JSON download: {str(e)}")
            return False