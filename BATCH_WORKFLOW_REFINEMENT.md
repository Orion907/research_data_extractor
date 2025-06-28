# Batch Workflow Refinement Plan

## Overview
Streamline the research data extraction interface by removing redundant pages and creating an intuitive workflow focused on actual researcher needs for systematic reviews and meta-analyses.

## Current State Analysis

### Existing Pages (6 total):
1. **Unified Extraction** - Phase 1 prototype with domain priming + extraction
2. **Extract Data** - Single document extraction 
3. **Batch Processing** - Multiple document processing
4. **Manual Annotation** - Specialized annotation features
5. **Domain Priming** - Standalone domain vocabulary building
6. **Analytics Dashboard** - Usage statistics and analytics

### Problems Identified:
- **Redundant workflows**: Unified vs Extract Data do similar things
- **Cognitive overload**: Too many options, unclear starting point
- **Feature overlap**: Domain priming exists in multiple places
- **Decision paralysis**: Users unsure which page to use
- **Maintenance burden**: 6 different UIs to maintain and debug

## Proposed Streamlined Structure

### Target: 2 Essential Pages

#### 1. 🗺️ **Domain Setup** 
**Purpose**: One-time vocabulary preparation for research domain
- **Primary workflow**: Upload 3-5 sample articles → analyze → create domain map
- **Skip option**: "Skip domain setup / Use general extraction" for immediate processing
- **Load existing**: Choose from saved domain profiles
- **Domain preview**: Show sample mappings and vocabulary enhancements

#### 2. 📚 **Batch Extraction**
**Purpose**: Main research extraction workflow (1 or many documents)
- **Upload flexibility**: Single document or batch upload (same interface)
- **PICOTS input**: Research question criteria
- **Domain-aware processing**: Use domain map if available, general extraction if not
- **Results export**: CSV/JSON download with structured PICOTS data
- **Progress tracking**: Clear progress through uploaded documents

## Implementation Plan

### ✅ Phase 1: Remove Redundant Pages (COMPLETED)
**Status**: ✅ **COMPLETED** - Commit 6c0c760c 

**Accomplished**:
1. **✅ Removed from navigation**:
   - ❌ Manual Annotation (archived for future "Advanced Features")
   - ❌ Analytics Dashboard (archived for future settings/admin area)
   - ❌ Extract Data (functionality merged into Batch Extraction)
   - ❌ Unified Extraction (domain features moved to Domain Setup)
   - ❌ Domain Priming (merged into Domain Setup)

2. **✅ Updated streamlit_app.py**:
   - ✅ Simplified navigation to 2 main options
   - ✅ Added clear user guidance with tooltips
   - ✅ Added skip option for domain setup
   - ✅ Improved app title and descriptions

**Results**:
- Navigation reduced from 6 → 2 pages
- Clear workflow guidance implemented
- Skip option allows immediate extraction
- All core functionality preserved

**Actual Implementation**:
```python
# New streamlined navigation in streamlit_app.py
page = st.sidebar.selectbox(
    "Choose your workflow:", 
    ["🗺️ Domain Setup", "📚 Batch Extraction"],
    help="Domain Setup: Create vocabulary maps for better extraction (recommended first step)\n"
         "Batch Extraction: Extract PICOTS data from research articles (1 or many files)"
)
```

**User Experience Improvements**:
- Clear tooltips explain each workflow
- "Skip to Extraction" button for immediate processing  
- Consistent terminology focused on research workflows
- Better app title: "🔬 Research Data Extractor"

### Phase 2: Enhance Domain Setup Page
1. **Merge domain priming features** from multiple pages
2. **Add skip/default option** for immediate processing
3. **Improve onboarding** with clear workflow explanation
4. **Domain profile management** (save/load/preview)

### Phase 3: Enhance Batch Extraction Page
1. **Merge best features** from Unified Extraction and Extract Data
2. **Single upload interface** that handles 1 or many files gracefully
3. **PICOTS persistence** across sessions
4. **Domain-aware processing** when domain map available
5. **Structured CSV export** with research-ready PICOTS data

### Phase 4: Polish and Test
1. **User testing** with researchers
2. **Interface refinement** based on feedback
3. **Documentation** for clear workflows
4. **Performance optimization**

## Key Question (KQ) Management - Future Consideration

### Current Decision: Defer Implementation
- **Rationale**: Need researcher feedback on whether this adds value or complexity
- **Alternative**: Include KQ info in PICOTS field for now
- **Future option**: Add optional KQ tagging after core workflow is perfected

### Example KQ Structure (for future reference):
```
Key Question 1: Benefits/harms of mindfulness interventions in general child/adolescent populations
Key Question 2: Benefits/harms in children/adolescents with anxiety/depression  
Key Question 3: Benefits/harms in children/adolescents with chronic conditions at risk for anxiety/depression
```

### If implemented later:
- Optional KQ selection per batch upload
- KQ-specific PICOTS templates
- Results organized by KQ
- Cross-KQ analysis capabilities

## User Experience Goals

### Before (Current State):
```
User lands on app → Sees 6 confusing options → Uncertain where to start → 
Tries multiple pages → Gets frustrated with redundancy
```

### After (Target State):
```
User lands on app → Sees 2 clear options:
1. "Set up domain vocabulary (recommended first step)"
2. "Extract data from research articles"
→ Clear workflow → Successful extraction
```

## Success Metrics

### ✅ Usability (Phase 1 Achievements):
- ✅ **Dramatically reduced decision paralysis**: 6 → 2 clear options
- ✅ **Faster onboarding**: Clear workflow guidance with tooltips
- ✅ **Flexible entry point**: Can skip domain setup or use it for enhancement
- 🎯 **Target**: Reduced time to first successful extraction

### ✅ Technical (Phase 1 Achievements):
- ✅ **Reduced navigation complexity**: Simplified routing in streamlit_app.py
- ✅ **Cleaner imports**: Removed unused page dependencies
- ✅ **Maintained functionality**: All features preserved, just reorganized
- 🎯 **Target**: Easier maintenance and testing

### 🎯 Research Impact (Ongoing):
- ✅ **Preserved domain enhancement capabilities**: Domain setup still available
- ✅ **Maintained CSV export quality**: Research-ready PICOTS data structure
- 🎯 **Target**: Faster processing of systematic review workloads

## Implementation Timeline

### ✅ Phase 1 (COMPLETED): Remove Redundant Pages
- ✅ Update navigation and routing
- ✅ Archive unused page components  
- ✅ Test core functionality still works
- ✅ Add skip options and user guidance

**Status**: **COMPLETED** - All Phase 1 objectives achieved

### 🔄 Phase 2 (NEXT): Enhance Domain Setup Page
- **Current status**: Using unified_extraction_page domain priming section
- **Next steps**:
  - Improve skip/default workflow
  - Better onboarding guidance
  - Domain profile management improvements

### 📋 Phase 3 (PLANNED): Enhance Batch Extraction Page  
- Merge best features from previous pages
- Improve upload interface for 1 or many files
- Enhanced PICOTS persistence and CSV export
- Better progress tracking

### 🧪 Phase 4 (PLANNED): Testing and Refinement
- User testing with researchers
- Interface improvements based on feedback
- Documentation and onboarding materials
- Performance optimization

## Risk Mitigation

### Risk: Users miss domain setup benefits
**Mitigation**: Clear onboarding guidance, optional but recommended workflow

### Risk: Loss of specialized features
**Mitigation**: Move advanced features to settings area, don't delete code initially

### Risk: Workflow too simplified
**Mitigation**: Gather user feedback early, be ready to add complexity if needed

## File Changes Required

### To Remove:
- `src/ui/pages/extraction_page.py` (merge into batch)
- `src/ui/pages/manual_annotation_page.py` (archive)
- `src/ui/pages/analytics_page.py` (move to settings)
- `src/ui/pages/domain_priming_page.py` (merge into domain setup)

### To Enhance:
- `src/ui/pages/batch_page.py` → Enhanced batch extraction
- `src/ui/pages/unified_extraction_page.py` → Transform into domain setup
- `streamlit_app.py` → Simplified navigation

### Navigation Structure:
```python
pages = {
    "🗺️ Domain Setup": DomainSetupPage,
    "📚 Batch Extraction": BatchExtractionPage
}
```

## Long-term Vision

Create the most intuitive research data extraction tool possible:
- **Researchers can start extracting immediately** (skip domain setup)
- **Or get enhanced results** with minimal domain setup effort  
- **Process 1 article or 100 articles** with the same simple workflow
- **Export research-ready data** without manual formatting
- **Scale to handle systematic reviews** with hundreds of articles

The goal is to make research data extraction as simple as uploading files and clicking "Extract" while maintaining the sophisticated domain-aware capabilities under the hood.