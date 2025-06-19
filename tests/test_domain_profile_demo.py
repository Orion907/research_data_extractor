"""
Demo script showing the complete domain priming workflow
"""
import os
import sys
import logging
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from src.utils.domain_priming.term_mapper import TermMapper

def create_diabetes_domain_profile():
    """Create a domain profile for diabetes research"""
    
    logger.info("🔬 Creating Diabetes Research Domain Profile")
    
    # Initialize TermMapper
    mapper = TermMapper(provider="mock", model_name="domain-analysis")
    
    # Sample diabetes research articles (more comprehensive)
    diabetes_articles = [
        """
        Background: Type 2 diabetes mellitus (T2DM) affects 463 million adults globally. 
        This randomized controlled trial (RCT) evaluated metformin hydrochloride efficacy 
        versus placebo in treatment-naïve patients. Primary endpoint was hemoglobin A1c (HbA1c) 
        reduction at 12 weeks. Secondary endpoints included fasting plasma glucose (FPG), 
        postprandial glucose (PPG), and body mass index (BMI) changes.
        
        Methods: We enrolled 240 participants (mean age 58.3 ± 12.4 years, 52% female) 
        with newly diagnosed T2DM. Inclusion criteria: HbA1c ≥ 7.0%, BMI 25-40 kg/m², 
        estimated glomerular filtration rate (eGFR) ≥ 60 mL/min/1.73m². Exclusion criteria: 
        type 1 diabetes mellitus (T1DM), diabetic ketoacidosis (DKA), pregnancy.
        """,
        """
        Results: Baseline characteristics were similar between groups. Mean HbA1c was 
        8.2% ± 1.1% (66 ± 12 mmol/mol). After 12 weeks, metformin group showed significant 
        HbA1c reduction versus placebo (7.1% vs 8.0%, p < 0.001). FPG decreased from 
        156 ± 28 mg/dL to 124 ± 22 mg/dL in metformin group versus 158 ± 30 to 152 ± 26 mg/dL 
        in placebo group (p < 0.001). PPG improved by 45 mg/dL versus 8 mg/dL (p < 0.01).
        
        Adverse events (AEs) occurred in 23% metformin versus 15% placebo patients. 
        Most common AEs were gastrointestinal: nausea (12%), diarrhea (8%), abdominal pain (5%). 
        No serious adverse events (SAEs) were attributed to study medication.
        """,
        """
        Conclusion: Metformin demonstrates superior glycemic control compared to placebo 
        in treatment-naïve T2DM patients with minimal side effects. The drug significantly 
        reduced HbA1c, FPG, and PPG levels. These findings support metformin as first-line 
        antidiabetic therapy per American Diabetes Association (ADA) and European Association 
        for the Study of Diabetes (EASD) guidelines. Future studies should evaluate 
        long-term cardiovascular outcomes and quality of life (QoL) measures.
        """
    ]
    
    # Create comprehensive domain profile
    domain_profile = mapper.create_domain_profile(diabetes_articles)
    
    # Save the profile
    profile_filename = "diabetes_t2dm_domain_profile.json"
    saved_path = mapper.save_domain_profile(domain_profile, profile_filename)
    
    # Display the results
    logger.info("📊 Domain Profile Analysis Complete!")
    logger.info("=" * 60)
    
    # Show detected patterns
    patterns = domain_profile["raw_patterns"]
    logger.info(f"🔍 Top Medical Terms: {patterns['top_terms'][:10]}")
    logger.info(f"🔤 Abbreviations: {list(patterns['abbreviations'].keys())}")
    logger.info(f"📝 Potential Fields: {patterns['potential_fields']}")
    logger.info(f"🎯 Domain Indicators: {patterns['domain_indicators']}")
    
    # Show enhanced patterns
    enhanced = domain_profile["enhanced_patterns"]
    logger.info("\n🧠 LLM Enhancement Results:")
    logger.info(f"   Synonym mappings: {len(enhanced['synonym_mappings'])} terms")
    logger.info(f"   Abbreviations expanded: {len(enhanced['abbreviation_expansions'])} abbreviations")
    logger.info(f"   Semantic clusters: {list(enhanced['semantic_clusters'].keys())}")
    
    # Show specific examples
    if enhanced['synonym_mappings']:
        logger.info("\n📚 Example Synonym Mappings:")
        for term, synonyms in list(enhanced['synonym_mappings'].items())[:3]:
            logger.info(f"   '{term}' → {synonyms}")
    
    if enhanced['abbreviation_expansions']:
        logger.info("\n🔤 Abbreviation Expansions:")
        for abbrev, details in enhanced['abbreviation_expansions'].items():
            logger.info(f"   {abbrev} → {details['full_form']}")
    
    logger.info(f"\n💾 Profile saved to: {saved_path}")
    
    return domain_profile, saved_path

def demonstrate_profile_usage(profile_path: str):
    """Demonstrate how to load and use a saved domain profile"""
    
    logger.info("\n🔄 Demonstrating Profile Usage")
    logger.info("=" * 60)
    
    # Load the saved profile
    mapper = TermMapper(provider="mock")
    loaded_profile = mapper.load_domain_profile(profile_path)
    
    # Extract useful mappings for data extraction
    enhanced = loaded_profile["enhanced_patterns"]
    
    # Simulate how this would improve data extraction
    logger.info("💡 How this enhances data extraction:")
    
    # Show synonym awareness
    if enhanced['synonym_mappings']:
        logger.info("\n🔄 Synonym Awareness Example:")
        logger.info("   Original text: 'Patient received glucophage therapy'")
        logger.info("   System recognizes: glucophage = metformin (from domain profile)")
        logger.info("   Extraction result: Maps to 'diabetes medication' field")
    
    # Show abbreviation handling
    if enhanced['abbreviation_expansions']:
        logger.info("\n📝 Abbreviation Handling Example:")
        logger.info("   Original text: 'HbA1c was 8.2%'")
        logger.info("   System knows: HbA1c = Hemoglobin A1c (from domain profile)")
        logger.info("   Extraction result: Correctly categorizes as glycemic control measure")
    
    # Show field recognition
    logger.info("\n🎯 Improved Field Recognition:")
    logger.info("   Domain profile helps identify:")
    for cluster_name, terms in enhanced['semantic_clusters'].items():
        if terms:  # Only show non-empty clusters
            logger.info(f"     {cluster_name}: {', '.join(terms[:3])}")
    
    logger.info("\n✨ This domain intelligence makes extraction much more accurate!")

if __name__ == "__main__":
    logger.info("🚀 Starting Domain Priming Demonstration")
    
    # Step 1: Create domain profile
    profile, profile_path = create_diabetes_domain_profile()
    
    # Step 2: Show how to use it
    demonstrate_profile_usage(profile_path)
    
    logger.info("\n🎉 Domain Priming Demo Complete!")
    logger.info("Next step: Integrate this with the actual data extraction pipeline")