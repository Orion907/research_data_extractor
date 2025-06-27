"""
Enhanced pattern detection for domain priming
Consolidates functionality from pattern_detector.py and domain_mapper.py
"""
import re
import logging
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Set, Optional
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

logger = logging.getLogger(__name__)

class EnhancedPatternDetector:
    """
    Unified pattern detection system that combines term frequency analysis,
    field detection, and domain mapping capabilities
    """
    
    def __init__(self, min_frequency: int = 3, min_term_length: int = 2):
        """
        Initialize the enhanced pattern detector
        
        Args:
            min_frequency (int): Minimum frequency for a term to be considered significant
            min_term_length (int): Minimum length for terms to be analyzed
        """
        self.min_frequency = min_frequency
        self.min_term_length = min_term_length
        
        # Initialize NLTK data
        self._setup_nltk()
        
        # Storage for analysis results
        self.term_frequencies = Counter()
        self.potential_fields = set()
        self.field_clusters = defaultdict(set)
        
        logger.info("Initialized EnhancedPatternDetector")
    
    def _setup_nltk(self):
        """Download and setup required NLTK data"""
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
            'significant', 'p', 'table', 'figure', 'et', 'al', 'vs', 'versus',
            'used', 'using', 'given', 'shown', 'found', 'measured', 'observed'
        }
        self.stop_words.update(medical_stopwords)
    
    def analyze_sample_texts(self, sample_texts: List[str]) -> Dict:
        """
        Comprehensive analysis of multiple sample texts
        
        Args:
            sample_texts (List[str]): List of extracted text from sample articles
            
        Returns:
            Dict: Complete analysis results
        """
        logger.info(f"Analyzing {len(sample_texts)} sample texts for patterns")
        
        # Combine all texts for unified analysis
        combined_text = "\n".join(sample_texts)
        
        # Run comprehensive analyses
        analysis_results = {
            'term_frequencies': self._analyze_term_frequencies(combined_text),
            'potential_fields': self._identify_potential_fields(combined_text),
            'numeric_patterns': self._detect_numeric_patterns(combined_text),
            'abbreviations': self._detect_abbreviations(combined_text),
            'field_mappings': self._generate_field_mappings(combined_text),
            'similarity_clusters': self._create_similarity_clusters(),
            'analysis_stats': {
                'total_texts': len(sample_texts),
                'total_characters': len(combined_text),
                'total_words': len(word_tokenize(combined_text)),
                'unique_terms': len(set(word_tokenize(combined_text.lower())))
            }
        }
        
        logger.info("Enhanced pattern analysis complete")
        return analysis_results
    
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
        self.term_frequencies = word_freq
        
        # Return only terms above minimum frequency
        significant_terms = {
            term: freq for term, freq in word_freq.items() 
            if freq >= self.min_frequency
        }
        
        logger.info(f"Found {len(significant_terms)} significant terms")
        return dict(sorted(significant_terms.items(), key=lambda x: x[1], reverse=True))
    
    def _identify_potential_fields(self, text: str) -> List[str]:
        """
        Identify potential data field names based on patterns
        Combines patterns from both original modules
        
        Args:
            text (str): Text to analyze
            
        Returns:
            List[str]: Potential field names
        """
        potential_fields = set()
        
        # Enhanced field patterns combining both modules
        field_patterns = [
            # Basic field indicators
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:',  # "Age:" "Blood pressure:"
            r'\b([A-Z][a-z]+(?:\s+[a-z]+)*)\s+(?:was|were)\s+',  # "Age was" "Treatment was"
            r'\b([A-Z][a-z]+(?:\s+[a-z]+)*)\s+(?:included?|comprised?)\s+',  # "Participants included"
            
            # Age-related patterns
            r'\b(age|aged|years?|yrs?)\b',
            r'\b(mean\s+age|average\s+age|median\s+age)\b',
            
            # Sample size patterns  
            r'\b(n\s*=|sample\s+size|participants?|subjects?|patients?)\b',
            r'\b(\d+\s+participants?|\d+\s+subjects?|\d+\s+patients?)\b',
            
            # Gender patterns
            r'\b(gender|sex|male|female|boys?|girls?)\b',
            r'\b(percentage\s+male|percentage\s+female|\d+%\s+male|\d+%\s+female)\b',
            
            # Study design patterns
            r'\b(intervention|treatment|therapy|protocol)\b',
            r'\b(control\s+group|experimental\s+group|treatment\s+group)\b',
            
            # Outcome patterns
            r'\b(outcome|endpoint|measure|assessment|scale|score)\b',
            r'\b(primary\s+outcome|secondary\s+outcome)\b',
            
            # Domain-specific patterns
            r'\b(mindfulness|meditation|mindful|awareness)\b',
            r'\b(anxiety|depression|stress|wellbeing|well-being)\b',
            r'\b(children|child|adolescent|pediatric|paediatric)\b',
        ]
        
        # Extract terms using patterns
        for pattern in field_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else match[1] if len(match) > 1 else ""
                if len(match) > 2 and match.lower() not in self.stop_words:
                    # Clean and normalize the match
                    clean_match = re.sub(r'\s+', '_', match.strip().lower())
                    potential_fields.add(clean_match)
        
        self.potential_fields = potential_fields
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
            'measurements': [],
            'sample_sizes': []
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
        
        # Sample size patterns
        sample_size_pattern = r'(?:n\s*=\s*|sample\s+size\s*[=:]?\s*)(\d+)'
        patterns['sample_sizes'] = re.findall(sample_size_pattern, text, re.IGNORECASE)
        
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
            if abbrev not in abbreviations and len(abbrev) <= 6:  # Reasonable abbreviation length
                abbreviations[abbrev] = ['Unknown']
        
        logger.info(f"Detected {len(abbreviations)} potential abbreviations")
        return dict(abbreviations)
    
    def _generate_field_mappings(self, text: str) -> Dict[str, str]:
        """
        Generate field mappings from analyzed text
        
        Args:
            text (str): Text to analyze
            
        Returns:
            Dict[str, str]: Field mappings (variant -> canonical)
        """
        # Analyze text for fields first
        self._identify_potential_fields(text)
        
        # Create similarity clusters
        clusters = self._create_similarity_clusters()
        
        # Generate mappings
        field_mappings = {}
        
        for canonical_term, variants in clusters.items():
            for variant in variants:
                field_mappings[variant] = canonical_term
                # Also add common variations
                field_mappings[variant.replace('_', '')] = canonical_term
                field_mappings[variant.replace('_', ' ')] = canonical_term
        
        logger.info(f"Generated {len(field_mappings)} field mappings")
        return field_mappings
    
    def _create_similarity_clusters(self) -> Dict[str, Set[str]]:
        """
        Group similar terms together based on semantic similarity
        Enhanced with more comprehensive medical/research term patterns
        
        Returns:
            Dict[str, Set[str]]: Clusters of similar terms
        """
        clusters = defaultdict(set)
        
        # Enhanced similarity rules for comprehensive research terms
        similarity_rules = [
            # Age variations
            (['age', 'aged', 'mean_age', 'average_age', 'median_age', 'age_range', 'age_years'], 'age'),
            
            # Sample size variations  
            (['n', 'sample_size', 'participants', 'subjects', 'patients', 'study_population'], 'sample_size'),
            
            # Gender variations
            (['gender', 'sex', 'male', 'female'], 'gender'),
            
            # Mindfulness variations (domain-specific)
            (['mindfulness', 'mindful', 'meditation', 'awareness', 'mindful_awareness', 'mindful_attention'], 'mindfulness'),
            
            # Population variations
            (['children', 'child', 'adolescent', 'pediatric', 'paediatric'], 'population'),
            
            # Mental health outcomes
            (['anxiety', 'anxious', 'worry', 'worried'], 'anxiety'),
            (['depression', 'depressed', 'mood'], 'depression'),
            (['stress', 'stressed', 'stressful'], 'stress'),
            
            # Assessment variations
            (['scale', 'assessment', 'tool', 'measure', 'assessment_tool', 'measurement'], 'assessment'),
            
            # Intervention variations  
            (['intervention', 'treatment', 'therapy', 'protocol', 'intervention_type'], 'intervention'),
            
            # Outcome variations
            (['outcome', 'endpoint', 'primary_outcome', 'secondary_outcome', 'primary_outcomes'], 'outcomes'),
            
            # Study design variations
            (['randomized', 'randomised', 'rct', 'controlled_trial'], 'study_design'),
            
            # Medical conditions (cardiovascular)
            (['hypertension', 'high_blood_pressure', 'htn'], 'hypertension'),
            (['diabetes', 'diabetes_mellitus', 'dm', 'diabetic'], 'diabetes'),
            (['myocardial_infarction', 'heart_attack', 'mi'], 'myocardial_infarction'),
        ]
        
        # Apply similarity rules
        for similar_terms, canonical_term in similarity_rules:
            found_terms = set()
            for term in similar_terms:
                if term in self.term_frequencies:
                    found_terms.add(term)
            
            if found_terms:
                clusters[canonical_term] = list(found_terms)  # Convert set to list for JSON serialization
        
        self.field_clusters = clusters
        return dict(clusters)
    
    def normalize_extracted_value(self, value: str, field_type: str) -> str:
        """
        Normalize extracted values based on field type and common patterns
        Enhanced from domain_mapper functionality
        
        Args:
            value (str): Raw extracted value
            field_type (str): Type of field (age, sample_size, etc.)
            
        Returns:
            str: Normalized value
        """
        if not value or not isinstance(value, str):
            return str(value) if value else ""
        
        original_value = value
        value = value.strip()
        
        # Age normalization
        if field_type in ['age', 'mean_age', 'median_age']:
            age_patterns = [
                r'(\d+\.?\d*)\s*(?:years?|yrs?|y\.o\.?)',
                r'(?:age|aged)\s*(\d+\.?\d*)',
                r'(\d+\.?\d*)\s*$'
            ]
            
            for pattern in age_patterns:
                match = re.search(pattern, value, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            # Handle age ranges - take the midpoint
            range_match = re.search(r'(\d+)\s*-\s*(\d+)', value)
            if range_match:
                start, end = int(range_match.group(1)), int(range_match.group(2))
                midpoint = (start + end) / 2
                return str(midpoint)
        
        # Sample size normalization
        elif field_type in ['sample_size', 'n', 'participants', 'children', 'population']:
            size_patterns = [
                r'(\d+)\s*(?:children|participants?|subjects?|patients?)',
                r'n\s*=\s*(\d+)',
                r'(\d+)\s*$'
            ]
            
            for pattern in size_patterns:
                match = re.search(pattern, value, re.IGNORECASE)
                if match:
                    return match.group(1)
        
        # Assessment/scale normalization with acronym preservation
        elif field_type in ['assessment', 'scale', 'mindfulness', 'anxiety']:
            # Preserve research acronyms
            acronym_patterns = {
                r'\bSCARED\b': '<<SCARED>>',
                r'\bCAMM\b': '<<CAMM>>', 
                r'\bMASC\b': '<<MASC>>',
                r'\bCDI\b': '<<CDI>>',
                r'\bBDI\b': '<<BDI>>'
            }
            
            # Replace acronyms with placeholders
            for pattern, placeholder in acronym_patterns.items():
                value = re.sub(pattern, placeholder, value, flags=re.IGNORECASE)
            
            # Convert to lowercase
            value = value.lower()
            
            # Restore acronyms
            acronym_restore = {
                '<<scared>>': 'SCARED',
                '<<camm>>': 'CAMM',
                '<<masc>>': 'MASC', 
                '<<cdi>>': 'CDI',
                '<<bdi>>': 'BDI'
            }
            
            for placeholder, acronym in acronym_restore.items():
                value = value.replace(placeholder, acronym)
            
            return value
        
        # Default: basic cleanup
        else:
            return re.sub(r'\s+', ' ', value.lower().strip())