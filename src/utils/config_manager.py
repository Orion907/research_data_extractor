# src/utils/config_manager.py
"""
Module for managing application configuration
"""
import os
import yaml
import logging
from pathlib import Path
import re

# Configure logging
logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Manages application configuration loaded from YAML files with environment variable overrides,
    validation, and runtime reloading.
    """
    
    # Regular expression for environment variable substitution
    ENV_VAR_PATTERN = re.compile(r'\${([A-Za-z0-9_]+)(?::([^}]*))?}')
    
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
            project_root = Path(__file__).parent.parent.parent.absolute()
            config_dir = project_root / "config"
        else:
            config_dir = Path(config_dir).absolute()
        
        self.config_dir = config_dir
        
        # Set environment from env parameter or from environment variable
        self.env = env or os.environ.get("APP_ENV", "development")
        
        # Initialize empty configuration dictionary
        self.config = {}
        
        # Schema validation dictionary (to be populated by validate_schema)
        self.schema = {}
        
        # Load configuration
        self._load_config()
        
        logger.info(f"Configuration loaded for environment: {self.env}")
        logger.debug(f"Configuration directory: {self.config_dir}")
    
    def _load_config(self):
        """
        Load configuration from YAML files and apply environment variable overrides
        """
        # Load default configuration
        default_config_path = self.config_dir / "default.yaml"
        
        try:
            if default_config_path.exists():
                with open(default_config_path, 'r') as file:
                    self.config = yaml.safe_load(file) or {}
                logger.info(f"Loaded default configuration from {default_config_path}")
            else:
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
            else:
                logger.debug(f"Environment configuration file not found: {env_config_path}")
        except yaml.YAMLError as e:
            logger.error(f"Error parsing environment YAML configuration: {str(e)}")
            
        # Process environment variable substitutions
        self._process_env_vars(self.config)
    
    def _process_env_vars(self, config_dict):
        """
        Process environment variable substitutions in the config dictionary
        
        Args:
            config_dict (dict): Configuration dictionary to process
        """
        for key, value in config_dict.items():
            if isinstance(value, dict):
                # Recursively process nested dictionaries
                self._process_env_vars(value)
            elif isinstance(value, str):
                # Process string values for environment variable substitutions
                config_dict[key] = self._replace_env_vars(value)
    
    def _replace_env_vars(self, value):
        """
        Replace environment variables in a string value
        
        Args:
            value (str): String value to process
            
        Returns:
            str: Processed string with environment variables replaced
        """
        def replace_var(match):
            var_name = match.group(1)
            default_value = match.group(2)
            
            # Get the environment variable or use the default value
            env_value = os.environ.get(var_name)
            if env_value is not None:
                return env_value
            elif default_value is not None:
                return default_value
            else:
                # Keep the original if environment variable not found and no default
                return match.group(0)
        
        # Replace all environment variables in the string
        return self.ENV_VAR_PATTERN.sub(replace_var, value)
    
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
    
    def validate_schema(self, schema):
        """
        Set a validation schema for configuration values
        
        Args:
            schema (dict): Dictionary defining the expected types and constraints
                           for configuration values
        """
        self.schema = schema
        
        # Validate the current configuration
        self._validate_config(self.config, self.schema)
    
    def _validate_config(self, config, schema, path=""):
        """
        Validate configuration against schema
        
        Args:
            config (dict): Configuration to validate
            schema (dict): Schema to validate against
            path (str): Current path in the config (for error reporting)
            
        Raises:
            ValueError: If validation fails
        """
        for key, value_schema in schema.items():
            full_path = f"{path}.{key}" if path else key
            
            if key not in config:
                if value_schema.get("required", False):
                    raise ValueError(f"Missing required configuration value: {full_path}")
                continue
            
            value = config[key]
            
            # Check type
            expected_type = value_schema.get("type")
            if expected_type and not isinstance(value, expected_type):
                raise ValueError(f"Invalid type for {full_path}: expected {expected_type.__name__}, got {type(value).__name__}")
            
            # Validate nested schema
            nested_schema = value_schema.get("schema")
            if nested_schema and isinstance(value, dict):
                self._validate_config(value, nested_schema, full_path)
    
    def get(self, key, default=None, value_type=None):
        """
        Get a configuration value with optional type conversion
        
        Args:
            key (str): Configuration key in dot notation (e.g., 'app.debug')
            default: Default value to return if key is not found
            value_type (type, optional): Type to convert the value to
            
        Returns:
            The configuration value, or the default if not found
        """
        keys = key.split('.')
        value = self.config
        
        # Navigate through the nested dictionaries
        try:
            for k in keys:
                value = value[k]
                
            # Convert value type if specified
            if value_type is not None:
                try:
                    value = value_type(value)
                except (ValueError, TypeError):
                    logger.warning(f"Failed to convert {key} to {value_type.__name__}")
                    return default
                    
            return value
        except (KeyError, TypeError):
            return default
    
    def get_int(self, key, default=None):
        """Get configuration value as integer"""
        return self.get(key, default, int)
    
    def get_float(self, key, default=None):
        """Get configuration value as float"""
        return self.get(key, default, float)
    
    def get_bool(self, key, default=None):
        """Get configuration value as boolean"""
        return self.get(key, default, bool)
    
    def get_list(self, key, default=None):
        """Get configuration value as list"""
        value = self.get(key, default)
        if isinstance(value, list):
            return value
        return default
    
    def get_all(self):
        """
        Get the entire configuration
        
        Returns:
            dict: The entire configuration dictionary
        """
        return self.config.copy()
    
    def get_path(self, key, relative_to_project_root=True, create=False):
        """
        Get a path from the configuration, resolving it relative to project root if needed
        
        Args:
            key (str): Configuration key in dot notation
            relative_to_project_root (bool): Whether to resolve the path relative to project root
            create (bool): Whether to create the directory if it doesn't exist
            
        Returns:
            Path: The resolved path
        """
        path_str = self.get(key)
        if not path_str:
            return None
            
        path = Path(path_str)
        
        if relative_to_project_root and not path.is_absolute():
            # Resolve relative to project root
            project_root = Path(__file__).parent.parent.parent.absolute()
            path = project_root / path
            
        if create and not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {path}")
            except Exception as e:
                logger.error(f"Failed to create directory {path}: {str(e)}")
                
        return path
    
    def reload(self):
        """
        Reload configuration from files
        
        Returns:
            bool: True if reload was successful, False otherwise
        """
        try:
            old_config = self.config.copy()
            self._load_config()
            
            # Validate against schema if set
            if self.schema:
                try:
                    self._validate_config(self.config, self.schema)
                except ValueError as e:
                    # Restore old configuration if validation fails
                    self.config = old_config
                    logger.error(f"Configuration validation failed after reload: {str(e)}")
                    return False
                    
            logger.info("Configuration reloaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error reloading configuration: {str(e)}")
            return False
    
    def set(self, key, value):
        """
        Set a configuration value at runtime
        
        Args:
            key (str): Configuration key in dot notation
            value: Value to set
            
        Returns:
            bool: True if set was successful, False otherwise
        """
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in config or not isinstance(config[k], dict):
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        return True