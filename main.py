"""
Main entry point for the PDF Data Extraction application.
"""
import os
import logging
import argparse
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Update imports to match your actual project structure
from src.pdf_processor.pdf_processor import extract_text_from_pdf
from src.pdf_processor.text_chunker import chunk_text
from src.utils.data_extractor import DataExtractor
from src.data_export.csv_exporter import save_to_csv
from src.utils.template_system import TemplateSystem

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Main function to orchestrate the data extraction process."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Extract patient data from research articles')
    parser.add_argument('--pdf', help='Path to PDF file', default=os.path.join("data", "input", "sample_research_article.pdf"))
    parser.add_argument('--output', help='Path to output CSV file', default=os.path.join("data", "output", "patient_data.csv"))
    parser.add_argument('--template', help='Template ID to use', default="patient_characteristics")
    parser.add_argument('--provider', help='LLM provider to use', default="anthropic")
    parser.add_argument('--model', help='Model name to use', default=None)
    parser.add_argument('--version', help='Template version ID to use', default=None)
    args = parser.parse_args()
    
    # Initialize template system
    template_system = TemplateSystem()
    
    # Check if the specified template exists
    available_templates = template_system.list_templates()
    if args.template not in available_templates:
        logger.warning(f"Template {args.template} not found. Available templates: {available_templates}")
        logger.info("Using default template: patient_characteristics")
        template_id = "patient_characteristics"
    else:
        template_id = args.template
    
    # If version is specified, check if it exists
    version_id = args.version
    if version_id:
        template_versions = template_system.list_versions(template_id)
        if version_id not in template_versions:
            logger.warning(f"Version {version_id} not found for template {template_id}.")
            logger.info(f"Available versions: {template_versions}")
            logger.info("Using latest version.")
            version_id = None
    
    # Step 1: Extract text from PDF
    pdf_path = args.pdf
    logger.info(f"Extracting text from PDF: {pdf_path}")
    try:
        text = extract_text_from_pdf(pdf_path)
        logger.info(f"Successfully extracted {len(text)} characters of text")
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return
    
    # Step 2: Chunk the text for LLM processing
    logger.info("Chunking text for LLM processing")
    try:
        chunks = chunk_text(text, chunk_size=1000, overlap=100)
        logger.info(f"Created {len(chunks)} text chunks")
    except Exception as e:
        logger.error(f"Error chunking text: {str(e)}")
        return
    
    # Step 3: Extract patient data using LLM with template system
    logger.info(f"Extracting patient data using LLM with template: {template_id}")
    try:
        # Initialize the DataExtractor with the template system
        extractor = DataExtractor(
            provider=args.provider,
            model_name=args.model,
            template_system=template_system
        )
        
        # Extract data using the specified template
        chunk_contents = [chunk['content'] for chunk in chunks[:3]]  # First 3 chunks to save API usage
        
        # Get the filename without path for analytics
        pdf_filename = os.path.basename(pdf_path)
        
        patient_data = extractor.extract_from_chunks(
            chunk_contents,
            template_id=template_id,
            version_id=version_id,
            source_file=pdf_filename
        )
        
        logger.info(f"Successfully extracted patient data with {len(patient_data)} characteristics")
    except Exception as e:
        logger.error(f"Error extracting patient data: {str(e)}")
        return
    
    # Step 4: Save data to CSV
    output_path = args.output
    logger.info(f"Saving patient data to CSV: {output_path}")
    try:
        # Convert patient_data dict to a format suitable for CSV
        csv_data = [{"Characteristic": k, "Value": v} for k, v in patient_data.items()]
        save_to_csv(csv_data, output_path)
        logger.info("Data successfully saved to CSV")
    except Exception as e:
        logger.error(f"Error saving data to CSV: {str(e)}")
        return
    
    # Step 5: Generate and save analytics summary
    try:
        # Get analytics summary
        summary = extractor.get_analytics_summary()
        
        # Save analytics summary to a timestamped file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analytics_dir = Path("data/analytics")
        analytics_dir.mkdir(exist_ok=True, parents=True)
        
        analytics_file = analytics_dir / f"extraction_summary_{timestamp}.txt"
        
        with open(analytics_file, "w") as f:
            f.write(f"Extraction Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            for key, value in summary.items():
                if key != 'template_performance':
                    f.write(f"{key}: {value}\n")
            
            f.write("\nTemplate Performance:\n")
            f.write("-" * 30 + "\n")
            
            if 'template_performance' in summary:
                for template_id, metrics in summary['template_performance'].items():
                    f.write(f"Template: {template_id}\n")
                    for metric, value in metrics.items():
                        f.write(f"  {metric}: {value}\n")
                    f.write("\n")
        
        logger.info(f"Analytics summary saved to: {analytics_file}")
    except Exception as e:
        logger.error(f"Error generating analytics summary: {str(e)}")
    
    logger.info("Process completed successfully!")

if __name__ == "__main__":
    main()