"""
Domain Priming Page for Research Data Extractor
Provides UI for building and managing domain-specific term mappings
"""
import streamlit as st
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
import json
import logging

from src.utils.domain_priming import DomainPrimingEngine
from src.ui.components.domain_mapping_components import (
    SampleUploadComponent,
    DomainAnalysisComponent, 
    DomainMapEditorComponent,
    ProfileManagerComponent
)
from src.pdf_processor import extract_text_from_pdf

logger = logging.getLogger(__name__)

class DomainPrimingPage:
    """Main domain priming page orchestrating the complete workflow"""
    
    def __init__(self):
        self.engine = None
        
        # Initialize session state
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state variables for domain priming"""
        if 'domain_priming' not in st.session_state:
            st.session_state.domain_priming = {
                'uploaded_files': [],
                'extracted_texts': [],
                'current_profile': None,
                'analysis_results': None,
                'domain_map': {},
                'workflow_stage': 'upload'  # upload, analysis, review, manage
            }
    
    def _init_engine(self):
        """Initialize domain priming engine with current config"""
        try:
            # Get configuration from session state or config
            config = st.session_state.get('config', {})
            llm_provider = config.get('llm_provider', 'anthropic')
            api_key = config.get('api_key')
            
            if not api_key:
                st.warning("⚠️ No API key found. Please configure your LLM settings first.")
                return False
                
            self.engine = DomainPrimingEngine(
                llm_provider=llm_provider,
                api_key=api_key
            )
            return True
            
        except Exception as e:
            st.error(f"Failed to initialize domain priming engine: {str(e)}")
            logger.error(f"Engine initialization error: {e}")
            return False
    
    def render(self):
        """Render the complete domain priming page"""
        st.title("🧠 Domain Priming")
        st.markdown("""
        Build intelligent term mappings from sample articles to improve extraction accuracy.
        Upload 1-5 sample articles to automatically detect equivalent terms and concepts.
        """)
        
        # Initialize engine
        if not self.engine:
            if not self._init_engine():
                st.stop()
        
        # Create workflow tabs
        tab1, tab2, tab3, tab4 = st.tabs([
            "📁 Upload Samples", 
            "🔍 Analyze Patterns", 
            "✏️ Review & Edit", 
            "💾 Manage Profiles"
        ])
        
        with tab1:
            self._render_upload_tab()
        
        with tab2:
            self._render_analysis_tab()
        
        with tab3:
            self._render_review_tab()
        
        with tab4:
            self._render_manage_tab()
    
    def _render_upload_tab(self):
        """Render sample upload interface"""
        st.header("Upload Sample Articles")
        st.markdown("Upload 1-5 sample PDF articles that represent your research domain.")
        
        # Initialize upload component
        upload_component = SampleUploadComponent()
        
        # Render upload interface
        upload_results = upload_component.render()
        
        if upload_results:
            # Store results in session state
            st.session_state.domain_priming['uploaded_files'] = upload_results['files']
            st.session_state.domain_priming['extracted_texts'] = upload_results['texts']
            st.session_state.domain_priming['workflow_stage'] = 'analysis'
            
            st.success(f"✅ Successfully processed {len(upload_results['files'])} files")
            st.info("👉 Go to the 'Analyze Patterns' tab to continue")
    
    def _render_analysis_tab(self):
        """Render pattern analysis interface"""
        st.header("Pattern Analysis")
        
        # Check if we have uploaded texts
        if not st.session_state.domain_priming['extracted_texts']:
            st.warning("⚠️ Please upload sample articles first")
            return
        
        # Initialize analysis component
        analysis_component = DomainAnalysisComponent(self.engine)
        
        # Render analysis interface
        analysis_results = analysis_component.render(
            st.session_state.domain_priming['extracted_texts']
        )
        
        if analysis_results:
            # Store results in session state
            st.session_state.domain_priming['analysis_results'] = analysis_results
            st.session_state.domain_priming['current_profile'] = analysis_results
            st.session_state.domain_priming['domain_map'] = analysis_results.get('domain_map', {})
            st.session_state.domain_priming['workflow_stage'] = 'review'
            
            st.success("✅ Analysis complete!")
            st.info("👉 Go to the 'Review & Edit' tab to refine your domain mappings")
    
    def _render_review_tab(self):
        """Render domain map review and editing interface"""
        st.header("Review & Edit Domain Mappings")
        
        # Check if we have analysis results
        if not st.session_state.domain_priming['current_profile']:
            st.warning("⚠️ Please complete pattern analysis first")
            return
        
        # Initialize editor component
        editor_component = DomainMapEditorComponent(self.engine)
        
        # Render editing interface
        edited_profile = editor_component.render(
            st.session_state.domain_priming['current_profile']
        )
        
        if edited_profile:
            # Update session state with refined profile
            st.session_state.domain_priming['current_profile'] = edited_profile
            st.session_state.domain_priming['domain_map'] = edited_profile.get('domain_map', {})
            
            st.success("✅ Domain mappings updated!")
    
    def _render_manage_tab(self):
        """Render profile management interface"""
        st.header("Manage Domain Profiles")
        
        # Initialize profile manager component
        manager_component = ProfileManagerComponent(self.engine)
        
        # Render management interface
        manager_results = manager_component.render(
            st.session_state.domain_priming.get('current_profile')
        )
        
        if manager_results:
            if manager_results['action'] == 'loaded':
                # Profile was loaded
                st.session_state.domain_priming['current_profile'] = manager_results['profile']
                st.session_state.domain_priming['domain_map'] = manager_results['profile'].get('domain_map', {})
                st.success("✅ Profile loaded successfully!")
                
            elif manager_results['action'] == 'saved':
                st.success(f"✅ Profile saved as '{manager_results['name']}'")