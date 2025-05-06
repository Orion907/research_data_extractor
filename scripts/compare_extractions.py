# scripts/compare_extractions.py
"""
Script to compare extraction results between different versions
"""
import os
import sys
import argparse
import json
import logging
import csv
from pathlib import Path
import difflib

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from src.utils.data_validator import DataValidator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compare_extractions(file1, file2, output_file=None):
    """
    Compare two extraction result files
    
    Args:
        file1 (str): Path to first extraction file
        file2 (str): Path to second extraction file
        output_file (str, optional): Path to save comparison results
        
    Returns:
        dict: Comparison results
    """
    logger.info(f"Comparing extractions: {file1} vs {file2}")
    
    try:
        # Load the extraction data
        with open(file1, 'r', encoding='utf-8') as f:
            data1 = json.load(f)
        
        with open(file2, 'r', encoding='utf-8') as f:
            data2 = json.load(f)
        
        # Initialize validator for field normalization
        validator = DataValidator()
        
        # Normalize field names
        normalized1 = validator.normalize_fields(data1)
        normalized2 = validator.normalize_fields(data2)
        
        # Compare the fields
        all_fields = set(normalized1.keys()) | set(normalized2.keys())
        only_in_1 = set(normalized1.keys()) - set(normalized2.keys())
        only_in_2 = set(normalized2.keys()) - set(normalized1.keys())
        common_fields = set(normalized1.keys()) & set(normalized2.keys())
        
        # Check for differences in common fields
        different_fields = {}
        for field in common_fields:
            if normalized1[field] != normalized2[field]:
                different_fields[field] = {
                    'file1': normalized1[field],
                    'file2': normalized2[field]
                }
        
        # Compile comparison results
        comparison = {
            'files': {
                'file1': file1,
                'file2': file2
            },
            'fields': {
                'total_unique': len(all_fields),
                'common': len(common_fields),
                'only_in_file1': len(only_in_1),
                'only_in_file2': len(only_in_2),
                'different_values': len(different_fields)
            },
            'only_in_file1': list(only_in_1),
            'only_in_file2': list(only_in_2),
            'differences': different_fields
        }
        
        # Calculate similarity score (simple ratio)
        similarity = 1.0 - (
            (len(only_in_1) + len(only_in_2) + len(different_fields)) / 
            max(len(all_fields), 1)
        )
        comparison['similarity_score'] = similarity
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(comparison, f, indent=2)
            logger.info(f"Comparison saved to: {output_file}")
        
        # Log summary
        logger.info(f"Comparison summary:")
        logger.info(f"  Total unique fields: {comparison['fields']['total_unique']}")
        logger.info(f"  Common fields: {comparison['fields']['common']}")
        logger.info(f"  Only in file 1: {comparison['fields']['only_in_file1']}")
        logger.info(f"  Only in file 2: {comparison['fields']['only_in_file2']}")
        logger.info(f"  Fields with different values: {comparison['fields']['different_values']}")
        logger.info(f"  Similarity score: {comparison['similarity_score']:.2f}")
        
        return comparison
        
    except Exception as e:
        logger.error(f"Error comparing extraction files: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {
            'error': str(e),
            'similarity_score': 0
        }

def compare_directory_extractions(dir1, dir2, output_dir=None):
    """
    Compare extraction files between two directories
    
    Args:
        dir1 (str): Path to first directory
        dir2 (str): Path to second directory
        output_dir (str, optional): Directory to save comparison results
        
    Returns:
        dict: Summary of comparisons
    """
    dir1_path = Path(dir1)
    dir2_path = Path(dir2)
    
    logger.info(f"Comparing extractions between directories:")
    logger.info(f"  Directory 1: {dir1_path}")
    logger.info(f"  Directory 2: {dir2_path}")
    
    # Create output directory if specified
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all JSON files in both directories
    files1 = {f.name: f for f in dir1_path.glob('*.json')}
    files2 = {f.name: f for f in dir2_path.glob('*.json')}
    
    # Find common files
    common_files = set(files1.keys()) & set(files2.keys())
    only_in_dir1 = set(files1.keys()) - set(files2.keys())
    only_in_dir2 = set(files2.keys()) - set(files1.keys())
    
    logger.info(f"Found {len(common_files)} common files for comparison")
    logger.info(f"  Only in directory 1: {len(only_in_dir1)} files")
    logger.info(f"  Only in directory 2: {len(only_in_dir2)} files")
    
    # Compare common files
    comparisons = []
    total_similarity = 0.0
    
    # Create summary CSV file if output_dir is specified
    if output_dir:
        summary_csv = output_path / "comparison_summary.csv"
        with open(summary_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'File', 'Total Fields', 'Common Fields', 'Only in Dir1', 
                'Only in Dir2', 'Different Values', 'Similarity Score'
            ])
    
    for filename in common_files:
        logger.info(f"Comparing: {filename}")
        
        # Determine output file path if needed
        output_file = None
        if output_dir:
            output_file = output_path / f"comparison_{filename}"
        
        # Compare the files
        comparison = compare_extractions(
            file1=str(files1[filename]),
            file2=str(files2[filename]),
            output_file=str(output_file) if output_file else None
        )
        
        # Add to comparisons list
        comparisons.append({
            'file': filename,
            'similarity': comparison['similarity_score'],
            'fields': comparison.get('fields', {})
        })
        
        # Update total similarity
        total_similarity += comparison['similarity_score']
        
        # Add to summary CSV if output_dir is specified
        if output_dir and 'fields' in comparison:
            with open(summary_csv, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    filename,
                    comparison['fields']['total_unique'],
                    comparison['fields']['common'],
                    comparison['fields']['only_in_file1'],
                    comparison['fields']['only_in_file2'],
                    comparison['fields']['different_values'],
                    f"{comparison['similarity_score']:.2f}"
                ])
    
    # Calculate average similarity
    avg_similarity = total_similarity / max(len(common_files), 1)
    
    # Compile summary
    summary = {
        'directories': {
            'dir1': str(dir1_path),
            'dir2': str(dir2_path)
        },
        'files': {
            'total_unique': len(set(files1.keys()) | set(files2.keys())),
            'common': len(common_files),
            'only_in_dir1': len(only_in_dir1),
            'only_in_dir2': len(only_in_dir2)
        },
        'only_in_dir1': list(only_in_dir1),
        'only_in_dir2': list(only_in_dir2),
        'comparisons': comparisons,
        'average_similarity': avg_similarity
    }
    
    # Save summary if output directory is specified
    if output_dir:
        summary_json = output_path / "comparison_summary.json"
        with open(summary_json, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Comparison summary saved to: {summary_json}")
    
    logger.info(f"Directory comparison complete")
    logger.info(f"  Average similarity score: {avg_similarity:.2f}")
    
    return summary

def main():
    """Main function to compare extraction files"""
    parser = argparse.ArgumentParser(description='Compare extraction results')
    
    # Command type
    subparsers = parser.add_subparsers(dest='command', help='Comparison command')
    
    # Single file comparison
    file_parser = subparsers.add_parser('files', help='Compare two files')
    file_parser.add_argument('file1', help='Path to first extraction file')
    file_parser.add_argument('file2', help='Path to second extraction file')
    file_parser.add_argument('--output', help='Path to save comparison results')
    
    # Directory comparison
    dir_parser = subparsers.add_parser('dirs', help='Compare files in two directories')
    dir_parser.add_argument('dir1', help='Path to first directory')
    dir_parser.add_argument('dir2', help='Path to second directory')
    dir_parser.add_argument('--output-dir', help='Directory to save comparison results')
    
    args = parser.parse_args()
    
    # Process based on command
    if args.command == 'files':
        compare_extractions(
            file1=args.file1,
            file2=args.file2,
            output_file=args.output
        )
    elif args.command == 'dirs':
        compare_directory_extractions(
            dir1=args.dir1,
            dir2=args.dir2,
            output_dir=args.output_dir
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()