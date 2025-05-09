# tests/test_template_categories.py
"""
Test module for template categories functionality
"""
import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from src.utils.prompt_manager import PromptManager
from src.utils.config.template_categories import CATEGORY_GROUPS

def test_categories():
    """Test the template categories functionality"""
    
    # Create a temporary directory for templates
    temp_dir = os.path.join(os.path.dirname(__file__), "temp_templates")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Create a prompt manager with the temp directory
        manager = PromptManager(templates_dir=temp_dir)
        
        # Create a few test templates with categories
        template1_id = "demographic_extraction"
        template1_text = "Extract demographics from the following RCT: {text}"
        template1_categories = {
            "extraction_domain": ["population_parameters"],
            "data_structuring": ["tabular_export"],
            "customization_target": ["domain_specific"]
        }
        
        template2_id = "outcome_extraction"
        template2_text = "Extract outcome measures from the following RCT: {text}"
        template2_categories = {
            "extraction_domain": ["outcome_measures", "safety_profile"],
            "data_structuring": ["ml_training_ready"],
            "customization_target": ["variable_focused"]
        }
        
        # Save the templates with categories
        version1 = manager.save_template(
            template1_id, 
            template1_text, 
            "Template for demographic extraction",
            categories=template1_categories
        )
        
        version2 = manager.save_template(
            template2_id, 
            template2_text, 
            "Template for outcome extraction",
            categories=template2_categories
        )
        
        logger.info(f"Created template versions: {version1}, {version2}")
        
        # Test filtering by categories
        population_templates = manager.filter_templates_by_category(
            "extraction_domain", "population_parameters"
        )
        logger.info(f"Templates for population parameters: {population_templates}")
        assert template1_id in population_templates
        assert template2_id not in population_templates
        
        outcome_templates = manager.filter_templates_by_category(
            "extraction_domain", "outcome_measures"
        )
        logger.info(f"Templates for outcome measures: {outcome_templates}")
        assert template2_id in outcome_templates
        assert template1_id not in outcome_templates
        
        # Test loading templates
        template1 = manager.get_template(template1_id)
        categories1 = template1.get('metadata', {}).get('categories', {})
        logger.info(f"Template 1 categories: {categories1}")
        assert "population_parameters" in categories1.get("extraction_domain", [])
        
        # Test with invalid category
        template3_id = "test_invalid_category"
        template3_text = "Test template with invalid category: {text}"
        template3_categories = {
            "invalid_group": ["invalid_value"],
            "extraction_domain": ["population_parameters", "invalid_value"]
        }
        
        version3 = manager.save_template(
            template3_id, 
            template3_text, 
            "Template with invalid category",
            categories=template3_categories
        )
        
        template3 = manager.get_template(template3_id)
        categories3 = template3.get('metadata', {}).get('categories', {})
        logger.info(f"Template 3 categories after validation: {categories3}")
        
        # Should only contain valid categories
        assert "invalid_group" not in categories3
        assert "population_parameters" in categories3.get("extraction_domain", [])
        assert "invalid_value" not in categories3.get("extraction_domain", [])
        
        return True
    
    finally:
        # Clean up temp directory
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_result = test_categories()
    logger.info(f"Test completed with result: {test_result}")