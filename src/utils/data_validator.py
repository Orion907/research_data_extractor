# src/utils/data_validator.py
"""
Module for validating extracted patient characteristic data
"""
import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Union, Optional

# Configure logging
logger = logging.getLogger(__name__)

class DataValidator:
    """
    Validates extracted patient characteristic data
    """
    
    # Common patient characteristic fields with expected types and formats
    COMMON_FIELDS = {
        'sample_size': {'type': 'integer', 'required': True},
        'age': {'type': 'string', 'required': False},
        'age_range': {'type': 'string', 'required': False},
        'mean_age': {'type': 'numeric', 'required': False},
        'median_age': {'type': 'numeric', 'required': False},
        'gender_distribution': {'type': 'string', 'required': False},
        'male_percentage': {'type': 'percentage', 'required': False},
        'female_percentage': {'type': 'percentage', 'required': False},
        'ethnicity': {'type': 'string', 'required': False},
        'inclusion_criteria': {'type': 'list', 'required': False},
        'exclusion_criteria': {'type': 'list', 'required': False},
        'comorbidities': {'type': 'list', 'required': False},
        'medications': {'type': 'list', 'required': False},
        'bmi': {'type': 'numeric', 'required': False},
        'follow_up_period': {'type': 'string', 'required': False},
    }
    
    # Patterns for common formats
    PATTERNS = {
        'percentage': r'^(\d{1,3}(\.\d+)?)\s*%$',
        'age_range': r'^(\d+)\s*-\s*(\d+)\s*(years|yrs)?$',
        'numeric_with_unit': r'^(\d+(\.\d+)?)\s*([a-zA-Z]+)$',
    }
    
    def __init__(self, schema: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        Initialize the validator with an optional custom schema
        
        Args:
            schema (dict, optional): Custom schema for validation
        """
        self.schema = schema or self.COMMON_FIELDS
        logger.info("Initialized DataValidator")
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate extracted data against the schema
        
        Args:
            data (dict): Extracted patient characteristic data
            
        Returns:
            dict: Validation result with cleaned data and any validation issues
        """
        if not data:
            return {'valid': False, 'errors': ['No data provided'], 'cleaned_data': {}}
        
        errors = []
        warnings = []
        cleaned_data = {}
        
        # Check for required fields
        for field, field_schema in self.schema.items():
            if field_schema.get('required', False) and field not in data:
                errors.append(f"Required field '{field}' is missing")
        
        # Validate each field in the data
        for field, value in data.items():
            if field in self.schema:
                field_type = self.schema[field]['type']
                validation_result = self._validate_field(field, value, field_type)
                
                if validation_result['valid']:
                    cleaned_data[field] = validation_result['cleaned_value']
                    if 'warning' in validation_result:
                        warnings.append(f"{field}: {validation_result['warning']}")
                else:
                    errors.append(f"{field}: {validation_result['error']}")
            else:
                # Field not in schema, but we'll keep it with a warning
                cleaned_data[field] = value
                warnings.append(f"Unexpected field '{field}' not in schema")
        
        # Check for logical consistencies
        consistency_issues = self._check_consistencies(cleaned_data)
        if consistency_issues:
            warnings.extend(consistency_issues)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'cleaned_data': cleaned_data
        }
    
    def _validate_field(self, field: str, value: Any, expected_type: str) -> Dict[str, Any]:
        """
        Validate a single field
        
        Args:
            field (str): Field name
            value (any): Field value
            expected_type (str): Expected type from schema
            
        Returns:
            dict: Validation result
        """
        if value is None or value == '':
            return {'valid': True, 'cleaned_value': None}
        
        result = {'valid': False, 'error': f"Invalid {expected_type} format"}
        
        try:
            if expected_type == 'integer':
                # Handle integer type
                if isinstance(value, int):
                    result = {'valid': True, 'cleaned_value': value}
                elif isinstance(value, str):
                    # Extract numbers from strings like "50 patients"
                    matches = re.search(r'(\d+)', value)
                    if matches:
                        result = {'valid': True, 'cleaned_value': int(matches.group(1))}
                        if value != matches.group(1):
                            result['warning'] = f"Extracted '{matches.group(1)}' from '{value}'"
            
            elif expected_type == 'numeric':
                # Handle numeric type (float or integer)
                if isinstance(value, (int, float)):
                    result = {'valid': True, 'cleaned_value': value}
                elif isinstance(value, str):
                    # Extract numbers from strings like "58.3 years"
                    matches = re.search(r'(\d+(\.\d+)?)', value)
                    if matches:
                        result = {'valid': True, 'cleaned_value': float(matches.group(1))}
                        if value != matches.group(1):
                            result['warning'] = f"Extracted '{matches.group(1)}' from '{value}'"
            
            elif expected_type == 'percentage':
                # Handle percentage type
                if isinstance(value, (int, float)):
                    # Assume it's already a percentage value
                    if 0 <= value <= 100:
                        result = {'valid': True, 'cleaned_value': value}
                    else:
                        result['error'] = f"Percentage value {value} out of range (0-100)"
                elif isinstance(value, str):
                    # Parse percentage strings like "60%" or "60 percent"
                    matches = re.search(r'(\d+(\.\d+)?)\s*(%|percent)', value.lower())
                    if matches:
                        percent_value = float(matches.group(1))
                        if 0 <= percent_value <= 100:
                            result = {'valid': True, 'cleaned_value': percent_value}
                            if value != f"{percent_value}%":
                                result['warning'] = f"Normalized '{value}' to '{percent_value}%'"
                        else:
                            result['error'] = f"Percentage value {percent_value} out of range (0-100)"
            
            elif expected_type == 'string':
                # Handle string type
                if isinstance(value, str):
                    result = {'valid': True, 'cleaned_value': value.strip()}
                else:
                    result = {'valid': True, 'cleaned_value': str(value).strip(), 
                              'warning': f"Converted {type(value).__name__} to string"}
            
            elif expected_type == 'list':
                # Handle list type
                if isinstance(value, list):
                    result = {'valid': True, 'cleaned_value': value}
                elif isinstance(value, str):
                    # Try to parse as a list if it looks like one
                    if value.startswith('[') and value.endswith(']'):
                        try:
                            parsed_list = json.loads(value)
                            if isinstance(parsed_list, list):
                                result = {'valid': True, 'cleaned_value': parsed_list}
                            else:
                                result['error'] = "Value parses as JSON but not as list"
                        except json.JSONDecodeError:
                            pass
                    
                    # If it's a newline or comma-separated string, split it
                    if not result['valid'] and ('\n' in value or ',' in value):
                        if '\n' in value:
                            items = [item.strip() for item in value.split('\n') if item.strip()]
                        else:
                            items = [item.strip() for item in value.split(',') if item.strip()]
                        
                        if items:
                            result = {'valid': True, 'cleaned_value': items, 
                                      'warning': f"Converted string to list with {len(items)} items"}
            
        except Exception as e:
            result['error'] = f"Validation error: {str(e)}"
        
        return result
    
    def _check_consistencies(self, data: Dict[str, Any]) -> List[str]:
        """
        Check for logical consistencies between fields
        
        Args:
            data (dict): Cleaned data to check
            
        Returns:
            list: List of consistency issues found
        """
        issues = []
        
        # Check gender percentage adds up to 100%
        male_pct = data.get('male_percentage')
        female_pct = data.get('female_percentage')
        
        if male_pct is not None and female_pct is not None:
            total = male_pct + female_pct
            if abs(total - 100) > 0.1:  # Allow small rounding errors
                issues.append(f"Gender percentages add up to {total}%, not 100%")
        
        # Check age range consistency
        age_range = data.get('age_range')
        mean_age = data.get('mean_age')
        
        if age_range and mean_age:
            try:
                # Extract min and max age from range
                matches = re.search(r'(\d+)\s*-\s*(\d+)', age_range)
                if matches:
                    min_age = int(matches.group(1))
                    max_age = int(matches.group(2))
                    
                    # Check if mean age is within range
                    if not (min_age <= mean_age <= max_age):
                        issues.append(f"Mean age ({mean_age}) outside of age range ({min_age}-{max_age})")
            except Exception:
                pass
        
        # Add more consistency checks as needed
        
        return issues
    
    @staticmethod
    def normalize_fields(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize field names to a standard format
        
        Args:
            data (dict): Data to normalize
            
        Returns:
            dict: Data with normalized field names
        """
        # Common field name variations to normalize
        field_mapping = {
            'n': 'sample_size',
            'number_of_patients': 'sample_size',
            'patient_count': 'sample_size',
            'subject_count': 'sample_size',
            'total_patients': 'sample_size',
            'number_of_subjects': 'sample_size',
            
            'age_mean': 'mean_age',
            'average_age': 'mean_age',
            
            'gender': 'gender_distribution',
            'sex_distribution': 'gender_distribution',
            'sex': 'gender_distribution',
            
            'male': 'male_percentage',
            'males': 'male_percentage',
            'percent_male': 'male_percentage',
            
            'female': 'female_percentage',
            'females': 'female_percentage',
            'percent_female': 'female_percentage',
            
            # Add more mappings as needed
        }
        
        normalized = {}
        
        for key, value in data.items():
            # Convert to lowercase and remove spaces for matching
            lookup_key = key.lower().replace(' ', '_')
            
            if lookup_key in field_mapping:
                normalized_key = field_mapping[lookup_key]
            else:
                normalized_key = key
            
            normalized[normalized_key] = value
        
        return normalized