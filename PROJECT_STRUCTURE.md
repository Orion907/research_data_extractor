# Project Structure: Research Data Extractor (For AI Code Assistants)

This document provides a concise and accurate overview of the `research_data_extractor` project's file and directory structure. Its primary purpose is to facilitate efficient code analysis and interaction by AI code assistants like Claude.

## Top-Level Directory Overview

```plaintext
.
├── .env.example # Environment variable template
├── .gitignore
├── README.md
├── analytics/ # Generated analytics reports (CSV, JSON)
├── config/ # Application configuration files (YAML)
├── data/ # Data assets (input, output, domain profiles)
├── examples/ # Example usage scripts
├── main.py # Primary application entry point
├── project_info.md
├── prompts/ # LLM prompt templates (JSON files, versioned)
├── requirements.txt # Python package dependencies
├── scripts/ # Utility and automation scripts
├── setup.py # Project packaging configuration
├── src/ # Main application source code (detailed below)
├── streamlit_app.py # Streamlit web application entry point
└── tests/ # Test suites (detailed below)
```

**Note:** Temporary files, build artifacts, and `__pycache__` directories are omitted for clarity and efficiency.

## `src` Directory: Core Application Logic

```plaintext
.
├── __init__.py
├── batch_processor/
│   ├── __init__.py
│   └── batch_extractor.py
├── cli/
│   ├── __init__.py
│   ├── __main__.py
│   ├── commands/
│   │   └── __init__.py
│   ├── main.py
│   └── utils.py
├── data_export/
│   ├── __init__.py
│   └── csv_exporter.py
├── llm/
│   ├── __init__.py
│   ├── anthropic_client.py
│   ├── api_client.py
│   ├── client_factory.py
│   ├── mock_client.py
│   └── openai_client.py
├── pdf_processor/
│   ├── __init__.py
│   ├── pdf_processor.py
│   └── text_chunker.py
└── utils/
    ├── __init__.py
    ├── analytics.py
    ├── analytics_tracker.py
    ├── annotation_utils.py
    ├── config/
    │   └── template_categories.py
    ├── config_manager.py
    ├── data_extractor.py
    ├── data_validator.py
    ├── display_utils.py
    ├── docx_processor.py
    ├── domain_mapper.py
    ├── domain_priming/
    │   ├── __init__.py
    │   ├── pattern_detector.py
    │   └── term_mapper.py
    ├── picots_parser.py
    ├── prompt_manager.py
    ├── prompt_override.py
    ├── prompt_templates.py
    ├── results_manager.py
    ├── template_system.py
    ├── unified_analytics.py
    └── zip_processor.py
```

## `tests` Directory: Test Suites

```plaintext
.
├── __init__.py
├── run_integration_tests.py
├── test_anthropic_api.py
├── test_batch_processor.py
├── test_comparison_validation.py
├── test_config.py
├── test_config_manager.py
├── test_csv_export.py
├── test_data_extraction.py
├── test_data_extractor.py
├── test_data_extractor_debug.py
├── test_data_extractor_with_templates.py
├── test_data_validator.py
├── test_data_validator_enhanced.py
├── test_domain_enhanced_extraction.py
├── test_domain_profile_demo.py
├── test_end_to_end.py
├── test_enhanced_json_extraction.py
├── test_extraction_with_mock.py
├── test_extraction_with_validation.py
├── test_integration_workflow.py
├── test_llm_clients.py
├── test_mock_client.py
├── test_pattern_detector.py
├── test_pattern_detector_real_pdf.py
├── test_pdf_integration.py
├── test_pdf_processor.py
├── test_picots_parser.py
├── test_project_structure.py
├── test_prompt_management.py
├── test_prompt_versioning.py
├── test_results_manager.py
├── test_template_categories.py
├── test_template_preview.py
├── test_template_system.py
├── test_term_mapper.py
└── test_text_chunker.py
```
