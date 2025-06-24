# src/ui/pages/annotation_page.py

"""
Manual Annotation Page Component

This module provides the complete Manual Annotation interface as a reusable component,
including annotation editing and comparison functionality.
"""

import streamlit as st
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any, Union, List

from src.utils.annotation_utils import (
    display_annotation_interface, 
    load_extraction_results, 
    save_annotations, 
    compare_extractions
)


class AnnotationPage:
    """
    Complete Manual Annotation page component that handles:
    - Loading extraction results from files or recent extractions
    - Displaying annotation interface for editing
    - Saving annotated data
    - Comparing automatic vs manual extractions
    - Generating comparison reports
    """
    
    def __init__(self):
        """Initialize the annotation page component."""
        self.output_dir = "data/output"
        self.temp_dir = "data/temp"
        self.annotations_dir = "data/annotations"
        self.reports_dir = "data/reports"
        
        # Ensure directories exist
        for directory in [self.temp_dir, self.annotations_dir, self.reports_dir]:
            os.makedirs(directory, exist_ok=True)
    
    def render(self):
        """Render the complete Manual Annotation page."""
        st.header("Manual Annotation and Comparison")
        
        st.markdown("""
        This interface allows you to:
        1. **Review and edit** extraction results
        2. **Import** manually created CSV/JSON files
        3. **Compare** automatic and manual extractions
        4. **Calculate** evaluation metrics
        """)
        
        # Two tabs: annotation and comparison
        anno_tab, compare_tab = st.tabs(["Annotation", "Comparison"])
        
        with anno_tab:
            self._render_annotation_tab()
        
        with compare_tab:
            self._render_comparison_tab()
    
    def _render_annotation_tab(self):
        """Render the annotation tab interface."""
        # Option to load extraction results
        load_option = st.radio(
            "Load extraction data from:",
            ["Recent Extraction", "File Upload"],
            horizontal=True
        )
        
        extraction_data = None
        file_name = None
        
        if load_option == "Recent Extraction":
            extraction_data, file_name = self._load_recent_extraction()
        else:  # File Upload
            extraction_data, file_name = self._load_uploaded_file()
        
        # Display annotation interface if data is loaded
        if extraction_data:
            self._display_annotation_interface(extraction_data, file_name)
        else:
            st.info("Load extraction data to begin annotation")
    
    def _render_comparison_tab(self):
        """Render the comparison tab interface."""
        st.subheader("Compare Automatic vs. Manual Extractions")
        
        # File selection for comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### Automatic Extraction")
            auto_file = st.file_uploader(
                "Upload automatic extraction results",
                type=["json", "csv"],
                key="auto_extraction_upload"
            )
        
        with col2:
            st.markdown("##### Manual Extraction")
            manual_file = st.file_uploader(
                "Upload manual extraction results",
                type=["json", "csv"],
                key="manual_extraction_upload"
            )
        
        # If both files are uploaded
        if auto_file and manual_file:
            self._perform_comparison(auto_file, manual_file)
        else:
            st.info("Upload both automatic and manual extraction files to compare")
    
    def _load_recent_extraction(self) -> tuple[Optional[Dict], Optional[str]]:
        """
        Load extraction data from recent extraction files.
        
        Returns:
            tuple: (extraction_data, file_name) or (None, None) if no data
        """
        if not os.path.exists(self.output_dir):
            st.info("No output directory found. Run an extraction first or upload a file.")
            return None, None
        
        result_files = [
            f for f in os.listdir(self.output_dir) 
            if f.startswith("structured_") and f.endswith(".json")
        ]
        
        if not result_files:
            st.info("No recent extraction results found. Run an extraction first or upload a file.")
            return None, None
        
        result_files.sort(reverse=True)  # Newest first
        file_name = st.selectbox("Select extraction result:", result_files)
        
        if file_name:
            file_path = os.path.join(self.output_dir, file_name)
            extraction_data = load_extraction_results(file_path)
            if extraction_data:
                st.success(f"Loaded {file_name}")
                return extraction_data, file_name
            else:
                st.error(f"Failed to load {file_name}")
        
        return None, None
    
    def _load_uploaded_file(self) -> tuple[Optional[Dict], Optional[str]]:
        """
        Load extraction data from uploaded file.
        
        Returns:
            tuple: (extraction_data, file_name) or (None, None) if no data
        """
        uploaded_file = st.file_uploader(
            "Upload extraction results",
            type=["json", "csv"],
            key="annotation_file_upload"
        )
        
        if not uploaded_file:
            return None, None
        
        file_name = uploaded_file.name
        
        # Save uploaded file temporarily
        temp_path = os.path.join(self.temp_dir, file_name)
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Load the data
        extraction_data = load_extraction_results(temp_path)
        
        if extraction_data:
            st.success(f"Loaded {file_name}")
            return extraction_data, file_name
        else:
            st.error("Failed to load file. Make sure it's a valid JSON or CSV.")
            return None, None
    
    def _display_annotation_interface(self, extraction_data: Dict, file_name: str):
        """
        Display the annotation interface for editing extraction data.
        
        Args:
            extraction_data: The extraction data to annotate
            file_name: Name of the source file
        """
        # Determine if structured
        is_structured = isinstance(extraction_data, dict) and any(
            isinstance(v, dict) for v in extraction_data.values()
        )
        
        # Display annotation interface
        annotated_data = display_annotation_interface(extraction_data, is_structured)
        
        # Save annotations section
        self._render_save_annotations_section(annotated_data, file_name)
    
    def _render_save_annotations_section(self, annotated_data: Dict, file_name: str):
        """
        Render the save annotations section.
        
        Args:
            annotated_data: The annotated data to save
            file_name: Original file name for creating output name
        """
        st.subheader("Save Annotations")
        
        col1, col2 = st.columns(2)
        with col1:
            save_format = st.radio("Save format:", ["JSON", "CSV"], horizontal=True)
        
        with col2:
            save_suffix = st.text_input("Save suffix:", "annotated")
        
        if st.button("Save Annotations"):
            if file_name:
                self._save_annotations(annotated_data, file_name, save_suffix, save_format)
            else:
                st.error("No file name available for saving")
    
    def _save_annotations(self, annotated_data: Dict, file_name: str, suffix: str, format_type: str):
        """
        Save annotations to file and provide download.
        
        Args:
            annotated_data: The annotated data
            file_name: Original file name
            suffix: Suffix to add to output name
            format_type: Format type (JSON or CSV)
        """
        # Create a new file name
        base_name = file_name.split(".")[0]
        output_name = f"{base_name}_{suffix}.{format_type.lower()}"
        output_path = os.path.join(self.annotations_dir, output_name)
        
        # Save the annotations
        if save_annotations(annotated_data, output_path):
            st.success(f"Annotations saved to {output_path}")
            
            # Provide download button
            with open(output_path, "rb") as f:
                st.download_button(
                    label=f"Download {output_name}",
                    data=f,
                    file_name=output_name,
                    mime=f"application/{format_type.lower()}"
                )
        else:
            st.error("Failed to save annotations")
    
    def _perform_comparison(self, auto_file, manual_file):
        """
        Perform comparison between automatic and manual extractions.
        
        Args:
            auto_file: Uploaded automatic extraction file
            manual_file: Uploaded manual extraction file
        """
        # Save uploaded files temporarily
        auto_path = os.path.join(self.temp_dir, auto_file.name)
        manual_path = os.path.join(self.temp_dir, manual_file.name)
        
        with open(auto_path, "wb") as f:
            f.write(auto_file.getbuffer())
        
        with open(manual_path, "wb") as f:
            f.write(manual_file.getbuffer())
        
        # Load the data
        auto_data = load_extraction_results(auto_path)
        manual_data = load_extraction_results(manual_path)
        
        if auto_data and manual_data:
            self._display_comparison_results(auto_data, manual_data)
        else:
            st.error("Failed to load one or both files. Make sure they are valid JSON or CSV.")
    
    def _display_comparison_results(self, auto_data: Dict, manual_data: Dict):
        """
        Display comparison results and metrics.
        
        Args:
            auto_data: Automatic extraction data
            manual_data: Manual extraction data
        """
        # Compare the extractions
        comparison = compare_extractions(auto_data, manual_data)
        
        # Display metrics
        self._display_evaluation_metrics(comparison)
        
        # Display detailed differences
        self._display_detailed_differences(comparison)
        
        # Option to save comparison report
        self._render_save_comparison_section(comparison)
    
    def _display_evaluation_metrics(self, comparison: Dict):
        """
        Display evaluation metrics.
        
        Args:
            comparison: Comparison results dictionary
        """
        st.subheader("Evaluation Metrics")
        
        metrics = comparison.get("metrics", {})
        if metrics:
            metrics_cols = st.columns(3)
            with metrics_cols[0]:
                st.metric("Precision", f"{metrics.get('precision', 0):.2f}")
            with metrics_cols[1]:
                st.metric("Recall", f"{metrics.get('recall', 0):.2f}")
            with metrics_cols[2]:
                st.metric("F1 Score", f"{metrics.get('f1_score', 0):.2f}")
            
            st.text(f"True Positives: {metrics.get('true_positives', 0)}")
            st.text(f"False Positives: {metrics.get('false_positives', 0)}")
            st.text(f"False Negatives: {metrics.get('false_negatives', 0)}")
    
    def _display_detailed_differences(self, comparison: Dict):
        """
        Display detailed differences between extractions.
        
        Args:
            comparison: Comparison results dictionary
        """
        differences = comparison.get("differences", {})
        
        if differences:
            st.subheader("Detailed Differences")
            
            diff_tabs = st.tabs(["Different Values", "Only in Auto", "Only in Manual"])
            
            with diff_tabs[0]:
                self._display_different_values(differences.get("different_values", {}))
            
            with diff_tabs[1]:
                self._display_only_in_auto(differences.get("only_in_auto", {}))
            
            with diff_tabs[2]:
                self._display_only_in_manual(differences.get("only_in_manual", {}))
    
    def _display_different_values(self, different_values: Dict):
        """Display values that differ between extractions."""
        if different_values:
            for key, vals in different_values.items():
                st.markdown(f"**{key}:**")
                cols = st.columns(2)
                with cols[0]:
                    st.info(f"Auto: {vals.get('auto', '')}")
                with cols[1]:
                    st.success(f"Manual: {vals.get('manual', '')}")
        else:
            st.info("No value differences found")
    
    def _display_only_in_auto(self, auto_only: Dict):
        """Display items found only in automatic extraction."""
        if auto_only:
            for key, value in auto_only.items():
                st.markdown(f"**{key}:** {value}")
        else:
            st.info("No items found only in automatic extraction")
    
    def _display_only_in_manual(self, manual_only: Dict):
        """Display items found only in manual extraction."""
        if manual_only:
            for key, value in manual_only.items():
                st.markdown(f"**{key}:** {value}")
        else:
            st.info("No items found only in manual extraction")
    
    def _render_save_comparison_section(self, comparison: Dict):
        """
        Render the save comparison report section.
        
        Args:
            comparison: Comparison results dictionary
        """
        if st.button("Save Comparison Report"):
            report_path = os.path.join(
                self.reports_dir, 
                f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            )
            
            with open(report_path, 'w') as f:
                json.dump(comparison, f, indent=2)
                
            st.success(f"Comparison report saved to {report_path}")
            
            # Provide download button
            with open(report_path, "rb") as f:
                st.download_button(
                    label="Download Comparison Report",
                    data=f,
                    file_name=f"comparison_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )