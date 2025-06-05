"""
Main CLI entry point for Research Data Extractor
"""
import click
import logging
import os
from pathlib import Path

# Configure logging for CLI
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@click.group()
@click.version_option(version="0.1.0")
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
def cli(verbose, config):
    """
    Research Data Extractor - Extract patient characteristics from research articles
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    if config:
        logger.info(f"Using config file: {config}")
        # TODO: Load configuration from file

@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file path')
@click.option('--provider', default='anthropic', 
              type=click.Choice(['anthropic', 'openai', 'mock']), 
              help='LLM provider to use')
@click.option('--model', help='Model name to use')
@click.option('--template', default='patient_characteristics', help='Template ID to use')
def extract(input_file, output, provider, model, template):
    """Extract data from a single PDF file"""
    click.echo(f"Extracting from: {input_file}")
    click.echo(f"Provider: {provider}")
    click.echo(f"Template: {template}")
    
    # TODO: Implement single file extraction
    click.echo("Single file extraction not yet implemented")

@cli.command()
def version():
    """Show version information"""
    click.echo("Research Data Extractor CLI v0.1.0")

if __name__ == '__main__':
    cli()