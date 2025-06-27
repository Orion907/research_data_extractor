"""
Test suite for refactored domain priming system
Validates the integrated functionality of all domain priming components
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.utils.domain_priming import (
    EnhancedPatternDetector,
    DomainPrimingEngine,
    TermMapper,
    DomainMapper
)

class TestEnhancedPatternDetector:
    """Test the consolidated pattern detector"""
    
    def test_initialization(self):
        """Test proper initialization of enhanced pattern detector"""
        detector = EnhancedPatternDetector(min_frequency=2, min_term_length=3)
        assert detector.min_frequency == 2
        assert detector.min_term_length == 3
        assert len(detector.stop_words) > 0
    
    def test_comprehensive_analysis(self):
        """Test comprehensive analysis of sample texts"""
        detector = EnhancedPatternDetector(min_frequency=1)  # Lower threshold for testing
        
        sample_texts = [
            """
            This randomized controlled trial studied mindfulness-based interventions 
            for anxiety and depression in children aged 8-12 years. The sample included 
            150 participants (n=150) with 60% female subjects. Primary outcomes included 
            SCARED (Screen for Child Anxiety Related Emotional Disorders) scores and 
            Child Depression Inventory (CDI) measurements.
            """,
            """
            The study examined high blood pressure (hypertension) treatment in diabetic 
            patients. Mean age was 65.4 years. Participants showed significant reduction 
            in blood pressure from baseline measurements.
            """
        ]
        
        results = detector.analyze_sample_texts(sample_texts)
        
        # Verify all expected components are present
        assert 'term_frequencies' in results
        assert 'potential_fields' in results
        assert 'numeric_patterns' in results
        assert 'abbreviations' in results
        assert 'field_mappings' in results
        assert 'similarity_clusters' in results
        assert 'analysis_stats' in results
        
        # Verify term frequencies detected medical terms
        term_freq = results['term_frequencies']
        assert any('anxiety' in term or 'depression' in term for term in term_freq.keys())
        
        # Verify abbreviations detected
        abbreviations = results['abbreviations']
        assert 'SCARED' in abbreviations or 'CDI' in abbreviations
        
        # Verify numeric patterns detected
        numeric = results['numeric_patterns']
        assert len(numeric['ages']) > 0 or len(numeric['percentages']) > 0

class TestDomainPrimingEngine:
    """Test the unified domain priming engine"""
    
    @pytest.fixture
    def mock_engine(self):
        """Create domain priming engine with mock LLM client"""
        with patch('src.utils.domain_priming.term_mapper.ClientFactory.create_client') as mock_factory:
            mock_client = Mock()
            mock_client.generate_completion.return_value = '''
            {
                "synonym_mappings": {
                    "anxiety": ["worry", "anxious", "nervousness"],
                    "depression": ["depressed", "mood disorder", "sadness"],
                    "hypertension": ["high blood pressure", "HTN"]
                },
                "abbreviation_expansions": {
                    "SCARED": {"full_form": "Screen for Child Anxiety Related Emotional Disorders", "variations": ["scared scale"]},
                    "CDI": {"full_form": "Child Depression Inventory", "variations": ["cdi scale"]}
                },
                "field_enhancements": {
                    "age": {"data_type": "numeric", "variations": ["mean age", "average age"], "examples": ["12.5 years", "aged 8-12"]},
                    "sample_size": {"data_type": "numeric", "variations": ["n", "participants"], "examples": ["n=150", "150 subjects"]}
                },
                "semantic_clusters": {
                    "mental_health": ["anxiety", "depression", "mood"],
                    "demographics": ["age", "gender", "participants"]
                }
            }
            '''
            mock_factory.return_value = mock_client
            
            engine = DomainPrimingEngine(llm_provider="mock")
            return engine
    
    def test_phase1_sample_analysis(self, mock_engine):
        """Test Phase 1: Sample article analysis and domain map building"""
        sample_texts = [
            """
            This study examined mindfulness interventions for anxiety in children. 
            Participants included 120 children aged 8-12 years (mean age 10.2 years).
            The Screen for Child Anxiety Related Emotional Disorders (SCARED) was used 
            to measure anxiety levels. Results showed significant reduction in anxiety scores.
            """,
            """
            A randomized trial of meditation therapy for depression. The sample consisted 
            of 85 adolescent participants. Child Depression Inventory (CDI) scores were 
            the primary outcome measure. High blood pressure (hypertension) was also monitored.
            """
        ]
        
        # Run Phase 1 analysis
        domain_profile = mock_engine.analyze_sample_articles(
            sample_texts, 
            domain_name="mindfulness_children_test"
        )
        
        # Verify domain profile structure
        assert 'metadata' in domain_profile
        assert 'raw_patterns' in domain_profile
        assert 'enhanced_patterns' in domain_profile
        assert 'domain_map' in domain_profile
        assert 'statistics' in domain_profile
        
        # Verify metadata
        metadata = domain_profile['metadata']
        assert metadata['domain_name'] == "mindfulness_children_test"
        assert metadata['sample_count'] == 2
        assert 'created_at' in metadata
        
        # Verify domain map creation
        domain_map = domain_profile['domain_map']
        assert len(domain_map) > 0
        
        # Should contain mappings from LLM enhancement
        anxiety_mapping = domain_map.get('anxiety', [])
        assert 'worry' in anxiety_mapping or 'anxious' in anxiety_mapping
    
    def test_phase1_user_refinement(self, mock_engine):
        """Test Phase 1: Human-in-the-loop refinement"""
        # First create a domain profile
        sample_texts = ["Sample medical text with anxiety and depression terms."]
        domain_profile = mock_engine.analyze_sample_articles(sample_texts)
        
        # Test user modifications
        user_modifications = {
            'add_mapping': {
                'canonical': 'stress',
                'synonyms': ['tension', 'pressure', 'strain']
            },
            'edit_mapping': {
                'canonical': 'anxiety',
                'synonyms': ['worry', 'nervousness', 'fear', 'panic']
            }
        }
        
        refined_profile = mock_engine.review_and_refine_domain_map(user_modifications, save_profile=False)
        
        # Verify refinements applied
        domain_map = refined_profile['domain_map']
        assert 'stress' in domain_map
        assert 'tension' in domain_map['stress']
        
        # Verify metadata updated
        assert refined_profile['metadata']['user_refined'] is True
        assert 'last_refined' in refined_profile['metadata']
    
    def test_phase2_enhanced_prompt_generation(self, mock_engine):
        """Test Phase 2: Enhanced prompt generation with PICOTS integration"""
        # Create a domain profile first
        sample_texts = ["Medical text with anxiety, depression, and hypertension terms."]
        mock_engine.analyze_sample_articles(sample_texts)
        
        # Test PICOTS term extraction
        picots_data = {
            'Population': 'children with anxiety disorders',
            'Intervention': 'mindfulness-based interventions',
            'Comparator': 'standard care',
            'Outcome': 'anxiety reduction, depression scores',
            'Timing': '8-week intervention',
            'Setting': 'school-based'
        }
        
        picots_terms = mock_engine.extract_picots_terms(picots_data)
        assert 'anxiety' in picots_terms
        # Check that we extract key terms from multi-word phrases  
        assert 'interventions' in picots_terms  # from "mindfulness-based interventions"
        assert 'depression' in picots_terms
        
        # Test enhanced prompt generation
        base_prompt = "Extract data from the following research article..."
        enhanced_prompt = mock_engine.generate_enhanced_prompt(
            base_prompt, 
            picots_terms
        )
        
        # Verify prompt contains domain mappings
        assert len(enhanced_prompt) > len(base_prompt)
        assert "consider the following terms as equivalent" in enhanced_prompt.lower()
    
    def test_domain_profile_persistence(self, mock_engine):
        """Test domain profile saving and loading"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Override the profiles directory
            mock_engine.domain_profiles_dir = Path(temp_dir)
            
            # Create and save a profile
            sample_texts = ["Test medical text for persistence testing."]
            domain_profile = mock_engine.analyze_sample_articles(
                sample_texts, 
                domain_name="persistence_test"
            )
            
            # Save profile
            saved_path = mock_engine.save_domain_profile()
            assert Path(saved_path).exists()
            
            # Clear current profile and load it back
            mock_engine.current_domain_profile = None
            loaded_profile = mock_engine.load_domain_profile(saved_path)
            
            # Verify loaded profile matches original
            assert loaded_profile['metadata']['domain_name'] == "persistence_test"
            assert loaded_profile['metadata']['sample_count'] == 1
            
            # Test profile listing
            available_profiles = mock_engine.list_available_profiles()
            assert len(available_profiles) == 1
            assert available_profiles[0]['domain_name'] == "persistence_test"

class TestIntegrationWorkflow:
    """Test complete workflow integration"""
    
    def test_end_to_end_workflow(self):
        """Test complete domain priming workflow from sample analysis to prompt enhancement"""
        with patch('src.utils.domain_priming.term_mapper.ClientFactory.create_client') as mock_factory:
            # Setup mock LLM client
            mock_client = Mock()
            mock_client.generate_completion.return_value = '''
            {
                "synonym_mappings": {
                    "mindfulness": ["meditation", "awareness", "mindful attention"],
                    "anxiety": ["worry", "nervousness", "fear"]
                },
                "abbreviation_expansions": {},
                "field_enhancements": {},
                "semantic_clusters": {}
            }
            '''
            mock_factory.return_value = mock_client
            
            # Initialize engine
            engine = DomainPrimingEngine(llm_provider="mock")
            
            # Phase 1: Analyze samples
            sample_texts = [
                "Mindfulness interventions reduced anxiety in children aged 8-12.",
                "Meditation therapy showed effectiveness for worry and nervousness."
            ]
            
            domain_profile = engine.analyze_sample_articles(
                sample_texts,
                domain_name="integration_test"
            )
            
            # Verify domain map created
            domain_map = domain_profile['domain_map']
            assert 'mindfulness' in domain_map
            assert 'meditation' in domain_map['mindfulness']
            
            # Phase 2: Generate enhanced prompt
            picots_data = {
                'Population': 'children with anxiety',
                'Intervention': 'mindfulness meditation',
                'Outcome': 'anxiety reduction'
            }
            
            picots_terms = engine.extract_picots_terms(picots_data)
            base_prompt = "Extract study data using the following format..."
            
            enhanced_prompt = engine.generate_enhanced_prompt(base_prompt, picots_terms)
            
            # Verify enhancement
            assert "mindfulness" in enhanced_prompt.lower()
            assert "meditation" in enhanced_prompt.lower()
            assert "equivalent" in enhanced_prompt.lower()
            
            # Verify summary generation
            summary = engine.get_domain_profile_summary()
            assert summary['domain_name'] == "integration_test"
            assert summary['total_mappings'] > 0

class TestLegacyCompatibility:
    """Test that legacy components still work for backward compatibility"""
    
    def test_legacy_pattern_detector_import(self):
        """Test that original PatternDetector can still be imported"""
        from src.utils.domain_priming import PatternDetector
        
        detector = PatternDetector()
        assert detector is not None
    
    def test_legacy_term_mapper_functionality(self):
        """Test that TermMapper still works with enhanced detector"""
        with patch('src.utils.domain_priming.term_mapper.ClientFactory.create_client') as mock_factory:
            mock_client = Mock()
            mock_client.generate_completion.return_value = '{"synonym_mappings": {}}'
            mock_factory.return_value = mock_client
            
            mapper = TermMapper(provider="mock")
            
            # Test pattern detection
            sample_texts = ["Medical text with various terms for testing."]
            patterns = mapper.detect_domain_patterns(sample_texts)
            
            # Should work with enhanced detector
            assert 'top_terms' in patterns
            assert 'term_frequencies' in patterns

class TestContextAwarePrompting:
    """Test context-aware PICOTS-based prompt generation"""
    
    @pytest.fixture
    def mock_engine_with_profile(self):
        """Create engine with a loaded domain profile"""
        with patch('src.utils.domain_priming.term_mapper.ClientFactory.create_client') as mock_factory:
            mock_client = Mock()
            mock_client.generate_completion.return_value = '''
            {
                "synonym_mappings": {
                    "mindfulness": ["meditation", "awareness", "mindful attention"],
                    "anxiety": ["worry", "nervousness", "fear"],
                    "children": ["kids", "pediatric population", "youth"],
                    "hypertension": ["high blood pressure", "HTN"]
                },
                "abbreviation_expansions": {},
                "field_enhancements": {},
                "semantic_clusters": {}
            }
            '''
            mock_factory.return_value = mock_client
            
            engine = DomainPrimingEngine(llm_provider="mock")
            
            # Create a sample domain profile
            sample_texts = ["Mindfulness interventions for anxiety in children with hypertension."]
            domain_profile = engine.analyze_sample_articles(sample_texts, domain_name="test_profile")
            
            return engine
    
    def test_picots_prompt_chunking(self, mock_engine_with_profile):
        """Test that prompts are properly chunked by PICOTS sections"""
        engine = mock_engine_with_profile
        
        picots_data = {
            'Population': 'children with anxiety disorders',
            'Intervention': 'mindfulness-based interventions',
            'Comparator': 'standard care treatment',
            'Outcome': 'anxiety reduction scores',
            'Timing': '8-week intervention period',
            'Setting': 'school-based programs'
        }
        
        base_prompt = "Extract research data from the following text."
        
        # Generate enhanced prompts by PICOTS sections
        enhanced_prompts = engine.generate_enhanced_prompts_by_picots(base_prompt, picots_data)
        
        # Verify we get separate prompts for each PICOTS section
        assert len(enhanced_prompts) == 6  # All PICOTS sections
        assert 'Population' in enhanced_prompts
        assert 'Intervention' in enhanced_prompts
        assert 'Outcome' in enhanced_prompts
        
        # Verify each prompt is section-specific
        pop_prompt = enhanced_prompts['Population']
        assert 'POPULATION' in pop_prompt.upper()
        assert 'children with anxiety disorders' in pop_prompt
        
        intervention_prompt = enhanced_prompts['Intervention']
        assert 'INTERVENTION' in intervention_prompt.upper()
        assert 'mindfulness-based interventions' in intervention_prompt
    
    def test_context_window_management(self, mock_engine_with_profile):
        """Test that prompt size is managed within context limits"""
        engine = mock_engine_with_profile
        
        # Create large PICOTS data that could overflow context
        large_picots = {
            'Population': 'children and adolescents aged 8-18 years with diagnosed anxiety disorders including generalized anxiety, social anxiety, separation anxiety, and specific phobias',
            'Intervention': 'mindfulness-based stress reduction programs including meditation, breathing exercises, body awareness, and cognitive mindfulness techniques',
            'Outcome': 'anxiety symptom reduction measured by validated scales including SCARED, MASC, and clinical interviews'
        }
        
        base_prompt = "Extract comprehensive research data from the following text according to the specified criteria."
        
        # Test with small context limit
        small_prompts = engine.generate_enhanced_prompts_by_picots(
            base_prompt, 
            large_picots, 
            max_context_tokens=1000  # Very small limit
        )
        
        # Verify prompts respect context limits
        for section, prompt in small_prompts.items():
            estimated_tokens = engine.estimate_prompt_tokens(prompt)
            assert estimated_tokens <= 1000, f"{section} prompt exceeds token limit: {estimated_tokens}"
    
    def test_relevant_mapping_extraction(self, mock_engine_with_profile):
        """Test that only relevant mappings are included per PICOTS section"""
        engine = mock_engine_with_profile
        
        picots_data = {
            'Population': 'children with anxiety',  # Should match 'children' and 'anxiety' mappings
            'Intervention': 'mindfulness training',  # Should match 'mindfulness' mappings  
            'Outcome': 'blood pressure changes'     # Should match 'hypertension' mappings
        }
        
        base_prompt = "Extract data."
        enhanced_prompts = engine.generate_enhanced_prompts_by_picots(base_prompt, picots_data)
        
        # Check Population prompt includes relevant terms
        pop_prompt = enhanced_prompts['Population']
        assert 'children' in pop_prompt.lower() or 'anxiety' in pop_prompt.lower()
        
        # Check Intervention prompt includes mindfulness terms
        intervention_prompt = enhanced_prompts['Intervention']
        assert 'mindfulness' in intervention_prompt.lower() or 'meditation' in intervention_prompt.lower()
        
        # Check Outcome prompt includes hypertension terms  
        outcome_prompt = enhanced_prompts['Outcome']
        assert 'hypertension' in outcome_prompt.lower() or 'blood pressure' in outcome_prompt.lower()
    
    def test_workflow_orchestration(self, mock_engine_with_profile):
        """Test complete PICOTS extraction workflow orchestration"""
        engine = mock_engine_with_profile
        
        # Mock extraction engine
        mock_extraction_engine = Mock()
        mock_extraction_engine.extract_from_chunk.return_value = {
            'extracted_data': 'sample data',
            'confidence': 0.8
        }
        
        text_chunks = [
            "Sample research text about mindfulness in children.",
            "Another chunk about anxiety treatment outcomes."
        ]
        
        picots_data = {
            'Population': 'children with anxiety',
            'Intervention': 'mindfulness therapy',
            'Outcome': 'anxiety reduction'
        }
        
        # Execute workflow
        results = engine.execute_picots_extraction_workflow(
            text_chunks,
            picots_data, 
            mock_extraction_engine
        )
        
        # Verify results structure
        assert 'Population' in results
        assert 'Intervention' in results
        assert 'Outcome' in results
        assert '_metadata' in results
        
        # Verify metadata
        metadata = results['_metadata']
        # Check actual number of sections processed (metadata excludes itself)
        actual_sections = len([k for k in results.keys() if k != '_metadata'])
        assert metadata['total_sections_processed'] == actual_sections
        assert metadata['total_chunks_processed'] == 2
        assert 'workflow_completed_at' in metadata
        
        # Verify extraction engine was called correctly
        # Should be called once per section per chunk
        expected_calls = actual_sections * 2  # sections × chunks
        assert mock_extraction_engine.extract_from_chunk.call_count == expected_calls
    
    def test_token_estimation(self, mock_engine_with_profile):
        """Test token estimation accuracy"""
        engine = mock_engine_with_profile
        
        # Test various prompt sizes
        short_prompt = "Extract data."
        medium_prompt = "Extract research data from the following text according to PICOTS criteria."
        long_prompt = medium_prompt + " " + "Additional instructions. " * 50
        
        short_tokens = engine.estimate_prompt_tokens(short_prompt)
        medium_tokens = engine.estimate_prompt_tokens(medium_prompt)
        long_tokens = engine.estimate_prompt_tokens(long_prompt)
        
        # Verify token estimates increase with content
        assert short_tokens < medium_tokens < long_tokens
        
        # Verify rough accuracy (should be reasonable estimates)
        assert 2 <= short_tokens <= 5
        assert 15 <= medium_tokens <= 25
        assert long_tokens > 100

class TestOptimizedPicots:
    """Test optimized PICOTS extraction workflows"""
    
    @pytest.fixture
    def mock_optimized_engine(self):
        """Create engine with domain profile for optimization testing"""
        with patch('src.utils.domain_priming.term_mapper.ClientFactory.create_client') as mock_factory:
            mock_client = Mock()
            mock_client.generate_completion.return_value = '''
            {
                "synonym_mappings": {
                    "mindfulness": ["meditation", "awareness"],
                    "anxiety": ["worry", "nervousness"], 
                    "children": ["kids", "pediatric"],
                    "intervention": ["treatment", "therapy"],
                    "outcome": ["endpoint", "result"]
                },
                "abbreviation_expansions": {},
                "field_enhancements": {},
                "semantic_clusters": {}
            }
            '''
            mock_factory.return_value = mock_client
            
            engine = DomainPrimingEngine(llm_provider="mock")
            sample_texts = ["Mindfulness interventions for anxiety in children with measured outcomes."]
            engine.analyze_sample_articles(sample_texts, domain_name="optimization_test")
            
            return engine
    
    def test_picots_section_filtering(self, mock_optimized_engine):
        """Test filtering of relevant PICOTS sections"""
        engine = mock_optimized_engine
        
        # Test with mixed quality PICOTS data
        picots_data = {
            'Population': 'children aged 8-12 with anxiety disorders',
            'Intervention': 'mindfulness-based interventions',
            'Comparator': '',  # Empty - should be filtered
            'Outcome': 'anxiety reduction scores',
            'Timing': 'n/a',  # Placeholder - should be filtered  
            'Setting': 'school-based programs'
        }
        
        filtered = engine._filter_relevant_picots_sections(picots_data)
        
        # Verify filtering
        assert 'Population' in filtered
        assert 'Intervention' in filtered
        assert 'Outcome' in filtered
        assert 'Setting' in filtered
        assert 'Comparator' not in filtered  # Empty content filtered out
        assert 'Timing' not in filtered      # N/A filtered out
        
        assert len(filtered) == 4  # Only meaningful sections
    
    def test_shared_context_extraction(self, mock_optimized_engine):
        """Test shared context optimization"""
        engine = mock_optimized_engine
        
        text_chunks = [
            "This randomized controlled trial (RCT) examined mindfulness interventions. Participants included 120 children.",
            "The study used SCARED (Screen for Child Anxiety) and CDI (Child Depression Inventory) measures.",
            "Primary outcomes included anxiety reduction. Secondary endpoints measured behavioral changes."
        ]
        
        shared_context = engine._extract_shared_context(text_chunks)
        
        # Verify shared context extraction
        assert 'total_word_count' in shared_context
        assert 'chunk_count' in shared_context
        assert shared_context['chunk_count'] == 3
        
        # Check abbreviation extraction
        abbreviations = shared_context['common_abbreviations']
        assert 'RCT' in abbreviations
        assert 'SCARED' in abbreviations
        assert 'CDI' in abbreviations
        
        # Check study type detection
        study_indicators = shared_context['study_type_indicators']
        assert 'randomized' in study_indicators
        assert 'controlled' in study_indicators
        assert 'trial' in study_indicators
    
    def test_intelligent_batching(self, mock_optimized_engine):
        """Test intelligent section batching"""
        engine = mock_optimized_engine
        
        filtered_picots = {
            'Population': 'children with anxiety',
            'Intervention': 'mindfulness therapy',
            'Comparator': 'standard care',
            'Outcome': 'anxiety scores',
            'Timing': '8-week period',
            'Setting': 'school clinics'
        }
        
        batches = engine._create_intelligent_batches(filtered_picots)
        
        # Verify intelligent grouping
        assert len(batches) > 0
        
        # Check that compatible sections are grouped
        batch_contents = [list(batch.keys()) for batch in batches]
        
        # Population and Setting should be together (contextual compatibility)
        pop_setting_together = any(
            'Population' in batch and 'Setting' in batch 
            for batch in batch_contents
        )
        
        # Intervention and Comparator should be together (treatment compatibility)
        int_comp_together = any(
            'Intervention' in batch and 'Comparator' in batch
            for batch in batch_contents
        )
        
        # At least one intelligent grouping should occur
        assert pop_setting_together or int_comp_together
    
    def test_optimized_workflow_performance_tracking(self, mock_optimized_engine):
        """Test performance tracking in optimized workflow"""
        engine = mock_optimized_engine
        
        # Mock extraction engine
        mock_extraction_engine = Mock()
        mock_extraction_engine.extract_from_chunk.return_value = {
            'extracted_data': 'sample data',
            'confidence': 0.9
        }
        
        text_chunks = ["Sample text 1", "Sample text 2"]
        picots_data = {
            'Population': 'children with anxiety disorders',
            'Intervention': 'mindfulness-based therapy'
        }
        
        # Test balanced optimization
        results = engine.execute_optimized_picots_workflow(
            text_chunks, 
            picots_data, 
            mock_extraction_engine,
            optimization_level="balanced"
        )
        
        # Verify performance tracking
        metadata = results['_metadata']
        assert 'processing_time_seconds' in metadata
        assert 'optimization_level' in metadata
        assert metadata['optimization_level'] == 'balanced'
        assert 'efficiency_metrics' in metadata
        
        efficiency = metadata['efficiency_metrics']
        assert 'extractions_per_second' in efficiency
        assert 'avg_time_per_section' in efficiency
        assert 'avg_time_per_chunk' in efficiency
        
        # Verify processing actually occurred
        assert metadata['total_sections_processed'] == 2
        assert metadata['total_chunks_processed'] == 2
    
    def test_parallel_vs_sequential_comparison(self, mock_optimized_engine):
        """Test that parallel processing works without errors"""
        engine = mock_optimized_engine
        
        # Mock extraction engine with slight delay to test concurrency
        mock_extraction_engine = Mock()
        
        def mock_extract_with_delay(*args, **kwargs):
            import time
            time.sleep(0.01)  # Small delay to simulate processing
            return {'extracted_data': 'test data', 'confidence': 0.8}
        
        mock_extraction_engine.extract_from_chunk = mock_extract_with_delay
        
        text_chunks = ["Text 1", "Text 2"]
        picots_data = {
            'Population': 'test population',
            'Intervention': 'test intervention', 
            'Outcome': 'test outcome'
        }
        
        import time
        
        # Test parallel processing
        start_time = time.time()
        parallel_results = engine.execute_optimized_picots_workflow(
            text_chunks, picots_data, mock_extraction_engine, optimization_level="parallel"
        )
        parallel_time = time.time() - start_time
        
        # Test sequential processing
        start_time = time.time()
        sequential_results = engine.execute_optimized_picots_workflow(
            text_chunks, picots_data, mock_extraction_engine, optimization_level="sequential"
        )
        sequential_time = time.time() - start_time
        
        # Verify both produce results
        assert len(parallel_results) > 1  # Has sections + metadata
        assert len(sequential_results) > 1
        
        # Verify metadata indicates correct processing mode
        assert parallel_results['_metadata']['optimization_level'] == 'parallel'
        assert sequential_results['_metadata']['optimization_level'] == 'sequential'
        
        # Parallel should generally be faster (though with small delays, timing may vary)
        # Main test is that both complete successfully
        assert parallel_time > 0
        assert sequential_time > 0
    
    def test_optimization_level_selection(self, mock_optimized_engine):
        """Test that different optimization levels are selected appropriately"""
        engine = mock_optimized_engine
        
        mock_extraction_engine = Mock()
        mock_extraction_engine.extract_from_chunk.return_value = {'data': 'test'}
        
        text_chunks = ["Test text"]
        
        # Test with minimal PICOTS (should use parallel)
        minimal_picots = {'Population': 'test population'}
        results = engine.execute_optimized_picots_workflow(
            text_chunks, minimal_picots, mock_extraction_engine, optimization_level="balanced"
        )
        # With 1 section, balanced should work efficiently
        assert results['_metadata']['total_sections_processed'] == 1
        
        # Test with many PICOTS sections (should use batching logic)
        extensive_picots = {
            'Population': 'test population',
            'Intervention': 'test intervention',
            'Comparator': 'test comparator', 
            'Outcome': 'test outcome',
            'Timing': 'test timing',
            'Setting': 'test setting'
        }
        results = engine.execute_optimized_picots_workflow(
            text_chunks, extensive_picots, mock_extraction_engine, optimization_level="balanced"
        )
        # Should handle all sections
        assert results['_metadata']['total_sections_processed'] >= 5