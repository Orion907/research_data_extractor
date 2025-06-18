# src/utils/annotation_utils.py
"""
Utility functions for manual annotation and comparison of extraction results
"""
import streamlit as st
import json
import pandas as pd
import os
import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

def load_extraction_results(file_path):
    """
    Load extraction results from a file
    
    Args:
        file_path (str): Path to the file (JSON or CSV)
        
    Returns:
        dict or DataFrame: Loaded extraction data
    """
    try:
        if file_path.endswith('.json'):
            with open(file_path, 'r') as f:
                data = json.load(f)
            return data
        elif file_path.endswith('.csv'):
            return pd.read_csv(file_path).to_dict('records')
        else:
            logger.error(f"Unsupported file type: {file_path}")
            return None
    except Exception as e:
        logger.error(f"Error loading extraction results: {str(e)}")
        return None

def display_annotation_interface(extraction_data, is_structured=True):
    """
    Display an interface for manual annotation of extraction results
    
    Args:
        extraction_data (dict or list): The extraction data to annotate
        is_structured (bool): Whether the data is structured (dict of dicts)
        
    Returns:
        dict or list: The annotated data
    """
    annotated_data = extraction_data.copy() if isinstance(extraction_data, dict) else extraction_data.copy()
    
    st.subheader("Manual Annotation")
    st.markdown("Review and edit the extracted data below:")
    
    if is_structured:
        # Structured data format (dict of dicts)
        for key, item in extraction_data.items():
            if isinstance(item, dict) and 'value' in item:
                st.text(f"Characteristic: {key}")
                
                # Sources info if available
                if 'sources' in item:
                    st.text(f"Source chunks: {', '.join(map(str, item['sources']))}")
                
                # Editable value field
                new_value = st.text_area(f"Value for {key}", item['value'])
                
                # Update the value
                annotated_data[key]['value'] = new_value
                
                # Option to delete this entry
                if st.checkbox(f"Delete {key}", False):
                    del annotated_data[key]
                
                st.markdown("---")
        
        # Option to add new fields
        with st.expander("Add New Field"):
            new_key = st.text_input("New Characteristic Name")
            new_value = st.text_area("New Value")
            
            if st.button("Add Field"):
                if new_key and new_key not in annotated_data:
                    annotated_data[new_key] = {
                        'value': new_value,
                        'sources': ['manual'],
                        'added_manually': True
                    }
                    st.success(f"Added field: {new_key}")
                elif new_key in annotated_data:
                    st.error(f"Field already exists: {new_key}")
                else:
                    st.error("Please enter a field name")
    else:
        # Simple list of records
        for i, item in enumerate(extraction_data):
            st.subheader(f"Item {i+1}")
            
            # Create a form for each item
            edited_item = {}
            
            for key, value in item.items():
                edited_item[key] = st.text_area(f"{key}", value)
            
            # Update the annotated data
            annotated_data[i] = edited_item
            
            st.markdown("---")
    
    return annotated_data

def save_annotations(annotated_data, output_path):
    """
    Save annotated data to a file
    
    Args:
        annotated_data (dict or list): The annotated data
        output_path (str): Path to save the file
        
    Returns:
        bool: Whether the save was successful
    """
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        if output_path.endswith('.json'):
            with open(output_path, 'w') as f:
                json.dump(annotated_data, f, indent=2)
        elif output_path.endswith('.csv'):
            # Convert to DataFrame first
            if isinstance(annotated_data, dict):
                # Flatten structured data
                flattened = []
                for key, item in annotated_data.items():
                    if isinstance(item, dict) and 'value' in item:
                        flattened.append({
                            'Characteristic': key,
                            'Value': item['value'],
                            'Sources': ', '.join(map(str, item.get('sources', [])))
                        })
                    else:
                        flattened.append({
                            'Characteristic': key,
                            'Value': str(item)
                        })
                df = pd.DataFrame(flattened)
            else:
                df = pd.DataFrame(annotated_data)
            
            df.to_csv(output_path, index=False)
        else:
            logger.error(f"Unsupported output format: {output_path}")
            return False
        
        logger.info(f"Annotations saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving annotations: {str(e)}")
        return False

def compare_extractions(auto_data, manual_data):
    """
    Compare automatic and manual extractions using enhanced validation
    
    Args:
        auto_data (dict or list): Automatic extraction data
        manual_data (dict or list): Manual extraction data
        
    Returns:
        dict: Comparison results with metrics, differences, and transformation details
    """
    from .data_validator import DataValidator
    
    # Initialize validator
    validator = DataValidator()
    
    # Prepare both datasets for comparison (normalize and clean)
    auto_prepared = validator.prepare_for_comparison(auto_data)
    manual_prepared = validator.prepare_for_comparison(manual_data)

    # Track what transformations were made for transparency
    transformation_log = {
        "auto_transformations": _get_transformation_summary(auto_data, auto_prepared),
        "manual_transformations": _get_transformation_summary(manual_data, manual_prepared)
    }
    
    # Initialize results with transformation info
    results = {
        "metrics": {},
        "differences": {
            "different_values": {},
            "only_in_auto": {},
            "only_in_manual": {}
        },
        "transformation_log": transformation_log
    }
    
    # Calculate true positives, false positives, false negatives
    true_positives = 0
    different_values = {}
    only_in_auto = {}
    only_in_manual = {}
    
    # Check each key in auto against manual
    for key, auto_value in auto_prepared.items():
        if key in manual_prepared:
            manual_value = manual_prepared[key]
            if str(auto_value).lower().strip() == str(manual_value).lower().strip():
                true_positives += 1
            else:
                different_values[key] = {
                    "auto": auto_value,
                    "manual": manual_value
                }
        else:
            only_in_auto[key] = auto_value
    
    # Check for keys only in manual
    for key, manual_value in manual_prepared.items():
        if key not in auto_prepared:
            only_in_manual[key] = manual_value
    
    # Calculate metrics
    false_positives = len(only_in_auto) + len(different_values)
    false_negatives = len(only_in_manual) + len(different_values)
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    # Populate results
    results["metrics"] = {
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score
    }
    
    results["differences"] = {
        "different_values": different_values,
        "only_in_auto": only_in_auto,
        "only_in_manual": only_in_manual
    }
    
    return results

def _get_transformation_summary(original_data, prepared_data):
    """
    Create a summary of what transformations were applied
    
    Args:
        original_data: Original data before preparation
        prepared_data: Data after preparation
        
    Returns:
        dict: Summary of transformations
    """
    transformations = {
        "field_mappings": {},
        "value_normalizations": {},
        "fields_added": [],
        "fields_removed": []
    }
    
    # Convert original data to flat format for comparison
    original_flat = {}
    if isinstance(original_data, dict):
        for key, value in original_data.items():
            if isinstance(value, dict) and 'value' in value:
                original_flat[key] = value['value']
            else:
                original_flat[key] = value
    elif isinstance(original_data, list):
        for item in original_data:
            if isinstance(item, dict) and 'Characteristic' in item and 'Value' in item:
                original_flat[item['Characteristic']] = item['Value']
    
    # Track field mappings (keys that changed)
    for orig_key in original_flat.keys():
        if orig_key not in prepared_data:
            # Look for mapped version
            for prep_key in prepared_data.keys():
                if orig_key.lower().replace(' ', '_') in prep_key.lower():
                    transformations["field_mappings"][orig_key] = prep_key
                    break
    
    # Track value normalizations (values that changed)
    for key in prepared_data.keys():
        if key in original_flat:
            orig_val = str(original_flat[key]).strip()
            prep_val = str(prepared_data[key]).strip()
            if orig_val != prep_val and orig_val.lower() != prep_val.lower():
                transformations["value_normalizations"][key] = {
                    "original": orig_val,
                    "normalized": prep_val
                }
    
    # Track added/removed fields
    transformations["fields_added"] = [k for k in prepared_data.keys() if k not in original_flat.keys()]
    transformations["fields_removed"] = [k for k in original_flat.keys() if k not in prepared_data.keys()]
    
    return transformations