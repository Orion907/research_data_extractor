"""
Main entry point for the PDF Data Extraction application.
"""
import os
from dotenv import load_dotenv
from src.pdf_processor import extract_text_from_pdf
from src.data_extractor import extract_patient_data

# Load environment variables
load_dotenv()

def main():
    """Main function to orchestrate the data extraction process."""
    # Sample usage
    pdf_path = "data/sample_paper.pdf"
    
    # Step 1: Extract text from PDF
    print("Extracting text from PDF...")
    text = extract_text_from_pdf(pdf_path)
    
    # Step 2: Extract patient data using LLM
    print("Extracting patient data...")
    patient_data = extract_patient_data(text)
    
    # Step 3: Save data to CSV
    # TODO: Implement this part
    
    print("Process completed!")

if __name__ == "__main__":
    main()