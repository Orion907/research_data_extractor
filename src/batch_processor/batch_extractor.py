"""
Batch processing module for handling multiple PDF extractions
"""
import os
import logging
import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any
from ..pdf_processor import extract_text_from_pdf, chunk_text
from ..utils import DataExtractor, Analytics

# Configure logging
logger = logging.getLogger(__name__)

class BatchExtractor:
    """
    Handles batch processing of multiple PDF files for patient characteristic extraction
    """
    
    def __init__(self, provider="anthropic", model_name=None, api_key=None):
        """
        Initialize the batch extractor
        
        Args:
            provider (str): LLM provider ('anthropic', 'openai', 'mock')
            model_name (str, optional): Specific model to use
            api_key (str, optional): API key for the service
        """
        self.provider = provider
        self.model_name = model_name
        self.api_key = api_key
        
        # Initialize data extractor
        self.extractor = DataExtractor(provider=provider, api_key=api_key, model_name=model_name)
        
        # Initialize analytics
        self.analytics = Analytics()
        
        # Track batch processing results
        self.batch_results = []
        self.failed_files = []
        
        logger.info(f"Initialized BatchExtractor with {provider} provider")
    
    def process_directory(self, input_dir: str, output_dir: str, 
                     template_id: str = "patient_characteristics",
                     chunk_size: int = 1000, overlap: int = 100,
                     max_files: int = None) -> Dict[str, Any]:
        """
        Process all PDF files in a directory
        
        Args:
            input_dir (str): Directory containing PDF files
            output_dir (str): Directory to save extraction results
            template_id (str): Template ID to use for extraction
            chunk_size (int): Size of text chunks
            overlap (int): Overlap between chunks
            
        Returns:
            dict: Summary of batch processing results
        """
        # Validate input directory
        if not os.path.exists(input_dir):
            raise ValueError(f"Input directory does not exist: {input_dir}")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Find all PDF files
        pdf_files = []
        for file in os.listdir(input_dir):
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(input_dir, file))

        # Limit files if max_files specified
        if max_files and len(pdf_files) > max_files:
            original_count = len(pdf_files)
            pdf_files = pdf_files[:max_files]
            logger.info(f"Limited to {max_files} files (found {original_count} total)")

        if not pdf_files:
            logger.warning(f"No PDF files found in {input_dir}")
            return {"total_files": 0, "processed": 0, "failed": 0, "results": []}

        logger.info(f"Found {len(pdf_files)} PDF files to process")
        
        # Process each PDF file
        for i, pdf_path in enumerate(pdf_files):
            logger.info(f"Processing file {i+1}/{len(pdf_files)}: {os.path.basename(pdf_path)}")
            
            try:
                result = self._process_single_pdf(pdf_path, output_dir, template_id, chunk_size, overlap)
                self.batch_results.append(result)
                logger.info(f"Successfully processed: {os.path.basename(pdf_path)}")
                
            except Exception as e:
                error_info = {
                    "file_path": pdf_path,
                    "file_name": os.path.basename(pdf_path),
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                self.failed_files.append(error_info)
                logger.error(f"Failed to process {os.path.basename(pdf_path)}: {str(e)}")
        
        # Generate summary
        summary = {
            "total_files": len(pdf_files),
            "processed": len(self.batch_results),
            "failed": len(self.failed_files),
            "results": self.batch_results,
            "failed_files": self.failed_files,
            "output_directory": output_dir,
            "processing_timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Batch processing complete: {summary['processed']}/{summary['total_files']} files processed successfully")
        
        return summary
    
    def _process_single_pdf(self, pdf_path: str, output_dir: str, 
                           template_id: str, chunk_size: int, overlap: int) -> Dict[str, Any]:
        """
        Process a single PDF file
        
        Args:
            pdf_path (str): Path to the PDF file
            output_dir (str): Output directory
            template_id (str): Template ID for extraction
            chunk_size (int): Chunk size for text processing
            overlap (int): Overlap between chunks
            
        Returns:
            dict: Processing result for this file
        """
        start_time = datetime.now()
        file_name = os.path.basename(pdf_path)
        base_name = os.path.splitext(file_name)[0]
        
        try:
            # Step 1: Extract text from PDF
            logger.debug(f"Extracting text from {file_name}")
            text = extract_text_from_pdf(pdf_path)
            
            if not text.strip():
                raise ValueError("No text could be extracted from PDF")
            
            # Step 2: Chunk the text
            logger.debug(f"Chunking text for {file_name}")
            chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
            
            if not chunks:
                raise ValueError("No text chunks created")
            
            # Step 3: Extract patient characteristics
            logger.debug(f"Extracting patient characteristics from {file_name}")
            chunk_contents = [chunk['content'] for chunk in chunks]
            extraction_result = self.extractor.extract_from_chunks(
                chunk_contents, 
                template_id=template_id,
                source_file=file_name
            )
            
            # Step 4: Save results
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            # Save individual result file
            result_file_path = os.path.join(output_dir, f"{base_name}_extraction.json")
            result_data = {
                "metadata": {
                    "source_file": file_name,
                    "source_path": pdf_path,
                    "processing_time_seconds": processing_time,
                    "template_id": template_id,
                    "provider": self.provider,
                    "model": self.model_name,
                    "chunk_count": len(chunks),
                    "text_length": len(text),
                    "processed_at": end_time.isoformat()
                },
                "extraction": extraction_result
            }
            
            with open(result_file_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, indent=2)
            
            # Return processing summary
            return {
                "file_name": file_name,
                "file_path": pdf_path,
                "result_file": result_file_path,
                "processing_time_seconds": processing_time,
                "chunk_count": len(chunks),
                "text_length": len(text),
                "extraction_fields": len(extraction_result) if isinstance(extraction_result, dict) else 0,
                "status": "success",
                "processed_at": end_time.isoformat()
            }
            
        except Exception as e:
            # Log the error and re-raise
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            logger.error(f"Error processing {file_name}: {str(e)}")
            
            # Save error information
            error_file_path = os.path.join(output_dir, f"{base_name}_error.json")
            error_data = {
                "file_name": file_name,
                "file_path": pdf_path,
                "error": str(e),
                "processing_time_seconds": processing_time,
                "failed_at": end_time.isoformat()
            }
            
            try:
                with open(error_file_path, 'w', encoding='utf-8') as f:
                    json.dump(error_data, f, indent=2)
            except:
                pass  # Don't fail on error file creation
            
            raise

    def generate_batch_report(self, output_dir: str, report_name: str = "batch_processing_report.csv") -> str:
        """
        Generate a CSV report summarizing the batch processing results
        
        Args:
            output_dir (str): Directory to save the report
            report_name (str): Name of the report file
            
        Returns:
            str: Path to the generated report file
        """
        if not self.batch_results and not self.failed_files:
            logger.warning("No batch processing results to report")
            return None
        
        # Prepare data for the report
        report_data = []
        
        # Add successful processing results
        for result in self.batch_results:
            report_data.append({
                'file_name': result['file_name'],
                'status': 'success',
                'processing_time_seconds': result['processing_time_seconds'],
                'chunk_count': result['chunk_count'],
                'text_length': result['text_length'],
                'extraction_fields': result['extraction_fields'],
                'result_file': result['result_file'],
                'processed_at': result['processed_at'],
                'error': ''
            })
        
        # Add failed processing results
        for failed in self.failed_files:
            report_data.append({
                'file_name': failed['file_name'],
                'status': 'failed',
                'processing_time_seconds': 0,
                'chunk_count': 0,
                'text_length': 0,
                'extraction_fields': 0,
                'result_file': '',
                'processed_at': failed['timestamp'],
                'error': failed['error']
            })
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(report_data)
        report_path = os.path.join(output_dir, report_name)
        df.to_csv(report_path, index=False)
        
        logger.info(f"Generated batch processing report: {report_path}")
        return report_path