"""
Test module for domain priming pattern detector
"""
import os
import sys
import logging

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.utils.domain_priming import PatternDetector

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_pattern_detector():
    """Test the PatternDetector with sample medical text"""
    
    # Sample medical research texts
    sample_texts = [
        """
        The study included 150 patients with type 2 diabetes mellitus (T2DM). 
        Patients were aged between 45-70 years (mean age 58.3 years), with 60% being male. 
        Inclusion criteria were HbA1c > 7.5% and BMI > 25 kg/m².
        Blood pressure was measured at 140/90 mmHg on average.
        """,
        """
        Participants comprised 200 adults with hypertension (HTN).
        Age range was 35-65 years with mean age of 52.7 years.
        Gender distribution: 55% female, 45% male.
        Systolic blood pressure averaged 150 mmHg.
        Body mass index (BMI) ranged from 22-35 kg/m².
        """,
        """
        The randomized controlled trial (RCT) enrolled 75 subjects.
        Demographics: mean age 61.2 years, 65% male participants.
        Exclusion criteria included severe renal impairment and pregnancy.
        Hemoglobin A1c (HbA1c) levels were 8.2% ± 1.1%.
        """
    ]
    
    try:
        # Initialize the pattern detector
        logger.info("Initializing PatternDetector...")
        detector = PatternDetector(min_frequency=2, min_term_length=3)
        
        # Analyze the sample texts
        logger.info("Analyzing sample texts...")
        results = detector.analyze_sample_texts(sample_texts)
        
        # Display results
        print("\n" + "="*50)
        print("PATTERN DETECTION RESULTS")
        print("="*50)
        
        print(f"\nAnalysis Stats:")
        print(f"  Total texts: {results['analysis_stats']['total_texts']}")
        print(f"  Total characters: {results['analysis_stats']['total_characters']:,}")
        print(f"  Total words: {results['analysis_stats']['total_words']:,}")
        
        print(f"\nTop 10 Frequent Terms:")
        term_count = 0
        for term, freq in results['term_frequencies'].items():
            if term_count < 10:
                print(f"  {term}: {freq}")
                term_count += 1
        
        print(f"\nPotential Fields Detected:")
        for field in results['potential_fields'][:10]:  # Show first 10
            print(f"  - {field}")
        
        print(f"\nAbbreviations Found:")
        for abbrev, definitions in results['abbreviations'].items():
            print(f"  {abbrev}: {', '.join(definitions)}")
        
        print(f"\nNumeric Patterns:")
        print(f"  Ages found: {len(results['numeric_patterns']['ages'])}")
        print(f"  Percentages found: {len(results['numeric_patterns']['percentages'])}")
        print(f"  Ranges found: {len(results['numeric_patterns']['ranges'])}")
        print(f"  Measurements found: {len(results['numeric_patterns']['measurements'])}")
        
        # Show some examples
        if results['numeric_patterns']['ages']:
            print(f"  Example ages: {results['numeric_patterns']['ages'][:3]}")
        if results['numeric_patterns']['percentages']:
            print(f"  Example percentages: {results['numeric_patterns']['percentages'][:3]}")
        
        print("\n" + "="*50)
        print("✅ PatternDetector test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error testing PatternDetector: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    test_pattern_detector()