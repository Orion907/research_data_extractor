# src/llm/mock_client.py
"""
Mock LLM client for testing without API access
"""
import logging
import json
import re
from .api_client import BaseLLMClient

logger = logging.getLogger(__name__)

class MockLLMClient(BaseLLMClient):
    """Mock LLM client for testing without API access"""
    
    def __init__(self, api_key=None, model_name="mock-model"):
        """
        Initialize the mock client
        
        Args:
            api_key (str, optional): Not used, for compatibility
            model_name (str, optional): Mock model name
        """
        self.model_name = model_name
        logger.info(f"Initialized Mock LLM client with model: {model_name}")
    
    def generate_completion(self, prompt, max_tokens=None, temperature=0.0):
        """
        Return a mock response based on the prompt
        
        Args:
            prompt (str): The prompt to analyze
            max_tokens (int, optional): Not used, for compatibility
            temperature (float, optional): Not used, for compatibility
            
        Returns:
            str: Generated mock completion
        """
        logger.info("Generating mock completion")
        
        # Check if prompt contains specific keywords to return appropriate responses
        prompt_lower = prompt.lower()
        
        # Response for patient characteristic extraction
        if "patient" in prompt_lower and "characteristic" in prompt_lower:
            # Look for specific conditions in the prompt
            if "diabetes" in prompt_lower:
                return self._generate_diabetes_response()
            elif "heart failure" in prompt_lower or "cardiac" in prompt_lower:
                return self._generate_heart_failure_response()
            elif "cancer" in prompt_lower or "oncology" in prompt_lower:
                return self._generate_cancer_response()
            else:
                # Generic patient characteristics
                return self._generate_generic_patient_response()
        
        # Response for age and gender extraction
        elif "age" in prompt_lower and "gender" in prompt_lower:
            return """
            {
                "Age": "65 years old",
                "Gender": "Male",
                "Ethnicity": "Caucasian"
            }
            """
        
        # Default response
        return """
        {
            "Extracted Data": "This is a mock response for testing without API access"
        }
        """
    
    def _generate_diabetes_response(self):
        """Generate a mock response for diabetes studies"""
        return """
        {
            "sample_size": 75,
            "condition": "type 2 diabetes mellitus (T2DM)",
            "mean_age": 58.3,
            "age_range": "45-70 years",
            "male_percentage": 60,
            "female_percentage": 40,
            "inclusion_criteria": [
                "HbA1c > 7.5%",
                "BMI > 25 kg/m²"
            ],
            "exclusion_criteria": [
                "pregnancy",
                "severe renal impairment (eGFR < 30 mL/min)",
                "active cancer treatment"
            ],
            "medications": [
                "metformin (100%)",
                "insulin therapy (45%)"
            ]
        }
        """
    
    def _generate_heart_failure_response(self):
        """Generate a mock response for heart failure studies"""
        return """
        {
            "sample_size": 50,
            "condition": "heart failure",
            "mean_age": 67,
            "age_range": "45-85 years",
            "male_percentage": 60,
            "female_percentage": 40,
            "nyha_class": "III-IV",
            "mean_ejection_fraction": "30%",
            "exclusion_criteria": [
                "prior myocardial infarction"
            ],
            "medications": [
                "beta blockers (80%)",
                "ACE inhibitors (75%)",
                "diuretics (95%)"
            ]
        }
        """
    
    def _generate_cancer_response(self):
        """Generate a mock response for cancer studies"""
        return """
        {
            "sample_size": 120,
            "condition": "metastatic colorectal cancer",
            "mean_age": 62.7,
            "age_range": "42-85 years",
            "male_percentage": 55,
            "female_percentage": 45,
            "stage": {
                "stage II": "65%",
                "stage III": "35%"
            },
            "ecog_status": "0-2",
            "exclusion_criteria": [
                "prior therapy",
                "significant comorbidities",
                "pregnancy"
            ],
            "treatment_arms": [
                "standard chemotherapy",
                "experimental regimen"
            ]
        }
        """
    
    def _generate_generic_patient_response(self):
        """Generate a generic patient characteristics response"""
        return """
        {
            "sample_size": 100,
            "mean_age": 55.7,
            "age_range": "18-75 years",
            "gender_distribution": "male: 52%, female: 48%",
            "inclusion_criteria": [
                "adults over 18 years",
                "able to provide informed consent"
            ],
            "exclusion_criteria": [
                "severe comorbidities",
                "participation in other clinical trials"
            ]
        }
        """
    
    def get_available_models(self):
        """Return mock available models"""
        return [
            "mock-model-basic", 
            "mock-model-advanced",
            "mock-model-specialized"
        ]