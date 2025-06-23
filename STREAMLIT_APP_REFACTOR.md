```
# Refactoring Instructions for `streamlit_app.py`

**Goal:** Decompose `streamlit_app.py` into dedicated modules for improved anti-fragility and maintainability.

**Action to Claude:** "Extract the following specific logical blocks from `streamlit_app.py` into new modules as described below. After extraction, `streamlit_app.py` should only handle imports, top-level application initialization, navigation, and calls to the new module functions."

### New Modules & Their Responsibilities:

1.  **`src/app_state_manager.py`**:
    * **Logic to Move:** All `st.session_state` initializations and state reset functions (e.g., for "Process New File", "Process New Batch").
    * **Functions:** `initialize_session_state()`, `reset_single_extraction_state()`, `reset_batch_processing_state()`.

2.  **`src/processing/single_document_processor.py`**:
    * **Logic to Move:** All steps from file upload to `chunk_results` generation in the "Extract Data" section. This includes PDF text extraction, text chunking, prompt generation (with PICOTS/custom chars), LLM calls, and per-chunk analytics logging.
    * **Functions:** `process_document_for_extraction(...)` (takes all relevant inputs, returns `chunk_results`, `success_status`, `error_message`).

3.  **`src/processing/batch_document_pipeline.py`**:
    * **Logic to Move:** The entire batch processing loop logic, including ZIP file handling (`ZipProcessor`), temporary file management, and iterating through and processing each file. This module should call `single_document_processor.process_document` internally for each file.
    * **Functions:** `run_batch_processing(...)` (takes batch settings, files; returns summary results, e.g., `batch_results`, `failed_files`).

4.  **`src/ui/annotation_interface.py`**:
    * **Logic to Move:** All UI and operational logic for "Manual Annotation" tab, including loading files, rendering annotation/comparison UIs, and saving results.
    * **Functions:** `render_annotation_page()`, `render_comparison_page()`.

5.  **`src/ui/analytics_dashboard_renderer.py`**:
    * **Logic to Move:** All UI and plotting logic for "Analytics Dashboard".
    * **Functions:** `render_dashboard(analytics_manager)`.

### `streamlit_app.py` After Refactoring:

* **Imports:** Only import the main functions/classes from the new modules (e.g., `from src.processing.single_document_processor import process_document_for_extraction`).
* **Initialization:** Keep `logging` setup, `ConfigManager`, `TemplateSystem`, `Analytics` initialization. Call `app_state_manager.initialize_session_state()`.
* **Structure:** Maintain the main `st.sidebar.selectbox` navigation.
* **Page Content:** Each `if page == "..."` block should primarily:
    * Collect necessary user inputs from Streamlit widgets.
    * Call the appropriate function from the new modules, passing the collected inputs.
    * Display high-level feedback (e.g., success/error messages) based on return values.
    * Manage direct download buttons that use pre-generated files or simple DataFrame conversions.
```