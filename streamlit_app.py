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

# Import UI components and pages (streamlined for Phase 1)
from src.ui import BatchPage
from src.ui.pages.unified_extraction_page import UnifiedExtractionPage


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
st.title("🔬 Research Data Extractor")
st.markdown("**Streamlined workflow for systematic reviews and meta-analyses**")

# Streamlined Navigation - Phase 1 Simplification
st.sidebar.markdown("## 🔬 Research Data Extraction")
st.sidebar.markdown("**Streamlined workflow for systematic reviews**")

page = st.sidebar.selectbox(
    "Choose your workflow:", 
    ["🗺️ Domain Setup", "📚 Batch Extraction"],
    help="Domain Setup: Create vocabulary maps for better extraction (recommended first step)\nBatch Extraction: Extract PICOTS data from research articles (1 or many files)"
)

if page == "🗺️ Domain Setup":
    # Domain vocabulary creation (enhanced from Unified Extraction domain features)
    st.header("🗺️ Domain Setup")
    st.markdown("""
    **Recommended first step**: Create a domain vocabulary map for enhanced extraction accuracy.
    
    Upload 3-5 sample articles from your research area to build specialized vocabulary mappings.
    This improves extraction quality for all subsequent articles in your systematic review.
    """)
    
    # Skip option for immediate processing
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("💡 **Tip**: Domain setup significantly improves extraction accuracy for specialized research areas")
    with col2:
        if st.button("⏭️ Skip to Extraction", key="skip_domain_setup"):
            st.session_state.skip_domain_setup = True
            st.info("👆 Use the navigation above to go to 'Batch Extraction'")
    
    # Use the domain priming features from UnifiedExtractionPage
    unified_page = UnifiedExtractionPage(extraction_engine, document_processor, config)
    # Only render the domain priming section
    unified_page._render_domain_priming_window()

elif page == "📚 Batch Extraction":
    # Main extraction workflow (enhanced batch processing)
    st.header("📚 Batch Extraction")
    st.markdown("""
    **Main research workflow**: Upload research articles and extract structured PICOTS data.
    
    - Upload single articles or batches (works the same way)
    - Enter your PICOTS research criteria  
    - Get structured CSV data ready for analysis
    """)
    
    # Use the enhanced batch processing page
    batch_page = BatchPage(extraction_engine, document_processor, batch_coordinator, config)
    batch_page.render()

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