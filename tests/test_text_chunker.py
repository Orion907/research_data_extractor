"""
Test module for text chunking functionality
"""
import os
import sys
import unittest

# Add the src directory to the Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pdf_processor.pdf_processor import extract_text_from_pdf
from src.pdf_processor.text_chunker import chunk_text

class TestTextChunker(unittest.TestCase):
    """Test cases for text chunking functionality"""
    
    def test_chunk_text(self):
        """Test chunking with a sample text"""
        # Sample scientific text with paragraphs
        sample_text = """
        Background: Previous studies have shown that patient characteristics can influence treatment outcomes.
        
        Methods: We conducted a randomized controlled trial with 150 patients (ages 25-65, 60% female).
        Patients were divided into two groups: treatment (n=75) and control (n=75).
        
        Results: The treatment group showed a significant reduction in systolic blood pressure.
        
        Conclusion: Age should be considered when prescribing medication X.
        """
        
        # Test with default settings
        chunks = chunk_text(sample_text, chunk_size=100, overlap=20)
        
        # Verify we got chunks
        self.assertTrue(len(chunks) > 0)
        
        # Verify each chunk has the right keys
        for chunk in chunks:
            self.assertIn('content', chunk)
            self.assertIn('index', chunk)
            self.assertIn('start_char', chunk)
            self.assertIn('end_char', chunk)
    
    def test_create_text_chunk_with_empty_text(self):
        """Test chunking with empty text"""
        chunks = chunk_text("", chunk_size=100, overlap=20)
        self.assertEqual(len(chunks), 0)
    
    def test_create_text_chunk_with_long_text(self):
        """Test chunking with text longer than chunk size"""
        long_text = "This is a very long text. " * 20  # ~400 characters
        chunks = chunk_text(long_text, chunk_size=100, overlap=20)
        self.assertTrue(len(chunks) > 1)
        
        # Check overlap works correctly
        if len(chunks) >= 2:
            chunk1_end = chunks[0]['content'][-20:]
            chunk2_start = chunks[1]['content'][:20]
            self.assertTrue(chunk1_end in chunk2_start or chunk2_start in chunk1_end)

def run_extraction_and_chunking():
    """
    Test PDF extraction and chunking with a sample PDF.
    """
    # Paths for data
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    input_dir = os.path.join(data_dir, 'input')
    output_dir = os.path.join(data_dir, 'output')
    chunks_dir = os.path.join(output_dir, 'chunks')
    
    # Ensure directories exist
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(chunks_dir, exist_ok=True)
    
    # Path to the sample PDF
    sample_pdf_path = os.path.join(input_dir, "sample_research_article.pdf")
    extracted_text_file = os.path.join(output_dir, "extracted_text.txt")
    
    # Check if PDF exists
    if not os.path.exists(sample_pdf_path):
        print(f"Sample PDF file not found: {sample_pdf_path}")
        print("Please place a sample PDF in the data/input directory.")
        return False
    
    # Extract or load text
    if os.path.exists(extracted_text_file):
        with open(extracted_text_file, "r", encoding="utf-8") as f:
            extracted_text = f.read()
        print(f"Loaded extracted text ({len(extracted_text)} characters)")
    else:
        print("Extracting text from PDF...")
        extracted_text = extract_text_from_pdf(sample_pdf_path)
        
        # Save the extracted text
        with open(extracted_text_file, "w", encoding="utf-8") as f:
            f.write(extracted_text)
        print(f"Saved extracted text to {extracted_text_file}")
    
    # Create chunks
    chunks = chunk_text(
        text=extracted_text,
        chunk_size=1000,
        overlap=150,
        respect_paragraphs=True
    )
    
    print(f"Created {len(chunks)} chunks from the extracted text")
    
    # Save chunks to files
    for i, chunk in enumerate(chunks):
        chunk_file = os.path.join(chunks_dir, f"chunk_{i+1:03d}.txt")
        with open(chunk_file, "w", encoding="utf-8") as f:
            f.write(chunk['content'])
    
    print(f"All {len(chunks)} chunks saved to {chunks_dir}")
    
    # Calculate statistics
    sizes = [len(chunk['content']) for chunk in chunks]
    avg_size = sum(sizes) / len(sizes) if sizes else 0
    
    print("\nChunk Statistics:")
    print(f"- Total chunks: {len(chunks)}")
    print(f"- Average chunk size: {avg_size:.1f} characters")
    print(f"- Smallest chunk: {min(sizes)} characters")
    print(f"- Largest chunk: {max(sizes)} characters")
    
    return True

if __name__ == "__main__":
    # Always run the extraction and chunking test
    run_extraction_and_chunking()
    # Comment out the unit tests for now
    # unittest.main()