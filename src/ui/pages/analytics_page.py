# src/ui/pages/analytics_page.py

"""
Analytics Dashboard Page Component

This module provides the complete Analytics Dashboard interface as a reusable component,
including metrics display, charts, and performance analysis.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional, List

from src.utils.unified_analytics import Analytics


class AnalyticsPage:
    """
    Complete Analytics Dashboard page component that handles:
    - Time period selection and filtering
    - Summary metrics display
    - Extraction activity charts
    - Model performance comparison
    - Prompt performance analysis
    - Raw analytics data exploration
    """
    
    def __init__(self, analytics: Analytics):
        """
        Initialize the analytics page component.
        
        Args:
            analytics: Analytics system instance
        """
        self.analytics = analytics
    
    def render(self) -> None:
        """Render the complete Analytics Dashboard page."""
        st.header("Analytics Dashboard")
        
        # Time period selection
        time_period = self._render_time_period_selector()
        
        # Generate report using the unified Analytics system
        report = self.analytics.generate_report(days=time_period)
        
        # Display summary metrics
        self._render_summary_metrics(report)
        
        # Display extraction activity charts
        self._render_activity_charts(report)
        
        # Display model performance comparison
        self._render_model_performance(report)
        
        # Display prompt performance comparison
        self._render_prompt_performance(report)
        
        # Raw analytics data (for debugging)
        self._render_raw_data(report)
    
    def _render_time_period_selector(self) -> int:
        """
        Render time period selection widget.
        
        Returns:
            int: Selected time period in days
        """
        return st.selectbox(
            "Time Period",
            [7, 30, 90, 365],
            index=1,
            format_func=lambda x: f"Last {x} days"
        )
    
    def _render_summary_metrics(self, report: Dict[str, Any]):
        """
        Render summary metrics section.
        
        Args:
            report: Analytics report data
        """
        st.subheader("Summary Metrics")
        
        stats = report.get('stats', {})
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Extractions", stats.get('count', 0))
        
        with col2:
            avg_duration = stats.get('avg_duration_ms', 0)
            st.metric("Avg. Duration (ms)", f"{avg_duration:.1f}")
        
        with col3:
            success_rate = stats.get('success_rate', 0)
            st.metric("Success Rate", f"{success_rate * 100:.1f}%")
    
    def _render_activity_charts(self, report: Dict[str, Any]):
        """
        Render extraction activity charts.
        
        Args:
            report: Analytics report data
        """
        time_series = report.get('time_series', {})
        dates = time_series.get('dates', [])
        
        if not dates:
            st.info("No extraction data available for the selected time period.")
            return
        
        st.subheader("Extraction Activity")
        
        # Convert to DataFrame for plotting
        time_df = pd.DataFrame({
            'date': pd.to_datetime(dates),
            'count': time_series.get('counts', []),
            'success_rate': time_series.get('success_rates', [])
        })
        
        # Create charts
        self._create_activity_charts(time_df)
    
    def _create_activity_charts(self, time_df: pd.DataFrame):
        """
        Create and display activity charts.
        
        Args:
            time_df: DataFrame with time series data
        """
        # Plot using matplotlib
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Extractions per day
        ax1.bar(time_df['date'], time_df['count'])
        ax1.set_title('Extractions per Day')
        ax1.set_ylabel('Count')
        ax1.tick_params(axis='x', rotation=45)
        
        # Success rate
        ax2.plot(time_df['date'], time_df['success_rate'], marker='o', linestyle='-')
        ax2.set_title('Success Rate')
        ax2.set_ylabel('Rate')
        ax2.set_ylim(0, 1)
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        st.pyplot(fig)
    
    def _render_model_performance(self, report: Dict[str, Any]):
        """
        Render model performance comparison section.
        
        Args:
            report: Analytics report data
        """
        stats = report.get('stats', {})
        models = stats.get('models', {})
        
        if not models:
            return
        
        st.subheader("Model Performance")
        
        # Convert model stats to DataFrame
        model_data = []
        for model_name, model_stats in models.items():
            model_data.append({
                'model': model_name,
                'count': model_stats.get('count', 0),
                'success_rate': model_stats.get('success_rate', 0),
                'avg_time': 0  # Would need to calculate this from raw data
            })
        
        model_df = pd.DataFrame(model_data)
        
        # Display as interactive table
        st.dataframe(
            model_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Optional: Create a model performance chart
        if len(model_data) > 1:
            self._create_model_performance_chart(model_df)
    
    def _create_model_performance_chart(self, model_df: pd.DataFrame):
        """
        Create model performance comparison chart.
        
        Args:
            model_df: DataFrame with model performance data
        """
        st.subheader("Model Performance Comparison")
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Model usage count
        ax1.bar(model_df['model'], model_df['count'])
        ax1.set_title('Model Usage Count')
        ax1.set_ylabel('Count')
        ax1.tick_params(axis='x', rotation=45)
        
        # Model success rate
        ax2.bar(model_df['model'], model_df['success_rate'])
        ax2.set_title('Model Success Rate')
        ax2.set_ylabel('Success Rate')
        ax2.set_ylim(0, 1)
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        st.pyplot(fig)
    
    def _render_prompt_performance(self, report: Dict[str, Any]):
        """
        Render prompt performance comparison section.
        
        Args:
            report: Analytics report data
        """
        stats = report.get('stats', {})
        prompts = stats.get('prompts', {})
        
        if not prompts:
            return
        
        st.subheader("Prompt Performance")
        
        # Convert prompt stats to DataFrame
        prompt_data = []
        for prompt_id, prompt_stats in prompts.items():
            prompt_data.append({
                'prompt_id': prompt_id,
                'count': prompt_stats.get('count', 0),
                'success_rate': prompt_stats.get('success_rate', 0)
            })
        
        prompt_df = pd.DataFrame(prompt_data)
        
        # Display as interactive table
        st.dataframe(
            prompt_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Optional: Create a prompt performance chart
        if len(prompt_data) > 1:
            self._create_prompt_performance_chart(prompt_df)
    
    def _create_prompt_performance_chart(self, prompt_df: pd.DataFrame):
        """
        Create prompt performance comparison chart.
        
        Args:
            prompt_df: DataFrame with prompt performance data
        """
        st.subheader("Prompt Performance Comparison")
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
        
        # Prompt usage count
        ax1.bar(prompt_df['prompt_id'], prompt_df['count'])
        ax1.set_title('Prompt Usage Count')
        ax1.set_ylabel('Count')
        ax1.tick_params(axis='x', rotation=45)
        
        # Prompt success rate
        ax2.bar(prompt_df['prompt_id'], prompt_df['success_rate'])
        ax2.set_title('Prompt Success Rate')
        ax2.set_ylabel('Success Rate')
        ax2.set_ylim(0, 1)
        ax2.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        st.pyplot(fig)
    
    def _render_raw_data(self, report: Dict[str, Any]):
        """
        Render raw analytics data section for debugging.
        
        Args:
            report: Analytics report data
        """
        with st.expander("Raw Analytics Data"):
            st.json(report)
    
    def render_extraction_metrics(self, extraction_results: List[Dict]) -> None:
        """
        Render metrics for a specific set of extraction results.
        
        Args:
            extraction_results: List of extraction result dictionaries
        """
        if not extraction_results:
            st.info("No extraction results to analyze.")
            return
        
        st.subheader("Current Session Metrics")
        
        # Calculate session metrics
        total_extractions = len(extraction_results)
        successful_extractions = sum(
            1 for result in extraction_results 
            if result.get('status') == 'success'
        )
        success_rate = successful_extractions / total_extractions if total_extractions > 0 else 0
        
        # Display session metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Session Extractions", total_extractions)
        
        with col2:
            st.metric("Successful", successful_extractions)
        
        with col3:
            st.metric("Session Success Rate", f"{success_rate * 100:.1f}%")
        
        # Show breakdown by type if available
        self._render_session_breakdown(extraction_results)
    
    def _render_session_breakdown(self, extraction_results: List[Dict]):
        """
        Render breakdown of session extraction results.
        
        Args:
            extraction_results: List of extraction result dictionaries
        """
        # Group by document type or other characteristics
        doc_types = {}
        processing_times = []
        
        for result in extraction_results:
            # Group by document type if available
            doc_type = result.get('document_type', 'unknown')
            if doc_type not in doc_types:
                doc_types[doc_type] = {'count': 0, 'successful': 0}
            
            doc_types[doc_type]['count'] += 1
            if result.get('status') == 'success':
                doc_types[doc_type]['successful'] += 1
            
            # Collect processing times
            if 'processing_time' in result:
                processing_times.append(result['processing_time'])
        
        # Display document type breakdown
        if len(doc_types) > 1:
            st.subheader("Document Type Breakdown")
            
            type_data = []
            for doc_type, stats in doc_types.items():
                success_rate = stats['successful'] / stats['count'] if stats['count'] > 0 else 0
                type_data.append({
                    'Document Type': doc_type,
                    'Count': stats['count'],
                    'Successful': stats['successful'],
                    'Success Rate': f"{success_rate * 100:.1f}%"
                })
            
            type_df = pd.DataFrame(type_data)
            st.dataframe(type_df, use_container_width=True, hide_index=True)
        
        # Display processing time statistics
        if processing_times:
            st.subheader("Processing Time Statistics")
            
            avg_time = sum(processing_times) / len(processing_times)
            min_time = min(processing_times)
            max_time = max(processing_times)
            
            time_cols = st.columns(3)
            with time_cols[0]:
                st.metric("Average Time", f"{avg_time:.2f}s")
            with time_cols[1]:
                st.metric("Minimum Time", f"{min_time:.2f}s")
            with time_cols[2]:
                st.metric("Maximum Time", f"{max_time:.2f}s")