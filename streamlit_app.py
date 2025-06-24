# File: streamlit_app.py

"""
Streamlit application for Research Data Extractor with Analytics Dashboard
"""
import os
import time
import streamlit as st
import logging
import pandas as pd
import json
import matplotlib.pyplot as plt
import tempfile
from datetime import datetime
from src.utils.prompt_override import get_extraction_prompt_with_version
from src.pdf_processor import extract_text_from_pdf, chunk_text
from src.utils.zip_processor import ZipProcessor
from src.utils import DataExtractor, TemplateSystem, Analytics, ConfigManager
from src.data_export import save_to_csv, save_extraction_results_to_csv
from src.utils.display_utils import display_structured_results
from src.utils.annotation_utils import display_annotation_interface, load_extraction_results, save_annotations, compare_extractions
from src.utils.prompt_templates import PromptTemplate
from src.utils.picots_parser import PicotsParser

# Import foundation and processing modules
from src.app import SessionStateManager, FileHandlerUtils, ConfigurationLoader
from src.processing import DocumentProcessor, ExtractionEngine, BatchCoordinator

# Import UI components and pages
from src.ui import ExtractionPage, BatchPage

def get_extraction_prompt_with_version(text, custom_characteristics=None, version=None):
    """
    Get extraction prompt with version support and optional custom characteristics
    
    Args:
        text (str): The text to extract from
        custom_characteristics (list, optional): List of specific characteristics to extract
        version (str, optional): Version of the template to use
    
    Returns:
        str: The formatted prompt
    """
    if custom_characteristics:
        return PromptTemplate.custom_extraction_prompt(text, custom_characteristics)
    else:
        return PromptTemplate.get_extraction_prompt(text, version=version)

def display_results(results):
    """Display extraction results with simple error handling"""
    try:
        return display_structured_results(results)
    except Exception as e:
        logger.error(f"Error displaying structured results: {str(e)}")
        st.error("Error displaying structured results. Showing raw data instead.")
        
        # Simple fallback: show raw results
        st.subheader("Raw Extraction Results")
        for i, result in enumerate(results):
            with st.expander(f"Chunk {i+1} Results"):
                st.text(result.get('extraction', 'No data'))
        return {}

# Initialize configuration loader and setup logging
config_loader = ConfigurationLoader.create_default_loader()
logger = logging.getLogger(__name__)

# Initialize all session state using the new manager
SessionStateManager.initialize_all_state()

# Load configuration systems using the new loader
init_result = config_loader.initialize_all()
config = init_result['config_manager']
template_system = init_result['template_system']
analytics = init_result['analytics']

# Initialize processing modules
document_processor = DocumentProcessor(config.config)
extraction_engine = ExtractionEngine(config.config, analytics)
batch_coordinator = BatchCoordinator(config.config)

# Show initialization errors if any
if init_result['errors']:
    for error in init_result['errors']:
        st.error(f"Configuration Error: {error}")
    st.warning("Some features may not work properly due to configuration errors.")

# App title and description
st.title("Research Article Data Extractor")

# Navigation
page = st.sidebar.selectbox("Navigate", ["Extract Data", "Batch Processing", "Manual Annotation", "Analytics Dashboard"])

if page == "Extract Data":
    # Use the new extraction page component
    extraction_page = ExtractionPage(extraction_engine, document_processor, config)
    extraction_page.render()

elif page == "Batch Processing":
    # Use the new batch processing page component
    batch_page = BatchPage(extraction_engine, document_processor, batch_coordinator, config)
    batch_page.render()

elif page == "Manual Annotation":
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
        # Option to load extraction results
        load_option = st.radio(
            "Load extraction data from:",
            ["Recent Extraction", "File Upload"],
            horizontal=True
        )
        
        extraction_data = None
        file_name = None
        
        if load_option == "Recent Extraction":
            # List recent extraction files
            output_dir = "data/output"
            if os.path.exists(output_dir):
                result_files = [f for f in os.listdir(output_dir) if f.startswith("structured_") and f.endswith(".json")]
                
                if result_files:
                    result_files.sort(reverse=True)  # Newest first
                    file_name = st.selectbox("Select extraction result:", result_files)
                    
                    if file_name:
                        file_path = os.path.join(output_dir, file_name)
                        extraction_data = load_extraction_results(file_path)
                        st.success(f"Loaded {file_name}")
                else:
                    st.info("No recent extraction results found. Run an extraction first or upload a file.")
            else:
                st.info("No output directory found. Run an extraction first or upload a file.")
                
        else:  # File Upload
            uploaded_file = st.file_uploader(
                "Upload extraction results",
                type=["json", "csv"],
                key="annotation_file_upload"
            )
            
            if uploaded_file:
                file_name = uploaded_file.name
                
                # Save uploaded file temporarily
                temp_path = f"data/temp/{file_name}"
                os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Load the data
                extraction_data = load_extraction_results(temp_path)
                
                if extraction_data:
                    st.success(f"Loaded {file_name}")
                else:
                    st.error("Failed to load file. Make sure it's a valid JSON or CSV.")
        
        # Display annotation interface if data is loaded
        if extraction_data:
            # Determine if structured
            is_structured = isinstance(extraction_data, dict) and any(isinstance(v, dict) for v in extraction_data.values())
            
            # Display annotation interface
            annotated_data = display_annotation_interface(extraction_data, is_structured)
            
            # Save annotations
            col1, col2 = st.columns(2)
            with col1:
                save_format = st.radio("Save format:", ["JSON", "CSV"], horizontal=True)
            
            with col2:
                save_suffix = st.text_input("Save suffix:", "annotated")
            
            if st.button("Save Annotations"):
                if file_name:
                    # Create a new file name
                    base_name = file_name.split(".")[0]
                    output_name = f"{base_name}_{save_suffix}.{save_format.lower()}"
                    output_path = os.path.join("data/annotations", output_name)
                    
                    # Save the annotations
                    if save_annotations(annotated_data, output_path):
                        st.success(f"Annotations saved to {output_path}")
                        
                        # Provide download button
                        with open(output_path, "rb") as f:
                            st.download_button(
                                label=f"Download {output_name}",
                                data=f,
                                file_name=output_name,
                                mime=f"application/{save_format.lower()}"
                            )
                    else:
                        st.error("Failed to save annotations")
                else:
                    st.error("No file name available for saving")
        else:
            st.info("Load extraction data to begin annotation")
    
    with compare_tab:
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
            # Save uploaded files temporarily
            auto_path = f"data/temp/{auto_file.name}"
            manual_path = f"data/temp/{manual_file.name}"
            
            os.makedirs(os.path.dirname(auto_path), exist_ok=True)
            
            with open(auto_path, "wb") as f:
                f.write(auto_file.getbuffer())
            
            with open(manual_path, "wb") as f:
                f.write(manual_file.getbuffer())
            
            # Load the data
            auto_data = load_extraction_results(auto_path)
            manual_data = load_extraction_results(manual_path)
            
            if auto_data and manual_data:
                # Compare the extractions
                comparison = compare_extractions(auto_data, manual_data)
                
                # Display metrics
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
                    
                    # Display detailed differences
                    differences = comparison.get("differences", {})
                    
                    if differences:
                        st.subheader("Detailed Differences")
                        
                        diff_tabs = st.tabs(["Different Values", "Only in Auto", "Only in Manual"])
                        
                        with diff_tabs[0]:
                            different = differences.get("different_values", {})
                            if different:
                                for key, vals in different.items():
                                    st.markdown(f"**{key}:**")
                                    cols = st.columns(2)
                                    with cols[0]:
                                        st.info(f"Auto: {vals.get('auto', '')}")
                                    with cols[1]:
                                        st.success(f"Manual: {vals.get('manual', '')}")
                            else:
                                st.info("No value differences found")
                        
                        with diff_tabs[1]:
                            auto_only = differences.get("only_in_auto", {})
                            if auto_only:
                                for key, value in auto_only.items():
                                    st.markdown(f"**{key}:** {value}")
                            else:
                                st.info("No items found only in automatic extraction")
                        
                        with diff_tabs[2]:
                            manual_only = differences.get("only_in_manual", {})
                            if manual_only:
                                for key, value in manual_only.items():
                                    st.markdown(f"**{key}:** {value}")
                            else:
                                st.info("No items found only in manual extraction")
                        
                        # Option to save comparison report
                        if st.button("Save Comparison Report"):
                            report_path = f"data/reports/comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                            os.makedirs(os.path.dirname(report_path), exist_ok=True)
                            
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
                else:
                    st.error("Failed to compute comparison metrics")
            else:
                st.error("Failed to load one or both files. Make sure they are valid JSON or CSV.")
        else:
            st.info("Upload both automatic and manual extraction files to compare")

elif page == "Analytics Dashboard":
    st.header("Analytics Dashboard")
    
    # Time period selection
    time_period = st.selectbox(
        "Time Period",
        [7, 30, 90, 365],
        index=1,
        format_func=lambda x: f"Last {x} days"
    )
    
    # Generate report using the unified Analytics system
    report = analytics.generate_report(days=time_period)
    
    # Summary metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Extractions", report['stats']['count'])
    
    with col2:
        st.metric("Avg. Duration (ms)", f"{report['stats']['avg_duration_ms']:.1f}")
    
    with col3:
        st.metric("Success Rate", f"{report['stats']['success_rate'] * 100:.1f}%")
    
    # Charts
    if report['time_series']['dates']:
        st.subheader("Extraction Activity")
        
        # Convert to DataFrame for plotting
        time_df = pd.DataFrame({
            'date': pd.to_datetime(report['time_series']['dates']),
            'count': report['time_series']['counts'],
            'success_rate': report['time_series']['success_rates']
        })
        
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
    else:
        st.info("No extraction data available for the selected time period.")

    # Model performance comparison
    if report['stats']['models']:
        st.subheader("Model Performance")
        
        model_data = []
        for model_name, stats in report['stats']['models'].items():
            model_data.append({
                'model': model_name,
                'count': stats['count'],
                'success_rate': stats['success_rate'],
                'avg_time': 0  # Would need to calculate this from raw data
            })
        
        model_df = pd.DataFrame(model_data)
        st.dataframe(model_df)
    
    # Prompt performance comparison
    if report['stats']['prompts']:
        st.subheader("Prompt Performance")
        
        prompt_data = []
        for prompt_id, stats in report['stats']['prompts'].items():
            prompt_data.append({
                'prompt_id': prompt_id,
                'count': stats['count'],
                'success_rate': stats['success_rate']
            })
        
        prompt_df = pd.DataFrame(prompt_data)
        st.dataframe(prompt_df)
    
    # Raw analytics data (for debugging)
    with st.expander("Raw Analytics Data"):
        st.json(report)

# Run the app properly if executed directly
if __name__ == "__main__":
    import sys
    
    # Check if running with streamlit or directly with python
    if not any('streamlit' in arg for arg in sys.argv):
        import subprocess
        
        # Get the current script path
        script_path = os.path.abspath(__file__)
        
        # Run streamlit with this script
        print("Launching Streamlit application...")
        subprocess.call(["streamlit", "run", script_path])