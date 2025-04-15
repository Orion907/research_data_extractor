"""
Module for exporting data to CSV format
"""
import csv
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

def save_to_csv(data, output_path):
    """
    Save data to a CSV file
    
    Args:
        data (list): List of dictionaries with data to save
        output_path (str): Path to save the CSV file
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
        
        # Write data to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"Successfully wrote {len(data)} rows to {output_path}")
    
    except Exception as e:
        logger.error(f"Error saving data to CSV: {str(e)}")
        raise