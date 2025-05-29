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
                                   version_id=None, source_file=None, picots_context=None):
        """
        Extract patient characteristics from a text chunk

        Args:
            text_chunk (str): The text chunk to analyze
            template_id (str, optional): Template ID to use
            version_id (str, optional): Template version ID to use
            source_file (str, optional): Source file name for analytics
            picots_context (dict, optional): PICOTS data to enhance extraction
    
        Returns:
            dict: Extracted patient characteristics
        """
        # Track extraction start time
        start_time = datetime.now()
        
        # Get the appropriate prompt using template system with PICOTS context
        if template_id == "patient_characteristics":
            # Use new comprehensive template with PICOTS context
            from .prompt_templates import PromptTemplate
            prompt = PromptTemplate.get_extraction_prompt(text_chunk, picots_context)
        else:
            # Use template system for other templates
            prompt = self.template_system.get_extraction_prompt(text_chunk, template_id, version_id)
        
        logger.info(f"Sending text chunk ({len(text_chunk)} chars) to LLM for extraction using template {template_id}")
        completion = self.client.generate_completion(prompt)
        
        # Process the completion into structured data
        try:
            # Step 1: Try to find and parse JSON structure
            if "{" in completion and "}" in completion:
                json_start = completion.find("{")
                json_end = completion.rfind("}") + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = completion[json_start:json_end]
                    try:
                        data = json.loads(json_str)
                        
                        # Verify expected schema elements exist
                        expected_keys = ["demographics", "inclusion_criteria", "exclusion_criteria", 
                                        "medications", "comorbidities", "disease_specific"]
                        
                        # Add any missing expected keys with empty values
                        for key in expected_keys:
                            if key not in data:
                                if key in ["inclusion_criteria", "exclusion_criteria", "medications", "comorbidities"]:
                                    data[key] = []
                                elif key == "demographics":
                                    data[key] = {"age": "", "gender": "", "ethnicity": ""}
                                else:
                                    data[key] = {}
                        
                        logger.info(f"Successfully parsed JSON response with {len(data)} top-level elements")
                        
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
                                    "text_chunk_length": len(text_chunk),
                                    "format": "json"
                                }
                            )
                        
                        return data
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSON parsing error: {str(e)}")
                        # Continue to fallback parsing
            
            # Step 2: If JSON parsing fails, try to extract structured data using fallback mechanism
            logger.info("Falling back to categorized extraction approach")
            structured_data = {
                "demographics": {"age": "", "gender": "", "ethnicity": ""},
                "inclusion_criteria": [],
                "exclusion_criteria": [],
                "medications": [],
                "comorbidities": [],
                "disease_specific": {}
            }
            
            # Parse each section based on headers and list items
            lines = completion.strip().split('\n')
            current_section = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # Check for section headers
                lower_line = line.lower()
                if "demographics:" in lower_line:
                    current_section = "demographics"
                    continue
                elif "inclusion criteria:" in lower_line or "inclusion:" in lower_line:
                    current_section = "inclusion_criteria"
                    continue
                elif "exclusion criteria:" in lower_line or "exclusion:" in lower_line:
                    current_section = "exclusion_criteria"
                    continue
                elif "medications:" in lower_line or "medication:" in lower_line:
                    current_section = "medications"
                    continue
                elif "comorbidities:" in lower_line or "comorbidity:" in lower_line:
                    current_section = "comorbidities"
                    continue
                elif "disease" in lower_line and ("specific" in lower_line or "characteristics" in lower_line):
                    current_section = "disease_specific"
                    continue
                
                # Process content based on current section
                if current_section:
                    if current_section == "demographics":
                        # Check for demographic details like age, gender, ethnicity
                        if line.startswith("-") or line.startswith("*"):
                            line = line[1:].strip()
                        
                        if ":" in line:
                            key, value = line.split(":", 1)
                            key = key.strip().lower()
                            value = value.strip()
                            
                            if "age" in key:
                                structured_data["demographics"]["age"] = value
                            elif "gender" in key or "sex" in key or "male" in key or "female" in key:
                                structured_data["demographics"]["gender"] = value
                            elif "ethnic" in key or "race" in key:
                                structured_data["demographics"]["ethnicity"] = value
                    elif current_section in ["inclusion_criteria", "exclusion_criteria", "medications", "comorbidities"]:
                        if line.startswith("-") or line.startswith("*"):
                            item = line[1:].strip()
                            structured_data[current_section].append(item)
                        # Handle non-bulleted items too
                        elif len(line) > 3 and not line.endswith(':'):
                            structured_data[current_section].append(line)
                    elif current_section == "disease_specific":
                        if ":" in line:
                            key, value = line.split(":", 1)
                            structured_data["disease_specific"][key.strip()] = value.strip()
                        elif line.startswith("-") or line.startswith("*"):
                            item = line[1:].strip()
                            # Use the item as a key with empty value if it doesn't contain a value
                            if ":" in item:
                                sub_key, sub_value = item.split(":", 1)
                                structured_data["disease_specific"][sub_key.strip()] = sub_value.strip()
                            else:
                                # Use a numbered key if we can't determine a better key
                                key = f"characteristic_{len(structured_data['disease_specific']) + 1}"
                                structured_data["disease_specific"][key] = item
            
            # Track extraction and return structured data
            end_time = datetime.now()
            if source_file:
                self.template_system.track_template_usage(
                    template_id,
                    version_id or "latest",
                    source_file,
                    sum(len(val) if isinstance(val, list) else 1 for val in structured_data.values()),
                    start_time,
                    end_time,
                    True,
                    None,
                    {
                        "provider": self.provider,
                        "model": self.model_name,
                        "text_chunk_length": len(text_chunk),
                        "format": "fallback_structured"
                    }
                )
            
            return structured_data
                
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
                        "text_chunk_length": len(text_chunk),
                        "format": "error"
                    }
                )
            
            # Return the raw completion if parsing fails
            return {
                "raw_extraction": completion,
                "error": error_msg
            }
    
    def extract_from_chunks(self, chunks, template_id="patient_characteristics", 
                        version_id=None, merge=True, source_file=None, 
                        picots_context=None):
        """
        Extract patient characteristics from multiple text chunks
    
        Args:
            chunks (list): List of text chunks to analyze
            template_id (str, optional): Template ID to use
            version_id (str, optional): Template version ID to use
            merge (bool): Whether to merge results into a single dictionary
            source_file (str, optional): Source file name for analytics
            picots_context (dict, optional): PICOTS data to enhance extraction
        
        Returns:
            dict or list: Extracted patient characteristics (merged dict or list of dicts)
        """
        results = []
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            extraction = self.extract_patient_characteristics(
                chunk, template_id, version_id, source_file, picots_context
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