# Clinical Research Data Extractor

This project extracts comprehensive clinical research data from published research article PDFs using the PICOTS framework and LLM integration.

## What It Extracts (PICOTS Framework)

- **Population**: Patient demographics, inclusion/exclusion criteria, baseline characteristics
- **Intervention**: Treatment details, drug dosages, procedures, therapy protocols  
- **Comparator**: Control groups, placebo details, comparison treatments
- **Outcomes**: Primary/secondary endpoints, efficacy measures, safety data
- **Timing**: Study duration, follow-up periods, treatment schedules
- **Setting**: Study locations, care settings, geographic details

## Key Features

- **PDF Processing**: Intelligent text extraction and chunking for optimal LLM processing
- **PICOTS Integration**: Parse and utilize PICOTS criteria to focus extraction
- **Template System**: Flexible prompt templates with versioning and analytics
- **Multiple LLM Support**: OpenAI, Anthropic, and mock clients for testing
- **Interactive UI**: Streamlit web interface for easy use
- **Batch Processing**: Handle multiple PDFs efficiently
- **Export Options**: CSV and XLSX output formats

## Project Structure

research_data_extractor/
├── src/                          # Source code
│   ├── pdf_processor/           # PDF extraction and text chunking
│   ├── llm/                     # LLM API integration (OpenAI, Anthropic, Mock)
│   ├── utils/                   # Core extraction logic, templates, analytics
│   │   ├── data_extractor.py    # Main extraction orchestrator
│   │   ├── template_system.py   # Prompt template management
│   │   ├── picots_parser.py     # PICOTS criteria parsing
│   │   └── analytics.py         # Performance tracking
│   └── data_export/             # CSV/XLSX export functionality
├── tests/                       # Comprehensive test suite
├── data/                        # Data files
│   ├── input/                   # Input PDFs
│   ├── output/                  # Extracted data
│   └── results/                 # Processed results
├── config/                      # Configuration files
├── streamlit_app.py            # Web interface
└── main.py                     # Command-line interface

## Quick Start

### 1. Environment Setup
```bash
conda create -n clinical_extractor python=3.9
conda activate clinical_extractor
pip install -r requirements.txt

# Set your API key (choose one)
export ANTHROPIC_API_KEY="your-key-here"
export OPENAI_API_KEY="your-key-here"

streamlit run streamlit_app.py
python main.py --pdf data/input/sample_article.pdf --output results/extracted_data.csv

from src.utils.data_extractor import DataExtractor

# Initialize extractor
extractor = DataExtractor(provider="anthropic")

# Extract from text chunks
results = extractor.extract_from_chunks(text_chunks)

from src.utils.picots_parser import PicotsParser

# Parse PICOTS criteria
parser = PicotsParser()
picots_data = parser.parse_picots_text(picots_criteria)

# Extract with PICOTS context
results = extractor.extract_from_chunks(
    text_chunks, 
    picots_context=picots_data
)

# Full test suite
python -m pytest tests/

# Specific component tests
python tests/test_picots_parser.py
python tests/test_data_extraction.py
python tests/test_end_to_end.py