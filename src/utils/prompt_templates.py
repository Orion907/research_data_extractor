"""
Module for LLM prompt templates
"""
import logging

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
    
    Format your response as a structured list of key-value pairs.
    
    ARTICLE SECTION:
    {text}
    
    EXTRACTED PATIENT CHARACTERISTICS:
    """
    
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