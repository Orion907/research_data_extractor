# tests/test_pdf_integration.py
import os
import sys
import logging
import unittest

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pdf_processor.pdf_processor import extract_text_from_pdf
from src.pdf_processor.text_chunker import chunk_text

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestPDFIntegration(unittest.TestCase):
    """Integration tests for PDF processing and chunking"""
    
    def setUp(self):
        """Set up test case - prepare paths and directories"""
        # Get project root directory
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Set up paths
        self.data_dir = os.path.join(self.project_root, "data")
        self.input_dir = os.path.join(self.data_dir, "input")
        self.output_dir = os.path.join(self.data_dir, "output")
        self.chunks_dir = os.path.join(self.output_dir, "chunks")
        
        # Ensure directories exist
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.chunks_dir, exist_ok=True)
        
        # Path to sample PDF - replace with your actual sample PDF name
        self.sample_pdf_path = os.path.join(self.input_dir, "sample_research_article.pdf")
        
        # Check if sample PDF exists
        if not os.path.exists(self.sample_pdf_path):
            logger.warning(f"Sample PDF file not found: {self.sample_pdf_path}")
            logger.warning("Some tests will be skipped. Please add a sample PDF to the input directory.")
    
    def test_pdf_extraction(self):
        """Test PDF text extraction"""
        if not os.path.exists(self.sample_pdf_path):
            self.skipTest("Sample PDF file not found")
        
        # Extract text from PDF
        text = extract_text_from_pdf(self.sample_pdf_path)
        
        # Verify the extraction was successful
        self.assertIsNotNone(text)
        self.assertGreater(len(text), 0)
        
        # Save extracted text for debugging
        extracted_text_file = os.path.join(self.output_dir, "extracted_text_test.txt")
        with open(extracted_text_file, "w", encoding="utf-8") as f:
            f.write(text)
        
        logger.info(f"Extracted {len(text)} characters of text from {self.sample_pdf_path}")
        logger.info(f"Saved extracted text to {extracted_text_file}")
    
    def test_text_chunking(self):
        """Test text chunking functionality"""
        # Create a sample text if no PDF is available
        if not os.path.exists(self.sample_pdf_path):
            sample_text = """
            Abstract
            
            Background: Previous studies have shown that patient characteristics can influence treatment outcomes.
            
            Methods: We conducted a randomized controlled trial with 150 patients (ages 25-65, 60% female).
            Patients were divided into two groups: treatment (n=75) and control (n=75).
            
            Results: The treatment group showed a significant reduction in systolic blood pressure.
            
            Conclusion: Age should be considered when prescribing medication X.
            """
        else:
            # Use extracted text from the sample PDF
            sample_text = extract_text_from_pdf(self.sample_pdf_path)
        
        # Chunk the text
        chunks = chunk_text(
            text=sample_text,
            chunk_size=500,  # Smaller chunk size for testing
            overlap=50,
            respect_paragraphs=True
        )
        
        # Verify chunking
        self.assertGreater(len(chunks), 0)
        
        # Log chunking statistics
        logger.info(f"Created {len(chunks)} chunks from the text")
        
        # Check that chunks have the correct keys
        for i, chunk in enumerate(chunks):
            self.assertIn('content', chunk)
            self.assertIn('index', chunk)
            self.assertIn('start_char', chunk)
            self.assertIn('end_char', chunk)
            
            # Save chunks to files for inspection
            chunk_file = os.path.join(self.chunks_dir, f"test_chunk_{i+1:03d}.txt")
            with open(chunk_file, "w", encoding="utf-8") as f:
                f.write(chunk['content'])
        
        # Test overlapping - check if overlapping text exists between chunks
        if len(chunks) >= 2:
            for i in range(len(chunks) - 1):
                current_chunk = chunks[i]['content']
                next_chunk = chunks[i + 1]['content']
                
                overlap_found = False
                # Check different sized window for overlap
                for window_size in range(10, 60, 10):
                    if current_chunk[-window_size:] in next_chunk:
                        overlap_found = True
                        break
                
                self.assertTrue(overlap_found, f"No overlap found between chunk {i} and {i+1}")
    
    def test_end_to_end_pdf_processing(self):
        """Test the complete process from PDF to chunks"""
        if not os.path.exists(self.sample_pdf_path):
            self.skipTest("Sample PDF file not found")
        
        # Extract text from PDF
        text = extract_text_from_pdf(self.sample_pdf_path)
        self.assertGreater(len(text), 0)
        
        # Chunk the text
        chunks = chunk_text(
            text=text,
            chunk_size=800,
            overlap=100,
            respect_paragraphs=True
        )
        self.assertGreater(len(chunks), 0)
        
        # Verify each chunk has content
        for chunk in chunks:
            self.assertGreater(len(chunk['content']), 0)
        
        # Calculate statistics
        sizes = [len(chunk['content']) for chunk in chunks]
        avg_size = sum(sizes) / len(sizes) if sizes else 0
        
        logger.info("\nChunk Statistics:")
        logger.info(f"- Total chunks: {len(chunks)}")
        logger.info(f"- Average chunk size: {avg_size:.1f} characters")
        logger.info(f"- Smallest chunk: {min(sizes)} characters")
        logger.info(f"- Largest chunk: {max(sizes)} characters")

if __name__ == "__main__":
    unittest.main()