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
from src.pdf_processor import extract_text_from_pdf, chunk_text
from src.utils import DataExtractor, PromptTemplate
from src.data_export.csv_exporter import save_to_csv
from src.utils.analytics_tracker import AnalyticsTracker

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Make sure the prompt templates are initialized
PromptTemplate.initialize()

# Initialize analytics tracker
analytics = AnalyticsTracker()

# App title and description
st.title("Research Article Data Extractor")

# Navigation
page = st.sidebar.selectbox("Navigate", ["Extract Data", "Analytics Dashboard"])

if page == "Extract Data":
    st.markdown("""
    This application extracts patient characteristic data from medical research articles.
    Upload a PDF of a research article to get started.
    """)

    # LLM provider selection
    provider = st.sidebar.selectbox(
        "LLM Provider",
        ["anthropic", "openai"],
        index=0
    )

    # Model selection (will be dynamically populated based on provider)
    if provider == "anthropic":
        models = ["claude-3-sonnet-20240229", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
    else:
        models = ["gpt-3.5-turbo", "gpt-4o", "gpt-4-1106-preview"]

    model = st.sidebar.selectbox("Model", models)

    # Advanced settings expander
    with st.sidebar.expander("Advanced Settings"):
        # Chunk size
        chunk_size = st.number_input("Chunk Size (chars)", min_value=500, max_value=10000, value=1000)
        
        # Chunk overlap
        overlap = st.number_input("Chunk Overlap (chars)", min_value=0, max_value=500, value=100)
        
        # Temperature setting
        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.0, step=0.1)
        
        # Prompt version selection
        versions = PromptTemplate.get_all_prompt_versions('patient_characteristics')
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
        
        # Process button
        if st.button("Process Article"):
            # Check for API key
            api_key_env_var = "ANTHROPIC_API_KEY" if provider == "anthropic" else "OPENAI_API_KEY"
            if not os.environ.get(api_key_env_var):
                st.error(f"Please set the {api_key_env_var} environment variable before processing.")
            else:
                # Chunk the text
                with st.spinner("Chunking text..."):
                    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
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
                        start_time = time.time()
                        
                        # Select appropriate prompt
                        if use_custom and custom_chars:
                            prompt_id = 'custom_patient_characteristics'
                            prompt = PromptTemplate.custom_extraction_prompt(
                                chunk['content'], 
                                custom_chars,
                                version=None
                            )
                        else:
                            prompt_id = 'patient_characteristics'
                            prompt = PromptTemplate.get_extraction_prompt(
                                chunk['content'],
                                version=prompt_version if prompt_version != "default" else None
                            )
                        
                        # Generate completion
                        completion = extractor.client.generate_completion(
                            prompt, 
                            temperature=temperature
                        )
                        
                        # Calculate duration in milliseconds
                        duration_ms = (time.time() - start_time) * 1000
                        
                        # Track in analytics
                        analytics.track_extraction(
                            prompt_id=prompt_id,
                            model=model,
                            duration_ms=duration_ms,
                            char_count=len(chunk['content']),
                            success=True,
                            metadata={
                                'chunk_index': chunk['index'],
                                'temperature': temperature,
                                'file_name': uploaded_file.name
                            }
                        )
                        
                        # Add to results
                        chunk_results.append({
                            'chunk_index': chunk['index'],
                            'extraction': completion
                        })
                
                # Merge results
                with st.spinner("Compiling results..."):
                    # Save raw results
                    raw_output_path = f"data/output/raw_{uploaded_file.name.replace('.pdf', '.csv')}"
                    
                    # Convert to DataFrame for display
                    df = pd.DataFrame([
                        {'chunk': item['chunk_index'], 'extraction': item['extraction']} 
                        for item in chunk_results
                    ])
                    
                    # Save results
                    save_to_csv(df.to_dict('records'), raw_output_path)
                    
                    # Show results
                    st.subheader("Extraction Results")
                    st.dataframe(df)
                    
                    # Download button
                    with open(raw_output_path, 'rb') as f:
                        st.download_button(
                            label="Download Results as CSV",
                            data=f,
                            file_name=f"extracted_data_{uploaded_file.name.replace('.pdf', '.csv')}",
                            mime="text/csv"
                        )

elif page == "Analytics Dashboard":
    st.header("Analytics Dashboard")
    
    # Time period selection
    time_period = st.selectbox(
        "Time Period",
        [7, 30, 90, 365],
        index=1,
        format_func=lambda x: f"Last {x} days"
    )
    
    # Generate report
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