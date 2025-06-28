"""
Unified Extraction Page - Phase 1 Implementation

Combines Domain Priming and Extraction in side-by-side windows for seamless workflow.
Implements the user's desired workflow: sample upload → term extraction → PICOTS → processing.
"""

import streamlit as st
from typing import Dict, Any, Optional, List
from pathlib import Path

from ..components.file_upload import FileUploadComponent, FileUploadSection
from ..components.progress_display import ProgressDisplayComponent, ChunkProgressTracker, ProgressCallbackHandler
from ..components.results_viewer import ResultsDisplaySection
# Import domain mapping components conditionally to avoid matplotlib dependency
try:
    from ..components.domain_mapping_components import (
        SampleUploadComponent, 
        DomainAnalysisComponent,
        DomainMapEditorComponent,
        ProfileManagerComponent
    )
    DOMAIN_COMPONENTS_AVAILABLE = True
except ImportError as e:
    # Fallback to simplified components if domain mapping components unavailable
    DOMAIN_COMPONENTS_AVAILABLE = False
from src.utils.domain_priming import DomainPrimingEngine


class UnifiedExtractionPage:
    """
    Unified page combining Domain Priming and Extraction workflows.
    
    Phase 1 Implementation:
    - Side-by-side Domain Priming and Extraction windows
    - Real-time state synchronization
    - Parallel processing enabled by default
    - Integrated PICOTS workflow
    """
    
    def __init__(self, extraction_engine, document_processor, config):
        """
        Initialize unified extraction page.
        
        Args:
            extraction_engine: The extraction engine instance
            document_processor: The document processor instance
            config: Configuration object
        """
        self.extraction_engine = extraction_engine
        self.document_processor = document_processor
        self.config = config
        
        # Initialize domain priming engine with parallel processing as default
        self.domain_engine = DomainPrimingEngine(
            llm_provider=config.get('llm.provider', 'anthropic'),
            api_key=config.get('api.anthropic_key'),
            model_name=config.get('llm.model_name')
        )
        
        # Initialize session state for unified workflow
        self._initialize_session_state()
    
    def render(self) -> None:
        """Render the unified extraction page with side-by-side windows."""
        st.title("🔬 Unified Research Data Extraction")
        st.markdown("""
        **Phase 1 Prototype**: Domain Priming + Extraction on one page with parallel processing.
        Upload sample articles to build domain vocabulary, then process research articles with enhanced extraction.
        """)
        
        # Create two-column layout for side-by-side windows
        col_priming, col_extraction = st.columns([1, 1], gap="large")
        
        with col_priming:
            self._render_domain_priming_window()
        
        with col_extraction:
            self._render_extraction_window()
        
        # Bottom section for unified workflow status
        self._render_workflow_status()
    
    def _initialize_session_state(self) -> None:
        """Initialize session state for unified workflow."""
        # Domain priming state
        if 'domain_profile_ready' not in st.session_state:
            st.session_state.domain_profile_ready = False
        if 'active_domain_profile' not in st.session_state:
            st.session_state.active_domain_profile = None
        if 'domain_profile_name' not in st.session_state:
            st.session_state.domain_profile_name = None
        
        # Extraction state
        if 'extraction_ready' not in st.session_state:
            st.session_state.extraction_ready = False
        if 'unified_picots_data' not in st.session_state:
            st.session_state.unified_picots_data = None
        
        # Parallel processing enabled by default
        if 'optimization_level' not in st.session_state:
            st.session_state.optimization_level = "parallel"
    
    def _render_domain_priming_window(self) -> None:
        """Render the domain priming window (left side)."""
        st.header("📚 Domain Priming")
        st.markdown("*Build vocabulary from sample articles*")
        
        # Check if we have an active profile
        if st.session_state.active_domain_profile:
            st.success(f"✅ Active Profile: **{st.session_state.domain_profile_name}**")
            
            # Quick profile info
            with st.expander("📋 Profile Summary", expanded=False):
                profile = st.session_state.active_domain_profile
                domain_map = profile.get('domain_map', {})
                st.write(f"**Total Mappings:** {len(domain_map)}")
                st.write(f"**Created:** {profile.get('metadata', {}).get('created_at', 'Unknown')}")
                
                # Show a few sample mappings
                if domain_map:
                    st.write("**Sample Mappings:**")
                    for i, (canonical, synonyms) in enumerate(list(domain_map.items())[:3]):
                        st.write(f"• {canonical} → {', '.join(synonyms[:3])}")
            
            # Option to load different profile or create new one
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Load Different Profile", key="load_different"):
                    st.session_state.show_profile_loader = True
            with col2:
                if st.button("➕ Create New Profile", key="create_new"):
                    st.session_state.active_domain_profile = None
                    st.session_state.domain_profile_ready = False
                    st.rerun()
        
        else:
            # Domain priming workflow tabs
            tab1, tab2, tab3 = st.tabs(["📄 Upload Samples", "🧠 Analyze & Map", "💾 Save Profile"])
            
            with tab1:
                self._render_sample_upload_section()
            
            with tab2:
                self._render_domain_analysis_section()
            
            with tab3:
                self._render_profile_management_section()
        
        # Profile loader modal
        if st.session_state.get('show_profile_loader', False):
            self._render_profile_loader_modal()
    
    def _render_extraction_window(self) -> None:
        """Render the extraction window (right side)."""
        st.header("🔍 Enhanced Extraction")
        st.markdown("*Process articles with domain-aware prompts*")
        
        # Check domain priming readiness
        if not st.session_state.domain_profile_ready and not st.session_state.active_domain_profile:
            st.info("👈 Create or load a domain profile first to enable enhanced extraction.")
            return
        
        # Render provider and model selection
        self._render_provider_selection()
        
        # Advanced settings in expander
        with st.expander("⚙️ Advanced Settings", expanded=False):
            settings = self._render_extraction_settings()
        
        # File upload section
        st.subheader("📄 Upload Research Article")
        uploaded_file = FileUploadComponent.pdf_uploader(
            "Upload a research article PDF",
            key="unified_extraction_upload",
            help_text="Upload the PDF you want to extract data from"
        )
        
        if uploaded_file:
            FileUploadComponent.display_file_info(uploaded_file)
            
            # Process PDF if not already done
            if not self._is_file_processed(uploaded_file.name):
                self._extract_text_from_pdf(uploaded_file)
        
        # PICOTS input section
        st.subheader("📊 PICOTS Criteria")
        st.markdown("Define your research question criteria for enhanced extraction:")
        
        picots_result = self._render_unified_picots_section()
        
        # Enhanced extraction button and processing
        if uploaded_file and st.session_state.get('file_processed'):
            self._render_enhanced_processing_section(uploaded_file, picots_result, settings if 'settings' in locals() else {})
    
    def _render_sample_upload_section(self) -> None:
        """Render sample upload section for domain priming."""
        st.markdown("Upload 1-5 sample articles to build domain vocabulary:")
        
        sample_files = FileUploadComponent.batch_pdf_uploader(
            "Upload sample PDF files (1-5 recommended)",
            key="domain_sample_upload"
        )
        
        if sample_files:
            FileUploadComponent.display_batch_file_info(sample_files)
            
            if st.button("📝 Extract Text from Samples", key="extract_samples"):
                self._process_sample_files(sample_files)
    
    def _render_domain_analysis_section(self) -> None:
        """Render domain analysis section."""
        if 'sample_texts' not in st.session_state:
            st.info("👆 Upload sample files first to enable analysis.")
            return
        
        st.markdown(f"**Ready to analyze {len(st.session_state.sample_texts)} sample articles**")
        
        # Domain name input
        domain_name = st.text_input(
            "Domain Profile Name:",
            value=f"profile_{st.session_state.get('domain_timestamp', '')}",
            key="domain_name_input"
        )
        
        # Analysis button
        if st.button("🧠 Analyze Samples & Build Domain Map", key="analyze_samples"):
            if domain_name:
                self._run_domain_analysis(domain_name)
            else:
                st.error("Please provide a domain profile name.")
        
        # Show analysis results if available
        if 'domain_analysis_results' in st.session_state:
            self._display_analysis_results()
    
    def _render_profile_management_section(self) -> None:
        """Render profile management section."""
        if 'domain_analysis_results' not in st.session_state:
            st.info("👆 Complete domain analysis first.")
            return
        
        st.markdown("**Review and save your domain profile:**")
        
        # Show domain map summary
        results = st.session_state.domain_analysis_results
        domain_map = results.get('domain_map', {})
        
        if domain_map:
            st.write(f"**Found {len(domain_map)} domain mappings**")
            
            # Quick editor for domain map
            with st.expander("✏️ Edit Domain Mappings", expanded=False):
                self._render_quick_domain_editor(domain_map)
        
        # Save profile button
        if st.button("💾 Save Domain Profile", key="save_domain_profile"):
            self._save_domain_profile()
    
    def _render_unified_picots_section(self) -> Dict[str, Any]:
        """Render PICOTS input with domain-aware enhancements."""
        picots_text = st.text_area(
            "Paste your PICOTS criteria:",
            height=150,
            placeholder="""Population: Adults aged 18-65 with type 2 diabetes
Intervention: Metformin therapy
Comparator: Placebo or standard care
Outcome: HbA1c reduction, weight loss
Timing: 12-week treatment period
Setting: Outpatient clinics""",
            key="unified_picots_input"
        )
        
        result = {'picots_text': None, 'picots_data': None}
        
        if picots_text:
            result['picots_text'] = picots_text
            
            # Parse PICOTS if parser available
            try:
                from src.utils.picots_parser import PicotsParser
                parser = PicotsParser()
                picots_data = parser.parse_picots_table(picots_text)
                result['picots_data'] = picots_data
                st.session_state.unified_picots_data = picots_data
                
                # Show domain mapping preview if we have an active profile
                if st.session_state.active_domain_profile and picots_data:
                    self._show_picots_domain_preview(picots_data)
                    
            except (ImportError, Exception) as e:
                # Simple parsing fallback for any parsing errors
                st.info(f"Using simplified PICOTS parsing: {str(e)}")
                result['picots_data'] = self._simple_picots_parse(picots_text)
                st.session_state.unified_picots_data = result['picots_data']
        
        return result
    
    def _render_enhanced_processing_section(self, uploaded_file, picots_result: Dict, settings: Dict) -> None:
        """Render enhanced processing section with parallel execution."""
        st.subheader("🚀 Enhanced Processing")
        
        # Show optimization level
        optimization_level = st.selectbox(
            "Processing Optimization:",
            ["parallel", "balanced", "sequential"],
            index=0,  # Default to parallel for Phase 1
            help="Parallel processing is enabled by default for Phase 1",
            key="unified_optimization_level"
        )
        st.session_state.optimization_level = optimization_level
        
        # Processing button
        process_ready = (
            st.session_state.get('file_processed', False) and
            (st.session_state.active_domain_profile or st.session_state.domain_profile_ready)
        )
        
        processing_complete = st.session_state.get('unified_processing_complete', False)
        
        if st.button(
            "🔬 Process with Enhanced Domain Extraction",
            key="unified_process_button",
            disabled=not process_ready or processing_complete
        ) or processing_complete:
            
            if not processing_complete and process_ready:
                self._perform_enhanced_extraction(uploaded_file, picots_result, optimization_level)
            
            # Display results if processing is complete
            if processing_complete and 'unified_chunk_results' in st.session_state:
                self._display_enhanced_results(uploaded_file.name)
    
    def _render_workflow_status(self) -> None:
        """Render unified workflow status at the bottom."""
        st.markdown("---")
        st.subheader("📊 Workflow Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Domain priming status
            if st.session_state.active_domain_profile:
                st.success("✅ Domain Profile Active")
                st.write(f"**Profile:** {st.session_state.domain_profile_name}")
            elif st.session_state.domain_profile_ready:
                st.success("✅ Domain Profile Ready")
            else:
                st.info("⏳ Domain Profile Needed")
        
        with col2:
            # PICOTS status
            if st.session_state.unified_picots_data:
                st.success("✅ PICOTS Defined")
                
                # Handle both PicotsData objects and dict objects
                picots_data = st.session_state.unified_picots_data
                if hasattr(picots_data, '__dict__'):
                    # PicotsData object - count non-empty sections
                    sections = []
                    if hasattr(picots_data, 'population') and picots_data.population: sections.append('Population')
                    if hasattr(picots_data, 'interventions') and picots_data.interventions: sections.append('Intervention')
                    if hasattr(picots_data, 'comparators') and picots_data.comparators: sections.append('Comparator')
                    if hasattr(picots_data, 'outcomes') and picots_data.outcomes: sections.append('Outcome')
                    if hasattr(picots_data, 'timing') and picots_data.timing: sections.append('Timing')
                    if hasattr(picots_data, 'setting') and picots_data.setting: sections.append('Setting')
                    picots_count = len(sections)
                else:
                    # Regular dict
                    picots_count = len([v for v in picots_data.values() if v])
                
                st.write(f"**Sections:** {picots_count}")
            else:
                st.info("⏳ PICOTS Optional")
        
        with col3:
            # Processing status
            if st.session_state.get('unified_processing_complete'):
                st.success("✅ Processing Complete")
                st.write(f"**Mode:** {st.session_state.optimization_level}")
            elif st.session_state.get('file_processed'):
                st.warning("⚡ Ready to Process")
            else:
                st.info("⏳ Upload Article")
    
    def _process_sample_files(self, sample_files: List) -> None:
        """Process sample files for domain priming."""
        with ProgressDisplayComponent.spinner_context("Extracting text from sample files..."):
            sample_texts = []
            
            for file in sample_files:
                try:
                    # Extract text from each PDF
                    temp_path, text, chunks = self.document_processor.process_uploaded_file(
                        file, "data/input", "sample_"
                    )
                    sample_texts.append(text)
                except Exception as e:
                    st.error(f"Error processing {file.name}: {str(e)}")
                    continue
            
            if sample_texts:
                import time
                st.session_state.sample_texts = sample_texts
                st.session_state.domain_timestamp = str(int(time.time() * 1000))
                st.success(f"✅ Extracted text from {len(sample_texts)} sample files")
                st.rerun()
    
    def _run_domain_analysis(self, domain_name: str) -> None:
        """Run domain analysis on sample texts."""
        with ProgressDisplayComponent.spinner_context("Analyzing domain patterns..."):
            try:
                # Run Phase 1 analysis
                domain_profile = self.domain_engine.analyze_sample_articles(
                    st.session_state.sample_texts,
                    domain_name=domain_name
                )
                
                st.session_state.domain_analysis_results = domain_profile
                st.session_state.domain_profile_name = domain_name
                st.success("✅ Domain analysis complete!")
                st.rerun()
                
            except Exception as e:
                st.error(f"Error during domain analysis: {str(e)}")
    
    def _save_domain_profile(self) -> None:
        """Save the domain profile and activate it."""
        try:
            # Apply any user edits
            if 'edited_domain_map' in st.session_state:
                results = st.session_state.domain_analysis_results
                results['domain_map'] = st.session_state.edited_domain_map
            
            # Set current profile in engine
            self.domain_engine.current_domain_profile = st.session_state.domain_analysis_results
            
            # Save to disk
            saved_path = self.domain_engine.save_domain_profile()
            
            # Activate the profile
            st.session_state.active_domain_profile = st.session_state.domain_analysis_results
            st.session_state.domain_profile_ready = True
            
            st.success(f"✅ Domain profile saved and activated: {saved_path}")
            
            # Clean up temporary state
            for key in ['sample_texts', 'domain_analysis_results', 'edited_domain_map']:
                if key in st.session_state:
                    del st.session_state[key]
            
            st.rerun()
            
        except Exception as e:
            st.error(f"Error saving domain profile: {str(e)}")
    
    def _perform_enhanced_extraction(self, uploaded_file, picots_result: Dict, optimization_level: str) -> None:
        """Perform enhanced extraction with domain priming and parallel processing."""
        # Validate API key
        provider = st.session_state.get('unified_provider', 'anthropic')
        is_valid, error_msg = self.extraction_engine.validate_api_key(provider)
        
        if not is_valid:
            ProgressDisplayComponent.show_status_message(error_msg, "error")
            return
        
        # Setup progress tracking
        chunks = st.session_state.get('chunks', [])
        progress_tracker = ChunkProgressTracker(len(chunks), uploaded_file.name)
        
        try:
            with ProgressDisplayComponent.spinner_context("Enhanced extraction with parallel processing..."):
                # Use optimized PICOTS workflow if available
                if st.session_state.unified_picots_data and hasattr(self.domain_engine, 'execute_optimized_picots_workflow'):
                    # Enhanced workflow with domain priming
                    # Convert PicotsData to dict format if needed
                    picots_for_workflow = self._convert_picots_to_dict(st.session_state.unified_picots_data)
                    
                    results = self.domain_engine.execute_optimized_picots_workflow(
                        text_chunks=[chunk['content'] for chunk in chunks],
                        picots_data=picots_for_workflow,
                        extraction_engine=self.extraction_engine,
                        optimization_level=optimization_level
                    )
                    
                    # Convert to expected format
                    chunk_results = self._convert_picots_results_to_chunks(results, chunks)
                else:
                    # Fallback to standard extraction
                    progress_callback = ProgressCallbackHandler.create_chunk_callback(progress_tracker)
                    
                    chunk_results = self.extraction_engine.process_chunks_batch(
                        chunks=chunks,
                        provider=provider,
                        model_name=st.session_state.get('unified_model', 'claude-3-sonnet-20240229'),
                        temperature=0.0,
                        source_file=uploaded_file.name,
                        picots_context=self._convert_picots_to_dict(st.session_state.unified_picots_data),
                        progress_callback=progress_callback
                    )
            
            # Store results
            st.session_state.unified_chunk_results = chunk_results
            st.session_state.unified_processing_complete = True
            
            progress_tracker.finish(success=True, message="Enhanced extraction completed")
            
        except Exception as e:
            progress_tracker.finish(success=False, message=f"Error: {str(e)}")
            ProgressDisplayComponent.show_status_message(f"Error during extraction: {str(e)}", "error")
    
    def _display_enhanced_results(self, filename: str) -> None:
        """Display enhanced extraction results."""
        chunk_results = st.session_state.get('unified_chunk_results', [])
        
        if not chunk_results:
            st.warning("No extraction results available")
            return
        
        st.success("🎉 Enhanced extraction complete!")
        
        # Show performance metrics if available
        if 'unified_performance_metrics' in st.session_state:
            metrics = st.session_state.unified_performance_metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Processing Time", f"{metrics.get('processing_time_seconds', 0):.1f}s")
            with col2:
                st.metric("Optimization Level", metrics.get('optimization_level', 'standard'))
            with col3:
                st.metric("Sections Processed", metrics.get('total_sections_processed', 0))
        
        # Display results using existing component
        structured_data = ResultsDisplaySection.create_results_section(
            chunk_results,
            filename,
            show_download=True,
            development_mode=False
        )
        
        # Reset button
        if st.button("🔄 Process New Article", key="unified_reset_button"):
            self._reset_extraction_state()
            st.rerun()
    
    # Helper methods
    def _is_file_processed(self, filename: str) -> bool:
        """Check if file has been processed."""
        return (st.session_state.get('unified_processing_complete', False) and 
                st.session_state.get('unified_uploaded_file_name') == filename)
    
    def _extract_text_from_pdf(self, uploaded_file) -> None:
        """Extract text from uploaded PDF."""
        with ProgressDisplayComponent.spinner_context("Processing uploaded PDF..."):
            try:
                temp_path, text, chunks = self.document_processor.process_uploaded_file(
                    uploaded_file, "data/input", "unified_"
                )
                
                ProgressDisplayComponent.show_file_processing_status(
                    uploaded_file.name, len(text), len(chunks), "success"
                )
                
                st.session_state.unified_processing_complete = False
                st.session_state.file_processed = True
                st.session_state.unified_uploaded_file_name = uploaded_file.name
                st.session_state.chunks = chunks
                
            except Exception as e:
                ProgressDisplayComponent.show_status_message(f"Error processing file: {str(e)}", "error")
                st.stop()
    
    def _render_provider_selection(self) -> None:
        """Render LLM provider selection for extraction."""
        # Provider selection
        if 'unified_provider' not in st.session_state:
            st.session_state.unified_provider = "anthropic"
        
        provider = st.selectbox(
            "LLM Provider:",
            ["anthropic", "openai", "mock"],
            index=["anthropic", "openai", "mock"].index(st.session_state.unified_provider),
            key="unified_provider_select"
        )
        st.session_state.unified_provider = provider
        
        # Model selection
        models = self.extraction_engine.get_available_models(provider)
        model = st.selectbox(
            "Model:",
            models,
            key="unified_model_select"
        )
        st.session_state.unified_model = model
    
    def _render_extraction_settings(self) -> Dict[str, Any]:
        """Render extraction settings."""
        settings = {}
        
        settings['chunk_size'] = st.number_input(
            "Chunk Size (chars)", 
            min_value=500, 
            max_value=10000, 
            value=1000,
            key="unified_chunk_size"
        )
        
        settings['temperature'] = st.slider(
            "Temperature", 
            min_value=0.0, 
            max_value=1.0, 
            value=0.0, 
            step=0.1,
            key="unified_temperature"
        )
        
        return settings
    
    def _simple_picots_parse(self, picots_text: str) -> Dict[str, str]:
        """Simple PICOTS parsing fallback."""
        lines = picots_text.strip().split('\n')
        picots_data = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().title()
                value = value.strip()
                if key and value:
                    picots_data[key] = value
        
        return picots_data
    
    def _reset_extraction_state(self) -> None:
        """Reset extraction state for new processing."""
        keys_to_clear = [
            'file_processed', 'chunks', 'unified_chunk_results',
            'unified_processing_complete', 'unified_uploaded_file_name',
            'unified_performance_metrics'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
    
    def _convert_picots_to_dict(self, picots_data) -> Dict[str, str]:
        """Convert PicotsData object to dict format for workflow processing."""
        if hasattr(picots_data, '__dict__'):
            # PicotsData object - convert to dict
            picots_dict = {}
            if hasattr(picots_data, 'population') and picots_data.population:
                picots_dict['Population'] = ' '.join(picots_data.population)
            if hasattr(picots_data, 'interventions') and picots_data.interventions:
                picots_dict['Intervention'] = ' '.join(picots_data.interventions)
            if hasattr(picots_data, 'comparators') and picots_data.comparators:
                picots_dict['Comparator'] = ' '.join(picots_data.comparators)
            if hasattr(picots_data, 'outcomes') and picots_data.outcomes:
                picots_dict['Outcome'] = ' '.join(picots_data.outcomes)
            if hasattr(picots_data, 'timing') and picots_data.timing:
                picots_dict['Timing'] = ' '.join(picots_data.timing)
            if hasattr(picots_data, 'setting') and picots_data.setting:
                picots_dict['Setting'] = ' '.join(picots_data.setting)
            return picots_dict
        else:
            # Already a dict
            return picots_data

    def _convert_picots_results_to_chunks(self, picots_results: Dict, original_chunks: List) -> List:
        """Convert PICOTS workflow results to chunk format for display."""
        chunk_results = []
        
        for i, chunk in enumerate(original_chunks):
            # Combine all PICOTS section results for this chunk
            combined_extraction = {}
            
            for section, section_results in picots_results.items():
                if section != '_metadata' and isinstance(section_results, list):
                    if i < len(section_results):
                        chunk_result = section_results[i]
                        if isinstance(chunk_result, dict):
                            # Add section-specific data
                            section_data = chunk_result.get('extracted_data', {})
                            if section_data:
                                combined_extraction[f"{section}_data"] = section_data
            
            # Create mock extraction text in the expected format
            extraction_text = "PICOTS Enhanced Extraction Results:\n\n"
            for section, data in combined_extraction.items():
                extraction_text += f"{section.replace('_', ' ').title()}:\n"
                if isinstance(data, dict):
                    for key, value in data.items():
                        extraction_text += f"  {key}: {value}\n"
                else:
                    extraction_text += f"  {data}\n"
                extraction_text += "\n"
            
            # Create result in expected format
            chunk_results.append({
                'chunk_index': i,
                'extraction': extraction_text if extraction_text.strip() else f"Mock extraction result for chunk {i+1} using parallel PICOTS processing",
                'confidence_score': 0.85,
                'source_file': chunk.get('source_file', f'chunk_{i+1}'),
                'metadata': {
                    'optimization_level': picots_results.get('_metadata', {}).get('optimization_level', 'parallel'),
                    'sections_processed': len([k for k in picots_results.keys() if k != '_metadata']),
                    'processing_time': picots_results.get('_metadata', {}).get('processing_time_seconds', 0)
                }
            })
        
        return chunk_results
    
    # Additional helper methods would go here...
    def _display_analysis_results(self) -> None:
        """Display domain analysis results."""
        results = st.session_state.domain_analysis_results
        
        with st.expander("📊 Analysis Results", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Terms Found:** {len(results.get('raw_patterns', {}).get('term_frequencies', {}))}")
                st.write(f"**Abbreviations:** {len(results.get('raw_patterns', {}).get('abbreviations', {}))}")
            
            with col2:
                st.write(f"**Domain Mappings:** {len(results.get('domain_map', {}))}")
                st.write(f"**Field Clusters:** {len(results.get('enhanced_patterns', {}).get('semantic_clusters', {}))}")
    
    def _render_quick_domain_editor(self, domain_map: Dict) -> None:
        """Render quick domain map editor."""
        if 'edited_domain_map' not in st.session_state:
            st.session_state.edited_domain_map = domain_map.copy()
        
        st.write("**Top domain mappings:**")
        for i, (canonical, synonyms) in enumerate(list(domain_map.items())[:5]):
            st.write(f"**{canonical}:** {', '.join(synonyms)}")
        
        st.info("💡 Full editing available in the dedicated Domain Priming page")
    
    def _show_picots_domain_preview(self, picots_data) -> None:
        """Show preview of relevant domain mappings for PICOTS."""
        if not st.session_state.active_domain_profile:
            return
        
        domain_map = st.session_state.active_domain_profile.get('domain_map', {})
        
        with st.expander("🔍 Domain Mapping Preview", expanded=False):
            st.markdown("**Relevant mappings for your PICOTS:**")
            
            # Extract terms from PICOTS and show relevant mappings
            relevant_mappings = {}
            
            # Handle both PicotsData objects and dict objects
            if hasattr(picots_data, '__dict__'):
                # PicotsData object - get all text content
                picots_dict = {}
                if hasattr(picots_data, 'population'): picots_dict['Population'] = ' '.join(picots_data.population)
                if hasattr(picots_data, 'interventions'): picots_dict['Intervention'] = ' '.join(picots_data.interventions)
                if hasattr(picots_data, 'comparators'): picots_dict['Comparator'] = ' '.join(picots_data.comparators)
                if hasattr(picots_data, 'outcomes'): picots_dict['Outcome'] = ' '.join(picots_data.outcomes)
                if hasattr(picots_data, 'timing'): picots_dict['Timing'] = ' '.join(picots_data.timing)
                if hasattr(picots_data, 'setting'): picots_dict['Setting'] = ' '.join(picots_data.setting)
            else:
                # Regular dict
                picots_dict = picots_data
            
            for section, content in picots_dict.items():
                if content:
                    words = str(content).lower().split()
                    for word in words:
                        if word in domain_map:
                            relevant_mappings[word] = domain_map[word]
            
            if relevant_mappings:
                for term, synonyms in list(relevant_mappings.items())[:3]:
                    st.write(f"• **{term}** → {', '.join(synonyms[:3])}")
            else:
                st.info("No direct mappings found. The system will still apply semantic understanding.")
    
    def _render_profile_loader_modal(self) -> None:
        """Render profile loader modal."""
        try:
            available_profiles = self.domain_engine.list_available_profiles()
            
            if available_profiles:
                st.selectbox(
                    "Select a profile to load:",
                    options=[p['domain_name'] for p in available_profiles],
                    key="profile_to_load"
                )
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Load Profile", key="load_profile_btn"):
                        profile_name = st.session_state.profile_to_load
                        self._load_selected_profile(profile_name, available_profiles)
                
                with col2:
                    if st.button("Cancel", key="cancel_load"):
                        st.session_state.show_profile_loader = False
                        st.rerun()
            else:
                st.info("No saved profiles found.")
                if st.button("OK", key="no_profiles_ok"):
                    st.session_state.show_profile_loader = False
                    st.rerun()
                    
        except Exception as e:
            st.error(f"Error loading profiles: {str(e)}")
    
    def _load_selected_profile(self, profile_name: str, available_profiles: List) -> None:
        """Load the selected domain profile."""
        try:
            # Find profile path
            profile_info = next(p for p in available_profiles if p['domain_name'] == profile_name)
            profile_path = profile_info['file_path']
            
            # Load profile
            loaded_profile = self.domain_engine.load_domain_profile(profile_path)
            
            # Activate profile
            st.session_state.active_domain_profile = loaded_profile
            st.session_state.domain_profile_name = profile_name
            st.session_state.domain_profile_ready = True
            st.session_state.show_profile_loader = False
            
            st.success(f"✅ Loaded profile: {profile_name}")
            st.rerun()
            
        except Exception as e:
            st.error(f"Error loading profile: {str(e)}")