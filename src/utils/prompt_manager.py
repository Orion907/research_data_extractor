# src/utils/prompt_manager.py
"""
Module for managing and versioning prompt templates
"""
import json
import os
import logging
from datetime import datetime
from .config.template_categories import ALL_CATEGORIES, CATEGORY_GROUPS

# Configure logging
logger = logging.getLogger(__name__)

class PromptManager:
    """
    Class for managing and versioning prompt templates
    """
    
    def __init__(self, templates_dir=None):
        """
        Initialize the prompt manager
        
        Args:
            templates_dir (str, optional): Directory to store prompt templates
        """
        # Default to a 'prompts' directory in the project root if not specified
        self.templates_dir = templates_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'prompts'
        )
        
        # Ensure the templates directory exists
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Dictionary to hold loaded prompt templates
        self.templates = {}
        
        # Load existing templates
        self._load_templates()
        
        logger.info(f"Initialized PromptManager with templates directory: {self.templates_dir}")
    
    def _load_templates(self):
        """
        Load all template files from the templates directory
        """
        if not os.path.exists(self.templates_dir):
            return
            
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(self.templates_dir, filename), 'r') as f:
                        template_data = json.load(f)
                        template_id = template_data.get('id')
                        if template_id:
                            self.templates[template_id] = template_data
                            logger.info(f"Loaded template: {template_id}")
                except Exception as e:
                    logger.error(f"Error loading template {filename}: {str(e)}")
    
    def save_template(self, template_id, template_text, description=None, metadata=None, categories=None):
        """
        Save a new template version
        
        Args:
            template_id (str): Identifier for the template
            template_text (str): The prompt template text
            description (str, optional): Description of the template
            metadata (dict, optional): Additional metadata for the template
            categories (dict, optional): Category tags for the template
                                        (e.g., {"extraction_domain": ["population_parameters"]})
            
        Returns:
            str: The version identifier for the saved template
        """
        # Generate a version identifier based on timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        version_id = f"{template_id}_v{timestamp}"
        
        # Process metadata and categories
        if metadata is None:
            metadata = {}
            
        # Validate and integrate categories
        processed_categories = self._validate_categories(categories)
        if processed_categories:
            metadata['categories'] = processed_categories
        
        # Create template data
        template_data = {
            'id': template_id,
            'version_id': version_id,
            'template_text': template_text,
            'description': description or f"Version created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            'created_at': datetime.now().isoformat(),
            'metadata': metadata
        }
        
        # Save to file
        filename = f"{version_id}.json"
        file_path = os.path.join(self.templates_dir, filename)
        
        try:
            with open(file_path, 'w') as f:
                json.dump(template_data, f, indent=2)
                
            # Update in-memory cache
            self.templates[template_id] = template_data
            
            logger.info(f"Saved template {template_id} as version {version_id}")
            return version_id
            
        except Exception as e:
            logger.error(f"Error saving template {template_id}: {str(e)}")
            raise
    
    def _validate_categories(self, categories):
        """
        Validate category tags against the defined category lists
        
        Args:
            categories (dict): Dictionary of category groups and their values
            
        Returns:
            dict: Validated categories dictionary
        """
        if not categories:
            return {}
            
        validated_categories = {}
        
        for group, values in categories.items():
            if group not in CATEGORY_GROUPS:
                logger.warning(f"Unknown category group: {group}")
                continue
                
            valid_values = []
            for value in values:
                if value in CATEGORY_GROUPS[group]:
                    valid_values.append(value)
                else:
                    logger.warning(f"Unknown category value: {value} in group {group}")
            
            if valid_values:
                validated_categories[group] = valid_values
                
        return validated_categories
    
    def get_template(self, template_id, version_id=None):
        """
        Get a template by ID and optionally version ID
        
        Args:
            template_id (str): Identifier for the template
            version_id (str, optional): Version identifier, returns latest if None
            
        Returns:
            dict: Template data dictionary
        """
        if template_id not in self.templates:
            logger.warning(f"Template {template_id} not found")
            return None
            
        # If version_id is specified, load that specific version
        if version_id:
            # Check if the current loaded template is the requested version
            if self.templates[template_id].get('version_id') == version_id:
                return self.templates[template_id]
                
            # Otherwise, load from file
            file_path = os.path.join(self.templates_dir, f"{version_id}.json")
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        return json.load(f)
                except Exception as e:
                    logger.error(f"Error loading template version {version_id}: {str(e)}")
                    return None
            else:
                logger.warning(f"Template version {version_id} not found")
                return None
        
        # Return the latest version
        return self.templates[template_id]
    
    def list_templates(self):
        """
        List all available templates
        
        Returns:
            list: List of template IDs
        """
        return list(self.templates.keys())
    
    def list_versions(self, template_id):
        """
        List all versions for a specific template
        
        Args:
            template_id (str): Identifier for the template
            
        Returns:
            list: List of version IDs
        """
        versions = []
        prefix = f"{template_id}_v"
        
        for filename in os.listdir(self.templates_dir):
            if filename.startswith(prefix) and filename.endswith('.json'):
                version_id = filename.replace('.json', '')
                versions.append(version_id)
        
        # Sort by timestamp (newest first)
        versions.sort(reverse=True)
        return versions

    def get_template_text(self, template_id, version_id=None):
        """
        Get the template text for a specific template and optionally version
        
        Args:
            template_id (str): Identifier for the template
            version_id (str, optional): Version identifier, returns latest if None
            
        Returns:
            str: Template text
        """
        template = self.get_template(template_id, version_id)
        if template:
            return template.get('template_text')
        return None
    
    def filter_templates_by_category(self, category_group, category_value):
        """
        Filter templates by a specific category
        
        Args:
            category_group (str): The category group (e.g., 'extraction_domain')
            category_value (str): The category value to filter by
            
        Returns:
            list: List of template IDs matching the category
        """
        matching_templates = []
        
        for template_id, template_data in self.templates.items():
            categories = template_data.get('metadata', {}).get('categories', {})
            if category_group in categories and category_value in categories[category_group]:
                matching_templates.append(template_id)
                
        return matching_templates