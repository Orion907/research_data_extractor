"""
Domain-adaptive field mapping generator
Analyzes article content to create context-specific field mappings
"""
import re
import logging
from collections import Counter, defaultdict
from typing import Dict, List, Set, Tuple

logger = logging.getLogger(__name__)

class DomainMapper:
    """
    Generates domain-specific field mappings by analyzing article content
    """
    
    def __init__(self):
        self.potential_fields = set()
        self.term_frequencies = Counter()
        self.field_clusters = defaultdict(set)
        
    def analyze_text_for_fields(self, text: str) -> Set[str]:
        """
        Extract potential field names from text content
        
        Args:
            text (str): Article text content
            
        Returns:
            Set[str]: Potential field names found
        """
        potential_fields = set()
        
        # Patterns for common research field indicators
        field_patterns = [
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
            
            # Mindfulness-specific (for your use case)
            r'\b(mindfulness|meditation|mindful|awareness)\b',
            r'\b(anxiety|depression|stress|wellbeing|well-being)\b',
            r'\b(children|child|adolescent|pediatric|paediatric)\b',
        ]
        
        # Extract terms using patterns
        for pattern in field_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Clean and normalize the match
                clean_match = re.sub(r'\s+', '_', match.strip().lower())
                potential_fields.add(clean_match)
                self.term_frequencies[clean_match] += 1
        
        # Look for structured data indicators (tables, lists)
        structured_patterns = [
            r'(\w+):\s*([^,\n]+)',  # "Age: 12.5 years"
            r'(\w+)\s*=\s*([^,\n]+)',  # "n = 150"
            r'(\w+)\s*\(\s*([^)]+)\)',  # "Participants (n=150)"
        ]
        
        for pattern in structured_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for field_name, value in matches:
                clean_field = re.sub(r'\s+', '_', field_name.strip().lower())
                potential_fields.add(clean_field)
                self.term_frequencies[clean_field] += 1
        
        return potential_fields
    
    def create_similarity_clusters(self) -> Dict[str, Set[str]]:
        """
        Group similar terms together based on semantic similarity
        
        Returns:
            Dict[str, Set[str]]: Clusters of similar terms
        """
        clusters = defaultdict(set)
        
        # Enhanced similarity rules for common research terms
        similarity_rules = [
            # Age variations
            (['age', 'aged', 'mean_age', 'average_age', 'median_age', 'age_range', 'age_years'], 'age'),
            
            # Sample size variations  
            (['n', 'sample_size', 'participants', 'subjects', 'patients', 'study_population'], 'sample_size'),
            
            # Gender variations
            (['gender', 'sex', 'male', 'female'], 'gender'),
            
            # Mindfulness variations (domain-specific) - FIXED: Added mindful_awareness
            (['mindfulness', 'mindful', 'meditation', 'awareness', 'mindful_awareness', 'mindful_attention'], 'mindfulness'),
            
            # Population variations (for your use case)
            (['children', 'child', 'adolescent', 'pediatric', 'paediatric'], 'population'),
            
            # Outcome variations
            (['anxiety', 'anxious', 'worry', 'worried'], 'anxiety'),
            (['depression', 'depressed', 'mood'], 'depression'),
            
            # NEW: Assessment variations
            (['scale', 'assessment', 'tool', 'measure', 'assessment_tool', 'measurement'], 'assessment'),
            
            # NEW: Intervention variations  
            (['intervention', 'treatment', 'therapy', 'protocol', 'intervention_type'], 'intervention'),
            
            # NEW: Outcome variations
            (['outcome', 'endpoint', 'primary_outcome', 'secondary_outcome', 'primary_outcomes'], 'outcomes'),
        ]
        
        # Apply similarity rules
        for similar_terms, canonical_term in similarity_rules:
            found_terms = set()
            for term in similar_terms:
                if term in self.term_frequencies:
                    found_terms.add(term)
            
            if found_terms:
                clusters[canonical_term] = found_terms
        
        return dict(clusters)
    
    def generate_field_mappings(self, texts: List[str]) -> Dict[str, str]:
        """
        Generate field mappings from a collection of article texts
        
        Args:
            texts (List[str]): List of article text contents
            
        Returns:
            Dict[str, str]: Field mappings (variant -> canonical)
        """
        logger.info(f"Analyzing {len(texts)} articles for domain-specific field mappings")
        
        # Analyze all texts
        for text in texts:
            fields = self.analyze_text_for_fields(text)
            self.potential_fields.update(fields)
        
        # Create similarity clusters
        clusters = self.create_similarity_clusters()
        
        # Generate mappings
        field_mappings = {}
        
        for canonical_term, variants in clusters.items():
            for variant in variants:
                field_mappings[variant] = canonical_term
                # Also add common variations
                field_mappings[variant.replace('_', '')] = canonical_term
                field_mappings[variant.replace('_', ' ')] = canonical_term
        
        logger.info(f"Generated {len(field_mappings)} field mappings from domain analysis")
        logger.info(f"Top terms found: {self.term_frequencies.most_common(10)}")
        
        return field_mappings

    def get_analysis_summary(self) -> Dict:
        """
        Get summary of the domain analysis
        
        Returns:
            Dict: Analysis summary with statistics
        """
        return {
            "total_potential_fields": len(self.potential_fields),
            "top_terms": self.term_frequencies.most_common(20),
            "field_clusters": dict(self.field_clusters)
        }
    
    def normalize_extracted_value(self, value: str, field_type: str) -> str:
        """
        Normalize extracted values based on field type and common patterns
        
        Args:
            value (str): Raw extracted value
            field_type (str): Type of field (age, sample_size, etc.)
            
        Returns:
            str: Normalized value
        """
        if not value or not isinstance(value, str):
            return str(value) if value else ""
        
        # Store original for fallback
        original_value = value
        value = value.strip()
        
        # Age normalization
        if field_type in ['age', 'mean_age', 'median_age']:
            # Extract numerical age from patterns like "10.2 years", "aged 12-15", "mean age 10.5"
            age_patterns = [
                r'(\d+\.?\d*)\s*(?:years?|yrs?|y\.o\.?)',  # "10.2 years"
                r'(?:age|aged)\s*(\d+\.?\d*)',             # "aged 10.2"
                r'(\d+\.?\d*)\s*$'                         # Just numbers
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
        
        # Sample size normalization - FIXED: More flexible field matching
        elif field_type in ['sample_size', 'n', 'participants', 'children', 'population']:
            # Extract numbers from patterns like "150 children", "n=75"
            size_patterns = [
                r'(\d+)\s*(?:children|participants?|subjects?|patients?)',  # "150 children"
                r'n\s*=\s*(\d+)',                                          # "n=75"
                r'(\d+)\s*$'                                               # Just numbers
            ]
            
            for pattern in size_patterns:
                match = re.search(pattern, value, re.IGNORECASE)
                if match:
                    return match.group(1)
        
        # Assessment/scale normalization - FIXED: Preserve acronyms before lowercasing
        elif field_type in ['assessment', 'scale', 'mindfulness', 'anxiety']:
            # First, preserve research acronyms BEFORE converting to lowercase
            acronym_patterns = {
                r'\bSCARED\b': '<<SCARED>>',  # Temporary placeholder
                r'\bCAMM\b': '<<CAMM>>', 
                r'\bMASC\b': '<<MASC>>',
                r'\bCDI\b': '<<CDI>>',
                r'\bBDI\b': '<<BDI>>'
            }
            
            # Replace acronyms with placeholders
            for pattern, placeholder in acronym_patterns.items():
                value = re.sub(pattern, placeholder, value, flags=re.IGNORECASE)
            
            # Now convert to lowercase
            value = value.lower()
            
            # Restore acronyms from placeholders
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
            # Remove extra whitespace, convert to lowercase for consistency
            return re.sub(r'\s+', ' ', value.lower().strip())