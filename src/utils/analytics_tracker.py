"""
Module for tracking and analyzing prompt and extraction performance
"""
import json
import os
import logging
import datetime
import pandas as pd
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

class AnalyticsTracker:
    """
    Tracks analytics for prompt performance and data extraction
    """
    
    def __init__(self, analytics_dir='data/analytics'):
        """
        Initialize the analytics tracker
        
        Args:
            analytics_dir (str): Directory to store analytics data
        """
        self.analytics_dir = analytics_dir
        self.extraction_stats = defaultdict(list)
        
        # Create analytics directory if it doesn't exist
        os.makedirs(analytics_dir, exist_ok=True)
        
        # Path for extraction data
        self.extractions_file = os.path.join(analytics_dir, 'extraction_stats.json')
        
        # Load existing data if available
        if os.path.exists(self.extractions_file):
            try:
                with open(self.extractions_file, 'r') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        self.extraction_stats[key] = value
            except Exception as e:
                logger.error(f"Error loading extraction stats: {str(e)}")
        
        logger.info(f"Initialized AnalyticsTracker with directory: {analytics_dir}")
    
    def track_extraction(self, prompt_id, model, duration_ms, char_count, token_count=None, success=True, metadata=None):
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