"""
Utility modules for the research data extraction project
"""
from .data_extractor import DataExtractor
from .prompt_templates import PromptTemplate

# Make these classes directly importable 
__all__ = ['DataExtractor', 'PromptTemplate']