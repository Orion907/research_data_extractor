# tests/test_data_validator_enhanced.py
"""
Tests for enhanced DataValidator comparison functionality
"""
import unittest
from src.utils.data_validator import DataValidator

class TestDataValidatorEnhanced(unittest.TestCase):
    """Test cases for enhanced DataValidator functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.validator = DataValidator()
        
        # Test data with various field name variations
        self.test_data = {
            "n": "75 patients",
            "age_years": "62.5 years", 
            "gender": "60% male, 40% female",
            "primary_outcome": "HbA1c reduction",
        }
        self.collision_test_data = {
            "study_population": "100 subjects"  # Test this separately
        }
    
    def test_field_normalization(self):
        """Test that field names get normalized correctly"""
        normalized = self.validator.normalize_fields(self.test_data)
        
        # Check expected mappings (no conflicts)
        self.assertEqual(normalized.get('sample_size'), "75 patients")
        self.assertEqual(normalized.get('mean_age'), "62.5 years") 
        self.assertEqual(normalized.get('gender_distribution'), "60% male, 40% female")
        
        # Test collision case separately
        collision_normalized = self.validator.normalize_fields(self.collision_test_data)
        self.assertEqual(collision_normalized.get('sample_size'), "100 subjects")
        
    def test_value_normalization(self):
        """Test that values get normalized for comparison"""
        # Test age value normalization
        age_normalized = self.validator._normalize_age_value("62.5 years")
        self.assertEqual(age_normalized, "62.5")
        
        # Test sample size normalization
        size_normalized = self.validator._normalize_sample_size_value("75 patients")
        self.assertEqual(size_normalized, "75")
        
        # Test percentage normalization
        pct_normalized = self.validator._normalize_percentage_value("60%")
        self.assertEqual(pct_normalized, "60")
    
    def test_prepare_for_comparison(self):
        """Test the complete comparison preparation pipeline"""
        comparison_ready = self.validator.prepare_for_comparison(self.test_data)
        
        # Should have normalized field names and values
        self.assertIn('sample_size', comparison_ready)
        self.assertIn('mean_age', comparison_ready)
        
        # Values should be cleaned (no units)
        self.assertEqual(comparison_ready['sample_size'], '75')  # From "n": "75 patients"
        self.assertEqual(comparison_ready['mean_age'], '62.5')   # From "age_years": "62.5 years"
        
    def test_no_duplicate_mappings(self):
        """Test that we don't have field mapping conflicts"""
        normalized1 = self.validator.normalize_fields({"age_years": "60"})
        normalized2 = self.validator.normalize_fields({"average_age": "60"})
        
        # Both should map to mean_age
        self.assertIn('mean_age', normalized1)
        self.assertIn('mean_age', normalized2)

if __name__ == '__main__':
    # Run the tests
    unittest.main()