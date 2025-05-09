# Research Data Extraction Project

This project extracts patient characteristic data from research article PDFs using Python and LLM integration.

## Project Structure

```
data_extraction_project/
├── src/                   # Source code
│   ├── pdf_processing/    # PDF extraction and text chunking
│   ├── llm/               # LLM API integration
│   └── data_export/       # CSV/XLSX export
├── tests/                 # Test scripts
├── data/                  # Data files
│   ├── input/             # Input PDFs
│   └── output/            # Extracted data
└── requirements.txt       # Dependencies
```

## Setup

1. Create and activate virtual environment:
```bash
conda create -n data_ext_env python=3.9
conda activate data_ext_env
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Extract Text from PDF
```python
from src.pdf_processing import extract_text_from_pdf

# Extract text from a PDF
text = extract_text_from_pdf('data/input/sample_research_article.pdf')
```

### Chunk Text for LLM Processing
```python
from src.pdf_processing import chunk_text

# Create text chunks for LLM processing
chunks = chunk_text(text, chunk_size=1000, overlap=150)
```

## Testing

Run unit tests:
```bash
python -m tests.test_text_chunker
```

Run extraction and chunking test:
```bash
python -m tests.test_text_chunker --run-extraction
```