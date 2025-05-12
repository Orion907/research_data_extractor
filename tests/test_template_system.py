"""
Test module for the unified template system
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.utils.template_system import TemplateSystem

def test_template_system():
    """Test the unified template system functionality"""
    
    # Create a template system
    logger.info("Creating template system...")
    template_system = TemplateSystem()
    
    # Create a few test templates
    template1_id = "test_unified_template_1"
    template1_text = "This is test template 1 from the unified system. Context: {text}"
    
    template2_id = "test_unified_template_2"
    template2_text = "This is test template 2 from the unified system. Article: {text}"
    
    # Save the templates
    logger.info("Creating test templates...")
    version1 = template_system.create_template(
        template1_id, 
        template1_text, 
        "First test template using unified system",
        {"type": "test", "unified": True}
    )
    
    version2 = template_system.create_template(
        template2_id, 
        template2_text, 
        "Second test template using unified system",
        {"type": "test", "unified": True}
    )
    
    logger.info(f"Created template versions: {version1}, {version2}")
    
    # List available templates
    templates = template_system.list_templates()
    logger.info(f"Available templates: {templates}")
    
    # Create another version of the first template
    template1_updated = "This is an updated test template 1 from the unified system. Input: {text}"
    version1_updated = template_system.create_template(
        template1_id, 
        template1_updated, 
        "Updated first template using unified system"
    )
    
    logger.info(f"Created updated template version: {version1_updated}")
    
    # List versions of template 1
    versions = template_system.list_versions(template1_id)
    logger.info(f"Versions of template 1: {versions}")
    
    # Retrieve different versions
    latest = template_system.get_template_text(template1_id)
    original = template_system.get_template_text(template1_id, version1)
    
    logger.info(f"Latest version of template 1: {latest}")
    logger.info(f"Original version of template 1: {original}")
    
    # Test generating extraction prompts with templates
    sample_text = "This is a sample text that would normally be from a research article."
    
    prompt1 = template_system.get_extraction_prompt(sample_text, template1_id)
    prompt2 = template_system.get_extraction_prompt(sample_text, template2_id)
    
    logger.info("Generated extraction prompt with template 1:")
    logger.info(prompt1)
    
    logger.info("Generated extraction prompt with template 2:")
    logger.info(prompt2)
    
    # Test tracking template usage
    logger.info("Tracking template usage...")
    template_system.track_template_usage(
        template1_id,
        version1,
        "test_file_unified.pdf",
        15,
        datetime.now(),
        datetime.now(),
        True,
        None,
        {"test": True, "system": "unified"}
    )
    
    # Get analytics summary
    logger.info("Getting analytics summary...")
    summary = template_system.get_analytics_summary()
    
    logger.info("Analytics summary:")
    for key, value in summary.items():
        if key != 'template_performance':
            logger.info(f"  {key}: {value}")
    
    if 'template_performance' in summary:
        logger.info("Template performance:")
        for template_id, metrics in summary['template_performance'].items():
            logger.info(f"  {template_id}: {metrics}")
    
    # Export analytics to CSV
    csv_path = template_system.export_analytics()
    logger.info(f"Exported analytics to CSV: {csv_path}")
    
    return True

if __name__ == "__main__":
    test_template_system()
    logger.info("Template system test completed successfully!")