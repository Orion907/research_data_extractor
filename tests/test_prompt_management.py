# tests/test_prompt_management.py
import os
import sys
import logging
import unittest
import json
from datetime import datetime

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.prompt_manager import PromptManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestPromptManagement(unittest.TestCase):
    """Tests for prompt management and versioning"""
    
    def setUp(self):
        """Set up test case - create a temporary prompt directory"""
        # Get project root directory
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Create a temporary prompts directory for testing
        self.test_prompts_dir = os.path.join(self.project_root, "test_prompts")
        os.makedirs(self.test_prompts_dir, exist_ok=True)
        
        # Initialize a prompt manager with the test directory
        self.prompt_manager = PromptManager(templates_dir=self.test_prompts_dir)
    
    def tearDown(self):
        """Clean up after test case - remove test prompt files"""
        # Remove all files in the test prompts directory
        for file in os.listdir(self.test_prompts_dir):
            file_path = os.path.join(self.test_prompts_dir, file)
            if os.path.isfile(file_path):
                os.unlink(file_path)
    
    def test_save_and_retrieve_template(self):
        """Test saving and retrieving a prompt template"""
        # Define a test template
        template_id = "test_template"
        template_text = "This is a test template. Extract data from: {text}"
        description = "Test description"
        
        # Save the template
        version_id = self.prompt_manager.save_template(
            template_id=template_id,
            template_text=template_text,
            description=description
        )
        
        # Verify the version ID is generated correctly
        self.assertIsNotNone(version_id)
        self.assertTrue(version_id.startswith(template_id + "_v"))
        
        # Retrieve the template
        template = self.prompt_manager.get_template(template_id)
        
        # Verify the template data
        self.assertIsNotNone(template)
        self.assertEqual(template["id"], template_id)
        self.assertEqual(template["template_text"], template_text)
        self.assertEqual(template["description"], description)
        
        logger.info(f"Successfully saved and retrieved template with version: {version_id}")
    
    def test_template_versioning(self):
        """Test creating multiple versions of a template"""
        # Define a test template
        template_id = "versioning_test"
        original_text = "Original template for {text}"
        
        # Save the first version
        version1 = self.prompt_manager.save_template(
            template_id=template_id,
            template_text=original_text,
            description="Original version"
        )
        
        # Save an updated version
        updated_text = "Updated template for {text}"
        version2 = self.prompt_manager.save_template(
            template_id=template_id,
            template_text=updated_text,
            description="Updated version"
        )
        
        # Verify two different version IDs were generated
        self.assertNotEqual(version1, version2)
        
        # List versions
        versions = self.prompt_manager.list_versions(template_id)
        
        # Verify both versions are listed
        self.assertEqual(len(versions), 2)
        self.assertIn(version1, versions)
        self.assertIn(version2, versions)
    
    # tests/test_prompt_management.py (continued from previous code)
    
    def test_get_specific_template_version(self):
        """Test retrieving a specific version of a template"""
        # Define a test template
        template_id = "version_test"
        original_text = "Original template for {text}"
        updated_text = "Updated template for {text}"
        
        # Save multiple versions
        version1 = self.prompt_manager.save_template(
            template_id=template_id,
            template_text=original_text,
            description="Original version"
        )
        
        version2 = self.prompt_manager.save_template(
            template_id=template_id,
            template_text=updated_text,
            description="Updated version"
        )
        
        # Retrieve specific versions
        template1 = self.prompt_manager.get_template(template_id, version_id=version1)
        template2 = self.prompt_manager.get_template(template_id, version_id=version2)
        
        # Verify the correct template texts are retrieved
        self.assertEqual(template1["template_text"], original_text)
        self.assertEqual(template2["template_text"], updated_text)
        
        # Verify retrieving latest version (without specifying version_id)
        latest_template = self.prompt_manager.get_template(template_id)
        self.assertEqual(latest_template["template_text"], updated_text)
        
        logger.info("Successfully retrieved specific template versions")
    
    def test_list_templates(self):
        """Test listing all available templates"""
        # Create several templates
        templates = {
            "template1": "Template 1 text for {text}",
            "template2": "Template 2 text for {text}",
            "template3": "Template 3 text for {text}"
        }
        
        # Save all templates
        for template_id, template_text in templates.items():
            self.prompt_manager.save_template(
                template_id=template_id,
                template_text=template_text,
                description=f"Description for {template_id}"
            )
        
        # List all templates
        template_list = self.prompt_manager.list_templates()
        
        # Verify all templates are listed
        self.assertEqual(len(template_list), len(templates))
        for template_id in templates.keys():
            self.assertIn(template_id, template_list)
        
        logger.info(f"Successfully listed {len(template_list)} templates")
    
    def test_template_with_metadata(self):
        """Test saving and retrieving a template with metadata"""
        # Define a test template with metadata
        template_id = "metadata_test"
        template_text = "Template with metadata for {text}"
        metadata = {
            "category": "medical",
            "priority": "high",
            "tags": ["patient", "demographics", "research"]
        }
        
        # Save the template with metadata
        version_id = self.prompt_manager.save_template(
            template_id=template_id,
            template_text=template_text,
            description="Template with metadata",
            metadata=metadata
        )
        
        # Retrieve the template
        template = self.prompt_manager.get_template(template_id)
        
        # Verify the metadata was saved correctly
        self.assertIsNotNone(template.get("metadata"))
        self.assertEqual(template["metadata"]["category"], metadata["category"])
        self.assertEqual(template["metadata"]["priority"], metadata["priority"])
        self.assertEqual(template["metadata"]["tags"], metadata["tags"])
        
        logger.info("Successfully saved and retrieved template with metadata")
    
    def test_get_template_text(self):
        """Test getting just the template text"""
        # Define a test template
        template_id = "text_test"
        template_text = "Just the template text for {text}"
        
        # Save the template
        self.prompt_manager.save_template(
            template_id=template_id,
            template_text=template_text
        )
        
        # Get just the template text
        retrieved_text = self.prompt_manager.get_template_text(template_id)
        
        # Verify the text matches
        self.assertEqual(retrieved_text, template_text)
        
        logger.info("Successfully retrieved template text directly")