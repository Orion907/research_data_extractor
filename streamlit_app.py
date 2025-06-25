# File: streamlit_app.py

"""
Streamlit application for Research Data Extractor with Analytics Dashboard
"""
import os
import streamlit as st
import logging

# Import foundation and processing modules
from src.app import SessionStateManager, ConfigurationLoader
from src.processing import DocumentProcessor, ExtractionEngine, BatchCoordinator

# Import UI components and pages
from src.ui import ExtractionPage, BatchPage, AnnotationPage, AnalyticsPage


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
    # Use the new annotation page component
    annotation_page = AnnotationPage()
    annotation_page.render()

elif page == "Analytics Dashboard":
    # Use the new analytics page component
    analytics_page = AnalyticsPage(analytics)
    analytics_page.render()

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