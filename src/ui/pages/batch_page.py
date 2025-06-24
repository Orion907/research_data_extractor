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
        """Render the complete batch processing page."""
        # Page header
        st.header("🔄 Batch Processing")
        st.markdown("""
        Process multiple research articles at once. Upload multiple PDF files or a ZIP archive 
        containing PDFs to extract patient characteristics from all articles simultaneously.
        """)
        
        # Initialize session state
        self._initialize_session_state()
        
        # Render provider and model selection
        self._render_provider_selection()
        
        # Render advanced settings
        settings = self._render_advanced_settings()
        
        # File upload section
        upload_result = self._render_file_upload_section()
        
        # Processing section
        if st.session_state.batch_files:
            self._render_processing_section(settings)
    
    def _initialize_session_state(self) -> None:
        """Initialize session state for batch processing."""
        if 'batch_files' not in st.session_state:
            st.session_state.batch_files = []
        if 'batch_processing_complete' not in st.session_state:
            st.session_state.batch_processing_complete = False
        if 'batch_results' not in st.session_state:
            st.session_state.batch_results = []
    
    def _render_provider_selection(self) -> None:
        """Render LLM provider and model selection."""
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
            models = self.extraction_engine.get_available_models(st.session_state.batch_provider)
            
            if 'batch_model' not in st.session_state:
                st.session_state.batch_model = models[0]
            
            st.session_state.batch_model = st.selectbox(
                "Model", 
                models, 
                key="batch_model_select"
            )
    
    def _render_advanced_settings(self) -> Dict[str, Any]:
        """
        Render advanced settings.
        
        Returns:
            Dictionary of setting values
        """
        with st.expander("⚙️ Advanced Settings"):
            settings = ExtractionSettingsComponent.render_processing_settings(
                self.config,
                self.extraction_engine,
                key_prefix="batch"
            )
            
            # Add batch-specific settings
            settings['max_parallel'] = st.number_input(
                "Max Parallel Processing",
                min_value=1,
                max_value=5,
                value=2,
                help="Number of files to process simultaneously",
                key="batch_max_parallel"
            )
            
            settings['timeout_per_file'] = st.number_input(
                "Timeout per File (minutes)",
                min_value=5,
                max_value=60,
                value=15,
                help="Maximum time to spend on each file",
                key="batch_timeout"
            )
        
        return settings
    
    def _render_file_upload_section(self) -> Dict[str, Any]:
        """
        Render file upload section.
        
        Returns:
            Upload results
        """
        st.markdown("---")
        
        # Use the batch upload section
        upload_result = FileUploadSection.batch_upload_section()
        
        # Handle ZIP extraction if needed
        if upload_result['upload_type'] == 'zip' and upload_result['zip_file']:
            self._handle_zip_extraction(upload_result['zip_file'])
        elif upload_result['upload_type'] == 'multiple_files' and upload_result['uploaded_files']:
            st.session_state.batch_files = upload_result['uploaded_files']
        
        return upload_result
    
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
    
    def _render_processing_section(self, settings: Dict[str, Any]) -> None:
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
                self._perform_batch_processing(settings)
            
            # Display results if processing is complete
            if st.session_state.batch_processing_complete:
                self._display_batch_results()
    
    def _perform_batch_processing(self, settings: Dict[str, Any]) -> None:
        """Perform batch processing with progress tracking."""
        # Validate API key
        is_valid, error_msg = self.extraction_engine.validate_api_key(
            st.session_state.batch_provider
        )
        
        if not is_valid:
            st.error(error_msg)
            return
        
        # Setup batch progress display
        batch_display = BatchProgressDisplay(len(st.session_state.batch_files))
        
        # Create progress callback
        progress_callback = ProgressCallbackHandler.create_batch_callback(batch_display)
        
        try:
            # Process files using batch coordinator
            batch_results = self.batch_coordinator.process_batch(
                files=st.session_state.batch_files,
                provider=st.session_state.batch_provider,
                model_name=st.session_state.batch_model,
                settings=settings,
                progress_callback=progress_callback
            )
            
            # Store results
            st.session_state.batch_results = batch_results
            st.session_state.batch_processing_complete = True
            
            st.success("🎉 Batch processing completed!")
            
        except Exception as e:
            st.error(f"Error during batch processing: {str(e)}")
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