# src/utils/results_manager.py
"""
Module for managing and storing extraction results
"""
import os
import json
import logging
import pandas as pd
from datetime import datetime
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

class ResultsManager:
    """
    Manages storage, retrieval, and analysis of extraction results
    """
    
    def __init__(self, results_dir=None):
        """
        Initialize the results manager
        
        Args:
            results_dir (str, optional): Directory to store extraction results
        """
        # Default to a 'results' directory in the project root if not specified
        self.results_dir = results_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'data', 'results'
        )
        
        # Create subdirectories for different types of results
        self.raw_results_dir = os.path.join(self.results_dir, 'raw')
        self.processed_results_dir = os.path.join(self.results_dir, 'processed')
        self.exports_dir = os.path.join(self.results_dir, 'exports')
        
        # Ensure directories exist
        for directory in [self.results_dir, self.raw_results_dir, 
                          self.processed_results_dir, self.exports_dir]:
            os.makedirs(directory, exist_ok=True)
            
        logger.info(f"Initialized ResultsManager with results directory: {self.results_dir}")
    
    def save_extraction_result(self, result, source_file, model_info, 
                               prompt_id=None, metadata=None):
        """
        Save an extraction result with metadata
        
        Args:
            result (dict): The extracted data
            source_file (str): Source PDF file path
            model_info (dict): Information about the model used
            prompt_id (str, optional): ID of the prompt used
            metadata (dict, optional): Additional metadata
            
        Returns:
            str: ID of the saved result
        """
        # Generate a unique ID for this result
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        source_basename = os.path.basename(source_file).replace('.pdf', '')
        result_id = f"{source_basename}_{timestamp}"
        
        # Create metadata
        meta = {
            'result_id': result_id,
            'source_file': source_file,
            'extraction_time': datetime.now().isoformat(),
            'model_info': model_info,
            'prompt_id': prompt_id,
            'metadata': metadata or {}
        }
        
        # Create a complete result object
        complete_result = {
            'metadata': meta,
            'data': result
        }
        
        # Save to JSON file
        file_path = os.path.join(self.raw_results_dir, f"{result_id}.json")
        try:
            with open(file_path, 'w') as f:
                json.dump(complete_result, f, indent=2)
            logger.info(f"Saved extraction result to {file_path}")
            return result_id
        except Exception as e:
            logger.error(f"Error saving extraction result: {str(e)}")
            raise
    
    def get_result(self, result_id):
        """
        Get a specific result by ID
        
        Args:
            result_id (str): ID of the result to retrieve
            
        Returns:
            dict: The extraction result with metadata
        """
        file_path = os.path.join(self.raw_results_dir, f"{result_id}.json")
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Result not found: {result_id}")
                return None
                
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error retrieving result {result_id}: {str(e)}")
            return None
    
    def list_results(self, filter_by=None):
        """
        List available results, optionally filtered
        
        Args:
            filter_by (dict, optional): Filter criteria (e.g., {'source_file': 'article.pdf'})
            
        Returns:
            list: List of result IDs matching the filter
        """
        results = []
        
        for filename in os.listdir(self.raw_results_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(self.raw_results_dir, filename), 'r') as f:
                        data = json.load(f)
                        
                    # Apply filter if specified
                    if filter_by:
                        matches = True
                        for key, value in filter_by.items():
                            if key in data['metadata']:
                                if data['metadata'][key] != value:
                                    matches = False
                                    break
                            else:
                                matches = False
                                break
                        
                        if matches:
                            results.append(data['metadata']['result_id'])
                    else:
                        results.append(data['metadata']['result_id'])
                        
                except Exception as e:
                    logger.warning(f"Error processing result file {filename}: {str(e)}")
        
        return results
    
    def export_to_csv(self, result_id=None, output_path=None, include_metadata=True):
        """
        Export results to CSV
        
        Args:
            result_id (str, optional): Specific result to export, exports all if None
            output_path (str, optional): Path to save the CSV file
            include_metadata (bool): Whether to include metadata in the export
            
        Returns:
            str: Path to the exported CSV file
        """
        # If output path not specified, create one in the exports directory
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"extraction_results_{timestamp}.csv"
            output_path = os.path.join(self.exports_dir, filename)
        
        if result_id:
            # Export a single result
            result = self.get_result(result_id)
            if not result:
                raise ValueError(f"Result not found: {result_id}")
                
            # Convert the data to a flat format for CSV
            flat_data = self._flatten_result(result, include_metadata)
            
            # Save to CSV
            df = pd.DataFrame([flat_data])
            df.to_csv(output_path, index=False)
            logger.info(f"Exported result {result_id} to {output_path}")
            
        else:
            # Export all results
            flat_results = []
            
            for result_id in self.list_results():
                result = self.get_result(result_id)
                if result:
                    flat_data = self._flatten_result(result, include_metadata)
                    flat_results.append(flat_data)
            
            if flat_results:
                df = pd.DataFrame(flat_results)
                df.to_csv(output_path, index=False)
                logger.info(f"Exported {len(flat_results)} results to {output_path}")
            else:
                logger.warning("No results to export")
                # Create an empty CSV
                pd.DataFrame().to_csv(output_path, index=False)
        
        return output_path
    
    def _flatten_result(self, result, include_metadata=True):
        """
        Flatten a nested result dictionary for CSV export
        
        Args:
            result (dict): The result to flatten
            include_metadata (bool): Whether to include metadata
            
        Returns:
            dict: Flattened dictionary
        """
        flat_dict = {}
        
        # Include metadata if requested
        if include_metadata:
            for key, value in result['metadata'].items():
                if key == 'metadata' or key == 'model_info':
                    # Handle nested dictionaries
                    for subkey, subvalue in value.items():
                        flat_dict[f"meta_{key}_{subkey}"] = subvalue
                else:
                    flat_dict[f"meta_{key}"] = value
        
        # Add the actual data
        for key, value in result['data'].items():
            flat_dict[key] = value
        
        return flat_dict
    
    def compare_results(self, result_ids):
        """
        Compare multiple extraction results
        
        Args:
            result_ids (list): List of result IDs to compare
            
        Returns:
            dict: Comparison statistics
        """
        if not result_ids or len(result_ids) < 2:
            raise ValueError("At least two result IDs are required for comparison")
            
        results = []
        for result_id in result_ids:
            result = self.get_result(result_id)
            if result:
                results.append(result)
            else:
                logger.warning(f"Result not found: {result_id}")
        
        if len(results) < 2:
            raise ValueError("At least two valid results are required for comparison")
            
        # Identify common fields
        common_fields = set(results[0]['data'].keys())
        for result in results[1:]:
            common_fields &= set(result['data'].keys())
        
        # Compare values for common fields
        comparison = {
            'common_fields': len(common_fields),
            'total_fields': {result_id: len(results[i]['data']) for i, result_id in enumerate(result_ids)},
            'field_agreement': {},
            'field_values': {}
        }
        
        # Analyze each common field
        for field in common_fields:
            values = [result['data'][field] for result in results]
            unique_values = set(values)
            
            comparison['field_values'][field] = values
            comparison['field_agreement'][field] = {
                'agreement': len(unique_values) == 1,
                'unique_values': len(unique_values)
            }
        
        return comparison
    
    def get_result_stats(self):
        """
        Get statistics about the stored results
        
        Returns:
            dict: Statistics about the results
        """
        stats = {
            'total_results': 0,
            'by_source': {},
            'by_model': {},
            'by_prompt': {},
            'field_frequency': {}
        }
        
        field_counts = {}
        
        for result_id in self.list_results():
            result = self.get_result(result_id)
            if not result:
                continue
                
            stats['total_results'] += 1
            
            # Count by source file
            source_file = result['metadata'].get('source_file', 'unknown')
            if source_file not in stats['by_source']:
                stats['by_source'][source_file] = 0
            stats['by_source'][source_file] += 1
            
            # Count by model
            model_info = result['metadata'].get('model_info', {})
            model_name = model_info.get('model_name', 'unknown')
            if model_name not in stats['by_model']:
                stats['by_model'][model_name] = 0
            stats['by_model'][model_name] += 1
            
            # Count by prompt
            prompt_id = result['metadata'].get('prompt_id', 'unknown')
            if prompt_id not in stats['by_prompt']:
                stats['by_prompt'][prompt_id] = 0
            stats['by_prompt'][prompt_id] += 1
            
            # Count field frequency
            for field in result['data'].keys():
                if field not in field_counts:
                    field_counts[field] = 0
                field_counts[field] += 1
        
        # Calculate field frequency as percentage
        if stats['total_results'] > 0:
            for field, count in field_counts.items():
                stats['field_frequency'][field] = round(count / stats['total_results'] * 100, 1)
        
        return stats