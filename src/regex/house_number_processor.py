#!/usr/bin/env python3
"""
Complete House Number Processor - All-in-One Solution
======================================================

Single comprehensive script for Bangladeshi address house number extraction,
processing, organization, and management.

Features:
    1. Extract house numbers from addresses (Core Algorithm)
    2. Process entire dataset with confidence filtering
    3. Split dataset by confidence levels
    4. Re-process specific confidence folders
    5. Sync changes between split and main dataset

Usage:
    # Extract from single address
    python3 house_number_processor.py extract "270/a Dhanmondi 15, Dhaka"
    
    # Process entire dataset
    python3 house_number_processor.py process --confidence 0.70
    
    # Split dataset by confidence
    python3 house_number_processor.py split
    
    # Re-process specific confidence level
    python3 house_number_processor.py reprocess 2.very_high_90_95
    
    # Update main dataset from split
    python3 house_number_processor.py sync 2.very_high_90_95

Author: Advanced AI Address Parser System
Date: December 2025
Version: 2.0
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ============================================================================
# CORE EXTRACTION ALGORITHM
# ============================================================================

class ExtractionMethod(Enum):
    """Methods used for extraction"""
    EXPLICIT_HOUSE = "explicit_house"
    BANGLA_PATTERN = "bangla_pattern"
    ENGLISH_PATTERN = "english_pattern"
    CONTEXTUAL = "contextual"
    POSITIONAL = "positional"
    MIXED_LANGUAGE = "mixed_language"
    SLASH_FORMAT = "slash_format"
    NOT_FOUND = "not_found"
    NOT_CONFIDENT = "not_confident"
    INSTITUTIONAL = "institutional_skip"


@dataclass
class HouseNumberResult:
    """Result of house number extraction"""
    house_number: str
    confidence: float
    method: ExtractionMethod
    original: str = ""
    reason: str = ""
    
    def __str__(self):
        return f"HouseNumber('{self.house_number}', {self.confidence:.1%}, {self.method.value})"
    
    def to_dict(self) -> Dict:
        return {
            'house_number': self.house_number,
            'confidence': self.confidence,
            'method': self.method.value,
            'original': self.original,
            'reason': self.reason
        }


class AdvancedHouseNumberExtractor:
    """Advanced AI-Based House Number Extractor for Bangladeshi Addresses"""
    
    def __init__(self, preserve_format: bool = True, confidence_threshold: float = 0.70):
        self.preserve_format = preserve_format
        self.confidence_threshold = confidence_threshold
        self._setup_advanced_patterns()
        self._setup_exclusions()
        self._setup_bangla_mappings()
        
    def _setup_advanced_patterns(self):
        """Setup advanced extraction patterns"""
        
        # EXPLICIT HOUSE PATTERNS (96-98% confidence)
        # CRITICAL: Most specific patterns FIRST, simple patterns LAST
        # HIGHEST PRIORITY: House/Building/Plot/Holding patterns (explicit mentions)
        self.explicit_house_patterns = [
            # Hash notation with complex patterns - e.g., "H# CB 11/12" - capture full pattern
            (r'(h#[\s]*[A-Z]{1,3}[\s]+[\d০-৯]+[a-zA-Z0-9/\-&\s]*?)(?=\s*[,\(]|\s*$)', 0.98),  # H# CB 11/12
            (r'(h#[\s]*[A-Z]{0,3}[\s]*[\d০-৯]+[a-zA-Z0-9/\-&\s]*?)(?=\s*[,\(]|\s*$)', 0.98),
            # House# with letter+number - e.g., "House#F25" - capture full
            (r'((?:house|home)[#][\s]*[A-Za-z][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Capture "House#F25"
            (r'(house#[\s]*[\d০-৯]+[a-zA-Z0-9/\-&\s]*?)(?=\s*[,\(]|\s*$)', 0.98),
            (r'(home#[\s]*[\d০-৯]+[a-zA-Z0-9/\-&]*)', 0.98),
            
            # H:51 pattern (H colon number) - e.g., "H:51, R:18, S:7"
            (r'\bh:[\s]*([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            
            # H # 1 pattern (H space hash) - e.g., "H # 1, R # 9" - capture full pattern
            (r'\b(h\s+#\s*[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            
            # Letter hash number pattern - e.g., "U#19"
            (r'\b([A-Z]#[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Captures full pattern like "U#19"
            
            # H@ pattern (H at symbol) - e.g., "h@45", "H@45" - extract number only
            (r'\b[hH]@[\s]*([\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # h@45 → "45", H@45 → "45"
            # H-07, R-2/2 type patterns (H = House, R = Road - but H takes priority)
            # IMPORTANT: Handle slash patterns like "h-107/2" - extract number only
            (r'\b[hH][\s-]+([\d০-৯]+[/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # h-107/2 → "107/2", H-12/6 → "12/6" (with slash - HIGH PRIORITY)
            (r'^h[\s-]+([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # H-07 → "07" (at start)
            (r'\b[hH][\s-]+([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # H-7 → "7", H-04 → "04", h-107 → "107" (anywhere)
            # H with number (no dash) - e.g., "H3" - extract number only
            (r'\b[hH][\s]*([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # H3 → "3", h3 → "3"
            
            # H 30/B pattern (H space number/slash) - e.g., "H 30/B"
            (r'\bh\s+([\d০-৯]+[/\-][a-zA-Z\d]+)(?=\s*[,\(\)]|\s|$)', 0.98),
            
            # Banglish alphabet patterns with house numbers - MUST CAPTURE FULL PREFIX (e.g., "Kha/50", "JA-10/1/A", "CHO 55/A", "Kh-72/8", "K/72/3")
            # Handle both with and without spaces/dashes between Banglish prefix and number
            (r'((?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]*[-/]?[\s]*[\d০-৯]+[/\-][\d০-৯]+[/\-][a-zA-Z\d]+)', 0.98),  # JA-10/1/A, K/72/3
            (r'((?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]+[\d০-৯]+[/\-][a-zA-Z\d]+)(?=\s*[,\(\)]|\s|$)', 0.98),  # CHO 55/A, Kha 72/B (with space, number/letter)
            (r'((?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]+[\d০-৯]+[/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Kha 72/8 (with space, number/number)
            (r'((?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]*[-/][\s]*[\d০-৯]+[/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Kha/50, Kh-72/8 (with dash/slash) - MUST MATCH Kha/50
            (r'((?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]*[/][\s]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),  # Kha/50 (simple slash pattern) - HIGH PRIORITY
            (r'((?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]*[-/]?[\s]*[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Simple Banglish patterns
            
            # Building number patterns (e.g., "Building No 376", "Building No. 376", "Building No-2", "Building no:3")
            (r'(?:building|bldg)[\s]+(?:no\.?|number|#)[\s\-:]*([\d০-৯]{1,5}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            
            # Building without "No" keyword - e.g., "Building 9", "Building 11G"
            (r'(?:building|bldg)[\s]+([\d০-৯]{1,5}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            
            # Building with dash and zero - e.g., "Building-03"
            (r'(?:building|bldg)[\s-]+([\d০-৯]{1,5}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            
            # Plot number patterns with ampersand (e.g., "Plot #70 & 70/1")
            (r'(?:plot)[\s]+(?:no\.?|number|#|:)[\s-]*([\d০-৯]+[\s]*&[\s]*[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Plot number patterns (e.g., "Plot - 9/2(a)", "Plot # 17", "Plot No. 8", "Plot #24/2")
            (r'(?:plot)[\s]+(?:no\.?|number|#|:)[\s-]*([\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?[\(]?[a-zA-Z\d]?[\)]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Plot # with slash - e.g., "Plot #24/2" - capture full pattern
            (r'((?:plot)[\s]+#[\s]*[\d০-৯]+[/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Capture "Plot #24/2"
            
            # Plot with space (no dash) - e.g., "Plot 4"
            (r'(?:plot)[\s]+([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            
            # Plot with dash - e.g., "Plot-6", "Plot-62"
            (r'(?:plot)[\s-]+([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            
            # Holding number patterns (e.g., "Holding No: 228/B/3/A") - capture full pattern
            (r'(?:holding)[\s]+(?:no\.?|number|#)[\s:]*[\s-]*([\d০-৯]+[/\-][a-zA-Z\d]+[/\-][\d০-৯]+[/\-][a-zA-Z\d]+)(?=\s*[,\(\)]|\s|$)', 0.98),  # 228/B/3/A
            (r'(?:holding)[\s]+(?:no\.?|number|#)[\s:]*[\s-]*([\d০-৯]+[/\-]?[a-zA-Z\d/]+)(?=\s*[,\(\)]|\s|$)', 0.98),  # Other holding patterns
            
            # Holding with letter-number pattern - e.g., "Holding no: E-10"
            (r'(?:holding)[\s]+(?:no\.?|number|#)[\s:]*[\s-]*([A-Za-z][\s-]*[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            
            # Holding with dash - e.g., "Holding no-1924" (no space after "no") - HIGH PRIORITY - capture full
            (r'((?:holding)[\s]+no-[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Capture "Holding no-1924"
            # Holding No New: pattern - e.g., "Holding No New: 97" - capture full
            (r'((?:holding)[\s]+(?:no\.?|number|#)[\s]+new[\s:]*[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Capture "Holding No New: 97"
            
            # House with multiple numbers (ranges, plus, ampersand) - MUST BE BEFORE simple number patterns
            (r'(?:house|home|hous|bari|basha)[\s:]*(\d+[\s]*[+&][\s]*\d+)', 0.98),  # 8+9, 8&9 (check first!)
            (r'(?:house|home|hous|bari|basha)[\s:]*(\d+[\s]*[-][\s]*\d+)', 0.98),  # 98-99, 169-170, 16-17
            
            # House with number + Banglish pattern (e.g., "House 60 Kha 7")
            (r'(?:house|home|hous|bari|basha)[\s]+([\d০-৯]+[\s]+(?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]+[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),  # House 60 Kha 7
            
            # House No. with comma-separated numbers including slash (e.g., "House No. 33, 33/1")
            (r'(?:house|home|hous|bari|basha)[\s]+(?:no\.?|number|#)[\s-]*([\d০-৯]{1,5}[\s]*,[\s]*[\d০-৯]{1,5}[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # House No. with comma-separated numbers (e.g., "House No 37,39")
            (r'(?:house|home|hous|bari|basha)[\s]+(?:no\.?|number|#)[\s-]*([\d০-৯]{1,5}[\s]*,[\s]*[\d০-৯]{1,5})(?=\s*[,\(\)]|\s|$)', 0.98),
            # House No. patterns (e.g., "House No. 16", "House No - 63", "House-303", "House-09", "House-34")
            # House No # pattern - e.g., "House No #17" - capture full
            (r'((?:house|home|hous|bari|basha)[\s]+(?:no\.?|number)[\s]*#[\s]*[\d০-৯]{1,5}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Capture "House No #17"
            (r'(?:house|home|hous|bari|basha)[\s]+(?:no\.?|number|#)[\s-]*([\d০-৯]{1,5}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # House No: pattern (with colon) - e.g., "House No: 01", "House No: 24", "House No: 149" - capture full
            (r'((?:house|home|hous|bari|basha)[\s]+(?:no\.?|number|#)[\s:]*[\d০-৯]{1,5}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Capture "House No: 01"
            # House No. with letter/number - e.g., "House No. F/30" - capture full
            (r'((?:house|home|hous|bari|basha)[\s]+(?:no\.?|number|#)[\s-]*[A-Za-z][/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Capture "House No. F/30"
            # House No. with letter+number - e.g., "House No. B40" - capture full
            (r'((?:house|home|hous|bari|basha)[\s]+(?:no\.?|number|#)[\s-]*[A-Za-z][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Capture "House No. B40"
            (r'(?:house|home|hous|bari|basha)[\s-]+([\d০-৯]{1,5}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # House-303, House-09
            # House with space and dash - e.g., "house -01", "House - 8" - capture full (handle period after number)
            (r'((?:house|home|hous|bari|basha)[\s]+-[\s]*[\d০-৯]{1,5}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Capture "house -01", "House - 8"
            # House with colon (with or without space) - e.g., "House: 81/A", "House: 1", "House : 11/A" - capture full
            (r'((?:house|home|hous|bari|basha)[\s]*:[\s]*[\d০-৯]+[/\-]?[A-Za-z]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Capture "House: 81/A", "House: 1", "House : 11/A"
            # House with letter/number - e.g., "House A/10", "House C/36" - capture full
            (r'((?:house|home|hous|bari|basha)[\s]+[A-Za-z][/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Capture "House A/10", "House C/36"
            # House with letter+number - e.g., "House J57" - capture full
            (r'((?:house|home|hous|bari|basha)[\s]+[A-Za-z][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Capture "House J57"
            (r'(?:house|home|hous|bari|basha)[\s]+([\d০-৯]{1,5}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # House 20, House 1 (simple number)
            # House with slash pattern - e.g., "House 4/4", "House 12/6" - capture full
            (r'((?:house|home|hous|bari|basha)[\s]+[\d০-৯]+[/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Capture "House 4/4", "House 12/6"
            
            # House with 3-part slash patterns (e.g., 316/1/B, 93/3/A) - Must capture full pattern
            (r'(?:house|home|hous|bari|basha)[\s:]*(\d+/\d+/[a-zA-Z0-9]+)', 0.98),
            
            # House with 2-part slash + letter (e.g., 36/1, 88/B, 187/4, 689/A)
            (r'(?:house|home|hous|bari|basha)[\s:]*(\d+/\d+)', 0.98),  # 36/1, 187/4, 9/6, 11/1
            (r'(?:house|home|hous|bari|basha)[\s:]*(\d+/[a-zA-Z]+)', 0.98),  # 88/B, 689/A, 315/A, 11/A
            
            # House with dash + letter (e.g., 88-B, 12B)
            (r'(?:house|home|hous|bari|basha)[\s:]*(\d+[\s]*-[\s]*[a-zA-Z])', 0.98),
            (r'(?:house|home|hous|bari|basha)[\s-]+(\d+[a-zA-Z])(?=\s*[,\(\)]|\s|$)', 0.98),  # House-12B
            
            # Basa/Basha with complex slash (e.g., Basa 49/23)
            (r'(?:basa|basha)[\s]*([\d০-৯]+[/\-]\d+(?:[/\-][a-zA-Z0-9]+)?)', 0.98),
            
            # Basa with lowercase "no" - e.g., "basa no.753"
            (r'(?:basa|basha)[\s]+(?:no\.?|number|#)[\s-]*([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            
            # Number before "No House" - e.g., "78 No House"
            (r'([\d০-৯]+[a-zA-Z]?)[\s]+no\s+house(?=\s*[,\(\)]|\s|$)', 0.98),
            
            # Number before "No Basa" - e.g., "15 No Basa"
            (r'([\d০-৯]+[a-zA-Z]?)[\s]+no\s+basa(?=\s*[,\(\)]|\s|$)', 0.98),
            
            # House with slash and multiple letters (e.g., House 10/GA, House 17/E)
            (r'(?:house|home|hous|bari|basha)[\s:]*(\d+[/\-][A-Z]+)', 0.98),
            
            # House with single letter suffix (e.g., House 12A)
            (r'(?:house|home|hous|bari|basha)[\s:]*(\d+[a-zA-Z])', 0.98),
            
            # Home- pattern - e.g., "Home-1342" - capture full
            (r'((?:home)[\s-]+[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Capture "Home-1342"
            # Home with letter+number - e.g., "Home J57" - capture full
            (r'((?:home)[\s]+[A-Za-z][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Capture "Home J57"
            # Home No. pattern - e.g., "Home No. C-3"
            (r'(?:home)[\s]+(?:no\.?|number|#)[\s-]*([A-Za-z][\s-]*[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Mahol- pattern (Banglish) - e.g., "Mahol-732"
            (r'(?:mahol|mahal)[\s-]+([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            
            # House with just number (LOWEST PRIORITY - checked last)
            (r'(?:house|home|hous|hose|hause)[\s:]*([\d০-৯]{1,5})(?=\s*[,\(\)]|\s|$)', 0.96),
        ]
        
        # Common words to exclude from house number matching
        self.excluded_words = [
            'Staff', 'South', 'North', 'East', 'West', 'Road', 'Street', 'Lane', 
            'Avenue', 'Block', 'Sector', 'Plot', 'Floor', 'Flat', 'Building',
            'Tower', 'House', 'Apartment', 'Complex', 'Market', 'Bazar', 'Goli',
            'Moholla', 'Para', 'Purbo', 'Paschim', 'Uttar', 'Dakkhin'
        ]
        
        # SLASH FORMAT PATTERNS (90-95% confidence)
        # Order matters: most specific patterns first!
        self.slash_patterns = [
            # Slash patterns with range (e.g., "345/3-5") - MUST be before range patterns
            (r'(\d+[/\-]\d+[-]\d+)\s*[,\s]', 0.95),  # 345/3-5 (number/number-number)
            
            # Banglish suffix patterns (e.g., "44/22 KA", "72/8", "9/2(a)")
            (r'(\d+[/\-]\d+[\s]+(?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[a-z]?)(?=\s*[,\(\)]|\s|$)', 0.95),  # 44/22 KA
            (r'(\d+[/\-]\d+[a-zA-Z]?[\(]?[a-zA-Z\d]?[\)]?)(?=\s*[,\(\)]|\s|$)', 0.93),  # 9/2(a), 72/8, 44/22
            
            # 4-part with letter in 2nd position (e.g., 363/A/4/3)
            (r'(\d+[/\-][A-Z][/\-]\d+[/\-]\d+)\s*[,\s]', 0.95),
            # 4-part with letter in 3rd position (e.g., 76/2/E/24)
            (r'(\d+[/\-]\d+[/\-][A-Z][/\-]\d+)\s*[,\s]', 0.95),
            # 4-part all numeric (e.g., 135/3/A/1)
            (r'(\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?)\s*[,\s]', 0.95),
            # 3-part with letters at end (e.g., 255/1/Gha, 135/3/Ka)
            (r'(\d+[/\-]\d+[/\-][A-Za-z]+)\s*[,\s]', 0.93),
            # 3-part patterns (e.g., 202/1-D, 135/3/A-1, 27/A/1k, 238/1/N)
            (r'(\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?[/\-][A-Z])\s*[,\s]', 0.93),
            (r'(\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?)\s*[,\s]', 0.93),
            (r'(\d+[/\-][A-Za-z][/\-]\d+[a-zA-Z]?)\s*[,\s]', 0.93),  # 27/A/1k, 43/E/2
            # 3-part with letter at end - e.g., "238/1/N", "60/1/A" (English equivalent of Bangla pattern)
            (r'(\d+[/\-]\d+[/\-][A-Za-z])(?=\s*[,\(\)]|\s|$)', 0.93),  # 238/1/N, 60/1/A
            # 3-part with letter-number pattern - e.g., "135/3/A-1"
            (r'(\d+[/\-]\d+[/\-][A-Za-z][\s-]*\d+[a-zA-Z]?)(?=\s*[,\s\.]|$)', 0.93),  # 135/3/A-1
            # Number/letter/letter pattern - e.g., "10/W/A"
            (r'(\d+[/\-][A-Za-z][/\-][A-Za-z])\s*[,\s]', 0.93),
            # 2-part with space + letter (e.g., "27/2 C") - HIGH PRIORITY to capture full pattern
            (r'(\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?\s+[A-Z])(?=\s|,|$)', 0.95),
            # 2-part patterns
            (r'(\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?)\s*[,\s]', 0.90),
            # 1-part with letter suffix (e.g., 23/Ka) - checked last
            (r'(\d+[a-zA-Z]?[/\-][a-zA-Z]+)\s*[,\s]', 0.90),
            
            # Number-letter-slash pattern - e.g., "43-R/5", "1-A/11", "2-F/3"
            (r'(\d+[a-zA-Z]?[-][A-Za-z][/\-]\d+[a-zA-Z]?)\s*[,\s]', 0.93),
            
            # Letter-letter-slash pattern - e.g., "BA-A/3", "House-E/13"
            (r'([A-Za-z]{2,}[-][A-Za-z][/\-]\d+[a-zA-Z]?)\s*[,\s]', 0.93),
            
            # Location C/A pattern - e.g., "72 Dilkusha C/A" - extract just the number before location
            # This is a contextual pattern, so add it to contextual_patterns instead
        ]
        
        # CONTEXTUAL PATTERNS (85-95% confidence)
        self.contextual_patterns = [
            # Range patterns anywhere in address (e.g., "177-78" in "9A, Hal Madhobilota, 177-78, Malibagh")
            (r'(?:^|[,\s])(\d{1,4}[\s]*[-][\s]*\d{1,4})(?=\s*[,\(]|\s+[A-Z])', 0.95),
            # Comma-separated house numbers anywhere (e.g., "367, 368" in middle of address)
            # Exclude if second number is followed by location keywords (e.g., "376, 60 Feet" - 60 is part of road name)
            (r'(?:^|[,\s])(\d{1,4}[\s]*,[\s]*\d{1,4})(?=\s*[,\(]|\s+[A-Z])(?!.*(?:feet|road|street|lane|avenue|goli|bazar|market|moholla|para|block|sector))', 0.95),
            # Standalone number before location name (e.g., "712 Nayanagar", "73 Dilkhusa")
            (r'(?:^|[,\s])(\d{2,4}[a-zA-Z]?)(?=\s+[A-Z][a-z]+)', 0.90),  # 73 Dilkhusa, 712 Nayanagar
            
            # Number before location with C/A pattern - e.g., "72 Dilkusha C/A"
            (r'(?:^|[,\s])(\d{2,3}[a-zA-Z]?)(?=\s+[A-Za-z]+\s+[A-Za-z]/[A-Za-z])', 0.90),
            # Complex slash patterns
            (r'(?:^|[,\s])(\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?[/\-][a-zA-Z\d]+)(?=\s*[,\(]|\s+[A-Z])', 0.92),
            (r'(?:^|[,\s])(\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?[/\-][a-zA-Z\d]+)(?=\s*[,\(]|\s+[A-Z])', 0.92),
            (r'(?:^|[,\s])(\d+[a-zA-Z]?[/\-][a-zA-Z\d]+)(?=\s*[,\(]|\s+[A-Z])', 0.90),
            (r'(?:^|[,\s])(\d+[/\-][a-zA-Z])(?=\s*[,\(]|\s+[A-Z])', 0.90),
        ]
        
        # BANGLA PATTERNS (90-95% confidence)
        self.bangla_patterns = [
            # Bangla number with নং - e.g., "৩৩২ নং পিরেরবাগ"
            (r'([\d০-৯]+)[\s]+নং(?=\s+[^\d])', 0.95),
            # Bangla house with hash - e.g., "বাড়ি#২৩৫" - capture full
            (r'((?:বাড়ি|বাসা|বাড়ী)[#][\s]*[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.95),  # Capture "বাড়ি#২৩৫"
            # Bangla slash pattern - e.g., "১২৬/সি" - capture full
            (r'([\d০-৯]+[/\-][\u0980-\u09FF]+)(?=\s*[,\(\)]|\s|$)', 0.95),  # Capture "১২৬/সি"
            # Bangla 3-part slash - e.g., "৬০/১/এ" - capture full
            (r'([\d০-৯]+[/\-][\d০-৯]+[/\-][\u0980-\u09FF]+)(?=\s*[,\(\)]|\s|$)', 0.95),  # Capture "৬০/১/এ"
            # Bangla বাসা- pattern - e.g., "বাসা-১৫৬" - capture full
            (r'((?:বাসা|বাড়ি)[\s-]+[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.95),  # Capture "বাসা-১৫৬"
            # Bangla হোল্ডিং pattern - e.g., "হোল্ডিং ১৩" - capture full
            (r'((?:হোল্ডিং|হোল্ডিং)[\s]+[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.95),  # Capture "হোল্ডিং ১৩"
            # Bangla বিল্ডিং নম্বর pattern - e.g., "বিল্ডিং নম্বর ২৯" - capture full
            (r'((?:বিল্ডিং|বিল্ডিং)[\s]+(?:নম্বর|নং|নাম্বার)[\s]*[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.95),  # Capture "বিল্ডিং নম্বর ২৯"
            # House number after flat number in Bangla (e.g., "ফ্ল্যাট নং- এ ৫, ৩৭২" → extract "৩৭২")
            (r'(?:ফ্ল্যাট|ফ্ল্যাট)[\s]+(?:নং|নাম্বার|নম্বর|:|-)[\s-]*[এআইঈউঊঋএঐওঔ]?[\s-]*[\d০-৯]+[\s]*,[\s]*([\d০-৯]+)', 0.95),
            (r'(?:বাড়ি|বাসা|বাড়ী|বাসা|ঘর)[\s]*(?:নং|নাম্বার|নম্বর|:)?[\s]*([\d০-৯]+)', 0.95),
            (r'(?:বাড়ি|বাসা)[\s]*([\d০-৯]+[a-zA-Z]?[/\-][\d০-৯]+[a-zA-Z]?)', 0.93),
        ]
        
        # POSITIONAL PATTERNS (70-95% confidence)
        # Patterns at the very start of address (before House, Road, etc.)
        self.positional_patterns = [
            # Standalone number at start followed by slash pattern (e.g., "215 2/3 Abedin Kibria House")
            (r'^(\d{1,4})\s+\d+[/\-]\d+.*?(?:house|home|bari|basha|building)', 0.95),
            # Standalone number at start followed by slash (e.g., "215 2/3" - prioritize standalone number)
            (r'^(\d{3,4})\s+\d+[/\-]\d+', 0.93),
            
            # Standalone number at start before building/villa name - e.g., "19 Bikrampur Villa", "49 Prominent Garden"
            (r'^(\d{1,3}[a-zA-Z]?)\s+[A-Z][a-z]+', 0.90),
            # Number after flat number (e.g., "Flat No- A 5, 372" → extract "372")
            (r'(?:flat|apartment)[\s]+(?:no\.?|number|#|:|-)[\s-]*[a-zA-Z]?[\s-]*\d+[\s]*,[\s]*(\d{1,4})(?=\s*[,\(\)]|\s|$)', 0.95),
            # Comma-separated house numbers at start (e.g., "367, 368, North Shajahanpur")
            (r'^(\d{1,4}[\s]*,[\s]*\d{1,4})\s*[,\(]', 0.95),
            # Range patterns at start (e.g., "177-78, Malibagh")
            (r'^(\d{1,4}[\s]*[-][\s]*\d{1,4})\s*[,\(]', 0.95),
            # At start, before "House" keyword (e.g., "1/A House")
            (r'^(\d{1,4}[a-zA-Z]?[/\-][A-Za-z]+)\s+(?:house|home|road|street)', 0.92),
            (r'^(\d{1,4}[a-zA-Z]?[/\-]\d+[a-zA-Z]?)\s+(?:house|home|road|street)', 0.92),
            # Standard positional patterns
            (r'^(\d{1,4}[a-zA-Z]?[/\-]\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?)\s*[,\(]', 0.92),
            (r'^(\d{1,4}[a-zA-Z]?[/\-]\d+[a-zA-Z]?)\s*[,\(]', 0.90),
            (r'^(\d{1,4}[a-zA-Z]?)\s*[,\(]', 0.85),
        ]
        
    def _setup_exclusions(self):
        """Setup exclusion patterns"""
        self.institutional_keywords = {
            'university', 'college', 'hospital', 'school', 'bank', 'office',
            'company', 'corporation', 'limited', 'ltd', 'pvt', 'government'
        }
        
        self.commercial_prefixes = {'plot', 'sector', 'block', 'floor', 'flat', 'apartment', 'unit'}
        
        self.invalid_patterns = [
            r'^\d{4,}$',  # Too many digits (likely postal code)
            r'^[01]$',    # Just 0 or 1
        ]
        
    def _setup_bangla_mappings(self):
        """Setup Bangla to English number mappings"""
        self.bangla_to_english = {
            '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4',
            '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'
        }
        
    def _bangla_to_english_number(self, text: str) -> str:
        """Convert Bangla numerals to English"""
        for bangla, english in self.bangla_to_english.items():
            text = text.replace(bangla, english)
        return text
        
    def _is_institutional(self, address: str) -> bool:
        """Check if address is institutional"""
        address_lower = address.lower()
        institutional_count = sum(1 for keyword in self.institutional_keywords if keyword in address_lower)
        return institutional_count >= 2
        
    def _is_road_goli_number(self, number: str, address: str, match_pos: int) -> bool:
        """
        Check if extracted number is actually a road/goli/ward number
        Examples: "2 No. Road", "3 No Goli", "6no Kotowali Road"
        """
        # Check what comes after the match
        if match_pos < len(address):
            after_match = address[match_pos:].strip()
            
            # Pattern: "X No. Road/Goli/Ward/etc."
            # Check if followed by "No." or "No" or "no" and then a location type
            location_keywords = [
                'road', 'goli', 'ward', 'gate', 'checkpost', 'rail', 'kotowali',
                'sher shah', 'mp', 'councillor', 'sector', 'thana', 'upazila'
            ]
            
            # Pattern 1: "X No. Road" or "X No Road"
            if re.match(r'^no\.?\s+\w+', after_match, re.IGNORECASE):
                # Check if any location keyword follows
                after_no = after_match.lower()
                for keyword in location_keywords:
                    if keyword in after_no[:50]:  # Check first 50 chars
                        return True
            
            # Pattern 2: Just number at start like "2 No. Road" (already extracted "2")
            # The number itself might be valid, check context before it in address
            # If address starts with this pattern, it's likely a road number
            if match_pos <= 5:  # Number is at/near the start
                # Check if address starts with pattern like "2 No. Road"
                start = address[:50].lower()
                if re.search(r'^\d+\s*no\.?\s+(' + '|'.join(location_keywords) + ')', start):
                    return True
        
        # Check if the number appears in context like "Basa X" pattern
        # If we find "Basa" or "Basha" before the number, it IS a house number
        before_match = address[:match_pos].lower()
        if 'basa' in before_match or 'basha' in before_match or 'house' in before_match:
            # Check if it's close to the number (within last 20 chars)
            if any(word in before_match[-20:] for word in ['basa', 'basha', 'house']):
                return False  # Not a road number, it's a house number
        
        return False
    
    def _is_postal_code(self, house_number: str, address: str, match_start: int, match_end: int) -> bool:
        """
        STRICT POSTAL CODE DETECTION - Completely exclude postal codes from house numbers
        Bangladeshi postal codes are typically 4-digit numbers (1000-9999)
        """
        # EXCEPTION: If it's part of a Holding/Building/House/Plot pattern, it's NOT a postal code
        before_match = address[:match_start].lower()
        if re.search(r'(?:holding|building|house|home|plot|basa|basha)[\s]+(?:no\.?|number|#)[\s-]*', before_match[-30:], re.IGNORECASE):
            return False  # It's a house/building/holding number, not postal code
        
        # EXCEPTION: If it's a standalone number before a location name (e.g., "72 Dilkusha"), it's NOT a postal code
        remaining = address[match_end:].strip()
        if remaining and re.match(r'^[A-Z][a-z]+', remaining):
            # Number is followed by a capitalized word (location name), likely house number
            return False
        
        # EXCEPTION: If it's part of a Holding/Building/House/Plot pattern, it's NOT a postal code
        before_match = address[:match_start].lower()
        if re.search(r'(?:holding|building|house|home|plot|basa|basha)[\s]+(?:no\.?|number|#)[\s-]*', before_match[-30:], re.IGNORECASE):
            return False  # It's a house/building/holding number, not postal code
        
        # EXCEPTION: If it's a standalone number before a location name (e.g., "72 Dilkusha"), it's NOT a postal code
        remaining = address[match_end:].strip()
        if remaining and re.match(r'^[A-Z][a-z]+', remaining):
            # Number is followed by a capitalized word (location name), likely house number
            return False
        
        # Check if it's a 4-digit number (typical postal code)
        if re.match(r'^\d{4}$', house_number):
            # Check if it appears after location name or at end of address
            remaining = address[match_end:].strip()
            before_match = address[:match_start].lower()
            
            # Location keywords that typically precede postal codes
            location_keywords = [
                'dhaka', 'chittagong', 'sylhet', 'rajshahi', 'khulna', 'barisal', 
                'rangpur', 'mymensingh', 'comilla', 'cox', 'bazar', 'sadar'
            ]
            
            # Check if location name appears before the number
            for loc in location_keywords:
                if loc in before_match[-30:]:  # Last 30 chars before match
                    return True  # Likely postal code
            
            # Check if at end of address (last 20% of address)
            if match_end > len(address) * 0.8:
                return True  # Likely postal code
            
            # Check if followed by parentheses or nothing significant
            if remaining and len(remaining) < 10:
                return True  # Likely postal code
        
        # Check for Banglish patterns with 4-digit numbers (ka 1216, ka-1207, etc.)
        if re.match(r'^(?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s-]*\d{4}$', house_number, re.IGNORECASE):
            # This is STRICTLY a postal code pattern
            remaining = address[match_end:].strip()
            before_match = address[:match_start].lower()
            
            # Check if location name appears before
            location_keywords = [
                'dhaka', 'chittagong', 'sylhet', 'rajshahi', 'khulna', 'barisal', 
                'rangpur', 'mymensingh', 'comilla', 'cox', 'bazar', 'sadar'
            ]
            
            for loc in location_keywords:
                if loc in before_match[-30:]:
                    return True  # Postal code
            
            # Check if at end of address
            if match_end > len(address) * 0.7:
                return True  # Postal code
            
            # Check if there's a house pattern earlier (should prioritize that)
            if re.search(r'(?:house|home|hous|building|bldg|plot|holding)[\s]+', address[:match_start], re.IGNORECASE):
                return True  # There's a house pattern earlier, this is postal code
        
        # Check for patterns like "Dhaka-1216" or "Dhaka 1216"
        if re.match(r'^\d{4}$', house_number):
            # Check context around the match
            context_before = address[max(0, match_start-20):match_start].lower()
            context_after = address[match_end:min(len(address), match_end+20)].lower()
            
            # If preceded by location name or dash
            if re.search(r'(dhaka|chittagong|sylhet|rajshahi|khulna|barisal|rangpur|mymensingh)[\s-]*$', context_before):
                return True  # Postal code
        
        return False
    
    def _is_banglish_in_location_name(self, house_number: str, address: str, match_start: int) -> bool:
        """
        Check if Banglish pattern is part of a location name (e.g., "Nikunja 2" should not extract "ja 2")
        """
        # Check if Banglish pattern matches
        if re.match(r'^(?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]+[\d০-৯]+', house_number, re.IGNORECASE):
            # Get context before the match (wider context to catch location names)
            context_before = address[max(0, match_start-30):match_start].lower()
            
            # Extract the Banglish letter(s) from house number
            banglish_match = re.match(r'^((?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch))', house_number, re.IGNORECASE)
            if banglish_match:
                banglish_letters = banglish_match.group(1).lower()
                
                # Common location names that might contain these letters
                # Check if the Banglish letters are part of a longer word (location name)
                location_patterns = [
                    r'nikunja', r'banani', r'gulshan', r'dhanmondi', r'uttara', r'mirpur',
                    r'khilkhet', r'rampura', r'bashundhara', r'baridhara', r'tejgaon',
                    r'mohammadpur', r'wari', r'old\s+dhaka', r'new\s+market', r'farmgate',
                    r'bonosree', r'banasree', r'khilgaon', r'rampura', r'bashundhara'
                ]
                
                # Check if any location pattern appears before the Banglish match
                for pattern in location_patterns:
                    if re.search(pattern, context_before, re.IGNORECASE):
                        # Check if the Banglish letters are actually part of this location name
                        location_match = re.search(pattern, context_before, re.IGNORECASE)
                        if location_match:
                            location_word = location_match.group(0).lower()
                            # If Banglish letters are part of the location word, it's a location name
                            if banglish_letters in location_word and len(location_word) > len(banglish_letters):
                                return True  # Banglish is part of location name
        
        return False
    
    def _is_banglish_part_of_word(self, house_number: str, address: str, match_start: int) -> bool:
        """
        Check if Banglish pattern is part of a word (e.g., "Building-2" should not extract "g-2")
        """
        # Check if Banglish pattern matches
        banglish_match = re.match(r'^((?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch))', house_number, re.IGNORECASE)
        if banglish_match:
            banglish_letters = banglish_match.group(1).lower()
            
            # Simple check: if character before the Banglish letter is a letter, it's part of a word
            if match_start > 0:
                char_before = address[match_start - 1]
                if char_before.isalpha():
                    # The Banglish letter is part of a word (like "Building" -> "g")
                    return True
            
            # Also check if it's part of common words
            context_before = address[max(0, match_start-30):match_start].lower()
            word_patterns = [
                r'building', r'housing', r'garage', r'garden', r'gate', r'ground',
                r'chamber', r'channel', r'church', r'chowk', r'chowdhury',
                r'khana', r'khan', r'khal', r'khulna', r'kolkata',
                r'jame', r'jamuna', r'jahan', r'jahanpur', r'jheel',
                r'goli', r'gulshan', r'gulistan', r'gulshan', r'gulisthan'
            ]
            
            for pattern in word_patterns:
                if re.search(pattern, context_before, re.IGNORECASE):
                    return True
        
        return False
    
    def _validate_house_number(self, number: str) -> bool:
        """Validate extracted house number"""
        if not number or len(number) > 30:
            return False
        for pattern in self.invalid_patterns:
            if re.match(pattern, number):
                return False
        return True
        
    def extract(self, address: str) -> HouseNumberResult:
        """Extract house number from address"""
        if not address:
            return HouseNumberResult("", 0.0, ExtractionMethod.NOT_FOUND, address, "Empty address")
            
        original_address = address
        # Store original for Bangla pattern preservation
        original_address_for_bangla = address
        address = self._bangla_to_english_number(address)
        
        # Skip institutional addresses
        if self._is_institutional(address):
            return HouseNumberResult("", 0.0, ExtractionMethod.INSTITUTIONAL, original_address, "Institutional address")
        
        # Try patterns in order of confidence
        # IMPORTANT: Collect all matches first, then prioritize best match
        # Order matters: explicit house patterns (including Banglish) should be checked before slash patterns
        all_patterns = [
            (self.positional_patterns, ExtractionMethod.POSITIONAL),
            (self.explicit_house_patterns, ExtractionMethod.EXPLICIT_HOUSE),  # Includes Banglish patterns
            (self.slash_patterns, ExtractionMethod.SLASH_FORMAT),
            (self.contextual_patterns, ExtractionMethod.CONTEXTUAL),
            (self.bangla_patterns, ExtractionMethod.BANGLA_PATTERN),
        ]
        
        all_matches = []
        
        for patterns, method in all_patterns:
            for pattern, confidence in patterns:
                # For Bangla patterns, match against original address
                search_text = original_address_for_bangla if method == ExtractionMethod.BANGLA_PATTERN else address
                match = re.search(pattern, search_text, re.IGNORECASE)
                if match:
                    house_number = match.group(1).strip()
                    
                    # Clean up
                    house_number = house_number.rstrip(',.')
                    
                    # For Bangla patterns, preserve original format
                    if method == ExtractionMethod.BANGLA_PATTERN:
                        # Try to get the original Bangla format from original_address
                        original_match = re.search(pattern, original_address_for_bangla, re.IGNORECASE)
                        if original_match:
                            house_number = original_match.group(1).strip()
                            house_number = house_number.rstrip(',.')
                    
                    # Check if comma-separated pattern is actually valid (not part of location name)
                    # E.g., "376, 60" in "Building No 376, 60 Feet" - "60" is part of "60 Feet" road name
                    skip_match = False
                    if re.match(r'^\d+[\s]*,[\s]*\d+$', house_number):
                        match_end_pos = match.end()
                        if match_end_pos < len(address):
                            remaining = address[match_end_pos:].strip()
                            # Check if second number is followed by location keywords
                            location_keywords = ['feet', 'road', 'street', 'lane', 'avenue', 'goli', 'bazar', 
                                                'market', 'moholla', 'para', 'block', 'sector', 'mollar', 'mor']
                            remaining_lower = remaining.lower()
                            for keyword in location_keywords:
                                if remaining_lower.startswith(keyword) or f' {keyword}' in remaining_lower[:20]:
                                    # Second number is part of location name, skip this match
                                    skip_match = True
                                    break
                    
                    if skip_match:
                        continue
                    
                    # Post-processing: Check if extracted number has space + letter that's part of excluded word
                    # E.g., "144/6 S" from "144/6 Staff" → remove S → "144/6"
                    # But keep "27/2 C" from "27/2 C Moneshwar" → keep C → "27/2 C"
                    if ' ' in house_number:
                        parts = house_number.rsplit(' ', 1)
                        if len(parts) == 2 and len(parts[1]) == 1 and parts[1].isupper():
                            # Has space + single capital letter
                            letter = parts[1]
                            # Check what comes immediately after the match in original address
                            match_end_pos = match.end()
                            if match_end_pos < len(address):
                                remaining = address[match_end_pos:]
                                # If next chars (after any whitespace) continue the letter as a word, it's excluded
                                next_chars = remaining.lstrip()
                                if next_chars and next_chars[0].islower():
                                    # Letter is followed by lowercase = part of word (e.g., "Staff")
                                    # Check if it's an excluded word
                                    for excluded_word in self.excluded_words:
                                        if (letter + next_chars[:len(excluded_word)-1]).lower() == excluded_word.lower():
                                            # Remove the letter
                                            house_number = parts[0]
                                            break
                    
                    # Validate house number
                    if not self._validate_house_number(house_number):
                        continue
                    
                    # Get match positions
                    match_start_pos = match.start()
                    match_end_pos = match.end()
                    
                    # STRICT POSTAL CODE VALIDATION - Completely exclude postal codes
                    if self._is_postal_code(house_number, address, match_start_pos, match_end_pos):
                        continue  # Skip postal codes - STRICTLY PROHIBITED
                    
                    # Check if Banglish pattern is part of location name (e.g., "Nikunja 2" should not extract "ja 2")
                    if self._is_banglish_in_location_name(house_number, address, match_start_pos):
                        continue  # Skip - Banglish is part of location name
                    
                    # Check if Banglish pattern is part of a word (e.g., "Building-2" should not extract "g-2")
                    if self._is_banglish_part_of_word(house_number, address, match_start_pos):
                        continue  # Skip - Banglish is part of word
                    
                    # Check if comma-separated pattern has flat number as first part (e.g., "5, 372" where 5 is flat number)
                    # In this case, prefer just the second number (372) as house number
                    if re.match(r'^[\d০-৯]+[\s]*,[\s]*[\d০-৯]+$', house_number):
                        # Check if first number is a flat number (English or Bangla)
                        before_match = address[:match_start_pos]
                        # Check for English flat
                        if re.search(r'flat[\s]+(?:no\.?|number|#|:|-)[\s-]*[a-z]?[\s-]*[\d০-৯]+', before_match[-30:], re.IGNORECASE):
                            # First number is a flat number, extract only second number
                            parts = house_number.split(',')
                            if len(parts) == 2:
                                house_number = parts[1].strip()  # Use second number only
                        # Check for Bangla flat (ফ্ল্যাট)
                        elif 'ফ্ল্যাট' in before_match[-30:]:
                            # First number is a flat number, extract only second number
                            parts = house_number.split(',')
                            if len(parts) == 2:
                                house_number = parts[1].strip()  # Use second number only
                                # Convert Bangla numerals to English
                                house_number = self._bangla_to_english_number(house_number)
                    
                    # Advanced AI: Check if this is actually a road/goli/ward number (not house number)
                    # This prevents false positives like "2 No. Road", "3 No Goli", "6no Kotowali Road"
                    if self._is_road_goli_number(house_number, address, match.end()):
                        # This is a road/goli number, skip it
                        continue
                    
                    # Store match for later prioritization
                    all_matches.append({
                        'house_number': house_number,
                        'confidence': confidence,
                        'method': method,
                        'pattern': pattern,
                        'match_start': match.start(),
                        'match_end': match.end(),
                    })
        
        if not all_matches:
            return HouseNumberResult("", 0.0, ExtractionMethod.NOT_FOUND, original_address, "No pattern matched")
        
        # Filter: If explicit house pattern or slash pattern appears early, remove Banglish patterns that appear later (likely postal codes)
        early_house_pattern = None
        early_slash_pattern = None
        for match in all_matches:
            pattern = match['pattern']
            method = match['method']
            # Check for explicit house patterns (House 8+9, House 48 & 52, House No. 16, House 20, etc.)
            if method == ExtractionMethod.EXPLICIT_HOUSE:
                # Check address context around match for house keyword (include match area)
                context_around = address[max(0, match['match_start']-10):match['match_end']+5].lower()
                if re.search(r'(?:house|home|hous|building|bldg|bari|basha)[\s]+', context_around, re.IGNORECASE):
                    if match['match_start'] < len(address) * 0.5:  # First 50% of address
                        early_house_pattern = match
                        break
            # Check for slash patterns
            elif method == ExtractionMethod.SLASH_FORMAT:
                if match['match_start'] < len(address) * 0.3:  # First 30% of address
                    early_slash_pattern = match
                    break
        
        # If there's an early house or slash pattern, filter out late Banglish patterns (postal codes or location names)
        if early_house_pattern or early_slash_pattern:
            filtered_matches = []
            early_pattern = early_house_pattern if early_house_pattern else early_slash_pattern
            for match in all_matches:
                pattern = match['pattern']
                method = match['method']
                # Skip Banglish patterns that appear after early house/slash pattern
                if method == ExtractionMethod.EXPLICIT_HOUSE:
                    # Check if house_number is a Banglish pattern (more reliable than pattern string)
                    if re.match(r'^(?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]+[\d০-৯]+', match['house_number'], re.IGNORECASE):
                        if match['match_start'] > early_pattern['match_start']:
                            # Skip all Banglish patterns after house pattern (postal codes or location names)
                            continue
                filtered_matches.append(match)
            all_matches = filtered_matches
        
        # Filter: If House/Building/Plot/Holding/Banglish patterns exist, remove Road/Flat patterns
        has_house_building_plot = False
        has_banglish_pattern = False
        has_slash_pattern = False
        has_standalone_number = False
        
        for match in all_matches:
            pattern = match['pattern']
            method = match['method']
            house_number = match['house_number']
            
            # Check for Banglish patterns (regardless of method)
            if re.match(r'^(?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]*[-/]?', house_number, re.IGNORECASE):
                has_banglish_pattern = True
            
            # Check for house/building/plot/holding in pattern or address context or house_number itself
            if method == ExtractionMethod.EXPLICIT_HOUSE:
                # Check if house_number itself contains house/building/plot/holding keywords (e.g., "Holding no-1924", "House No #17")
                if re.search(r'(?:house|home|hous|building|bldg|plot|holding)[\s]+(?:no\.?|number|#|:|-)', house_number.lower(), re.IGNORECASE):
                    has_house_building_plot = True
                # Check pattern
                elif re.search(r'(?:house|home|hous|building|bldg|plot|holding)[\s]+(?:no\.?|number|#|:|-)', pattern, re.IGNORECASE):
                    has_house_building_plot = True
                # Check address context
                else:
                    context_around = address[max(0, match['match_start']-15):match['match_end']+5].lower()
                    if re.search(r'(?:house|home|hous|building|bldg|plot|holding)[\s]+(?:no\.?|number|#|:|-)', context_around, re.IGNORECASE):
                        has_house_building_plot = True
            elif method == ExtractionMethod.SLASH_FORMAT:
                has_slash_pattern = True
            elif method == ExtractionMethod.POSITIONAL:
                # Check if it's a standalone number at start
                if match['match_start'] < len(address) * 0.2:  # First 20% of address
                    has_standalone_number = True
        
        # Check if only flat patterns exist (no house/building/plot/banglish/slash/standalone)
        # If we have house/building/plot/banglish/slash/standalone, we're good
        # Also check if any match is a Banglish pattern (double-check BEFORE "only flat" check)
        for match in all_matches:
            if re.match(r'^(?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]*[-/]?', match['house_number'], re.IGNORECASE):
                has_banglish_pattern = True
                break
        
        if not (has_house_building_plot or has_banglish_pattern or has_slash_pattern or has_standalone_number):
            
            # Check if ALL matches are flat patterns
            only_flat_patterns = True
            for match in all_matches:
                house_num = match['house_number']
                # Skip if it's a Banglish pattern (never a flat)
                if re.match(r'^(?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]*[-/]?', house_num, re.IGNORECASE):
                    only_flat_patterns = False
                    break
                # Skip if it's a house/building/plot pattern (never a flat)
                context_around_match = address[max(0, match['match_start']-15):match['match_end']+5].lower()
                if re.search(r'(?:house|home|hous|building|bldg|plot|holding)[\s-]+', context_around_match, re.IGNORECASE):
                    only_flat_patterns = False
                    break
                # Skip if it's a long slash pattern (likely house number like "365/2", not flat)
                if '/' in house_num and len(house_num) > 4 and re.match(r'^\d{3,}', house_num):
                    only_flat_patterns = False
                    break
                
                # Check if this is a flat pattern
                context_around = address[max(0, match['match_start']-25):match['match_end']+5].lower()
                before_match = address[:match['match_start']].lower()
                is_flat = False
                
                # Check if "flat" appears before the match
                if 'flat' in before_match[-25:]:
                    # Short slash patterns: 7/C, 8/A, 4-B, 10-C
                    if re.match(r'^\d{1,2}[/\-][A-Z]$', house_num, re.IGNORECASE) or re.match(r'^\d{1,2}[-][A-Z]$', house_num, re.IGNORECASE):
                        is_flat = True
                    # Letter + number patterns: G2, A8 (when after "flat")
                    elif re.match(r'^[A-Z]\d+$', house_num, re.IGNORECASE):
                        is_flat = True
                    # Number-letter patterns: 4-B (when after "flat")
                    elif re.match(r'^\d+[-][A-Z]$', house_num, re.IGNORECASE):
                        is_flat = True
                    # Standard flat pattern with "flat" keyword
                    elif re.search(r'flat[\s]+(?:no\.?|number|#|:|-|:)', context_around, re.IGNORECASE):
                        is_flat = True
                
                if not is_flat:
                    only_flat_patterns = False
                    break
            
            # If only flat patterns exist, return empty
            if only_flat_patterns:
                return HouseNumberResult("", 0.0, ExtractionMethod.NOT_FOUND, original_address, "Only flat number found, no house number")
        
        # Remove road/flat patterns if house/building/plot/banglish/slash exists
        if has_house_building_plot or has_banglish_pattern or has_slash_pattern or has_standalone_number:
            filtered_matches = []
            for match in all_matches:
                pattern = match['pattern']
                method = match['method']
                # Check if this is a flat pattern - STRICT DETECTION (100% EXCLUDE IF FLAT)
                is_flat = False
                house_num = match['house_number']
                context_around = address[max(0, match['match_start']-25):match['match_end']+5].lower()
                before_match = address[:match['match_start']].lower()
                
                # Check if "flat" appears before the match
                if 'flat' in before_match[-25:]:
                    # Short slash patterns: 7/C, 8/A, 4-B, 10-C (100% flat when after "flat")
                    if re.match(r'^\d{1,2}[/\-][A-Z]$', house_num, re.IGNORECASE) or re.match(r'^\d{1,2}[-][A-Z]$', house_num, re.IGNORECASE):
                        is_flat = True
                    # Letter + number patterns: G2, A8 (100% flat when after "flat")
                    elif re.match(r'^[A-Z]\d+$', house_num, re.IGNORECASE):
                        is_flat = True
                    # Number-letter patterns: 4-B (100% flat when after "flat")
                    elif re.match(r'^\d+[-][A-Z]$', house_num, re.IGNORECASE):
                        is_flat = True
                    # Standard flat pattern with "flat" keyword
                    elif re.search(r'flat[\s]+(?:no\.?|number|#|:|-|:)', context_around, re.IGNORECASE):
                        is_flat = True
                
                # Also check if pattern string contains flat keyword
                if re.search(r'flat[\s]+(?:no\.?|number|#|:|-|:)', pattern, re.IGNORECASE):
                    is_flat = True
                # Check if this is a Banglish pattern - PRESERVE IT (highest priority)
                is_banglish = re.match(r'^(?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]*[-/]?', match['house_number'], re.IGNORECASE)
                if is_banglish:
                    filtered_matches.append(match)
                    continue
                
                # STRICTLY EXCLUDE flat patterns (100% certainty) - check BEFORE house patterns
                # Skip flat patterns immediately if identified as 100% flat
                if is_flat:
                    continue
                
                # PRESERVE house/building/plot patterns - never filter them out
                # Check if house_number itself contains keywords (e.g., "Holding no-1924", "House No #17", "House 4/4")
                is_house_building_plot = False
                if re.search(r'(?:house|home|hous|building|bldg|plot|holding)[\s]+(?:no\.?|number|#|:|-|:)', house_num.lower(), re.IGNORECASE):
                    is_house_building_plot = True
                # Also check for house- pattern in house_number (House-12B, House-303, Home-1342)
                if re.search(r'(?:house|home)[\s-]+', house_num.lower(), re.IGNORECASE):
                    is_house_building_plot = True
                # Check address context
                if not is_house_building_plot:
                    context_around_match = address[max(0, match['match_start']-15):match['match_end']+5].lower()
                    if re.search(r'(?:house|home|hous|building|bldg|plot|holding)[\s]+(?:no\.?|number|#|:|-|:)', context_around_match, re.IGNORECASE):
                        is_house_building_plot = True
                    # Also check for house- pattern (House-12B, House-303)
                    if re.search(r'house[\s-]+', context_around_match, re.IGNORECASE):
                        is_house_building_plot = True
                if is_house_building_plot:
                    filtered_matches.append(match)
                    continue
                
                # PRESERVE slash patterns that are NOT flat patterns (e.g., "365/2" is house number, not flat)
                # If it's a slash pattern and NOT a flat pattern, preserve it
                if method == ExtractionMethod.SLASH_FORMAT and not is_flat:
                    # Check if it's a house number pattern (e.g., "365/2", "14/1")
                    # These are typically 3+ digit numbers with slash, not short patterns like "7/C"
                    if re.match(r'^\d{3,}[/\-]\d+', match['house_number']):
                        filtered_matches.append(match)
                        continue
                    # Also preserve if it's a longer pattern (not a short flat pattern)
                    if len(match['house_number']) > 4 and '/' in match['house_number']:
                        filtered_matches.append(match)
                        continue
                    # Preserve if it appears at the start of address (likely house number)
                    if match['match_start'] < len(address) * 0.2:  # First 20% of address
                        filtered_matches.append(match)
                        continue
                
                # Check if this is a road pattern
                is_road = False
                # Check address context for road keyword
                context_around = address[max(0, match['match_start']-20):match['match_end']+5].lower()
                if re.search(r'road[\s]+(?:no\.?|number|#|:|-|:)', context_around, re.IGNORECASE):
                    is_road = True
                # Also check if slash/contextual pattern appears after "road" keyword
                if method in [ExtractionMethod.SLASH_FORMAT, ExtractionMethod.CONTEXTUAL]:
                    before_match = address[:match['match_start']].lower()
                    # Check if "road" appears in the last 20 chars before match
                    if 'road' in before_match[-20:]:
                        # Check if it's followed by "no", "number", "#", ":", or "-"
                        if re.search(r'road[\s]+(?:no\.?|number|#|:|-)?[\s-]*', before_match[-20:], re.IGNORECASE):
                            is_road = True
                # Skip road patterns if house/building/plot/banglish exists (STRICTLY EXCLUDE ROAD NUMBERS)
                if is_road and (has_house_building_plot or has_banglish_pattern):
                    continue
                # Skip road/flat patterns in pattern string
                if re.search(r'(?:road|flat|apartment|lift|floor)[\s]+(?:no\.?|number|#|:|-|:)', pattern, re.IGNORECASE):
                    continue
                # Skip patterns that match road numbers (e.g., "Road No. 6/A", "Road-14/1")
                if re.search(r'road[\s]+(?:no\.?|number|#|:|-)[\s-]*\d+', address[match['match_start']:match['match_end']+20], re.IGNORECASE):
                    continue
                filtered_matches.append(match)
            all_matches = filtered_matches
        
        # If all matches were filtered out, return empty
        if not all_matches:
            return HouseNumberResult("", 0.0, ExtractionMethod.NOT_FOUND, original_address, "All matches filtered out (likely only flat/road numbers)")
        
        # Prioritize matches: prefer House/Building/Plot/Holding over Road/Flat
        def get_priority(match):
            hn = match['house_number']
            pattern = match['pattern']
            method = match['method']
            priority = 0
            
            # HIGHEST PRIORITY: House/Building/Plot/Holding patterns
            # Check address context for building/house keywords
            context_around = address[max(0, match['match_start']-15):match['match_end']+5].lower()
            has_building = re.search(r'building[\s]+(?:no\.?|number|#|:|-|:)', context_around, re.IGNORECASE)
            has_house = re.search(r'house[\s]+(?:no\.?|number|#|:|-|:)', context_around, re.IGNORECASE)
            has_house_dash = re.search(r'house[\s-]+', context_around, re.IGNORECASE)  # House-12B, House-303
            has_plot = re.search(r'plot[\s]+(?:no\.?|number|#|:|-|:)', context_around, re.IGNORECASE)
            
            if method == ExtractionMethod.EXPLICIT_HOUSE:
                if has_building or has_house or has_house_dash or has_plot or re.search(r'(?:house|home|hous|building|bldg|plot|holding)[\s]+(?:no\.?|number|#|:|-)', pattern, re.IGNORECASE):
                    priority += 3500  # Highest priority for explicit house/building/plot/holding
                elif re.search(r'(?:house|home|hous|building|bldg|plot|holding)[\s-]+', pattern, re.IGNORECASE):
                    priority += 2800  # House-303, Building-2, etc.
                elif re.match(r'^(?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]*[-/]?', match['house_number'], re.IGNORECASE):
                    priority += 3000  # Banglish alphabet patterns (Kha/50, JA-10/1/A, etc.) - HIGH PRIORITY
                else:
                    priority += 2000  # Other explicit house patterns
            
            # Check if this is a road/flat pattern (lower priority)
            # Check both pattern and address context
            context_around = address[max(0, match['match_start']-15):match['match_end']+5].lower()
            before_match_priority = address[:match['match_start']].lower()
            is_flat = re.search(r'flat[\s]+(?:no\.?|number|#|:|-|:)', context_around, re.IGNORECASE)
            # Also check if pattern appears after "flat" keyword (letter+number like G2, or short patterns)
            if 'flat' in before_match_priority[-25:]:
                house_num_priority = match['house_number']
                # Letter + number patterns: G2, A8 (100% flat when after "flat")
                if re.match(r'^[A-Z]\d+$', house_num_priority, re.IGNORECASE):
                    is_flat = True
                # Short slash patterns: 7/C, 8/A, 4-B (100% flat when after "flat")
                elif re.match(r'^\d{1,2}[/\-][A-Z]$', house_num_priority, re.IGNORECASE):
                    is_flat = True
                # Number-letter patterns: 4-B (100% flat when after "flat")
                elif re.match(r'^\d+[-][A-Z]$', house_num_priority, re.IGNORECASE):
                    is_flat = True
            
            is_road = re.search(r'road[\s]+(?:no\.?|number|#|:|-|:)', context_around, re.IGNORECASE)
            # Also check if slash/contextual pattern appears after "road" keyword
            if method in [ExtractionMethod.SLASH_FORMAT, ExtractionMethod.CONTEXTUAL]:
                before_match = address[:match['match_start']].lower()
                if 'road' in before_match[-20:]:
                    if re.search(r'road[\s]+(?:no\.?|number|#|:|-)?[\s-]*', before_match[-20:], re.IGNORECASE):
                        is_road = True
            
            # Check if house/building/plot exists in address (for penalty calculation)
            address_lower = address.lower()
            has_house_in_address = re.search(r'house[\s-]+', address_lower, re.IGNORECASE)
            has_building_in_address = re.search(r'building[\s-]+', address_lower, re.IGNORECASE)
            has_plot_in_address = re.search(r'plot[\s]+', address_lower, re.IGNORECASE)
            
            if is_flat or re.search(r'(?:road|flat|apartment|lift|floor)[\s]+(?:no\.?|number|#|:|-|:)', pattern, re.IGNORECASE):
                priority -= 2000  # Much lower priority for road/flat
            if is_road:
                priority -= 1500  # Lower priority for road
                # EXTRA penalty if house/building/plot exists in address
                if has_house_in_address or has_building_in_address or has_plot_in_address:
                    priority -= 2000  # Very low priority for road when house/building/plot exists
            
            # Prioritize standalone numbers at start (e.g., "215" in "215 2/3")
            if method == ExtractionMethod.POSITIONAL:
                if match['match_start'] < len(address) * 0.1:  # First 10% of address
                    # Check if it's a standalone number (not part of slash pattern)
                    if re.match(r'^\d{3,4}$', match['house_number']):
                        priority += 2500  # Very high priority for standalone numbers at start
            
            # Prioritize slash patterns that appear earlier in address
            # If there's a slash pattern at start and Banglish pattern later, prefer slash
            if method == ExtractionMethod.SLASH_FORMAT:
                if match['match_start'] < len(address) * 0.3:  # First 30% of address
                    priority += 2000  # Very high priority for early slash patterns
            elif method == ExtractionMethod.EXPLICIT_HOUSE:
                # If Banglish pattern appears late in address, might be postal code
                if re.match(r'^(?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s-]*\d{4}$', match['house_number'], re.IGNORECASE):
                    # This is a postal code pattern (4 digits) - STRICTLY PROHIBITED
                    priority -= 5000  # Very low priority for postal codes
                elif re.search(r'(?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]*[-/]?', pattern, re.IGNORECASE):
                    # Check if there's an early slash pattern (should prefer that)
                    has_early_slash = any(m['method'] == ExtractionMethod.SLASH_FORMAT and m['match_start'] < len(address) * 0.3 for m in all_matches)
                    if has_early_slash and match['match_start'] > len(address) * 0.2:
                        priority -= 2000  # Much lower priority if early slash pattern exists
                    elif match['match_start'] > len(address) * 0.6:  # Last 40% of address
                        priority -= 500  # Lower priority for late Banglish patterns (might be postal code)
            
            # High priority: Range patterns (177-78)
            if re.search(r'\d+[\s]*[-][\s]*\d+', hn):
                priority += 1000  # Range pattern
            elif re.search(r'\d+[\s]*,[\s]*\d+', hn):
                # Comma-separated pattern
                priority += 1000  # Comma-separated pattern
            
            # Lower priority: Simple single letter patterns (9A)
            if re.match(r'^\d+[a-zA-Z]$', hn):
                priority -= 500  # Simple letter suffix
            
            # Add confidence as secondary priority
            priority += match['confidence'] * 100
            
            # Add position bonus (earlier is better)
            position_bonus = (1.0 - (match['match_start'] / len(address))) * 100
            priority += position_bonus
            
            return priority
        
        # Sort by priority (highest first)
        all_matches.sort(key=get_priority, reverse=True)
        
        # Return the best match
        best_match = all_matches[0]
        return HouseNumberResult(
            house_number=best_match['house_number'],
            confidence=best_match['confidence'],
            method=best_match['method'],
            original=original_address,
            reason=f"Matched pattern: {best_match['pattern']}"
        )


# ============================================================================
# FILE OPERATIONS
# ============================================================================

def load_json(filepath: Path) -> List[Dict]:
    """Load JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath: Path, data: List[Dict]) -> None:
    """Save JSON file"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================================
# COMMAND: EXTRACT (Single Address)
# ============================================================================

def cmd_extract(address: str, show_details: bool = False):
    """Extract house number from single address"""
    print("=" * 80)
    print("HOUSE NUMBER EXTRACTION")
    print("=" * 80)
    print()
    print(f"Address: {address}")
    print()
    
    extractor = AdvancedHouseNumberExtractor()
    result = extractor.extract(address)
    
    print(f"House Number:  {result.house_number or '(not found)'}")
    print(f"Confidence:    {result.confidence:.1%}")
    print(f"Method:        {result.method.value}")
    
    if show_details:
        print(f"Reason:        {result.reason}")
    
    print()
    return result


# ============================================================================
# COMMAND: PROCESS (Entire Dataset)
# ============================================================================

def cmd_process(confidence: float = 0.70, input_file: str = None, output_file: str = None):
    """Process entire dataset"""
    if input_file is None:
        input_file = 'data/json/real-customer-address-dataset.json'
    if output_file is None:
        output_file = 'data/json/real-customer-address-dataset-processed.json'
    
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    print("=" * 80)
    print("PROCESSING DATASET")
    print(f"Confidence Threshold: {confidence:.0%}")
    print("=" * 80)
    print()
    
    print(f"📂 Loading dataset from: {input_path}")
    data = load_json(input_path)
    print(f"   ✓ Loaded {len(data)} records")
    print()
    
    extractor = AdvancedHouseNumberExtractor(confidence_threshold=confidence)
    
    print("🔄 Processing records...")
    extracted_count = 0
    confidence_dist = {'>95': 0, '90-95': 0, '85-90': 0, '80-85': 0, '75-80': 0, '70-75': 0, '<70': 0}
    
    for i, record in enumerate(data, 1):
        if i % 100 == 0:
            print(f"   Processed {i}/{len(data)} records...")
        
        address = record.get('address', '')
        result = extractor.extract(address)
        
        if result.confidence >= confidence:
            record['components']['house_number'] = result.house_number
            extracted_count += 1
            
            # Track confidence distribution
            if result.confidence >= 0.95:
                confidence_dist['>95'] += 1
            elif result.confidence >= 0.90:
                confidence_dist['90-95'] += 1
            elif result.confidence >= 0.85:
                confidence_dist['85-90'] += 1
            elif result.confidence >= 0.80:
                confidence_dist['80-85'] += 1
            elif result.confidence >= 0.75:
                confidence_dist['75-80'] += 1
            elif result.confidence >= 0.70:
                confidence_dist['70-75'] += 1
            else:
                confidence_dist['<70'] += 1
        else:
            record['components']['house_number'] = ""
    
    print()
    print(f"💾 Saving to: {output_path}")
    save_json(output_path, data)
    print()
    
    # Statistics
    print("=" * 80)
    print("PROCESSING COMPLETE")
    print("=" * 80)
    print()
    print(f"Total Records:         {len(data)}")
    print(f"Extracted:             {extracted_count} ({extracted_count/len(data)*100:.1f}%)")
    print(f"Not Extracted:         {len(data) - extracted_count}")
    print()
    print("Confidence Distribution:")
    for range_name, count in confidence_dist.items():
        if count > 0:
            print(f"  {range_name:>10}:  {count:>4} records")
    print()


# ============================================================================
# COMMAND: SPLIT (By Confidence)
# ============================================================================

def cmd_split(input_file: str = None, output_dir: str = None):
    """Split dataset by confidence levels"""
    if input_file is None:
        input_file = 'data/json/real-customer-address-dataset.json'
    if output_dir is None:
        output_dir = 'data/json/processing/house'
    
    input_path = Path(input_file)
    output_path = Path(output_dir)
    
    print("=" * 80)
    print("SPLITTING DATASET BY CONFIDENCE")
    print("=" * 80)
    print()
    
    print(f"📂 Loading dataset...")
    data = load_json(input_path)
    print(f"   ✓ Loaded {len(data)} records")
    print()
    
    extractor = AdvancedHouseNumberExtractor()
    
    # Categories (with numbered prefixes for sorting)
    categories = {
        '1.excellent_95_100': (0.95, 1.00),
        '2.very_high_90_95': (0.90, 0.95),
        '3.high_85_90': (0.85, 0.90),
        '4.good_80_85': (0.80, 0.85),
        '5.medium_high_75_80': (0.75, 0.80),
        '6.medium_70_75': (0.70, 0.75),
        '7.acceptable_65_70': (0.65, 0.70),
        '8.low_below_65': (0.00, 0.65),
    }
    
    split_data = {cat: [] for cat in categories.keys()}
    split_data['no_house_number'] = []
    
    print("🔄 Categorizing records...")
    for i, record in enumerate(data, 1):
        if i % 100 == 0:
            print(f"   Processed {i}/{len(data)} records...")
        
        address = record.get('address', '')
        result = extractor.extract(address)
        
        if result.house_number and result.confidence >= 0.65:
            # Find appropriate category
            for cat_name, (min_conf, max_conf) in categories.items():
                if min_conf <= result.confidence < max_conf:
                    split_data[cat_name].append(record)
                    break
        else:
            split_data['no_house_number'].append(record)
    
    print()
    print("💾 Saving split datasets...")
    
    # Save each category
    for cat_name, records in split_data.items():
        if cat_name == 'no_house_number':
            cat_path = output_path / cat_name / 'data.json'
        else:
            cat_path = output_path / 'with_house_number' / cat_name / 'data.json'
        
        save_json(cat_path, records)
        print(f"   ✓ {cat_name}: {len(records)} records")
    
    print()
    print("=" * 80)
    print("SPLIT COMPLETE")
    print("=" * 80)
    print()


# ============================================================================
# COMMAND: REPROCESS (Specific Confidence Level)
# ============================================================================

def cmd_reprocess(confidence_level: str, base_dir: str = None):
    """Re-process specific confidence level"""
    if base_dir is None:
        base_dir = 'data/json/processing/house'
    
    data_path = Path(base_dir) / 'with_house_number' / confidence_level / 'data.json'
    
    if not data_path.exists():
        print(f"❌ Error: {data_path} not found")
        return
    
    # Confidence thresholds (with numbered prefixes for sorting)
    thresholds = {
        '1.excellent_95_100': 0.95,
        '2.very_high_90_95': 0.90,
        '3.high_85_90': 0.85,
        '4.good_80_85': 0.80,
        '5.medium_high_75_80': 0.75,
        '6.medium_70_75': 0.70,
        '7.acceptable_65_70': 0.65,
        '8.low_below_65': 0.60,
    }
    
    threshold = thresholds.get(confidence_level, 0.70)
    
    print("=" * 80)
    print(f"RE-PROCESSING: {confidence_level.upper()}")
    print(f"Threshold: {threshold:.0%}")
    print("=" * 80)
    print()
    
    print(f"📂 Loading data...")
    data = load_json(data_path)
    print(f"   ✓ Loaded {len(data)} records")
    print()
    
    extractor = AdvancedHouseNumberExtractor(confidence_threshold=threshold)
    
    print("🔄 Re-processing...")
    updated = 0
    
    for i, record in enumerate(data, 1):
        address = record.get('address', '')
        old_number = record['components'].get('house_number', '')
        
        result = extractor.extract(address)
        
        if result.confidence >= threshold and result.house_number != old_number:
            record['components']['house_number'] = result.house_number
            updated += 1
            if updated <= 10:
                print(f"   ✓ {old_number} → {result.house_number}")
    
    print()
    print(f"💾 Saving updates...")
    save_json(data_path, data)
    print()
    
    print("=" * 80)
    print(f"RE-PROCESSING COMPLETE")
    print("=" * 80)
    print()
    print(f"Total:    {len(data)} records")
    print(f"Updated:  {updated} records")
    print()


# ============================================================================
# COMMAND: SYNC (Update Main Dataset from Split)
# ============================================================================

def cmd_sync(confidence_level: str, main_file: str = None, split_dir: str = None):
    """Sync main dataset from split data"""
    if main_file is None:
        main_file = 'data/json/real-customer-address-dataset.json'
    if split_dir is None:
        split_dir = 'data/json/processing/house'
    
    main_path = Path(main_file)
    split_path = Path(split_dir) / 'with_house_number' / confidence_level / 'data.json'
    
    if not split_path.exists():
        print(f"❌ Error: {split_path} not found")
        return
    
    print("=" * 80)
    print(f"SYNCING FROM: {confidence_level}")
    print("=" * 80)
    print()
    
    print("📂 Loading datasets...")
    main_data = load_json(main_path)
    split_data = load_json(split_path)
    print(f"   ✓ Main: {len(main_data)} records")
    print(f"   ✓ Split: {len(split_data)} records")
    print()
    
    # Create mapping
    split_map = {}
    for record in split_data:
        address = record['address']
        house_number = record['components'].get('house_number', '')
        if house_number:
            split_map[address] = house_number
    
    print("🔄 Updating main dataset...")
    updated = 0
    
    for record in main_data:
        address = record['address']
        if address in split_map:
            old_number = record['components'].get('house_number', '')
            new_number = split_map[address]
            if old_number != new_number:
                record['components']['house_number'] = new_number
                updated += 1
                if updated <= 10:
                    print(f"   ✓ {old_number} → {new_number}")
    
    print()
    print(f"💾 Saving main dataset...")
    save_json(main_path, main_data)
    print()
    
    print("=" * 80)
    print("SYNC COMPLETE")
    print("=" * 80)
    print()
    print(f"Updated:  {updated} records")
    print()


# ============================================================================
# MAIN CLI
# ============================================================================

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Complete House Number Processor - All-in-One Solution',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Extract from single address:
    python3 house_number_processor.py extract "270/a Dhanmondi 15, Dhaka"
  
  Process entire dataset:
    python3 house_number_processor.py process --confidence 0.70
  
  Split dataset by confidence:
    python3 house_number_processor.py split
  
  Re-process specific level:
    python3 house_number_processor.py reprocess 2.very_high_90_95
  
  Sync main dataset:
    python3 house_number_processor.py sync 2.very_high_90_95
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract house number from address')
    extract_parser.add_argument('address', help='Address string')
    extract_parser.add_argument('--details', action='store_true', help='Show detailed information')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process entire dataset')
    process_parser.add_argument('--confidence', type=float, default=0.70, help='Confidence threshold (default: 0.70)')
    process_parser.add_argument('--input', help='Input file path')
    process_parser.add_argument('--output', help='Output file path')
    
    # Split command
    split_parser = subparsers.add_parser('split', help='Split dataset by confidence')
    split_parser.add_argument('--input', help='Input file path')
    split_parser.add_argument('--output', help='Output directory')
    
    # Reprocess command
    reprocess_parser = subparsers.add_parser('reprocess', help='Re-process confidence level')
    reprocess_parser.add_argument('level', help='Confidence level folder name')
    reprocess_parser.add_argument('--base-dir', help='Base split directory')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync main dataset from split')
    sync_parser.add_argument('level', help='Confidence level folder name')
    sync_parser.add_argument('--main-file', help='Main dataset file')
    sync_parser.add_argument('--split-dir', help='Split directory')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute command
    if args.command == 'extract':
        cmd_extract(args.address, args.details)
    elif args.command == 'process':
        cmd_process(args.confidence, args.input, args.output)
    elif args.command == 'split':
        cmd_split(args.input, args.output)
    elif args.command == 'reprocess':
        cmd_reprocess(args.level, args.base_dir)
    elif args.command == 'sync':
        cmd_sync(args.level, args.main_file, args.split_dir)


if __name__ == "__main__":
    main()

