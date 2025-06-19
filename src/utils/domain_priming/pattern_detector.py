"""
Python-based pattern detection for domain priming
"""
import re
import logging
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Set
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)

class PatternDetector:
    """
    Detects patterns in sample texts to identify domain-specific terms and structures
    """
    
    def __init__(self, min_frequency: int = 3, min_term_length: int = 2):
        """
        Initialize the pattern detector
        
        Args:
            min_frequency (int): Minimum frequency for a term to be considered significant
            min_term_length (int): Minimum length for terms to be analyzed
        """
        self.min_frequency = min_frequency
        self.min_term_length = min_term_length
        
        # Download required NLTK data if not present
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('tokenizers/punkt_tab')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            logger.info("Downloading required NLTK data...")
            nltk.download('punkt')
            nltk.download('punkt_tab')
            nltk.download('stopwords')
        
        # Get English stopwords
        self.stop_words = set(stopwords.words('english'))
        
        # Medical/research-specific stopwords to add
        medical_stopwords = {
            'study', 'patient', 'patients', 'group', 'groups', 'trial', 'research',
            'analysis', 'data', 'results', 'conclusion', 'method', 'methods',
            'significant', 'p', 'table', 'figure', 'et', 'al', 'vs', 'versus'
        }
        self.stop_words.update(medical_stopwords)
        
        logger.info("Initialized PatternDetector")
    
    def analyze_sample_texts(self, sample_texts: List[str]) -> Dict:
        """
        Analyze multiple sample texts to detect patterns
        
        Args:
            sample_texts (List[str]): List of extracted text from sample articles
            
        Returns:
            Dict: Analysis results with patterns and statistics
        """
        logger.info(f"Analyzing {len(sample_texts)} sample texts for patterns")
        
        # Combine all texts for analysis
        combined_text = "\n".join(sample_texts)
        
        # Run individual analyses
        term_frequencies = self._analyze_term_frequencies(combined_text)
        potential_fields = self._identify_potential_fields(combined_text)
        numeric_patterns = self._detect_numeric_patterns(combined_text)
        abbreviation_patterns = self._detect_abbreviations(combined_text)
        
        results = {
            'term_frequencies': term_frequencies,
            'potential_fields': potential_fields,
            'numeric_patterns': numeric_patterns,
            'abbreviations': abbreviation_patterns,
            'analysis_stats': {
                'total_texts': len(sample_texts),
                'total_characters': len(combined_text),
                'total_words': len(word_tokenize(combined_text))
            }
        }
        
        logger.info("Pattern analysis complete")
        return results
    
    def _analyze_term_frequencies(self, text: str) -> Dict[str, int]:
        """
        Analyze frequency of terms in the text
        
        Args:
            text (str): Combined text from samples
            
        Returns:
            Dict[str, int]: Term frequencies above minimum threshold
        """
        # Tokenize and clean
        words = word_tokenize(text.lower())
        
        # Filter words
        filtered_words = [
            word for word in words 
            if (word.isalpha() and 
                len(word) >= self.min_term_length and 
                word not in self.stop_words)
        ]
        
        # Count frequencies
        word_freq = Counter(filtered_words)
        
        # Return only terms above minimum frequency
        significant_terms = {
            term: freq for term, freq in word_freq.items() 
            if freq >= self.min_frequency
        }
        
        logger.info(f"Found {len(significant_terms)} significant terms")
        return dict(sorted(significant_terms.items(), key=lambda x: x[1], reverse=True))
    
    def _identify_potential_fields(self, text: str) -> List[str]:
        """
        Identify potential data field names based on common patterns
        
        Args:
            text (str): Text to analyze
            
        Returns:
            List[str]: Potential field names
        """
        potential_fields = set()
        
        # Pattern for "X:" or "X was" or "X were" constructions
        field_patterns = [
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:',  # "Age:" "Blood pressure:"
            r'\b([A-Z][a-z]+(?:\s+[a-z]+)*)\s+(?:was|were)\s+',  # "Age was" "Treatment was"
            r'\b([A-Z][a-z]+(?:\s+[a-z]+)*)\s+(?:included?|comprised?)\s+',  # "Participants included"
        ]
        
        for pattern in field_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) > 2 and match.lower() not in self.stop_words:
                    potential_fields.add(match)
        
        logger.info(f"Identified {len(potential_fields)} potential fields")
        return list(potential_fields)
    
    def _detect_numeric_patterns(self, text: str) -> Dict[str, List[str]]:
        """
        Detect common numeric patterns (ages, percentages, ranges, etc.)
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Dict[str, List[str]]: Categorized numeric patterns
        """
        patterns = {
            'ages': [],
            'percentages': [],
            'ranges': [],
            'measurements': []
        }
        
        # Age patterns
        age_pattern = r'\b(?:age[ds]?|years?)\s*(?:of\s*)?(\d+(?:\.\d+)?(?:\s*[-±]\s*\d+(?:\.\d+)?)?)\s*(?:years?|yrs?|y\.o\.)?'
        patterns['ages'] = re.findall(age_pattern, text, re.IGNORECASE)
        
        # Percentage patterns
        percent_pattern = r'(\d+(?:\.\d+)?)\s*%'
        patterns['percentages'] = re.findall(percent_pattern, text)
        
        # Range patterns
        range_pattern = r'(\d+(?:\.\d+)?)\s*[-–—]\s*(\d+(?:\.\d+)?)'
        patterns['ranges'] = re.findall(range_pattern, text)
        
        # Measurement patterns (with units)
        measurement_pattern = r'(\d+(?:\.\d+)?)\s*(mg|kg|cm|mm|ml|g|mmHg|bpm|°C|°F)\b'
        patterns['measurements'] = re.findall(measurement_pattern, text, re.IGNORECASE)
        
        logger.info(f"Detected numeric patterns: {len(patterns['ages'])} ages, {len(patterns['percentages'])} percentages")
        return patterns
    
    def _detect_abbreviations(self, text: str) -> Dict[str, List[str]]:
        """
        Detect potential abbreviations and their contexts
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Dict[str, List[str]]: Potential abbreviations with contexts
        """
        abbreviations = defaultdict(list)
        
        # Pattern for abbreviations in parentheses
        abbrev_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\(([A-Z]{2,})\)'
        matches = re.findall(abbrev_pattern, text)
        
        for full_term, abbrev in matches:
            abbreviations[abbrev].append(full_term)
        
        # Pattern for standalone abbreviations (2+ uppercase letters)
        standalone_pattern = r'\b([A-Z]{2,})\b'
        standalone_matches = re.findall(standalone_pattern, text)
        
        for abbrev in standalone_matches:
            if abbrev not in abbreviations:
                abbreviations[abbrev] = ['Unknown']
        
        logger.info(f"Detected {len(abbreviations)} potential abbreviations")
        return dict(abbreviations)