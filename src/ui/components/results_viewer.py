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
    
    @staticmethod
    def create_enhanced_batch_download(
        structured_results: List[Dict[str, Any]],
        filename_base: str,
        picots_enhanced: bool = False
    ) -> None:
        """
        Create enhanced download section for batch results with PICOTS-aware formatting.
        
        Args:
            structured_results: Structured batch results data
            filename_base: Base filename for downloads
            picots_enhanced: Whether PICOTS criteria were used
        """
        if not structured_results:
            st.warning("No results to download")
            return
        
        # Create enhanced DataFrame with better column organization
        df = pd.DataFrame(structured_results)
        
        # Reorder columns for better CSV structure
        base_columns = ['source_file', 'chunk_index']
        metadata_columns = ['processing_time', 'chunk_count', 'character_count', 'successful_chunks', 'failed_chunks']
        
        # PICOTS-specific columns if available
        picots_columns = [col for col in df.columns if col.startswith('extracted_')]
        picots_flag_columns = [col for col in df.columns if 'picots' in col.lower()]
        
        # Main content column
        content_columns = ['extraction_text']
        
        # Reorder columns for logical flow
        ordered_columns = base_columns + picots_columns + picots_flag_columns + content_columns + metadata_columns
        
        # Only include columns that exist in the DataFrame
        final_columns = [col for col in ordered_columns if col in df.columns]
        df = df[final_columns]
        
        # Create download buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Enhanced CSV with structured columns
            csv_data = df.to_csv(index=False)
            
            filename_suffix = "_picots_enhanced" if picots_enhanced else "_standard"
            
            st.download_button(
                label="📊 Download Enhanced CSV",
                data=csv_data,
                file_name=f"{filename_base}{filename_suffix}.csv",
                mime="text/csv",
                help="CSV with structured columns and PICOTS-aware organization"
            )
        
        with col2:
            # JSON export
            json_data = df.to_json(orient='records', indent=2)
            
            st.download_button(
                label="📋 Download JSON",
                data=json_data,
                file_name=f"{filename_base}{filename_suffix}.json",
                mime="application/json",
                help="JSON format with full structured data"
            )
        
        with col3:
            # Summary statistics CSV
            summary_df = ResultsDownloadComponent._create_batch_summary_csv(structured_results, picots_enhanced)
            summary_csv = summary_df.to_csv(index=False)
            
            st.download_button(
                label="📈 Download Summary",
                data=summary_csv,
                file_name=f"{filename_base}_summary{filename_suffix}.csv",
                mime="text/csv",
                help="Summary statistics and metadata across all files"
            )
        
        # Display column information
        with st.expander("📋 CSV Column Information", expanded=False):
            st.write("**File Information:**")
            st.write("- `source_file`: Original filename")
            st.write("- `chunk_index`: Text chunk number within file")
            
            if picots_columns:
                st.write("**PICOTS-Extracted Fields:**")
                for col in picots_columns:
                    field_name = col.replace('extracted_', '').replace('_', ' ').title()
                    st.write(f"- `{col}`: {field_name}")
            
            st.write("**Content:**")
            st.write("- `extraction_text`: Full extracted text")
            
            st.write("**Processing Metadata:**")
            st.write("- `processing_time`: When extraction was completed")
            st.write("- `chunk_count`: Total chunks in file")
            st.write("- `character_count`: Total characters processed")
    
    @staticmethod
    def _create_batch_summary_csv(
        structured_results: List[Dict[str, Any]], 
        picots_enhanced: bool = False
    ) -> pd.DataFrame:
        """
        Create summary CSV with aggregate statistics.
        
        Args:
            structured_results: Structured batch results data
            picots_enhanced: Whether PICOTS criteria were used
            
        Returns:
            DataFrame with summary statistics
        """
        # Group by source file
        files_summary = {}
        
        for result in structured_results:
            filename = result.get('source_file', 'unknown')
            
            if filename not in files_summary:
                files_summary[filename] = {
                    'filename': filename,
                    'total_chunks': 0,
                    'total_characters': result.get('character_count', 0),
                    'successful_chunks': result.get('successful_chunks', 0),
                    'failed_chunks': result.get('failed_chunks', 0),
                    'picots_enhanced': picots_enhanced,
                    'extracted_fields_count': 0
                }
            
            # Count extracted fields (PICOTS-structured data)
            extracted_fields = sum(1 for key in result.keys() if key.startswith('extracted_'))
            files_summary[filename]['extracted_fields_count'] = max(
                files_summary[filename]['extracted_fields_count'], 
                extracted_fields
            )
            files_summary[filename]['total_chunks'] += 1
        
        # Calculate success rates
        for file_data in files_summary.values():
            total_chunks = file_data['successful_chunks'] + file_data['failed_chunks']
            file_data['success_rate'] = (
                file_data['successful_chunks'] / total_chunks if total_chunks > 0 else 0
            )
        
        return pd.DataFrame(list(files_summary.values()))


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
        Create a complete batch results display section with enhanced PICOTS-aware CSV export.
        
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
        
        # Enhanced download section for batch results with PICOTS support
        if show_download:
            # Check if PICOTS was used
            picots_enhanced = any(
                result.get('metadata', {}).get('picots_enhanced', False) 
                for result in batch_results
            )
            
            # Combine all successful results with enhanced structure
            structured_results = ResultsDisplaySection._create_structured_batch_data(
                batch_results, 
                picots_enhanced=picots_enhanced
            )
            
            if structured_results:
                st.subheader("💾 Download Enhanced Results")
                
                # Show PICOTS enhancement status
                if picots_enhanced:
                    st.info("🎯 **PICOTS-Enhanced Export**: Results include targeted extraction based on your research criteria")
                
                # Enhanced download options
                ResultsDownloadComponent.create_enhanced_batch_download(
                    structured_results,
                    "batch_extraction_results",
                    picots_enhanced=picots_enhanced
                )
    
    @staticmethod
    def _create_structured_batch_data(
        batch_results: List[Dict[str, Any]], 
        picots_enhanced: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Create structured data for batch export with PICOTS awareness.
        
        Args:
            batch_results: List of batch processing results
            picots_enhanced: Whether PICOTS criteria were used
            
        Returns:
            Structured data suitable for CSV export
        """
        structured_data = []
        
        for result in batch_results:
            if result.get('status') == 'success':
                file_results = result.get('results', [])
                filename = result.get('filename', 'unknown')
                metadata = result.get('metadata', {})
                
                for item in file_results:
                    # Base structure
                    row_data = {
                        'source_file': filename,
                        'chunk_index': item.get('chunk_index', 0),
                        'extraction_text': item.get('extraction', ''),
                        'processing_time': metadata.get('processing_time', ''),
                        'picots_enhanced': picots_enhanced
                    }
                    
                    # Add metadata
                    if metadata:
                        row_data.update({
                            'chunk_count': metadata.get('chunk_count', 0),
                            'character_count': metadata.get('character_count', 0),
                            'successful_chunks': metadata.get('successful_chunks', 0),
                            'failed_chunks': metadata.get('failed_chunks', 0)
                        })
                    
                    # Try to parse structured extraction if available
                    try:
                        extraction_text = item.get('extraction', '')
                        if extraction_text:
                            # Parse into structured fields for better CSV organization
                            parsed_data = ResultsDisplaySection._parse_extraction_for_csv(
                                extraction_text, picots_enhanced
                            )
                            row_data.update(parsed_data)
                    except Exception:
                        # Fallback to raw text if parsing fails
                        pass
                    
                    structured_data.append(row_data)
        
        return structured_data
    
    @staticmethod
    def _parse_extraction_for_csv(extraction_text: str, picots_enhanced: bool = False) -> Dict[str, Any]:
        """
        Parse extraction text into structured fields for CSV export.
        
        Args:
            extraction_text: Raw extraction text
            picots_enhanced: Whether PICOTS criteria were used
            
        Returns:
            Dictionary of parsed fields
        """
        parsed_fields = {}
        
        # Common patterns to extract
        field_patterns = {
            'population': ['population', 'participants', 'subjects', 'patients'],
            'intervention': ['intervention', 'treatment', 'therapy', 'medication'],
            'comparison': ['comparison', 'control', 'placebo', 'comparator'],
            'outcomes': ['outcomes', 'results', 'endpoints', 'measures'],
            'timing': ['timing', 'duration', 'follow-up', 'period'],
            'setting': ['setting', 'location', 'context', 'environment'],
            'sample_size': ['sample size', 'n =', 'participants', 'subjects'],
            'age': ['age', 'years old', 'mean age'],
            'gender': ['gender', 'sex', 'male', 'female'],
            'conditions': ['condition', 'disease', 'diagnosis', 'disorder']
        }
        
        # Simple text parsing - look for key information
        lines = extraction_text.lower().split('\n')
        
        for field, keywords in field_patterns.items():
            field_value = ""
            for line in lines:
                for keyword in keywords:
                    if keyword in line:
                        # Extract the line containing the keyword
                        field_value = line.strip()
                        break
                if field_value:
                    break
            
            # Clean up and store
            if field_value:
                parsed_fields[f'extracted_{field}'] = field_value[:200]  # Limit length
        
        # Add PICOTS-specific fields if enhanced
        if picots_enhanced:
            parsed_fields['picots_structured'] = True
            # Could add more PICOTS-specific parsing here
        
        return parsed_fields


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