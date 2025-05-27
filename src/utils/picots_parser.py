# src/utils/picots_parser.py
"""
Module for parsing PICOTS criteria from research protocols
"""
import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class PicotsData:
    """Structured PICOTS data"""
    population: List[str]
    interventions: List[str]
    comparators: List[str]
    outcomes: List[str]
    timing: List[str]
    setting: List[str]
    key_questions: Optional[List[str]] = None
    abbreviations: Optional[Dict[str, str]] = None
    detected_kqs: Optional[List[str]] = None

class PicotsParser:
    """Parser for PICOTS criteria tables"""
    
    def __init__(self):
        self.picots_sections = [
            'population', 'interventions', 'comparators', 
            'outcomes', 'timing', 'setting'
        ]
        
    def parse_picots_table(self, table_text: str, key_questions: Optional[str] = None) -> PicotsData:
        """
        Parse PICOTS table text into structured data
        
        Args:
            table_text (str): Raw PICOTS table text
            key_questions (str, optional): Separate key questions text
            
        Returns:
            PicotsData: Structured PICOTS information
        """
        logger.info("Parsing PICOTS table")
        
        # Initialize result structure
        result = PicotsData(
            population=[], interventions=[], comparators=[],
            outcomes=[], timing=[], setting=[]
        )
        
        # Parse key questions if provided
        if key_questions:
            result.key_questions = self._parse_key_questions(key_questions)
            
        # Detect KQs mentioned in the table
        result.detected_kqs = self._detect_table_kqs(table_text)
        
        # Parse abbreviations section
        result.abbreviations = self._parse_abbreviations(table_text)
        
        # Parse each PICOTS section
        for section in self.picots_sections:
            inclusion_criteria = self._extract_section_inclusion(table_text, section)
            setattr(result, section, inclusion_criteria)
            
        logger.info(f"Parsed PICOTS with {len(result.detected_kqs or [])} detected KQs")
        return result
    
    def _detect_table_kqs(self, text: str) -> List[str]:
        """Detect Key Question references in table text"""
        kq_pattern = r'KQ\s*(\d+)\.?\s*([^•\n]+)'
        matches = re.findall(kq_pattern, text, re.IGNORECASE)
        
        detected = []
        for kq_num, description in matches:
            detected.append(f"KQ {kq_num}: {description.strip()}")
            
        return list(set(detected))  # Remove duplicates
    
    def _parse_key_questions(self, kq_text: str) -> List[str]:
        """Parse separate key questions text"""
        # Split by Key Question indicators
        kq_pattern = r'\*\*Key Question \d+\.?\*\*\s*(.+?)(?=\*\*Key Question|\Z)'
        matches = re.findall(kq_pattern, kq_text, re.DOTALL | re.IGNORECASE)
        
        return [kq.strip() for kq in matches if kq.strip()]
    
    def _parse_abbreviations(self, text: str) -> Dict[str, str]:
        """Parse abbreviations section"""
        abbrev_section = re.search(r'Abbreviations?:(.+?)$', text, re.DOTALL | re.IGNORECASE)
        if not abbrev_section:
            return {}
            
        abbrev_text = abbrev_section.group(1)
        
        # Pattern to match "ABBREV = Full Name"
        pattern = r'([A-Z]+(?:-[A-Z]+)*)\s*=\s*([^;]+)'
        matches = re.findall(pattern, abbrev_text)
        
        return {abbrev.strip(): full_name.strip() for abbrev, full_name in matches}
    
    def _extract_section_inclusion(self, text: str, section: str) -> List[str]:
        """Extract inclusion criteria for a specific PICOTS section"""
        # Look for the section name followed by tab, then capture until the next tab (exclusion column)
        section_pattern = rf'{section.capitalize()}\s*\t([^\t]+)'
        section_match = re.search(section_pattern, text, re.IGNORECASE | re.DOTALL)
    
        if not section_match:
            return []
        
        # Get the inclusion content (everything between first and second tab)
        inclusion_text = section_match.group(1).strip()
    
        # Split into individual criteria by double newlines (KQ separators)
        criteria = []
    
        # Split by double newlines first to separate KQs
        kq_blocks = re.split(r'\n\s*\n', inclusion_text)
    
        for block in kq_blocks:
            block = block.strip()
            if block and not block.startswith('Definition'):  # Skip definition blocks
                criteria.append(block)
    
        return criteria

if __name__ == "__main__":
    # For quick testing during development
    print("Use 'python tests/test_picots_parser.py' for comprehensive testing")