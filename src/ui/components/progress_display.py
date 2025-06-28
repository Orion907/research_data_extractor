"""
Progress Display Component

Reusable progress display components with consistent styling and status updates.
"""

import streamlit as st
import time
from typing import Optional, List, Dict, Any, Callable
from contextlib import contextmanager


class ProgressDisplayComponent:
    """Reusable progress display component for various processing tasks."""
    
    @staticmethod
    def create_progress_bar(
        label: str = "Processing...",
        initial_value: float = 0.0,
        key: Optional[str] = None
    ) -> Any:
        """
        Create a progress bar with label.
        
        Args:
            label: Label to display above progress bar
            initial_value: Initial progress value (0.0 to 1.0)
            key: Unique key for the progress bar
            
        Returns:
            Streamlit progress bar object
        """
        if label:
            st.text(label)
        return st.progress(initial_value, text=key)
    
    @staticmethod
    def update_progress_bar(progress_bar: Any, value: float, label: str = None) -> None:
        """
        Update progress bar value and optional label.
        
        Args:
            progress_bar: The progress bar object to update
            value: Progress value (0.0 to 1.0)
            label: Optional label to update
        """
        if label:
            progress_bar.progress(value, text=label)
        else:
            progress_bar.progress(value)
    
    @staticmethod
    @contextmanager
    def spinner_context(message: str = "Processing..."):
        """
        Context manager for spinner display.
        
        Args:
            message: Message to display with spinner
        """
        with st.spinner(message):
            yield
    
    @staticmethod
    def show_status_message(
        message: str,
        status_type: str = "info",
        icon: Optional[str] = None
    ) -> None:
        """
        Display a status message with appropriate styling.
        
        Args:
            message: Message to display
            status_type: Type of status ('success', 'error', 'warning', 'info')
            icon: Optional icon to display with message
        """
        if icon:
            message = f"{icon} {message}"
            
        if status_type == "success":
            st.success(message)
        elif status_type == "error":
            st.error(message)
        elif status_type == "warning":
            st.warning(message)
        else:  # info or default
            st.info(message)
    
    @staticmethod
    def show_file_processing_status(
        filename: str,
        text_length: int,
        chunk_count: int,
        status: str = "success",
        picots_enhanced: bool = False,
        domain_enhanced: bool = False
    ) -> None:
        """
        Display file processing status with enhanced format (Phase 3).
        
        Args:
            filename: Name of the file being processed
            text_length: Length of extracted text
            chunk_count: Number of chunks processed
            status: Processing status
            picots_enhanced: Whether PICOTS criteria were used
            domain_enhanced: Whether domain profile was used
        """
        # Build enhancement indicators
        enhancements = []
        if picots_enhanced:
            enhancements.append("🎯 PICOTS")
        if domain_enhanced:
            enhancements.append("🗺️ Domain")
        
        enhancement_text = f" ({', '.join(enhancements)})" if enhancements else ""
        
        # Status icon
        if status == "success":
            icon = "✅"
            status_func = st.success
        elif status == "error":
            icon = "❌"
            status_func = st.error
        elif status == "warning":
            icon = "⚠️"
            status_func = st.warning
        else:
            icon = "ℹ️"
            status_func = st.info
        
        # Format message with enhancements
        message = f"{icon} **{filename}** - {chunk_count} chunks, {text_length:,} characters{enhancement_text}"
        status_func(message)


class BatchProgressDisplay:
    """Specialized progress display for batch processing operations with enhancement tracking."""
    
    def __init__(self, total_files: int, picots_enhanced: bool = False, domain_enhanced: bool = False):
        """
        Initialize batch progress display with enhancement tracking (Phase 3).
        
        Args:
            total_files: Total number of files to process
            picots_enhanced: Whether PICOTS criteria are being used
            domain_enhanced: Whether domain profile is being used
        """
        self.total_files = total_files
        self.current_file = 0
        self.picots_enhanced = picots_enhanced
        self.domain_enhanced = domain_enhanced
        self.progress_bar = None
        self.status_container = None
        self.file_statuses = []
        self.setup_display()
    
    def setup_display(self) -> None:
        """Setup the batch progress display elements with enhancement indicators."""
        # Enhancement indicators in header
        enhancement_badges = []
        if self.picots_enhanced:
            enhancement_badges.append("🎯 PICOTS-Enhanced")
        if self.domain_enhanced:
            enhancement_badges.append("🗺️ Domain-Enhanced")
        
        header_text = "📊 Batch Processing Progress"
        if enhancement_badges:
            header_text += f" ({', '.join(enhancement_badges)})"
        
        st.subheader(header_text)
        
        # Show batch enhancement summary
        if self.picots_enhanced or self.domain_enhanced:
            enhancement_info = []
            if self.picots_enhanced:
                enhancement_info.append("**PICOTS**: Targeted extraction based on research criteria")
            if self.domain_enhanced:
                enhancement_info.append("**Domain Profile**: Enhanced vocabulary and synonym recognition")
            
            st.info(" • ".join(enhancement_info))
        
        # Overall progress
        self.progress_bar = st.progress(0.0)
        
        # Status container for updates
        self.status_container = st.empty()
        
        # File status container
        self.file_status_container = st.container()
    
    def update_overall_progress(self, completed_files: int, message: str = None) -> None:
        """
        Update overall batch progress.
        
        Args:
            completed_files: Number of completed files
            message: Optional status message
        """
        self.current_file = completed_files
        progress = completed_files / self.total_files if self.total_files > 0 else 0
        
        progress_text = f"Processing file {completed_files + 1} of {self.total_files}"
        if message:
            progress_text = f"{progress_text}: {message}"
            
        self.progress_bar.progress(progress, text=progress_text)
        
        # Update status
        with self.status_container:
            if completed_files == self.total_files:
                st.success(f"✅ Batch processing complete! Processed {self.total_files} files.")
            else:
                st.info(f"🔄 {progress_text}")
    
    def add_file_status(self, filename: str, status: str, details: str = None) -> None:
        """
        Add file processing status to the display.
        
        Args:
            filename: Name of the file
            status: Status ('processing', 'success', 'error', 'warning')
            details: Optional details about the processing
        """
        with self.file_status_container:
            if status == "processing":
                icon = "🔄"
                color = "blue"
            elif status == "success":
                icon = "✅"
                color = "green"
            elif status == "error":
                icon = "❌"
                color = "red"
            elif status == "warning":
                icon = "⚠️"
                color = "orange"
            else:
                icon = "ℹ️"
                color = "gray"
            
            # Create status message
            status_message = f"{icon} **{filename}**"
            if details:
                status_message += f" - {details}"
            
            # Display with appropriate styling
            if status == "error":
                st.error(status_message)
            elif status == "warning":
                st.warning(status_message)
            elif status == "success":
                st.success(status_message)
            else:
                st.info(status_message)


class ChunkProgressTracker:
    """Progress tracker for chunk-by-chunk processing."""
    
    def __init__(self, total_chunks: int, filename: str = None):
        """
        Initialize chunk progress tracker.
        
        Args:
            total_chunks: Total number of chunks to process
            filename: Optional filename being processed
        """
        self.total_chunks = total_chunks
        self.filename = filename
        self.current_chunk = 0
        self.progress_bar = None
        self.setup_display()
    
    def setup_display(self) -> None:
        """Setup the chunk progress display."""
        title = "📝 Processing Chunks"
        if self.filename:
            title += f" - {self.filename}"
        
        st.subheader(title)
        self.progress_bar = st.progress(0.0)
        self.status_container = st.empty()
    
    def update_progress(self, current_chunk: int, status: str = None) -> None:
        """
        Update chunk processing progress.
        
        Args:
            current_chunk: Current chunk number (1-based from callback)
            status: Optional status message
        """
        self.current_chunk = current_chunk
        # Ensure progress never exceeds 1.0
        progress = min(self.current_chunk / self.total_chunks, 1.0) if self.total_chunks > 0 else 0
        
        progress_text = f"Chunk {self.current_chunk} of {self.total_chunks}"
        if status:
            progress_text += f" - {status}"
        
        self.progress_bar.progress(progress, text=progress_text)
        
        with self.status_container:
            if self.current_chunk == self.total_chunks:
                st.success(f"✅ Completed processing {self.total_chunks} chunks!")
            else:
                st.info(f"🔄 {progress_text}")
    
    def finish(self, success: bool = True, message: str = None) -> None:
        """
        Mark processing as finished.
        
        Args:
            success: Whether processing completed successfully
            message: Optional completion message
        """
        self.progress_bar.progress(1.0)
        
        with self.status_container:
            if success:
                final_message = f"✅ Successfully processed {self.total_chunks} chunks"
                if message:
                    final_message += f" - {message}"
                st.success(final_message)
            else:
                error_message = f"❌ Processing failed"
                if message:
                    error_message += f" - {message}"
                st.error(error_message)


class ProcessingStepsDisplay:
    """Display processing steps with status indicators."""
    
    def __init__(self, steps: List[str]):
        """
        Initialize processing steps display.
        
        Args:
            steps: List of processing step names
        """
        self.steps = steps
        self.current_step = 0
        self.step_status = ['pending'] * len(steps)
        self.setup_display()
    
    def setup_display(self) -> None:
        """Setup the processing steps display."""
        st.subheader("🔧 Processing Steps")
        self.steps_container = st.container()
        self.update_display()
    
    def update_display(self) -> None:
        """Update the visual display of processing steps."""
        with self.steps_container:
            for i, (step, status) in enumerate(zip(self.steps, self.step_status)):
                if status == 'completed':
                    icon = "✅"
                elif status == 'processing':
                    icon = "🔄"
                elif status == 'error':
                    icon = "❌"
                else:  # pending
                    icon = "⏳"
                
                st.write(f"{icon} **Step {i+1}:** {step}")
    
    def start_step(self, step_index: int) -> None:
        """
        Mark a step as started.
        
        Args:
            step_index: Index of the step to start
        """
        if 0 <= step_index < len(self.steps):
            self.step_status[step_index] = 'processing'
            self.current_step = step_index
            self.update_display()
    
    def complete_step(self, step_index: int, success: bool = True) -> None:
        """
        Mark a step as completed.
        
        Args:
            step_index: Index of the step to complete
            success: Whether the step completed successfully
        """
        if 0 <= step_index < len(self.steps):
            self.step_status[step_index] = 'completed' if success else 'error'
            self.update_display()
    
    def finish_all(self, success: bool = True) -> None:
        """
        Mark all steps as completed.
        
        Args:
            success: Whether all steps completed successfully
        """
        final_status = 'completed' if success else 'error'
        self.step_status = [final_status] * len(self.steps)
        self.update_display()
        
        if success:
            st.success("🎉 All processing steps completed successfully!")
        else:
            st.error("❌ Processing failed. Please check the logs for details.")


class ProgressCallbackHandler:
    """Helper class to create progress callbacks for processing functions."""
    
    @staticmethod
    def create_chunk_callback(progress_tracker: ChunkProgressTracker) -> Callable:
        """
        Create a progress callback for chunk processing.
        
        Args:
            progress_tracker: The chunk progress tracker to update
            
        Returns:
            Callback function for chunk processing
        """
        def callback(current: int, total: int, status: str = None):
            progress_tracker.update_progress(current, status)
        
        return callback
    
    @staticmethod
    def create_batch_callback(batch_display: BatchProgressDisplay) -> Callable:
        """
        Create a progress callback for batch processing.
        
        Args:
            batch_display: The batch progress display to update
            
        Returns:
            Callback function for batch processing
        """
        def callback(completed_files: int, total_files: int, current_file: str = None):
            message = f"Processing {current_file}" if current_file else None
            batch_display.update_overall_progress(completed_files, message)
        
        return callback