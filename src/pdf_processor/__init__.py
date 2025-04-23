"""
PDF Processing module for extracting and processing text from research articles
"""
from .pdf_processor import extract_text_from_pdf
from .text_chunker import chunk_text

# This makes the functions directly importable from src.pdf_processing
__all__ = ['extract_text_from_pdf', 'chunk_text']