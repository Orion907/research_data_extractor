"""
Batch Extraction Page - Phase 2 Enhanced Implementation

Clean, focused page for research data extraction with:
- Clear purpose explanation and workflow overview  
- PICOTS input purpose explanation
- Domain status awareness
- Enhanced batch processing integration
"""

import streamlit as st
from typing import Dict, Any, Optional
from .batch_page import BatchPage


class BatchExtractionPage:
    """
    Dedicated page for batch extraction workflow.
    Keeps streamlit_app.py clean by containing all batch extraction UI logic.
    """
    
    def __init__(self, extraction_engine, document_processor, batch_coordinator, config):
        """Initialize batch extraction page with required components."""
        self.extraction_engine = extraction_engine
        self.document_processor = document_processor
        self.batch_coordinator = batch_coordinator
        self.config = config
        
        # Initialize the core batch processing page
        self.batch_page = BatchPage(extraction_engine, document_processor, batch_coordinator, config)
    
    def render(self) -> None:
        """Render the complete batch extraction page."""
        st.header("📚 Batch Extraction")
        
        # Enhanced workflow explanation
        self._render_workflow_explanation()
        
        # Pro tip
        st.info("🎯 **Pro tip**: Define your PICOTS criteria to get more focused and accurate extraction results")
        
        # Core batch processing functionality
        self.batch_page.render()
    
    def _render_workflow_explanation(self) -> None:
        """Render workflow explanation section."""
        st.markdown("### 📊 Research Data Extraction")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🔍 What this does:**
            - Extracts structured PICOTS data from research articles
            - Works with single articles or batch uploads
            - Exports research-ready CSV data for analysis
            """)
        
        with col2:
            st.markdown("""
            **💡 PICOTS Input Purpose:**
            - Makes LLM prompts more targeted and accurate
            - Focuses extraction on your specific research criteria
            - Improves data quality and relevance
            """)
    
    def _render_domain_status(self) -> None:
        """Render domain status awareness section."""
        # Domain setup has been removed - using PICOTS-enhanced extraction
        pass