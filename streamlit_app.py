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
from datetime import datetime
from src.utils.prompt_override import get_extraction_prompt_with_version
from src.pdf_processor import extract_text_from_pdf, chunk_text
from src.utils import DataExtractor, TemplateSystem, Analytics, ConfigManager
from src.data_export import save_to_csv, save_extraction_results_to_csv
from src.utils.display_utils import display_structured_results
from src.utils.annotation_utils import display_annotation_interface, load_extraction_results, save_annotations, compare_extractions
from src.utils.prompt_templates import PromptTemplate

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

def safe_display_results(results):
    """Wrapper for display_structured_results that handles mixed data types and errors"""
    try:
        return display_structured_results(results)
    except Exception as e:
        # Log the full error details for debugging
        logger.error(f"Error in display_structured_results: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Show error to user with more helpful context
        st.error(f"Could not display structured results: {str(e)}")
        st.info("Displaying simplified version of the extracted data")
        
        # Initialize a more organized data structure
        combined_data = {}
        
        for result in results:
            try:
                # First attempt to parse as JSON if it looks like JSON
                extraction_text = result['extraction']
                if '{' in extraction_text and '}' in extraction_text:
                    json_start = extraction_text.find('{')
                    json_end = extraction_text.rfind('}') + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        try:
                            json_str = extraction_text[json_start:json_end]
                            json_data = json.loads(json_str)
                            # Merge JSON data into combined data
                            for key, value in json_data.items():
                                # Handle nested structures
                                if isinstance(value, dict):
                                    # Flatten one level of nesting with prefixes
                                    for sub_key, sub_value in value.items():
                                        combined_data[f"{key}.{sub_key}"] = sub_value
                                elif isinstance(value, list):
                                    # Convert lists to comma-separated string
                                    combined_data[key] = ", ".join(str(item) for item in value)
                                else:
                                    combined_data[key] = value
                            continue  # Skip to next result if JSON parsing succeeded
                        except json.JSONDecodeError:
                            # JSON parsing failed, proceed with line-by-line parsing
                            pass
                
                # Fallback to line-by-line parsing
                lines = extraction_text.strip().split('\n')
                for line in lines:
                    if ':' in line:
                        try:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip()
                            # Skip empty values or very short keys
                            if value and len(key) > 1:
                                combined_data[key] = value
                        except Exception:
                            # Skip problematic lines
                            pass
            except Exception as chunk_error:
                # Log but continue processing other chunks
                logger.warning(f"Error processing chunk {result.get('chunk_index')}: {str(chunk_error)}")
        
        # Display as simple expander sections with better organization
        st.write("### Simplified Extraction Results")
        
        if not combined_data:
            st.warning("No structured data could be extracted. Please check the raw view.")
        else:
            # Display total items count
            st.info(f"Found {len(combined_data)} extracted items")
            
            # Group items by common prefixes if possible
            grouped_data = {}
            ungrouped = {}
            
            for key, value in combined_data.items():
                # Try to find category prefixes (e.g., "demographics.age")
                if '.' in key:
                    category, subkey = key.split('.', 1)
                    if category not in grouped_data:
                        grouped_data[category] = {}
                    grouped_data[category][subkey] = value
                else:
                    ungrouped[key] = value
            
            # Display grouped data first
            for category, items in grouped_data.items():
                with st.expander(f"{category.title()} ({len(items)} items)", expanded=True):
                    for key, value in items.items():
                        st.markdown(f"**{key}:** {value}")
            
            # Then display ungrouped data
            if ungrouped:
                with st.expander(f"Other Extracted Items ({len(ungrouped)} items)", expanded=True):
                    for key, value in ungrouped.items():
                        st.markdown(f"**{key}:** {value}")
        
        return combined_data

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add at the top of your app after importing dependencies
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'view_type' not in st.session_state:
    st.session_state.view_type = "Structured"
if 'current_file' not in st.session_state:
    st.session_state.current_file = None
if 'chunk_results' not in st.session_state:
    st.session_state.chunk_results = []
if 'results_df' not in st.session_state:
    st.session_state.results_df = None
if 'extracted_text' not in st.session_state:
    st.session_state.extracted_text = ""

# Load configuration
config = ConfigManager()

# Make sure the prompt templates are initialized
template_system = TemplateSystem()

# Initialize analytics system
analytics = Analytics()

if 'view_type' not in st.session_state:
    st.session_state.view_type = "Structured"

# App title and description
st.title("Research Article Data Extractor")

# Navigation
page = st.sidebar.selectbox("Navigate", ["Extract Data", "Manual Annotation", "Analytics Dashboard"])

if page == "Extract Data":
    st.markdown("""
    This application extracts patient characteristic data from medical research articles.
    Upload a PDF of a research article to get started.
    """)

    # LLM provider selection
    provider = st.sidebar.selectbox(
        "LLM Provider",
        ["anthropic", "openai", "mock"],  # Added mock for testing without API
        index=0
    )

    # Model selection (will be dynamically populated based on provider)
    if provider == "anthropic":
        models = ["claude-3-sonnet-20240229", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
    elif provider == "openai":
        models = ["gpt-3.5-turbo", "gpt-4o", "gpt-4-1106-preview"]
    else:  # mock
        models = ["mock-model"]

    model = st.sidebar.selectbox("Model", models)

    # Advanced settings expander
    with st.sidebar.expander("Advanced Settings"):
        # Chunk size
        chunk_size = st.number_input(
            "Chunk Size (chars)", 
            min_value=500, 
            max_value=10000, 
            value=config.get('pdf_processor.text_chunking.chunk_size', 1000)
        )
        
        # Chunk overlap
        overlap = st.number_input(
            "Chunk Overlap (chars)", 
            min_value=0, 
            max_value=500, 
            value=config.get('pdf_processor.text_chunking.overlap', 100)
        )
        
        # Temperature setting
        temperature = st.slider(
            "Temperature", 
            min_value=0.0, 
            max_value=1.0, 
            value=config.get('llm.temperature', 0.0), 
            step=0.1
        )
        
        # Prompt version selection
        versions = template_system.list_versions('patient_characteristics')
        if versions:
            prompt_version = st.selectbox("Prompt Version", versions, index=len(versions)-1)
        else:
            prompt_version = "default"
        
        # Custom characteristics
        use_custom = st.checkbox("Define Custom Characteristics")
        custom_chars = []
        if use_custom:
            custom_chars_text = st.text_area("Enter characteristics (one per line)")
            if custom_chars_text:
                custom_chars = [line.strip() for line in custom_chars_text.split('\n') if line.strip()]

        st.markdown("---")
        st.markdown("### Development Options")
        st.session_state.development_mode = st.checkbox(
            "Development Mode", 
            value=st.session_state.get('development_mode', False),
            help="Show detailed extraction results by chunk"
        )
        st.session_state.include_chunks = st.checkbox(
            "Include chunks in CSV", 
            value=st.session_state.get('include_chunks', False),
            help="Include individual chunk data in CSV export"
        )

    # File uploader
    uploaded_file = st.file_uploader("Upload a research article PDF", type="pdf")

    # Process the uploaded file
    if uploaded_file is not None:
        # Save the uploaded file temporarily
        temp_path = f"data/input/temp_{uploaded_file.name}"
        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"File {uploaded_file.name} uploaded successfully!")
        
        # Extract text
        with st.spinner("Extracting text from PDF..."):
            text = extract_text_from_pdf(temp_path)
            st.info(f"Extracted {len(text)} characters of text")
    
        if 'processing_complete' not in st.session_state:
            st.session_state.processing_complete = False
        if 'view_type' not in st.session_state:
            st.session_state.view_type = "Structured"

        # Process button
        if st.button("Process Article", key="process_article_button", disabled=st.session_state.processing_complete) or st.session_state.processing_complete:
            # Only do the processing part if we haven't completed it yet
            if not st.session_state.processing_complete:
                # Check for API key (skip for mock provider)
                api_key_env_var = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
                if provider != "mock" and not os.environ.get(api_key_env_var):
                    st.error(f"Please set the {api_key_env_var} environment variable before processing.")
                else:
                    # Set state variables
                    st.session_state.processing_complete = True
                    st.session_state.uploaded_file_name = uploaded_file.name
                
                    # Chunk the text
                    with st.spinner("Chunking text..."):
                        chunks = chunk_text(
                            text, 
                            chunk_size=chunk_size, 
                            overlap=overlap, 
                            respect_paragraphs=config.get('pdf_processor.text_chunking.respect_paragraphs', True)
                        )
                        st.session_state.chunks = chunks  # Store chunks in session state
                        st.info(f"Created {len(chunks)} text chunks")
                    
                    # Initialize extractor
                    with st.spinner("Initializing AI model..."):
                        extractor = DataExtractor(provider=provider, model_name=model)
                    
                    # Process chunks
                    progress_bar = st.progress(0)
                    chunk_results = []
                    
                    with st.spinner("Extracting data from chunks..."):
                        for i, chunk in enumerate(chunks):
                            # Update progress
                            progress = (i + 1) / len(chunks)
                            progress_bar.progress(progress)
                            
                            # Extract data from chunk
                            start_time = datetime.now()
                            
                            # Select appropriate prompt
                            if use_custom and custom_chars:
                                prompt_id = 'custom_patient_characteristics'
                                # Use the imported function designed for custom prompts
                                prompt = get_extraction_prompt_with_version(
                                    chunk['content'],
                                    custom_characteristics=custom_chars,
                                    version=None  # or whatever version parameter is appropriate
                                )
                            else:
                                prompt_id = 'patient_characteristics'
                                prompt = get_extraction_prompt_with_version(
                                    chunk['content'], 
                                    version=prompt_version if prompt_version != "default" else None
                                )
                            
                            # Generate completion
                            try:
                                completion = extractor.client.generate_completion(
                                    prompt, 
                                    temperature=temperature
                                )

                                # Basic completion validation - make sure we actually got a response
                                if not completion or not isinstance(completion, str):
                                    st.warning(f"Warning: Chunk {i+1} returned an invalid response format. Skipping...")
                                    # Log in analytics
                                    analytics.log_extraction(
                                        template_id=prompt_id,
                                        version_id=prompt_version if prompt_version != "default" else "latest",
                                        source_file=uploaded_file.name,
                                        characteristics_found=0,
                                        start_time=start_time,
                                        end_time=datetime.now(),
                                        success=False,
                                        error="Invalid response format",
                                        metadata={
                                            'provider': provider,
                                            'model': model,
                                            'chunk_index': chunk['index'],
                                            'temperature': temperature,
                                            'text_chunk_length': len(chunk['content'])
                                        }  
                                    )
                                    continue  # Skip to next chunk

                                # Calculate end time
                                end_time = datetime.now()

                                # Track in analytics using the unified Analytics system
                                analytics.log_extraction(
                                    template_id=prompt_id,
                                    version_id=prompt_version if prompt_version != "default" else "latest",
                                    source_file=uploaded_file.name,
                                    characteristics_found=len(completion.split('\n')),  # Rough estimate
                                    start_time=start_time,
                                    end_time=end_time,
                                    success=True,
                                    metadata={
                                        'provider': provider,
                                        'model': model,
                                        'chunk_index': chunk['index'],
                                        'temperature': temperature,
                                        'text_chunk_length': len(chunk['content'])
                                    }
                                )

                                # Add to results
                                chunk_results.append({
                                    'chunk_index': chunk['index'],
                                    'extraction': completion
                                })

                            except Exception as e:
                                st.error(f"Error processing chunk {i+1}: {str(e)}")
                                logger.error(f"Chunk processing error: {str(e)}")
                                # Log error in analytics
                                analytics.log_extraction(
                                    template_id=prompt_id,
                                    version_id=prompt_version if prompt_version != "default" else "latest",
                                    source_file=uploaded_file.name,
                                    characteristics_found=0,
                                    start_time=start_time,
                                    end_time=datetime.now(),
                                    success=False,
                                    error=str(e),
                                    metadata={
                                        'provider': provider,
                                        'model': model,
                                        'chunk_index': chunk['index'],
                                        'temperature': temperature,
                                        'text_chunk_length': len(chunk['content'])
                                    }
                                )
                    
                    # Store results in session state
                    if 'chunk_results' not in st.session_state:
                        st.session_state.chunk_results = []
                    st.session_state.chunk_results = chunk_results    

            else:
                # Retrieve stored values if processing was already done
                chunk_results = st.session_state.chunk_results
                uploaded_file_name = st.session_state.uploaded_file_name
                if 'results_df' in st.session_state:
                    df = st.session_state.results_df
                else:
                    # Recreate dataframe if needed
                    df = pd.DataFrame([
                        {'chunk': item['chunk_index'], 'extraction': item['extraction']} 
                        for item in st.session_state.chunk_results
                    ])
                    st.session_state.results_df = df

            # This section is outside both the if and else blocks but still within the outer if
            with st.spinner("Compiling results..."):
                # Save raw results
                raw_output_path = f"data/output/raw_{st.session_state.uploaded_file_name.replace('.pdf', '.csv')}"
                os.makedirs(os.path.dirname(raw_output_path), exist_ok=True)

                # Convert to DataFrame for display and saving
                if 'results_df' not in st.session_state or st.session_state.results_df is None:
                    st.session_state.results_df = pd.DataFrame([
                        {'chunk': item['chunk_index'], 'extraction': item['extraction']} 
                        for item in st.session_state.chunk_results
                    ])

                # Save results to CSV
                save_extraction_results_to_csv(
                    st.session_state.chunk_results, 
                    raw_output_path,
                    include_chunks=st.session_state.get('include_chunks', False)
                )

                st.info("""
                The CSV file now contains a 'combined' row at the top that intelligently merges data from all chunks.
                Different values for the same field are combined with '|' separators.
                The individual chunk data follows the combined row for reference.
                """)

                # Show structured results
                st.subheader("Extraction Results")

                # Option to toggle between raw and structured view
                view_type = st.radio(
                    "View Format", 
                    ["Structured", "Raw Data"], 
                    index=0 if st.session_state.view_type == "Structured" else 1,
                    horizontal=True,
                    key='view_type_radio'
                )
                st.session_state.view_type = view_type

                if view_type == "Structured":
                    # Use our display function for structured display
                    combined_data = display_structured_results(
                        st.session_state.chunk_results, 
                        development_mode=st.session_state.get('development_mode', False)
                    )

                    # Save structured results
                    structured_output_path = f"data/output/structured_{st.session_state.uploaded_file_name.replace('.pdf', '.json')}"
                    os.makedirs(os.path.dirname(structured_output_path), exist_ok=True)
                    with open(structured_output_path, 'w') as f:
                        json.dump(combined_data, f, indent=2)
            
                    # Add download button for structured results
                    with open(structured_output_path, 'rb') as f:
                        st.download_button(
                            label="Download Structured Results as JSON",
                            data=f,
                            file_name=f"structured_{st.session_state.uploaded_file_name.replace('.pdf', '.json')}",
                            mime="application/json"
                        )
                else:
                    # Show traditional raw view
                    st.dataframe(st.session_state.results_df)

                # Original CSV download button (keep this for backward compatibility)
                with open(raw_output_path, 'rb') as f:
                    st.download_button(
                        label="Download as CSV (with Merged Data)",
                        data=f,
                        file_name=f"extracted_data_{st.session_state.uploaded_file_name.replace('.pdf', '.csv')}",
                        mime="text/csv"
                    )

                if st.button("Process New File", key="reset_button"):
                    # Reset all session state variables
                    st.session_state.processing_complete = False
                    st.session_state.view_type = "Structured"
                    st.session_state.uploaded_file_name = None
                    st.session_state.chunk_results = []
                    st.session_state.results_df = None
                    st.session_state.chunks = []
                    # Any other session state variables that need to be reset
    
                    # Trigger a rerun to refresh the page
                    st.rerun()

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