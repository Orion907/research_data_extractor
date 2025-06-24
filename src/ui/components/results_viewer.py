"""
Results Viewer Component

Reusable components for displaying extraction results in various formats.
"""

import streamlit as st
import pandas as pd
import json
import os
from typing import Optional, List, Dict, Any, Union
from pathlib import Path


class ResultsViewerComponent:
    """Reusable component for displaying extraction results."""
    
    @staticmethod
    def display_view_type_selector(
        default_view: str = "Structured",
        key: str = "results_view_type"
    ) -> str:
        """
        Display view type selector for results.
        
        Args:
            default_view: Default view type
            key: Unique key for the selector
            
        Returns:
            Selected view type
        """
        return st.radio(
            "View Format",
            ["Structured", "Raw Data", "JSON"],
            index=["Structured", "Raw Data", "JSON"].index(default_view),
            horizontal=True,
            key=key
        )
    
    @staticmethod
    def display_structured_results(
        extraction_results: List[Dict[str, Any]],
        development_mode: bool = False,
        show_categories_expanded: bool = True
    ) -> Dict[str, Any]:
        """
        Display extraction results in structured format.
        
        Args:
            extraction_results: List of extraction results by chunk
            development_mode: Whether to show detailed extraction by chunk
            show_categories_expanded: Whether to expand category sections
            
        Returns:
            Combined structured data from all chunks
        """
        try:
            from src.utils.display_utils import display_structured_results
            return display_structured_results(extraction_results, development_mode)
        except ImportError:
            st.error("Display utilities not available")
            return {}
    
    @staticmethod
    def display_raw_results(extraction_results: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Display extraction results in raw DataFrame format.
        
        Args:
            extraction_results: List of extraction results by chunk
            
        Returns:
            DataFrame containing raw results
        """
        # Convert to DataFrame
        results_df = pd.DataFrame([
            {
                'chunk': item['chunk_index'],
                'extraction': item['extraction']
            } 
            for item in extraction_results
        ])
        
        # Display the DataFrame
        st.dataframe(results_df, use_container_width=True)
        
        return results_df
    
    @staticmethod
    def display_json_results(extraction_results: List[Dict[str, Any]]) -> None:
        """
        Display extraction results in JSON format.
        
        Args:
            extraction_results: List of extraction results by chunk
        """
        st.subheader("JSON Results")
        
        # Option to show individual chunks or combined
        display_type = st.radio(
            "JSON Display Type",
            ["Combined", "By Chunk"],
            horizontal=True,
            key="json_display_type"
        )
        
        if display_type == "Combined":
            # Combine all extractions
            combined_results = {
                "source": "combined_extraction",
                "total_chunks": len(extraction_results),
                "extractions": [item['extraction'] for item in extraction_results]
            }
            
            st.json(combined_results)
        else:
            # Show each chunk separately
            for item in extraction_results:
                with st.expander(f"Chunk {item['chunk_index'] + 1}"):
                    chunk_data = {
                        "chunk_index": item['chunk_index'],
                        "extraction": item['extraction']
                    }
                    st.json(chunk_data)
    
    @staticmethod
    def display_batch_results_summary(
        batch_results: List[Dict[str, Any]],
        show_details: bool = False
    ) -> None:
        """
        Display summary of batch processing results.
        
        Args:
            batch_results: List of batch processing results
            show_details: Whether to show detailed results for each file
        """
        st.subheader("📊 Batch Processing Summary")
        
        # Summary statistics
        total_files = len(batch_results)
        successful_files = sum(1 for result in batch_results if result.get('status') == 'success')
        failed_files = total_files - successful_files
        
        # Display summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Files", total_files)
        
        with col2:
            st.metric("Successful", successful_files, delta=None)
        
        with col3:
            st.metric("Failed", failed_files, delta=None)
        
        # Progress bar
        success_rate = successful_files / total_files if total_files > 0 else 0
        st.progress(success_rate, text=f"Success Rate: {success_rate:.1%}")
        
        # Detailed results
        if show_details:
            st.subheader("📋 Detailed Results")
            
            for i, result in enumerate(batch_results):
                filename = result.get('filename', f'File {i+1}')
                status = result.get('status', 'unknown')
                
                if status == 'success':
                    icon = "✅"
                    color = "normal"
                elif status == 'error':
                    icon = "❌"
                    color = "normal"
                else:
                    icon = "⚠️"
                    color = "normal"
                
                with st.expander(f"{icon} {filename}"):
                    if status == 'success':
                        extraction_results = result.get('results', [])
                        if extraction_results:
                            ResultsViewerComponent.display_structured_results(
                                extraction_results,
                                development_mode=False,
                                show_categories_expanded=False
                            )
                        else:
                            st.info("No extraction results available")
                    else:
                        error_message = result.get('error', 'Unknown error')
                        st.error(f"Processing failed: {error_message}")


class ResultsDownloadComponent:
    """Component for handling results downloads."""
    
    @staticmethod
    def create_download_section(
        results_data: Union[Dict, List, pd.DataFrame],
        filename_base: str,
        formats: List[str] = ["CSV", "JSON"]
    ) -> None:
        """
        Create download section with multiple format options.
        
        Args:
            results_data: Data to be downloaded
            filename_base: Base filename (without extension)
            formats: List of formats to offer ("CSV", "JSON", "TXT")
        """
        st.subheader("💾 Download Results")
        
        # Create download buttons for each format
        col_count = len(formats)
        cols = st.columns(col_count)
        
        for i, format_type in enumerate(formats):
            with cols[i]:
                if format_type == "CSV":
                    ResultsDownloadComponent._create_csv_download(results_data, filename_base)
                elif format_type == "JSON":
                    ResultsDownloadComponent._create_json_download(results_data, filename_base)
                elif format_type == "TXT":
                    ResultsDownloadComponent._create_txt_download(results_data, filename_base)
    
    @staticmethod
    def _create_csv_download(results_data: Any, filename_base: str) -> None:
        """Create CSV download button."""
        try:
            # Convert to DataFrame if not already
            if isinstance(results_data, pd.DataFrame):
                df = results_data
            elif isinstance(results_data, list):
                df = pd.DataFrame(results_data)
            elif isinstance(results_data, dict):
                # Flatten dictionary for CSV
                flattened = []
                for key, value in results_data.items():
                    if isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            flattened.append({
                                'Category': key,
                                'Field': subkey,
                                'Value': str(subvalue)
                            })
                    else:
                        flattened.append({
                            'Category': 'General',
                            'Field': key,
                            'Value': str(value)
                        })
                df = pd.DataFrame(flattened)
            else:
                st.error("Cannot convert data to CSV format")
                return
            
            csv_data = df.to_csv(index=False)
            
            st.download_button(
                label="📄 Download CSV",
                data=csv_data,
                file_name=f"{filename_base}.csv",
                mime="text/csv"
            )
            
        except Exception as e:
            st.error(f"Error creating CSV download: {str(e)}")
    
    @staticmethod
    def _create_json_download(results_data: Any, filename_base: str) -> None:
        """Create JSON download button."""
        try:
            # Convert to JSON string
            if isinstance(results_data, (dict, list)):
                json_data = json.dumps(results_data, indent=2, ensure_ascii=False)
            elif isinstance(results_data, pd.DataFrame):
                json_data = results_data.to_json(orient='records', indent=2)
            else:
                json_data = json.dumps({"data": str(results_data)}, indent=2)
            
            st.download_button(
                label="📋 Download JSON",
                data=json_data,
                file_name=f"{filename_base}.json",
                mime="application/json"
            )
            
        except Exception as e:
            st.error(f"Error creating JSON download: {str(e)}")
    
    @staticmethod
    def _create_txt_download(results_data: Any, filename_base: str) -> None:
        """Create TXT download button."""
        try:
            # Convert to text format
            if isinstance(results_data, dict):
                txt_lines = []
                for key, value in results_data.items():
                    txt_lines.append(f"=== {key} ===")
                    if isinstance(value, dict):
                        for subkey, subvalue in value.items():
                            txt_lines.append(f"{subkey}: {subvalue}")
                    else:
                        txt_lines.append(str(value))
                    txt_lines.append("")
                txt_data = "\n".join(txt_lines)
            elif isinstance(results_data, list):
                txt_data = "\n".join(str(item) for item in results_data)
            else:
                txt_data = str(results_data)
            
            st.download_button(
                label="📝 Download TXT",
                data=txt_data,
                file_name=f"{filename_base}.txt",
                mime="text/plain"
            )
            
        except Exception as e:
            st.error(f"Error creating TXT download: {str(e)}")


class ResultsDisplaySection:
    """High-level component that combines results viewing and downloading."""
    
    @staticmethod
    def create_results_section(
        extraction_results: List[Dict[str, Any]],
        filename: str,
        show_download: bool = True,
        development_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Create a complete results display section.
        
        Args:
            extraction_results: List of extraction results
            filename: Source filename
            show_download: Whether to show download options
            development_mode: Whether to enable development features
            
        Returns:
            Structured results data
        """
        if not extraction_results:
            st.warning("No extraction results to display")
            return {}
        
        st.subheader("📊 Extraction Results")
        
        # View type selector
        view_type = ResultsViewerComponent.display_view_type_selector()
        
        # Display results based on selected view
        structured_data = {}
        
        if view_type == "Structured":
            structured_data = ResultsViewerComponent.display_structured_results(
                extraction_results,
                development_mode=development_mode,
                show_categories_expanded=True
            )
        elif view_type == "Raw Data":
            results_df = ResultsViewerComponent.display_raw_results(extraction_results)
            structured_data = results_df.to_dict('records')
        elif view_type == "JSON":
            ResultsViewerComponent.display_json_results(extraction_results)
            structured_data = {
                "extraction_results": extraction_results
            }
        
        # Download section
        if show_download and structured_data:
            filename_base = filename.replace('.pdf', '') if filename.endswith('.pdf') else filename
            
            ResultsDownloadComponent.create_download_section(
                structured_data,
                f"extracted_data_{filename_base}",
                formats=["CSV", "JSON", "TXT"]
            )
        
        return structured_data
    
    @staticmethod
    def create_batch_results_section(
        batch_results: List[Dict[str, Any]],
        show_download: bool = True
    ) -> None:
        """
        Create a complete batch results display section.
        
        Args:
            batch_results: List of batch processing results
            show_download: Whether to show download options
        """
        if not batch_results:
            st.warning("No batch results to display")
            return
        
        # Display batch summary
        ResultsViewerComponent.display_batch_results_summary(
            batch_results,
            show_details=True
        )
        
        # Download section for batch results
        if show_download:
            # Combine all successful results
            all_results = []
            for result in batch_results:
                if result.get('status') == 'success':
                    file_results = result.get('results', [])
                    for item in file_results:
                        item['source_file'] = result.get('filename', 'unknown')
                        all_results.append(item)
            
            if all_results:
                ResultsDownloadComponent.create_download_section(
                    all_results,
                    "batch_extraction_results",
                    formats=["CSV", "JSON"]
                )


class ResultsComparisonComponent:
    """Component for comparing extraction results."""
    
    @staticmethod
    def compare_extractions(
        results1: List[Dict[str, Any]],
        results2: List[Dict[str, Any]],
        label1: str = "Results 1",
        label2: str = "Results 2"
    ) -> None:
        """
        Compare two sets of extraction results.
        
        Args:
            results1: First set of extraction results
            results2: Second set of extraction results
            label1: Label for first results
            label2: Label for second results
        """
        st.subheader("🔍 Results Comparison")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**{label1}**")
            structured1 = ResultsViewerComponent.display_structured_results(
                results1,
                development_mode=False,
                show_categories_expanded=False
            )
        
        with col2:
            st.write(f"**{label2}**")
            structured2 = ResultsViewerComponent.display_structured_results(
                results2,
                development_mode=False,
                show_categories_expanded=False
            )
        
        # Show differences
        st.subheader("📋 Differences")
        
        # Compare categories
        all_categories = set(structured1.keys()) | set(structured2.keys())
        
        for category in sorted(all_categories):
            items1 = structured1.get(category, {})
            items2 = structured2.get(category, {})
            
            # Find differences
            only_in_1 = set(items1.keys()) - set(items2.keys())
            only_in_2 = set(items2.keys()) - set(items1.keys())
            common = set(items1.keys()) & set(items2.keys())
            
            if only_in_1 or only_in_2 or any(items1.get(k) != items2.get(k) for k in common):
                with st.expander(f"📊 {category} Differences"):
                    if only_in_1:
                        st.write(f"**Only in {label1}:**")
                        for item in only_in_1:
                            st.write(f"• {item}: {items1[item]}")
                    
                    if only_in_2:
                        st.write(f"**Only in {label2}:**")
                        for item in only_in_2:
                            st.write(f"• {item}: {items2[item]}")
                    
                    # Check for different values
                    different_values = [k for k in common if items1.get(k) != items2.get(k)]
                    if different_values:
                        st.write("**Different values:**")
                        for item in different_values:
                            st.write(f"• **{item}:**")
                            st.write(f"  - {label1}: {items1[item]}")
                            st.write(f"  - {label2}: {items2[item]}")