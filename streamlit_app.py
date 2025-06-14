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
page = st.sidebar.selectbox("Navigate", ["Extract Data", "Batch Processing", "Manual Annotation", "Analytics Dashboard"])

if page == "Extract Data":
    st.markdown("""
    This application extracts patient characteristic data from medical research articles.
    Upload a PDF of a research article to get started.
    """)

    # LLM provider selection  
    if 'provider' not in st.session_state:
        st.session_state.provider = "anthropic"

    st.session_state.provider = st.sidebar.selectbox(
        "LLM Provider", 
        ["anthropic", "openai", "mock"],
        index=["anthropic", "openai", "mock"].index(st.session_state.provider)
    )

    # Model selection (will be dynamically populated based on provider)
    if st.session_state.provider == "anthropic":
        models = ["claude-3-sonnet-20240229", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
    elif st.session_state.provider == "openai":
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


    # File uploader
    uploaded_file = st.file_uploader("Upload a research article PDF", type="pdf")
    # PICOTS criteria input (replace the file upload section)
    st.markdown("---")
    st.subheader("📊 PICOTS Criteria (Optional)")
    st.markdown("Paste your PICOTS criteria below to customize the extraction focus.")
    
    # Create expandable section for PICOTS input
    with st.expander("📋 What is PICOTS?", expanded=False):
        st.markdown("""
        **PICOTS** helps focus research extraction:
        - **P**opulation: Who are the study participants?
        - **I**ntervention: What treatment/exposure is being studied?
        - **C**omparison: What is the control or comparison group?
        - **O**utcomes: What outcomes are being measured?
        - **T**iming: What is the timeframe?
        - **S**etting: Where is the study conducted?
        """)
    
    # Text area for PICOTS input
    picots_text = st.text_area(
        "Paste your PICOTS criteria here:",
        height=200,
        placeholder="""Example format:
        Population: Adults aged 18-65 with type 2 diabetes
        Intervention: Metformin therapy
        Comparison: Placebo or standard care
        Outcomes: HbA1c reduction, weight loss, adverse events
        Timing: 12-week treatment period
        Setting: Outpatient clinics

        Abbreviations: HbA1c = Hemoglobin A1c; BMI = Body Mass Index""",
    help="Copy and paste your PICOTS criteria from your protocol document. Including abbreviations helps improve extraction accuracy!"
)

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

        # Process PICOTS if provided
        picots_data = None
        if picots_text.strip():
            try:
                # Initialize parser and parse the PICOTS text
                parser = PicotsParser()
                picots_data = parser.parse_picots_table(picots_text.strip())
                
                st.success("✅ PICOTS criteria parsed successfully!")
                
                # Display parsed data for verification
                with st.expander("🔍 View Parsed PICOTS Data", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if picots_data.population:
                            st.write("**Population:**")
                            for item in picots_data.population:
                                st.write(f"• {item}")
                        
                        if picots_data.interventions:
                            st.write("**Interventions:**")
                            for item in picots_data.interventions:
                                st.write(f"• {item}")
                                
                        if picots_data.comparators:
                            st.write("**Comparators:**")
                            for item in picots_data.comparators:
                                st.write(f"• {item}")
                    
                    with col2:
                        if picots_data.outcomes:
                            st.write("**Outcomes:**")
                            for item in picots_data.outcomes:
                                st.write(f"• {item}")
                                
                        if picots_data.timing:
                            st.write("**Timing:**")
                            for item in picots_data.timing:
                                st.write(f"• {item}")
                                
                        if picots_data.setting:
                            st.write("**Setting:**")
                            for item in picots_data.setting:
                                st.write(f"• {item}")
                    
                    # Show detected KQs if any
                    if picots_data.detected_kqs:
                        st.write("**Detected Key Questions:**")
                        for kq in picots_data.detected_kqs:
                            st.write(f"• {kq}")

                    # Show abbreviations if any
                    if picots_data.abbreviations:
                        st.write("**Abbreviations:**")
                        for abbrev, full_name in picots_data.abbreviations.items():
                            st.write(f"• {abbrev} = {full_name}")
                            
            except Exception as e:
                st.error(f"Error parsing PICOTS data: {str(e)}")
                picots_data = {"raw_text": picots_text.strip()}
        
        st.markdown("---")

        # Fixed: proper indentation for session state initialization
        if 'processing_complete' not in st.session_state:
            st.session_state.processing_complete = False
        if 'view_type' not in st.session_state:
            st.session_state.view_type = "Structured"

        if st.button("Process Article", key="process_article_button", disabled=st.session_state.processing_complete) or st.session_state.processing_complete:

            # Only do the processing part if we haven't completed it yet
            if not st.session_state.processing_complete:
                        
                # Check for API key (skip for mock provider)
                api_key_env_var = "ANTHROPIC_API_KEY" if st.session_state.provider == "anthropic" else "OPENAI_API_KEY"
                if st.session_state.provider != "mock" and not os.environ.get(api_key_env_var):
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
                        st.session_state.chunks = chunks
                        st.info(f"Created {len(chunks)} text chunks")
                        
                        # Initialize extractor
                        with st.spinner("Initializing AI model..."):
                            extractor = DataExtractor(provider=st.session_state.provider, model_name=model)
                        
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
                                
                                # Select appropriate prompt with PICOTS context
                                if use_custom and custom_chars:
                                    prompt_id = 'custom_patient_characteristics'
                                    prompt = get_extraction_prompt_with_version(
                                        chunk['content'],
                                        custom_characteristics=custom_chars,
                                        version=None
                                    )
                                else:
                                    prompt_id = 'comprehensive_research'
                                    # Use new comprehensive template with PICOTS context
                                    from src.utils.prompt_templates import PromptTemplate
        
                                    # Convert PicotsData object to dictionary format for template
                                    picots_context = None
                                    if picots_data:
                                        picots_context = {
                                            'picots_sections': {
                                                'population': picots_data.population,
                                                'interventions': picots_data.interventions,
                                                'comparators': picots_data.comparators,
                                                'outcomes': picots_data.outcomes,
                                                'timing': picots_data.timing,
                                                'setting': picots_data.setting
                                            },
                                            'key_questions': picots_data.detected_kqs,
                                            'abbreviations': picots_data.abbreviations
                                        }
        
                                    prompt = PromptTemplate.get_extraction_prompt(
                                        chunk['content'], 
                                        picots_context=picots_context
                                    )
                                
                                # Generate completion
                                try:
                                    completion = extractor.client.generate_completion(
                                        prompt, 
                                        temperature=temperature
                                    )

                                    # Basic completion validation
                                    if not completion or not isinstance(completion, str):
                                        st.warning(f"Warning: Chunk {i+1} returned an invalid response format. Skipping...")
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
                                            'provider': st.session_state.provider,
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
                                            'provider': st.session_state.provider,
                                            'model': st.session_state.batch_model,
                                            'chunk_index': chunk['index'],
                                            'temperature': st.session_state.batch_temperature,
                                            'text_chunk_length': len(chunk['content'])
                                        }
                                    )
                            
                            # Store results in session state (this should be OUTSIDE the for loop)
                            st.session_state.chunk_results = chunk_results
                        
            else:
                # Retrieve stored values if processing was already done            
                chunk_results = st.session_state.chunk_results
                
            # Display results section (this should be OUTSIDE the processing_complete check)
            if st.session_state.processing_complete and 'chunk_results' in st.session_state:
                
                # Add your results display code here
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
                        include_chunks=False
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
                            st.session_state.chunk_results
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

elif page == "Batch Processing":
    st.header("🔄 Batch Processing")
    
    st.markdown("""
    Process multiple research articles at once. Upload multiple PDF files or a ZIP archive 
    containing PDFs to extract patient characteristics from all articles simultaneously.
    """)
    
    # Initialize session state for batch processing
    if 'batch_files' not in st.session_state:
        st.session_state.batch_files = []
    if 'batch_processing_complete' not in st.session_state:
        st.session_state.batch_processing_complete = False
    if 'batch_results' not in st.session_state:
        st.session_state.batch_results = []
    
    # Provider and model selection (same as single processing)
    col1, col2 = st.columns(2)
    with col1:
        if 'batch_provider' not in st.session_state:
            st.session_state.batch_provider = "anthropic"
        
        st.session_state.batch_provider = st.selectbox(
            "LLM Provider",
            ["anthropic", "openai", "mock"],
            index=["anthropic", "openai", "mock"].index(st.session_state.batch_provider),
            key="batch_provider_select"
        )

    with col2:
        if st.session_state.batch_provider == "anthropic":
            models = ["claude-3-sonnet-20240229", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
        elif st.session_state.batch_provider == "openai":
            models = ["gpt-3.5-turbo", "gpt-4o", "gpt-4-1106-preview"]
        else:  # mock
            models = ["mock-model"]
        
        if 'batch_model' not in st.session_state:
            st.session_state.batch_model = models[0]
        
        st.session_state.batch_model = st.selectbox("Model", models, key="batch_model_select")
    
    # File upload section
    st.markdown("---")
    st.subheader("📁 Upload Files")
    
    upload_method = st.radio(
        "Upload Method:",
        ["Multiple PDF Files", "ZIP Archive"],
        horizontal=True
    )
    
    if upload_method == "Multiple PDF Files":
        uploaded_files = st.file_uploader(
            "Select PDF files",
            type="pdf",
            accept_multiple_files=True,
            key="batch_pdf_upload"
        )
        
        if uploaded_files:
            st.success(f"Selected {len(uploaded_files)} PDF files")
            # Display file list
            with st.expander("📋 Selected Files", expanded=True):
                for i, file in enumerate(uploaded_files, 1):
                    st.write(f"{i}. {file.name}")
            
            st.session_state.batch_files = uploaded_files
    
    else:  # ZIP Archive
        uploaded_zip = st.file_uploader(
            "Select ZIP archive containing PDFs",
            type="zip",
            key="batch_zip_upload"
        )
        
        if uploaded_zip:
            # Initialize ZIP processor
            zip_processor = ZipProcessor(max_files=50, max_file_size_mb=100)
            
            # Validate ZIP file first
            with st.spinner("Validating ZIP archive..."):
                is_valid, validation_errors, zip_info = zip_processor.validate_zip_file(uploaded_zip.getvalue())
            
            if is_valid:
                st.success(f"✅ Valid ZIP archive found!")
                
                # Display ZIP file information
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Files", zip_info['total_files'])
                with col2:
                    st.metric("PDF Files", zip_info['pdf_files'])
                with col3:
                    st.metric("Total Size", f"{zip_info['total_size'] / (1024*1024):.1f} MB")
                
                # Show PDF file list
                with st.expander("📋 PDF Files Found", expanded=True):
                    for i, pdf_name in enumerate(zip_info['pdf_file_names'], 1):
                        st.write(f"{i}. {pdf_name}")
                
                # Extract files button
                if st.button("Extract PDF Files", key="extract_zip_button"):
                    with st.spinner("Extracting PDF files from ZIP archive..."):
                        # Create temporary directory for this session
                        if 'zip_temp_dir' not in st.session_state:
                            st.session_state.zip_temp_dir = tempfile.mkdtemp()
                        
                        # Extract files
                        extracted_files, extract_errors = zip_processor.extract_pdfs_from_zip(
                            uploaded_zip.getvalue(), 
                            st.session_state.zip_temp_dir
                        )
                        
                        if extracted_files:
                            st.success(f"✅ Successfully extracted {len(extracted_files)} PDF files!")
                            
                            # Convert extracted files to file-like objects for compatibility
                            file_objects = []
                            for file_info in extracted_files:
                                # Create a simple file-like object with the necessary attributes
                                class FileObject:
                                    def __init__(self, name, path):
                                        self.name = name
                                        self.path = path
                                        with open(path, 'rb') as f:
                                            self._content = f.read()
                                    
                                    def getbuffer(self):
                                        return self._content
                                
                                file_objects.append(FileObject(file_info['name'], file_info['path']))
                            
                            # Store in session state for batch processing
                            st.session_state.batch_files = file_objects
                            
                            # Display success message
                            st.info("Files extracted and ready for batch processing. Scroll down to start processing.")
                            
                        if extract_errors:
                            st.warning("⚠️ Some issues occurred during extraction:")
                            for error in extract_errors:
                                st.write(f"• {error}")
                        
                        if not extracted_files and extract_errors:
                            st.error("❌ Failed to extract any PDF files from the ZIP archive.")
            
            else:
                st.error("❌ ZIP archive validation failed:")
                for error in validation_errors:
                    st.write(f"• {error}")

    # Initialize batch processing settings in session state
    if 'batch_chunk_size' not in st.session_state:
        st.session_state.batch_chunk_size = 1000
    if 'batch_overlap' not in st.session_state:
        st.session_state.batch_overlap = 100
    if 'batch_temperature' not in st.session_state:
        st.session_state.batch_temperature = 0.0
    if 'batch_continue_on_error' not in st.session_state:
        st.session_state.batch_continue_on_error = True
    if 'batch_save_individual' not in st.session_state:
        st.session_state.batch_save_individual = True
    if 'batch_max_concurrent' not in st.session_state:
        st.session_state.batch_max_concurrent = "Sequential (1 at a time)"
              
    
    # Batch Processing Settings
    with st.expander("⚙️ Batch Processing Settings"):
        settings_col1, settings_col2 = st.columns(2)
        
        with settings_col1:
            # Chunk settings
            st.number_input(
                "Chunk Size (chars)", 
                min_value=500, 
                max_value=10000, 
                value=st.session_state.batch_chunk_size,
                key="batch_chunk_size"
            )

            st.number_input(
                "Chunk Overlap (chars)", 
                min_value=0, 
                max_value=500, 
                value=st.session_state.batch_overlap,
                key="batch_overlap"
            )

            # Temperature setting
            st.slider(
                "Temperature", 
                min_value=0.0, 
                max_value=1.0, 
                value=st.session_state.batch_temperature, 
                step=0.1,
                key="batch_temperature"
            )
        
        with settings_col2:
            # Processing options
            st.checkbox(
                "Continue processing if a file fails", 
                value=st.session_state.batch_continue_on_error,
                help="If checked, batch processing will continue even if individual files fail",
                key="batch_continue_on_error"
            )
            
            st.checkbox(
                "Save individual file results", 
                value=st.session_state.batch_save_individual,
                help="Save separate result files for each processed PDF",
                key="batch_save_individual"
            )
            
            st.selectbox(
                "Processing Mode",
                ["Sequential (1 at a time)", "Limited Parallel (3 at a time)", "Full Parallel"],
                index=["Sequential (1 at a time)", "Limited Parallel (3 at a time)", "Full Parallel"].index(st.session_state.batch_max_concurrent),
                help="Sequential is safer for API rate limits",
                key="batch_max_concurrent"
            )
    
    # Processing section
    if st.session_state.batch_files:
        st.markdown("---")
        st.subheader("🚀 Process Batch")
        
        # Show batch summary
        st.info(f"Ready to process {len(st.session_state.batch_files)} PDF files")
        
        if st.button("Start Batch Processing", disabled=st.session_state.batch_processing_complete):
            # Initialize batch processing
            st.session_state.batch_processing_complete = False
            
            # Check for API key (skip for mock provider)
            api_key_env_var = "ANTHROPIC_API_KEY" if st.session_state.batch_provider == "anthropic" else "OPENAI_API_KEY"
            if st.session_state.batch_provider != "mock" and not os.environ.get(api_key_env_var):
                st.error(f"Please set the {api_key_env_var} environment variable before processing.")
            else:
                # Initialize extractor
                with st.spinner("Initializing AI model..."):
                    batch_extractor = DataExtractor(provider=st.session_state.batch_provider, model_name=st.session_state.batch_model)
                
                # Initialize results storage
                batch_results = []
                failed_files = []
                
                # Create progress containers
                overall_progress = st.progress(0)
                status_text = st.empty()
                current_file_text = st.empty()
                
                # Process each file
                for file_idx, file_obj in enumerate(st.session_state.batch_files):
                    try:
                        # Update progress
                        progress = file_idx / len(st.session_state.batch_files)
                        overall_progress.progress(progress)
                        status_text.text(f"Processing file {file_idx + 1} of {len(st.session_state.batch_files)}")
                        current_file_text.text(f"Current file: {file_obj.name}")
                        
                        # Save file temporarily
                        temp_path = f"data/input/batch_temp_{file_obj.name}"
                        os.makedirs(os.path.dirname(temp_path), exist_ok=True)
                        
                        with open(temp_path, "wb") as f:
                            f.write(file_obj.getbuffer())
                        
                        # Extract text from PDF
                        text = extract_text_from_pdf(temp_path)
                        
                        if not text.strip():
                            raise ValueError("No text could be extracted from PDF")
                        
                        # Chunk the text
                        chunks = chunk_text(
                            text, 
                            chunk_size=st.session_state.batch_chunk_size, 
                            overlap=st.session_state.batch_overlap, 
                            respect_paragraphs=True
                        )
                        
                        # Process chunks
                        file_results = []
                        for chunk in chunks:
                            # Track extraction timing
                            chunk_start_time = datetime.now()
                            
                            # Use the same prompt as single processing
                            prompt = PromptTemplate.get_extraction_prompt(chunk['content'])
                            
                            completion = batch_extractor.client.generate_completion(
                                prompt, 
                                temperature=st.session_state.batch_temperature
                            )
                            
                            chunk_end_time = datetime.now()
                            
                            # Log analytics for this chunk
                            analytics.log_extraction(
                                template_id='comprehensive_research',
                                version_id='batch_processing',
                                source_file=file_obj.name,
                                characteristics_found=len(completion.split('\n')),  # Rough estimate
                                start_time=chunk_start_time,
                                end_time=chunk_end_time,
                                success=True,
                                metadata={
                                    'provider': st.session_state.batch_provider,
                                    'model': st.session_state.batch_model,
                                    'chunk_index': chunk['index'],
                                    'temperature': st.session_state.batch_temperature,
                                    'text_chunk_length': len(chunk['content']),
                                    'processing_type': 'batch',
                                    'batch_file_count': len(st.session_state.batch_files)
                                }
                            )
                            
                            file_results.append({
                                'chunk_index': chunk['index'],
                                'extraction': completion
                            })
                                            
                        # Store results
                        batch_results.append({
                            'file_name': file_obj.name,
                            'status': 'success',
                            'chunks_processed': len(file_results),
                            'results': file_results,
                            'text_length': len(text)
                        })
                        
                        # Clean up temp file
                        os.unlink(temp_path)
                        
                    except Exception as e:
                        error_msg = str(e)
                        failed_files.append({
                            'file_name': file_obj.name,
                            'error': error_msg
                        })

                        # Log failed extraction
                        analytics.log_extraction(
                            template_id='comprehensive_research',
                            version_id='batch_processing',
                            source_file=file_obj.name,
                            characteristics_found=0,
                            start_time=datetime.now(),
                            end_time=datetime.now(),
                            success=False,
                            error=error_msg,
                            metadata={
                                'provider': st.session_state.batch_provider,
                                'model': st.session_state.batch_model,
                                'processing_type': 'batch',
                                'batch_file_count': len(st.session_state.batch_files)
                            }
                        )

                        batch_results.append({
                            'file_name': file_obj.name,
                            'status': 'failed',
                            'error': error_msg,
                            'chunks_processed': 0,
                            'results': []
                        })
                        
                        # Clean up temp file if it exists
                        temp_path = f"data/input/batch_temp_{file_obj.name}"
                        if os.path.exists(temp_path):
                            os.unlink(temp_path)
                        
                        # Continue or stop based on settings
                        if not st.session_state.batch_continue_on_error:
                            st.error(f"Processing stopped due to error in {file_obj.name}: {error_msg}")
                            break
                        else:
                            st.warning(f"Error processing {file_obj.name}: {error_msg}")
                
                # Complete processing
                overall_progress.progress(1.0)
                status_text.text("Batch processing complete!")
                current_file_text.text("")
                
                # Store results in session state
                st.session_state.batch_results = batch_results
                st.session_state.batch_processing_complete = True
                
                # Show summary
                successful_files = len([r for r in batch_results if r['status'] == 'success'])
                st.success(f"✅ Batch processing complete! {successful_files}/{len(st.session_state.batch_files)} files processed successfully.")
                
                if failed_files:
                    with st.expander("❌ Failed Files", expanded=False):
                        for failed in failed_files:
                            st.write(f"• **{failed['file_name']}**: {failed['error']}")
        
        # Results section
    if st.session_state.batch_processing_complete:
        st.markdown("---")
        st.subheader("📊 Batch Results")
        
        # Summary metrics
        total_files = len(st.session_state.batch_results)
        successful_files = len([r for r in st.session_state.batch_results if r['status'] == 'success'])
        failed_files = total_files - successful_files
        total_chunks = sum(r.get('chunks_processed', 0) for r in st.session_state.batch_results)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Files", total_files)
        with col2:
            st.metric("Successful", successful_files, delta=f"{successful_files/total_files*100:.0f}%")
        with col3:
            st.metric("Failed", failed_files, delta=f"-{failed_files/total_files*100:.0f}%" if failed_files > 0 else "0%")
        with col4:
            st.metric("Total Chunks", total_chunks)
        
        # Results tabs
        results_tab, download_tab, details_tab = st.tabs(["📋 Results Summary", "💾 Downloads", "🔍 Detailed Results"])
        
        with results_tab:
            # Show results summary table
            summary_data = []
            for result in st.session_state.batch_results:
                summary_data.append({
                    'File Name': result['file_name'],
                    'Status': '✅ Success' if result['status'] == 'success' else '❌ Failed',
                    'Chunks Processed': result.get('chunks_processed', 0),
                    'Text Length': f"{result.get('text_length', 0):,} chars" if result.get('text_length') else 'N/A',
                    'Error': result.get('error', '') if result['status'] == 'failed' else ''
                })
            
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, use_container_width=True)
        
        with download_tab:
            st.markdown("### 📥 Download Options")
            
            # Combined results download
            if st.button("📊 Generate Combined Results"):
                with st.spinner("Generating combined results..."):
                    # Create combined results file
                    combined_results = []
                    
                    for result in st.session_state.batch_results:
                        if result['status'] == 'success':
                            for chunk_result in result['results']:
                                combined_results.append({
                                    'source_file': result['file_name'],
                                    'chunk_index': chunk_result['chunk_index'],
                                    'extraction': chunk_result['extraction']
                                })
                    
                    # Save combined results
                    combined_output_path = f"data/output/batch_combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    os.makedirs(os.path.dirname(combined_output_path), exist_ok=True)
                    
                    save_extraction_results_to_csv(
                        combined_results,
                        combined_output_path,
                        include_chunks=True
                    )
                    
                    st.success("Combined results generated!")
                    
                    # Download button
                    with open(combined_output_path, 'rb') as f:
                        st.download_button(
                            label="📥 Download Combined Results CSV",
                            data=f,
                            file_name=f"batch_results_combined_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
            
            # Individual file downloads
            if st.session_state.batch_save_individual:
                st.markdown("### 📄 Individual File Results")
                
                for result in st.session_state.batch_results:
                    if result['status'] == 'success':
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{result['file_name']}** ({result['chunks_processed']} chunks)")
                        with col2:
                            # Create individual file result
                            individual_output_path = f"data/output/batch_{result['file_name'].replace('.pdf', '.csv')}"
                            os.makedirs(os.path.dirname(individual_output_path), exist_ok=True)
                            
                            save_extraction_results_to_csv(
                                result['results'],
                                individual_output_path,
                                include_chunks=False
                            )
                            
                            with open(individual_output_path, 'rb') as f:
                                st.download_button(
                                    label="📥 Download",
                                    data=f,
                                    file_name=f"{result['file_name'].replace('.pdf', '_results.csv')}",
                                    mime="text/csv",
                                    key=f"download_{result['file_name']}"
                                )
        
        with details_tab:
            st.markdown("### 🔍 Detailed Extraction Results")
            
            # File selector
            file_names = [r['file_name'] for r in st.session_state.batch_results if r['status'] == 'success']
            if file_names:
                selected_file = st.selectbox("Select file to view detailed results:", file_names)
                
                # Find the selected result
                selected_result = next(r for r in st.session_state.batch_results if r['file_name'] == selected_file)
                
                # Display detailed results using the same function as single file processing
                if selected_result['results']:
                    try:
                        combined_data = display_structured_results(selected_result['results'])
                    except Exception as e:
                        st.error(f"Error displaying structured results: {str(e)}")
                        # Fallback to raw display
                        st.subheader("Raw Extraction Results")
                        for i, chunk_result in enumerate(selected_result['results']):
                            with st.expander(f"Chunk {i+1} Results"):
                                st.text(chunk_result['extraction'])
            else:
                st.info("No successful extractions to display.")
        
        # Reset button
        if st.button("🔄 Process New Batch", key="reset_batch_button"):
            # Reset batch processing session state
            st.session_state.batch_processing_complete = False
            st.session_state.batch_files = []
            st.session_state.batch_results = []
            if 'zip_temp_dir' in st.session_state:
                # Clean up temporary directory
                import shutil
                try:
                    shutil.rmtree(st.session_state.zip_temp_dir)
                except:
                    pass
                del st.session_state.zip_temp_dir
            
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