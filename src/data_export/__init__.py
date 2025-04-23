"""
Data export module for the research data extraction project
"""
from .csv_exporter import save_to_csv

# Make these functions directly importable
__all__ = ['save_to_csv']