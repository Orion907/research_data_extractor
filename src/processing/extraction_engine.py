"""
Extraction engine module for LLM-based data extraction and processing.

This module provides a centralized interface for LLM interactions, prompt handling,
data extraction processing, and result validation with analytics integration.
"""

import os
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

from src.utils.data_extractor import DataExtractor
from src.utils.prompt_templates import PromptTemplate
from src.utils.template_system import TemplateSystem
from src.utils.unified_analytics import Analytics
from src.utils.picots_parser import PicotsParser

logger = logging.getLogger(__name__)


class ExtractionEngine:
    """
    Handles LLM-based data extraction operations including prompt construction,
    completion processing, error handling, and analytics integration.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, analytics: Optional[Analytics] = None):
        """
        Initialize the ExtractionEngine.
        
        Args:
            config: Configuration dictionary for extraction parameters
            analytics: Analytics instance for tracking extractions
        """
        self.config = config or {}
        self.analytics = analytics or Analytics()
        self.template_system = TemplateSystem()
        self.current_extractor = None
        
    def validate_api_key(self, provider: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that the required API key is available for the provider.
        
        Args:
            provider: LLM provider name ('anthropic', 'openai', 'mock')
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if provider == "mock":
            return True, None
        
        api_key_env_var = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
        
        if not os.environ.get(api_key_env_var):
            return False, f"Please set the {api_key_env_var} environment variable before processing."
        
        return True, None
    
    def initialize_extractor(self, provider: str, model_name: str) -> DataExtractor:
        """
        Initialize the LLM extractor with the specified provider and model.
        
        Args:
            provider: LLM provider name
            model_name: Model name to use
            
        Returns:
            Initialized DataExtractor instance
            
        Raises:
            Exception: If API key validation fails or initialization fails
        """
        # Validate API key
        is_valid, error_msg = self.validate_api_key(provider)
        if not is_valid:
            raise Exception(error_msg)
        
        # Initialize extractor
        logger.info(f"Initializing extractor with provider={provider}, model={model_name}")
        self.current_extractor = DataExtractor(
            provider=provider, 
            model_name=model_name,
            template_system=self.template_system
        )
        
        return self.current_extractor
    
    def construct_extraction_prompt(
        self,
        text: str,
        custom_characteristics: Optional[List[str]] = None,
        picots_context: Optional[Dict[str, Any]] = None,
        version: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Construct the appropriate extraction prompt based on parameters.
        
        Args:
            text: Text content to extract from
            custom_characteristics: List of custom characteristics to extract
            picots_context: PICOTS context data for enhanced prompts
            version: Prompt version to use
            
        Returns:
            Tuple of (prompt, prompt_id)
        """
        if custom_characteristics:
            prompt_id = 'custom_patient_characteristics'
            prompt = PromptTemplate.custom_extraction_prompt(text, custom_characteristics)
        else:
            prompt_id = 'comprehensive_research'
            # Convert PicotsData object to dictionary format if needed
            if picots_context and hasattr(picots_context, 'population'):
                picots_dict = {
                    'picots_sections': {
                        'population': picots_context.population,
                        'interventions': picots_context.interventions,
                        'comparators': picots_context.comparators,
                        'outcomes': picots_context.outcomes,
                        'timing': picots_context.timing,
                        'setting': picots_context.setting
                    },
                    'key_questions': getattr(picots_context, 'detected_kqs', []),
                    'abbreviations': getattr(picots_context, 'abbreviations', {})
                }
            else:
                picots_dict = picots_context
            
            prompt = PromptTemplate.get_extraction_prompt(
                text, 
                picots_context=picots_dict,
                version=version
            )
        
        return prompt, prompt_id
    
    def process_single_chunk(
        self,
        chunk: Dict[str, Any],
        provider: str,
        model_name: str,
        temperature: float,
        source_file: str,
        custom_characteristics: Optional[List[str]] = None,
        picots_context: Optional[Dict[str, Any]] = None,
        prompt_version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single text chunk for data extraction.
        
        Args:
            chunk: Text chunk dictionary with 'content' and 'index'
            provider: LLM provider name
            model_name: Model name to use
            temperature: Temperature setting for LLM
            source_file: Source filename for analytics
            custom_characteristics: Custom characteristics to extract
            picots_context: PICOTS context data
            prompt_version: Prompt version to use
            
        Returns:
            Extraction result dictionary or None if failed
        """
        start_time = datetime.now()
        
        try:
            # Initialize extractor if needed
            if not self.current_extractor:
                self.initialize_extractor(provider, model_name)
            
            # Construct prompt
            prompt, prompt_id = self.construct_extraction_prompt(
                chunk['content'],
                custom_characteristics,
                picots_context,
                prompt_version
            )
            
            # Generate completion
            logger.info(f"Processing chunk {chunk['index']} with {provider}/{model_name}")
            completion = self.current_extractor.client.generate_completion(
                prompt, 
                temperature=temperature
            )
            
            # Basic completion validation
            if not completion or not isinstance(completion, str):
                logger.warning(f"Chunk {chunk['index']} returned invalid response format")
                return None
            
            end_time = datetime.now()
            
            # Track successful extraction in analytics
            self.analytics.log_extraction(
                template_id=prompt_id,
                version_id=prompt_version if prompt_version != "default" else "latest",
                source_file=source_file,
                characteristics_found=len(completion.split('\n')),
                start_time=start_time,
                end_time=end_time,
                success=True,
                metadata={
                    'provider': provider,
                    'model': model_name,
                    'chunk_index': chunk['index'],
                    'temperature': temperature,
                    'text_chunk_length': len(chunk['content'])
                }
            )
            
            return {
                'chunk_index': chunk['index'],
                'extraction': completion
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing chunk {chunk['index']}: {error_msg}")
            
            # Track failed extraction in analytics
            self.analytics.log_extraction(
                template_id=prompt_id if 'prompt_id' in locals() else 'unknown',
                version_id=prompt_version if prompt_version != "default" else "latest",
                source_file=source_file,
                characteristics_found=0,
                start_time=start_time,
                end_time=datetime.now(),
                success=False,
                error=error_msg,
                metadata={
                    'provider': provider,
                    'model': model_name,
                    'chunk_index': chunk['index'],
                    'temperature': temperature,
                    'text_chunk_length': len(chunk['content']) if chunk else 0
                }
            )
            
            return None
    
    def process_chunks_batch(
        self,
        chunks: List[Dict[str, Any]],
        provider: str,
        model_name: str,
        temperature: float,
        source_file: str,
        custom_characteristics: Optional[List[str]] = None,
        picots_context: Optional[Dict[str, Any]] = None,
        prompt_version: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple text chunks for data extraction.
        
        Args:
            chunks: List of text chunk dictionaries
            provider: LLM provider name
            model_name: Model name to use
            temperature: Temperature setting for LLM
            source_file: Source filename for analytics
            custom_characteristics: Custom characteristics to extract
            picots_context: PICOTS context data
            prompt_version: Prompt version to use
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of successful extraction results
        """
        logger.info(f"Processing {len(chunks)} chunks for {source_file}")
        results = []
        
        for i, chunk in enumerate(chunks):
            if progress_callback:
                progress_callback(i + 1, len(chunks), f"Processing chunk {i + 1}")
            
            result = self.process_single_chunk(
                chunk=chunk,
                provider=provider,
                model_name=model_name,
                temperature=temperature,
                source_file=source_file,
                custom_characteristics=custom_characteristics,
                picots_context=picots_context,
                prompt_version=prompt_version
            )
            
            if result:
                results.append(result)
        
        logger.info(f"Successfully processed {len(results)}/{len(chunks)} chunks")
        return results
    
    def process_batch_file(
        self,
        file_chunks: List[Dict[str, Any]],
        file_name: str,
        provider: str,
        model_name: str,
        temperature: float,
        processing_type: str = "batch"
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process all chunks from a single file in batch processing.
        
        Args:
            file_chunks: List of text chunks from the file
            file_name: Name of the file being processed
            provider: LLM provider name
            model_name: Model name to use
            temperature: Temperature setting for LLM
            processing_type: Type of processing (for analytics)
            
        Returns:
            Tuple of (successful_results, failed_chunks)
        """
        logger.info(f"Processing {len(file_chunks)} chunks from {file_name}")
        
        # Initialize extractor if needed
        if not self.current_extractor:
            self.initialize_extractor(provider, model_name)
        
        successful_results = []
        failed_chunks = []
        
        for chunk in file_chunks:
            chunk_start_time = datetime.now()
            
            try:
                # Use simplified prompt for batch processing
                prompt = PromptTemplate.get_extraction_prompt(chunk['content'])
                
                completion = self.current_extractor.client.generate_completion(
                    prompt, 
                    temperature=temperature
                )
                
                chunk_end_time = datetime.now()
                
                # Log analytics for this chunk
                self.analytics.log_extraction(
                    template_id='comprehensive_research',
                    version_id='batch_processing',
                    source_file=file_name,
                    characteristics_found=len(completion.split('\n')),
                    start_time=chunk_start_time,
                    end_time=chunk_end_time,
                    success=True,
                    metadata={
                        'provider': provider,
                        'model': model_name,
                        'chunk_index': chunk['index'],
                        'temperature': temperature,
                        'text_chunk_length': len(chunk['content']),
                        'processing_type': processing_type
                    }
                )
                
                successful_results.append({
                    'chunk_index': chunk['index'],
                    'extraction': completion
                })
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to process chunk {chunk['index']} from {file_name}: {error_msg}")
                
                # Log failed extraction
                self.analytics.log_extraction(
                    template_id='comprehensive_research',
                    version_id='batch_processing',
                    source_file=file_name,
                    characteristics_found=0,
                    start_time=chunk_start_time,
                    end_time=datetime.now(),
                    success=False,
                    error=error_msg,
                    metadata={
                        'provider': provider,
                        'model': model_name,
                        'processing_type': processing_type
                    }
                )
                
                failed_chunks.append({
                    'chunk_index': chunk['index'],
                    'error': error_msg
                })
        
        logger.info(f"File {file_name}: {len(successful_results)} successful, {len(failed_chunks)} failed")
        return successful_results, failed_chunks
    
    def parse_picots_data(self, picots_text: str) -> Optional[Any]:
        """
        Parse PICOTS criteria text into structured data.
        
        Args:
            picots_text: Raw PICOTS text input
            
        Returns:
            Parsed PICOTS data object or None if parsing fails
        """
        if not picots_text.strip():
            return None
        
        try:
            parser = PicotsParser()
            picots_data = parser.parse_picots_table(picots_text.strip())
            logger.info("Successfully parsed PICOTS criteria")
            return picots_data
        except Exception as e:
            logger.error(f"Error parsing PICOTS data: {str(e)}")
            return {"raw_text": picots_text.strip()}
    
    def get_available_models(self, provider: str) -> List[str]:
        """
        Get list of available models for a provider.
        
        Args:
            provider: LLM provider name
            
        Returns:
            List of available model names
        """
        if provider == "anthropic":
            return [
                "claude-3-5-sonnet-20241022", 
                "claude-3-5-sonnet-20240620", 
                "claude-3-opus-20240229", 
                "claude-3-haiku-20240307"
            ]
        elif provider == "openai":
            return ["gpt-3.5-turbo", "gpt-4o", "gpt-4-1106-preview"]
        else:  # mock
            return ["mock-model"]
    
    def get_template_versions(self, template_id: str = 'patient_characteristics') -> List[str]:
        """
        Get available template versions.
        
        Args:
            template_id: Template identifier
            
        Returns:
            List of available version names
        """
        versions = self.template_system.list_versions(template_id)
        return versions if versions else ["default"]
    
    def get_extraction_stats(self) -> Dict[str, Any]:
        """
        Get extraction statistics from analytics.
        
        Returns:
            Dictionary of extraction statistics
        """
        try:
            return self.analytics.get_extraction_stats()
        except Exception as e:
            logger.warning(f"Failed to get extraction stats: {str(e)}")
            return {
                'total_extractions': 0,
                'successful_extractions': 0,
                'failed_extractions': 0,
                'success_rate': 0.0
            }
    
    def cleanup(self):
        """Clean up resources and reset state."""
        self.current_extractor = None
        logger.debug("ExtractionEngine cleaned up")