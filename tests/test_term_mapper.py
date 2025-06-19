"""
Test module for TermMapper functionality
"""
import os
import sys
import logging

# Add the project root to the Python path (matching existing test pattern)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import from the correct subdirectory
from src.utils.domain_priming.term_mapper import TermMapper

def test_term_mapper_initialization():
    """Test basic TermMapper initialization"""
    
    logger.info("Testing TermMapper initialization...")
    
    # Test with mock provider
    mapper = TermMapper(provider="mock", model_name="test-model")
    
    # Verify initialization
    assert mapper.provider == "mock"
    assert mapper.model_name == "test-model"
    assert isinstance(mapper.term_mappings, dict)
    assert isinstance(mapper.abbreviation_mappings, dict)
    assert isinstance(mapper.domain_glossary, dict)
    
    logger.info("✅ TermMapper initialization test passed!")
    return True

def test_basic_domain_profile_creation():
    """Test basic domain profile creation"""
    
    logger.info("Testing basic domain profile creation...")
    
    # Initialize mapper
    mapper = TermMapper(provider="mock")
    
    # Sample texts (very basic for now)
    sample_texts = [
        "This is a sample medical research article about diabetes.",
        "Another article discussing cardiovascular interventions.",
        "A study on patient outcomes and quality of life measures."
    ]
    
    # Create domain profile
    profile = mapper.create_domain_profile(sample_texts)
    
    # Verify profile structure
    assert "created_at" in profile
    assert "sample_count" in profile
    assert profile["sample_count"] == 3
    assert "raw_patterns" in profile
    assert "enhanced_patterns" in profile
    
    logger.info("✅ Basic domain profile creation test passed!")
    return True

def test_realistic_pattern_detection():
    """Test pattern detection with realistic medical text"""
    
    logger.info("Testing realistic pattern detection...")
    
    # Initialize mapper
    mapper = TermMapper(provider="mock")
    
    # More realistic medical sample texts
    sample_texts = [
        """
        Background: Type 2 diabetes mellitus (T2DM) affects approximately 463 million adults worldwide.
        This randomized controlled trial evaluated the efficacy of metformin versus placebo in 
        newly diagnosed patients. The primary outcome was hemoglobin A1c (HbA1c) reduction.
        
        Methods: We enrolled 240 patients (mean age 58.3 ± 12.4 years, 52% female) with T2DM.
        Inclusion criteria included HbA1c ≥ 7.0% and body mass index (BMI) 25-40 kg/m².
        Participants were randomized to metformin 1000mg twice daily or placebo for 12 weeks.
        """,
        """
        Results: At baseline, mean HbA1c was 8.2% ± 1.1%. After 12 weeks, the metformin group
        showed significant reduction in HbA1c compared to placebo (7.1% vs 8.0%, p < 0.001).
        Fasting plasma glucose (FPG) decreased from 156 mg/dL to 124 mg/dL in the treatment group.
        
        Adverse events occurred in 23% of metformin patients versus 15% of placebo patients.
        Most common side effects were gastrointestinal: nausea (12%), diarrhea (8%), abdominal pain (5%).
        """,
        """
        Conclusion: Metformin demonstrates superior glycemic control compared to placebo in
        treatment-naive T2DM patients. The drug was generally well-tolerated with expected
        gastrointestinal side effects. These findings support metformin as first-line therapy
        for newly diagnosed type 2 diabetes mellitus patients with elevated HbA1c levels.
        """
    ]
    
    # Create domain profile with realistic data
    profile = mapper.create_domain_profile(sample_texts)
    
    # Verify the sophisticated pattern detection worked
    raw_patterns = profile["raw_patterns"]
    
    # Check that we detected meaningful patterns
    assert len(raw_patterns["top_terms"]) > 0
    assert "abbreviations" in raw_patterns
    assert "potential_fields" in raw_patterns
    assert "numeric_patterns" in raw_patterns
    
    # Log some interesting findings
    logger.info(f"🔍 Top terms detected: {raw_patterns['top_terms'][:10]}")
    logger.info(f"🔤 Abbreviations found: {list(raw_patterns['abbreviations'].keys())}")
    logger.info(f"📊 Numeric patterns: Ages={len(raw_patterns['numeric_patterns'].get('ages', []))}, "
               f"Percentages={len(raw_patterns['numeric_patterns'].get('percentages', []))}")
    
    logger.info("✅ Realistic pattern detection test passed!")
    return True

def test_llm_semantic_enhancement():
    """Test LLM semantic enhancement of detected patterns"""
    
    logger.info("Testing LLM semantic enhancement...")
    
    # Initialize mapper
    mapper = TermMapper(provider="mock")
    
    # Create a realistic medical text sample
    sample_texts = [
        """
        This randomized controlled trial (RCT) evaluated metformin efficacy in type 2 diabetes mellitus (T2DM).
        Participants included 150 adults (mean age 58.3 years, 60% male) with elevated hemoglobin A1c (HbA1c).
        Primary outcome was HbA1c reduction after 12 weeks of metformin 1000mg twice daily versus placebo.
        Secondary outcomes included fasting plasma glucose (FPG) and body mass index (BMI) changes.
        """
    ]
    
    # Create domain profile to test the full pipeline
    profile = mapper.create_domain_profile(sample_texts)
    
    # Verify enhanced patterns exist
    enhanced = profile["enhanced_patterns"]
    
    assert "synonym_mappings" in enhanced
    assert "abbreviation_expansions" in enhanced
    assert "field_enhancements" in enhanced
    assert "semantic_clusters" in enhanced
    
    # Log the enhancement results
    logger.info("🧠 LLM Enhancement Results:")
    logger.info(f"   Synonym mappings: {len(enhanced['synonym_mappings'])} terms enhanced")
    logger.info(f"   Abbreviations expanded: {len(enhanced['abbreviation_expansions'])} abbreviations")
    logger.info(f"   Fields enhanced: {len(enhanced['field_enhancements'])} fields")
    logger.info(f"   Semantic clusters: {len(enhanced['semantic_clusters'])} clusters")
    
    # Show some specific examples
    if enhanced['synonym_mappings']:
        example_term = list(enhanced['synonym_mappings'].keys())[0]
        logger.info(f"   Example synonym mapping: '{example_term}' → {enhanced['synonym_mappings'][example_term]}")
    
    logger.info("✅ LLM semantic enhancement test passed!")
    return True

# Update the main execution
if __name__ == "__main__":
    test_term_mapper_initialization()
    test_basic_domain_profile_creation()
    test_realistic_pattern_detection()
    test_llm_semantic_enhancement()  # Add this line
    logger.info("All TermMapper tests completed successfully!")