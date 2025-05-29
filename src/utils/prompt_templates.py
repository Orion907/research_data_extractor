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
    
    # Base prompt for extracting comprehensive clinical research data
    COMPREHENSIVE_RESEARCH_TEMPLATE = """
    You are an AI assistant specialized in extracting comprehensive clinical research data from medical research articles.

    Below is a section of a research article. Please extract ALL available research information, organized by the PICOTS framework:

    **POPULATION:** Demographics, sample size, inclusion/exclusion criteria, baseline characteristics
    **INTERVENTION:** Treatment details, dosages, procedures, protocols  
    **COMPARATOR:** Control groups, placebo details, comparison treatments
    **OUTCOMES:** Primary/secondary endpoints, efficacy measures, safety data
    **TIMING:** Study duration, follow-up periods, treatment schedules
    **SETTING:** Study locations, care settings, geographic details

{picots_enhancement}

{abbreviations_context}

Format your response as a JSON object with the following structure:
{{
  "population": {{
    "demographics": {{
      "age": "",
      "gender": "",
      "ethnicity": "",
      "sample_size": ""
    }},
    "inclusion_criteria": [],
    "exclusion_criteria": [],
    "baseline_characteristics": [],
    "comorbidities": []
  }},
  "intervention": {{
    "treatments": [],
    "dosages": [],
    "procedures": [],
    "duration": ""
  }},
  "comparator": {{
    "control_type": "",
    "control_details": [],
    "comparison_groups": []
  }},
  "outcomes": {{
    "primary_endpoints": [],
    "secondary_endpoints": [],
    "safety_measures": [],
    "efficacy_measures": []
  }},
  "timing": {{
    "study_duration": "",
    "follow_up_periods": [],
    "treatment_schedule": ""
  }},
  "setting": {{
    "locations": [],
    "care_settings": [],
    "geographic_scope": ""
  }}
}}

ARTICLE SECTION:
{text}

EXTRACTED RESEARCH DATA:
"""
    
    @classmethod
    def initialize(cls):
        """
        Initialize prompt templates and save initial versions
        """
        # Create prompts directory if it doesn't exist
        prompts_dir = 'data/prompts'
        os.makedirs(prompts_dir, exist_ok=True)
        
        # Create comprehensive_research directory  
        cr_dir = os.path.join(prompts_dir, 'comprehensive_research')
        os.makedirs(cr_dir, exist_ok=True)
        
        # Save default template if not already saved
        version = 'v1.0'
        prompt_file = os.path.join(cr_dir, f"{version}.txt")
        
        if not os.path.exists(prompt_file):
            with open(prompt_file, 'w', encoding='utf-8') as f:
                f.write(cls.COMPREHENSIVE_RESEARCH_TEMPLATE)
            
            # Save version info
            versions_file = os.path.join(prompts_dir, 'versions.json')
            versions = {}
            
            if os.path.exists(versions_file):
                try:
                    with open(versions_file, 'r') as f:
                        versions = json.load(f)
                except Exception as e:
                    logger.error(f"Error loading versions: {str(e)}")
            
            versions['comprehensive_research'] = version
            
            with open(versions_file, 'w') as f:
                json.dump(versions, f)
                
            logger.info(f"Initialized prompt template 'comprehensive_research' with version {version}")
        
        # Initialize analytics file if it doesn't exist
        analytics_file = os.path.join(prompts_dir, 'analytics.json')
        if not os.path.exists(analytics_file):
            analytics = defaultdict(lambda: defaultdict(int))
            with open(analytics_file, 'w') as f:
                json.dump({}, f)
    
    @staticmethod
    def get_extraction_prompt(text, picots_context=None, version=None):
        """
        Generate a prompt for extracting comprehensive clinical research data
    
        Args:
            text (str): The text chunk to analyze
            picots_context (dict, optional): PICOTS data to enhance extraction focus
            version (str, optional): Version of the template to use (not fully implemented yet)
        
        Returns:
            str: Formatted prompt for the LLM
        """
        if version:
            logger.warning(f"Version parameter '{version}' provided to get_extraction_prompt() but versioning is not fully implemented. Using default template.")
    
        # Prepare enhancement sections
        picots_enhancement = ""
        abbreviations_context = ""
    
        if picots_context:
            # Add PICOTS-specific focus areas
            picots_enhancement = "\n**SPECIAL FOCUS AREAS:**\n"
        
            # Add Key Questions if available
            if picots_context.get('key_questions'):
                picots_enhancement += "Key Research Questions to address:\n"
                for kq in picots_context['key_questions']:
                    picots_enhancement += f"- {kq}\n"
        
            # Add specific PICOTS criteria if available
            if picots_context.get('picots_sections'):
                picots_enhancement += "\nPay special attention to:\n"
                for section, criteria in picots_context['picots_sections'].items():
                    if criteria:
                        picots_enhancement += f"- {section.upper()}: {criteria}\n"
        
            # Add abbreviations context
            if picots_context.get('abbreviations'):
                abbreviations_context = "\n**ABBREVIATIONS TO RECOGNIZE:**\n"
                for abbrev, definition in picots_context['abbreviations'].items():
                    abbreviations_context += f"- {abbrev}: {definition}\n"
    
        # Format the template with dynamic content
        return PromptTemplate.COMPREHENSIVE_RESEARCH_TEMPLATE.format(
            text=text,
            picots_enhancement=picots_enhancement,
            abbreviations_context=abbreviations_context
        )
    
    @staticmethod
    def custom_extraction_prompt(text, characteristics=None, version=None):
        """
        Generate a custom extraction prompt with specific characteristics to look for
    
        Args:
            text (str): The text chunk to analyze
            characteristics (list, optional): List of specific characteristics to extract
            version (str, optional): Version of the template to use (not fully implemented yet)
            
        Returns:
            str: Formatted prompt for the LLM
        """
        if version:
            logger.warning(f"Version parameter '{version}' provided to custom_extraction_prompt() but versioning is not fully implemented. Using default template.")
        
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