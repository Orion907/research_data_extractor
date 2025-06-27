# Domain Priming System: Implementation Plan & Status

This document outlines the implementation plan for dynamic domain mapping integration in the research data extraction pipeline, including the completed refactoring and upcoming UI development.

---

## ✅ **COMPLETED: Backend Refactoring (Phase 0)**

The domain priming system has been successfully refactored with a unified architecture:

### **Implemented Components:**
- **EnhancedPatternDetector**: Consolidated pattern detection and field mapping
- **DomainPrimingEngine**: Unified orchestrator for complete workflow
- **TermMapper**: Enhanced with LLM-based semantic understanding
- **Comprehensive Testing**: 9 test cases covering all functionality
- **Legacy Compatibility**: Backward compatibility maintained

### **Key Features:**
- ✅ Sample text analysis and pattern detection
- ✅ LLM-enhanced semantic term mapping
- ✅ Human-in-the-loop review and refinement
- ✅ Domain profile persistence (JSON storage)
- ✅ PICOTS-driven term filtering
- ✅ Dynamic prompt enhancement

---

## ✅ **COMPLETED: Complete UI Implementation (Phase 1)**

**🎉 Phase 1 Implementation Summary:**
- ✅ Complete domain priming UI with 4 interactive tabs
- ✅ Professional PDF upload and processing workflow
- ✅ Real-time pattern analysis with LLM enhancement
- ✅ Advanced domain mapping editor with CRUD operations  
- ✅ Comprehensive profile management system
- ✅ Full integration with existing Streamlit app
- ✅ Error handling, validation, and user feedback
- ✅ Session state management and progress tracking

### **Phase 1.1: Domain Priming Page Creation** ✅

Successfully created a complete Streamlit page dedicated to domain priming workflow:

**Implemented Files:**
```
✅ src/ui/pages/domain_priming_page.py        # Main page component
✅ src/ui/components/domain_mapping_components.py  # UI components  
✅ streamlit_app.py                           # Navigation integration
```

**Implemented Components:**
1. **✅ Sample Upload Section**
   - ✅ File uploader for 1-5 PDF sample articles
   - ✅ Progress indicator for PDF processing  
   - ✅ Validation (file type, size limits)
   - ✅ PDF text extraction with statistics

2. **✅ Domain Analysis Section** 
   - ✅ Real-time progress display during analysis
   - ✅ Analysis statistics (terms found, patterns detected)
   - ✅ LLM enhancement with configurable options
   - ✅ Analysis results summary with metrics

3. **✅ Domain Map Review Section**
   - ✅ Interactive table/editor for domain mappings
   - ✅ Add/Edit/Delete functionality for term equivalencies
   - ✅ Multi-tab interface for different operations
   - ✅ Change tracking and validation

4. **✅ Profile Management Section**
   - ✅ Save domain profile with custom name
   - ✅ Load existing profiles with preview
   - ✅ Profile listing with metadata
   - ✅ Export functionality

### **Phase 1.2: UI Component Development** ✅

**✅ SampleUploadComponent**
```python
class SampleUploadComponent:
    ✅ handle_file_upload()
    ✅ validate_files() 
    ✅ process_pdfs_to_text()
    ✅ display_upload_status()
```

**✅ DomainAnalysisComponent** 
```python
class DomainAnalysisComponent:
    ✅ run_pattern_analysis()
    ✅ enhance_with_llm()
    ✅ display_progress()
    ✅ show_analysis_results()
```

**✅ DomainMapEditorComponent**
```python
class DomainMapEditorComponent:
    ✅ display_mapping_table()
    ✅ handle_add_mapping()
    ✅ handle_edit_mapping() 
    ✅ handle_delete_mapping()
    ✅ validate_mappings()
```

**✅ ProfileManagerComponent**
```python  
class ProfileManagerComponent:
    ✅ save_profile()
    ✅ load_profile()
    ✅ list_profiles()
    ✅ delete_profile()
    ✅ export_profile()
```

### **Phase 1.3: Integration with Existing Workflow** ✅

**✅ Streamlit App Navigation:**
- ✅ Added "Domain Priming" to sidebar navigation
- ✅ Integrated with existing session state management
- ✅ Connected to configuration and analytics systems

**✅ Backend Integration:**
- ✅ Wired UI components to `DomainPrimingEngine`
- ✅ Implemented error handling and user feedback
- ✅ Added progress tracking for long-running operations

### **Phase 1.4: User Experience Enhancements** ✅

**✅ Safety Features:**
- ✅ Confirmation dialogs for destructive actions
- ✅ Change tracking for domain map edits  
- ✅ Profile metadata and backup functionality
- ✅ Validation warnings and user feedback

**✅ Performance Optimizations:**
- ✅ Progress indicators for PDF extraction
- ✅ Session state management for results caching
- ✅ Efficient component rendering
- ✅ Configurable LLM enhancement options

### **Implementation Architecture:**

```
streamlit_app.py
├── Navigation: "Domain Priming" 
└── DomainPrimingPage
    ├── SampleUploadComponent
    │   ├── File validation & upload
    │   └── PDF to text conversion
    ├── DomainAnalysisComponent  
    │   ├── EnhancedPatternDetector integration
    │   ├── TermMapper LLM enhancement
    │   └── Progress & results display
    ├── DomainMapEditorComponent
    │   ├── Interactive mapping table
    │   ├── CRUD operations
    │   └── Validation & warnings
    └── ProfileManagerComponent
        ├── Save/Load profiles
        ├── Profile listing & selection
        └── Export functionality
```

**Backend Integration:**
```python
# In DomainPrimingPage
engine = DomainPrimingEngine(
    llm_provider=config.llm_provider,
    api_key=config.api_key
)

# Phase 1 Workflow
sample_texts = upload_component.process_files()
domain_profile = engine.analyze_sample_articles(sample_texts)
refined_profile = engine.review_and_refine_domain_map(user_edits)
saved_path = engine.save_domain_profile(profile_name)
```

---

## ✅ **IMPLEMENTED: Context-Aware Prompt Management**

### **🚀 Advanced Context Window Management** ✅

The domain priming system now includes sophisticated context-aware prompt generation:

**✅ PICOTS-Based Prompt Chunking:**
- Separate prompts generated for each PICOTS section (Population, Intervention, Comparator, Outcome, Timing, Setting)
- Section-specific domain mappings included only where relevant
- Context size estimation and management (configurable token limits)

**✅ Intelligent Domain Mapping Selection:**
- Term extraction from PICOTS section content
- Relevance matching between section terms and domain mappings  
- Priority-based mapping inclusion (most comprehensive mappings first)
- Automatic synonym limiting to prevent context overflow

**✅ Prompt Chaining Workflow:**
- `execute_picots_extraction_workflow()` orchestrates complete extraction
- Each PICOTS section processed separately with appropriate mappings
- Token usage tracking and reporting
- Error handling with graceful degradation

**✅ Context Management Features:**
- Token estimation (4 chars ≈ 1 token approximation)
- Configurable context limits per section
- Reserved space for responses and safety margins
- Automatic mapping truncation when approaching limits

**✅ Backward Compatibility:**
- Legacy `generate_enhanced_prompt()` method maintained 
- Deprecation warnings guide users to new chunked approach
- All existing functionality preserved

---

## 📋 **PLANNED: Enhanced Extraction Integration (Phase 2)**

### **Phase 2.1: Extraction Page Enhancement**

Integrate domain priming into the existing extraction workflow:

**Modified Components:**
- **ExtractionPage**: Add domain profile selection
- **BatchPage**: Bulk apply domain profiles to multiple articles
- **Results Display**: Show domain mapping effects in results

**User Experience:**
1. **Profile Selection**
   - Dropdown to select active domain profile
   - Preview of selected profile's mappings
   - Option to create new profile if none exists

2. **PICOTS Integration** 
   - Automatic term extraction from PICOTS fields
   - Real-time preview of relevant domain mappings
   - Warning if no relevant mappings found

3. **Enhanced Prompt Preview**
   - Show before/after prompt comparison
   - Highlight injected domain mappings
   - Estimated context usage

### **Phase 2.2: Backend Integration Points**

**Modified Files:**
```
src/ui/pages/extraction_page.py
src/ui/pages/batch_page.py  
src/processing/extraction_engine.py
src/utils/prompt_manager.py
```

**Integration Architecture:**
```python
# In ExtractionEngine
def extract_with_domain_priming(self, text_chunks, picots_data, domain_profile):
    # Extract PICOTS terms
    picots_terms = engine.extract_picots_terms(picots_data)
    
    # Generate enhanced prompts
    enhanced_prompts = []
    for chunk in text_chunks:
        base_prompt = self.prompt_manager.create_extraction_prompt(chunk, picots_data)
        enhanced_prompt = engine.generate_enhanced_prompt(base_prompt, picots_terms)
        enhanced_prompts.append(enhanced_prompt)
    
    # Continue with existing extraction logic
    return self.process_with_enhanced_prompts(enhanced_prompts)
```

### **Phase 2.3: Results Analysis**

**Domain Mapping Analytics:**
- Track which domain mappings were used
- Measure extraction consistency improvements  
- Compare results with/without domain priming
- User feedback collection on mapping effectiveness

**Performance Monitoring:**
- Context window usage optimization
- LLM API cost impact analysis
- Processing time comparisons
- Success rate improvements

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
