"""
Module for managing application configuration
"""
import os
import yaml
import logging
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Manages application configuration loaded from YAML files
    """
    
    def __init__(self, config_dir=None, env=None):
        """
        Initialize the configuration manager
        
        Args:
            config_dir (str, optional): Path to the configuration directory
            env (str, optional): Environment name (development, production, etc.)
        """
        # Set default config directory if not provided
        if config_dir is None:
            # Get project root directory (assuming this file is in src/utils)
            project_root = Path(__file__).parent.parent.parent
            config_dir = project_root / "config"
        
        self.config_dir = Path(config_dir)
        
        # Set environment from env parameter or from environment variable
        self.env = env or os.environ.get("APP_ENV", "development")
        
        # Initialize empty configuration dictionary
        self.config = {}
        
        # Load configuration
        self._load_config()
        
        logger.info(f"Configuration loaded for environment: {self.env}")
    
    def _load_config(self):
        """
        Load configuration from YAML files
        """
        # Load default configuration
        default_config_path = self.config_dir / "default.yaml"
        
        try:
            with open(default_config_path, 'r') as file:
                self.config = yaml.safe_load(file) or {}
            logger.info(f"Loaded default configuration from {default_config_path}")
        except FileNotFoundError:
            logger.warning(f"Default configuration file not found: {default_config_path}")
            self.config = {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing default YAML configuration: {str(e)}")
            self.config = {}
        
        # Load environment-specific configuration
        env_config_path = self.config_dir / f"{self.env}.yaml"
        
        try:
            if env_config_path.exists():
                with open(env_config_path, 'r') as file:
                    env_config = yaml.safe_load(file) or {}
                
                # Merge environment config with default config
                self._deep_merge(self.config, env_config)
                logger.info(f"Loaded environment configuration from {env_config_path}")
        except yaml.YAMLError as e:
            logger.error(f"Error parsing environment YAML configuration: {str(e)}")
    
    def _deep_merge(self, dict1, dict2):
        """
        Deep merge dict2 into dict1
        
        Args:
            dict1 (dict): Base dictionary
            dict2 (dict): Dictionary to merge on top of base
        """
        for key, value in dict2.items():
            if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
                # Recursively merge dictionaries
                self._deep_merge(dict1[key], value)
            else:
                # Overwrite value in dict1
                dict1[key] = value
    
    def get(self, key, default=None):
        """
        Get a configuration value
        
        Args:
            key (str): Configuration key in dot notation (e.g., 'app.debug')
            default: Default value to return if key is not found
            
        Returns:
            The configuration value, or the default if not found
        """
        keys = key.split('.')
        value = self.config
        
        # Navigate through the nested dictionaries
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_all(self):
        """
        Get the entire configuration
        
        Returns:
            dict: The entire configuration dictionary
        """
        return self.config.copy()