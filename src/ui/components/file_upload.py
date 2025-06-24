"""
File Upload Component

Reusable file upload widgets with consistent styling and validation.
"""

import streamlit as st
import tempfile
import os
from typing import Optional, List, Dict, Any
from pathlib import Path


class FileUploadComponent:
    """Reusable file upload component with validation and processing."""
    
    @staticmethod
    def pdf_uploader(
        label: str = "Upload a research article PDF",
        key: Optional[str] = None,
        help_text: Optional[str] = None,
        accept_multiple_files: bool = False
    ) -> Optional[Any]:
        """
        Create a PDF file uploader with validation.
        
        Args:
            label: Label for the file uploader
            key: Unique key for the widget
            help_text: Help text to display
            accept_multiple_files: Whether to accept multiple files
            
        Returns:
            Uploaded file object(s) or None
        """
        uploaded_file = st.file_uploader(
            label,
            type=["pdf"],
            key=key,
            help=help_text,
            accept_multiple_files=accept_multiple_files
        )
        
        if uploaded_file is not None:
            if accept_multiple_files:
                # Validate each file
                valid_files = []
                for file in uploaded_file:
                    if FileUploadComponent._validate_pdf_file(file):
                        valid_files.append(file)
                    else:
                        st.error(f"Invalid PDF file: {file.name}")
                return valid_files if valid_files else None
            else:
                # Validate single file
                if FileUploadComponent._validate_pdf_file(uploaded_file):
                    return uploaded_file
                else:
                    st.error(f"Invalid PDF file: {uploaded_file.name}")
                    return None
        
        return None
    
    @staticmethod
    def batch_pdf_uploader(
        label: str = "Upload multiple PDF files for batch processing",
        key: Optional[str] = None,
    ) -> Optional[List[Any]]:
        """
        Create a batch PDF file uploader.
        
        Args:
            label: Label for the file uploader
            key: Unique key for the widget
            
        Returns:
            List of uploaded file objects or None
        """
        return FileUploadComponent.pdf_uploader(
            label=label,
            key=key,
            help_text="Select multiple PDF files to process in batch",
            accept_multiple_files=True
        )
    
    @staticmethod
    def zip_uploader(
        label: str = "Upload a ZIP file containing PDFs",
        key: Optional[str] = None,
        help_text: Optional[str] = None
    ) -> Optional[Any]:
        """
        Create a ZIP file uploader for batch processing.
        
        Args:
            label: Label for the file uploader
            key: Unique key for the widget
            help_text: Help text to display
            
        Returns:
            Uploaded ZIP file object or None
        """
        uploaded_file = st.file_uploader(
            label,
            type=["zip"],
            key=key,
            help=help_text or "Upload a ZIP file containing PDF documents"
        )
        
        if uploaded_file is not None:
            if FileUploadComponent._validate_zip_file(uploaded_file):
                return uploaded_file
            else:
                st.error(f"Invalid ZIP file: {uploaded_file.name}")
                return None
        
        return None
    
    @staticmethod
    def display_file_info(uploaded_file: Any, show_details: bool = True) -> None:
        """
        Display information about the uploaded file.
        
        Args:
            uploaded_file: The uploaded file object
            show_details: Whether to show detailed file information
        """
        if uploaded_file is None:
            return
            
        st.success(f"✅ File uploaded: **{uploaded_file.name}**")
        
        if show_details:
            file_size = len(uploaded_file.getvalue()) / 1024 / 1024  # Convert to MB
            st.info(f"📄 File size: {file_size:.2f} MB")
            
            # Display file type
            file_type = uploaded_file.type if hasattr(uploaded_file, 'type') else 'Unknown'
            st.info(f"📋 File type: {file_type}")
    
    @staticmethod
    def display_batch_file_info(uploaded_files: List[Any]) -> None:
        """
        Display information about multiple uploaded files.
        
        Args:
            uploaded_files: List of uploaded file objects
        """
        if not uploaded_files:
            return
            
        st.success(f"✅ {len(uploaded_files)} files uploaded successfully")
        
        total_size = 0
        for file in uploaded_files:
            file_size = len(file.getvalue()) / 1024 / 1024  # Convert to MB
            total_size += file_size
        
        st.info(f"📄 Total size: {total_size:.2f} MB")
        
        # Show file list in expandable section
        with st.expander("📋 View uploaded files"):
            for i, file in enumerate(uploaded_files, 1):
                file_size = len(file.getvalue()) / 1024 / 1024  # Convert to MB
                st.write(f"{i}. **{file.name}** ({file_size:.2f} MB)")
    
    @staticmethod
    def _validate_pdf_file(uploaded_file: Any) -> bool:
        """
        Validate that the uploaded file is a valid PDF.
        
        Args:
            uploaded_file: The uploaded file object
            
        Returns:
            True if valid PDF, False otherwise
        """
        if not uploaded_file:
            return False
            
        # Check file extension
        if not uploaded_file.name.lower().endswith('.pdf'):
            return False
            
        # Check file size (max 50MB)
        file_size = len(uploaded_file.getvalue()) / 1024 / 1024
        if file_size > 50:
            st.error(f"File too large: {file_size:.2f} MB. Maximum size is 50 MB.")
            return False
            
        # Check PDF magic bytes
        file_content = uploaded_file.getvalue()
        if not file_content.startswith(b'%PDF-'):
            st.error("File does not appear to be a valid PDF.")
            return False
            
        return True
    
    @staticmethod
    def _validate_zip_file(uploaded_file: Any) -> bool:
        """
        Validate that the uploaded file is a valid ZIP.
        
        Args:
            uploaded_file: The uploaded file object
            
        Returns:
            True if valid ZIP, False otherwise
        """
        if not uploaded_file:
            return False
            
        # Check file extension
        if not uploaded_file.name.lower().endswith('.zip'):
            return False
            
        # Check file size (max 100MB)
        file_size = len(uploaded_file.getvalue()) / 1024 / 1024
        if file_size > 100:
            st.error(f"ZIP file too large: {file_size:.2f} MB. Maximum size is 100 MB.")
            return False
            
        # Check ZIP magic bytes
        file_content = uploaded_file.getvalue()
        if not file_content.startswith(b'PK\x03\x04'):
            st.error("File does not appear to be a valid ZIP archive.")
            return False
            
        return True


class FileUploadSection:
    """Higher-level file upload section with integrated PICOTS input."""
    
    @staticmethod
    def single_document_upload_section() -> Dict[str, Any]:
        """
        Create a complete single document upload section.
        
        Returns:
            Dictionary containing upload results and PICOTS data
        """
        result = {
            'uploaded_file': None,
            'picots_text': None,
            'picots_data': None
        }
        
        # File upload
        uploaded_file = FileUploadComponent.pdf_uploader(
            "Upload a research article PDF",
            key="single_doc_upload"
        )
        
        if uploaded_file:
            FileUploadComponent.display_file_info(uploaded_file)
            result['uploaded_file'] = uploaded_file
        
        # PICOTS criteria section
        result.update(FileUploadSection._picots_input_section())
        
        return result
    
    @staticmethod
    def batch_upload_section() -> Dict[str, Any]:
        """
        Create a complete batch upload section.
        
        Returns:
            Dictionary containing upload results and options
        """
        result = {
            'uploaded_files': None,
            'upload_type': 'multiple_files',
            'zip_file': None
        }
        
        st.subheader("📄 Batch File Upload")
        
        # Upload type selection
        upload_type = st.radio(
            "Choose upload method:",
            ["Multiple PDF files", "ZIP archive"],
            key="batch_upload_type"
        )
        
        if upload_type == "Multiple PDF files":
            uploaded_files = FileUploadComponent.batch_pdf_uploader(
                key="batch_pdf_upload"
            )
            
            if uploaded_files:
                FileUploadComponent.display_batch_file_info(uploaded_files)
                result['uploaded_files'] = uploaded_files
                result['upload_type'] = 'multiple_files'
        
        else:  # ZIP archive
            zip_file = FileUploadComponent.zip_uploader(
                key="batch_zip_upload"
            )
            
            if zip_file:
                FileUploadComponent.display_file_info(zip_file)
                result['zip_file'] = zip_file
                result['upload_type'] = 'zip'
        
        return result
    
    @staticmethod
    def _picots_input_section() -> Dict[str, Any]:
        """
        Create PICOTS criteria input section.
        
        Returns:
            Dictionary containing PICOTS text and parsed data
        """
        result = {
            'picots_text': None,
            'picots_data': None
        }
        
        st.markdown("---")
        st.subheader("📊 PICOTS Criteria (Optional)")
        st.markdown("Paste your PICOTS criteria below to customize the extraction focus.")
        
        # PICOTS explanation
        with st.expander("📋 What is PICOTS?", expanded=False):
            st.markdown("""
            **PICOTS** helps focus research extraction:
            - **P**opulation: Who are the study participants?
            - **I**ntervention: What treatment/exposure is being studied?
            - **C**omparison: What is the control or comparison group?
            - **O**utcomes: What outcomes are being measured?
            - **T**iming: What is the timeframe?
            - **S**etting: Where is the study conducted?
            """)
        
        # PICOTS text input
        picots_text = st.text_area(
            "Paste your PICOTS criteria here:",
            height=200,
            placeholder="""Example format:
Population: Adults aged 18-65 with type 2 diabetes
Intervention: Metformin therapy
Comparison: Placebo or standard care
Outcomes: HbA1c reduction, weight loss, adverse events
Timing: 12-week treatment period
Setting: Outpatient clinics

Abbreviations: HbA1c = Hemoglobin A1c; BMI = Body Mass Index""",
            help="Copy and paste your PICOTS criteria from your protocol document. Including abbreviations helps improve extraction accuracy!",
            key="picots_input"
        )
        
        if picots_text:
            result['picots_text'] = picots_text
            # Parse PICOTS data if parser is available
            try:
                from src.utils.picots_parser import PicotsParser
                parser = PicotsParser()
                picots_data = parser.parse_picots_text(picots_text)
                result['picots_data'] = picots_data
                
                # Display parsed PICOTS in expandable section
                if picots_data:
                    with st.expander("📋 Parsed PICOTS Criteria", expanded=False):
                        for key, value in picots_data.items():
                            if value:
                                st.write(f"**{key.title()}:** {value}")
            
            except ImportError:
                # PICOTS parser not available
                pass
        
        return result