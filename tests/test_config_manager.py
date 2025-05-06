# tests/test_config_manager.py
"""
Test module for configuration management
"""
import os
import sys
import logging
import unittest
from pathlib import Path
import tempfile
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to Python path
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

from src.utils.config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    """Test cases for the ConfigManager class"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for test configuration
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_dir = Path(self.temp_dir.name)
        
        # Create default.yaml in temporary directory
        with open(self.config_dir / "default.yaml", 'w') as f:
            yaml.dump({
                'app': {
                    'name': 'Research Data Extractor',
                    'version': '0.1.0',
                    'debug': False
                },
                'pdf_processor': {
                    'text_chunking': {
                        'chunk_size': 1000,
                        'overlap': 150
                    }
                },
                'env_var_test': '${TEST_ENV_VAR:default_value}'
            }, f)
        
        # Create development.yaml in temporary directory
        with open(self.config_dir / "development.yaml", 'w') as f:
            yaml.dump({
                'app': {
                    'debug': True
                },
                'pdf_processor': {
                    'text_chunking': {
                        'chunk_size': 800
                    }
                }
            }, f)
        
        # Create production.yaml in temporary directory
        with open(self.config_dir / "production.yaml", 'w') as f:
            yaml.dump({
                'app': {
                    'debug': False
                },
                'pdf_processor': {
                    'text_chunking': {
                        'chunk_size': 1200
                    }
                }
            }, f)
    
    def tearDown(self):
        """Clean up after tests"""
        self.temp_dir.cleanup()
    
    def test_default_config_loading(self):
        """Test loading default configuration"""
        config = ConfigManager(config_dir=self.config_dir)
        
        self.assertEqual(config.get('app.name'), 'Research Data Extractor')
        self.assertEqual(config.get('app.version'), '0.1.0')
        # In development mode by default
        self.assertTrue(config.get('app.debug'))
        self.assertEqual(config.get('pdf_processor.text_chunking.chunk_size'), 800)
    
    def test_environment_selection(self):
        """Test environment-specific configuration"""
        # Test development environment
        dev_config = ConfigManager(config_dir=self.config_dir, env="development")
        self.assertTrue(dev_config.get('app.debug'))
        self.assertEqual(dev_config.get('pdf_processor.text_chunking.chunk_size'), 800)
        
        # Test production environment
        prod_config = ConfigManager(config_dir=self.config_dir, env="production")
        self.assertFalse(prod_config.get('app.debug'))
        self.assertEqual(prod_config.get('pdf_processor.text_chunking.chunk_size'), 1200)
    
    def test_get_with_default(self):
        """Test getting values with defaults"""
        config = ConfigManager(config_dir=self.config_dir)
        
        # Existing value
        self.assertEqual(config.get('app.name'), 'Research Data Extractor')
        
        # Non-existing value with default
        self.assertEqual(config.get('app.non_existing', 'default'), 'default')
        
        # Non-existing value without default
        self.assertIsNone(config.get('app.non_existing'))
    
    def test_type_conversion(self):
        """Test type conversion methods"""
        config = ConfigManager(config_dir=self.config_dir)
        
        # Test int conversion
        config.set('test.int', '123')
        self.assertEqual(config.get_int('test.int'), 123)
        
        # Test float conversion
        config.set('test.float', '123.45')
        self.assertEqual(config.get_float('test.float'), 123.45)
        
        # Test bool conversion
        config.set('test.bool', 'True')
        self.assertEqual(config.get_bool('test.bool'), True)
        
        # Test list
        config.set('test.list', [1, 2, 3])
        self.assertEqual(config.get_list('test.list'), [1, 2, 3])
    
    def test_env_var_substitution(self):
        """Test environment variable substitution"""
        # Set test environment variable
        os.environ['TEST_ENV_VAR'] = 'test_value'
        
        config = ConfigManager(config_dir=self.config_dir)
        self.assertEqual(config.get('env_var_test'), 'test_value')
        
        # Unset the environment variable to test default value
        del os.environ['TEST_ENV_VAR']
        
        config = ConfigManager(config_dir=self.config_dir)
        self.assertEqual(config.get('env_var_test'), 'default_value')
    
    def test_validation(self):
        """Test configuration validation"""
        config = ConfigManager(config_dir=self.config_dir)
        
        # Define a schema
        schema = {
            'app': {
                'type': dict,
                'schema': {
                    'name': {'type': str, 'required': True},
                    'version': {'type': str},
                    'debug': {'type': bool}
                }
            },
            'pdf_processor': {
                'type': dict,
                'schema': {
                    'text_chunking': {
                        'type': dict,
                        'schema': {
                            'chunk_size': {'type': int},
                            'overlap': {'type': int}
                        }
                    }
                }
            }
        }
        
        # Valid configuration
        config.validate_schema(schema)
        
        # Invalid configuration - modify a value with wrong type
        config.set('app.debug', 'not a boolean')
        
        with self.assertRaises(ValueError):
            config.validate_schema(schema)
    
    def test_path_resolution(self):
        """Test path resolution"""
        config = ConfigManager(config_dir=self.config_dir)
        
        # Set a test path
        config.set('test.path', 'data/output')
        
        # Resolve path relative to project root
        path = config.get_path('test.path')
        expected_path = project_root / 'data' / 'output'
        self.assertEqual(path, expected_path)
        
        # Test create option
        created_path = config.get_path('test.path', create=True)
        self.assertTrue(created_path.exists())
        self.assertTrue(created_path.is_dir())
        
        # Clean up created directory
        import shutil
        shutil.rmtree(created_path, ignore_errors=True)
    
    def test_reload(self):
        """Test configuration reloading"""
        config = ConfigManager(config_dir=self.config_dir)
        
        # Initial value
        self.assertEqual(config.get('app.name'), 'Research Data Extractor')
        
        # Modify the configuration file
        with open(self.config_dir / "default.yaml", 'w') as f:
            yaml.dump({
                'app': {
                    'name': 'Updated App Name',
                    'version': '0.1.0',
                    'debug': False
                }
            }, f)
        
        # Reload configuration
        result = config.reload()
        self.assertTrue(result)
        
        # Check updated value
        self.assertEqual(config.get('app.name'), 'Updated App Name')

def run_basic_test():
    """Run a basic test of the configuration manager"""
    # Use the actual project configuration
    config = ConfigManager()
    
    # Print some configuration values
    print("App name:", config.get('app.name'))
    print("Debug mode:", config.get('app.debug'))
    print("Chunk size:", config.get('pdf_processor.text_chunking.chunk_size'))
    
    # Test path resolution
    output_dir = config.get_path('output.directory', create=True)
    print("Output directory:", output_dir)
    
    return True

if __name__ == "__main__":
    print("\n=== Running Unit Tests ===")
    unittest.main()
    
    print("\n=== Running Basic Test ===")
    run_basic_test()