"""
Batch Processing Page

Page component for batch document processing with integrated UI components.
"""

import streamlit as st
import tempfile
from typing import Dict, Any, Optional, List
from ..components.file_upload import FileUploadSection
from ..components.progress_display import BatchProgressDisplay, ProgressCallbackHandler
from ..components.results_viewer import ResultsDisplaySection
from .extraction_page import ExtractionSettingsComponent


class BatchPage:
    """Batch processing page with modular UI components."""
    
    def __init__(self, extraction_engine, document_processor, batch_coordinator, config):
        """
        Initialize batch page.
        
        Args:
            extraction_engine: The extraction engine instance
            document_processor: The document processor instance
            batch_coordinator: The batch coordinator instance
            config: Configuration object
        """
        self.extraction_engine = extraction_engine
        self.document_processor = document_processor
        self.batch_coordinator = batch_coordinator
        self.config = config
    
    def render(self) -> None:
        """Render the complete single-screen batch processing page."""
        # Initialize session state
        self._initialize_session_state()
        
        # Single-screen layout with three main sections
        self._render_tool_configuration_panel()
        self._render_picots_and_upload_section()
        self._render_results_section()
    
    def _initialize_session_state(self) -> None:
        """Initialize session state for batch processing."""
        if 'batch_files' not in st.session_state:
            st.session_state.batch_files = []
        if 'batch_processing_complete' not in st.session_state:
            st.session_state.batch_processing_complete = False
        if 'batch_results' not in st.session_state:
            st.session_state.batch_results = []
        # Phase 3: PICOTS persistence
        if 'batch_picots_text' not in st.session_state:
            st.session_state.batch_picots_text = ""
        if 'batch_picots_data' not in st.session_state:
            st.session_state.batch_picots_data = None
    
    def _render_tool_configuration_panel(self) -> None:
        """Render consolidated tool configuration panel (25% of screen)."""
        st.markdown("### 🛠️ Tool Configuration")
        
        # Model selection in a more compact layout
        col1, col2 = st.columns(2)
        
        with col1:
            if 'batch_provider' not in st.session_state:
                st.session_state.batch_provider = "anthropic"
            
            st.session_state.batch_provider = st.selectbox(
                "Provider",
                ["anthropic", "openai", "mock"],
                index=["anthropic", "openai", "mock"].index(st.session_state.batch_provider),
                key="batch_provider_select"
            )
        
        with col2:
            models = self.extraction_engine.get_available_models(st.session_state.batch_provider)
            
            if 'batch_model' not in st.session_state:
                st.session_state.batch_model = models[0]
            
            # Show model with brief description
            model_options = models
            if st.session_state.batch_provider == "anthropic":
                model_display = {
                    "claude-3-5-sonnet-20241022": "Claude 3.5 Sonnet (Latest)",
                    "claude-3-opus-20240229": "Claude 3 Opus (Most Capable)",
                    "claude-3-haiku-20240307": "Claude 3 Haiku (Fastest)"
                }
                display_names = [model_display.get(m, m) for m in models]
                selected_idx = st.selectbox(
                    "Model",
                    range(len(models)),
                    format_func=lambda x: display_names[x],
                    key="batch_model_select"
                )
                st.session_state.batch_model = models[selected_idx]
            else:
                st.session_state.batch_model = st.selectbox(
                    "Model", 
                    models, 
                    key="batch_model_select"
                )
        
        # Advanced settings in collapsible section
        self._render_advanced_settings_compact()
    
    def _render_advanced_settings_compact(self) -> Dict[str, Any]:
        """
        Render compact advanced settings.
        
        Returns:
            Dictionary of setting values
        """
        settings = {}
        
        with st.expander("⚙️ Advanced Settings", expanded=False):
            # Compact two-column layout for settings
            col1, col2 = st.columns(2)
            
            with col1:
                settings['temperature'] = st.slider(
                    "Temperature", 0.0, 1.0, 0.3, 0.1,
                    help="Higher values = more creative",
                    key="batch_temperature"
                )
                
                settings['max_parallel'] = st.number_input(
                    "Parallel Files", 1, 5, 2,
                    help="Files processed simultaneously",
                    key="batch_max_parallel"
                )
            
            with col2:
                settings['chunk_size'] = st.number_input(
                    "Chunk Size", 1000, 8000, 4000,
                    help="Text chunk size for processing",
                    key="batch_chunk_size"
                )
                
                settings['timeout_per_file'] = st.number_input(
                    "Timeout (min)", 5, 60, 15,
                    help="Max time per file",
                    key="batch_timeout"
                )
        
        return settings
    
    def _render_picots_and_upload_section(self) -> None:
        """Render combined PICOTS and upload section."""
        # Render PICOTS section
        picots_result = self._render_picots_section()
        
        # Render file upload section
        upload_result = self._render_file_upload_section()
        
        # If files are uploaded, show processing section
        if st.session_state.batch_files:
            # Get advanced settings
            settings = self._render_advanced_settings_compact()
            
            # Show processing section
            self._render_processing_section(settings, picots_result)
    
    def _render_results_section(self) -> None:
        """Render the results section."""
        if st.session_state.batch_processing_complete and st.session_state.batch_results:
            st.markdown("---")
            st.subheader("📊 Processing Results")
            self._display_batch_results()
    
    def _render_picots_section(self) -> Dict[str, Any]:
        """
        Render PICOTS input section for batch processing (Phase 3 enhancement).
        
        Returns:
            Dictionary containing PICOTS text and parsed data
        """
        result = {
            'picots_text': None,
            'picots_data': None
        }
        
        st.markdown("---")
        st.subheader("📊 PICOTS Criteria (Enhanced for Batch)")
        st.markdown("Define your research criteria to improve extraction accuracy across all uploaded files.")
        
        # PICOTS explanation with batch-specific benefits
        with st.expander("📋 Why use PICOTS for Batch Processing?", expanded=False):
            st.markdown("""
            **PICOTS enhances batch extraction by:**
            - **P**opulation: Identifies consistent patient demographics across studies
            - **I**ntervention: Focuses on specific treatments/exposures 
            - **C**omparison: Standardizes control group extraction
            - **O**utcomes: Targets relevant outcome measures
            - **T**iming: Captures temporal aspects consistently
            - **S**etting: Maintains setting context across articles
            
            **Batch Benefits:** PICOTS criteria are applied to ALL uploaded files, 
            ensuring consistent extraction focus and better data compilation.
            """)
        
        # Enhanced PICOTS text input with persistence
        picots_text = st.text_area(
            "Enter your PICOTS criteria:",
            value=st.session_state.batch_picots_text,
            height=200,
            placeholder="""Example format:
Population: Adults aged 18-65 with type 2 diabetes
Intervention: Metformin therapy 500mg twice daily
Comparison: Placebo or standard care
Outcomes: HbA1c reduction, weight loss, cardiovascular events
Timing: 12-week treatment period with 6-month follow-up
Setting: Outpatient diabetes clinics

Key Questions: What is the efficacy of metformin vs placebo?
Abbreviations: HbA1c = Hemoglobin A1c; BMI = Body Mass Index""",
            help="PICOTS criteria will be applied to ALL files in your batch for consistent extraction.",
            key="batch_picots_input"
        )
        
        # Update session state for persistence
        if picots_text != st.session_state.batch_picots_text:
            st.session_state.batch_picots_text = picots_text
        
        if picots_text:
            result['picots_text'] = picots_text
            
            # Parse PICOTS data if parser is available
            try:
                from src.utils.picots_parser import PicotsParser
                parser = PicotsParser()
                picots_data = parser.parse_picots_text(picots_text)
                result['picots_data'] = picots_data
                st.session_state.batch_picots_data = picots_data
                
                # Display parsed PICOTS with batch context
                if picots_data:
                    with st.expander("📋 Parsed PICOTS (Applied to Batch)", expanded=False):
                        st.success(f"✅ PICOTS criteria ready for batch processing of {len(st.session_state.batch_files)} files")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            for key, value in list(picots_data.items())[:3]:
                                if value:
                                    st.write(f"**{key.title()}:** {value}")
                        with col2:
                            for key, value in list(picots_data.items())[3:6]:
                                if value:
                                    st.write(f"**{key.title()}:** {value}")
                        
                        # Show domain integration status if available
                        if (st.session_state.get('active_domain_profile') or 
                            st.session_state.get('domain_profile_ready')):
                            st.info("🗺️ **Enhanced mode**: PICOTS + Domain profile will provide optimal extraction accuracy")
                
            except ImportError:
                st.warning("⚠️ Advanced PICOTS parsing not available. Using basic text processing.")
                # Simple fallback parsing
                result['picots_data'] = self._simple_picots_parse(picots_text)
                st.session_state.batch_picots_data = result['picots_data']
            except Exception as e:
                st.error(f"Error parsing PICOTS: {str(e)}")
        
        return result
    
    def _simple_picots_parse(self, picots_text: str) -> Dict[str, str]:
        """Simple PICOTS parsing fallback for batch processing."""
        lines = picots_text.strip().split('\n')
        picots_data = {}
        
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()
                if key and value:
                    picots_data[key] = value
        
        return picots_data
    
    def _render_file_upload_section(self) -> Dict[str, Any]:
        """
        Render enhanced unified file upload section (Phase 3 improvement).
        
        Returns:
            Upload results
        """
        st.markdown("---")
        st.subheader("📁 Upload Research Articles")
        
        # Phase 3: Unified upload interface that handles 1 or many files gracefully
        return BatchFileUploadComponent._render_unified_upload_interface()
    
    def _handle_zip_extraction(self, zip_file) -> None:
        """Handle ZIP file extraction."""
        try:
            from src.utils.zip_processor import ZipProcessor
            
            # Initialize ZIP processor
            zip_processor = ZipProcessor(max_files=50, max_file_size_mb=100)
            
            # Validate ZIP file
            with st.spinner("Validating ZIP archive..."):
                is_valid, validation_errors, zip_info = zip_processor.validate_zip_file(
                    zip_file.getvalue()
                )
            
            if is_valid:
                st.success("✅ Valid ZIP archive found!")
                
                # Display ZIP information
                self._display_zip_info(zip_info)
                
                # Extract files button
                if st.button("Extract PDF Files", key="extract_zip_button"):
                    self._extract_zip_files(zip_processor, zip_file)
            else:
                st.error("❌ ZIP archive validation failed:")
                for error in validation_errors:
                    st.write(f"• {error}")
                    
        except ImportError:
            st.error("ZIP processing not available. Please upload individual PDF files.")
    
    def _display_zip_info(self, zip_info: Dict[str, Any]) -> None:
        """Display ZIP file information."""
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
    
    def _extract_zip_files(self, zip_processor, zip_file) -> None:
        """Extract files from ZIP archive."""
        with st.spinner("Extracting PDF files from ZIP archive..."):
            # Create temporary directory
            if 'zip_temp_dir' not in st.session_state:
                st.session_state.zip_temp_dir = tempfile.mkdtemp()
            
            # Extract files
            extracted_files, extract_errors = zip_processor.extract_pdfs_from_zip(
                zip_file.getvalue(),
                st.session_state.zip_temp_dir
            )
            
            if extracted_files:
                st.success(f"✅ Successfully extracted {len(extracted_files)} PDF files!")
                
                # Convert to file-like objects
                file_objects = self._create_file_objects(extracted_files)
                st.session_state.batch_files = file_objects
                
                st.info("Files extracted and ready for batch processing.")
            
            if extract_errors:
                st.warning("⚠️ Some issues occurred during extraction:")
                for error in extract_errors:
                    st.write(f"• {error}")
            
            if not extracted_files and extract_errors:
                st.error("❌ Failed to extract any PDF files from the ZIP archive.")
    
    def _create_file_objects(self, extracted_files: List[Dict[str, Any]]) -> List:
        """Create file-like objects from extracted files."""
        file_objects = []
        
        for file_info in extracted_files:
            class FileObject:
                def __init__(self, name, path):
                    self.name = name
                    self.path = path
                    with open(path, 'rb') as f:
                        self._content = f.read()
                
                def getbuffer(self):
                    return self._content
                
                def getvalue(self):
                    return self._content
            
            file_objects.append(FileObject(file_info['name'], file_info['path']))
        
        return file_objects
    
    def _render_processing_section(self, settings: Dict[str, Any], picots_result: Dict[str, Any] = None) -> None:
        """Render the batch processing section."""
        st.markdown("---")
        st.subheader("🚀 Start Batch Processing")
        
        # Display file summary
        num_files = len(st.session_state.batch_files)
        st.info(f"Ready to process {num_files} files")
        
        # Processing button
        if st.button(
            "Start Batch Processing",
            key="start_batch_button",
            disabled=st.session_state.batch_processing_complete
        ) or st.session_state.batch_processing_complete:
            
            if not st.session_state.batch_processing_complete:
                self._perform_batch_processing(settings, picots_result)
            
            # Display results if processing is complete
            if st.session_state.batch_processing_complete:
                self._display_batch_results()
    
    def _perform_batch_processing(self, settings: Dict[str, Any], picots_result: Dict[str, Any] = None) -> None:
        """Perform batch processing with progress tracking."""
        # Validate API key
        is_valid, error_msg = self.extraction_engine.validate_api_key(
            st.session_state.batch_provider
        )
        
        if not is_valid:
            st.error(error_msg)
            return
        
        # Setup enhanced batch progress display (Phase 3)
        picots_enhanced = picots_result and picots_result.get('picots_data') is not None
        domain_enhanced = (st.session_state.get('active_domain_profile') or 
                          st.session_state.get('domain_profile_ready'))
        
        batch_display = BatchProgressDisplay(
            len(st.session_state.batch_files),
            picots_enhanced=picots_enhanced,
            domain_enhanced=domain_enhanced
        )
        
        # Create progress callback
        progress_callback = ProgressCallbackHandler.create_batch_callback(batch_display)
        
        try:
            # Prepare PICOTS context for enhanced extraction (Phase 3)
            picots_context = None
            if picots_result and picots_result.get('picots_data'):
                picots_context = picots_result['picots_data']
                st.info(f"🎯 Processing with PICOTS context: {len(picots_context)} criteria defined")
            
            # Process files using batch coordinator
            batch_results = self.batch_coordinator.process_batch(
                files=st.session_state.batch_files,
                provider=st.session_state.batch_provider,
                model_name=st.session_state.batch_model,
                settings=settings,
                progress_callback=progress_callback,
                picots_context=picots_context  # Phase 3: PICOTS integration
            )
            
            # Store results
            st.session_state.batch_results = batch_results
            st.session_state.batch_processing_complete = True
            
            st.success("🎉 Batch processing completed!")
            
        except Exception as e:
            # Enhanced error reporting (Phase 3)
            error_msg = str(e)
            st.error(f"🚨 **Batch Processing Error**: {error_msg}")
            
            # Provide context-specific recovery suggestions
            recovery_suggestions = []
            
            if "api" in error_msg.lower() or "key" in error_msg.lower():
                recovery_suggestions.append("Check your API key configuration")
                recovery_suggestions.append("Verify network connectivity")
            elif "memory" in error_msg.lower() or "timeout" in error_msg.lower():
                recovery_suggestions.append("Try reducing batch size or file chunk size")
                recovery_suggestions.append("Check advanced settings for timeout values")
            elif "file" in error_msg.lower() or "pdf" in error_msg.lower():
                recovery_suggestions.append("Verify uploaded files are valid PDFs")
                recovery_suggestions.append("Try uploading files individually to identify problematic files")
            elif "picots" in error_msg.lower():
                recovery_suggestions.append("Check PICOTS criteria format")
                recovery_suggestions.append("Try processing without PICOTS first")
            
            if recovery_suggestions:
                st.warning("**💡 Suggested Recovery Actions:**")
                for suggestion in recovery_suggestions:
                    st.write(f"• {suggestion}")
            
            # Recovery options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Retry Batch", key="retry_batch_button"):
                    st.session_state.batch_processing_complete = False
                    st.rerun()
            
            with col2:
                if st.button("📋 View Error Details", key="error_details_button"):
                    st.code(f"Error Type: {type(e).__name__}\nMessage: {str(e)}")
            
            with col3:
                if st.button("🆕 Start Fresh", key="fresh_start_button"):
                    self._reset_batch_state()
                    st.rerun()
            
            # Log error for debugging if batch display is available
            if 'batch_display' in locals():
                batch_display.add_file_status("Processing", "error", str(e))
    
    def _display_batch_results(self) -> None:
        """Display batch processing results."""
        batch_results = st.session_state.get('batch_results', [])
        
        if not batch_results:
            st.warning("No batch results available")
            return
        
        # Display results using the results display section
        ResultsDisplaySection.create_batch_results_section(
            batch_results,
            show_download=True
        )
        
        # Reset button
        if st.button("Start New Batch", key="reset_batch_button"):
            self._reset_batch_state()
            st.rerun()
    
    def _reset_batch_state(self) -> None:
        """Reset batch processing session state."""
        # Import session state manager
        from src.app import SessionStateManager
        SessionStateManager.reset_batch_processing_state()
        
        # Clear additional state
        for key in ['batch_files', 'batch_results', 'zip_temp_dir']:
            if key in st.session_state:
                del st.session_state[key]


class BatchSettingsComponent:
    """Standalone component for batch processing settings."""
    
    @staticmethod
    def render_batch_settings(key_prefix: str = "batch") -> Dict[str, Any]:
        """
        Render batch-specific settings.
        
        Args:
            key_prefix: Prefix for session state keys
            
        Returns:
            Dictionary of batch settings
        """
        settings = {}
        
        col1, col2 = st.columns(2)
        
        with col1:
            settings['max_parallel'] = st.number_input(
                "Max Parallel Files",
                min_value=1,
                max_value=10,
                value=3,
                help="Number of files to process simultaneously",
                key=f"{key_prefix}_max_parallel"
            )
        
        with col2:
            settings['timeout_minutes'] = st.number_input(
                "Timeout (minutes)",
                min_value=5,
                max_value=120,
                value=30,
                help="Maximum time per file",
                key=f"{key_prefix}_timeout"
            )
        
        settings['fail_fast'] = st.checkbox(
            "Stop on First Error",
            value=False,
            help="Stop batch processing if any file fails",
            key=f"{key_prefix}_fail_fast"
        )
        
        settings['save_intermediate'] = st.checkbox(
            "Save Intermediate Results",
            value=True,
            help="Save results as each file completes",
            key=f"{key_prefix}_save_intermediate"
        )
        
        return settings


class BatchFileUploadComponent:
    """Enhanced file upload component for batch processing (Phase 3)."""
    
    @staticmethod
    def _render_unified_upload_interface() -> Dict[str, Any]:
        """
        Phase 3: Unified upload interface that gracefully handles 1 or many files.
        Eliminates the artificial distinction between upload methods.
        """
        result = {
            'upload_type': 'unified',
            'uploaded_files': [],
            'zip_files': [],
            'total_files': 0
        }
        
        # Enhanced upload description
        st.markdown("""
        **📤 Flexible Upload Options:**
        - Upload **single** or **multiple** PDF files at once
        - Upload **ZIP archives** containing PDFs (auto-detected and extracted)
        - Mix and match: Upload some PDFs directly + ZIP files in the same session
        """)
        
        # Single unified upload widget that accepts everything
        st.markdown("#### Drop your files here or click to browse:")
        uploaded_items = st.file_uploader(
            "Upload PDF files or ZIP archives",
            type=['pdf', 'zip'],
            accept_multiple_files=True,
            help="Select one or more PDF files, or ZIP files containing PDFs. All will be processed together.",
            key="unified_batch_uploader"
        )
        
        if uploaded_items:
            # Process all uploaded items automatically
            pdf_files = []
            zip_files = []
            
            # Categorize uploads automatically
            for item in uploaded_items:
                if item.name.lower().endswith('.pdf'):
                    pdf_files.append(item)
                elif item.name.lower().endswith('.zip'):
                    zip_files.append(item)
            
            # Enhanced visual feedback
            BatchFileUploadComponent._display_upload_summary(pdf_files, zip_files)
            
            # Auto-process ZIP files (Phase 3: streamlined workflow)
            all_pdf_files = pdf_files.copy()
            if zip_files:
                extracted_pdfs = BatchFileUploadComponent._auto_extract_zip_files(zip_files)
                all_pdf_files.extend(extracted_pdfs)
            
            # Update session state
            if all_pdf_files:
                st.session_state.batch_files = all_pdf_files
                result['uploaded_files'] = all_pdf_files
                result['total_files'] = len(all_pdf_files)
                
                # Success feedback with batch context
                st.success(f"✅ **Ready for processing:** {len(all_pdf_files)} PDF files loaded")
                
                # Show file list in expandable section
                with st.expander(f"📋 View {len(all_pdf_files)} uploaded files", expanded=False):
                    for i, file in enumerate(all_pdf_files[:10]):  # Show max 10
                        file_size = len(file.getvalue()) / 1024 / 1024  # MB
                        st.write(f"{i+1}. **{file.name}** ({file_size:.1f} MB)")
                    if len(all_pdf_files) > 10:
                        st.write(f"... and {len(all_pdf_files) - 10} more files")
        
        else:
            # Empty state with helpful guidance
            st.info("📁 **No files uploaded yet.** Select PDF files or ZIP archives to get started.")
        
        return result
    
    @staticmethod
    def _display_upload_summary(pdf_files: List, zip_files: List) -> None:
        """Display enhanced upload summary with visual feedback."""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if pdf_files:
                st.metric("📄 PDF Files", len(pdf_files))
                total_pdf_size = sum(len(f.getvalue()) for f in pdf_files) / 1024 / 1024
                st.caption(f"Total size: {total_pdf_size:.1f} MB")
        
        with col2:
            if zip_files:
                st.metric("📦 ZIP Archives", len(zip_files))
                total_zip_size = sum(len(f.getvalue()) for f in zip_files) / 1024 / 1024
                st.caption(f"Total size: {total_zip_size:.1f} MB")
        
        with col3:
            total_items = len(pdf_files) + len(zip_files)
            st.metric("📁 Total Items", total_items)
            st.caption("Mixed upload detected" if pdf_files and zip_files else "Single type upload")
    
    @staticmethod
    def _auto_extract_zip_files(zip_files: List) -> List:
        """
        Phase 3: Automatic ZIP extraction with progress feedback.
        Streamlined workflow without manual confirmation steps.
        """
        extracted_pdfs = []
        
        for zip_file in zip_files:
            with st.spinner(f"🔄 Extracting {zip_file.name}..."):
                try:
                    # Auto-extract without confirmation (Phase 3 improvement)
                    from src.utils.zip_processor import ZipProcessor
                    zip_processor = ZipProcessor(max_files=50, max_file_size_mb=100)
                    
                    # Validate and extract in one step
                    is_valid, validation_errors, zip_info = zip_processor.validate_zip_file(
                        zip_file.getvalue()
                    )
                    
                    if is_valid:
                        # Extract directly to temporary files
                        with tempfile.TemporaryDirectory() as temp_dir:
                            extracted_files = zip_processor.extract_zip_file(
                                zip_file.getvalue(),
                                temp_dir
                            )
                            
                            # Convert to file objects
                            file_objects = BatchFileUploadComponent._convert_extracted_files_to_objects(extracted_files)
                            extracted_pdfs.extend(file_objects)
                            
                            st.success(f"✅ Extracted {len(file_objects)} PDFs from {zip_file.name}")
                    else:
                        st.error(f"❌ Invalid ZIP file: {zip_file.name}")
                        for error in validation_errors:
                            st.error(f"  • {error}")
                
                except Exception as e:
                    st.error(f"❌ Error extracting {zip_file.name}: {str(e)}")
        
        return extracted_pdfs
    
    @staticmethod
    def _convert_extracted_files_to_objects(extracted_files: List[Dict[str, Any]]) -> List:
        """Convert extracted files to file-like objects."""
        file_objects = []
        
        for file_info in extracted_files:
            class FileObject:
                def __init__(self, name, path):
                    self.name = name
                    self.path = path
                    with open(path, 'rb') as f:
                        self._content = f.read()
                
                def getbuffer(self):
                    return self._content
                
                def getvalue(self):
                    return self._content
            
            file_objects.append(FileObject(file_info['name'], file_info['path']))
        
        return file_objects


class BatchResultsComponent:
    """Component for displaying batch processing results."""
    
    @staticmethod
    def display_batch_summary(batch_results: List[Dict[str, Any]]) -> None:
        """
        Display batch processing summary.
        
        Args:
            batch_results: List of batch processing results
        """
        if not batch_results:
            st.warning("No batch results to display")
            return
        
        st.subheader("📊 Batch Processing Summary")
        
        # Calculate summary statistics
        total_files = len(batch_results)
        successful_files = sum(1 for result in batch_results if result.get('status') == 'success')
        failed_files = total_files - successful_files
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Files", total_files)
        
        with col2:
            st.metric("Successful", successful_files)
        
        with col3:
            st.metric("Failed", failed_files)
        
        with col4:
            success_rate = successful_files / total_files if total_files > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1%}")
        
        # Progress visualization
        st.progress(success_rate, text=f"Overall Success Rate: {success_rate:.1%}")
    
    @staticmethod
    def display_file_results(batch_results: List[Dict[str, Any]]) -> None:
        """
        Display individual file results.
        
        Args:
            batch_results: List of batch processing results
        """
        st.subheader("📋 Individual File Results")
        
        for result in batch_results:
            filename = result.get('filename', 'Unknown File')
            status = result.get('status', 'unknown')
            
            # Status icon and color
            if status == 'success':
                icon = "✅"
                expanded = False
            elif status == 'error':
                icon = "❌"
                expanded = True
            else:
                icon = "⚠️"
                expanded = True
            
            with st.expander(f"{icon} {filename}", expanded=expanded):
                if status == 'success':
                    extraction_results = result.get('results', [])
                    if extraction_results:
                        # Display condensed results
                        st.write(f"**Chunks processed:** {len(extraction_results)}")
                        
                        # Show first few extractions as preview
                        if len(extraction_results) > 0:
                            st.write("**Sample extraction:**")
                            sample = extraction_results[0].get('extraction', 'No data')
                            st.text(sample[:200] + "..." if len(sample) > 200 else sample)
                    else:
                        st.info("No extraction results available")
                else:
                    error_message = result.get('error', 'Unknown error')
                    st.error(f"Processing failed: {error_message}")
                    
                    # Show additional error details if available
                    if 'details' in result:
                        st.write("**Error details:**")
                        st.code(result['details'])