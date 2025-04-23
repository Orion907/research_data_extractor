# src/utils/unified_analytics.py
"""
Unified analytics module for tracking extraction performance and prompt effectiveness
"""
import json
import os
import logging
import datetime
import pandas as pd
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

class Analytics:
    """
    Unified analytics system for tracking extraction performance and prompt effectiveness
    """
    
    def __init__(self, analytics_dir=None):
        """
        Initialize the analytics system
        
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
        
        # Initialize storage for different types of analytics
        self.extraction_stats = defaultdict(list)
        
        # Define file paths
        self.extractions_file = os.path.join(self.analytics_dir, 'extraction_stats.json')
        self.prompt_analytics_file = os.path.join(self.analytics_dir, 'prompt_analytics.json')
        
        # Load existing data if available
        self._load_existing_data()
        
        logger.info(f"Initialized unified Analytics system with directory: {self.analytics_dir}")
    
    def _load_existing_data(self):
        """
        Load existing analytics data from files
        """
        # Load extraction stats
        if os.path.exists(self.extractions_file):
            try:
                with open(self.extractions_file, 'r') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        self.extraction_stats[key] = value
                logger.info(f"Loaded existing extraction stats from {self.extractions_file}")
            except Exception as e:
                logger.error(f"Error loading extraction stats: {str(e)}")
        else:
            # Initialize with empty extractions list
            self.extraction_stats['extractions'] = []
            # Create the file
            with open(self.extractions_file, 'w') as f:
                json.dump(dict(self.extraction_stats), f)
        
        # Initialize prompt analytics file if it doesn't exist
        if not os.path.exists(self.prompt_analytics_file):
            with open(self.prompt_analytics_file, 'w') as f:
                json.dump([], f)
    
    def track_extraction(self, prompt_id, model, duration_ms, char_count, token_count=None, 
                         success=True, metadata=None):
        """
        Track a single extraction event
        
        Args:
            prompt_id (str): Identifier for the prompt used
            model (str): Model used for extraction
            duration_ms (float): Duration in milliseconds
            char_count (int): Character count of the processed text
            token_count (int, optional): Token count if available
            success (bool): Whether the extraction was successful
            metadata (dict, optional): Additional metadata
        """
        timestamp = datetime.datetime.now().isoformat()
        
        event = {
            'timestamp': timestamp,
            'prompt_id': prompt_id,
            'model': model,
            'duration_ms': duration_ms,
            'char_count': char_count,
            'token_count': token_count,
            'success': success
        }
        
        # Add any additional metadata
        if metadata:
            event.update(metadata)
        
        # Add to tracked stats
        self.extraction_stats['extractions'].append(event)
        
        # Save to file
        try:
            with open(self.extractions_file, 'w') as f:
                json.dump(dict(self.extraction_stats), f)
            logger.debug(f"Tracked extraction event with prompt {prompt_id}")
        except Exception as e:
            logger.error(f"Error saving extraction stats: {str(e)}")
    
    def log_extraction(self, template_id, version_id, source_file, 
                      characteristics_found, start_time, end_time, success=True,
                      error=None, metadata=None):
        """
        Log a detailed data extraction event
        
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
            'logged_at': datetime.datetime.now().isoformat()
        }
        
        # Append to the log file
        try:
            with open(self.prompt_analytics_file, 'r') as f:
                logs = json.load(f)
                
            logs.append(log_entry)
            
            with open(self.prompt_analytics_file, 'w') as f:
                json.dump(logs, f, indent=2)
                
            logger.info(f"Logged extraction from {source_file} using template {template_id}")
            
        except Exception as e:
            logger.error(f"Error logging extraction: {str(e)}")
    
    def get_extraction_stats(self, days=None, model=None, prompt_id=None):
        """
        Get statistics on extractions
        
        Args:
            days (int, optional): Number of days to look back
            model (str, optional): Filter by model
            prompt_id (str, optional): Filter by prompt ID
            
        Returns:
            dict: Statistics on extractions
        """
        events = self.extraction_stats.get('extractions', [])
        
        # Filter by date if specified
        if days:
            cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
            events = [e for e in events if e['timestamp'] >= cutoff]
        
        # Filter by model if specified
        if model:
            events = [e for e in events if e['model'] == model]
        
        # Filter by prompt if specified
        if prompt_id:
            events = [e for e in events if e['prompt_id'] == prompt_id]
        
        # Calculate statistics
        if not events:
            return {
                'count': 0,
                'avg_duration_ms': 0,
                'success_rate': 0,
                'models': {},
                'prompts': {}
            }
        
        # Basic stats
        stats = {
            'count': len(events),
            'avg_duration_ms': sum(e['duration_ms'] for e in events) / len(events),
            'success_rate': sum(1 for e in events if e['success']) / len(events)
        }
        
        # Model breakdown
        models = {}
        for e in events:
            model_name = e['model']
            if model_name not in models:
                models[model_name] = {'count': 0, 'success_count': 0}
            models[model_name]['count'] += 1
            if e['success']:
                models[model_name]['success_count'] += 1
        
        for m in models:
            models[m]['success_rate'] = models[m]['success_count'] / models[m]['count']
        
        stats['models'] = models
        
        # Prompt breakdown
        prompts = {}
        for e in events:
            prompt_id = e['prompt_id']
            if prompt_id not in prompts:
                prompts[prompt_id] = {'count': 0, 'success_count': 0}
            prompts[prompt_id]['count'] += 1
            if e['success']:
                prompts[prompt_id]['success_count'] += 1
        
        for p in prompts:
            prompts[p]['success_rate'] = prompts[p]['success_count'] / prompts[p]['count']
        
        stats['prompts'] = prompts
        
        return stats
    
    def get_analytics_summary(self, days=30):
        """
        Get a summary of extraction performance
        
        Args:
            days (int): Number of days to include in the summary
            
        Returns:
            dict: Summary statistics
        """
        try:
            with open(self.prompt_analytics_file, 'r') as f:
                logs = json.load(f)
                
            # Convert to DataFrame for easier analysis
            df = pd.DataFrame(logs)
            
            # If no data, return empty summary
            if df.empty:
                return {
                    'total_extractions': 0,
                    'successful_extractions': 0,
                    'failed_extractions': 0,
                    'avg_extraction_time': 0,
                    'avg_characteristics_found': 0,
                    'total_files_processed': 0,
                    'template_performance': {}
                }
            
            # Convert string timestamps to datetime
            df['start_time'] = pd.to_datetime(df['start_time'])
            
            # Filter for recent entries
            cutoff_date = datetime.datetime.now() - pd.Timedelta(days=days)
            recent_df = df[df['start_time'] > cutoff_date]
            
            # If no recent data, return empty summary
            if recent_df.empty:
                return {
                    'total_extractions': 0,
                    'successful_extractions': 0,
                    'failed_extractions': 0,
                    'avg_extraction_time': 0,
                    'avg_characteristics_found': 0,
                    'total_files_processed': 0,
                    'template_performance': {}
                }
            
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
    
    def generate_report(self, days=30):
        """
        Generate a comprehensive analytics report
        
        Args:
            days (int): Number of days to include in report
            
        Returns:
            dict: Report data
        """
        # Get overall stats
        stats = self.get_extraction_stats(days=days)
        
        # Create time series data for visualizations
        events = self.extraction_stats.get('extractions', [])
        
        # Filter by date
        cutoff = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
        events = [e for e in events if e['timestamp'] >= cutoff]
        
        # Convert to DataFrame for easier analysis
        if events:
            df = pd.DataFrame(events)
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            
            # Daily counts
            daily_counts = df.groupby('date').size().reset_index(name='count')
            daily_success = df.groupby('date')['success'].mean().reset_index(name='success_rate')
            
            # Merge
            daily_data = pd.merge(daily_counts, daily_success, on='date')
            
            # Convert to dict for JSON serialization
            time_series = {
                'dates': [d.isoformat() for d in daily_data['date']],
                'counts': daily_data['count'].tolist(),
                'success_rates': daily_data['success_rate'].tolist()
            }
        else:
            time_series = {
                'dates': [],
                'counts': [],
                'success_rates': []
            }
        
        return {
            'stats': stats,
            'time_series': time_series
        }
    
    def export_analytics_csv(self, output_path=None):
        """
        Export analytics data to CSV
        
        Args:
            output_path (str, optional): Path to save the CSV file
            
        Returns:
            str: Path to the saved CSV file
        """
        if output_path is None:
            output_path = os.path.join(self.analytics_dir, f'analytics_export_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.csv')
            
        try:
            with open(self.prompt_analytics_file, 'r') as f:
                logs = json.load(f)
                
            # Convert to DataFrame
            df = pd.DataFrame(logs)
            
            # If dataframe is empty, return an empty CSV
            if df.empty:
                with open(output_path, 'w') as f:
                    f.write("No analytics data available")
                logger.info(f"Created empty CSV file at {output_path}")
                return output_path
            
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