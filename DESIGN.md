# Project Design: Research Data Extractor for Systematic Reviews (AI-Optimized)

## 1. System Goal

This tool assists researchers conducting systematic reviews by automating structured data extraction from PDF articles of Randomized Controlled Trials (RCTs). It aims to reduce manual effort and improve data consistency.

## 2. Primary Users

* Researchers conducting systematic reviews.

## 3. Core Workflow

The system's high-level workflow involves:
1.  **Input:** User provides PDF articles (already selected for a systematic review on a specific topic).
2.  **Intelligent Term Mapping (Pre-processing):** Software extracts domain-specific medical abbreviations and terms from a sample of articles for semantic normalization.
3.  **Protocol Context Injection:** User provides their systematic review protocol (P.I.C.O.T.S. information) as context.
4.  **Article Processing:** All input articles are converted to text and chunked for LLM optimization.
5.  **LLM Extraction:** Chunks, protocol context, and term mappings are fed to an LLM via API for data extraction.
6.  **Output:** Extracted data is saved in CSV format for researcher analysis.

## 4. Key Functional Components & Responsibilities

* **User Interface (`streamlit_app.py`, `cli/`):** Provides flexible input (Streamlit UI or Command Line Interface).
* **PDF Processing (`src/pdf_processor/`):**
    * Converts PDF articles to plain text.
    * Chunks text for optimized LLM context window management.
* **LLM Interaction (`src/llm/`):**
    * Manages API calls to Large Language Models (e.g., Anthropic, OpenAI).
    * Handles prompt construction and response parsing.
* **Intelligent Term Mapping (`src/utils/domain_priming/`):**
    * Utilizes Python's NLTK to identify relevant medical abbreviations and terms from a sample of articles.
    * Maps semantically equivalent terms to a canonical representation. This mapping is then used during LLM prompting/extraction.
* **Protocol Context Management:** Allows injection of P.I.C.O.T.S. (Population, Intervention, Comparison, Outcome, Timing, Setting) information from research protocols (Word docs via copy/paste) directly into LLM prompts.
* **Data Export (`src/data_export/`):** Converts extracted data into a researcher-friendly CSV format.
* **Core Utilities (`src/utils/`):** General shared functionalities, config management, analytics, etc.

## 5. Intelligence & Differentiation

The tool's intelligence primarily comes from:
* **Intelligent Term Mapping:** Using NLTK and LLM-assisted term extraction from sample articles to build a dynamic, review-specific glossary for semantic normalization during extraction.
* **P.I.C.O.T.S. Protocol Context:** Injecting structured research protocol information directly into the LLM prompt to significantly enhance extraction accuracy and relevance to the specific systematic review.
* **LLM Integration:** Leveraging advanced LLM capabilities for complex information extraction from unstructured text.