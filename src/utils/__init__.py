# src/utils/__init__.py (update)
"""
Utility modules for the research data extraction project
"""
from .data_extractor import DataExtractor
from .prompt_templates import PromptTemplate
from .prompt_manager import PromptManager
from .analytics import PromptAnalytics
from .config_manager import ConfigManager
from .unified_analytics import Analytics
from .results_manager import ResultsManager  # Add this import
from .batch_processor import BatchProcessor  # Add this import too

# Create a global configuration instance
config = ConfigManager()
PromptAnalytics = Analytics
AnalyticsTracker = Analytics

# Make these classes directly importable 
__all__ = ['DataExtractor', 'PromptTemplate', 'PromptManager', 
           'Analytics', 'PromptAnalytics', 'AnalyticsTracker', 'ConfigManager', 
           'config', 'ResultsManager', 'BatchProcessor']