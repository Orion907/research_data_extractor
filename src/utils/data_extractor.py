# src/utils/data_extractor.py
"""
Module for extracting structured data from text using LLMs
"""
import json
import logging
from datetime import datetime
from ..llm.client_factory import ClientFactory
from .prompt_templates import PromptTemplate
from .results_manager import ResultsManager  # Import the ResultsManager

# Configure logging
logger = logging.getLogger(__name__)

class DataExtractor:
    """
    Extracts structured data from text using LLM APIs
    """
    
    def __init__(self, provider="anthropic", api_key=None, model_name=None, results_dir=None, validator=None):
        """
        Initialize the extractor
        
        Args:
            provider (str): LLM provider to use ('openai', 'anthropic', or 'mock')
            api_key (str, optional): API key for the service
            model_name (str, optional): Model name to use
            results_dir (str, optional): Directory to store results
            validator (DataValidator, optional): Validator for extracted data
        """
        self.client = ClientFactory.create_client(provider, api_key, model_name)
        self.provider = provider
        self.model_name = model_name or self.client.model_name
        # Add a results manager
        self.results_manager = ResultsManager(results_dir)
        # Store the validator if provided
        self.validator = validator
        logger.info(f"Initialized DataExtractor with {provider} provider")
    
    def extract_patient_characteristics(self, text_chunk, template_id=None, source_file=None):
        """
        Extract patient characteristics from a text chunk
        
        Args:
            text_chunk (str): The text chunk to analyze
            template_id (str, optional): ID of the prompt template to use
            source_file (str, optional): Path to the source PDF file
            
        Returns:
            dict: Extracted patient characteristics
        """
        # Record start time for analytics
        start_time = datetime.now()
        
        # Use the static method directly
        prompt = PromptTemplate.get_extraction_prompt(text_chunk)
        if template_id:
            # Here we'd use a specific template if provided
            # For now, just use the default
            pass
        
        logger.info("Sending text chunk to LLM for extraction")
        completion = self.client.generate_completion(prompt)
        
        # Process the completion into structured data (best effort)
        try:
            # Try to parse as JSON if response looks like JSON
            if "{" in completion and "}" in completion:
                # Extract JSON-like content if embedded in other text
                json_start = completion.find("{")
                json_end = completion.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = completion[json_start:json_end]
                    data = json.loads(json_str)
                    result_data = data
                    success = True
                else:
                    result_data = {"raw_extraction": completion}
                    success = False
            else:
                # Parse as key-value pairs if not JSON
                result_data = {}
                lines = completion.strip().split('\n')
                
                for line in lines:
                    line = line.strip()
                    if ':' in line:
                        key, value = line.split(':', 1)
                        result_data[key.strip()] = value.strip()
                success = len(result_data) > 0
            
            # Validate data if validator is provided
            if self.validator and success:
                result_data = self.validator.validate_and_clean(result_data)
            
            # Calculate end time for analytics
            end_time = datetime.now()
            
            # Save the result if source_file is provided
            if source_file and self.results_manager:
                # Create model info
                model_info = {
                    "provider": self.provider,
                    "model_name": self.model_name
                }
                
                # Save the result
                result_id = self.results_manager.save_extraction_result(
                    result=result_data,
                    source_file=source_file,
                    model_info=model_info,
                    prompt_id=template_id,
                    metadata={
                        "text_chunk_length": len(text_chunk),
                        "extraction_time_ms": (end_time - start_time).total_seconds() * 1000,
                        "success": success
                    }
                )
                logger.info(f"Saved extraction result with ID: {result_id}")
            
            return result_data
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM response into structured data: {str(e)}")
            # Return the raw completion if parsing fails
            return {"raw_extraction": completion}
    
    def extract_from_chunks(self, chunks, merge=True, source_file=None):
        """
        Extract patient characteristics from multiple text chunks
        
        Args:
            chunks (list): List of text chunks to analyze
            merge (bool): Whether to merge results into a single dictionary
            source_file (str, optional): Path to the source file for results management
            
        Returns:
            dict or list: Extracted patient characteristics (merged dict or list of dicts)
        """
        results = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            extraction = self.extract_patient_characteristics(chunk, source_file=source_file)
            results.append(extraction)
        
        if merge:
            # Merge all results into a single dictionary
            merged = {}
            for result in results:
                for key, value in result.items():
                    # If the key already exists, prefer non-empty and longer values
                    if key in merged:
                        if not merged[key] or (value and len(str(value)) > len(str(merged[key]))):
                            merged[key] = value
                    else:
                        merged[key] = value
            
            return merged
        else:
            return results