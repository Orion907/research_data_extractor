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