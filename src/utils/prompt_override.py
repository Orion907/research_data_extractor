"""
Module for prompt template overrides and version-specific functionality
"""
import os
import json
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Default template for patient characteristics extraction
PATIENT_CHARACTERISTICS_TEMPLATE = """
You are an AI assistant specialized in extracting patient characteristic data from medical research articles.

Below is a section of a research article. Please extract all patient characteristics mentioned, including:
- Demographics (age, gender, ethnicity)
- Inclusion/exclusion criteria
- Comorbidities
- Medications
- Disease-specific characteristics

Format your response as a structured list of key-value pairs.

ARTICLE SECTION:
{text}

EXTRACTED PATIENT CHARACTERISTICS:
"""

def get_extraction_prompt_with_version(text, version=None, custom_characteristics=None):
    """
    Generate a prompt for extracting patient characteristics with version control
    
    Args:
        text (str): The text chunk to analyze
        version (str, optional): Specific template version to use
        custom_characteristics (list, optional): List of specific characteristics to extract
        
    Returns:
        str: Formatted prompt for the LLM
    """
    # Check if using custom characteristics
    if custom_characteristics:
        characteristics_str = "\n".join([f"- {item}" for item in custom_characteristics])
        
        custom_template = f"""
        You are an AI assistant specialized in extracting patient characteristic data from medical research articles.
        
        Below is a section of a research article. Please extract the following patient characteristics:
        {characteristics_str}
        
        Format your response as a structured list of key-value pairs.
        
        ARTICLE SECTION:
        {{text}}
        
        EXTRACTED PATIENT CHARACTERISTICS:
        """
        
        return custom_template.format(text=text)
    
    # If a specific version is requested, try to load it
    if version:
        version_path = os.path.join("prompts", f"{version}.json")
        if os.path.exists(version_path):
            try:
                with open(version_path, 'r') as f:
                    template_data = json.load(f)
                    # Extract the template text from the loaded file
                    template_text = template_data.get("template_text")
                    if template_text:
                        logger.info(f"Using prompt template version: {version}")
                        return template_text.format(text=text)
            except Exception as e:
                logger.error(f"Error loading template version {version}: {str(e)}")
                # Fall back to default template if there's an error
    
    # Otherwise use the default template
    logger.info("Using default patient characteristics template")
    return PATIENT_CHARACTERISTICS_TEMPLATE.format(text=text)

def list_available_versions():
    """
    List all available template versions
    
    Returns:
        list: List of available version IDs
    """
    prompts_dir = "prompts"
    if not os.path.exists(prompts_dir):
        return []
        
    versions = []
    for filename in os.listdir(prompts_dir):
        if filename.endswith('.json'):
            versions.append(filename.replace('.json', ''))
    
    return sorted(versions)