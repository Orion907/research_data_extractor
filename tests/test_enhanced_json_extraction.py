# tests/test_enhanced_json_extraction.py
import os
import sys
import logging
from pathlib import Path
import json

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the necessary components
from src.utils.data_extractor import DataExtractor
from src.llm.anthropic_client import AnthropicClient

def test_enhanced_json_extraction():
    """Test the enhanced JSON extraction capabilities."""
    try:
        # Get API key from environment or .env file
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            # Try loading from .env file manually
            env_path = Path(__file__).parent.parent / ".env"
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith("ANTHROPIC_API_KEY="):
                        api_key = line[len("ANTHROPIC_API_KEY="):].strip()
                        os.environ["ANTHROPIC_API_KEY"] = api_key
                        break
            
            if not api_key:
                logger.error("No ANTHROPIC_API_KEY found")
                return False
        
        logger.info("Initializing DataExtractor...")
        extractor = DataExtractor(provider="anthropic", api_key=api_key)
        
        # Sample text
        sample_text = """
        In this randomized clinical trial, we enrolled 120 patients with type 2 diabetes mellitus.
        The participants were aged 45-75 years (mean age: 62.3 years), and 55% were female.
        Inclusion criteria were HbA1c levels ≥7.5% and BMI >25 kg/m².
        Patients with severe renal impairment (eGFR <30 mL/min/1.73m²) or a history of 
        cardiovascular events within the past 6 months were excluded.
        All patients were on stable doses of metformin (≥1500 mg daily) for at least 3 months
        prior to enrollment, and 40% were also receiving sulfonylureas.
        """
        
        logger.info("Extracting patient characteristics...")
        result = extractor.extract_patient_characteristics(
            sample_text, 
            template_id="patient_characteristics",
            source_file="test_file.pdf"
        )
        
        logger.info("Extraction result:")
        logger.info(json.dumps(result, indent=2))
        
        # Verify expected structure
        expected_keys = ["demographics", "inclusion_criteria", "exclusion_criteria", 
                         "medications", "comorbidities", "disease_specific"]
        
        for key in expected_keys:
            if key not in result:
                logger.error(f"Missing expected key in result: {key}")
                return False
                
        # Check specific expected values
        if "demographics" in result:
            # Check for age information in any form (age, age_range, or mean_age)
            if not any(age_field in result["demographics"] for age_field in ["age", "age_range", "mean_age"]):
                logger.error("Demographics section missing any age field")
                return False
            
            # Check for diabetes information in either disease_specific or disease_characteristics
            has_diabetes = False
            
            # Check in disease_specific
            if "disease_specific" in result and result["disease_specific"]:
                has_diabetes = any("diabetes" in str(item).lower() for item in result["disease_specific"].values())
            
            # Also check in disease_characteristics if it exists
            if "disease_characteristics" in result and not has_diabetes:
                has_diabetes = any("diabetes" in str(item).lower() for item in result["disease_characteristics"])
            
            if not has_diabetes:
                logger.warning("Disease type 'diabetes' not found in any disease section")
        
        logger.info("Test completed successfully!")
        return True
    
    except Exception as e:
        logger.error(f"Error testing enhanced JSON extraction: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    logger.info("Starting test of enhanced JSON extraction...")
    success = test_enhanced_json_extraction()
    logger.info(f"Test completed. Success: {success}")