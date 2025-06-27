# Prototype Development Plan: Dynamic Domain Mapping Integration

This plan outlines a streamlined approach to integrate dynamic domain mapping into your existing research review data extraction pipeline, focusing on efficiency and user safety for your prototype.

---

## 1. Domain Map Generation Module (Phase 1: Build & Refine)

This initial phase creates the core functionality for identifying equivalent terms within your research domain.

### User Interaction: Sample Article Upload
* **User Action:** Your system will prompt the user to upload a small, representative sample of relevant PDFs (e.g., 5-10 articles). Clearly explain that these articles are used to build a domain-specific vocabulary map.

### Data Preparation
* **PDF to Text:** Leverage your existing PDF conversion module to transform the sample PDFs into plain text.
* **Text Chunking:** While not strictly necessary for domain mapping, using your existing chunking process here can simplify prototype development and integration.

### NLP Processing & Term Extraction
* **Python Libraries:** You'll primarily use **NLTK** and/or **SpaCy** for these steps.
* **Preprocessing:**
    * Perform **tokenization**, **lemmatization**, and **Part-of-Speech (POS) tagging** on the text from the sample articles.
    * Remove common stop words, punctuation, and purely numerical tokens to reduce noise.
* **Candidate Term Identification:**
    * Extract **nouns and noun phrases**. SpaCy's `noun_chunks` are highly effective for this, as these often represent the medical conditions, interventions, outcomes, and other key terms you want to map.
    * Filter these terms based on criteria like length or frequency to ensure relevance and reduce trivial entries.
* **Semantic Similarity & Clustering:**
    * Generate **word embeddings** for your candidate terms. SpaCy's pre-trained models come with excellent word vectors that are ideal for this.
    * Calculate the **cosine similarity** between all pairs of candidate terms. This metric quantifies how semantically close two terms are.
    * **Clustering:** Group terms that exhibit high semantic similarity (e.g., a cosine similarity score above a defined threshold, like 0.85). You can use a simple threshold-based grouping or a basic clustering algorithm from **Scikit-learn** (like Agglomerative Clustering) to identify clusters where "hypertension" and "high blood pressure" are correctly grouped together.

### Domain Map Structure & Storage
* **Data Structure:** Represent the domain map as a Python dictionary. A practical structure is one where **canonical terms** are keys, and their values are lists of **equivalent terms**. For example: `{'Hypertension': ['High blood pressure', 'HTN'], 'Myocardial Infarction': ['Heart attack', 'MI']}`.
* **Persistence:** Store this map in a lightweight, easily loadable format. A **JSON file** (`domain_map.json`) is a great choice for human readability and easy parsing, or a **Python pickle file** for direct object serialization. Storing it avoids regenerating the map for every user session.

### User Review & Refinement (Crucial Safety Feature)
* **User Interface (Basic):** Present the automatically generated domain map to the user. For a prototype, simply printing it to the console or displaying it in a basic web view (if applicable) is sufficient.
* **User Action:** Provide a mechanism for the user to **manually review, edit, add, or delete equivalencies**. This step is paramount for **safety**; it allows the domain expert (the researcher) to correct any erroneous groupings, remove false positives, or add crucial terms that the automated process might have missed. This **human-in-the-loop validation** minimizes the risk of incorrect or incomplete data extraction due to flawed mappings.
* **Save Refined Map:** After user review, save the finalized domain map.

---

## 2. Dynamic Domain Map Integration (Phase 2: Integrate & Test)

This phase integrates the refined domain map into your existing LLM prompting strategy, making your data extraction smarter.

### User Interaction: PICOTS Input
* **User Action:** The user copy-pastes their PICOTS information directly from their research protocol. (This is an existing step in your pipeline.)

### Enhanced Prompt Generation
* **Core Extraction Prompt:** Your existing process for generating the base LLM prompt from the user's PICOTS information will remain.
* **Dynamic Domain Map Injection (Key Safety & Efficiency Step):**
    * **Load Map:** Load the refined `domain_map.json` (or pickle file) into memory.
    * **PICOTS-Driven Filtering:** For each element of the PICOTS (Population, Intervention, Comparator, Outcome, Timing, Setting), extract the key terms the user has defined.
    * **Lookup & Select:** Look up these key PICOTS terms in your loaded `domain_map`. Identify any associated equivalent terms.
    * **Concise Injection:** Construct a **small, highly specific section** of the prompt that includes *only the relevant equivalencies* for the current PICOTS and extraction task. **Avoid sending the entire domain map to the LLM**, as this can quickly overwhelm the context window and increase API costs.
        * **Example Prompt Snippet:**
            ```
            "Please consider the following terms as equivalent for extraction:
            - 'Hypertension' and 'High blood pressure'
            - 'Myocardial Infarction' and 'Heart attack'
            - 'Intervention A' and 'Treatment A'"
            ```
    * **Instruction to LLM:** Explicitly instruct the LLM to use these provided equivalencies during the data extraction process. For example: "When extracting 'Outcome', if 'MI' is present, report it as 'Myocardial Infarction', also consider 'heart attack' as equivalent to 'Myocardial Infarction'."

### LLM Interaction
* **Input to LLM:** Your existing `chunk>LLM through API` process will now send the LLM an **enhanced prompt**. This prompt will contain your core extraction instructions based on PICOTS, the dynamically selected domain equivalencies, and the current article chunk.
* **Output:** The LLM extracts the data in the specified CSV format, leveraging the provided equivalencies for more accurate and consistent term usage. (This is an existing step in your pipeline.)

### Results Aggregation
* **CSV Consolidation:** Your existing process for consolidating the CSV results from individual chunks into a single, comprehensive CSV for all articles remains. The dynamic domain mapping should significantly improve the consistency of terms within this final output.

---

## 3. Safety & Iteration (Ongoing)

### Error Handling & Edge Cases
* **User Feedback Loop:** Encourage users to provide feedback on any inconsistencies or errors they find in the extracted data. This feedback is invaluable for continuously refining your domain mapping and prompt engineering strategies.
* **Term Ambiguity:** Be mindful that some terms can be ambiguous (e.g., "lead" can mean a metal or a type of study). The human review step for the domain map is a key mitigation for this, but it's an inherent challenge in NLP.

### Prototype Testing
* **Test with Varied Articles:** Thoroughly test the full pipeline with a diverse set of articles, including those that explicitly use equivalent terms, to confirm that the mapping functions as intended.
* **Iterative Refinement:** Be prepared to iteratively adjust the semantic similarity thresholds, clustering methods, and, most importantly, your prompt engineering based on the LLM's actual performance and output.

This plan aims to add significant intelligence to your prototype while maintaining a lean development approach and prioritizing accurate, user-validated results.

---
