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
@click.option('--picots-file', type=click.Path(exists=True), help='PICOTS criteria file')
@click.option('--chunk-size', default=1000, help='Text chunk size for processing')
@click.option('--chunk-overlap', default=100, help='Overlap between text chunks')
def extract(input_file, output, provider, model, template, picots_file, chunk_size, chunk_overlap):
    """Extract data from a single PDF file"""
    from pathlib import Path
    from ..pdf_processor import extract_text_from_pdf, chunk_text
    from ..utils.data_extractor import DataExtractor
    from ..utils.picots_parser import PicotsParser
    from ..data_export.csv_exporter import save_to_csv
    from .utils import validate_file_exists, ensure_output_directory, get_default_output_filename
    import json
    
    try:
        # Validate input file
        input_path = validate_file_exists(input_file, "PDF file")
        
        # Generate output filename if not provided
        if not output:
            output = get_default_output_filename(input_path, "extracted")
        
        # Ensure output directory exists
        output_path = Path(output)
        if output_path.parent != Path('.'):
            ensure_output_directory(str(output_path.parent))
        
        click.echo(f"📄 Processing: {input_file}")
        click.echo(f"🤖 Provider: {provider}")
        click.echo(f"📝 Template: {template}")
        if picots_file:
            click.echo(f"🎯 PICOTS file: {picots_file}")
        
        # Process PICOTS file if provided
        # Process PICOTS file if provided
        picots_data = None
        picots_context = None  # Initialize this variable
        if picots_file:
            with click.progressbar(length=1, label='Parsing PICOTS') as bar:
                try:
                    with open(picots_file, 'r', encoding='utf-8') as f:
                        picots_text = f.read()
                    
                    parser = PicotsParser()
                    picots_data = parser.parse_picots_table(picots_text)
                    
                    # Convert to format expected by DataExtractor
                    picots_context = {
                        'picots_sections': {
                            'population': picots_data.population,
                            'interventions': picots_data.interventions,
                            'comparators': picots_data.comparators,
                            'outcomes': picots_data.outcomes,
                            'timing': picots_data.timing,
                            'setting': picots_data.setting
                        },
                        'key_questions': picots_data.detected_kqs,
                        'abbreviations': picots_data.abbreviations
                    }
                    bar.update(1)
                    click.echo("✅ PICOTS criteria parsed successfully")
                    
                except Exception as e:
                    click.echo(f"⚠️  Warning: Could not parse PICOTS file: {str(e)}")
                    picots_context = None
        
        # Extract text from PDF
        with click.progressbar(length=1, label='Extracting PDF text') as bar:
            text = extract_text_from_pdf(str(input_path))
            bar.update(1)
            click.echo(f"📊 Extracted {len(text):,} characters")
        
        # Chunk the text
        with click.progressbar(length=1, label='Chunking text') as bar:
            chunks = chunk_text(text, chunk_size=chunk_size, overlap=chunk_overlap)
            bar.update(1)
            click.echo(f"🔄 Created {len(chunks)} chunks")
        
        # Initialize extractor
        with click.progressbar(length=1, label='Initializing AI model') as bar:
            extractor = DataExtractor(provider=provider, model_name=model)
            bar.update(1)
        
        # Process chunks
        chunk_results = []
        with click.progressbar(chunks, label='Processing chunks') as chunks_bar:
            for chunk in chunks_bar:
                try:
                    # Extract using existing method with PICOTS context
                    if picots_context:
                        from ..utils.prompt_templates import PromptTemplate
                        prompt = PromptTemplate.get_extraction_prompt(
                            chunk['content'], 
                            picots_context=picots_context
                        )
                        completion = extractor.client.generate_completion(prompt)
                    else:
                        completion = extractor.client.generate_completion(
                            extractor.template_system.get_extraction_prompt(
                                chunk['content'], template
                            )
                        )
                    
                    chunk_results.append({
                        'chunk_index': chunk['index'],
                        'extraction': completion
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk['index']}: {str(e)}")
                    click.echo(f"⚠️  Warning: Chunk {chunk['index']} failed: {str(e)}")
        
        # Process and save results
        if chunk_results:
            with click.progressbar(length=1, label='Saving results') as bar:
                # For CSV output, flatten the results
                csv_data = []
                for result in chunk_results:
                    csv_data.append({
                        'chunk': result['chunk_index'],
                        'extraction': result['extraction']
                    })
                
                # Save to CSV
                save_to_csv(csv_data, str(output_path))
            
            click.echo(f"✅ Results saved to: {output_path}")
            click.echo(f"📈 Processed {len(chunk_results)} chunks successfully")
        else:
            click.echo("❌ No results to save - all chunks failed processing")
            
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        logger.error(f"Extract command failed: {str(e)}")
        raise click.ClickException(str(e))
    
@cli.command()
@click.argument('input_dir', type=click.Path(exists=True))
@click.option('--output-dir', '-o', required=True, type=click.Path(), help='Output directory for results')
@click.option('--provider', default='anthropic',
              type=click.Choice(['anthropic', 'openai', 'mock']),
              help='LLM provider to use')
@click.option('--model', help='Model name to use')
@click.option('--template', default='patient_characteristics', help='Template ID to use')
@click.option('--max-files', type=int, help='Maximum number of files to process')
@click.option('--chunk-size', default=1000, help='Text chunk size for processing')
@click.option('--chunk-overlap', default=100, help='Overlap between text chunks')
@click.option('--generate-report', is_flag=True, default=True, help='Generate batch processing report')
def batch(input_dir, output_dir, provider, model, template, max_files, chunk_size, chunk_overlap, generate_report):
    """Process multiple PDF files from a directory"""
    from ..batch_processor.batch_extractor import BatchExtractor
    from pathlib import Path
    from .utils import ensure_output_directory
    import os
    
    try:
        # Ensure output directory exists
        ensure_output_directory(output_dir)
        
        # Count PDF files
        pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
        total_files = len(pdf_files)
        
        if max_files and total_files > max_files:
            total_files = max_files
            click.echo(f"🔢 Limiting processing to {max_files} files")
        
        click.echo(f"📁 Input directory: {input_dir}")
        click.echo(f"📁 Output directory: {output_dir}")
        click.echo(f"📄 Found {total_files} PDF files to process")
        click.echo(f"🤖 Provider: {provider}")
        click.echo(f"📝 Template: {template}")
        
        # Initialize batch extractor
        with click.progressbar(length=1, label='Initializing batch processor') as bar:
            batch_extractor = BatchExtractor(provider=provider, model_name=model)
            bar.update(1)
        
        # Process all files
        click.echo("🚀 Starting batch processing...")
        
        summary = batch_extractor.process_directory(
            input_dir=input_dir,
            output_dir=output_dir,
            template_id=template,
            chunk_size=chunk_size,
            overlap=chunk_overlap,
            max_files=max_files
        )
        
        # Display results
        click.echo(f"\n📊 Batch Processing Summary:")
        click.echo(f"   Total files: {summary['total_files']}")
        click.echo(f"   ✅ Processed successfully: {summary['processed']}")
        click.echo(f"   ❌ Failed: {summary['failed']}")
        
        if summary['failed'] > 0:
            click.echo(f"\n❌ Failed files:")
            for failed in summary['failed_files']:
                click.echo(f"   • {failed['file_name']}: {failed['error']}")
        
        # Generate report if requested
        if generate_report:
            with click.progressbar(length=1, label='Generating report') as bar:
                report_path = batch_extractor.generate_batch_report(output_dir)
                bar.update(1)
                if report_path:
                    click.echo(f"📈 Report generated: {report_path}")
        
        click.echo(f"✅ Batch processing complete!")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        logger.error(f"Batch command failed: {str(e)}")
        raise click.ClickException(str(e))

@cli.command()
def version():
    """Show version information"""
    click.echo("Research Data Extractor CLI v0.1.0")

if __name__ == '__main__':
    cli()