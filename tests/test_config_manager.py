# tests/test_config_manager.py
"""
Test module for configuration management
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.utils.config_manager import ConfigManager

def test_config_loading():
    """Test loading configuration from YAML files"""
    
    # Test with default environment
    logger.info("Testing with default environment...")
    config = ConfigManager()
    
    # Verify some configuration values
    app_name = config.get('app.name')
    logger.info(f"app.name: {app_name}")
    
    chunk_size = config.get('pdf_processor.text_chunking.chunk_size')
    logger.info(f"pdf_processor.text_chunking.chunk_size: {chunk_size}")
    
    # Test with specified environment
    logger.info("\nTesting with production environment...")
    prod_config = ConfigManager(env="production")
    
    # Verify some configuration values that should be different in production
    debug_mode = prod_config.get('app.debug')
    logger.info(f"production app.debug: {debug_mode}")
    
    # Test path resolution
    logger.info("\nTesting path resolution...")
    output_dir = config.get_path('output.directory', create=True)
    logger.info(f"Resolved output directory: {output_dir}")
    logger.info(f"Output directory exists: {output_dir.exists()}")
    
    return True

if __name__ == "__main__":
    test_config_loading()
    logger.info("Configuration test completed successfully!")