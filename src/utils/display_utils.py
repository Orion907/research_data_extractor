# src/utils/display_utils.py
"""
Utilities for displaying structured extraction results in the Streamlit app.
"""
import json
import re
import logging
import streamlit as st
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)

def parse_extraction_result(text):
    """
    Parse LLM extraction results into structured data.
    
    Args:
        text (str): Raw extraction text from LLM
        
    Returns:
        dict: Structured data extracted from the text
    """
    # Try to parse JSON if the text appears to be JSON format
    if '{' in text and '}' in text:
        try:
            # Find the JSON object in the text
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            json_str = text[json_start:json_end]
            
            # Parse the JSON
            return json.loads(json_str)
        except json.JSONDecodeError:
            logger.warning("Failed to parse as JSON, attempting key-value parsing")
    
    # If not JSON or JSON parsing failed, try key-value format
    try:
        result = {}
        # Split by lines and find key-value pairs
        lines = text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip()] = value.strip()
                
        return result
    except Exception as e:
        logger.warning(f"Failed to parse as key-value pairs: {str(e)}")
        return {"raw_text": text}

def categorize_extraction_data(data):
    """
    Categorize extraction data into logical groups.
    
    Args:
        data (dict): Parsed extraction data
        
    Returns:
        dict: Data categorized by type
    """
    categories = {
        "Demographics": {},
        "Inclusion Criteria": {},
        "Exclusion Criteria": {},
        "Comorbidities": {},
        "Medications": {},
        "Disease-specific": {},
        "Other": {}
    }
    
    # Keywords to help categorize data
    category_keywords = {
        "Demographics": ["age", "gender", "sex", "ethnicity", "race", "bmi", "weight", "height", 
                        "demographics", "population", "patients", "subjects", "participant"],
        "Inclusion Criteria": ["inclusion", "eligible", "eligibility"],
        "Exclusion Criteria": ["exclusion", "excluded", "ineligible"],
        "Comorbidities": ["comorbid", "condition", "disease", "disorder", "syndrome", "diagnosis"],
        "Medications": ["medication", "drug", "treatment", "therapy", "dosage", "dose", 
                      "administered", "prescription"],
        "Disease-specific": ["biomarker", "marker", "measurement", "level", "score", "stage", 
                           "grade", "severity", "symptom"]
    }
    
    # Assign each data item to a category
    for key, value in data.items():
        key_lower = key.lower()
        
        # Check if the key contains "inclusion" and "criteria"
        if "inclusion" in key_lower and "criteria" in key_lower:
            categories["Inclusion Criteria"][key] = value
            continue
            
        # Check if the key contains "exclusion" and "criteria"
        if "exclusion" in key_lower and "criteria" in key_lower:
            categories["Exclusion Criteria"][key] = value
            continue
        
        # Try to match to other categories
        assigned = False
        for category, keywords in category_keywords.items():
            if any(keyword in key_lower for keyword in keywords):
                categories[category][key] = value
                assigned = True
                break
                
        # If not assigned to any specific category, put in "Other"
        if not assigned:
            categories["Other"][key] = value
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v}

def display_structured_results(extraction_results, development_mode=False):
    """
    Display extraction results in a structured, user-friendly format.
    
    Args:
        extraction_results (list): List of extraction results by chunk
        development_mode (bool): Whether to show detailed extraction by chunk
        
    Returns:
        dict: Combined structured data from all chunks
    """
    # Combine and deduplicate results from all chunks
    combined_data = {}
    
    for result in extraction_results:
        chunk_idx = result['chunk_index']
        extraction_text = result['extraction']
        
        # Parse the extraction result
        parsed_data = parse_extraction_result(extraction_text)
        
        # Display individual chunk results only in development mode
        if development_mode:
            st.subheader(f"Chunk {chunk_idx+1} Extractions")
            
            # Categorize and display results for this chunk
            categorized = categorize_extraction_data(parsed_data)
            
            for category, items in categorized.items():
                if items:  # Only show non-empty categories
                    with st.expander(f"{category} ({len(items)} items)"):
                        # Convert to DataFrame for display
                        values = []
                        for value in items.values():
                            if isinstance(value, list):
                                # Convert lists to strings
                                values.append("; ".join(str(item) for item in value))
                            elif isinstance(value, dict):
                                # Convert dicts to JSON strings
                                values.append(json.dumps(value))
                            else:
                                values.append(value)
                        
                        df = pd.DataFrame(
                            {"Value": values},
                            index=items.keys()
                        )
                        st.dataframe(df, use_container_width=True)
        
        # Categorize for combining (we do this regardless of display mode)
        categorized = categorize_extraction_data(parsed_data)
                
        # Add to combined data (for all chunks)
        for category, items in categorized.items():
            if items:
                if category not in combined_data:
                    combined_data[category] = {}
                combined_data[category].update(items)
    
    # Deduplicate the combined data
    deduplicated_data = {}
    for category, items in combined_data.items():
        if items:  # Only process non-empty categories
            unique_items = {}
            for key, value in items.items():
                # Convert value to string for comparison
                value_str = str(value)
                # Only add if we haven't seen this value before
                if value_str not in [str(v) for v in unique_items.values()]:
                    unique_items[key] = value
            deduplicated_data[category] = unique_items
    
    # Display combined results
    header_text = "Combined Extraction Results" if development_mode else "Extraction Results"
    st.header(f"{header_text} (Deduplicated)")
    
    # Display the deduplicated data
    for category, items in deduplicated_data.items():
        if items:  # Only show non-empty categories
            with st.expander(f"{category} ({len(items)} items)", expanded=True):
                # Convert to DataFrame for display
                values = []
                for value in items.values():
                    if isinstance(value, list):
                        # Convert lists to strings
                        values.append("; ".join(str(item) for item in value))
                    elif isinstance(value, dict):
                        # Convert dicts to JSON strings
                        values.append(json.dumps(value))
                    else:
                        values.append(value)
                
                df = pd.DataFrame(
                    {"Value": values},
                    index=items.keys()
                )
                st.dataframe(df, use_container_width=True)
    
    # Return the deduplicated data for potential further processing
    return deduplicated_data