# tests/test_project_structure.py
import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_project_structure():
    """Verify that all expected files exist in the project structure."""
    
    # Define the expected directory structure with key files
    # Format: directories are dictionaries, files are strings in lists
    expected_structure = {
        'src': {
            'pdf_processor': ['pdf_processor.py', 'text_chunker.py', '__init__.py'],
            'llm': ['api_client.py', 'anthropic_client.py', 'openai_client.py', 'client_factory.py', 'mock_client.py', '__init__.py'],
            'data_export': ['csv_exporter.py', '__init__.py'],
            'utils': ['data_extractor.py', 'prompt_templates.py', 'prompt_manager.py', 'analytics.py', 'config_manager.py', 'unified_analytics.py', '__init__.py'],
            '__pycache__': []  # Allow this directory but don't check contents
        },
        'tests': ['test_pdf_processor.py', 'test_text_chunker.py', 'test_data_extractor.py', 'test_mock_client.py', '__init__.py'],
        'data': {
            'input': [],
            'output': {
                'chunks': []
            }
        },
        'config': ['default.yaml', 'development.yaml', 'production.yaml'],
        'prompts': [],
        'analytics': [],
        'root_files': ['.env', '.gitignore', 'main.py', 'README.md', 'requirements.txt', 'setup.py', 'streamlit_app.py']
    }
    
    missing_files = []
    
    def check_structure(base_path, structure, is_root=False):
        for key, value in structure.items():
            path = key if is_root else os.path.join(base_path, key)
            
            if key == 'root_files' and is_root:
                # Handle root files specially
                for file in value:
                    file_path = os.path.join(base_path, file)
                    if not os.path.exists(file_path):
                        missing_files.append(file_path)
                        logger.warning(f"Missing file: {file_path}")
            elif isinstance(value, list):
                # Key is a directory with a list of files
                if not os.path.exists(path) and value:  # Only care if directory should have files
                    os.makedirs(path, exist_ok=True)
                    logger.info(f"Created directory: {path}")
                
                # Check each file in the directory
                for file in value:
                    file_path = os.path.join(path, file)
                    if not os.path.exists(file_path):
                        missing_files.append(file_path)
                        logger.warning(f"Missing file: {file_path}")
            elif isinstance(value, dict):
                # Key is a directory with subdirectories
                if not os.path.exists(path):
                    os.makedirs(path, exist_ok=True)
                    logger.info(f"Created directory: {path}")
                
                # Recursively check subdirectories
                check_structure(path, value)
    
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Check the structure
    check_structure(project_root, expected_structure, is_root=True)
    
    if missing_files:
        logger.warning(f"Found {len(missing_files)} missing files in the project structure")
        return False
    else:
        logger.info("All expected files exist in the project structure")
        return True

if __name__ == "__main__":
    verify_project_structure()