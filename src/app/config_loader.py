"""
Configuration loading utilities for Streamlit app

Provides centralized configuration initialization and management
with safe defaults and error handling.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from src.utils import ConfigManager, TemplateSystem, Analytics


class ConfigurationLoader:
    """
    Centralized configuration loader for the Streamlit application.
    
    Handles initialization of all configuration systems including
    ConfigManager, TemplateSystem, and Analytics with proper error handling
    and safe defaults.
    """
    
    def __init__(self):
        """Initialize configuration loader."""
        self.logger = logging.getLogger(__name__)
        self._config_manager: Optional[ConfigManager] = None
        self._template_system: Optional[TemplateSystem] = None
        self._analytics: Optional[Analytics] = None
        self._initialization_errors: List[str] = []
    
    def initialize_all(self) -> Dict[str, Any]:
        """
        Initialize all configuration systems.
        
        Returns:
            Dictionary containing initialized systems and any errors
        """
        result = {
            'config_manager': None,
            'template_system': None, 
            'analytics': None,
            'errors': [],
            'success': True
        }
        
        # Initialize ConfigManager
        try:
            self._config_manager = ConfigManager()
            result['config_manager'] = self._config_manager
            self.logger.info("ConfigManager initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize ConfigManager: {str(e)}"
            self.logger.error(error_msg)
            result['errors'].append(error_msg)
            result['success'] = False
        
        # Initialize TemplateSystem
        try:
            self._template_system = TemplateSystem()
            result['template_system'] = self._template_system
            self.logger.info("TemplateSystem initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize TemplateSystem: {str(e)}"
            self.logger.error(error_msg)
            result['errors'].append(error_msg)
            result['success'] = False
        
        # Initialize Analytics
        try:
            self._analytics = Analytics()
            result['analytics'] = self._analytics
            self.logger.info("Analytics system initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize Analytics: {str(e)}"
            self.logger.error(error_msg)
            result['errors'].append(error_msg)
            result['success'] = False
        
        self._initialization_errors = result['errors']
        return result
    
    def get_config_manager(self) -> Optional[ConfigManager]:
        """
        Get the ConfigManager instance.
        
        Returns:
            ConfigManager instance or None if initialization failed
        """
        if self._config_manager is None:
            try:
                self._config_manager = ConfigManager()
            except Exception as e:
                self.logger.error(f"Failed to get ConfigManager: {str(e)}")
                return None
        
        return self._config_manager
    
    def get_template_system(self) -> Optional[TemplateSystem]:
        """
        Get the TemplateSystem instance.
        
        Returns:
            TemplateSystem instance or None if initialization failed
        """
        if self._template_system is None:
            try:
                self._template_system = TemplateSystem()
            except Exception as e:
                self.logger.error(f"Failed to get TemplateSystem: {str(e)}")
                return None
        
        return self._template_system
    
    def get_analytics(self) -> Optional[Analytics]:
        """
        Get the Analytics instance.
        
        Returns:
            Analytics instance or None if initialization failed
        """
        if self._analytics is None:
            try:
                self._analytics = Analytics()
            except Exception as e:
                self.logger.error(f"Failed to get Analytics: {str(e)}")
                return None
        
        return self._analytics
    
    def get_default_settings(self) -> Dict[str, Any]:
        """
        Get default application settings.
        
        Returns:
            Dictionary of default settings for the application
        """
        config = self.get_config_manager()
        
        default_settings = {
            # PDF Processing settings
            'chunk_size': config.get('pdf_processor.text_chunking.chunk_size', 1000) if config else 1000,
            'chunk_overlap': config.get('pdf_processor.text_chunking.overlap', 100) if config else 100,
            'respect_paragraphs': config.get('pdf_processor.text_chunking.respect_paragraphs', True) if config else True,
            
            # LLM settings
            'default_temperature': config.get('llm.temperature', 0.0) if config else 0.0,
            'default_provider': 'anthropic',
            
            # Model options
            'anthropic_models': [
                "claude-3-5-sonnet-20241022", 
                "claude-3-5-sonnet-20240620", 
                "claude-3-opus-20240229", 
                "claude-3-haiku-20240307"
            ],
            'openai_models': [
                "gpt-3.5-turbo", 
                "gpt-4o", 
                "gpt-4-1106-preview"
            ],
            'mock_models': ["mock-model"],
            
            # File handling
            'max_file_size_mb': 100,
            'supported_file_types': ['pdf'],
            'supported_batch_types': ['pdf', 'zip'],
            
            # Batch processing
            'max_batch_files': 50,
            'batch_processing_modes': [
                "Sequential (1 at a time)", 
                "Limited Parallel (3 at a time)", 
                "Full Parallel"
            ],
            
            # Output settings
            'default_output_dir': 'data/output',
            'default_temp_dir': 'data/temp',
            'default_annotations_dir': 'data/annotations',
            'default_reports_dir': 'data/reports'
        }
        
        return default_settings
    
    def get_api_key_requirements(self) -> Dict[str, str]:
        """
        Get API key requirements for different providers.
        
        Returns:
            Dictionary mapping providers to their required environment variables
        """
        return {
            'anthropic': 'ANTHROPIC_API_KEY',
            'openai': 'OPENAI_API_KEY',
            'mock': None  # No API key required for mock provider
        }
    
    def validate_api_key(self, provider: str) -> tuple[bool, str]:
        """
        Validate that required API key is available for provider.
        
        Args:
            provider: The LLM provider name
            
        Returns:
            Tuple of (is_valid, message)
        """
        requirements = self.get_api_key_requirements()
        
        if provider not in requirements:
            return False, f"Unknown provider: {provider}"
        
        required_key = requirements[provider]
        
        if required_key is None:
            return True, "No API key required"
        
        if not os.environ.get(required_key):
            return False, f"Missing required environment variable: {required_key}"
        
        return True, f"API key found for {provider}"
    
    def get_prompt_versions(self, template_name: str = 'patient_characteristics') -> List[str]:
        """
        Get available prompt versions from template system.
        
        Args:
            template_name: Name of the template
            
        Returns:
            List of available versions
        """
        template_system = self.get_template_system()
        
        if template_system is None:
            return ["default"]
        
        try:
            versions = template_system.list_versions(template_name)
            return versions if versions else ["default"]
        except Exception as e:
            self.logger.error(f"Failed to get prompt versions: {str(e)}")
            return ["default"]
    
    def get_initialization_status(self) -> Dict[str, Any]:
        """
        Get status of all initialized systems.
        
        Returns:
            Dictionary with initialization status
        """
        return {
            'config_manager_ready': self._config_manager is not None,
            'template_system_ready': self._template_system is not None,
            'analytics_ready': self._analytics is not None,
            'errors': self._initialization_errors.copy(),
            'has_errors': len(self._initialization_errors) > 0
        }
    
    def setup_logging(self, level: int = logging.INFO) -> None:
        """
        Setup application logging configuration.
        
        Args:
            level: Logging level
        """
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # Set specific logger levels if needed
        logging.getLogger('streamlit').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)
    
    @classmethod
    def create_default_loader(cls) -> 'ConfigurationLoader':
        """
        Create a configuration loader with default initialization.
        
        Returns:
            Configured ConfigurationLoader instance
        """
        loader = cls()
        loader.setup_logging()
        loader.initialize_all()
        return loader


# Global configuration loader instance for backward compatibility
_global_loader: Optional[ConfigurationLoader] = None


def get_global_config_loader() -> ConfigurationLoader:
    """
    Get or create the global configuration loader instance.
    
    Returns:
        Global ConfigurationLoader instance
    """
    global _global_loader
    
    if _global_loader is None:
        _global_loader = ConfigurationLoader.create_default_loader()
    
    return _global_loader


def get_config_manager() -> Optional[ConfigManager]:
    """Get ConfigManager from global loader."""
    return get_global_config_loader().get_config_manager()


def get_template_system() -> Optional[TemplateSystem]:
    """Get TemplateSystem from global loader."""
    return get_global_config_loader().get_template_system()


def get_analytics() -> Optional[Analytics]:
    """Get Analytics from global loader."""
    return get_global_config_loader().get_analytics()