"""
Definitions for prompt template categories.
This file contains the standard categories for organizing prompt templates.
"""

# Define the category options
EXTRACTION_DOMAINS = [
    "core_trial_characteristics",
    "population_parameters",
    "intervention_specifications",
    "comparative_elements",
    "outcome_measures",
    "statistical_framework",
    "bias_assessment",
    "safety_profile"
]

DATA_STRUCTURING_FORMATS = [
    "tabular_export",
    "nested_hierarchical",
    "ml_training_ready",
    "meta_analysis_compatible"
]

CUSTOMIZATION_TARGETS = [
    "domain_specific",
    "method_specific",
    "question_driven",
    "variable_focused"
]

# Map for human-readable names
CATEGORY_DISPLAY_NAMES = {
    # Extraction domains
    "core_trial_characteristics": "Core Trial Characteristics",
    "population_parameters": "Population Parameters",
    "intervention_specifications": "Intervention Specifications",
    "comparative_elements": "Comparative Elements",
    "outcome_measures": "Outcome Measures",
    "statistical_framework": "Statistical Framework",
    "bias_assessment": "Bias Assessment",
    "safety_profile": "Safety Profile",
    
    # Data structuring formats
    "tabular_export": "Tabular Export",
    "nested_hierarchical": "Nested Hierarchical",
    "ml_training_ready": "ML Training Ready",
    "meta_analysis_compatible": "Meta-Analysis Compatible",
    
    # Customization targets
    "domain_specific": "Domain-Specific",
    "method_specific": "Method-Specific",
    "question_driven": "Question-Driven",
    "variable_focused": "Variable-Focused"
}

# Consolidated categories for validation
ALL_CATEGORIES = EXTRACTION_DOMAINS + DATA_STRUCTURING_FORMATS + CUSTOMIZATION_TARGETS

# Category groups for organization
CATEGORY_GROUPS = {
    "extraction_domain": EXTRACTION_DOMAINS,
    "data_structuring": DATA_STRUCTURING_FORMATS,
    "customization_target": CUSTOMIZATION_TARGETS
}
