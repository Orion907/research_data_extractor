"""
Unified Domain Priming Engine
Orchestrates the complete domain priming workflow as outlined in DOMAIN_PRIMING_REFACTOR_PLAN.md
"""
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
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
    
    def generate_enhanced_prompts_by_picots(self, 
                                           base_prompt: str,
                                           picots_data: Dict,
                                           max_context_tokens: int = 6000) -> Dict[str, str]:
        """
        Phase 2: Generate context-aware enhanced prompts chunked by PICOTS sections
        Creates separate prompts for each PICOTS component to manage context size
        
        Args:
            base_prompt (str): Original extraction prompt template
            picots_data (Dict): PICOTS information with section-specific details
            max_context_tokens (int): Maximum tokens per prompt (conservative estimate)
            
        Returns:
            Dict[str, str]: Mapping of PICOTS section to enhanced prompt
        """
        if not self.current_domain_profile:
            logger.warning("No domain profile loaded. Returning base prompts unchanged.")
            return self._create_base_picots_prompts(base_prompt, picots_data)
        
        enhanced_prompts = {}
        domain_map = self.current_domain_profile['domain_map']
        
        # Define PICOTS sections and their priorities
        picots_sections = {
            'Population': picots_data.get('Population', ''),
            'Intervention': picots_data.get('Intervention', ''), 
            'Comparator': picots_data.get('Comparator', ''),
            'Outcome': picots_data.get('Outcome', ''),
            'Timing': picots_data.get('Timing', ''),
            'Setting': picots_data.get('Setting', '')
        }
        
        for section_name, section_content in picots_sections.items():
            if not section_content:
                continue
                
            # Extract terms specific to this PICOTS section
            section_terms = self._extract_terms_from_text(section_content)
            
            # Find relevant mappings for this section
            section_mappings = self._find_relevant_mappings(domain_map, section_terms)
            
            # Create context-aware prompt for this section
            section_prompt = self._create_section_prompt(
                base_prompt, 
                section_name, 
                section_content,
                section_mappings,
                max_context_tokens
            )
            
            enhanced_prompts[section_name] = section_prompt
            
            logger.info(f"Created enhanced prompt for {section_name} with {len(section_mappings)} mappings")
        
        return enhanced_prompts
    
    def _create_base_picots_prompts(self, base_prompt: str, picots_data: Dict) -> Dict[str, str]:
        """Create base prompts without domain enhancement"""
        prompts = {}
        for section in ['Population', 'Intervention', 'Comparator', 'Outcome', 'Timing', 'Setting']:
            if picots_data.get(section):
                prompts[section] = f"{base_prompt}\n\nFocus specifically on extracting {section.lower()} information: {picots_data[section]}"
        return prompts
    
    def _extract_terms_from_text(self, text: str) -> List[str]:
        """Extract meaningful terms from PICOTS section text"""
        import re
        from nltk.tokenize import word_tokenize
        
        # Clean and tokenize
        cleaned_text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = word_tokenize(cleaned_text)
        
        # Filter meaningful terms (length > 2, not stopwords)
        stop_words = self.pattern_detector.stop_words
        meaningful_terms = [
            word for word in words 
            if len(word) > 2 and word not in stop_words
        ]
        
        # Also extract multi-word phrases (2-3 words)
        phrases = []
        words_list = text.lower().split()
        for i in range(len(words_list) - 1):
            # Two-word phrases
            phrase = f"{words_list[i]} {words_list[i+1]}"
            if len(phrase) > 5 and not any(stop in phrase for stop in ['and', 'or', 'the', 'of']):
                phrases.append(phrase)
            
            # Three-word phrases
            if i < len(words_list) - 2:
                phrase3 = f"{words_list[i]} {words_list[i+1]} {words_list[i+2]}"
                if len(phrase3) > 8 and not any(stop in phrase3 for stop in ['and', 'or', 'the', 'of']):
                    phrases.append(phrase3)
        
        return meaningful_terms + phrases
    
    def _find_relevant_mappings(self, domain_map: Dict[str, List[str]], section_terms: List[str]) -> Dict[str, List[str]]:
        """Find domain mappings relevant to specific PICOTS section terms"""
        relevant_mappings = {}
        section_terms_lower = [term.lower() for term in section_terms]
        
        for canonical_term, synonyms in domain_map.items():
            # Check if canonical term or synonyms match section terms
            all_mapping_terms = [canonical_term.lower()] + [syn.lower() for syn in synonyms]
            
            # Use more sophisticated matching
            for section_term in section_terms_lower:
                for mapping_term in all_mapping_terms:
                    # Exact match or substring match (both directions)
                    if (section_term == mapping_term or 
                        section_term in mapping_term or 
                        mapping_term in section_term):
                        relevant_mappings[canonical_term] = synonyms
                        break
                if canonical_term in relevant_mappings:
                    break
        
        return relevant_mappings
    
    def _create_section_prompt(self, 
                              base_prompt: str,
                              section_name: str, 
                              section_content: str,
                              section_mappings: Dict[str, List[str]],
                              max_context_tokens: int) -> str:
        """Create context-aware prompt for specific PICOTS section"""
        
        # Estimate token usage (rough approximation: 4 chars = 1 token)
        base_tokens = len(base_prompt) // 4
        section_tokens = len(section_content) // 4
        
        # Reserve tokens for response and safety margin
        available_tokens = max_context_tokens - base_tokens - section_tokens - 500
        
        # Build domain mapping section within token limit
        mapping_section = ""
        if section_mappings and available_tokens > 100:
            mapping_section = f"\nFor {section_name.lower()} extraction, consider these equivalent terms:\n"
            
            # Sort mappings by relevance (number of synonyms as proxy)
            sorted_mappings = sorted(
                section_mappings.items(),
                key=lambda x: len(x[1]),
                reverse=True
            )
            
            used_tokens = len(mapping_section) // 4
            
            for canonical_term, synonyms in sorted_mappings:
                if not synonyms:
                    continue
                    
                # Estimate tokens for this mapping
                mapping_line = f"- '{canonical_term}' = {', '.join(synonyms[:3])}\n"  # Limit synonyms
                mapping_tokens = len(mapping_line) // 4
                
                if used_tokens + mapping_tokens > available_tokens:
                    break
                    
                mapping_section += mapping_line
                used_tokens += mapping_tokens
            
            mapping_section += f"\nUse canonical terms (first term) in your {section_name.lower()} extraction.\n"
        
        # Construct final prompt
        section_specific_prompt = f"""{base_prompt}

FOCUS: Extract {section_name.upper()} information specifically.
Target: {section_content}{mapping_section}

Extract all relevant {section_name.lower()} data from the provided text, using the canonical terms where equivalent terms are found."""
        
        return section_specific_prompt
    
    def estimate_prompt_tokens(self, prompt: str) -> int:
        """Rough estimation of prompt tokens (4 characters ≈ 1 token)"""
        return len(prompt) // 4
    
    def generate_enhanced_prompt(self, 
                               base_prompt: str,
                               picots_terms: List[str],
                               max_mappings: int = 10) -> str:
        """
        Legacy method: Generate single enhanced prompt 
        DEPRECATED: Use generate_enhanced_prompts_by_picots() for better context management
        
        Args:
            base_prompt (str): Original extraction prompt based on PICOTS
            picots_terms (List[str]): Key terms from user's PICOTS  
            max_mappings (int): Maximum number of mappings to include
            
        Returns:
            str: Enhanced prompt with relevant domain mappings
        """
        logger.warning("Using deprecated generate_enhanced_prompt(). Consider using generate_enhanced_prompts_by_picots() for better context management.")
        
        if not self.current_domain_profile:
            logger.warning("No domain profile loaded. Returning base prompt unchanged.")
            return base_prompt
        
        domain_map = self.current_domain_profile['domain_map']
        
        # Find relevant mappings based on PICOTS terms (simplified legacy logic)
        relevant_mappings = {}
        picots_terms_lower = [term.lower() for term in picots_terms]
        
        for canonical_term, synonyms in domain_map.items():
            all_terms = [canonical_term.lower()] + [syn.lower() for syn in synonyms]
            
            for picots_term in picots_terms_lower:
                if any(picots_term in term or term in picots_term for term in all_terms):
                    relevant_mappings[canonical_term] = synonyms
                    break
        
        # Limit mappings
        if len(relevant_mappings) > max_mappings:
            sorted_mappings = sorted(relevant_mappings.items(), key=lambda x: len(x[1]), reverse=True)
            relevant_mappings = dict(sorted_mappings[:max_mappings])
        
        if not relevant_mappings:
            logger.info("No relevant domain mappings found for PICOTS terms")
            return base_prompt
        
        # Create simple mapping section
        mapping_section = "Please consider the following terms as equivalent for extraction:\n"
        for canonical_term, synonyms in relevant_mappings.items():
            if synonyms:
                synonym_list = "', '".join(synonyms[:3])  # Limit to 3 synonyms
                mapping_section += f"- '{canonical_term}' and '{synonym_list}'\n"
        
        mapping_section += "\nWhen extracting data, use the canonical term (first term listed).\n\n"
        enhanced_prompt = base_prompt + "\n\n" + mapping_section
        
        logger.info(f"Enhanced prompt with {len(relevant_mappings)} relevant domain mappings")
        return enhanced_prompt
    
    def execute_picots_extraction_workflow(self,
                                         text_chunks: List[str],
                                         picots_data: Dict,
                                         extraction_engine,
                                         base_prompt_template: str = None,
                                         optimization_level: str = "balanced") -> Dict[str, List[Dict]]:
        """
        LEGACY METHOD: Execute PICOTS extraction workflow (sequential)
        Use execute_optimized_picots_workflow() for better performance
        
        Args:
            text_chunks (List[str]): Text chunks to process
            picots_data (Dict): PICOTS research question data
            extraction_engine: LLM extraction engine instance
            base_prompt_template (str): Base prompt template
            optimization_level (str): "sequential", "parallel", or "balanced"
            
        Returns:
            Dict[str, List[Dict]]: Results organized by PICOTS section
        """
        logger.warning("Using legacy execute_picots_extraction_workflow(). Consider using execute_optimized_picots_workflow() for better performance.")
        
        if optimization_level in ["parallel", "balanced"]:
            return self.execute_optimized_picots_workflow(
                text_chunks, picots_data, extraction_engine, base_prompt_template, optimization_level
            )
        
        # Original sequential implementation for backward compatibility
        if not base_prompt_template:
            base_prompt_template = "Extract research data from the following text according to the specified criteria."
        
        enhanced_prompts = self.generate_enhanced_prompts_by_picots(base_prompt_template, picots_data)
        extraction_results = {}
        
        logger.info(f"Starting sequential PICOTS extraction workflow for {len(enhanced_prompts)} sections across {len(text_chunks)} chunks")
        
        for section_idx, (section_name, section_prompt) in enumerate(enhanced_prompts.items(), 1):
            logger.info(f"Processing {section_name} section ({section_idx}/{len(enhanced_prompts)})")
            section_results = []
            
            for chunk_idx, text_chunk in enumerate(text_chunks, 1):
                try:
                    chunk_result = extraction_engine.extract_from_chunk(
                        text_chunk, section_prompt, section_context=section_name
                    )
                    if chunk_result:
                        chunk_result['section'] = section_name
                        chunk_result['chunk_index'] = chunk_idx
                        section_results.append(chunk_result)
                except Exception as e:
                    logger.error(f"Error processing {section_name} section, chunk {chunk_idx}: {e}")
                    continue
            
            extraction_results[section_name] = section_results
        
        # Add metadata
        total_extractions = sum(len(results) for results in extraction_results.values())
        sections_processed = len(extraction_results)
        
        extraction_results['_metadata'] = {
            'total_sections_processed': sections_processed,
            'total_chunks_processed': len(text_chunks),
            'total_successful_extractions': total_extractions,
            'domain_profile_used': self.current_domain_profile['metadata']['domain_name'] if self.current_domain_profile else None,
            'workflow_completed_at': datetime.now().isoformat(),
            'optimization_level': 'sequential'
        }
        
        return extraction_results

    def execute_optimized_picots_workflow(self,
                                        text_chunks: List[str],
                                        picots_data: Dict,
                                        extraction_engine,
                                        base_prompt_template: str = None,
                                        optimization_level: str = "balanced") -> Dict[str, List[Dict]]:
        """
        Execute optimized PICOTS extraction workflow with intelligent batching and parallel processing
        
        Args:
            text_chunks (List[str]): Text chunks to process
            picots_data (Dict): PICOTS research question data
            extraction_engine: LLM extraction engine instance
            base_prompt_template (str): Base prompt template
            optimization_level (str): "parallel", "batched", or "balanced"
            
        Returns:
            Dict[str, List[Dict]]: Results organized by PICOTS section
        """
        if not base_prompt_template:
            base_prompt_template = "Extract research data from the following text according to the specified criteria."
        
        start_time = datetime.now()
        
        # Step 1: Filter and prepare PICOTS sections
        filtered_picots = self._filter_relevant_picots_sections(picots_data)
        if not filtered_picots:
            logger.warning("No relevant PICOTS sections found after filtering")
            return {'_metadata': {'error': 'No relevant PICOTS sections'}}
        
        logger.info(f"Starting optimized PICOTS workflow: {len(filtered_picots)} sections, {len(text_chunks)} chunks, {optimization_level} mode")
        
        # Step 2: Optimize shared context
        shared_context = self._extract_shared_context(text_chunks)
        
        # Step 3: Choose optimization strategy
        if optimization_level == "parallel":
            results = self._execute_parallel_picots(
                text_chunks, filtered_picots, extraction_engine, base_prompt_template, shared_context
            )
        elif optimization_level == "batched":
            results = self._execute_batched_picots(
                text_chunks, filtered_picots, extraction_engine, base_prompt_template, shared_context
            )
        else:  # balanced
            results = self._execute_balanced_picots(
                text_chunks, filtered_picots, extraction_engine, base_prompt_template, shared_context
            )
        
        # Step 4: Generate comprehensive metadata
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        total_extractions = sum(len(section_results) for section_results in results.values())
        
        results['_metadata'] = {
            'total_sections_processed': len(results),
            'total_chunks_processed': len(text_chunks),
            'total_successful_extractions': total_extractions,
            'domain_profile_used': self.current_domain_profile['metadata']['domain_name'] if self.current_domain_profile else None,
            'workflow_completed_at': end_time.isoformat(),
            'processing_time_seconds': processing_time,
            'optimization_level': optimization_level,
            'sections_filtered': len(picots_data) - len(filtered_picots),
            'efficiency_metrics': {
                'extractions_per_second': total_extractions / processing_time if processing_time > 0 else 0,
                'avg_time_per_section': processing_time / len(filtered_picots) if filtered_picots else 0,
                'avg_time_per_chunk': processing_time / len(text_chunks) if text_chunks else 0
            }
        }
        
        logger.info(f"Optimized PICOTS workflow completed in {processing_time:.2f}s: {total_extractions} extractions")
        return results
    
    def _filter_relevant_picots_sections(self, picots_data: Dict) -> Dict[str, str]:
        """
        Filter PICOTS sections to only include those with meaningful content
        
        Args:
            picots_data (Dict): Raw PICOTS data
            
        Returns:
            Dict[str, str]: Filtered PICOTS sections with content
        """
        filtered = {}
        
        for section_name, content in picots_data.items():
            if content and isinstance(content, str):
                # Filter out sections with minimal content
                cleaned_content = content.strip()
                if len(cleaned_content) >= 10 and not cleaned_content.lower() in ['n/a', 'none', 'not applicable', 'tbd', 'tba']:
                    filtered[section_name] = cleaned_content
                    
        logger.info(f"Filtered PICOTS sections: {len(filtered)}/{len(picots_data)} sections have meaningful content")
        return filtered
    
    def _extract_shared_context(self, text_chunks: List[str]) -> Dict[str, Any]:
        """
        Extract shared context that can be reused across PICOTS sections
        
        Args:
            text_chunks (List[str]): Text chunks to analyze
            
        Returns:
            Dict[str, Any]: Shared context information
        """
        # Analyze common patterns across all chunks
        all_text = "\n".join(text_chunks)
        
        # Extract common research patterns
        shared_context = {
            'total_word_count': len(all_text.split()),
            'chunk_count': len(text_chunks),
            'estimated_total_tokens': self.estimate_prompt_tokens(all_text),
            'common_abbreviations': self._extract_common_abbreviations(all_text),
            'study_type_indicators': self._extract_study_type_indicators(all_text),
            'common_measurement_terms': self._extract_measurement_terms(all_text)
        }
        
        logger.info(f"Extracted shared context: {shared_context['total_word_count']} words, {len(shared_context['common_abbreviations'])} abbreviations")
        return shared_context
    
    def _extract_common_abbreviations(self, text: str) -> List[str]:
        """Extract common abbreviations that appear across text"""
        import re
        # Find patterns like "Term (ABBR)" or standalone abbreviations
        abbrev_pattern = r'\b([A-Z]{2,6})\b'
        abbreviations = set(re.findall(abbrev_pattern, text))
        # Filter out common non-medical abbreviations
        filtered = [abbr for abbr in abbreviations if abbr not in {'PDF', 'URL', 'HTTP', 'HTML', 'XML'}]
        return list(filtered)
    
    def _extract_study_type_indicators(self, text: str) -> List[str]:
        """Extract indicators of study type"""
        indicators = []
        study_patterns = {
            'randomized': r'\b(randomized|randomised|rct)\b',
            'controlled': r'\b(controlled|control)\b',
            'trial': r'\b(trial|study)\b',
            'cohort': r'\b(cohort|longitudinal)\b',
            'cross_sectional': r'\b(cross.?sectional|survey)\b'
        }
        
        for study_type, pattern in study_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                indicators.append(study_type)
        
        return indicators
    
    def _extract_measurement_terms(self, text: str) -> List[str]:
        """Extract common measurement and outcome terms"""
        measurement_patterns = [
            r'\b(baseline|endpoint|outcome|measure)\b',
            r'\b(scale|score|rating|index)\b',
            r'\b(primary|secondary|tertiary)\b',
            r'\b(efficacy|effectiveness|safety)\b'
        ]
        
        measurements = set()
        for pattern in measurement_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            measurements.update(matches)
        
        return list(measurements)
    
    def _execute_parallel_picots(self, 
                                text_chunks: List[str],
                                filtered_picots: Dict[str, str],
                                extraction_engine,
                                base_prompt_template: str,
                                shared_context: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """
        Execute PICOTS sections in parallel using threading
        
        Note: True async would require async LLM clients. This uses threading for I/O concurrency.
        """
        import concurrent.futures
        import threading
        
        results = {}
        results_lock = threading.Lock()
        
        def process_section(section_name: str, section_content: str):
            """Process a single PICOTS section"""
            try:
                section_results = []
                
                # Generate section-specific prompt with optimizations
                section_prompt = self._create_optimized_section_prompt(
                    base_prompt_template, section_name, section_content, shared_context
                )
                
                # Process each chunk for this section
                for chunk_idx, text_chunk in enumerate(text_chunks, 1):
                    try:
                        chunk_result = extraction_engine.extract_from_chunk(
                            text_chunk, section_prompt, section_context=section_name
                        )
                        
                        if chunk_result:
                            chunk_result['section'] = section_name
                            chunk_result['chunk_index'] = chunk_idx
                            chunk_result['processing_mode'] = 'parallel'
                            section_results.append(chunk_result)
                            
                    except Exception as e:
                        logger.error(f"Error processing {section_name} chunk {chunk_idx}: {e}")
                        continue
                
                # Thread-safe result storage
                with results_lock:
                    results[section_name] = section_results
                    
                logger.info(f"Completed parallel processing for {section_name}: {len(section_results)} extractions")
                
            except Exception as e:
                logger.error(f"Error processing section {section_name}: {e}")
                with results_lock:
                    results[section_name] = []
        
        # Execute sections in parallel using ThreadPoolExecutor
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(6, len(filtered_picots))) as executor:
            futures = []
            
            for section_name, section_content in filtered_picots.items():
                future = executor.submit(process_section, section_name, section_content)
                futures.append(future)
            
            # Wait for all sections to complete
            concurrent.futures.wait(futures)
        
        logger.info(f"Parallel PICOTS processing completed for {len(results)} sections")
        return results
    
    def _execute_batched_picots(self,
                               text_chunks: List[str],
                               filtered_picots: Dict[str, str],
                               extraction_engine,
                               base_prompt_template: str,
                               shared_context: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """
        Execute PICOTS sections in intelligent batches
        """
        # Define compatible section batches
        section_batches = self._create_intelligent_batches(filtered_picots)
        results = {}
        
        for batch_idx, batch_sections in enumerate(section_batches, 1):
            logger.info(f"Processing batch {batch_idx}/{len(section_batches)}: {list(batch_sections.keys())}")
            
            # Create combined prompt for this batch
            batch_prompt = self._create_batched_prompt(
                base_prompt_template, batch_sections, shared_context
            )
            
            # Process each chunk with the batched prompt
            for chunk_idx, text_chunk in enumerate(text_chunks, 1):
                try:
                    chunk_result = extraction_engine.extract_from_chunk(
                        text_chunk, batch_prompt, section_context=f"batch_{batch_idx}"
                    )
                    
                    if chunk_result:
                        # Split results by section if possible
                        split_results = self._split_batch_results(chunk_result, batch_sections)
                        
                        for section_name, section_result in split_results.items():
                            if section_name not in results:
                                results[section_name] = []
                            
                            section_result['chunk_index'] = chunk_idx
                            section_result['processing_mode'] = 'batched'
                            section_result['batch_index'] = batch_idx
                            results[section_name].append(section_result)
                            
                except Exception as e:
                    logger.error(f"Error processing batch {batch_idx} chunk {chunk_idx}: {e}")
                    continue
        
        logger.info(f"Batched PICOTS processing completed for {len(results)} sections")
        return results
    
    def _execute_balanced_picots(self,
                                text_chunks: List[str],
                                filtered_picots: Dict[str, str],
                                extraction_engine,
                                base_prompt_template: str,
                                shared_context: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """
        Execute balanced approach: batch compatible sections, parallelize others
        """
        # Determine optimal strategy based on content
        if len(filtered_picots) <= 2:
            # Few sections: use parallel processing
            return self._execute_parallel_picots(
                text_chunks, filtered_picots, extraction_engine, base_prompt_template, shared_context
            )
        elif len(filtered_picots) >= 5:
            # Many sections: use batching
            return self._execute_batched_picots(
                text_chunks, filtered_picots, extraction_engine, base_prompt_template, shared_context
            )
        else:
            # Medium number: hybrid approach
            return self._execute_hybrid_picots(
                text_chunks, filtered_picots, extraction_engine, base_prompt_template, shared_context
            )
    
    def _execute_hybrid_picots(self,
                              text_chunks: List[str],
                              filtered_picots: Dict[str, str],
                              extraction_engine,
                              base_prompt_template: str,
                              shared_context: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """
        Execute hybrid approach: intelligent combination of batching and parallelization
        """
        # Analyze sections for optimal grouping
        high_priority_sections = ['Population', 'Intervention', 'Outcome']
        batch_sections = {}
        parallel_sections = {}
        
        for section_name, content in filtered_picots.items():
            if section_name in high_priority_sections:
                parallel_sections[section_name] = content
            else:
                batch_sections[section_name] = content
        
        results = {}
        
        # Process high-priority sections in parallel
        if parallel_sections:
            parallel_results = self._execute_parallel_picots(
                text_chunks, parallel_sections, extraction_engine, base_prompt_template, shared_context
            )
            results.update(parallel_results)
        
        # Process remaining sections in batches
        if batch_sections:
            batch_results = self._execute_batched_picots(
                text_chunks, batch_sections, extraction_engine, base_prompt_template, shared_context
            )
            results.update(batch_results)
        
        logger.info(f"Hybrid PICOTS processing completed: {len(parallel_sections)} parallel + {len(batch_sections)} batched")
        return results
    
    def _create_intelligent_batches(self, filtered_picots: Dict[str, str]) -> List[Dict[str, str]]:
        """
        Create intelligent batches of compatible PICOTS sections
        """
        # Define section compatibility matrix
        compatible_groups = [
            ['Population', 'Setting'],  # Often related context
            ['Intervention', 'Comparator'],  # Treatment comparisons
            ['Outcome', 'Timing']  # Measurement timing
        ]
        
        batches = []
        used_sections = set()
        
        # Create batches from compatible groups
        for group in compatible_groups:
            batch = {}
            for section in group:
                if section in filtered_picots and section not in used_sections:
                    batch[section] = filtered_picots[section]
                    used_sections.add(section)
            
            if batch:
                batches.append(batch)
        
        # Add remaining sections as individual batches
        for section_name, content in filtered_picots.items():
            if section_name not in used_sections:
                batches.append({section_name: content})
        
        return batches
    
    def _create_optimized_section_prompt(self,
                                       base_prompt: str,
                                       section_name: str,
                                       section_content: str,
                                       shared_context: Dict[str, Any]) -> str:
        """
        Create optimized prompt for a single section using shared context
        """
        # Get relevant domain mappings
        section_mappings = self._find_relevant_mappings(
            self.current_domain_profile['domain_map'] if self.current_domain_profile else {},
            self._extract_terms_from_text(section_content)
        )
        
        # Build optimized prompt with shared context
        optimization_info = f"""
Research Context: {shared_context.get('study_type_indicators', [])}
Common Terms: {', '.join(shared_context.get('common_abbreviations', [])[:5])}
"""
        
        mapping_section = ""
        if section_mappings:
            mapping_section = f"\nFor {section_name.lower()} extraction, consider these equivalent terms:\n"
            for canonical_term, synonyms in list(section_mappings.items())[:5]:  # Limit to 5 mappings
                if synonyms:
                    mapping_section += f"- '{canonical_term}' = {', '.join(synonyms[:2])}\n"
        
        optimized_prompt = f"""{base_prompt}
{optimization_info}
FOCUS: Extract {section_name.upper()} information specifically.
Target: {section_content}{mapping_section}

Extract all relevant {section_name.lower()} data using canonical terms where equivalent terms are found."""
        
        return optimized_prompt
    
    def _create_batched_prompt(self,
                              base_prompt: str,
                              batch_sections: Dict[str, str],
                              shared_context: Dict[str, Any]) -> str:
        """
        Create combined prompt for a batch of sections
        """
        section_instructions = []
        for section_name, content in batch_sections.items():
            section_instructions.append(f"**{section_name.upper()}**: {content}")
        
        batched_prompt = f"""{base_prompt}

Extract information for the following PICOTS sections:
{chr(10).join(section_instructions)}

Organize your response clearly by section. For each section found, extract the relevant data."""
        
        return batched_prompt
    
    def _split_batch_results(self, batch_result: Dict, batch_sections: Dict[str, str]) -> Dict[str, Dict]:
        """
        Split batched extraction results by section
        """
        # Simple implementation - in practice, would need more sophisticated parsing
        split_results = {}
        
        for section_name in batch_sections.keys():
            # Create a result entry for each section
            split_results[section_name] = {
                'extracted_data': batch_result.get('extracted_data', {}),
                'section': section_name,
                'confidence': batch_result.get('confidence', 0.0),
                'source': 'batched_extraction'
            }
        
        return split_results

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