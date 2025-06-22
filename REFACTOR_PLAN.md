# Refactoring Plan / Technical Debt Backlog

This document outlines areas of the codebase identified for refactoring, improvement, or optimization. Each item describes the current state, the desired state, and the rationale.

## 1. Deprecation Warnings

### 1.1. PyPDF2 to pypdf Migration
* **Current State:** The `src/pdf_processor/pdf_processor.py` module currently uses the deprecated `PyPDF2` library.
* **Desired State:** Migrate all PDF processing logic to use the `pypdf` library, which is the recommended and actively maintained successor.
* **Rationale:** Address `DeprecationWarning`, ensure future compatibility, and leverage potential performance improvements or new features of `pypdf`.

### 1.2. Claude Model Version Update
* **Current State:** The LLM interaction client in `src/llm/anthropic_client.py` uses the deprecated `claude-3-sonnet-20240229` model.
* **Desired State:** Update the model to a current, stable version, such as `claude-3-5-sonnet-20240620` (or the latest recommended Claude Sonnet model).
* **Rationale:** Address `DeprecationWarning`, ensure continued access to the latest model capabilities, and avoid potential service disruptions when the old model reaches EOL.

## 2. Code Quality & Readability

### 2.1. `src/pdf_processor/text_chunker.py` Refinement
* **Current State:** The `chunk_text` function, particularly the `respect_paragraphs=True` logic, has undergone several bug fixes. While functional, it might still be complex and could benefit from further simplification or extraction of helper methods.
* **Desired State:** Improve readability, potentially by breaking down the main `while` loop into smaller, more focused helper functions. Ensure clarity of boundary and overlap calculations.
* **Rationale:** Enhance maintainability, reduce cognitive load for future developers, and minimize the risk of reintroducing bugs.

### 2.2. `src/utils/data_validator.py` Refinement
* **Current State:** The validator logic has been updated to be more lenient, treating parsing failures as warnings.
* **Desired State:** Review the validation rules. Consider introducing configurable validation "modes" (e.g., 'strict', 'lenient', 'warning_only') or clearer logging for validation outcomes.
* **Rationale:** Provide more flexible and transparent data validation, allowing researchers to choose the strictness level appropriate for their use case. Improve debugging capabilities.

### 2.3. `streamlit_app.py` Modularization and Simplification
* **Current State:** `streamlit_app.py` is identified as the longest and most complex file in the project. It likely combines UI layout, data handling, and potentially core application logic.
* **Desired State:** Break down `streamlit_app.py` into smaller, more manageable functions or potentially separate modules (e.g., `ui_components.py`, `app_logic.py`). Separate UI rendering from business logic.
* **Rationale:** Improve readability, maintainability, and testability of the Streamlit application. Reduce the cognitive load associated with a single large file.

## 3. Modularization and Abstraction

### 3.1. LLM Client Abstraction Enforcement
* **Current State:** `src/llm/api_client.py` defines an interface, but explicit enforcement and clear separation of concerns might be improved.
* **Desired State:** Ensure strict adherence of `anthropic_client.py` and `openai_client.py` to the `api_client.py` interface. Potentially use Python's `abc` module for abstract base classes if not already.
* **Rationale:** Improve extensibility for adding new LLM providers, enforce consistent client behavior, and simplify testing.

## 4. Error Handling & Logging

### 4.1. Consistent Logging Levels
* **Current State:** Logging might not consistently use appropriate levels (DEBUG, INFO, WARNING, ERROR).
* **Desired State:** Standardize logging calls throughout the application, using correct levels for different types of messages (e.g., INFO for progress, WARNING for recoverable issues, ERROR for critical failures).
* **Rationale:** Improve observability and debugging capabilities, making it easier to monitor the application's health and troubleshoot issues. 