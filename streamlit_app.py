"""
Streamlit web interface for PDF extraction and analysis
"""
import os
import streamlit as st
import pandas as pd
from src.pdf_processor.pdf_processor import extract_text_from_pdf
from src.pdf_processor.text_chunker import chunk_text
from src.utils.data_extractor import DataExtractor
from src.llm.client_factory import ClientFactory

# Set page title and configuration
st.set_page_config(
    page_title="Research Article Data Extractor",
    page_icon="📄",
    layout="wide"
)

def main():
    """Main function for the Streamlit app"""
    
    # Header
    st.title("Research Article Data Extractor")
    st.write("Upload a research article PDF to extract patient characteristics data.")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # LLM Provider selection
        llm_provider = st.selectbox(
            "LLM Provider",
            options=["OpenAI", "Anthropic"],
            index=1  # Default to Anthropic
        )
        
        # Model selection based on provider
        if llm_provider == "OpenAI":
            model_options = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo"]
            default_model_index = 0
        else:  # Anthropic
            model_options = ["claude-3-sonnet-20240229", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
            default_model_index = 0
            
        model_name = st.selectbox(
            "Model",
            options=model_options,
            index=default_model_index
        )
        
        # Text chunking parameters
        chunk_size = st.slider("Chunk Size (characters)", 500, 3000, 1000)
        chunk_overlap = st.slider("Chunk Overlap (characters)", 0, 500, 100)
        
        # API key input (with secure handling)
        api_key = st.text_input(
            f"{llm_provider} API Key",
            type="password",
            help=f"Enter your {llm_provider} API key or set it in your environment variables"
        )
    
    # Main panel
    uploaded_file = st.file_uploader("Upload PDF File", type=["pdf"])
    
    if uploaded_file is not None:
        # Create a temporary file path
        temp_pdf_path = f"temp_{uploaded_file.name}"
        
        # Save the uploaded file temporarily
        with open(temp_pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
            
        st.success(f"File uploaded: {uploaded_file.name}")
        
        # Process PDF when the user clicks the button
        if st.button("Extract Data"):
            with st.spinner("Processing PDF..."):
                # Step 1: Extract text from PDF
                st.text("Step 1: Extracting text from PDF...")
                try:
                    extracted_text = extract_text_from_pdf(temp_pdf_path)
                    
                    # Display text preview
                    with st.expander("Preview extracted text"):
                        st.text_area("Extracted Text", extracted_text[:1000] + "...", height=200)
                    
                    # Step 2: Chunk text
                    st.text("Step 2: Chunking text...")
                    chunks = chunk_text(
                        text=extracted_text,
                        chunk_size=chunk_size,
                        overlap=chunk_overlap,
                        respect_paragraphs=True
                    )
                    
                    st.info(f"Created {len(chunks)} text chunks")
                    
                    # Step 3: Initialize data extractor with the selected LLM
                    st.text("Step 3: Initializing LLM client...")
                    try:
                        # Convert provider name to lowercase for the factory
                        provider_key = llm_provider.lower()
                        
                        # Initialize data extractor
                        extractor = DataExtractor(
                            provider=provider_key,
                            api_key=api_key if api_key else None,
                            model_name=model_name
                        )
                        
                        # Step 4: Extract patient characteristics
                        st.text("Step 4: Extracting patient characteristics...")
                        
                        # Use a progress bar for chunk processing
                        progress_bar = st.progress(0)
                        
                        # Process only the first few chunks to save time and API costs
                        num_chunks_to_process = min(5, len(chunks))
                        chunk_results = []
                        
                        for i in range(num_chunks_to_process):
                            # Update progress bar
                            progress_bar.progress((i + 1) / num_chunks_to_process)
                            
                            # Get chunk content
                            chunk_content = chunks[i]['content']
                            
                            # Process chunk
                            with st.expander(f"Processing chunk {i+1}/{num_chunks_to_process}"):
                                st.text(f"Chunk {i+1} content preview:")
                                st.text_area(f"Chunk {i+1}", chunk_content[:300] + "...", height=100)
                                with st.spinner("Analyzing with LLM..."):
                                    result = extractor.extract_patient_characteristics(chunk_content)
                                    chunk_results.append(result)
                                    st.json(result)
                        
                        # Step 5: Combine results
                        st.text("Step 5: Combining results...")
                        combined_results = {}
                        
                        for result in chunk_results:
                            for key, value in result.items():
                                # If the key already exists, prefer non-empty and longer values
                                if key in combined_results:
                                    if not combined_results[key] or (value and len(str(value)) > len(str(combined_results[key]))):
                                        combined_results[key] = value
                                else:
                                    combined_results[key] = value
                        
                        # Display results
                        st.subheader("Extracted Patient Characteristics")
                        
                        # Convert to DataFrame for better display
                        df = pd.DataFrame(list(combined_results.items()), columns=['Characteristic', 'Value'])
                        st.dataframe(df)
                        
                        # Download options
                        st.download_button(
                            label="Download as CSV",
                            data=df.to_csv(index=False),
                            file_name="patient_characteristics.csv",
                            mime="text/csv"
                        )
                        
                        st.download_button(
                            label="Download as Excel",
                            data=df.to_excel(engine="openpyxl", index=False).getvalue(),
                            file_name="patient_characteristics.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                        
                    except Exception as e:
                        st.error(f"Error during LLM processing: {str(e)}")
                    
                except Exception as e:
                    st.error(f"Error processing PDF: {str(e)}")
                
                # Clean up temp file
                if os.path.exists(temp_pdf_path):
                    os.remove(temp_pdf_path)
    
    # Footer information
    st.markdown("---")
    st.markdown("### About this tool")
    st.write("""
    This tool extracts patient characteristics data from research articles using the following process:
    1. Converts PDF to text
    2. Splits text into manageable chunks
    3. Uses AI to extract structured patient data
    4. Combines results into a downloadable format
    """)

if __name__ == "__main__":
    main()