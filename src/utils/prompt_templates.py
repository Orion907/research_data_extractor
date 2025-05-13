# src/utils/prompt_templates.py
"""
Module for LLM prompt templates
"""
import logging
import os
from collections import defaultdict
import json

# Configure logging
logger = logging.getLogger(__name__)

class PromptTemplate:
    """Class for managing prompt templates"""
    
    # Base prompt for extracting patient characteristics
    PATIENT_CHARACTERISTICS_TEMPLATE = """
You are an AI assistant specialized in extracting patient characteristic data from medical research articles.

Below is a section of a research article. Please extract all patient characteristics mentioned, including:
- Demographics (age, gender, ethnicity)
- Inclusion/exclusion criteria
- Comorbidities
- Medications
- Disease-specific characteristics

Format your response as a JSON object with the following structure:
{{
  "demographics": {{
    "age": "",
    "gender": "",
    "ethnicity": ""
  }},
  "inclusion_criteria": [],
  "exclusion_criteria": [],
  "comorbidities": [],
  "medications": [],
  "disease_specific": {{}}
}}

ARTICLE SECTION:
{text}

EXTRACTED PATIENT CHARACTERISTICS:
"""    
    
    @classmethod
    def initialize(cls):
        """
        Initialize prompt templates and save initial versions
        """
        # Create prompts directory if it doesn't exist
        prompts_dir = 'data/prompts'
        os.makedirs(prompts_dir, exist_ok=True)
        
        # Create patient_characteristics directory
        pc_dir = os.path.join(prompts_dir, 'patient_characteristics')
        os.makedirs(pc_dir, exist_ok=True)
        
        # Save default template if not already saved
        version = 'v1.0'
        prompt_file = os.path.join(pc_dir, f"{version}.txt")
        
        if not os.path.exists(prompt_file):
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(cls.PATIENT_CHARACTERISTICS_TEMPLATE)
            
            # Save version info
            versions_file = os.path.join(prompts_dir, 'versions.json')
            versions = {}
            
            if os.path.exists(versions_file):
                try:
                    with open(versions_file, 'r') as f:
                        versions = json.load(f)
                except Exception as e:
                    logger.error(f"Error loading versions: {str(e)}")
            
            versions['patient_characteristics'] = version
            
            with open(versions_file, 'w') as f:
                json.dump(versions, f)
                
            logger.info(f"Initialized prompt template 'patient_characteristics' with version {version}")
        
        # Initialize analytics file if it doesn't exist
        analytics_file = os.path.join(prompts_dir, 'analytics.json')
        if not os.path.exists(analytics_file):
            analytics = defaultdict(lambda: defaultdict(int))
            with open(analytics_file, 'w') as f:
                json.dump({}, f)
    
    @staticmethod
    def get_extraction_prompt(text):
        """
        Generate a prompt for extracting patient characteristics
        
        Args:
            text (str): The text chunk to analyze
            
        Returns:
            str: Formatted prompt for the LLM
        """
        return PromptTemplate.PATIENT_CHARACTERISTICS_TEMPLATE.format(text=text)
    
    @staticmethod
    def custom_extraction_prompt(text, characteristics=None):
        """
        Generate a custom extraction prompt with specific characteristics to look for
        
        Args:
            text (str): The text chunk to analyze
            characteristics (list, optional): List of specific characteristics to extract
            
        Returns:
            str: Formatted prompt for the LLM
        """
        if not characteristics:
            return PromptTemplate.get_extraction_prompt(text)
        
        characteristics_str = "\n".join([f"- {item}" for item in characteristics])
        
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
        
    @classmethod
    def get_all_prompt_versions(cls, prompt_name):
        """
        Get all versions of a prompt
        
        Args:
            prompt_name (str): Name of the prompt
            
        Returns:
            list: List of version identifiers
        """
        prompts_dir = 'data/prompts'
        prompt_dir = os.path.join(prompts_dir, prompt_name)
        
        if not os.path.exists(prompt_dir):
            return []
        
        # Get all txt files
        versions = []
        for filename in os.listdir(prompt_dir):
            if filename.endswith('.txt'):
                versions.append(filename[:-4])  # Remove .txt extension
        
        versions.sort()  # Sort versions
        return versions
    
    @classmethod
    def get_prompt_analytics(cls, prompt_name=None):
        """
        Get analytics for prompt usage
        
        Args:
            prompt_name (str, optional): Name of the prompt to get analytics for
            
        Returns:
            dict: Analytics data
        """
        prompts_dir = 'data/prompts'
        analytics_file = os.path.join(prompts_dir, 'analytics.json')
        
        if not os.path.exists(analytics_file):
            return {}
            
        try:
            with open(analytics_file, 'r') as f:
                analytics = json.load(f)
                
            if prompt_name:
                return analytics.get(prompt_name, {})
            else:
                return analytics
        except Exception as e:
            logger.error(f"Error loading analytics: {str(e)}")
            return {}