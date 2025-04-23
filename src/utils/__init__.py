# src/utils/__init__.py (updated)
"""
Utility modules for the research data extraction project
"""
from .data_extractor import DataExtractor
from .prompt_templates import PromptTemplate
from .prompt_manager import PromptManager
from .analytics import PromptAnalytics
from .config_manager import ConfigManager

# Create a global configuration instance
config = ConfigManager()

# Make these classes directly importable 
__all__ = ['DataExtractor', 'PromptTemplate', 'PromptManager', 'PromptAnalytics', 'ConfigManager', 'config']