# LLM Prompting Strategy (AI-Optimized)

## 1. Core Prompting Approach

The system employs a dynamic and context-rich prompting strategy for the Large Language Model (LLM) to maximize data extraction accuracy from research articles.

## 2. Key Prompt Components

Each LLM API call's prompt typically comprises the following critical elements:

* **Article Text Chunks:** Segments of the research article, processed by `src/pdf_processor/text_chunker.py`. This ensures the LLM receives manageable and relevant portions of the document.
* **Systematic Review Protocol Context (P.I.C.O.T.S.):**
    * Information extracted from the researcher's protocol document (Population, Intervention, Comparison, Outcome, Timing, Setting).
    * This is provided to the LLM to guide its understanding of the relevant data points and ensure extraction aligns with the review's scope.
* **Intelligent Term Mappings:**
    * A dynamically generated glossary of semantically equivalent medical abbreviations and terms, created by `src/utils/domain_priming/`.
    * This mapping instructs the LLM to normalize variations of terms (e.g., "T2DM" and "Type 2 Diabetes Mellitus" should be mapped to a single canonical term) during extraction.
* **Extraction Instructions/Schema:** Explicit instructions to the LLM on what data to extract and in what format (e.g., JSON schema, field definitions).

## 3. Prompt Management

* Prompts are likely versioned (e.g., `prompts/*_v*.json` at root level).
* `src/utils/prompt_manager.py` is responsible for selecting, loading, and assembling the appropriate prompt template with the dynamic context.