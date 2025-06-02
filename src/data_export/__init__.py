"""
Data export module for the research data extraction project
"""
from .csv_exporter import save_to_csv, save_extraction_results_to_csv, flatten_json_for_csv

# Make these functions directly importable
__all__ = ['save_to_csv', 'save_extraction_results_to_csv', 'flatten_json_for_csv'] 