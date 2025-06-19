"""
Test domain-enhanced data extraction
"""
import os
import sys
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from src.utils.data_extractor import DataExtractor
from src.utils.domain_priming.term_mapper import TermMapper

def test_domain_enhanced_extraction():
    """Test data extraction enhanced with domain priming"""
    
    logger.info("🧪 Testing Domain-Enhanced Data Extraction")
    
    # Step 1: Create domain profile (using our existing profile)
    profile_path = "data/domain_profiles/diabetes_t2dm_domain_profile.json"
    
    # Verify profile exists (create if needed)
    if not os.path.exists(profile_path):
        logger.info("Creating domain profile first...")
        mapper = TermMapper(provider="mock")
        sample_texts = [
            "Type 2 diabetes mellitus (T2DM) study with metformin versus placebo. "
            "Participants had mean age 58 years, 60% male. Primary outcome was HbA1c reduction."
        ]
        profile = mapper.create_domain_profile(sample_texts)
        mapper.save_domain_profile(profile, "diabetes_t2dm_domain_profile.json")
    
    # Step 2: Create domain-enhanced extractor
    extractor = DataExtractor(provider="mock", model_name="enhanced-extraction")
    
    # Step 3: Load domain profile
    success = extractor.load_domain_profile(profile_path)
    if not success:
        logger.error("Failed to load domain profile")
        return False
    
    # Step 4: Test extraction with domain enhancement
    test_text = """
    This RCT enrolled 240 subjects with T2DM. Mean age was 58.3 years.
    Patients received glucophage 1000mg BID or placebo. Primary endpoint 
    was HbA1c reduction. FPG and PPG were secondary outcomes.
    """
    
    logger.info("🔍 Extracting from text with domain enhancement...")
    
    # Create enhanced prompt
    enhanced_prompt = extractor.create_domain_enhanced_prompt(test_text)
    
    logger.info("📝 Enhanced Prompt Created:")
    logger.info("=" * 50)
    logger.info(enhanced_prompt[:500] + "...")
    logger.info("=" * 50)
    
    # Test actual extraction with domain enhancement
    try:
        extracted_data = extractor.extract_from_text(test_text, use_domain_enhancement=True)
        logger.info("✅ Extraction completed successfully")
        logger.info(f"📊 Extracted {len(extracted_data)} characteristics")
        
        # Show some results
        for key, value in list(extracted_data.items())[:5]:
            logger.info(f"   {key}: {value}")
            
    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return False
    
    logger.info("🎉 Domain-enhanced extraction test completed!")
    return True

if __name__ == "__main__":
    test_domain_enhanced_extraction()