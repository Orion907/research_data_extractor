"""
Batch coordinator module for orchestrating multi-file processing workflows.

This module provides coordination for batch processing operations including
file management, progress tracking, result aggregation, and error handling.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile

from .document_processor import DocumentProcessor
from .extraction_engine import ExtractionEngine
from src.utils.unified_analytics import Analytics

logger = logging.getLogger(__name__)


class BatchCoordinator:
    """
    Coordinates batch processing operations for multiple documents including
    parallel processing, progress tracking, and result aggregation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the BatchCoordinator.
        
        Args:
            config: Configuration dictionary for batch processing parameters
        """
        self.config = config or {}
        self.document_processor = DocumentProcessor(config)
        self.extraction_engine = ExtractionEngine(config)
        self.analytics = Analytics()
        
        # Batch processing settings
        self.max_workers = self.config.get('batch_processing.max_workers', 3)
        self.chunk_size = self.config.get('pdf_processor.text_chunking.chunk_size', 1000)
        self.overlap = self.config.get('pdf_processor.text_chunking.overlap', 100)
        
    def initialize_batch_state(self) -> Dict[str, Any]:
        """
        Initialize session state for batch processing.
        
        Returns:
            Dictionary with initial batch state values
        """
        return {
            'batch_files': [],
            'batch_processing_complete': False,
            'batch_results': [],
            'batch_chunk_size': self.chunk_size,
            'batch_overlap': self.overlap,
            'batch_provider': 'anthropic',
            'batch_model': 'claude-3-5-sonnet-20241022',
            'batch_temperature': 0.0,
            'batch_progress': 0,
            'batch_status': 'ready',
            'batch_errors': [],
            'batch_stats': {}
        }
    
    def validate_batch_files(self, files: List[Any]) -> Tuple[List[Any], List[str]]:
        """
        Validate uploaded files for batch processing.
        
        Args:
            files: List of uploaded file objects
            
        Returns:
            Tuple of (valid_files, validation_errors)
        """
        valid_files = []
        validation_errors = []
        
        for file_obj in files:
            try:
                # Check file type
                if not file_obj.name.lower().endswith('.pdf'):
                    validation_errors.append(f"{file_obj.name}: Not a PDF file")
                    continue
                
                # Check file size (basic validation)
                file_size_mb = len(file_obj.getbuffer()) / (1024 * 1024)
                max_size_mb = self.config.get('batch_processing.max_file_size_mb', 100)
                
                if file_size_mb > max_size_mb:
                    validation_errors.append(f"{file_obj.name}: File too large ({file_size_mb:.1f}MB > {max_size_mb}MB)")
                    continue
                
                valid_files.append(file_obj)
                
            except Exception as e:
                validation_errors.append(f"{file_obj.name}: Validation error - {str(e)}")
        
        logger.info(f"Validated {len(valid_files)}/{len(files)} files for batch processing")
        return valid_files, validation_errors
    
    def process_zip_archive(
        self, 
        zip_data: bytes, 
        temp_dir: str = "data/input"
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Process a ZIP archive containing PDF files.
        
        Args:
            zip_data: ZIP file data as bytes
            temp_dir: Directory to extract files to
            
        Returns:
            Tuple of (success, errors, zip_info)
        """
        logger.info("Processing ZIP archive for batch processing")
        return self.document_processor.process_zip_archive(zip_data, temp_dir)
    
    def prepare_batch_files(
        self, 
        files: List[Any], 
        temp_dir: str = "data/input"
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Prepare files for batch processing by extracting text and chunking.
        
        Args:
            files: List of file objects to prepare
            temp_dir: Directory for temporary files
            
        Returns:
            Tuple of (prepared_files, preparation_errors)
        """
        logger.info(f"Preparing {len(files)} files for batch processing")
        
        prepared_files = []
        preparation_errors = []
        
        for file_obj in files:
            try:
                # Process the file through document processor
                temp_path, text, chunks = self.document_processor.process_uploaded_file(
                    file_obj, temp_dir, "batch_temp_"
                )
                
                prepared_file = {
                    'file_name': file_obj.name,
                    'temp_path': temp_path,
                    'text': text,
                    'chunks': chunks,
                    'chunk_count': len(chunks),
                    'character_count': len(text),
                    'file_obj': file_obj
                }
                
                prepared_files.append(prepared_file)
                logger.info(f"Prepared {file_obj.name}: {len(chunks)} chunks, {len(text)} characters")
                
            except Exception as e:
                error_msg = str(e)
                preparation_errors.append({
                    'file_name': file_obj.name,
                    'error': error_msg
                })
                logger.error(f"Failed to prepare {file_obj.name}: {error_msg}")
        
        logger.info(f"Prepared {len(prepared_files)}/{len(files)} files successfully")
        return prepared_files, preparation_errors
    
    def process_single_file_batch(
        self,
        prepared_file: Dict[str, Any],
        provider: str,
        model_name: str,
        temperature: float,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Process a single file in batch mode with all its chunks.
        
        Args:
            prepared_file: Prepared file dictionary with chunks
            provider: LLM provider name
            model_name: Model name to use
            temperature: Temperature setting
            progress_callback: Optional progress callback function
            
        Returns:
            Processing result dictionary
        """
        file_name = prepared_file['file_name']
        chunks = prepared_file['chunks']
        
        logger.info(f"Processing {file_name} with {len(chunks)} chunks")
        
        if progress_callback:
            progress_callback(f"Processing {file_name}")
        
        try:
            # Process all chunks for this file
            successful_results, failed_chunks = self.extraction_engine.process_batch_file(
                file_chunks=chunks,
                file_name=file_name,
                provider=provider,
                model_name=model_name,
                temperature=temperature
            )
            
            # Aggregate results
            all_extractions = []
            for result in successful_results:
                all_extractions.append(result['extraction'])
            
            combined_extraction = '\n\n'.join(all_extractions) if all_extractions else ""
            
            result = {
                'file_name': file_name,
                'extraction_result': combined_extraction,
                'chunk_count': len(chunks),
                'successful_chunks': len(successful_results),
                'failed_chunks': len(failed_chunks),
                'character_count': prepared_file['character_count'],
                'processing_time': datetime.now().isoformat(),
                'temp_path': prepared_file['temp_path'],
                'status': 'success'
            }
            
            if failed_chunks:
                result['chunk_errors'] = failed_chunks
            
            logger.info(f"Completed {file_name}: {len(successful_results)}/{len(chunks)} chunks successful")
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to process {file_name}: {error_msg}")
            
            return {
                'file_name': file_name,
                'extraction_result': "",
                'chunk_count': len(chunks),
                'successful_chunks': 0,
                'failed_chunks': len(chunks),
                'character_count': prepared_file['character_count'],
                'processing_time': datetime.now().isoformat(),
                'temp_path': prepared_file['temp_path'],
                'status': 'failed',
                'error': error_msg
            }
    
    def execute_batch_processing(
        self,
        prepared_files: List[Dict[str, Any]],
        provider: str,
        model_name: str,
        temperature: float,
        use_parallel: bool = True,
        progress_callback: Optional[Callable] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Execute batch processing for multiple prepared files.
        
        Args:
            prepared_files: List of prepared file dictionaries
            provider: LLM provider name
            model_name: Model name to use
            temperature: Temperature setting
            use_parallel: Whether to use parallel processing
            progress_callback: Optional progress callback function
            
        Returns:
            Tuple of (successful_results, failed_files, batch_stats)
        """
        logger.info(f"Starting batch processing of {len(prepared_files)} files")
        start_time = datetime.now()
        
        successful_results = []
        failed_files = []
        
        if use_parallel and len(prepared_files) > 1:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all files for processing
                future_to_file = {
                    executor.submit(
                        self.process_single_file_batch,
                        prepared_file,
                        provider,
                        model_name,
                        temperature,
                        progress_callback
                    ): prepared_file for prepared_file in prepared_files
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_file):
                    prepared_file = future_to_file[future]
                    try:
                        result = future.result()
                        if result['status'] == 'success':
                            successful_results.append(result)
                        else:
                            failed_files.append(result)
                    except Exception as e:
                        error_result = {
                            'file_name': prepared_file['file_name'],
                            'error': str(e),
                            'status': 'failed'
                        }
                        failed_files.append(error_result)
                        logger.error(f"Parallel processing error for {prepared_file['file_name']}: {str(e)}")
        else:
            # Sequential processing
            for i, prepared_file in enumerate(prepared_files):
                if progress_callback:
                    progress_callback(f"Processing file {i+1}/{len(prepared_files)}: {prepared_file['file_name']}")
                
                result = self.process_single_file_batch(
                    prepared_file, provider, model_name, temperature, progress_callback
                )
                
                if result['status'] == 'success':
                    successful_results.append(result)
                else:
                    failed_files.append(result)
        
        end_time = datetime.now()
        processing_duration = (end_time - start_time).total_seconds()
        
        # Calculate batch statistics
        batch_stats = self._calculate_batch_stats(
            successful_results, failed_files, processing_duration
        )
        
        logger.info(f"Batch processing complete: {len(successful_results)} successful, {len(failed_files)} failed")
        return successful_results, failed_files, batch_stats
    
    def cleanup_batch_files(self, file_results: List[Dict[str, Any]]) -> None:
        """
        Clean up temporary files created during batch processing.
        
        Args:
            file_results: List of file processing results containing temp paths
        """
        temp_paths = []
        for result in file_results:
            if 'temp_path' in result and result['temp_path']:
                temp_paths.append(result['temp_path'])
        
        if temp_paths:
            self.document_processor.cleanup_temp_files(temp_paths)
            logger.info(f"Cleaned up {len(temp_paths)} temporary files")
    
    def aggregate_batch_results(
        self, 
        successful_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aggregate results from successful batch processing.
        
        Args:
            successful_results: List of successful processing results
            
        Returns:
            Aggregated results dictionary
        """
        if not successful_results:
            return {
                'total_files': 0,
                'combined_extractions': "",
                'total_chunks': 0,
                'total_characters': 0
            }
        
        combined_extractions = []
        total_chunks = 0
        total_characters = 0
        
        for result in successful_results:
            if result.get('extraction_result'):
                file_header = f"\n{'='*50}\nFILE: {result['file_name']}\n{'='*50}\n"
                combined_extractions.append(file_header + result['extraction_result'])
            
            total_chunks += result.get('chunk_count', 0)
            total_characters += result.get('character_count', 0)
        
        return {
            'total_files': len(successful_results),
            'combined_extractions': '\n\n'.join(combined_extractions),
            'total_chunks': total_chunks,
            'total_characters': total_characters,
            'file_results': successful_results
        }
    
    def _calculate_batch_stats(
        self, 
        successful_results: List[Dict[str, Any]], 
        failed_files: List[Dict[str, Any]], 
        processing_duration: float
    ) -> Dict[str, Any]:
        """
        Calculate comprehensive batch processing statistics.
        
        Args:
            successful_results: List of successful results
            failed_files: List of failed files
            processing_duration: Total processing time in seconds
            
        Returns:
            Dictionary of batch statistics
        """
        total_files = len(successful_results) + len(failed_files)
        total_chunks = sum(result.get('successful_chunks', 0) for result in successful_results)
        total_characters = sum(result.get('character_count', 0) for result in successful_results)
        
        return {
            'total_files': total_files,
            'successful_files': len(successful_results),
            'failed_files': len(failed_files),
            'success_rate': len(successful_results) / total_files if total_files > 0 else 0,
            'total_chunks_processed': total_chunks,
            'total_characters_processed': total_characters,
            'processing_duration_seconds': processing_duration,
            'average_time_per_file': processing_duration / total_files if total_files > 0 else 0,
            'chunks_per_second': total_chunks / processing_duration if processing_duration > 0 else 0
        }
    
    def get_batch_progress_info(
        self, 
        current_file: int, 
        total_files: int, 
        current_file_name: str
    ) -> Dict[str, Any]:
        """
        Get formatted batch progress information.
        
        Args:
            current_file: Current file number being processed
            total_files: Total number of files
            current_file_name: Name of current file
            
        Returns:
            Progress information dictionary
        """
        progress_percentage = (current_file / total_files) * 100
        
        return {
            'current_file': current_file,
            'total_files': total_files,
            'current_file_name': current_file_name,
            'progress_percentage': progress_percentage,
            'files_remaining': total_files - current_file,
            'status_message': f"Processing file {current_file}/{total_files}: {current_file_name}"
        }
    
    def process_batch(
        self,
        files: List[Any],
        provider: str,
        model_name: str,
        settings: Dict[str, Any],
        progress_callback: Optional[Callable] = None,
        picots_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of files with PICOTS context support (Phase 3 enhancement).
        
        Args:
            files: List of file objects to process
            provider: LLM provider name
            model_name: Model name to use
            settings: Processing settings
            progress_callback: Optional progress callback function
            picots_context: Optional PICOTS criteria for enhanced extraction
            
        Returns:
            List of processing results for each file
        """
        logger.info(f"Starting batch processing of {len(files)} files with PICOTS context: {picots_context is not None}")
        
        # Validate files
        valid_files, validation_errors = self.validate_batch_files(files)
        
        if validation_errors:
            logger.warning(f"File validation issues: {validation_errors}")
        
        if not valid_files:
            logger.error("No valid files to process")
            return []
        
        # Prepare files for processing
        prepared_files, preparation_errors = self.prepare_batch_files(valid_files)
        
        if preparation_errors:
            logger.warning(f"File preparation issues: {preparation_errors}")
        
        if not prepared_files:
            logger.error("No files could be prepared for processing")
            return []
        
        # Process files with PICOTS context
        temperature = settings.get('temperature', 0.0)
        use_parallel = settings.get('max_parallel', 1) > 1
        
        # Enhanced processing with PICOTS context
        successful_results, failed_files, batch_stats = self._execute_batch_with_picots(
            prepared_files=prepared_files,
            provider=provider,
            model_name=model_name,
            temperature=temperature,
            use_parallel=use_parallel,
            progress_callback=progress_callback,
            picots_context=picots_context
        )
        
        # Convert to standardized batch result format
        batch_results = []
        
        # Add successful results
        for result in successful_results:
            batch_results.append({
                'filename': result['file_name'],
                'status': 'success',
                'results': [{
                    'chunk_index': 0,
                    'extraction': result['extraction_result']
                }],
                'metadata': {
                    'chunk_count': result['chunk_count'],
                    'successful_chunks': result['successful_chunks'],
                    'failed_chunks': result['failed_chunks'],
                    'character_count': result['character_count'],
                    'processing_time': result['processing_time'],
                    'picots_enhanced': picots_context is not None
                }
            })
        
        # Add failed results
        for result in failed_files:
            batch_results.append({
                'filename': result['file_name'],
                'status': 'error',
                'error': result.get('error', 'Unknown error'),
                'metadata': {
                    'picots_enhanced': picots_context is not None
                }
            })
        
        # Cleanup temporary files
        all_results = successful_results + failed_files
        self.cleanup_batch_files(all_results)
        
        logger.info(f"Batch processing complete: {len(successful_results)} successful, {len(failed_files)} failed")
        return batch_results
    
    def _execute_batch_with_picots(
        self,
        prepared_files: List[Dict[str, Any]],
        provider: str,
        model_name: str,
        temperature: float,
        use_parallel: bool,
        progress_callback: Optional[Callable] = None,
        picots_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """
        Execute batch processing with PICOTS context integration.
        
        Args:
            prepared_files: List of prepared file dictionaries
            provider: LLM provider name
            model_name: Model name to use
            temperature: Temperature setting
            use_parallel: Whether to use parallel processing
            progress_callback: Optional progress callback function
            picots_context: Optional PICOTS criteria for enhanced extraction
            
        Returns:
            Tuple of (successful_results, failed_files, batch_stats)
        """
        logger.info(f"Executing batch with PICOTS context: {picots_context is not None}")
        start_time = datetime.now()
        
        successful_results = []
        failed_files = []
        
        if use_parallel and len(prepared_files) > 1:
            # Parallel processing with PICOTS
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_file = {
                    executor.submit(
                        self._process_single_file_with_picots,
                        prepared_file,
                        provider,
                        model_name,
                        temperature,
                        progress_callback,
                        picots_context
                    ): prepared_file for prepared_file in prepared_files
                }
                
                for future in as_completed(future_to_file):
                    prepared_file = future_to_file[future]
                    try:
                        result = future.result()
                        if result['status'] == 'success':
                            successful_results.append(result)
                        else:
                            failed_files.append(result)
                    except Exception as e:
                        error_result = {
                            'file_name': prepared_file['file_name'],
                            'error': str(e),
                            'status': 'failed'
                        }
                        failed_files.append(error_result)
        else:
            # Sequential processing with PICOTS
            for i, prepared_file in enumerate(prepared_files):
                if progress_callback:
                    progress_callback(f"Processing file {i+1}/{len(prepared_files)}: {prepared_file['file_name']}")
                
                result = self._process_single_file_with_picots(
                    prepared_file, provider, model_name, temperature, progress_callback, picots_context
                )
                
                if result['status'] == 'success':
                    successful_results.append(result)
                else:
                    failed_files.append(result)
        
        end_time = datetime.now()
        processing_duration = (end_time - start_time).total_seconds()
        
        batch_stats = self._calculate_batch_stats(
            successful_results, failed_files, processing_duration
        )
        
        return successful_results, failed_files, batch_stats
    
    def _process_single_file_with_picots(
        self,
        prepared_file: Dict[str, Any],
        provider: str,
        model_name: str,
        temperature: float,
        progress_callback: Optional[Callable] = None,
        picots_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a single file with PICOTS context integration.
        
        Args:
            prepared_file: Prepared file dictionary with chunks
            provider: LLM provider name
            model_name: Model name to use
            temperature: Temperature setting
            progress_callback: Optional progress callback function
            picots_context: Optional PICOTS criteria for enhanced extraction
            
        Returns:
            Processing result dictionary
        """
        file_name = prepared_file['file_name']
        chunks = prepared_file['chunks']
        
        logger.info(f"Processing {file_name} with {len(chunks)} chunks, PICOTS: {picots_context is not None}")
        
        if progress_callback:
            progress_callback(f"Processing {file_name}")
        
        try:
            # Process chunks with PICOTS context using extraction engine
            successful_results, failed_chunks = self.extraction_engine.process_chunks_batch(
                chunks=chunks,
                provider=provider,
                model_name=model_name,
                temperature=temperature,
                source_file=file_name,  # Required parameter
                picots_context=picots_context  # Phase 3: PICOTS integration
            )
            
            # Aggregate results
            all_extractions = []
            for result in successful_results:
                all_extractions.append(result['extraction'])
            
            combined_extraction = '\n\n'.join(all_extractions) if all_extractions else ""
            
            result = {
                'file_name': file_name,
                'extraction_result': combined_extraction,
                'chunk_count': len(chunks),
                'successful_chunks': len(successful_results),
                'failed_chunks': len(failed_chunks),
                'character_count': prepared_file['character_count'],
                'processing_time': datetime.now().isoformat(),
                'temp_path': prepared_file['temp_path'],
                'status': 'success',
                'picots_enhanced': picots_context is not None
            }
            
            if failed_chunks:
                result['chunk_errors'] = failed_chunks
            
            logger.info(f"Completed {file_name}: {len(successful_results)}/{len(chunks)} chunks successful")
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to process {file_name}: {error_msg}")
            
            return {
                'file_name': file_name,
                'extraction_result': "",
                'chunk_count': len(chunks),
                'successful_chunks': 0,
                'failed_chunks': len(chunks),
                'character_count': prepared_file['character_count'],
                'processing_time': datetime.now().isoformat(),
                'temp_path': prepared_file['temp_path'],
                'status': 'failed',
                'error': error_msg,
                'picots_enhanced': picots_context is not None
            }