# src/utils/data_extractor.py
"""
Module for extracting structured data from text using LLMs
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from ..llm.client_factory import ClientFactory
from .prompt_templates import PromptTemplate
from .template_system import TemplateSystem

# Configure logging
logger = logging.getLogger(__name__)

class DataExtractor:
    """
    Extracts structured data from text using LLM APIs
    """
    
    def __init__(self, provider="anthropic", api_key=None, model_name=None, 
                 template_system=None):
        """
        Initialize the extractor
        
        Args:
            provider (str): LLM provider to use ('openai', 'anthropic', or 'mock')
            api_key (str, optional): API key for the service
            model_name (str, optional): Model name to use
            template_system (TemplateSystem, optional): Template system instance to use
        """
        self.client = ClientFactory.create_client(provider, api_key, model_name)
        self.provider = provider
        self.model_name = model_name or self.client.model_name
        
        # Initialize template system if not provided
        self.template_system = template_system or TemplateSystem()
        
        logger.info(f"Initialized DataExtractor with {provider} provider, model {self.model_name}")
    
    def extract_patient_characteristics(self, text_chunk, template_id="patient_characteristics", 
                                       version_id=None, source_file=None):
        """
        Extract patient characteristics from a text chunk
        
        Args:
            text_chunk (str): The text chunk to analyze
            template_id (str, optional): Template ID to use
            version_id (str, optional): Template version ID to use
            source_file (str, optional): Source file name for analytics
            
        Returns:
            dict: Extracted patient characteristics
        """
        # Track extraction start time
        start_time = datetime.now()
        
        # Get the appropriate prompt using template system
        prompt = self.template_system.get_extraction_prompt(text_chunk, template_id, version_id)
        
        logger.info(f"Sending text chunk ({len(text_chunk)} chars) to LLM for extraction using template {template_id}")
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
                    
                    # Track successful extraction
                    end_time = datetime.now()
                    if source_file:
                        self.template_system.track_template_usage(
                            template_id,
                            version_id or "latest",
                            source_file,
                            len(data),
                            start_time,
                            end_time,
                            True,
                            None,
                            {
                                "provider": self.provider,
                                "model": self.model_name,
                                "text_chunk_length": len(text_chunk)
                            }
                        )
                    
                    return data
            
            # If not JSON, parse as key-value pairs
            result = {}
            lines = completion.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    result[key.strip()] = value.strip()
            
            # Track successful extraction
            end_time = datetime.now()
            if source_file:
                self.template_system.track_template_usage(
                    template_id,
                    version_id or "latest",
                    source_file,
                    len(result),
                    start_time,
                    end_time,
                    True,
                    None,
                    {
                        "provider": self.provider,
                        "model": self.model_name,
                        "text_chunk_length": len(text_chunk)
                    }
                )
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            logger.warning(f"Failed to parse LLM response into structured data: {error_msg}")
            
            # Track failed extraction
            end_time = datetime.now()
            if source_file:
                self.template_system.track_template_usage(
                    template_id,
                    version_id or "latest",
                    source_file,
                    0,
                    start_time,
                    end_time,
                    False,
                    error_msg,
                    {
                        "provider": self.provider,
                        "model": self.model_name,
                        "text_chunk_length": len(text_chunk)
                    }
                )
            
            # Return the raw completion if parsing fails
            return {"raw_extraction": completion}
    
    def extract_from_chunks(self, chunks, template_id="patient_characteristics", 
                            version_id=None, merge=True, source_file=None):
        """
        Extract patient characteristics from multiple text chunks
        
        Args:
            chunks (list): List of text chunks to analyze
            template_id (str, optional): Template ID to use
            version_id (str, optional): Template version ID to use
            merge (bool): Whether to merge results into a single dictionary
            source_file (str, optional): Source file name for analytics
            
        Returns:
            dict or list: Extracted patient characteristics (merged dict or list of dicts)
        """
        results = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            extraction = self.extract_patient_characteristics(
                chunk, template_id, version_id, source_file
            )
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
    
    def get_best_template_for_extraction(self, disease_type=None):
        """
        Get the best performing template for extraction
        
        Args:
            disease_type (str, optional): Disease type to filter templates by
            
        Returns:
            str: Template ID of the best performing template
        """
        return self.template_system.get_best_performing_template(disease_type)
    
    def get_analytics_summary(self, days=30):
        """
        Get summary of extraction analytics
        
        Args:
            days (int): Number of days to include
            
        Returns:
            dict: Analytics summary
        """
        return self.template_system.get_analytics_summary(days)