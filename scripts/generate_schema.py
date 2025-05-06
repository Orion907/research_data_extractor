# scripts/generate_schema.py
"""
Script to generate validation schemas for specific study types
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

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define schemas for different study types
SCHEMAS = {
    'generic': {
        'sample_size': {'type': 'integer', 'required': True},
        'mean_age': {'type': 'numeric', 'required': False},
        'age_range': {'type': 'string', 'required': False},
        'male_percentage': {'type': 'percentage', 'required': False},
        'female_percentage': {'type': 'percentage', 'required': False},
        'inclusion_criteria': {'type': 'list', 'required': False},
        'exclusion_criteria': {'type': 'list', 'required': False},
    },
    
    'diabetes': {
        'sample_size': {'type': 'integer', 'required': True},
        'mean_age': {'type': 'numeric', 'required': False},
        'age_range': {'type': 'string', 'required': False},
        'male_percentage': {'type': 'percentage', 'required': False},
        'female_percentage': {'type': 'percentage', 'required': False},
        'diabetes_type': {'type': 'string', 'required': True},
        'mean_hba1c': {'type': 'numeric', 'required': False},
        'mean_bmi': {'type': 'numeric', 'required': False},
        'diabetes_duration': {'type': 'string', 'required': False},
        'medications': {'type': 'list', 'required': False},
        'complications': {'type': 'list', 'required': False},
        'inclusion_criteria': {'type': 'list', 'required': False},
        'exclusion_criteria': {'type': 'list', 'required': False},
    },
    
    'heart_failure': {
        'sample_size': {'type': 'integer', 'required': True},
        'mean_age': {'type': 'numeric', 'required': False},
        'age_range': {'type': 'string', 'required': False},
        'male_percentage': {'type': 'percentage', 'required': False},
        'female_percentage': {'type': 'percentage', 'required': False},
        'nyha_class': {'type': 'string', 'required': False},
        'ejection_fraction': {'type': 'numeric', 'required': False},
        'ischemic_etiology': {'type': 'percentage', 'required': False},
        'comorbidities': {'type': 'list', 'required': False},
        'medications': {'type': 'list', 'required': False},
        'inclusion_criteria': {'type': 'list', 'required': False},
        'exclusion_criteria': {'type': 'list', 'required': False},
    },
    
    'oncology': {
        'sample_size': {'type': 'integer', 'required': True},
        'mean_age': {'type': 'numeric', 'required': False},
        'age_range': {'type': 'string', 'required': False},
        'male_percentage': {'type': 'percentage', 'required': False},
        'female_percentage': {'type': 'percentage', 'required': False},
        'cancer_type': {'type': 'string', 'required': True},
        'cancer_stage': {'type': 'string', 'required': False},
        'ecog_status': {'type': 'string', 'required': False},
        'prior_treatments': {'type': 'list', 'required': False},
        'metastatic_sites': {'type': 'list', 'required': False},
        'biomarkers': {'type': 'list', 'required': False},
        'inclusion_criteria': {'type': 'list', 'required': False},
        'exclusion_criteria': {'type': 'list', 'required': False},
    }
}

def generate_schema(schema_type, output_file=None, include_all=False):
    """
    Generate a validation schema for a specific study type
    
    Args:
        schema_type (str): Type of schema to generate
        output_file (str, optional): Path to save the schema
        include_all (bool): Whether to include all schema types in output
        
    Returns:
        dict: The generated schema
    """
    if schema_type not in SCHEMAS and not include_all:
        logger.error(f"Unknown schema type: {schema_type}")
        logger.info(f"Available types: {', '.join(SCHEMAS.keys())}")
        return None
    
    # Generate the schema
    if include_all:
        # Combine all schemas into one
        combined_schema = {}
        for schema_name, schema in SCHEMAS.items():
            for field, config in schema.items():
                if field not in combined_schema:
                    combined_schema[field] = config
        schema_data = combined_schema
        schema_name = "combined"
    else:
        schema_data = SCHEMAS[schema_type]
        schema_name = schema_type
    
    # Add metadata
    output_schema = {
        'name': schema_name,
        'description': f"Validation schema for {schema_name} studies",
        'version': '1.0',
        'fields': schema_data
    }
    
    # Save to file if specified
    if output_file:
        try:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_schema, f, indent=2)
                
            logger.info(f"Schema saved to: {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving schema: {str(e)}")
    
    return output_schema

def list_available_schemas():
    """List all available schema types"""
    logger.info("Available schema types:")
    for schema_type in SCHEMAS.keys():
        logger.info(f"  - {schema_type}")
    
    logger.info("Use 'all' to generate a combined schema with all fields")

def main():
    """Main function to generate schemas"""
    parser = argparse.ArgumentParser(description='Generate validation schemas for specific study types')
    
    # Command type
    subparsers = parser.add_subparsers(dest='command', help='Schema command')
    
    # Generate schema
    gen_parser = subparsers.add_parser('generate', help='Generate a schema')
    gen_parser.add_argument('type', help='Type of schema to generate')
    gen_parser.add_argument('--output', help='Path to save the schema')
    gen_parser.add_argument('--all', action='store_true', help='Include all schema types')
    
    # List available schemas
    list_parser = subparsers.add_parser('list', help='List available schema types')
    
    args = parser.parse_args()
    
    if args.command == 'generate':
        if args.type == 'all':
            generate_schema('generic', args.output, include_all=True)
        else:
            generate_schema(args.type, args.output)
    elif args.command == 'list':
        list_available_schemas()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()