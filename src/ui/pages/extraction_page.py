"""
Single Document Extraction Page

Page component for single document extraction with integrated UI components.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from ..components.file_upload import FileUploadSection
from ..components.progress_display import ProgressDisplayComponent, ChunkProgressTracker, ProgressCallbackHandler
from ..components.results_viewer import ResultsDisplaySection


class ExtractionPage:
    """Single document extraction page with modular UI components."""
    
    def __init__(self, extraction_engine, document_processor, config):
        """
        Initialize extraction page.
        
        Args:
            extraction_engine: The extraction engine instance
            document_processor: The document processor instance
            config: Configuration object
        """
        self.extraction_engine = extraction_engine
        self.document_processor = document_processor
        self.config = config
    
    def render(self) -> None:
        """Render the complete extraction page."""
        # Page header
        st.markdown("""
        This application extracts patient characteristic data from medical research articles.
        Upload a PDF of a research article to get started.
        """)
        
        # Render provider and model selection
        self._render_provider_selection()
        
        # Render advanced settings
        settings = self._render_advanced_settings()
        
        # File upload and PICOTS section
        upload_result = FileUploadSection.single_document_upload_section()
        
        # Process uploaded file if available
        if upload_result['uploaded_file'] is not None:
            self._process_uploaded_file(upload_result, settings)
    
    def _render_provider_selection(self) -> None:
        """Render LLM provider and model selection."""
        # Initialize provider in session state
        if 'provider' not in st.session_state:
            st.session_state.provider = "anthropic"
        
        # Provider selection
        st.session_state.provider = st.sidebar.selectbox(
            "LLM Provider", 
            ["anthropic", "openai", "mock"],
            index=["anthropic", "openai", "mock"].index(st.session_state.provider),
            key="extraction_provider"
        )
        
        # Model selection
        models = self.extraction_engine.get_available_models(st.session_state.provider)
        st.session_state.model = st.sidebar.selectbox(
            "Model", 
            models,
            key="extraction_model"
        )
    
    def _render_advanced_settings(self) -> Dict[str, Any]:
        """
        Render advanced settings sidebar.
        
        Returns:
            Dictionary of setting values
        """
        settings = {}
        
        with st.sidebar.expander("Advanced Settings"):
            # Chunk size
            settings['chunk_size'] = st.number_input(
                "Chunk Size (chars)", 
                min_value=500, 
                max_value=10000, 
                value=self.config.get('pdf_processor.text_chunking.chunk_size', 1000),
                key="extraction_chunk_size"
            )
            
            # Chunk overlap
            settings['overlap'] = st.number_input(
                "Chunk Overlap (chars)", 
                min_value=0, 
                max_value=500, 
                value=self.config.get('pdf_processor.text_chunking.overlap', 100),
                key="extraction_overlap"
            )
            
            # Temperature setting
            settings['temperature'] = st.slider(
                "Temperature", 
                min_value=0.0, 
                max_value=1.0, 
                value=self.config.get('llm.temperature', 0.0), 
                step=0.1,
                key="extraction_temperature"
            )
            
            # Prompt version selection
            versions = self.extraction_engine.get_template_versions('patient_characteristics')
            settings['prompt_version'] = st.selectbox(
                "Prompt Version", 
                versions, 
                index=len(versions)-1,
                key="extraction_prompt_version"
            )
            
            # Custom characteristics
            settings['use_custom'] = st.checkbox(
                "Define Custom Characteristics",
                key="extraction_use_custom"
            )
            
            settings['custom_chars'] = []
            if settings['use_custom']:
                custom_chars_text = st.text_area(
                    "Enter characteristics (one per line)",
                    key="extraction_custom_chars"
                )
                if custom_chars_text:
                    settings['custom_chars'] = [
                        line.strip() for line in custom_chars_text.split('\n') 
                        if line.strip()
                    ]
        
        return settings
    
    def _process_uploaded_file(
        self, 
        upload_result: Dict[str, Any], 
        settings: Dict[str, Any]
    ) -> None:
        """
        Process the uploaded file and handle extraction.
        
        Args:
            upload_result: Results from file upload section
            settings: Advanced settings
        """
        uploaded_file = upload_result['uploaded_file']
        picots_text = upload_result['picots_text']
        picots_data = upload_result['picots_data']
        
        # Process the PDF file
        if not self._is_file_processed(uploaded_file.name):
            self._extract_text_from_pdf(uploaded_file)
        
        # Display PICOTS parsing results
        if picots_data:
            self._display_picots_results(picots_data)
        
        st.markdown("---")
        
        # Main processing button and results
        self._render_processing_section(uploaded_file, picots_data, settings)
    
    def _is_file_processed(self, filename: str) -> bool:
        """Check if file has already been processed."""
        return (st.session_state.get('processing_complete', False) and 
                st.session_state.get('uploaded_file_name') == filename)
    
    def _extract_text_from_pdf(self, uploaded_file) -> None:
        """Extract text from PDF using progress display."""
        with ProgressDisplayComponent.spinner_context("Processing uploaded PDF..."):
            try:
                temp_path, text, chunks = self.document_processor.process_uploaded_file(
                    uploaded_file, "data/input", "temp_"
                )
                
                # Show processing status
                ProgressDisplayComponent.show_file_processing_status(
                    uploaded_file.name,
                    len(text),
                    len(chunks),
                    "success"
                )
                
                # Store in session state
                st.session_state.processing_complete = False  # Reset for new file
                st.session_state.file_processed = True
                st.session_state.uploaded_file_name = uploaded_file.name
                st.session_state.chunks = chunks
                
            except Exception as e:
                ProgressDisplayComponent.show_status_message(
                    f"Error processing file: {str(e)}",
                    "error"
                )
                st.stop()
    
    def _display_picots_results(self, picots_data: Any) -> None:
        """Display PICOTS parsing results."""
        if "raw_text" not in picots_data:
            ProgressDisplayComponent.show_status_message(
                "PICOTS criteria parsed successfully!",
                "success",
                "✅"
            )
            
            # Display parsed data for verification
            with st.expander("🔍 View Parsed PICOTS Data", expanded=False):
                self._render_picots_display(picots_data)
        else:
            ProgressDisplayComponent.show_status_message(
                "PICOTS parsing failed, will use raw text",
                "warning",
                "⚠️"
            )
    
    def _render_picots_display(self, picots_data: Any) -> None:
        """Render PICOTS data display."""
        col1, col2 = st.columns(2)
        
        with col1:
            if hasattr(picots_data, 'population') and picots_data.population:
                st.write("**Population:**")
                for item in picots_data.population:
                    st.write(f"• {item}")
            
            if hasattr(picots_data, 'interventions') and picots_data.interventions:
                st.write("**Interventions:**")
                for item in picots_data.interventions:
                    st.write(f"• {item}")
                    
            if hasattr(picots_data, 'comparators') and picots_data.comparators:
                st.write("**Comparators:**")
                for item in picots_data.comparators:
                    st.write(f"• {item}")
        
        with col2:
            if hasattr(picots_data, 'outcomes') and picots_data.outcomes:
                st.write("**Outcomes:**")
                for item in picots_data.outcomes:
                    st.write(f"• {item}")
                    
            if hasattr(picots_data, 'timing') and picots_data.timing:
                st.write("**Timing:**")
                for item in picots_data.timing:
                    st.write(f"• {item}")
                    
            if hasattr(picots_data, 'setting') and picots_data.setting:
                st.write("**Setting:**")
                for item in picots_data.setting:
                    st.write(f"• {item}")
        
        # Show detected key questions
        if hasattr(picots_data, 'detected_kqs') and picots_data.detected_kqs:
            st.write("**Detected Key Questions:**")
            for kq in picots_data.detected_kqs:
                st.write(f"• {kq}")
        
        # Show abbreviations
        if hasattr(picots_data, 'abbreviations') and picots_data.abbreviations:
            st.write("**Abbreviations:**")
            for abbrev, full_name in picots_data.abbreviations.items():
                st.write(f"• {abbrev} = {full_name}")
    
    def _render_processing_section(
        self, 
        uploaded_file, 
        picots_data: Any, 
        settings: Dict[str, Any]
    ) -> None:
        """Render the main processing section."""
        # Initialize session state
        if 'processing_complete' not in st.session_state:
            st.session_state.processing_complete = False
        
        # Check if we have processed chunks
        file_ready = st.session_state.get('file_processed', False)
        processing_complete = st.session_state.get('processing_complete', False)
        
        # Process article button
        if st.button(
            "Process Article", 
            key="process_article_button",
            disabled=not file_ready or processing_complete
        ) or processing_complete:
            
            if not processing_complete and file_ready:
                self._perform_extraction(uploaded_file, picots_data, settings)
            
            # Display results if processing is complete
            if processing_complete and 'chunk_results' in st.session_state:
                self._display_extraction_results(uploaded_file.name)
    
    def _perform_extraction(
        self, 
        uploaded_file, 
        picots_data: Any, 
        settings: Dict[str, Any]
    ) -> None:
        """Perform the actual extraction with progress tracking."""
        # Validate API key
        is_valid, error_msg = self.extraction_engine.validate_api_key(
            st.session_state.provider
        )
        
        if not is_valid:
            ProgressDisplayComponent.show_status_message(error_msg, "error")
            return
        
        # Setup progress tracking
        chunks = st.session_state.get('chunks', [])
        progress_tracker = ChunkProgressTracker(
            len(chunks), 
            uploaded_file.name
        )
        
        # Create progress callback
        progress_callback = ProgressCallbackHandler.create_chunk_callback(progress_tracker)
        
        try:
            with ProgressDisplayComponent.spinner_context("Extracting data from chunks..."):
                chunk_results = self.extraction_engine.process_chunks_batch(
                    chunks=chunks,
                    provider=st.session_state.provider,
                    model_name=st.session_state.model,
                    temperature=settings['temperature'],
                    source_file=uploaded_file.name,
                    custom_characteristics=settings['custom_chars'] if settings['use_custom'] else None,
                    picots_context=picots_data,
                    prompt_version=settings['prompt_version'],
                    progress_callback=progress_callback
                )
            
            # Mark processing as complete
            st.session_state.chunk_results = chunk_results
            st.session_state.processing_complete = True
            
            progress_tracker.finish(success=True, message="Extraction completed")
            
        except Exception as e:
            progress_tracker.finish(success=False, message=f"Error: {str(e)}")
            ProgressDisplayComponent.show_status_message(
                f"Error during extraction: {str(e)}",
                "error"
            )
    
    def _display_extraction_results(self, filename: str) -> None:
        """Display extraction results using the results viewer component."""
        chunk_results = st.session_state.get('chunk_results', [])
        
        if not chunk_results:
            ProgressDisplayComponent.show_status_message(
                "No extraction results available",
                "warning"
            )
            return
        
        # Display results using the results display section
        structured_data = ResultsDisplaySection.create_results_section(
            chunk_results,
            filename,
            show_download=True,
            development_mode=False
        )
        
        # Reset button
        if st.button("Process New File", key="reset_button"):
            self._reset_extraction_state()
            st.rerun()
    
    def _reset_extraction_state(self) -> None:
        """Reset extraction-related session state."""
        # Import session state manager
        from src.app import SessionStateManager
        SessionStateManager.reset_single_extraction_state()
        
        # Clear additional state
        for key in ['file_processed', 'chunks', 'chunk_results']:
            if key in st.session_state:
                del st.session_state[key]


class ExtractionSettingsComponent:
    """Standalone component for extraction settings."""
    
    @staticmethod
    def render_llm_settings(
        extraction_engine,
        config,
        key_prefix: str = "extraction"
    ) -> Dict[str, Any]:
        """
        Render LLM provider and model settings.
        
        Args:
            extraction_engine: The extraction engine instance
            config: Configuration object
            key_prefix: Prefix for session state keys
            
        Returns:
            Dictionary of selected settings
        """
        settings = {}
        
        # Provider selection
        provider_key = f"{key_prefix}_provider"
        if provider_key not in st.session_state:
            st.session_state[provider_key] = "anthropic"
        
        settings['provider'] = st.selectbox(
            "LLM Provider",
            ["anthropic", "openai", "mock"],
            index=["anthropic", "openai", "mock"].index(st.session_state[provider_key]),
            key=provider_key
        )
        
        # Model selection
        models = extraction_engine.get_available_models(settings['provider'])
        settings['model'] = st.selectbox(
            "Model",
            models,
            key=f"{key_prefix}_model"
        )
        
        return settings
    
    @staticmethod
    def render_processing_settings(
        config,
        extraction_engine,
        key_prefix: str = "extraction"
    ) -> Dict[str, Any]:
        """
        Render processing settings.
        
        Args:
            config: Configuration object
            extraction_engine: The extraction engine instance
            key_prefix: Prefix for session state keys
            
        Returns:
            Dictionary of processing settings
        """
        settings = {}
        
        # Chunk settings
        settings['chunk_size'] = st.number_input(
            "Chunk Size (chars)",
            min_value=500,
            max_value=10000,
            value=config.get('pdf_processor.text_chunking.chunk_size', 1000),
            key=f"{key_prefix}_chunk_size"
        )
        
        settings['overlap'] = st.number_input(
            "Chunk Overlap (chars)",
            min_value=0,
            max_value=500,
            value=config.get('pdf_processor.text_chunking.overlap', 100),
            key=f"{key_prefix}_overlap"
        )
        
        # LLM settings
        settings['temperature'] = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=config.get('llm.temperature', 0.0),
            step=0.1,
            key=f"{key_prefix}_temperature"
        )
        
        # Prompt version
        versions = extraction_engine.get_template_versions('patient_characteristics')
        settings['prompt_version'] = st.selectbox(
            "Prompt Version",
            versions,
            index=len(versions)-1,
            key=f"{key_prefix}_prompt_version"
        )
        
        return settings