"""
Test suite for batch processing functionality
"""
import os
import sys
import logging
import unittest
from pathlib import Path

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.batch_processor import BatchExtractor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestBatchProcessor(unittest.TestCase):
    """Test cases for BatchExtractor"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.input_dir = "data/input"
        self.output_dir = "data/output/batch_test"
        self.batch_extractor = BatchExtractor(provider="mock")
    
    def test_batch_processor_initialization(self):
        """Test that BatchExtractor initializes correctly"""
        self.assertIsNotNone(self.batch_extractor)
        self.assertEqual(self.batch_extractor.provider, "mock")
        self.assertIsNotNone(self.batch_extractor.extractor)
        self.assertIsNotNone(self.batch_extractor.analytics)
    
    def test_process_directory_with_valid_input(self):
        """Test processing a directory with PDF files"""
        if not os.path.exists(self.input_dir):
            self.skipTest(f"Input directory {self.input_dir} does not exist")
        
        # Check if there are any PDF files
        pdf_files = [f for f in os.listdir(self.input_dir) if f.lower().endswith('.pdf')]
        if not pdf_files:
            self.skipTest(f"No PDF files found in {self.input_dir}")
        
        results = self.batch_extractor.process_directory(
            input_dir=self.input_dir,
            output_dir=self.output_dir
        )
        
        # Verify results structure
        self.assertIn('total_files', results)
        self.assertIn('processed', results)
        self.assertIn('failed', results)
        self.assertIn('results', results)
        self.assertIn('output_directory', results)
        
        # Verify output directory was created
        self.assertTrue(os.path.exists(self.output_dir))
        
        print(f"\n=== BATCH PROCESSING TEST RESULTS ===")
        print(f"Total files: {results['total_files']}")
        print(f"Processed successfully: {results['processed']}")
        print(f"Failed: {results['failed']}")
    
    def test_process_directory_nonexistent_input(self):
        """Test processing a non-existent directory"""
        with self.assertRaises(ValueError):
            self.batch_extractor.process_directory(
                input_dir="nonexistent_directory",
                output_dir=self.output_dir
            )
    
    def test_generate_batch_report(self):
        """Test generating a batch processing report"""
        if not os.path.exists(self.input_dir):
            self.skipTest(f"Input directory {self.input_dir} does not exist")
        
        # Check if there are any PDF files
        pdf_files = [f for f in os.listdir(self.input_dir) if f.lower().endswith('.pdf')]
        if not pdf_files:
            self.skipTest(f"No PDF files found in {self.input_dir}")
        
        # Process directory first
        results = self.batch_extractor.process_directory(
            input_dir=self.input_dir,
            output_dir=self.output_dir
        )
        
        # Generate report
        report_path = self.batch_extractor.generate_batch_report(self.output_dir)
        
        # Verify report was created
        self.assertIsNotNone(report_path)
        self.assertTrue(os.path.exists(report_path))
        
        # Verify report contains expected data
        import pandas as pd
        df = pd.read_csv(report_path)
        
        # Check that report has expected columns
        expected_columns = ['file_name', 'status', 'processing_time_seconds', 
                           'chunk_count', 'text_length', 'extraction_fields']
        for col in expected_columns:
            self.assertIn(col, df.columns)
        
        # Check that all processed files are in the report
        self.assertEqual(len(df), results['total_files'])
        
        print(f"\n=== BATCH REPORT TEST RESULTS ===")
        print(f"Report generated: {report_path}")
        print(f"Report contains {len(df)} rows")
        print("Report preview:")
        print(df.head())

def run_manual_test():
    """Manual test function for quick verification"""
    print("Running manual batch processor test...")
    
    input_dir = "data/input"
    output_dir = "data/output/batch_test"
    
    if not os.path.exists(input_dir):
        print(f"Input directory {input_dir} does not exist. Please create it and add some PDF files.")
        return False
    
    # Initialize batch extractor with mock client for testing
    batch_extractor = BatchExtractor(provider="mock")
    
    try:
        # Process the directory
        print(f"Processing PDFs in {input_dir}...")
        results = batch_extractor.process_directory(
            input_dir=input_dir,
            output_dir=output_dir,
            template_id="patient_characteristics"
        )
        
        # Print summary
        print("\n=== BATCH PROCESSING SUMMARY ===")
        print(f"Total files: {results['total_files']}")
        print(f"Processed successfully: {results['processed']}")
        print(f"Failed: {results['failed']}")
        print(f"Output directory: {results['output_directory']}")
        
        if results['failed_files']:
            print("\nFailed files:")
            for failed in results['failed_files']:
                print(f"  - {failed['file_name']}: {failed['error']}")
        
        if results['results']:
            print("\nProcessed files:")
            for result in results['results']:
                print(f"  - {result['file_name']}: {result['processing_time_seconds']:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"Error during batch processing: {str(e)}")
        return False

if __name__ == "__main__":
    # Run manual test if executed directly
    success = run_manual_test()
    if success:
        print("\n✅ Batch processor test completed!")
    else:
        print("\n❌ Batch processor test failed!")
    
    # Optionally run unittest suite
    print("\nRunning unittest suite...")
    unittest.main(argv=[''], verbosity=2, exit=False)