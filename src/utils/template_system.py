"""
Unified prompt template management system
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from .prompt_manager import PromptManager
from .prompt_templates import PromptTemplate
from .analytics import PromptAnalytics

# Configure logging
logger = logging.getLogger(__name__)

class TemplateSystem:
    """
    Unified system for managing prompt templates, versioning, and analytics
    """
    
    def __init__(self, templates_dir: Optional[str] = None, analytics_dir: Optional[str] = None):
        """
        Initialize the template system
        
        Args:
            templates_dir (str, optional): Directory to store templates
            analytics_dir (str, optional): Directory to store analytics
        """
        # Initialize components
        self.prompt_manager = PromptManager(templates_dir)
        self.analytics = PromptAnalytics(analytics_dir)
        
        # Base directory for template storage
        self.templates_dir = templates_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'prompts'
        )
        
        logger.info(f"Initialized TemplateSystem with templates directory: {self.templates_dir}")
    
    def create_template(self, template_id: str, template_text: str, 
                        description: Optional[str] = None, 
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Create a new template or a new version of an existing template
        
        Args:
            template_id (str): Identifier for the template
            template_text (str): The template text
            description (str, optional): Description of the template
            metadata (dict, optional): Additional metadata
            
        Returns:
            str: Version identifier for the created template
        """
        version_id = self.prompt_manager.save_template(
            template_id, template_text, description, metadata
        )
        logger.info(f"Created template {template_id} with version {version_id}")
        return version_id
    
    def get_template(self, template_id: str, version_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a template by ID and optionally version ID
        
        Args:
            template_id (str): Identifier for the template
            version_id (str, optional): Version identifier
            
        Returns:
            dict: Template data
        """
        return self.prompt_manager.get_template(template_id, version_id)
    
    def get_template_text(self, template_id: str, version_id: Optional[str] = None) -> str:
        """
        Get template text by ID and optionally version ID
        
        Args:
            template_id (str): Identifier for the template
            version_id (str, optional): Version identifier
            
        Returns:
            str: Template text
        """
        return self.prompt_manager.get_template_text(template_id, version_id)
    
    def list_templates(self) -> List[str]:
        """
        List all available templates
        
        Returns:
            list: List of template IDs
        """
        return self.prompt_manager.list_templates()
    
    def list_versions(self, template_id: str) -> List[str]:
        """
        List all versions for a specific template
        
        Args:
            template_id (str): Identifier for the template
            
        Returns:
            list: List of version IDs
        """
        return self.prompt_manager.list_versions(template_id)
    
    def get_extraction_prompt(self, text: str, template_id: str = "patient_characteristics", 
                               version_id: Optional[str] = None) -> str:
        """
        Generate an extraction prompt using a template
        
        Args:
            text (str): The text to extract from
            template_id (str): The template to use
            version_id (str, optional): Specific version to use
            
        Returns:
            str: The formatted prompt
        """
        template_text = self.get_template_text(template_id, version_id)
        
        # If template not found, fall back to default template
        if not template_text:
            logger.warning(f"Template {template_id} not found, using default template")
            return PromptTemplate.get_extraction_prompt(text)
        
        # Replace the placeholder with the text
        return template_text.replace("{text}", text)
    
    def get_best_performing_template(self, disease_type: Optional[str] = None, 
                                     min_success_rate: float = 0.7) -> Optional[str]:
        """
        Get the best performing template based on analytics
        
        Args:
            disease_type (str, optional): Specific disease type to filter for
            min_success_rate (float): Minimum success rate required
            
        Returns:
            str: Template ID of the best performing template
        """
        # Get analytics summary
        summary = self.analytics.get_analytics_summary()
        
        # Extract template performance
        template_performance = summary.get('template_performance', {})
        
        # Filter templates
        candidates = []
        for template_id, metrics in template_performance.items():
            # Skip templates with too few runs or low success rate
            if metrics.get('count', 0) < 5 or metrics.get('success', 0) < min_success_rate:
                continue
            
            # If disease type is specified, filter by metadata
            if disease_type:
                template = self.get_template(template_id)
                if not template or not template.get('metadata'):
                    continue
                    
                # Check if template is for the specified disease
                template_disease = template.get('metadata', {}).get('disease')
                if template_disease != disease_type:
                    continue
            
            candidates.append((template_id, metrics))
        
        # Return the template with the highest success rate
        if candidates:
            candidates.sort(key=lambda x: x[1].get('success', 0), reverse=True)
            return candidates[0][0]
            
        # If no suitable template found, return None
        return None
    
    def track_template_usage(self, template_id: str, version_id: str, source_file: str,
                            characteristics_found: int, start_time: datetime, 
                            end_time: datetime, success: bool = True,
                            error: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Track template usage for analytics
        
        Args:
            template_id (str): Template ID used
            version_id (str): Version ID used
            source_file (str): Source file processed
            characteristics_found (int): Number of characteristics found
            start_time (datetime): Start time of processing
            end_time (datetime): End time of processing
            success (bool): Whether the extraction was successful
            error (str, optional): Error message if unsuccessful
            metadata (dict, optional): Additional metadata
        """
        self.analytics.log_extraction(
            template_id, version_id, source_file, 
            characteristics_found, start_time, end_time,
            success, error, metadata
        )
        
        logger.info(f"Tracked usage of template {template_id} version {version_id}")
    
    def get_analytics_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get summary of template performance
        
        Args:
            days (int): Number of days to include
            
        Returns:
            dict: Analytics summary
        """
        return self.analytics.get_analytics_summary(days)
    
    def export_analytics(self, output_path: Optional[str] = None) -> str:
        """
        Export analytics data to CSV
        
        Args:
            output_path (str, optional): Path to save the CSV
            
        Returns:
            str: Path to the saved CSV
        """
        return self.analytics.export_analytics_csv(output_path)