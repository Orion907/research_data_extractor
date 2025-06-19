"""
Test PatternDetector with real PDF content
"""
import os
import sys
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.pdf_processor import extract_text_from_pdf, chunk_text
from src.utils.domain_priming import PatternDetector

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pattern_detector_with_real_pdf():
    """Test PatternDetector with real PDF research article"""
    
    # Check for sample PDF
    input_dir = Path("data/input")
    pdf_files = list(input_dir.glob("*.pdf")) if input_dir.exists() else []
    
    if not pdf_files:
        print("❌ No PDF files found in data/input directory")
        print("Please add a research article PDF to data/input/ and try again")
        return False
    
    # Use first PDF found
    pdf_path = pdf_files[0]
    print(f"📄 Testing with PDF: {pdf_path.name}")
    
    try:
        # Extract text from PDF
        logger.info(f"Extracting text from {pdf_path}")
        full_text = extract_text_from_pdf(str(pdf_path))
        
        if not full_text.strip():
            print("❌ No text could be extracted from PDF")
            return False
        
        print(f"📊 Extracted {len(full_text):,} characters from PDF")
        
        # Chunk the text for analysis (use smaller chunks for pattern detection)
        logger.info("Chunking text for analysis")
        chunks = chunk_text(full_text, chunk_size=2000, overlap=200)
        
        # Use first few chunks as sample (don't overwhelm the pattern detector)
        sample_chunks = chunks[:5]  # First 5 chunks
        sample_texts = [chunk['content'] for chunk in sample_chunks]
        
        print(f"🔍 Analyzing {len(sample_texts)} text chunks for patterns")
        
        # Initialize pattern detector with more relaxed settings for real content
        detector = PatternDetector(min_frequency=2, min_term_length=3)
        
        # Analyze the real PDF content
        results = detector.analyze_sample_texts(sample_texts)
        
        # Display comprehensive results
        print("\n" + "="*60)
        print("REAL PDF PATTERN DETECTION RESULTS")
        print("="*60)
        
        print(f"\n📈 Analysis Stats:")
        print(f"  Source PDF: {pdf_path.name}")
        print(f"  Total chunks analyzed: {len(sample_texts)}")
        print(f"  Total characters: {results['analysis_stats']['total_characters']:,}")
        print(f"  Total words: {results['analysis_stats']['total_words']:,}")
        
        # Show top frequent terms
        print(f"\n🏷️ Top 15 Frequent Terms:")
        term_count = 0
        for term, freq in results['term_frequencies'].items():
            if term_count < 15:
                print(f"  {term}: {freq}")
                term_count += 1
        
        # Show potential fields
        print(f"\n📋 Potential Data Fields Detected ({len(results['potential_fields'])}):")
        for i, field in enumerate(results['potential_fields'][:15], 1):
            print(f"  {i:2d}. {field}")
        
        # Show abbreviations
        print(f"\n🔤 Abbreviations Found ({len(results['abbreviations'])}):")
        for abbrev, definitions in list(results['abbreviations'].items())[:10]:
            print(f"  {abbrev}: {', '.join(definitions)}")
        
        # Show numeric patterns with examples
        print(f"\n🔢 Numeric Patterns:")
        print(f"  Ages detected: {len(results['numeric_patterns']['ages'])}")
        if results['numeric_patterns']['ages']:
            ages_sample = results['numeric_patterns']['ages'][:5]
            print(f"    Examples: {ages_sample}")
        
        print(f"  Percentages detected: {len(results['numeric_patterns']['percentages'])}")
        if results['numeric_patterns']['percentages']:
            percent_sample = results['numeric_patterns']['percentages'][:5]
            print(f"    Examples: {percent_sample}%")
        
        print(f"  Ranges detected: {len(results['numeric_patterns']['ranges'])}")
        if results['numeric_patterns']['ranges']:
            ranges_sample = results['numeric_patterns']['ranges'][:5]
            print(f"    Examples: {ranges_sample}")
        
        print(f"  Measurements detected: {len(results['numeric_patterns']['measurements'])}")
        if results['numeric_patterns']['measurements']:
            measurements_sample = results['numeric_patterns']['measurements'][:5]
            print(f"    Examples: {measurements_sample}")
        
        # Save detailed results for inspection
        output_dir = Path("data/output")
        output_dir.mkdir(exist_ok=True)
        
        results_file = output_dir / f"pattern_analysis_{pdf_path.stem}.txt"
        with open(results_file, 'w', encoding='utf-8') as f:
            f.write(f"PATTERN ANALYSIS RESULTS\n")
            f.write(f"Source: {pdf_path.name}\n")
            f.write(f"Generated: {logger.name}\n\n")
            
            f.write("TOP 50 FREQUENT TERMS:\n")
            for i, (term, freq) in enumerate(list(results['term_frequencies'].items())[:50], 1):
                f.write(f"{i:2d}. {term}: {freq}\n")
            
            f.write(f"\nPOTENTIAL FIELDS ({len(results['potential_fields'])}):\n")
            for i, field in enumerate(results['potential_fields'], 1):
                f.write(f"{i:2d}. {field}\n")
            
            f.write(f"\nABBREVIATIONS ({len(results['abbreviations'])}):\n")
            for abbrev, definitions in results['abbreviations'].items():
                f.write(f"{abbrev}: {', '.join(definitions)}\n")
        
        print(f"\n💾 Detailed results saved to: {results_file}")
        
        # Quality assessment
        print(f"\n✅ Real PDF Pattern Detection Assessment:")
        print(f"  - Found {len(results['term_frequencies'])} significant terms")
        print(f"  - Detected {len(results['potential_fields'])} potential data fields")
        print(f"  - Identified {len(results['abbreviations'])} abbreviations")
        print(f"  - Located {sum(len(patterns) for patterns in results['numeric_patterns'].values())} numeric patterns")
        
        print("\n" + "="*60)
        print("✅ Real PDF test completed successfully!")
        print("This data will help optimize our LLM enhancement in Step 2")
        print("="*60)
        
        return True
        
    except Exception as e:
        logger.error(f"Error testing with real PDF: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    test_pattern_detector_with_real_pdf()