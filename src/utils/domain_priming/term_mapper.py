"""
Module for intelligent term mapping and domain priming using LLM semantic enhancement
"""
import logging
import json
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime
from src.llm.client_factory import ClientFactory
from .pattern_detector import PatternDetector  # Add this import

# Configure logging
logger = logging.getLogger(__name__)

class TermMapper:
    """
    Intelligent term mapping system that uses LLM to enhance domain understanding
    for better extraction accuracy
    """
    
    def __init__(self, provider="anthropic", api_key=None, model_name=None):
        """
        Initialize the TermMapper
        
        Args:
            provider (str): LLM provider to use ('openai', 'anthropic', or 'mock')
            api_key (str, optional): API key for the service
            model_name (str, optional): Model name to use
        """
        self.client = ClientFactory.create_client(provider, api_key, model_name)
        self.provider = provider
        self.model_name = model_name or getattr(self.client, 'model_name', 'unknown')
        
        # Initialize pattern detector
        self.pattern_detector = PatternDetector(min_frequency=2, min_term_length=3)
        
        # Storage for domain mappings
        self.term_mappings: Dict[str, List[str]] = {}
        self.abbreviation_mappings: Dict[str, str] = {}
        self.domain_glossary: Dict[str, str] = {}
        self.field_mappings: Dict[str, List[str]] = {}
        
        logger.info(f"Initialized TermMapper with {provider} provider, model {self.model_name}")
    
    def detect_domain_patterns(self, sample_texts: List[str]) -> Dict[str, any]:
        """
        Detect patterns in sample texts using the sophisticated PatternDetector
        
        Args:
            sample_texts (List[str]): List of sample article texts
            
        Returns:
            Dict: Detected patterns including terms, abbreviations, fields
        """
        logger.info(f"Running pattern detection on {len(sample_texts)} sample texts")
        
        # Use the existing PatternDetector for comprehensive analysis
        analysis_results = self.pattern_detector.analyze_sample_texts(sample_texts)
        
        # Transform the results into our expected format
        patterns = {
            "top_terms": list(analysis_results['term_frequencies'].keys())[:30],  # Top 30 terms
            "term_frequencies": analysis_results['term_frequencies'],
            "abbreviations": self._process_abbreviations(analysis_results['abbreviations']),
            "potential_fields": analysis_results['potential_fields'],
            "numeric_patterns": analysis_results['numeric_patterns'],
            "domain_indicators": self._identify_domain_indicators(analysis_results['term_frequencies']),
            "analysis_stats": analysis_results['analysis_stats']
        }
        
        logger.info(f"Pattern detection complete: {len(patterns['top_terms'])} terms, "
                   f"{len(patterns['abbreviations'])} abbreviations, "
                   f"{len(patterns['potential_fields'])} potential fields")
        
        return patterns
    
    def _process_abbreviations(self, raw_abbreviations: Dict[str, List[str]]) -> Dict[str, str]:
        """
        Process raw abbreviation data into a clean mapping
        
        Args:
            raw_abbreviations (Dict): Raw abbreviation data from PatternDetector
            
        Returns:
            Dict[str, str]: Clean abbreviation mappings
        """
        processed = {}
        
        for abbrev, possible_expansions in raw_abbreviations.items():
            # Filter out 'Unknown' entries and take the most common expansion
            valid_expansions = [exp for exp in possible_expansions if exp != 'Unknown']
            
            if valid_expansions:
                # Take the first (most common) expansion
                processed[abbrev] = valid_expansions[0]
            elif len(abbrev) >= 2:  # Keep unknown abbreviations for LLM processing
                processed[abbrev] = "unknown_expansion"
        
        return processed
    
    def _identify_domain_indicators(self, term_frequencies: Dict[str, int]) -> List[str]:
        """
        Identify terms that suggest specific medical/research domains
        
        Args:
            term_frequencies (Dict): Term frequency data
            
        Returns:
            List[str]: Domain indicator terms
        """
        # Domain-specific term patterns
        domain_patterns = {
            'cardiology': ['cardiovascular', 'cardiac', 'heart', 'blood', 'pressure', 'artery'],
            'diabetes': ['diabetes', 'glucose', 'insulin', 'glycemic', 'hemoglobin', 'hba1c'],
            'oncology': ['cancer', 'tumor', 'chemotherapy', 'radiation', 'oncology', 'malignant'],
            'neurology': ['neurological', 'brain', 'cognitive', 'memory', 'alzheimer', 'parkinson'],
            'psychology': ['psychological', 'mental', 'depression', 'anxiety', 'therapy', 'behavioral'],
            'surgery': ['surgical', 'operation', 'procedure', 'operative', 'incision', 'anesthesia']
        }
        
        domain_indicators = []
        
        for domain, keywords in domain_patterns.items():
            domain_score = sum(term_frequencies.get(keyword, 0) for keyword in keywords)
            if domain_score >= 3:  # Threshold for domain relevance
                domain_indicators.append(f"{domain}:{domain_score}")
        
        return domain_indicators
    
    def enhance_with_llm(self, patterns: Dict[str, any]) -> Dict[str, any]:
        """
        Use LLM to enhance detected patterns with semantic understanding
        
        Args:
            patterns (Dict): Raw patterns detected from texts
            
        Returns:
            Dict: Enhanced patterns with semantic mappings
        """
        logger.info("Starting LLM semantic enhancement of detected patterns")
        
        # Prepare the enhancement prompt
        enhancement_prompt = self._create_enhancement_prompt(patterns)
        
        try:
            # Get LLM response
            logger.info("Sending patterns to LLM for semantic enhancement")
            llm_response = self.client.generate_completion(enhancement_prompt)
            
            # Parse the LLM response
            enhanced_patterns = self._parse_llm_enhancement_response(llm_response, patterns)
            
            logger.info(f"LLM enhancement complete: generated {len(enhanced_patterns.get('synonym_mappings', {}))} synonym mappings")
            
        except Exception as e:
            logger.warning(f"LLM enhancement failed: {e}. Using fallback enhancement.")
            enhanced_patterns = self._fallback_enhancement(patterns)
        
        return enhanced_patterns

    def _create_enhancement_prompt(self, patterns: Dict[str, any]) -> str:
        """
        Create a prompt for LLM to enhance the detected patterns
        
        Args:
            patterns (Dict): Detected patterns from text analysis
            
        Returns:
            str: Formatted prompt for LLM
        """
        # Get the most relevant data for enhancement
        top_terms = patterns.get('top_terms', [])[:15]  # Top 15 terms
        abbreviations = patterns.get('abbreviations', {})
        potential_fields = patterns.get('potential_fields', [])[:10]  # Top 10 fields
        domain_indicators = patterns.get('domain_indicators', [])
        
        prompt = f"""You are a medical research expert helping to enhance domain-specific terminology for better data extraction from research articles.

    DETECTED PATTERNS FROM SAMPLE ARTICLES:

    Top Medical Terms: {', '.join(top_terms)}

    Abbreviations Found: {', '.join([f"{abbrev} ({exp})" for abbrev, exp in abbreviations.items()])}

    Potential Data Fields: {', '.join(potential_fields)}

    Domain Indicators: {', '.join(domain_indicators)}

    TASK: Enhance these patterns with semantic understanding for better data extraction. Please provide:

    1. SYNONYM MAPPINGS: For each important medical term, provide 3-5 synonyms or related terms that might appear in research articles.

    2. ABBREVIATION EXPANSIONS: For any abbreviations, provide the full expanded form and common variations.

    3. FIELD ENHANCEMENTS: For the potential data fields, suggest the most likely data types and common variations of how this information might be presented.

    4. SEMANTIC CLUSTERS: Group related terms into clusters (e.g., "medications", "measurements", "demographics").

    Please format your response as JSON with the following structure:
    {{
    "synonym_mappings": {{
        "term1": ["synonym1", "synonym2", "synonym3"],
        "term2": ["synonym1", "synonym2", "synonym3"]
    }},
    "abbreviation_expansions": {{
        "ABBREV1": {{"full_form": "Full Form", "variations": ["variation1", "variation2"]}},
        "ABBREV2": {{"full_form": "Full Form", "variations": ["variation1", "variation2"]}}
    }},
    "field_enhancements": {{
        "field_name": {{"data_type": "numeric/text/categorical", "variations": ["var1", "var2"], "examples": ["example1", "example2"]}},
        "field_name2": {{"data_type": "numeric/text/categorical", "variations": ["var1", "var2"], "examples": ["example1", "example2"]}}
    }},
    "semantic_clusters": {{
        "cluster_name1": ["term1", "term2", "term3"],
        "cluster_name2": ["term4", "term5", "term6"]
    }}
    }}

    Focus on medical research terminology that would be commonly found in clinical trials and research articles."""
        
        return prompt

    def _parse_llm_enhancement_response(self, llm_response: str, original_patterns: Dict) -> Dict[str, any]:
        """
        Parse the LLM response and extract enhanced patterns
        
        Args:
            llm_response (str): Raw response from LLM
            original_patterns (Dict): Original patterns for fallback
            
        Returns:
            Dict: Parsed enhanced patterns
        """
        try:
            # Try to extract JSON from the response
            import re
            
            # Look for JSON block in the response
            json_match = re.search(r'\{.*\}', llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                enhanced_data = json.loads(json_str)
                
                # Validate the structure
                expected_keys = ['synonym_mappings', 'abbreviation_expansions', 'field_enhancements', 'semantic_clusters']
                if all(key in enhanced_data for key in expected_keys):
                    logger.info("Successfully parsed LLM enhancement response")
                    return enhanced_data
                else:
                    logger.warning("LLM response missing expected keys, using fallback")
                    
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Failed to parse LLM response as JSON: {e}")
        
        # Fallback to simple enhancement
        return self._fallback_enhancement(original_patterns)

    def _fallback_enhancement(self, patterns: Dict[str, any]) -> Dict[str, any]:
        """
        Provide fallback enhancement when LLM fails
        
        Args:
            patterns (Dict): Original patterns
            
        Returns:
            Dict: Basic enhanced patterns
        """
        logger.info("Using fallback enhancement (no LLM)")
        
        # Simple rule-based enhancements
        synonym_mappings = {}
        top_terms = patterns.get('top_terms', [])
        
        # Add some basic medical synonyms
        medical_synonyms = {
            'diabetes': ['diabetes mellitus', 'diabetic', 'dm', 'hyperglycemia'],
            'metformin': ['biguanide', 'glucophage', 'antidiabetic medication'],
            'placebo': ['control', 'inactive treatment', 'sham treatment'],
            'patients': ['subjects', 'participants', 'individuals'],
            'randomized': ['randomised', 'random assignment', 'randomly allocated'],
            'treatment': ['therapy', 'intervention', 'medication', 'drug'],
            'reduction': ['decrease', 'decline', 'improvement', 'lowering']
        }
        
        # Apply synonyms for detected terms
        for term in top_terms:
            if term in medical_synonyms:
                synonym_mappings[term] = medical_synonyms[term]
        
        # Process abbreviations
        abbreviation_expansions = {}
        for abbrev, expansion in patterns.get('abbreviations', {}).items():
            abbreviation_expansions[abbrev] = {
                "full_form": expansion,
                "variations": [expansion.lower(), expansion.replace(' ', '_')]
            }
        
        # Basic field enhancements
        field_enhancements = {}
        for field in patterns.get('potential_fields', []):
            field_enhancements[field] = {
                "data_type": "text",
                "variations": [field.lower(), field.replace(' ', '_')],
                "examples": ["example1", "example2"]
            }
        
        # Basic semantic clusters
        semantic_clusters = {
            "medications": [term for term in top_terms if any(med in term.lower() for med in ['metformin', 'drug', 'treatment'])],
            "measurements": [term for term in top_terms if any(meas in term.lower() for meas in ['reduction', 'mean', 'level'])],
            "demographics": [term for term in top_terms if any(demo in term.lower() for demo in ['age', 'patients', 'male', 'female'])]
        }
        
        return {
            "synonym_mappings": synonym_mappings,
            "abbreviation_expansions": abbreviation_expansions,
            "field_enhancements": field_enhancements,
            "semantic_clusters": semantic_clusters
        }
    
    def create_domain_profile(self, sample_texts: List[str]) -> Dict[str, any]:
        """
        Create a complete domain profile from sample texts
        
        Args:
            sample_texts (List[str]): Sample article texts for domain analysis
            
        Returns:
            Dict: Complete domain profile with mappings and glossary
        """
        logger.info(f"Creating domain profile from {len(sample_texts)} sample texts")
        
        # Step 1: Detect raw patterns using the sophisticated PatternDetector
        patterns = self.detect_domain_patterns(sample_texts)
        
        # Step 2: Enhance with LLM
        enhanced = self.enhance_with_llm(patterns)
        
        # Step 3: Combine into domain profile
        domain_profile = {
            "created_at": datetime.now().isoformat(),
            "sample_count": len(sample_texts),
            "raw_patterns": patterns,
            "enhanced_patterns": enhanced,
            "provider": self.provider,
            "model": self.model_name
        }
        
        return domain_profile
    
    def save_domain_profile(self, profile: Dict[str, any], filename: str) -> str:
        """
        Save domain profile to file
        
        Args:
            profile (Dict): Domain profile to save
            filename (str): Filename for the profile
            
        Returns:
            str: Path to saved file
        """
        import os
        
        # Ensure domain_profiles directory exists
        profiles_dir = "data/domain_profiles"
        os.makedirs(profiles_dir, exist_ok=True)
        
        filepath = os.path.join(profiles_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2)
        
        logger.info(f"Saved domain profile to {filepath}")
        return filepath
    
    def load_domain_profile(self, filepath: str) -> Dict[str, any]:
        """
        Load domain profile from file
        
        Args:
            filepath (str): Path to domain profile file
            
        Returns:
            Dict: Loaded domain profile
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            profile = json.load(f)
        
        logger.info(f"Loaded domain profile from {filepath}")
        return profile