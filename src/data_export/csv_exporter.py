# src/data_export/csv_exporter.py
"""
Module for exporting data to CSV format
"""
import csv
import os
import logging
import json

# Configure logging
logger = logging.getLogger(__name__)

def save_to_csv(data, output_path, flatten_nested=True):
    """
    Save data to a CSV file with improved handling of nested structures
    
    Args:
        data (list): List of dictionaries with data to save
        output_path (str): Path to save the CSV file
        flatten_nested (bool): Whether to flatten nested dictionaries and lists
    """
    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # If data is empty, create an empty file with headers
        if not data:
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['No data available'])
            logger.warning(f"No data to write to {output_path}")
            return
        
        # Get field names from the first dictionary
        fieldnames = list(data[0].keys())
        
        # Process data for CSV
        processed_data = []
        for item in data:
            row = {}
            for key, value in item.items():
                if flatten_nested and isinstance(value, (dict, list)):
                    # Convert nested structures to JSON strings
                    row[key] = json.dumps(value)
                else:
                    row[key] = value
            processed_data.append(row)
        
        # Write data to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(processed_data)
        
        logger.info(f"Successfully wrote {len(processed_data)} rows to {output_path}")
    
    except Exception as e:
        logger.error(f"Error saving data to CSV: {str(e)}")
        raise

def save_patient_data_to_csv(patient_data, output_path):
    """
    Save patient characteristic data to CSV in a more readable format
    
    Args:
        patient_data (dict): Dictionary of patient characteristics
        output_path (str): Path to save the CSV file
    """
    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert to rows for CSV
        rows = []
        
        # Extract metadata if present
        metadata = patient_data.pop('_metadata', {})
        
        # Process each characteristic
        for key, value in patient_data.items():
            # Format value based on type
            formatted_value = format_value_for_csv(value)
            rows.append({'Characteristic': key, 'Value': formatted_value})
        
        # Add metadata at the end, prefixed
        for key, value in metadata.items():
            formatted_value = format_value_for_csv(value)
            rows.append({'Characteristic': f'_meta_{key}', 'Value': formatted_value})
        
        # Write to CSV
        fieldnames = ['Characteristic', 'Value']
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        
        logger.info(f"Successfully saved patient data to {output_path}")
        
    except Exception as e:
        logger.error(f"Error saving patient data to CSV: {str(e)}")
        raise

def format_value_for_csv(value):
    """
    Format a value for CSV output
    
    Args:
        value: The value to format
        
    Returns:
        str: Formatted value
    """
    if isinstance(value, list):
        # Format lists as semicolon-separated values
        return "; ".join(str(item) for item in value)
    elif isinstance(value, dict):
        # Format dictionaries as JSON strings
        return json.dumps(value)
    else:
        # Return other values as strings
        return str(value)