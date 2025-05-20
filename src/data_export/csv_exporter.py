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
    
# Add to src/data_export/csv_exporter.py (around line 70-80)

def flatten_json_for_csv(json_data, prefix=''):
    """
    Flatten a nested JSON structure for CSV export
    
    Args:
        json_data (dict or list): JSON data to flatten
        prefix (str): Prefix for nested keys
        
    Returns:
        dict: Flattened dictionary
    """
    flattened = {}
    
    if isinstance(json_data, dict):
        # Process dictionary items
        for key, value in json_data.items():
            new_key = f"{prefix}_{key}" if prefix else key
            
            if isinstance(value, (dict, list)):
                # Recursively flatten nested structures
                nested_flat = flatten_json_for_csv(value, new_key)
                flattened.update(nested_flat)
            else:
                # Add simple key-value pair
                flattened[new_key] = value
                
    elif isinstance(json_data, list):
        # Convert list to dictionary with indexed keys
        for i, item in enumerate(json_data):
            if isinstance(item, (dict, list)):
                # Recursively flatten nested structures
                nested_flat = flatten_json_for_csv(item, f"{prefix}_{i}")
                flattened.update(nested_flat)
            else:
                # Add list item with index
                flattened[f"{prefix}_{i}"] = item
    else:
        # Handle base case (shouldn't reach here normally)
        flattened[prefix] = json_data
        
    return flattened

# src/data_export/csv_exporter.py - modify the save_extraction_results_to_csv function
def save_extraction_results_to_csv(chunk_results, output_path, include_chunks=True):
    """
    Save extraction results to a CSV file with intelligent merging of related information
    
    Args:
        chunk_results (list): List of extraction results by chunk
        output_path (str): Path to save the CSV file
        include_chunks (bool): Whether to include individual chunk data
    """
    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if not chunk_results:
            # Create an empty file if no results
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['No data available'])
            logger.warning(f"No extraction results to write to {output_path}")
            return
        
        # Process each chunk result
        flattened_results = []
        all_keys = set()
        
        for chunk in chunk_results:
            chunk_index = chunk.get('chunk_index', 0)
            extraction_text = chunk.get('extraction', '')
            
            # Try to parse the extraction as JSON
            try:
                # Find JSON in text if necessary
                if '{' in extraction_text and '}' in extraction_text:
                    json_start = extraction_text.find('{')
                    json_end = extraction_text.rfind('}') + 1
                    json_text = extraction_text[json_start:json_end]
                    extraction_data = json.loads(json_text)
                else:
                    # If not JSON-like, use the raw text
                    extraction_data = {"raw_text": extraction_text}
                
                # Flatten the JSON structure
                flattened = flatten_json_for_csv(extraction_data)
                
                # Add chunk index
                flattened['chunk_index'] = chunk_index
                
                # Track all keys for header
                all_keys.update(flattened.keys())
                
                # Add to results
                flattened_results.append(flattened)
                
            except Exception as e:
                logger.error(f"Error processing extraction for chunk {chunk_index}: {str(e)}")
                # Add basic data in case of error
                flattened_results.append({
                    'chunk_index': chunk_index,
                    'error': f"Failed to process: {str(e)}",
                    'raw_text': extraction_text
                })
                all_keys.update(['chunk_index', 'error', 'raw_text'])
        
        # Create a merged row that combines all non-empty values from each chunk
        all_keys_sorted = sorted(list(all_keys))
        merged_row = {'chunk_index': 'combined'}
        
        # Go through each key and find the best value to use
        for key in all_keys_sorted:
            if key == 'chunk_index':
                continue  # Skip chunk_index in merging
                
            # Collect all non-empty values for this key
            values = [row.get(key, "") for row in flattened_results if row.get(key, "")]
            
            if not values:
                merged_row[key] = ""
            elif len(values) == 1:
                # Only one value, use it
                merged_row[key] = values[0]
            else:
                # Multiple values - combine them if they're different
                unique_values = []
                for val in values:
                    if val not in unique_values:
                        unique_values.append(val)
                
                if len(unique_values) == 1:
                    # All values are the same
                    merged_row[key] = unique_values[0]
                else:
                    # Combine different values
                    merged_row[key] = " | ".join(unique_values)
        
        # Write all results to CSV, with the merged row first
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_keys_sorted)
            writer.writeheader()
            writer.writerow(merged_row)  # Write the merged row first
            
            # Then write individual chunk rows if requested
            if include_chunks:
                for row in flattened_results:
                    # Ensure all rows have all columns
                    for key in all_keys_sorted:
                        if key not in row:
                            row[key] = ""
                    writer.writerow(row)
        
        logger.info(f"Successfully wrote extraction results to {output_path} {'with' if include_chunks else 'without'} individual chunks")
        
    except Exception as e:
        logger.error(f"Error saving extraction results to CSV: {str(e)}")
        raise