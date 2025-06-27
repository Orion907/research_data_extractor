"""
Unified Domain Priming Engine
Orchestrates the complete domain priming workflow as outlined in DOMAIN_PRIMING_REFACTOR_PLAN.md
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .enhanced_pattern_detector import EnhancedPatternDetector
from .term_mapper import TermMapper

logger = logging.getLogger(__name__)

class DomainPrimingEngine:
    """
    Unified engine that orchestrates the complete domain priming workflow:
    1. Phase 1: Build & Refine - Sample analysis and domain map generation
    2. Phase 2: Integrate & Test - Dynamic domain map integration for extraction
    """
    
    def __init__(self, 
                 llm_provider: str = "anthropic", 
                 api_key: Optional[str] = None,
                 model_name: Optional[str] = None,
                 min_frequency: int = 3,
                 min_term_length: int = 2):
        """
        Initialize the Domain Priming Engine
        
        Args:
            llm_provider (str): LLM provider for semantic enhancement
            api_key (Optional[str]): API key for LLM service
            model_name (Optional[str]): Specific model to use
            min_frequency (int): Minimum term frequency for significance
            min_term_length (int): Minimum term length for analysis
        """
        self.llm_provider = llm_provider
        self.api_key = api_key
        self.model_name = model_name
        
        # Initialize core components
        self.pattern_detector = EnhancedPatternDetector(
            min_frequency=min_frequency,
            min_term_length=min_term_length
        )
        
        self.term_mapper = TermMapper(
            provider=llm_provider,
            api_key=api_key,
            model_name=model_name
        )
        
        # Storage for domain profiles
        self.current_domain_profile: Optional[Dict] = None
        self.domain_profiles_dir = Path("data/domain_profiles")
        self.domain_profiles_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized DomainPrimingEngine with {llm_provider} provider")
    
    # =================================================================
    # PHASE 1: BUILD & REFINE
    # =================================================================
    
    def analyze_sample_articles(self, sample_texts: List[str], 
                              domain_name: Optional[str] = None) -> Dict:
        """
        Phase 1: Analyze sample articles to build domain vocabulary map
        
        Args:
            sample_texts (List[str]): Extracted text from 5-10 sample PDFs
            domain_name (Optional[str]): Name for this domain (for storage)
            
        Returns:
            Dict: Complete domain analysis results
        """
        logger.info(f"Starting Phase 1: Analyzing {len(sample_texts)} sample articles")
        
        if len(sample_texts) < 1:
            raise ValueError("At least 1 sample text is required for domain analysis")
        
        if len(sample_texts) > 20:
            logger.warning(f"Large number of samples ({len(sample_texts)}). Consider using 5-10 for optimal performance.")
        
        # Step 1: Enhanced pattern detection
        logger.info("Step 1: Running enhanced pattern detection...")
        pattern_results = self.pattern_detector.analyze_sample_texts(sample_texts)
        
        # Step 2: LLM-enhanced semantic mapping
        logger.info("Step 2: Enhancing patterns with LLM semantic understanding...")
        enhanced_patterns = self.term_mapper.enhance_with_llm(pattern_results)
        
        # Step 3: Create comprehensive domain profile
        domain_profile = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "domain_name": domain_name or f"domain_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "sample_count": len(sample_texts),
                "llm_provider": self.llm_provider,
                "model_name": self.model_name,
                "engine_version": "1.0"
            },
            "raw_patterns": pattern_results,
            "enhanced_patterns": enhanced_patterns,
            "domain_map": self._create_domain_map(pattern_results, enhanced_patterns),
            "statistics": {
                "total_terms": len(pattern_results.get('term_frequencies', {})),
                "significant_terms": len([t for t, f in pattern_results.get('term_frequencies', {}).items() if f >= 3]),
                "potential_fields": len(pattern_results.get('potential_fields', [])),
                "abbreviations": len(pattern_results.get('abbreviations', {})),
                "synonym_mappings": len(enhanced_patterns.get('synonym_mappings', {}))
            }
        }
        
        self.current_domain_profile = domain_profile
        
        logger.info(f"Phase 1 complete: Generated domain profile with {domain_profile['statistics']['total_terms']} terms")
        return domain_profile
    
    def _create_domain_map(self, raw_patterns: Dict, enhanced_patterns: Dict) -> Dict[str, List[str]]:
        """
        Create the core domain map structure: canonical_term -> [equivalent_terms]
        As specified in the plan: {'Hypertension': ['High blood pressure', 'HTN']}
        
        Args:
            raw_patterns (Dict): Raw pattern detection results
            enhanced_patterns (Dict): LLM-enhanced patterns
            
        Returns:
            Dict[str, List[str]]: Domain map with canonical terms as keys
        """
        domain_map = {}
        
        # Process LLM-enhanced synonym mappings
        synonym_mappings = enhanced_patterns.get('synonym_mappings', {})
        for canonical_term, synonyms in synonym_mappings.items():
            if isinstance(synonyms, list) and synonyms:
                domain_map[canonical_term] = synonyms
        
        # Process abbreviation expansions
        abbreviation_expansions = enhanced_patterns.get('abbreviation_expansions', {})
        for abbrev, expansion_data in abbreviation_expansions.items():
            if isinstance(expansion_data, dict):
                full_form = expansion_data.get('full_form', '')
                variations = expansion_data.get('variations', [])
                if full_form and full_form != 'unknown_expansion':
                    # Add abbreviation to the full form's synonyms
                    if full_form in domain_map:
                        domain_map[full_form].append(abbrev)
                    else:
                        domain_map[full_form] = [abbrev]
                    
                    # Add variations
                    if variations:
                        domain_map[full_form].extend(variations)
        
        # Process similarity clusters from raw patterns
        similarity_clusters = raw_patterns.get('similarity_clusters', {})
        for canonical_term, variant_set in similarity_clusters.items():
            # Convert set to list for JSON serialization
            variants = list(variant_set) if isinstance(variant_set, set) else variant_set
            if canonical_term in domain_map:
                domain_map[canonical_term].extend(variants)
            else:
                domain_map[canonical_term] = variants
        
        # Remove duplicates and ensure canonical term is not in its own synonyms
        for canonical_term, synonyms in domain_map.items():
            # Remove duplicates and the canonical term itself
            unique_synonyms = list(set(synonyms))
            if canonical_term in unique_synonyms:
                unique_synonyms.remove(canonical_term)
            domain_map[canonical_term] = unique_synonyms
        
        logger.info(f"Created domain map with {len(domain_map)} canonical terms")
        return domain_map
    
    def review_and_refine_domain_map(self, 
                                   user_modifications: Optional[Dict] = None,
                                   save_profile: bool = True) -> Dict:
        """
        Phase 1: Human-in-the-loop review and refinement of domain map
        Critical safety feature as specified in the plan
        
        Args:
            user_modifications (Optional[Dict]): User's manual edits to the domain map
            save_profile (bool): Whether to save the refined profile
            
        Returns:
            Dict: Refined domain profile
        """
        if not self.current_domain_profile:
            raise ValueError("No domain profile to refine. Run analyze_sample_articles first.")
        
        logger.info("Starting human review and refinement of domain map")
        
        original_map = self.current_domain_profile['domain_map'].copy()
        
        if user_modifications:
            # Apply user modifications
            for action, data in user_modifications.items():
                if action == 'add_mapping':
                    # Add new canonical term with synonyms
                    canonical = data.get('canonical')
                    synonyms = data.get('synonyms', [])
                    if canonical:
                        self.current_domain_profile['domain_map'][canonical] = synonyms
                
                elif action == 'edit_mapping':
                    # Edit existing mapping
                    canonical = data.get('canonical')
                    new_synonyms = data.get('synonyms', [])
                    if canonical in self.current_domain_profile['domain_map']:
                        self.current_domain_profile['domain_map'][canonical] = new_synonyms
                
                elif action == 'delete_mapping':
                    # Delete mapping
                    canonical = data.get('canonical')
                    if canonical in self.current_domain_profile['domain_map']:
                        del self.current_domain_profile['domain_map'][canonical]
                
                elif action == 'merge_mappings':
                    # Merge two mappings
                    primary = data.get('primary')
                    secondary = data.get('secondary')
                    if primary in self.current_domain_profile['domain_map'] and secondary in self.current_domain_profile['domain_map']:
                        # Merge secondary into primary
                        self.current_domain_profile['domain_map'][primary].extend(
                            self.current_domain_profile['domain_map'][secondary]
                        )
                        self.current_domain_profile['domain_map'][primary].append(secondary)
                        del self.current_domain_profile['domain_map'][secondary]
                        # Remove duplicates
                        self.current_domain_profile['domain_map'][primary] = list(set(
                            self.current_domain_profile['domain_map'][primary]
                        ))
        
        # Update metadata
        self.current_domain_profile['metadata']['last_refined'] = datetime.now().isoformat()
        self.current_domain_profile['metadata']['user_refined'] = True
        
        # Update statistics
        refined_map = self.current_domain_profile['domain_map']
        self.current_domain_profile['statistics']['refined_mappings'] = len(refined_map)
        self.current_domain_profile['statistics']['total_synonyms'] = sum(len(synonyms) for synonyms in refined_map.values())
        
        if save_profile:
            self.save_domain_profile()
        
        changes = len(refined_map) - len(original_map)
        logger.info(f"Domain map refinement complete. Changes: {changes:+d} mappings")
        
        return self.current_domain_profile
    
    def save_domain_profile(self, filename: Optional[str] = None) -> str:
        """
        Save current domain profile to file
        
        Args:
            filename (Optional[str]): Custom filename, auto-generated if None
            
        Returns:
            str: Path to saved file
        """
        if not self.current_domain_profile:
            raise ValueError("No domain profile to save")
        
        if not filename:
            domain_name = self.current_domain_profile['metadata']['domain_name']
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{domain_name}_{timestamp}.json"
        
        filepath = self.domain_profiles_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.current_domain_profile, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved domain profile to {filepath}")
        return str(filepath)
    
    def load_domain_profile(self, filepath: str) -> Dict:
        """
        Load domain profile from file
        
        Args:
            filepath (str): Path to domain profile file
            
        Returns:
            Dict: Loaded domain profile
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            profile = json.load(f)
        
        self.current_domain_profile = profile
        logger.info(f"Loaded domain profile from {filepath}")
        return profile
    
    # =================================================================
    # PHASE 2: INTEGRATE & TEST
    # =================================================================
    
    def generate_enhanced_prompt(self, 
                               base_prompt: str,
                               picots_terms: List[str],
                               max_mappings: int = 10) -> str:
        """
        Phase 2: Generate enhanced prompt with dynamic domain map injection
        Only includes PICOTS-relevant equivalencies as specified in the plan
        
        Args:
            base_prompt (str): Original extraction prompt based on PICOTS
            picots_terms (List[str]): Key terms from user's PICOTS
            max_mappings (int): Maximum number of mappings to include
            
        Returns:
            str: Enhanced prompt with relevant domain mappings
        """
        if not self.current_domain_profile:
            logger.warning("No domain profile loaded. Returning base prompt unchanged.")
            return base_prompt
        
        domain_map = self.current_domain_profile['domain_map']
        
        # Find relevant mappings based on PICOTS terms
        relevant_mappings = {}
        picots_terms_lower = [term.lower() for term in picots_terms]
        
        for canonical_term, synonyms in domain_map.items():
            # Check if canonical term or any synonym matches PICOTS terms
            all_terms = [canonical_term.lower()] + [syn.lower() for syn in synonyms]
            
            for picots_term in picots_terms_lower:
                if any(picots_term in term or term in picots_term for term in all_terms):
                    relevant_mappings[canonical_term] = synonyms
                    break
        
        # Limit number of mappings to avoid overwhelming context window
        if len(relevant_mappings) > max_mappings:
            # Sort by number of synonyms (more comprehensive mappings first)
            sorted_mappings = sorted(
                relevant_mappings.items(), 
                key=lambda x: len(x[1]), 
                reverse=True
            )
            relevant_mappings = dict(sorted_mappings[:max_mappings])
        
        if not relevant_mappings:
            logger.info("No relevant domain mappings found for PICOTS terms")
            return base_prompt
        
        # Create domain mapping section for prompt
        mapping_section = "Please consider the following terms as equivalent for extraction:\n"
        for canonical_term, synonyms in relevant_mappings.items():
            if synonyms:  # Only include if there are actually synonyms
                synonym_list = "', '".join(synonyms)
                mapping_section += f"- '{canonical_term}' and '{synonym_list}'\n"
        
        mapping_section += "\nWhen extracting data, if any of these equivalent terms are found, report them using the canonical term (the first term listed). For example, if you find 'high blood pressure', report it as 'hypertension'.\n\n"
        
        # Insert mapping section after any existing instructions but before the main task
        enhanced_prompt = base_prompt + "\n\n" + mapping_section
        
        logger.info(f"Enhanced prompt with {len(relevant_mappings)} relevant domain mappings")
        return enhanced_prompt
    
    def extract_picots_terms(self, picots_data: Dict) -> List[str]:
        """
        Extract key terms from PICOTS data for domain mapping lookup
        
        Args:
            picots_data (Dict): PICOTS information from user
            
        Returns:
            List[str]: Key terms for domain mapping
        """
        terms = []
        
        # Extract terms from each PICOTS component
        for component, value in picots_data.items():
            if isinstance(value, str) and value.strip():
                # Simple term extraction - split by common separators
                component_terms = []
                for separator in [',', ';', ' and ', ' or ', '/', '|']:
                    if separator in value:
                        component_terms.extend([t.strip() for t in value.split(separator)])
                        break
                else:
                    # No separators found, use the whole value
                    component_terms = [value.strip()]
                
                # Clean and filter terms
                for term in component_terms:
                    clean_term = term.strip().lower()
                    # Extract individual words from phrases
                    words = clean_term.split()
                    for word in words:
                        if len(word) > 2 and word.isalpha():  # Filter out very short terms and non-alphabetic
                            terms.append(word)
        
        logger.info(f"Extracted {len(terms)} key terms from PICOTS data")
        return terms
    
    def get_domain_profile_summary(self) -> Optional[Dict]:
        """
        Get summary of current domain profile
        
        Returns:
            Optional[Dict]: Summary information or None if no profile loaded
        """
        if not self.current_domain_profile:
            return None
        
        metadata = self.current_domain_profile['metadata']
        statistics = self.current_domain_profile['statistics']
        
        return {
            'domain_name': metadata.get('domain_name', 'Unknown'),
            'created_at': metadata.get('created_at', 'Unknown'),
            'last_refined': metadata.get('last_refined', 'Never'),
            'sample_count': metadata.get('sample_count', 0),
            'total_mappings': len(self.current_domain_profile.get('domain_map', {})),
            'total_synonyms': statistics.get('total_synonyms', 0),
            'llm_provider': metadata.get('llm_provider', 'Unknown'),
            'user_refined': metadata.get('user_refined', False)
        }
    
    def list_available_profiles(self) -> List[Dict]:
        """
        List all available domain profiles
        
        Returns:
            List[Dict]: List of profile summaries
        """
        profiles = []
        
        for profile_file in self.domain_profiles_dir.glob("*.json"):
            try:
                with open(profile_file, 'r', encoding='utf-8') as f:
                    profile = json.load(f)
                
                metadata = profile.get('metadata', {})
                statistics = profile.get('statistics', {})
                
                profiles.append({
                    'filename': profile_file.name,
                    'filepath': str(profile_file),
                    'domain_name': metadata.get('domain_name', 'Unknown'),
                    'created_at': metadata.get('created_at', 'Unknown'),
                    'sample_count': metadata.get('sample_count', 0),
                    'total_mappings': statistics.get('refined_mappings', statistics.get('total_terms', 0))
                })
            except Exception as e:
                logger.warning(f"Could not read profile {profile_file.name}: {e}")
        
        return sorted(profiles, key=lambda x: x['created_at'], reverse=True)