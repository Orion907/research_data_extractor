# src/utils/analytics.py
"""
Module for tracking and analyzing prompt performance
"""
import json
import os
import logging
from datetime import datetime
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)

class PromptAnalytics:
    """
    Class for tracking and analyzing prompt performance
    """
    
    def __init__(self, analytics_dir=None):
        """
        Initialize the analytics tracker
        
        Args:
            analytics_dir (str, optional): Directory to store analytics data
        """
        # Default to an 'analytics' directory in the project root if not specified
        self.analytics_dir = analytics_dir or os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            'analytics'
        )
        
        # Ensure the analytics directory exists
        os.makedirs(self.analytics_dir, exist_ok=True)
        
        # Path to the main analytics log file
        self.log_file = os.path.join(self.analytics_dir, 'prompt_analytics.json')
        
        # Create the log file if it doesn't exist
        if not os.path.exists(self.log_file):
            with open(self.log_file, 'w') as f:
                json.dump([], f)
        
        logger.info(f"Initialized PromptAnalytics with analytics directory: {self.analytics_dir}")
    
    def log_extraction(self, template_id, version_id, source_file, 
                      characteristics_found, start_time, end_time, success=True,
                      error=None, metadata=None):
        """
        Log a data extraction event
        
        Args:
            template_id (str): Identifier for the template used
            version_id (str): Version identifier for the template
            source_file (str): Source file processed
            characteristics_found (int): Number of characteristics extracted
            start_time (datetime): When the extraction started
            end_time (datetime): When the extraction completed
            success (bool): Whether the extraction was successful
            error (str, optional): Error message if the extraction failed
            metadata (dict, optional): Additional metadata about the extraction
        """
        # Calculate duration in seconds
        duration = (end_time - start_time).total_seconds()
        
        # Create the log entry
        log_entry = {
            'template_id': template_id,
            'version_id': version_id,
            'source_file': source_file,
            'characteristics_found': characteristics_found,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'success': success,
            'error': error,
            'metadata': metadata or {},
            'logged_at': datetime.now().isoformat()
        }
        
        # Append to the log file
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
                
            logs.append(log_entry)
            
            with open(self.log_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
            logger.info(f"Logged extraction from {source_file} using template {template_id}")
            
        except Exception as e:
            logger.error(f"Error logging extraction: {str(e)}")
    
    def get_analytics_summary(self, days=30):
        """
        Get a summary of extraction performance
        
        Args:
            days (int): Number of days to include in the summary
            
        Returns:
            dict: Summary statistics
        """
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
                
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame(logs)
            
            # Convert string timestamps to datetime
            df['start_time'] = pd.to_datetime(df['start_time'])
            
            # Filter for recent entries
            cutoff_date = datetime.now() - pd.Timedelta(days=days)
            recent_df = df[df['start_time'] > cutoff_date]
            
            # Basic summary statistics
            summary = {
                'total_extractions': len(recent_df),
                'successful_extractions': recent_df['success'].sum(),
                'failed_extractions': len(recent_df) - recent_df['success'].sum(),
                'avg_extraction_time': recent_df['duration_seconds'].mean(),
                'avg_characteristics_found': recent_df['characteristics_found'].mean(),
                'total_files_processed': recent_df['source_file'].nunique()
            }
            
            # Add template performance summary
            template_summary = recent_df.groupby('template_id').agg({
                'success': 'mean',
                'duration_seconds': 'mean',
                'characteristics_found': 'mean',
                'template_id': 'count'
            }).rename(columns={'template_id': 'count'})
            
            summary['template_performance'] = template_summary.to_dict('index')
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating analytics summary: {str(e)}")
            return {'error': str(e)}
    
    def export_analytics_csv(self, output_path=None):
        """
        Export analytics data to CSV
        
        Args:
            output_path (str, optional): Path to save the CSV file
            
        Returns:
            str: Path to the saved CSV file
        """
        if output_path is None:
            output_path = os.path.join(self.analytics_dir, f'analytics_export_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv')
            
        try:
            with open(self.log_file, 'r') as f:
                logs = json.load(f)
                
            # Convert to DataFrame
            df = pd.DataFrame(logs)
            
            # Remove nested dict columns for CSV export
            if 'metadata' in df.columns:
                df = df.drop('metadata', axis=1)
                
            # Save to CSV
            df.to_csv(output_path, index=False)
            
            logger.info(f"Exported analytics data to {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error exporting analytics: {str(e)}")
            raise