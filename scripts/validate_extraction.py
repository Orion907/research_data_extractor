# scripts/validate_extraction.py
"""
Script to validate extraction results from existing data
"""
import os
import sys
import argparse
import json
import logging
from pathlib import Path

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from src.utils.data_validator import DataValidator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_extraction_file(file_path, output_file=None, schema=None):
    """
    Validate extraction results from a JSON file
    
    Args:
        file_path (str): Path to the JSON file with extraction results
        output_file (str, optional): Path to save validation results
        schema (dict, optional): Custom validation schema
        
    Returns:
        dict: Validation results
    """
    logger.info(f"Validating extraction results from: {file_path}")
    
    try:
        # Load the extraction data
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Initialize validator with custom schema if provided
        validator = DataValidator(schema=schema)
        
        # Normalize field names
        normalized_data = validator.normalize_fields(data)
        
        # Validate the data
        validation_result = validator.validate(normalized_data)
        
        # Log validation results
        if validation_result['valid']:
            logger.info("Validation successful")
        else:
            logger.warning("Validation failed with errors")
            
        if validation_result['errors']:
            logger.warning("Validation errors:")
            for error in validation_result['errors']:
                logger.warning(f"  - {error}")
                
        if validation_result['warnings']:
            logger.info("Validation warnings:")
            for warning in validation_result['warnings']:
                logger.info(f"  - {warning}")
        
        # Save validation results if output file is specified
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'file': file_path,
                    'validation': validation_result
                }, f, indent=2)
                
            logger.info(f"Validation results saved to: {output_file}")
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Error validating file: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'valid': False,
            'errors': [f"Processing error: {str(e)}"],
            'warnings': [],
            'cleaned_data': {}
        }

def validate_extraction_directory(directory, output_dir=None, schema=None):
    """
    Validate all JSON files in a directory
    
    Args:
        directory (str): Directory containing JSON files
        output_dir (str, optional): Directory to save validation results
        schema (dict, optional): Custom validation schema
        
    Returns:
        dict: Summary of validation results
    """
    directory_path = Path(directory)
    logger.info(f"Validating all JSON files in: {directory_path}")
    
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all JSON files
    json_files = list(directory_path.glob('*.json'))
    
    if not json_files:
        logger.warning(f"No JSON files found in: {directory_path}")
        return {'files_processed': 0}
    
    # Process each file
    results = []
    valid_count = 0
    
    for file_path in json_files:
        logger.info(f"Processing: {file_path.name}")
        
        # Determine output file path if needed
        output_file = None
        if output_dir:
            output_file = output_path / f"validation_{file_path.stem}.json"
        
        # Validate the file
        result = validate_extraction_file(
            file_path=str(file_path),
            output_file=str(output_file) if output_file else None,
            schema=schema
        )
        
        # Track results
        results.append({
            'file': file_path.name,
            'valid': result['valid'],
            'error_count': len(result['errors']),
            'warning_count': len(result['warnings'])
        })
        
        if result['valid']:
            valid_count += 1
    
    # Compile summary
    summary = {
        'files_processed': len(json_files),
        'valid_files': valid_count,
        'invalid_files': len(json_files) - valid_count,
        'file_results': results
    }
    
    # Save summary if output directory is specified
    if output_dir:
        summary_path = output_path / "validation_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Validation summary saved to: {summary_path}")
    
    logger.info(f"Validation complete: {valid_count}/{len(json_files)} files valid")
    return summary

def load_custom_schema(schema_file):
    """
    Load a custom validation schema from a JSON file
    
    Args:
        schema_file (str): Path to the schema JSON file
        
    Returns:
        dict: The loaded schema
    """
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        logger.info(f"Loaded custom schema from: {schema_file}")
        return schema
    except Exception as e:
        logger.error(f"Error loading schema file: {str(e)}")
        return None

def main():
    """Main function to run validation"""
    parser = argparse.ArgumentParser(description='Validate patient data extraction results')
    
    # Command type
    subparsers = parser.add_subparsers(dest='command', help='Validation command')
    
    # Single file validation
    file_parser = subparsers.add_parser('file', help='Validate a single file')
    file_parser.add_argument('file', help='Path to the JSON file to validate')
    file_parser.add_argument('--output', help='Path to save validation results')
    file_parser.add_argument('--schema', help='Path to custom schema JSON file')
    
    # Directory validation
    dir_parser = subparsers.add_parser('dir', help='Validate all JSON files in a directory')
    dir_parser.add_argument('directory', help='Directory containing JSON files')
    dir_parser.add_argument('--output-dir', help='Directory to save validation results')
    dir_parser.add_argument('--schema', help='Path to custom schema JSON file')
    
    args = parser.parse_args()
    
    # Load custom schema if specified
    schema = None
    if hasattr(args, 'schema') and args.schema:
        schema = load_custom_schema(args.schema)
    
    # Process based on command
    if args.command == 'file':
        validate_extraction_file(
            file_path=args.file,
            output_file=args.output,
            schema=schema
        )
    elif args.command == 'dir':
        validate_extraction_directory(
            directory=args.directory,
            output_dir=args.output_dir,
            schema=schema
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()