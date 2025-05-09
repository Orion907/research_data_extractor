# tests/test_template_preview.py
"""
Test module for template preview and validation functionality
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

def test_template_validation():
    """Test the template validation functionality"""
    
    # Create a temporary directory for templates
    temp_dir = os.path.join(os.path.dirname(__file__), "temp_templates_validation")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Create a prompt manager with the temp directory
        manager = PromptManager(templates_dir=temp_dir)
        
        # Test valid template
        valid_template = "Extract patient characteristics from the following text: {text}"
        validation_result = manager.validate_template(valid_template)
        logger.info(f"Validation result for valid template: {validation_result}")
        assert validation_result['valid']
        assert 'text' in validation_result['placeholders']
        
        # Test invalid template (no placeholders)
        invalid_template = "This template has no placeholders."
        validation_result = manager.validate_template(invalid_template)
        logger.info(f"Validation result for template with no placeholders: {validation_result}")
        assert not validation_result['valid']
        
        # Test invalid template (missing text placeholder)
        invalid_template = "This template has a placeholder but not text: {other_placeholder}"
        validation_result = manager.validate_template(invalid_template)
        logger.info(f"Validation result for template without text placeholder: {validation_result}")
        assert not validation_result['valid']
        
        # Test saving valid template
        try:
            version_id = manager.save_template(
                "valid_template", 
                valid_template, 
                "Valid template with text placeholder"
            )
            logger.info(f"Saved valid template as version: {version_id}")
        except ValueError as e:
            logger.error(f"Unexpected error saving valid template: {e}")
            assert False, "Valid template should save without errors"
        
        # Test saving invalid template (should raise ValueError)
        try:
            manager.save_template(
                "invalid_template", 
                invalid_template, 
                "Invalid template without text placeholder"
            )
            assert False, "Invalid template should raise ValueError"
        except ValueError as e:
            logger.info(f"Expected error saving invalid template: {e}")
        
        return True
    
    finally:
        # Clean up temp directory
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

def test_template_preview():
    """Test the template preview functionality"""
    
    # Create a temporary directory for templates
    temp_dir = os.path.join(os.path.dirname(__file__), "temp_templates_preview")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # Create a prompt manager with the temp directory
        manager = PromptManager(templates_dir=temp_dir)
        
        # Test basic template preview
        template = "Extract patient characteristics from the following text: {text}"
        preview = manager.preview_template(template)
        logger.info(f"Basic preview: {preview}")
        assert "sample research article" in preview.lower()
        
        # Test preview with custom sample data
        hypertension_sample = {
            'text': 'In this study, 50 patients with hypertension were randomized...'
        }
        preview = manager.preview_template(template, hypertension_sample)
        logger.info(f"Custom preview: {preview}")
        assert "50 patients with hypertension" in preview
        
        # Test template with multiple placeholders
        multi_template = "Analyze {text} focusing on {focus_area} with {detail_level} detail."
        multi_sample_data = {
            'text': 'Clinical trial results for Drug X',
            'focus_area': 'adverse events'
        }
        preview = manager.preview_template(multi_template, multi_sample_data)
        logger.info(f"Multi-placeholder preview: {preview}")
        assert "Clinical trial results for Drug X" in preview
        assert "adverse events" in preview
        assert "[SAMPLE DETAIL_LEVEL]" in preview
        
        # Add these debug lines
        logger.info(f"TEMPLATE TEXT ABOUT TO USE: '{template}'")
        logger.info(f"SAMPLE DATA ABOUT TO USE: {hypertension_sample}")
        
        # Test get_template_with_preview
        version_id = manager.save_template(
            "preview_template", 
            template, 
            "Template for preview testing"
        )
        
        # Get template with preview and add additional debugging
        template_with_preview = manager.get_template_with_preview(
            "preview_template",
            version_id=None,
            sample_data=hypertension_sample
        )
        
        # Add this line to directly print the preview content
        logger.info(f"ACTUAL PREVIEW CONTENT: >>>{template_with_preview['preview']}<<<")
        
        logger.info(f"Template with preview metadata: {template_with_preview.keys()}")
        
        # Check if hypertension is ANYWHERE in the preview
        if "hypertension" in template_with_preview['preview']:
            logger.info("Hypertension word is present")
        else:
            logger.info("Hypertension word is NOT present")
        
        # Now run the assertions
        assert 'preview' in template_with_preview
        assert "50 patients with hypertension" in template_with_preview['preview']
        
        return True
    
    finally:
        # Clean up temp directory
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    test_validation_result = test_template_validation()
    logger.info(f"Validation test completed with result: {test_validation_result}")
    
    test_preview_result = test_template_preview()
    logger.info(f"Preview test completed with result: {test_preview_result}")