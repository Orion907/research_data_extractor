# tests/test_data_validator.py
"""
Test module for data validation functionality
"""
import os
import sys
import unittest

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from src.utils.data_validator import DataValidator

class TestDataValidator(unittest.TestCase):
    """Test cases for data validation functionality"""
    
    def setUp(self):
        """Set up for tests"""
        self.validator = DataValidator()
        
        # Sample data for testing
        self.valid_data = {
            'sample_size': 150,
            'mean_age': 58.3,
            'age_range': '45-70 years',
            'male_percentage': 60,
            'female_percentage': 40,
            'inclusion_criteria': [
                'HbA1c > 7.5%',
                'BMI > 25 kg/m²'
            ],
            'exclusion_criteria': [
                'pregnancy',
                'severe renal impairment',
                'active cancer treatment'
            ]
        }
        
        self.invalid_data = {
            'sample_size': 'about one hundred and fifty',
            'mean_age': 'fifty-eight point three',
            'male_percentage': 60,
            'female_percentage': 50,  # Note: adds up to 110%
        }
        
        self.string_format_data = {
            'sample_size': '150 patients',
            'mean_age': '58.3 years',
            'male_percentage': '60%',
            'inclusion_criteria': 'HbA1c > 7.5%, BMI > 25 kg/m²'
        }
    
    def test_validate_valid_data(self):
        """Test validation with valid data"""
        result = self.validator.validate(self.valid_data)
        self.assertTrue(result['valid'])
        self.assertEqual(len(result['errors']), 0)
        self.assertEqual(result['cleaned_data']['sample_size'], 150)
    
    def test_validate_invalid_data(self):
        """Test validation with invalid data"""
        result = self.validator.validate(self.invalid_data)
        # Should still be valid because no required fields are missing
        self.assertTrue(result['valid'])
        # But should have warnings
        self.assertTrue(len(result['warnings']) > 0)
        
        # Check consistency warning about percentages
        consistency_warning = [w for w in result['warnings'] if 'percentages add up to' in w]
        self.assertTrue(len(consistency_warning) > 0)
    
    def test_validate_string_format_data(self):
        """Test validation with string formatted data"""
        result = self.validator.validate(self.string_format_data)
        self.assertTrue(result['valid'])
        
        # Check type conversions
        self.assertEqual(result['cleaned_data']['sample_size'], 150)
        self.assertEqual(result['cleaned_data']['mean_age'], 58.3)
        self.assertEqual(result['cleaned_data']['male_percentage'], 60)
        
        # Check list conversion
        self.assertIsInstance(result['cleaned_data']['inclusion_criteria'], list)
        self.assertEqual(len(result['cleaned_data']['inclusion_criteria']), 2)
    
    def test_field_normalization(self):
        """Test field name normalization"""
        test_data = {
            'n': 100,
            'age_mean': 65,
            'gender': 'male: 55%, female: 45%'
        }
        
        normalized = self.validator.normalize_fields(test_data)
        
        # Check normalized field names
        self.assertIn('sample_size', normalized)
        self.assertIn('mean_age', normalized)
        self.assertIn('gender_distribution', normalized)
        
        # Check values are preserved
        self.assertEqual(normalized['sample_size'], 100)
        self.assertEqual(normalized['mean_age'], 65)
        self.assertEqual(normalized['gender_distribution'], 'male: 55%, female: 45%')
    
    def test_empty_data(self):
        """Test validation with empty data"""
        result = self.validator.validate({})
        self.assertFalse(result['valid'])
        self.assertTrue(len(result['errors']) > 0)
    
    def test_integer_field_validation(self):
        """Test validation of integer fields"""
        test_data = {'sample_size': '50 patients enrolled'}
        result = self.validator.validate(test_data)
        self.assertTrue(result['valid'])
        self.assertEqual(result['cleaned_data']['sample_size'], 50)
    
    def test_percentage_field_validation(self):
        """Test validation of percentage fields"""
        test_cases = [
            {'male_percentage': '60%', 'expected': 60},
            {'male_percentage': '60 percent', 'expected': 60},
            {'male_percentage': 60, 'expected': 60},
            {'male_percentage': 60.5, 'expected': 60.5},
        ]
        
        for case in test_cases:
            data = {'male_percentage': case['male_percentage']}
            result = self.validator.validate(data)
            self.assertTrue(result['valid'])
            self.assertEqual(result['cleaned_data']['male_percentage'], case['expected'])
    
    def test_list_field_validation(self):
        """Test validation of list fields"""
        test_cases = [
            {'inclusion_criteria': ['A', 'B', 'C'], 'expected_len': 3},
            {'inclusion_criteria': 'A, B, C', 'expected_len': 3},
            {'inclusion_criteria': 'A\nB\nC', 'expected_len': 3},
            {'inclusion_criteria': '["A", "B", "C"]', 'expected_len': 3},
        ]
        
        for case in test_cases:
            data = {'inclusion_criteria': case['inclusion_criteria']}
            result = self.validator.validate(data)
            self.assertTrue(result['valid'])
            self.assertEqual(len(result['cleaned_data']['inclusion_criteria']), case['expected_len'])

if __name__ == '__main__':
    unittest.main()