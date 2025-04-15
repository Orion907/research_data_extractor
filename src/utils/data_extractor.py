"""
Module for extracting structured data from text using LLMs
"""
import json
import logging
from ..llm.client_factory import ClientFactory
from .prompt_templates import PromptTemplate

# Configure logging
logger = logging.getLogger(__name__)

class DataExtractor:
    """
    Extracts structured data from text using LLM APIs
    """
    
    def __init__(self, provider="anthropic", api_key=None, model_name=None):
        """
        Initialize the extractor
        
        Args:
            provider (str): LLM provider to use ('openai' or 'anthropic')
            api_key (str, optional): API key for the service
            model_name (str, optional): Model name to use
        """
        self.client = ClientFactory.create_client(provider, api_key, model_name)
        logger.info(f"Initialized DataExtractor with {provider} provider")
    
    def extract_patient_characteristics(self, text_chunk):
        """
        Extract patient characteristics from a text chunk
        
        Args:
            text_chunk (str): The text chunk to analyze
            
        Returns:
            dict: Extracted patient characteristics
        """
        prompt = PromptTemplate.get_extraction_prompt(text_chunk)
        
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
                    return data
            
            # If not JSON, parse as key-value pairs
            result = {}
            lines = completion.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    result[key.strip()] = value.strip()
            
            return result
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM response into structured data: {str(e)}")
            # Return the raw completion if parsing fails
            return {"raw_extraction": completion}
    
    def extract_from_chunks(self, chunks, merge=True):
        """
        Extract patient characteristics from multiple text chunks
        
        Args:
            chunks (list): List of text chunks to analyze
            merge (bool): Whether to merge results into a single dictionary
            
        Returns:
            dict or list: Extracted patient characteristics (merged dict or list of dicts)
        """
        results = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            extraction = self.extract_patient_characteristics(chunk)
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