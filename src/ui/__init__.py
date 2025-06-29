"""
UI Package for Research Data Extractor

This package contains reusable UI components and page modules for the Streamlit application.
Supports modular, maintainable UI code organization.
"""

from .components import (
    FileUploadComponent,
    FileUploadSection,
    ProgressDisplayComponent,
    BatchProgressDisplay,
    ChunkProgressTracker,
    ProcessingStepsDisplay,
    ProgressCallbackHandler,
    ResultsViewerComponent,
    ResultsDownloadComponent,
    ResultsDisplaySection,
    ResultsComparisonComponent
)

from .pages import (
    ExtractionPage,
    ExtractionSettingsComponent,
    BatchPage,
    BatchSettingsComponent,
    BatchResultsComponent,
    AnnotationPage,
    AnalyticsPage,
    DomainSetupPage,
    BatchExtractionPage
)

__version__ = "1.0.0"