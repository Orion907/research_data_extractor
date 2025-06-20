# src/utils/__init__.py
"""
Utility modules for the research data extraction project
"""
from .data_extractor import DataExtractor
from .prompt_templates import PromptTemplate
from .prompt_manager import PromptManager
from .analytics import PromptAnalytics
from .config_manager import ConfigManager
from .unified_analytics import Analytics
from .template_system import TemplateSystem
from .domain_priming import TermMapper

# Create a global configuration instance
config = ConfigManager()
PromptAnalytics = Analytics
AnalyticsTracker = Analytics

# Create a global template system instance
template_system = TemplateSystem()

# Make these classes directly importable 
__all__ = [
    'DataExtractor', 
    'PromptTemplate', 
    'PromptManager', 
    'Analytics', 
    'PromptAnalytics', 
    'AnalyticsTracker', 
    'ConfigManager', 
    'config',
    'TemplateSystem',
    'template_system',
    'TermMapper'
]