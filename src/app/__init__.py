"""
App foundation utilities for Streamlit Research Data Extractor

This package contains core utilities that provide a foundation layer
for the Streamlit application with minimal coupling and high safety.
"""

from .session_state import SessionStateManager
from .file_handlers import FileHandlerUtils
from .config_loader import ConfigurationLoader

__all__ = [
    'SessionStateManager',
    'FileHandlerUtils', 
    'ConfigurationLoader'
]