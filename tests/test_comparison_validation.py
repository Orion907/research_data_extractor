"""
Test script for validating enhanced comparison functionality with synthetic data
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.annotation_utils import compare_extractions
import json

def create_synthetic_test_data():
    """
    Create realistic synthetic test data pairs to validate comparison enhancements
    """
    # Scenario 1: Field name variations and case differences
    auto_extraction_1 = {
        "Sample_Size": "75 patients",
        "mean_age": "62.5 years", 
        "Gender": "60% Male, 40% Female",
        "condition": "Type 2 Diabetes",
        "HbA1c": "8.3% ± 0.9%"
    }
    
    manual_extraction_1 = {
        "n": "75",  # Same as Sample_Size but different field name
        "average_age": "62.5",  # Same as mean_age, no units
        "gender": "60% male, 40% female",  # Case difference
        "condition": "type 2 diabetes",  # Case difference
        "hba1c": "8.3% ± 0.9%"  # Case difference in field name
    }
    
    # Scenario 2: Value format differences
    auto_extraction_2 = {
        "sample_size": "150 subjects",
        "age_range": "45-70 years",
        "inclusion_criteria": ["HbA1c > 7.5%", "BMI > 25 kg/m²"],
        "study_duration": "12 weeks"
    }
    
    manual_extraction_2 = {
        "sample_size": "150",  # No "subjects" text
        "age_range": "45-70",  # No "years" text
        "inclusion_criteria": ["HbA1c > 7.5%", "BMI > 25"],  # Partial unit difference
        "study_duration": "12 weeks",  # Identical
        "location": "Multiple centers"  # Only in manual
    }
    
    # Scenario 3: Genuine differences (should be detected)
    auto_extraction_3 = {
        "sample_size": "100 patients",
        "mean_age": "55.2 years",
        "primary_endpoint": "HbA1c reduction"
    }
    
    manual_extraction_3 = {
        "sample_size": "120 patients",  # Different value
        "mean_age": "58.7 years",  # Different value  
        "primary_endpoint": "Blood glucose control"  # Different value
    }
    
    return [
        (auto_extraction_1, manual_extraction_1, "Field name and case variations"),
        (auto_extraction_2, manual_extraction_2, "Value format differences"),
        (auto_extraction_3, manual_extraction_3, "Genuine differences")
    ]

def print_transformation_details(transformation_log):
    """
    Print transformation details in a readable format
    """
    if transformation_log.get("auto_transformations"):
        print("  🤖 Auto Data Transformations:")
        for transform in transformation_log["auto_transformations"]:
            print(f"    {transform}")
    
    if transformation_log.get("manual_transformations"):
        print("  ✋ Manual Data Transformations:")
        for transform in transformation_log["manual_transformations"]:
            print(f"    {transform}")

def run_comparison_tests():
    """
    Run comparison tests with synthetic data using the existing enhanced system
    """
    print("🧪 Testing Enhanced Comparison System with Synthetic Data")
    print("=" * 60)
    
    test_scenarios = create_synthetic_test_data()
    
    for i, (auto_data, manual_data, description) in enumerate(test_scenarios, 1):
        print(f"\n📋 Test Scenario {i}: {description}")
        print("-" * 40)
        
        # Show input data
        print("🤖 Automatic Extraction:")
        for key, value in auto_data.items():
            print(f"  {key}: {value}")
            
        print("\n✋ Manual Extraction:")
        for key, value in manual_data.items():
            print(f"  {key}: {value}")
        
        # Run comparison with your existing enhanced function
        print("\n🔍 Comparison Results:")
        try:
            comparison = compare_extractions(auto_data, manual_data)
            
            # Display metrics
            metrics = comparison.get("metrics", {})
            print(f"  📊 Precision: {metrics.get('precision', 0):.3f}")
            print(f"  📊 Recall: {metrics.get('recall', 0):.3f}")
            print(f"  📊 F1 Score: {metrics.get('f1_score', 0):.3f}")
            print(f"  ✅ True Positives: {metrics.get('true_positives', 0)}")
            print(f"  ❌ False Positives: {metrics.get('false_positives', 0)}")
            print(f"  ❌ False Negatives: {metrics.get('false_negatives', 0)}")
            
            # Display transformation details
            if "transformation_log" in comparison:
                print("\n🔧 Data Transformations Applied:")
                print_transformation_details(comparison["transformation_log"])
            
            # Display differences
            differences = comparison.get("differences", {})
            
            if differences.get("different_values"):
                print(f"\n🔄 Different Values ({len(differences['different_values'])}):")
                for field, vals in differences["different_values"].items():
                    print(f"    {field}: '{vals['auto']}' ≠ '{vals['manual']}'")
            
            if differences.get("only_in_auto"):
                print(f"\n➕ Only in Auto ({len(differences['only_in_auto'])}):")
                for field, value in differences["only_in_auto"].items():
                    print(f"    {field}: {value}")
                
            if differences.get("only_in_manual"):
                print(f"\n➕ Only in Manual ({len(differences['only_in_manual'])}):")
                for field, value in differences["only_in_manual"].items():
                    print(f"    {field}: {value}")
        
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            import traceback
            print(f"  🔍 Details: {traceback.format_exc()}")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    run_comparison_tests()