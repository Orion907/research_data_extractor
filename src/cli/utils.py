"""
Utility functions for the CLI
"""
import os
import sys
import click
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

def validate_input_directory(input_dir: str) -> Path:
    """
    Validate that input directory exists and contains PDF files
    
    Args:
        input_dir (str): Input directory path
        
    Returns:
        Path: Validated Path object
        
    Raises:
        click.ClickException: If directory is invalid
    """
    path = Path(input_dir)
    
    if not path.exists():
        raise click.ClickException(f"Input directory does not exist: {input_dir}")
    
    if not path.is_dir():
        raise click.ClickException(f"Input path is not a directory: {input_dir}")
    
    # Check for PDF files
    pdf_files = list(path.glob("*.pdf"))
    if not pdf_files:
        raise click.ClickException(f"No PDF files found in directory: {input_dir}")
    
    click.echo(f"Found {len(pdf_files)} PDF files in {input_dir}")
    return path

def ensure_output_directory(output_dir: str) -> Path:
    """
    Ensure output directory exists, create if necessary
    
    Args:
        output_dir (str): Output directory path
        
    Returns:
        Path: Output directory Path object
    """
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Output directory ready: {path}")
    return path

def validate_file_exists(file_path: str, file_type: str = "file") -> Path:
    """
    Validate that a file exists
    
    Args:
        file_path (str): File path to validate
        file_type (str): Description of file type for error messages
        
    Returns:
        Path: Validated Path object
        
    Raises:
        click.ClickException: If file doesn't exist
    """
    path = Path(file_path)
    if not path.exists():
        raise click.ClickException(f"{file_type.title()} does not exist: {file_path}")
    
    if not path.is_file():
        raise click.ClickException(f"Path is not a file: {file_path}")
    
    return path

def setup_logging(verbose: bool = False) -> None:
    """
    Setup logging configuration for CLI
    
    Args:
        verbose (bool): Enable debug logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        force=True
    )
    
    # Suppress some noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

def get_default_output_filename(input_path: Path, suffix: str = "extracted") -> str:
    """
    Generate default output filename based on input
    
    Args:
        input_path (Path): Input file path
        suffix (str): Suffix to add to filename
        
    Returns:
        str: Generated output filename
    """
    stem = input_path.stem  # filename without extension
    return f"{stem}_{suffix}.csv"

def display_progress_summary(processed: int, failed: int, total: int) -> None:
    """
    Display a summary of processing results
    
    Args:
        processed (int): Number of successfully processed files
        failed (int): Number of failed files
        total (int): Total number of files
    """
    click.echo("\n" + "="*50)
    click.echo("PROCESSING SUMMARY")
    click.echo("="*50)
    click.echo(f"Total files: {total}")
    click.echo(f"Successfully processed: {processed}")
    click.echo(f"Failed: {failed}")
    
    if total > 0:
        success_rate = (processed / total) * 100
        click.echo(f"Success rate: {success_rate:.1f}%")
    
    if failed > 0:
        click.echo(f"\n⚠️  {failed} files failed processing")
    else:
        click.echo(f"\n✅ All files processed successfully!")