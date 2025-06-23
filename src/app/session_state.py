"""
Safe session state management utilities for Streamlit app

Provides centralized session state management with backward compatibility
and safe initialization/reset patterns.
"""

import streamlit as st
from typing import Any, Dict, List, Optional


class SessionStateManager:
    """
    Centralized session state management with safety patterns.
    
    Provides safe initialization, access, and reset functionality
    while maintaining full backward compatibility with existing code.
    """
    
    # Define all known session state keys with their default values
    DEFAULT_STATE = {
        # Single extraction state
        'processing_complete': False,
        'view_type': "Structured",
        'current_file': None,
        'chunk_results': [],
        'results_df': None,
        'extracted_text': "",
        'uploaded_file_name': None,
        'chunks': [],
        
        # Provider and model settings
        'provider': "anthropic",
        'batch_provider': "anthropic",
        'batch_model': None,
        
        # Batch processing state
        'batch_files': [],
        'batch_processing_complete': False,
        'batch_results': [],
        'batch_chunk_size': 1000,
        'batch_overlap': 100,
        'batch_temperature': 0.0,
        'batch_continue_on_error': True,
        'batch_save_individual': True,
        'batch_max_concurrent': "Sequential (1 at a time)",
        'zip_temp_dir': None,
    }
    
    @staticmethod
    def initialize_all_state() -> None:
        """
        Initialize all session state variables with their default values.
        
        This is safe to call multiple times - it only sets values that don't exist.
        Maintains backward compatibility with existing initialization patterns.
        """
        for key, default_value in SessionStateManager.DEFAULT_STATE.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    @staticmethod
    def get_or_create(key: str, default_value: Any = None) -> Any:
        """
        Safely get a session state value, creating it with default if it doesn't exist.
        
        Args:
            key: Session state key
            default_value: Value to use if key doesn't exist
            
        Returns:
            The session state value
        """
        if key not in st.session_state:
            # Use provided default, or fall back to DEFAULT_STATE, or None
            if default_value is not None:
                st.session_state[key] = default_value
            elif key in SessionStateManager.DEFAULT_STATE:
                st.session_state[key] = SessionStateManager.DEFAULT_STATE[key]
            else:
                st.session_state[key] = None
        
        return st.session_state[key]
    
    @staticmethod
    def set_value(key: str, value: Any) -> None:
        """
        Safely set a session state value.
        
        Args:
            key: Session state key
            value: Value to set
        """
        st.session_state[key] = value
    
    @staticmethod
    def reset_single_extraction_state() -> None:
        """
        Reset session state variables related to single document extraction.
        
        This maintains the exact same behavior as the original reset logic
        but centralizes it for consistency and maintainability.
        """
        keys_to_reset = [
            'processing_complete',
            'view_type',
            'uploaded_file_name', 
            'chunk_results',
            'results_df',
            'chunks',
            'extracted_text',
            'current_file'
        ]
        
        for key in keys_to_reset:
            if key in st.session_state:
                if key == 'view_type':
                    st.session_state[key] = "Structured"  # Reset to default
                elif key == 'processing_complete':
                    st.session_state[key] = False  # Reset to default
                elif key in ['chunk_results', 'chunks']:
                    st.session_state[key] = []  # Reset to empty list
                else:
                    del st.session_state[key]  # Remove completely
    
    @staticmethod 
    def reset_batch_processing_state() -> None:
        """
        Reset session state variables related to batch processing.
        
        Includes cleanup of temporary directories and file objects.
        """
        import shutil
        import os
        
        # Clean up temporary directory if it exists
        if 'zip_temp_dir' in st.session_state and st.session_state.zip_temp_dir:
            try:
                if os.path.exists(st.session_state.zip_temp_dir):
                    shutil.rmtree(st.session_state.zip_temp_dir)
            except Exception:
                pass  # Silently handle cleanup errors
        
        keys_to_reset = [
            'batch_processing_complete',
            'batch_files',
            'batch_results', 
            'zip_temp_dir'
        ]
        
        for key in keys_to_reset:
            if key in st.session_state:
                if key in ['batch_files', 'batch_results']:
                    st.session_state[key] = []  # Reset to empty list
                else:
                    del st.session_state[key]  # Remove completely
    
    @staticmethod
    def get_state_summary() -> Dict[str, Any]:
        """
        Get a summary of current session state for debugging.
        
        Returns:
            Dictionary with state key counts and types
        """
        summary = {
            'total_keys': len(st.session_state),
            'initialized_keys': [],
            'custom_keys': []
        }
        
        for key in st.session_state.keys():
            if key in SessionStateManager.DEFAULT_STATE:
                summary['initialized_keys'].append(key)
            else:
                summary['custom_keys'].append(key)
        
        return summary
    
    @staticmethod
    def validate_state() -> List[str]:
        """
        Validate session state for common issues.
        
        Returns:
            List of validation warnings/errors
        """
        issues = []
        
        # Check for missing critical state
        critical_keys = ['processing_complete', 'batch_processing_complete']
        for key in critical_keys:
            if key not in st.session_state:
                issues.append(f"Missing critical state key: {key}")
        
        # Check for inconsistent state combinations
        if (st.session_state.get('processing_complete', False) and 
            not st.session_state.get('chunk_results')):
            issues.append("Processing marked complete but no results found")
        
        if (st.session_state.get('batch_processing_complete', False) and 
            not st.session_state.get('batch_results')):
            issues.append("Batch processing marked complete but no results found")
        
        return issues


class SessionStateContext:
    """
    Context manager for safe session state operations.
    
    Useful for operations that need to temporarily modify state
    and then restore it, or for batch state operations.
    """
    
    def __init__(self, backup_keys: Optional[List[str]] = None):
        """
        Initialize context manager.
        
        Args:
            backup_keys: List of keys to backup and restore, None for all
        """
        self.backup_keys = backup_keys
        self.backup_state = {}
    
    def __enter__(self):
        """Enter context - backup specified state."""
        keys_to_backup = self.backup_keys or list(st.session_state.keys())
        
        for key in keys_to_backup:
            if key in st.session_state:
                self.backup_state[key] = st.session_state[key]
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - restore backed up state if needed."""
        if exc_type is not None:
            # An exception occurred, restore backed up state
            for key, value in self.backup_state.items():
                st.session_state[key] = value
        
        return False  # Don't suppress exceptions