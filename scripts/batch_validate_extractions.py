# scripts/batch_validate_extractions.py
"""
Script to validate and process multiple extraction files in batch
"""
import os
import sys
import argparse
import json
import logging
import csv
from pathlib import Path
from datetime import datetime

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from src.utils.data_validator import DataValidator
from src.data_export.csv_exporter import save_to_csv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_and_process_batch(input_dir, output_dir, csv_output=True, json_output=True):
    """
    Validate and process a batch of extraction files
    
    Args:
        input_dir (str): Directory containing extraction JSON files
        output_dir (str): Directory to save processed results
        csv_output (bool): Whether to output results as CSV
        json_output (bool): Whether to output results as JSON
        
    Returns:
        dict: Summary of batch processing
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all JSON files
    json_files = list(input_path.glob('*.json'))
    
    if not json_files:
        logger.warning(f"No JSON files found in: {input_path}")
        return {'files_processed': 0}
    
    logger.info(f"Found {len(json_files)} JSON files to process")
    
    # Initialize validator
    validator = DataValidator()
    
    # Process each file
    processed_files = []
    validation_stats = {
        'total': len(json_files),
        'valid': 0,
        'invalid': 0,
        'warnings': 0,
        'characteristics_found': 0
    }
    
    # Create summary CSV file
    summary_csv = output_path / "batch_summary.csv"
    with open(summary_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'File', 'Valid', 'Error Count', 'Warning Count', 
            'Characteristics Count', 'Process Date'
        ])
    
    # Collect all validated data for combined output
    all_validated_data = {}
    
    for file_path in json_files:
        logger.info(f"Processing: {file_path.name}")
        file_base_name = file_path.stem
        
        try:
            # Load the extraction data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Normalize field names
            normalized_data = validator.normalize_fields(data)
            
            # Validate the data
            validation_result = validator.validate(normalized_data)
            cleaned_data = validation_result['cleaned_data']
            
            # Update statistics
            if validation_result['valid']:
                validation_stats['valid'] += 1
            else:
                validation_stats['invalid'] += 1
            
            if validation_result['warnings']:
                validation_stats['warnings'] += len(validation_result['warnings'])
            
            validation_stats['characteristics_found'] += len(cleaned_data)
            
            # Save processed JSON if requested
            if json_output:
                output_json = output_path / f"{file_base_name}_validated.json"
                with open(output_json, 'w', encoding='utf-8') as f:
                    json.dump({
                        'original_file': file_path.name,
                        'validation': {
                            'valid': validation_result['valid'],
                            'errors': validation_result['errors'],
                            'warnings': validation_result['warnings']
                        },
                        'data': cleaned_data
                    }, f, indent=2)
            
            # Save processed CSV if requested
            if csv_output:
                output_csv = output_path / f"{file_base_name}_validated.csv"
                
                # Convert to rows
                rows = []
                for key, value in cleaned_data.items():
                    # Format value based on type
                    if isinstance(value, list):
                        formatted_value = "; ".join(str(item) for item in value)
                    elif isinstance(value, dict):
                        formatted_value = json.dumps(value)
                    else:
                        formatted_value = str(value)
                    
                    rows.append({'Characteristic': key, 'Value': formatted_value})
                
                # Write to CSV
                fieldnames = ['Characteristic', 'Value']
                with open(output_csv, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
            
            # Add to summary CSV
            with open(summary_csv, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    file_path.name,
                    validation_result['valid'],
                    len(validation_result['errors']),
                    len(validation_result['warnings']),
                    len(cleaned_data),
                    datetime.now().isoformat()
                ])
            
            # Add to processed files list
            processed_files.append({
                'file': file_path.name,
                'valid': validation_result['valid'],
                'error_count': len(validation_result['errors']),
                'warning_count': len(validation_result['warnings']),
                'characteristic_count': len(cleaned_data)
            })
            
            # Add to consolidated data
            all_validated_data[file_base_name] = cleaned_data
            
        except Exception as e:
            logger.error(f"Error processing file {file_path.name}: {str(e)}")
            validation_stats['invalid'] += 1
            
            # Add to summary CSV
            with open(summary_csv, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    file_path.name,
                    False,
                    1,  # Count the exception as an error
                    0,
                    0,
                    datetime.now().isoformat()
                ])
            
            # Add to processed files list
            processed_files.append({
                'file': file_path.name,
                'valid': False,
                'error_count': 1,
                'warning_count': 0,
                'characteristic_count': 0,
                'error': str(e)
            })
    
    # Save consolidated data if any files were processed
    if all_validated_data and json_output:
        consolidated_json = output_path / "all_extracted_data.json"
        with open(consolidated_json, 'w', encoding='utf-8') as f:
            json.dump(all_validated_data, f, indent=2)
        logger.info(f"Consolidated data saved to: {consolidated_json}")
    
    # Create batch summary
    summary = {
        'process_date': datetime.now().isoformat(),
        'input_directory': str(input_path),
        'output_directory': str(output_path),
        'statistics': validation_stats,
        'files': processed_files
    }
    
    # Save summary
    summary_json = output_path / "batch_summary.json"
    with open(summary_json, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"Batch processing complete: {validation_stats['valid']}/{validation_stats['total']} files valid")
    logger.info(f"Summary saved to: {summary_json}")
    
    return summary

def main():
    """Main function to run batch validation and processing"""
    parser = argparse.ArgumentParser(description='Batch validate and process extraction results')
    parser.add_argument('input_dir', help='Directory containing extraction JSON files')
    parser.add_argument('output_dir', help='Directory to save processed results')
    parser.add_argument('--no-csv', action='store_true', help='Skip CSV output')
    parser.add_argument('--no-json', action='store_true', help='Skip JSON output')
    
    args = parser.parse_args()
    
    validate_and_process_batch(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        csv_output=not args.no_csv,
        json_output=not args.no_json
    )

if __name__ == "__main__":
    main()