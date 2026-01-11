#!/usr/bin/env python3
"""
Complete Flat Number Processor - All-in-One Solution
=====================================================

Single comprehensive script for Bangladeshi address flat number extraction,
processing, organization, and management.

Features:
    1. Extract flat numbers from addresses (Core Algorithm)
    2. Process entire dataset with confidence filtering
    3. Split dataset by confidence levels
    4. Re-process specific confidence folders
    5. Sync changes between split and main dataset

Usage:
    # Extract from single address
    python3 flat_number_processor.py extract "Flat No: 5A, House No: 24, Diamond Tower"
    
    # Process entire dataset
    python3 flat_number_processor.py process --confidence 0.70
    
    # Split dataset by confidence
    python3 flat_number_processor.py split
    
    # Re-process specific confidence level
    python3 flat_number_processor.py reprocess 2.very_high_90_95
    
    # Update main dataset from split
    python3 flat_number_processor.py sync 2.very_high_90_95

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
    EXPLICIT_FLAT = "explicit_flat"
    EXPLICIT_SUITE = "explicit_suite"
    EXPLICIT_APT = "explicit_apt"
    EXPLICIT_UNIT = "explicit_unit"
    EXPLICIT_FLOOR = "explicit_floor"
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
class FlatNumberResult:
    """Result of flat number extraction"""
    flat_number: str
    confidence: float
    method: ExtractionMethod
    original: str = ""
    reason: str = ""
    
    def __str__(self):
        return f"FlatNumber('{self.flat_number}', {self.confidence:.1%}, {self.method.value})"
    
    def to_dict(self) -> Dict:
        return {
            'flat_number': self.flat_number,
            'confidence': self.confidence,
            'method': self.method.value,
            'original': self.original,
            'reason': self.reason
        }


class AdvancedFlatNumberExtractor:
    """Advanced AI-Based Flat Number Extractor for Bangladeshi Addresses"""
    
    def __init__(self, preserve_format: bool = True, confidence_threshold: float = 0.70):
        self.preserve_format = preserve_format
        self.confidence_threshold = confidence_threshold
        self._setup_advanced_patterns()
        self._setup_exclusions()
        self._setup_bangla_mappings()
        
    def _setup_advanced_patterns(self):
        """Setup advanced extraction patterns"""
        
        # EXPLICIT FLAT PATTERNS (95-100% confidence)
        # CRITICAL: Most specific patterns FIRST, simple patterns LAST
        # Patterns must capture FULL flat number including suffixes like -C, /D, (A), (C)
        self.explicit_flat_patterns = [
            # Flat No # with dash/slash suffix - e.g., "Flat No # 10-C", "Flat No # 1/A" -> capture "10-C" or "1/A" (FULL)
            (r'(?:flat|flt)[\s]+(?:no\.?|number)[\s]*#[\s]*([A-Za-z]?[\d০-৯]+[/\-][A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 1.00),
            # Flat No # with letter+number - e.g., "Flat No # 5A", "Flat No # A5"
            (r'(?:flat|flt)[\s]+(?:no\.?|number)[\s]*#[\s]*([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 1.00),
            
            # Flat No. with dash suffix - e.g., "Flat No. 10-C", "Flat No: 10-C" -> capture "10-C" (FULL)
            (r'(?:flat|flt)[\s]+(?:no\.?|number|:)[\s-]*([\d০-৯]+[\s-]*[A-Za-z])(?=\s*[,\(\)]|\s|$)', 1.00),
            
            # Flat with dash and slash - e.g., "Flat-15/D" -> capture "15/D" (FULL)
            (r'(?:flat|flt)[\s-]+([\d০-৯]+[/][A-Za-z])(?=\s*[,\(\)]|\s|$)', 1.00),
            
            # Flat with dash and parentheses - e.g., "Flat-6(A)", "Flat - 8(C)" -> capture "6(A)", "8(C)" (FULL)
            (r'(?:flat|flt)[\s-]+([\d০-৯]+\([A-Za-z]\))(?=\s*[,\(\)]|\s|$)', 1.00),
            
            # Flat# with letter+number - e.g., "Flat#5A", "Flat#A5" - capture only number part
            (r'(?:flat|flt)[#][\s]*([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 1.00),
            # Flat# with letter-dash-number - e.g., "Flat#B-9"
            (r'(?:flat|flt)[#]([A-Za-z][\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),
            # Flat# with number - e.g., "Flat#5", "Flat#12" - capture only number part
            (r'(?:flat|flt)[#][\s]*([\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 1.00),
            # Flat# with space and letter-number - e.g., "Flat# A102"
            (r'(?:flat|flt)[#][\s]+([A-Za-z][\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),
            
            # NEW: Flat # with space before and after # - e.g., "Flat # 5A", "Flat # 7A" -> capture "5A", "7A"
            (r'(?:flat|flt)[\s]+#[\s]+([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 1.00),
            
            # NEW: Flat # with space before # but no space after # - e.g., "Flat #7B", "Flat #404" -> capture "7B", "404"
            (r'(?:flat|flt)[\s]+#([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 1.00),
            
            # NEW: Flat with colon pattern - e.g., "Flat: A4", "Flat: D5", "Flat: 9A", "Flat: 403", "Flat: 3/B", "Flat: 1/A", "Flat: D-8", "Flat: D-06"
            (r'(?:flat|flt)[\s]*:[\s]*([A-Za-z][\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),  # Letter-dash-number: "D-8", "D-06"
            (r'(?:flat|flt)[\s]*:[\s]*([A-Za-z]?[\d০-৯]{1,3}[/\-]?[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Other formats
            
            # NEW: Flat with parentheses after keyword - e.g., "(Flat 8C)", "Building (Flat 8C)"
            (r'\([\s]*(?:flat|flt)[\s]+([A-Za-z]?[\d০-৯]+[A-Za-z]?)[\s]*\)', 0.95),
            
            # NEW: Flat with dash and letter-number - e.g., "Flat-B3", "Flat-7C", "Flat-2C"
            (r'(?:flat|flt)[\s-]+([A-Za-z][\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),
            
            # NEW: Flat with dash and letter-dash-number - e.g., "Flat-G-6" -> capture "G-6"
            (r'(?:flat|flt)[\s-]+([A-Za-z][\s-]+[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),
            
            # NEW: Flat with dash and space then letter-slash-number - e.g., "Flat- B/7" -> capture "B/7"
            (r'(?:flat|flt)[\s-]+[\s]*([A-Za-z][/][\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),
            
            # NEW: Flat with dash and letter-space-number - e.g., "Flat-A 1" -> capture "A 1"
            (r'(?:flat|flt)[\s-]+([A-Za-z][\s]+[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),
            
            # NEW: Flat with dash and letter-slash-number - e.g., "Flat-C/6" -> capture "C/6"
            (r'(?:flat|flt)[\s-]+([A-Za-z][/][\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),
            
            # NEW: Flat with space and letter-number-slash-letter - e.g., "Flat L8/G" -> capture "L8/G"
            (r'(?:flat|flt)[\s]+([A-Za-z][\d০-৯]+[/][A-Za-z])(?=\s*[,\(\)]|\s|$)', 1.00),
            
            # Flat with em dash (—) - e.g., "Flat—04" - try both Unicode escape and literal (HIGH PRIORITY)
            (r'(?:flat|flt)[\s—\u2014]+([\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Flat with dash and number only - e.g., "Flat-04", "Flat-203" (after em dash normalization) - HIGH PRIORITY - CHECK BEFORE GENERAL DASH PATTERN
            # Allow up to 3 digits for flat numbers like 203, 301, etc.
            (r'(?:flat|flt)[\s-]+([\d০-৯]{1,3})(?=\s*[,\(\)]|\s|$)', 0.98),
            # NEW: Flat with dash and number-letter - e.g., "Flat-7C", "Flat-2C"
            (r'(?:flat|flt)[\s-]+([\d০-৯]+[A-Za-z])(?=\s*[,\(\)]|\s|$)', 0.98),
            
            # Flat Number: patterns - e.g., "Flat Number: 3C", "Flat Number: D-8"
            (r'(?:flat|flt)[\s]+number[\s]*:[\s]*([A-Za-z][\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),  # "Flat Number: D-8"
            (r'(?:flat|flt)[\s]+number[\s]*:[\s]*([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # "Flat Number: 3C"
            # NEW: Flat Number (without colon) with simple number - e.g., "Flat Number 506" -> capture "506"
            (r'(?:flat|flt)[\s]+number[\s]+([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),
            # Flat No. patterns with letter+number - e.g., "Flat No. 5A", "Flat No. A5", "Flat No: 5A", "Flat no: 3C"
            (r'(?:flat|flt)[\s]+no[\s]*:[\s]*([A-Za-z][\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),  # "Flat No: D-8" (letter-dash-number)
            (r'(?:flat|flt)[\s]+no\.?[\s]+([A-Za-z][\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),  # "Flat No. D-8" (letter-dash-number)
            # NEW: Flat no with letter-dash-number - e.g., "Flat no D-4" -> capture "D-4"
            (r'(?:flat|flt)[\s]+no[\s]+([A-Za-z][\s-]+[\d০-৯]+)(?=\s*[,\(\)\.]|\s|$)', 1.00),
            # NEW: Flat No with letter-number (no dash) - e.g., "Flat No D4" -> capture "D4"
            (r'(?:flat|flt)[\s]+no[\s]+([A-Za-z][\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),
            (r'(?:flat|flt)[\s]+no[\s]*:[\s]*([A-Za-z]{2}[\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),  # "Flat No: BC-103" (letter-letter-dash-number)
            (r'(?:flat|flt)[\s]+no\.?[\s]+([A-Za-z]{2}[\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),  # "Flat No. BC-103"
            (r'(?:flat|flt)[\s]+no[\s]*:[\s]*([\d০-৯]+[\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),  # "Flat No: 07-01" (number-dash-number)
            (r'(?:flat|flt)[\s]+no\.?[\s]+([\d০-৯]+[\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),  # "Flat No. 07-01"
            (r'(?:flat|flt)[\s]+no[\s]*:[\s]*([A-Za-z]?[\d০-৯]{1,4}[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # "Flat No: 1103" (up to 4 digits)
            (r'(?:flat|flt)[\s]+no[\s]*:[\s]*([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # "Flat no: 3C"
            # Flat No. with number-letter - e.g., "Flat No. 9B"
            (r'(?:flat|flt)[\s]+no\.?[\s]+([\d০-৯]+[A-Za-z])(?=\s*[,\(\)]|\s|$)', 0.98),  # "Flat No. 9B"
            # NEW: Flat No. with simple number only - e.g., "Flat No. 3" -> capture "3"
            (r'(?:flat|flt)[\s]+no\.?[\s]+([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),
            # REMOVED: General pattern that was matching "no" incorrectly - more specific patterns above handle all cases
            # (r'(?:flat|flt)[\s]+(?:no\.?|number|#|:|-)[\s-]*([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Flat No: with number-slash-letter - e.g., "Flat No: 13/C"
            (r'(?:flat|flt)[\s]+(?:no\.?|number)[\s]*:[\s]*([\d০-৯]+[/][A-Za-z])(?=\s*[,\(\)]|\s|$)', 0.98),
            # Flat No. with dash and letter - e.g., "Flat A5", "Flat No: A 5"
            (r'(?:flat|flt)[\s]+(?:no\.?|number|#|:|-)[\s-]*([A-Za-z])[\s-]*([\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            
            # Flat with dash and number only - e.g., "Flat-04", "Flat-203" (after em dash normalization) - CHECK BEFORE GENERAL DASH PATTERN
            # Allow up to 3 digits for flat numbers like 203, 301, etc.
            (r'(?:flat|flt)[\s-]+([\d০-৯]{1,3})(?=\s*[,\(\)]|\s|$)', 0.98),
            # Flat with dash - e.g., "Flat-5A", "Flat-A5", "Flat-5"
            (r'(?:flat|flt)[\s-]+([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            
            # Flat with space and letter+number - e.g., "Flat 5A", "Flat A5", "Flat 5", "Flat 301", "Flat 1103", "Flat 8C"
            # Allow up to 4 digits for flat numbers like 301, 403, 1103, etc.
            (r'(?:flat|flt)[\s]+([A-Za-z]?[\d০-৯]{1,4}[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Flat with space and letter-number - e.g., "Flat H2", "Flat A1"
            (r'(?:flat|flt)[\s]+([A-Za-z][\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Flat with letter-letter-number (no dash) - e.g., "Flat BC103", "Flat: BC103"
            (r'(?:flat|flt)[\s]*:?[\s]+([A-Za-z]{2}[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Flat with number-dash-number - e.g., "Flat 07-01"
            (r'(?:flat|flt)[\s]+([\d০-৯]+[\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Flat with two letters only - e.g., "Flat AG"
            (r'(?:flat|flt)[\s]+([A-Za-z]{2})(?=\s*[,\(\)]|\s|$)', 0.95),
            # Flat with letter-letter space number - e.g., "Flat-BC 103"
            (r'(?:flat|flt)[\s-]+([A-Za-z]{2}[\s]+[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Flat Number with slash - e.g., "Flat Number A/6"
            (r'(?:flat|flt)[\s]+(?:number|no\.?)[\s]+([A-Za-z][/\-][\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),
            
            # Flat with slash pattern - e.g., "Flat 5/A", "Flat 7/C", "Flat 4-B", "Flat: 8/A"
            (r'(?:flat|flt)[\s]+(?:no\.?|number|#|:|-)?[\s-]*([\d০-৯]+[/\-][A-Za-z])(?=\s*[,\(\)]|\s|$)', 0.98),
            (r'(?:flat|flt)[\s]+(?:no\.?|number|#|:|-)?[\s-]*([A-Za-z][/\-][\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),
            
            # Flat with letter only - e.g., "Flat A", "Flat B"
            (r'(?:flat|flt)[\s]+(?:no\.?|number|#|:|-)?[\s-]*([A-Za-z])(?=\s*[,\(\)]|\s|$)', 0.95),
            
            # INFORMAL PATTERNS (no spaces, typos) - Lower confidence but still valid
            # No-space patterns - e.g., "flat3c", "flatd8", "flatd-8", "flat04", "flatb9", "flatbc103"
            (r'(?:flat|flt)([\d০-৯]+[A-Za-z])(?=\s*[,\(\)]|\s|$)', 0.85),  # "flat3c" (number-letter)
            (r'(?:flat|flt)([A-Za-z][\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.85),  # "flatd8" (letter-number)
            (r'(?:flat|flt)([A-Za-z][\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.85),  # "flatd-8"
            (r'(?:flat|flt)([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.85),  # "flat04"
            (r'(?:flat|flt)([A-Za-z]{2}[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.85),  # "flatbc103"
            # Typo patterns - e.g., "flate 3c", "falt 3c", "flt 3c", "flaat 3c"
            (r'(?:flate|falt|flt|flaat)[\s]+([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.80),
        ]
        
        # EXPLICIT SUITE PATTERNS (95-100% confidence)
        self.explicit_suite_patterns = [
            # Suite# patterns - e.g., "Suite#10", "Suite#A5"
            (r'((?:suite|suit)[#][\s]*[A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 1.00),
            # Suite No. patterns - e.g., "Suite No. 10", "Suite No. A5"
            (r'(?:suite|suit)[\s]+(?:no\.?|number|#|:|-)[\s-]*([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Suite with dash - e.g., "Suite-10", "Suite-A5"
            (r'(?:suite|suit)[\s-]+([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Suite with space - e.g., "Suite 10", "Suite A5"
            (r'(?:suite|suit)[\s]+([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Suite with slash - e.g., "Suite 10/A", "Suite A/5"
            (r'(?:suite|suit)[\s]+(?:no\.?|number|#|:|-)?[\s-]*([\d০-৯]+[/\-][A-Za-z])(?=\s*[,\(\)]|\s|$)', 0.98),
            # NEW: Suite# with slash pattern - e.g., "Suite#10/E" (English)
            (r'(?:suite|suit)[#][\s]*([\d০-৯]+[/][A-Za-z])(?=\s*[,\(\)]|\s|$)', 1.00),
        ]
        
        # EXPLICIT APARTMENT/APT PATTERNS (95-100% confidence)
        self.explicit_apt_patterns = [
            # Apt# patterns - e.g., "Apt#5A", "Apt#A5"
            (r'((?:apt|apartment|apart)[#][\s]*[A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 1.00),
            # Apt No. patterns - e.g., "Apt No. 5A", "Apartment No. A5", "Apartment No. G-05"
            (r'(?:apt|apartment|apart)[\s]+(?:no\.?|number|#|:|-)[\s-]*([A-Za-z][\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),
            (r'(?:apt|apartment|apart)[\s]+(?:no\.?|number|#|:|-)[\s-]*([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Apt with space and letter-dash-number - e.g., "Apartment G-05" (no "No." keyword)
            (r'(?:apt|apartment|apart)[\s]+([A-Za-z][\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Apt with dash - e.g., "Apt-5A", "Apartment-A5"
            (r'(?:apt|apartment|apart)[\s-]+([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Apt with space - e.g., "Apt 5A", "Apartment A5"
            (r'(?:apt|apartment|apart)[\s]+([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
        ]
        
        # EXPLICIT UNIT PATTERNS (95-100% confidence)
        self.explicit_unit_patterns = [
            # Unit# patterns - e.g., "Unit#5A", "Unit#A5"
            (r'((?:unit|unt)[#][\s]*[A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 1.00),
            # Unit No. patterns -, "Unit No. A5"
            (r'(?:unit|unt)[\s]+(?:no\.?|number|#|:|-)[\s-]*([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Unit with dash - e.g., "Unit-5A", "Unit-A5"
            (r'(?:unit|unt)[\s-]+([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Unit with space - e.g., "Unit 5A", "Unit A5"
            (r'(?:unit|unt)[\s]+([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
        ]
        
        # EXPLICIT FLOOR/LEVEL PATTERNS (90-95% confidence)
        # Note: Floor numbers are sometimes part of flat numbers
        self.explicit_floor_patterns = [
            # Floor# patterns - e.g., "Floor#5", "Floor#12"
            (r'((?:floor|flr|fl)[#][\s]*[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.95),
            # Floor No. patterns - e.g., "Floor No. 5", "Floor No. 12"
            (r'(?:floor|flr|fl)[\s]+(?:no\.?|number|#|:|-)[\s-]*([\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.95),
            # Level# patterns - e.g., "Level#5", "Level#12"
            (r'((?:level|lvl)[#][\s]*[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.95),
            # Level No. patterns - e.g., "Level No. 5", "Level No. 12"
            (r'(?:level|lvl)[\s]+(?:no\.?|number|#|:|-)[\s-]*([\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.95),
        ]
        
        # BANGLA PATTERNS (90-95% confidence)
        # Must capture FULL flat number including letter suffix like "৩ সি"
        self.bangla_patterns = [
            # Bangla flat with নং and letter suffix - e.g., "ফ্ল্যাট নং ৩ সি" -> capture "৩ সি" (FULL)
            (r'(?:ফ্ল্যাট|ফ্ল্যাট)[\s]+(?:নং|নাম্বার|নম্বর|:|-)[\s-]*([\d০-৯]+[\s]+[A-Za-z\u0980-\u09FF]+)(?=\s*[,\(\)]|\s|$)', 0.95),
            # Bangla flat with নং and slash - e.g., "ফ্ল্যাট নং ১৩/সি"
            (r'(?:ফ্ল্যাট|ফ্ল্যাট)[\s]+(?:নং|নাম্বার|নম্বর|:|-)[\s-]*([\d০-৯]+[/][A-Za-z\u0980-\u09FF]+)(?=\s*[,\(\)]|\s|$)', 0.95),
            # Bangla flat with নং and dash - e.g., "ফ্ল্যাট নং ০৭-০১", "ফ্ল্যাট নং বিসি-১০৩"
            (r'(?:ফ্ল্যাট|ফ্ল্যাট)[\s]+(?:নং|নাম্বার|নম্বর|:|-)[\s-]*([\d০-৯]+[\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.95),  # "০৭-০১"
            (r'(?:ফ্ল্যাট|ফ্ল্যাট)[\s]+(?:নং|নাম্বার|নম্বর|:|-)[\s-]*([A-Za-z\u0980-\u09FF]+[\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.95),  # "বিসি-১০৩"
            # Bangla flat with hash - e.g., "ফ্ল্যাট#৫", "ফ্ল্যাট#৫এ"
            (r'((?:ফ্ল্যাট|ফ্ল্যাট)[#][\s]*[\d০-৯]+[A-Za-z\u0980-\u09FF]?)(?=\s*[,\(\)]|\s|$)', 0.95),
            # Bangla flat with dash - e.g., "ফ্ল্যাট-৫", "ফ্ল্যাট-৫এ", "ফ্ল্যাট ডি-৮", "ফ্ল্যাট বি-৯"
            (r'(?:ফ্ল্যাট|ফ্ল্যাট)[\s-]+([\d০-৯]+[A-Za-z\u0980-\u09FF]?)(?=\s*[,\(\)]|\s|$)', 0.95),
            (r'(?:ফ্ল্যাট|ফ্ল্যাট)[\s]+([A-Za-z\u0980-\u09FF]+[\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.95),  # "ডি-৮", "বি-৯"
            # Bangla flat with space - e.g., "ফ্ল্যাট ৫", "ফ্ল্যাট ৫এ", "ফ্ল্যাট ৩সি", "ফ্ল্যাট ৫এ", "ফ্ল্যাট ৯বি", "ফ্ল্যাট ০৪", "ফ্ল্যাট ৪"
            (r'(?:ফ্ল্যাট|ফ্ল্যাট)[\s]+([\d০-৯]+[A-Za-z\u0980-\u09FF]?)(?=\s*[,\(\)]|\s|$)', 0.95),
            # Mixed Bangla-English - e.g., "Flat নং 3C", "Flat নং-৩সি", "Flat নাম্বার 3C", "Flat ডি-৮", "Flat বি-৯"
            (r'(?:flat|flt)[\s]+(?:নং|নাম্বার|নম্বর)[\s-]*([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.90),
            (r'(?:flat|flt)[\s]+([A-Za-z\u0980-\u09FF]+[\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.90),  # "Flat ডি-৮", "Flat বি-৯"
            # Mixed English-Bangla - e.g., "ফ্ল্যাট D-8", "ফ্ল্যাট B-9", "ফ্ল্যাট BC 103"
            (r'(?:ফ্ল্যাট|ফ্ল্যাট)[\s]+([A-Za-z]+[\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.90),
            (r'(?:ফ্ল্যাট|ফ্ল্যাট)[\s]+([A-Za-z]{2}[\s]+[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.90),  # "BC 103"
            # NEW: Bangla flat with dash and letter-slash-number - e.g., "ফ্লাট-এ/৫" -> capture "এ/৫"
            # Also handle "ফ্ল্যাট-এ/৫" (with full spelling)
            (r'(?:ফ্ল্যাট|ফ্ল্যাট|ফ্লাট)[\s-]+([A-Za-z\u0980-\u09FF]+[/][\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.95),
            # NEW: Bangla suite with hash and slash - e.g., "স্যুট #১০/ই" -> capture "১০/ই"
            (r'(?:স্যুট|স্যুট)[\s]*#[\s]*([\d০-৯]+[/][A-Za-z\u0980-\u09FF]+)(?=\s*[,\(\)]|\s|$)', 0.95),
        ]
        
        # CONTEXTUAL PATTERNS (85-90% confidence)
        # Patterns that appear in specific contexts
        self.contextual_patterns = [
            # Letter + number after building/tower - e.g., "Diamond Tower, 5A"
            (r'(?:tower|building|bldg|apartment|apt)[\s]*,[\s]*([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.90),
            # Short slash patterns after comma - e.g., "Building, 5/A", "Tower, 7/C"
            (r'(?:tower|building|bldg|apartment|apt)[\s]*,[\s]*([\d০-৯]+[/\-][A-Za-z])(?=\s*[,\(\)]|\s|$)', 0.90),
            # NEW: Parentheses after house number - e.g., "House No. 586/1 (D1)"
            (r'(?:house|hous|home|bari|basha)[\s]*(?:no\.?|number|#|:|-)?[\s-]*[\d০-৯/]+[\s]*\(([A-Za-z]?[\d০-৯]+[A-Za-z]?)\)', 0.88),
            # NEW: After "Lift" keyword - e.g., "Lift 4, Flat: 5C"
            (r'(?:lift|lft)[\s]+[\d০-৯]+[\s]*,[\s]*(?:flat|flt)[\s]*(?:no\.?|number|#|:|-)?[\s-]*([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.85),
            # NEW: After "Floor" keyword - e.g., "6th Floor, 6B", "6 Floor, 6B", ". 6th Floor, 6B"
            # Pattern 1: Number before Floor - e.g., "6th Floor, 6B"
            (r'[\d০-৯]+(?:th|st|nd|rd)?[\s]+(?:floor|flr|fl)[\s]*[,\.]?[\s]*([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.85),
            # Pattern 2: Floor followed by number then comma - e.g., "Floor 6, 6B" (less common)
            (r'(?:floor|flr|fl)[\s]+[\d০-৯]+(?:th|st|nd|rd)?[\s]*[,\.][\s]*([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.85),
            # Floor + Flat patterns - e.g., "3rd floor flat 3C", "4th floor flat D-8", "Level 6 flat B-9"
            (r'[\d০-৯]+(?:th|st|nd|rd)?[\s]+(?:floor|flr|fl)[\s]+(?:flat|flt)[\s]+([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.90),
            (r'(?:level|lvl)[\s]+[\d০-৯]+[\s]+(?:flat|flt)[\s]+([A-Za-z]?[\d০-৯]+[A-Za-z]?)(?=\s*[,\(\)]|\s|$)', 0.90),
            (r'[\d০-৯]+(?:th|st|nd|rd)?[\s]+(?:floor|flr|fl)[\s]+(?:flat|flt)[\s]+([A-Za-z][\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.90),  # "D-8"
            (r'[\d০-৯]+(?:th|st|nd|rd)?[\s]+(?:floor|flr|fl)[\s]+(?:flat|flt)[\s]+([\d০-৯]+[\s-]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.90),  # "07-01"
            # NEW: Standalone letter-number/slash after comma - e.g., "Iman Manjil, F-5/A"
            (r',[\s]*([A-Za-z][\s-]*[\d০-৯]+[/][A-Za-z])(?=\s*[,\(\)]|\s|$)', 0.80),
        ]
        
        # POSITIONAL PATTERNS (85% confidence)
        # Patterns at the start of address - VERY RESTRICTIVE to avoid house number false positives
        # Only match if there's clear flat context or very specific patterns
        self.positional_patterns = [
            # Letter-number at start followed by building/tower with flat context - e.g., "7B, RR Tower" (only if flat mentioned later)
            # REMOVED - too many false positives
            
            # Letter + number at start BUT only if followed by "Flat" or similar keywords
            # REMOVED - too many false positives
            
            # Short slash pattern at start BUT only if followed by "Flat" keyword
            # REMOVED - too many false positives
            
            # Very specific: Letter-number at start followed by "Flat" keyword in next 30 chars
            (r'^([A-Za-z][\d০-৯]+[A-Za-z]?)[\s]*[,\(].{0,30}(?:flat|flt|suite|apt)', 0.85),
            
            # Very specific: Number-letter at start followed by "Flat" keyword in next 30 chars  
            (r'^([\d০-৯]+[A-Za-z])[\s]*[,\(].{0,30}(?:flat|flt|suite|apt)', 0.85),
        ]
        
    def _setup_exclusions(self):
        """Setup exclusion patterns"""
        self.institutional_keywords = {
            'university', 'college', 'hospital', 'school', 'bank', 'office',
            'company', 'corporation', 'limited', 'ltd', 'pvt', 'government'
        }
        
        self.invalid_patterns = [
            r'^\d{5,}$',  # Too many digits (5+ digits likely postal code or house number, but 4 digits can be valid flats like 1103)
            r'^[01]$',    # Just 0 or 1 (likely floor number)
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
        
        # IMPORTANT: If address contains flat-related keywords, don't skip even if institutional
        # This allows extraction from addresses like "Flat no D-4, Government Quarter"
        flat_keywords = ['flat', 'flt', 'suite', 'apt', 'apartment', 'unit', 'ফ্ল্যাট', 'স্যুট']
        if any(kw in address_lower for kw in flat_keywords):
            return False
        
        return institutional_count >= 2
    
    def _is_postal_code(self, flat_number: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted number is actually a postal code"""
        # Postal codes are typically 4 digits
        if re.match(r'^\d{4}$', flat_number):
            # IMPORTANT: If "flat" or "apt" or "unit" is in the context (anywhere before match_end), it's definitely a flat number, not a postal code
            before_context = address[max(0, match_start-50):match_start].lower()
            full_before = address[:match_end].lower()  # Check entire address up to match end
            if any(kw in full_before for kw in ['flat', 'flt', 'apt', 'apartment', 'unit', 'suite', 'no:', 'no.', 'number:']):
                return False
            
            # Check context - if it's at the end of address or after city name, it's likely postal code
            after_context = address[match_end:match_end+30].lower()
            
            # Check for city names before
            city_names = ['dhaka', 'mirpur', 'uttara', 'gulshan', 'banani', 'dhanmondi', 
                         'chittagong', 'chattogram', 'sylhet', 'rajshahi', 'khulna']
            for city in city_names:
                if city in before_context[-20:]:
                    return True
            
            # Check if at end of address
            if match_end >= len(address) - 10:
                return True
        
        return False
    
    def _is_house_number(self, flat_number: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted number is actually a house number"""
        # House numbers are typically longer or have specific patterns
        before_context = address[max(0, match_start-30):match_start].lower()
        
        # IMPORTANT: If "flat" or "suite" or "apt" is in the context, it's definitely a flat number, not a house number
        if any(kw in before_context[-30:] for kw in ['flat', 'flt', 'suite', 'apt', 'apartment', 'unit']):
            return False
        
        # Check for house keywords before
        house_keywords = ['house', 'home', 'hous', 'bari', 'basha', 'building', 'bldg', 'plot', 'holding']
        for keyword in house_keywords:
            if keyword in before_context[-20:]:
                # If number is 3+ digits, it's likely house number
                # For slash patterns, only treat as house number if it's a long pattern (like "38/B" in house context)
                # Short patterns like "1/A" or "3/B" in flat context are valid flat numbers
                if re.match(r'^\d{3,}', flat_number):
                    return True
                # Only treat slash patterns as house numbers if they're longer (like "38/B", "172/1") 
                # AND not in flat context (already checked above)
                if '/' in flat_number and re.match(r'^\d{2,}/', flat_number):
                    return True
        
        return False
    
    def _is_road_or_area_name(self, flat_number: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted number is part of a road name or area name"""
        # IMPORTANT: If "flat" or "apt" or "unit" is in the context before the match, it's definitely a flat number, not a road name
        before_context = address[max(0, match_start-50):match_start].lower()
        if any(kw in before_context for kw in ['flat', 'flt', 'apt', 'apartment', 'unit', 'suite', 'no.', 'no:', 'number:']):
            return False
        
        # Check context after the match
        after_context = address[match_end:match_end+50].lower()
        
        # If "flat" or "apt" appears in the immediate after context (before any road keyword), it's a flat number
        # Check the first 30 characters after the match for flat keywords
        if any(kw in after_context[:30] for kw in ['flat', 'flt', 'apt', 'apartment', 'unit', 'suite', 'house', 'building']):
            # If there's a comma before the road keyword, and flat keyword is before the comma, it's a flat number
            comma_pos = after_context.find(',')
            if comma_pos > 0 and comma_pos < 30:
                before_comma = after_context[:comma_pos]
                if any(kw in before_comma for kw in ['flat', 'flt', 'apt', 'apartment', 'unit', 'suite']):
                    return False
        
        # Road name keywords that often follow numbers
        road_keywords = ['feet', 'road', 'rd', 'street', 'st', 'lane', 'avenue', 'ave', 'goli', 'রোড', 'লেন']
        for keyword in road_keywords:
            if keyword in after_context[:20]:
                # Check if it's a road number pattern (e.g., "60 Feet", "2 No. Road")
                if re.match(r'^[\d০-৯]+$', flat_number):
                    # If number is followed by road keyword, it's likely part of road name
                    # BUT: if there's a comma and flat-related keywords before the road keyword, it's a flat number
                    keyword_pos = after_context.find(keyword)
                    if keyword_pos > 0:
                        before_keyword = after_context[:keyword_pos]
                        if ',' in before_keyword:
                            # There's a comma before the road keyword, check what's between
                            comma_pos = before_keyword.rfind(',')
                            between = after_context[comma_pos+1:keyword_pos]
                            if any(kw in between for kw in ['flat', 'flt', 'apt', 'apartment', 'unit', 'suite', 'house', 'building']):
                                return False
                    return True
        
        # Check for "No. Road" pattern - e.g., "2 No. Road"
        if re.search(r'no\.?\s+road', after_context[:15], re.IGNORECASE):
            return True
        
        # Check for area names that often have numbers - e.g., "Orphanage Road", "Agrabad Commercial Area"
        area_patterns = [
            r'orphanage\s+road',
            r'agrabad\s+commercial',
            r'east\s+kazipara',
            r'west\s+',
            r'north\s+',
            r'south\s+',
        ]
        for pattern in area_patterns:
            if re.search(pattern, after_context, re.IGNORECASE):
                # If number is 2-3 digits and followed by area name, it's likely part of address, not flat
                if re.match(r'^[\d০-৯]{2,3}$', flat_number):
                    return True
        
        # Check for "Tower" or "Building" followed by number - e.g., "Meheghni Tower, 60 Feet"
        # In this case, the number after Tower is likely part of road name, not flat number
        if 'tower' in before_context[-30:] or 'building' in before_context[-30:]:
            # If followed by road keywords, it's likely road name
            if any(kw in after_context[:20] for kw in ['feet', 'road', 'rd', 'street']):
                return True
        
        return False
    
    def _is_positional_false_positive(self, flat_number: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if positional pattern is a false positive (e.g., "9A, Hal Madhobilota" is house number, not flat)"""
        # Only check positional patterns (at start of address)
        if match_start > 10:
            return False
        
        # Check if there's explicit flat context before
        before_context = address[:match_start].lower()
        if any(kw in before_context for kw in ['flat', 'suite', 'apt', 'apartment', 'unit', 'ফ্ল্যাট']):
            return False
        
        # Get context after the match
        after_context = address[match_end:match_end+80].lower()
        full_after_context = address[match_end:].lower()
        
        # STRICT RULE: If pattern is at start (position 0-10) and followed by comma, it's ALWAYS a house number
        # UNLESS there's explicit flat context later in the address
        if match_start <= 10 and ',' in after_context[:5]:
            comma_pos = after_context.find(',')
            if comma_pos >= 0:
                text_after_comma = after_context[comma_pos+1:comma_pos+50].strip()
                
                # Comprehensive list of area/road/building/place indicators
                area_road_indicators = [
                    # Area names
                    'hal', 'madhobilota', 'malibagh', 'bazar', 'railgate', 'kawranbazar',
                    'shymoli', 'shyamoli', 'uttor', 'pirerbag', 'mirpur', 'mohammadpur',
                    'badda', 'cantonment', 'chattogram', 'dhaka', 'sylhet', 'rajshahi',
                    'khulna', 'barisal', 'uttara', 'gulshan', 'banani', 'dhanmondi',
                    'rampura', 'shahjahanpur', 'khilgaon', 'basabo', 'mayakanon',
                    'ujjibone', 'ajij', 'polli', 'amirbag', 'arambag', 'mehedibag',
                    # Building/villa names
                    'villa', 'casa', 'tower', 'building', 'bldg', 'complex', 'plaza',
                    'house', 'hous', 'bari', 'basha', 'promote', 'baily',
                    # Road/street indicators
                    'road', 'rd', 'street', 'st', 'lane', 'goli', 'avenue', 'ave',
                    'r/a', 'residential', 'area', 'mosjid', 'mosque', 'thana', 'ward',
                    'field', 'bazar', 'bazaar', 'moor', 'mor', 'moholla', 'mohalla',
                    # Bangla place indicators
                    'রাজাবাড়ি', 'গেন্ডা', 'সাভার', 'তল্লাবাগ', 'ট্যানাড়ি', 'মোড়',
                ]
                
                # Check if text after comma starts with or contains any indicator
                for indicator in area_road_indicators:
                    # Check if indicator appears in first 30 chars after comma
                    if (text_after_comma.startswith(indicator) or 
                        f' {indicator}' in text_after_comma[:30] or 
                        f', {indicator}' in text_after_comma[:30] or
                        indicator in text_after_comma[:25]):
                        # Exception: if it's followed by "Flat" or similar within next 100 chars, it might be a flat
                        if 'flat' not in full_after_context[:100] and 'suite' not in full_after_context[:100]:
                            return True
                
                # Additional check: If it's a simple number or letter-number at start followed by comma and text,
                # and that text doesn't contain "flat", it's likely a house number
                if re.match(r'^[\d০-৯]{1,3}$', flat_number) or re.match(r'^[A-Za-z][\d০-৯]{1,2}$', flat_number):
                    # If text after comma doesn't start with flat-related keywords, it's a house number
                    if not any(kw in text_after_comma[:20] for kw in ['flat', 'suite', 'apt', 'apartment', 'unit', 'floor', 'lift']):
                        # Check if it's followed by area/building name
                        if len(text_after_comma) > 3:  # Has some text after comma
                            return True
        
        # Check for specific patterns: number-letter at start followed by comma and area name
        # e.g., "9A, Hal Madhobilota", "C7, ANZ Casa Villa"
        if re.match(r'^[A-Za-z]?[\d০-৯]+[A-Za-z]?$', flat_number) and match_start <= 5:
            if ',' in after_context[:5]:
                text_after_comma = after_context[after_context.find(',')+1:after_context.find(',')+40].strip()
                # If followed by area/building name (not flat-related), it's a house number
                if len(text_after_comma) > 2 and not any(kw in text_after_comma[:25] for kw in ['flat', 'suite', 'apt', 'apartment', 'unit']):
                    return True
        
        # Check for slash patterns at start followed by building/area - e.g., "38/B, Promote Baily House"
        if ('/' in flat_number or '-' in flat_number) and match_start <= 5:
            if ',' in after_context[:5]:
                text_after_comma = after_context[after_context.find(',')+1:after_context.find(',')+40].strip()
                # If followed by building/area name (not flat-related), it's a house number
                building_keywords = ['promote', 'baily', 'house', 'villa', 'casa', 'tower', 'building', 'bldg']
                if any(kw in text_after_comma[:25].lower() for kw in building_keywords):
                    if 'flat' not in full_after_context[:100]:
                        return True
        
        return False
    
    def _validate_flat_number(self, number: str) -> bool:
        """Validate extracted flat number"""
        if not number or len(number) > 30:
            return False
        for pattern in self.invalid_patterns:
            if re.match(pattern, number):
                return False
        return True
        
    def extract(self, address: str) -> FlatNumberResult:
        """Extract flat number from address"""
        if not address:
            return FlatNumberResult("", 0.0, ExtractionMethod.NOT_FOUND, address, "Empty address")
            
        original_address = address
        original_address_for_bangla = address
        address = self._bangla_to_english_number(address)
        # Normalize em dash (—) to regular dash for easier pattern matching
        address = address.replace('—', '-').replace('\u2014', '-')
        
        # Skip institutional addresses
        if self._is_institutional(address):
            return FlatNumberResult("", 0.0, ExtractionMethod.INSTITUTIONAL, original_address, "Institutional address")
        
        # Try patterns in order of confidence
        all_patterns = [
            (self.explicit_flat_patterns, ExtractionMethod.EXPLICIT_FLAT),
            (self.explicit_suite_patterns, ExtractionMethod.EXPLICIT_SUITE),
            (self.explicit_apt_patterns, ExtractionMethod.EXPLICIT_APT),
            (self.explicit_unit_patterns, ExtractionMethod.EXPLICIT_UNIT),
            (self.explicit_floor_patterns, ExtractionMethod.EXPLICIT_FLOOR),
            (self.bangla_patterns, ExtractionMethod.BANGLA_PATTERN),
            (self.contextual_patterns, ExtractionMethod.CONTEXTUAL),
            (self.positional_patterns, ExtractionMethod.POSITIONAL),
        ]
        
        all_matches = []
        
        for patterns, method in all_patterns:
            for pattern, confidence in patterns:
                # For Bangla patterns, match against original address
                # For em dash patterns, also check original address before normalization
                if '—' in pattern or '\u2014' in pattern:
                    search_text = original_address
                elif method == ExtractionMethod.BANGLA_PATTERN:
                    search_text = original_address_for_bangla
                else:
                    search_text = address
                match = re.search(pattern, search_text, re.IGNORECASE)
                if match:
                    # Handle patterns with multiple groups
                    if match.lastindex >= 2:
                        # Combine groups (e.g., "Flat No- A 5" -> "A5")
                        flat_number = (match.group(1) + match.group(2)).strip()
                    else:
                        flat_number = match.group(1).strip()
                    
                    # Clean up - remove trailing punctuation and normalize spaces
                    flat_number = flat_number.rstrip(',.')
                    # Normalize multiple spaces to single space, but preserve single spaces (e.g., "BC 103")
                    flat_number = re.sub(r'\s+', ' ', flat_number).strip()
                    
                    # For Bangla patterns, preserve original format
                    if method == ExtractionMethod.BANGLA_PATTERN:
                        original_match = re.search(pattern, original_address_for_bangla, re.IGNORECASE)
                        if original_match:
                            if original_match.lastindex >= 2:
                                flat_number = (original_match.group(1) + original_match.group(2)).strip()
                            else:
                                flat_number = original_match.group(1).strip()
                            flat_number = flat_number.rstrip(',.')
                    
                    # Validate flat number
                    if not self._validate_flat_number(flat_number):
                        continue
                    
                    # Get match positions - use captured group position for filtering, not full match
                    # This ensures "Flat-203" uses position of "203" for context checking
                    if match.lastindex >= 1:
                        match_start_pos = match.start(1)  # Position of captured flat number
                        match_end_pos = match.end(1)
                    else:
                        match_start_pos = match.start()
                        match_end_pos = match.end()
                    
                    # Check exclusions
                    if self._is_postal_code(flat_number, address, match_start_pos, match_end_pos):
                        continue
                    
                    if self._is_house_number(flat_number, address, match_start_pos, match_end_pos):
                        continue
                    
                    if self._is_road_or_area_name(flat_number, address, match_start_pos, match_end_pos):
                        continue
                    
                    # Check for positional false positives (only for positional method)
                    if method == ExtractionMethod.POSITIONAL:
                        if self._is_positional_false_positive(flat_number, address, match_start_pos, match_end_pos):
                            continue
                    
                    # Store match for later prioritization
                    all_matches.append({
                        'flat_number': flat_number,
                        'confidence': confidence,
                        'method': method,
                        'pattern': pattern,
                        'match_start': match.start(),
                        'match_end': match.end(),
                    })
        
        if not all_matches:
            return FlatNumberResult("", 0.0, ExtractionMethod.NOT_FOUND, original_address, "No pattern matched")
        
        # Prioritize matches: prefer explicit patterns, higher confidence, earlier position
        def get_priority(match):
            priority = 0
            
            # Explicit patterns get highest priority
            if match['method'] in [ExtractionMethod.EXPLICIT_FLAT, ExtractionMethod.EXPLICIT_SUITE, 
                                  ExtractionMethod.EXPLICIT_APT, ExtractionMethod.EXPLICIT_UNIT]:
                priority += 10000
            elif match['method'] == ExtractionMethod.EXPLICIT_FLOOR:
                priority += 5000
            elif match['method'] == ExtractionMethod.BANGLA_PATTERN:
                priority += 3000
            elif match['method'] == ExtractionMethod.CONTEXTUAL:
                priority += 2000
            elif match['method'] == ExtractionMethod.POSITIONAL:
                priority += 1000
            
            # Add confidence as secondary priority
            priority += match['confidence'] * 100
            
            # Add position bonus (earlier in address is better for flat numbers)
            position_bonus = (1 - match['match_start'] / len(address)) * 100
            priority += position_bonus
            
            return priority
        
        # Sort by priority (highest first)
        all_matches.sort(key=get_priority, reverse=True)
        
        # Return the best match
        best_match = all_matches[0]
        return FlatNumberResult(
            flat_number=best_match['flat_number'],
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
    """Extract flat number from single address"""
    print("=" * 80)
    print("FLAT NUMBER EXTRACTION")
    print("=" * 80)
    print()
    print(f"Address: {address}")
    print()
    
    extractor = AdvancedFlatNumberExtractor()
    result = extractor.extract(address)
    
    print(f"Flat Number:  {result.flat_number or '(not found)'}")
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
    
    extractor = AdvancedFlatNumberExtractor(confidence_threshold=confidence)
    
    print("🔄 Processing records...")
    extracted_count = 0
    confidence_dist = {'>95': 0, '90-95': 0, '85-90': 0, '80-85': 0, '75-80': 0, '70-75': 0, '<70': 0}
    
    for i, record in enumerate(data, 1):
        if i % 100 == 0:
            print(f"   Processed {i}/{len(data)} records...")
        
        address = record.get('address', '')
        result = extractor.extract(address)
        
        if result.confidence >= confidence:
            record['components']['flat_number'] = result.flat_number
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
            record['components']['flat_number'] = ""
    
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
        output_dir = 'data/json/processing/flat'
    
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
    
    extractor = AdvancedFlatNumberExtractor()
    
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
    split_data['no_flat_number'] = []
    
    print("🔄 Categorizing records...")
    for i, record in enumerate(data, 1):
        if i % 100 == 0:
            print(f"   Processed {i}/{len(data)} records...")
        
        address = record.get('address', '')
        result = extractor.extract(address)
        
        # Create new record with only flat_number in components
        new_record = {
            'id': record.get('id'),
            'address': address,
            'components': {
                'flat_number': result.flat_number if result.confidence >= 0.65 and result.flat_number else ''
            }
        }
        
        if result.flat_number and result.confidence >= 0.65:
            # Find appropriate category
            for cat_name, (min_conf, max_conf) in categories.items():
                if min_conf <= result.confidence < max_conf:
                    split_data[cat_name].append(new_record)
                    break
        else:
            split_data['no_flat_number'].append(new_record)
    
    print()
    print("💾 Saving split datasets...")
    
    # Save each category
    for cat_name, records in split_data.items():
        if cat_name == 'no_flat_number':
            cat_path = output_path / cat_name / 'data.json'
        else:
            cat_path = output_path / 'with_flat_number' / cat_name / 'data.json'
        
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
        base_dir = 'data/json/processing/flat'
    
    data_path = Path(base_dir) / 'with_flat_number' / confidence_level / 'data.json'
    
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
    
    extractor = AdvancedFlatNumberExtractor(confidence_threshold=threshold)
    
    print("🔄 Re-processing...")
    updated = 0
    
    for i, record in enumerate(data, 1):
        address = record.get('address', '')
        old_number = record['components'].get('flat_number', '')
        
        result = extractor.extract(address)
        
        if result.confidence >= threshold and result.flat_number != old_number:
            record['components']['flat_number'] = result.flat_number
            updated += 1
            if updated <= 10:
                print(f"   ✓ {old_number} → {result.flat_number}")
    
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
# COMMAND: REPROCESS ALL
# ============================================================================

def cmd_reprocess_all(base_dir: str = None):
    """Re-process all confidence levels"""
    if base_dir is None:
        base_dir = 'data/json/processing/flat'
    
    input_file = 'data/json/real-customer-address-dataset.json'
    
    print("=" * 80)
    print("RE-PROCESSING ALL LEVELS")
    print("=" * 80)
    print()
    
    # Just run split again to reprocess everything (now keeps only flat_number)
    cmd_split(input_file, base_dir)


# ============================================================================
# COMMAND: SYNC (Update Main Dataset from Split)
# ============================================================================

def cmd_sync(confidence_level: str, main_file: str = None, split_dir: str = None):
    """Sync main dataset from split data"""
    if main_file is None:
        main_file = 'data/json/real-customer-address-dataset.json'
    if split_dir is None:
        split_dir = 'data/json/processing/flat'
    
    main_path = Path(main_file)
    split_path = Path(split_dir) / 'with_flat_number' / confidence_level / 'data.json'
    
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
        flat_number = record['components'].get('flat_number', '')
        if flat_number:
            split_map[address] = flat_number
    
    print("🔄 Syncing...")
    updated = 0
    
    for record in main_data:
        address = record.get('address', '')
        if address in split_map:
            if 'components' not in record:
                record['components'] = {}
            old_flat_number = record['components'].get('flat_number', '')
            new_flat_number = split_map[address]
            if old_flat_number != new_flat_number:
                record['components']['flat_number'] = new_flat_number
                updated += 1
                if updated <= 10:
                    print(f"   ✓ {old_flat_number} → {new_flat_number}")
    
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
# COMMAND: MOVE EMPTY (Move empty flat numbers to no_flat_number)
# ============================================================================

def cmd_move_empty(base_dir: str = None):
    """Move all records with empty flat_number to no_flat_number file"""
    if base_dir is None:
        base_dir = 'data/json/processing/flat'
    
    base_path = Path(base_dir)
    no_flat_path = base_path / 'no_flat_number' / 'data.json'
    
    print("=" * 80)
    print("MOVING EMPTY FLAT NUMBERS TO no_flat_number")
    print("=" * 80)
    print()
    
    # Load no_flat_number file
    print("📂 Loading no_flat_number file...")
    no_flat_data = load_json(no_flat_path)
    print(f"   ✓ Loaded {len(no_flat_data)} records")
    
    # Process all confidence level files
    with_flat_dirs = [
        base_path / 'with_flat_number' / '1.excellent_95_100' / 'data.json',
        base_path / 'with_flat_number' / '2.very_high_90_95' / 'data.json',
        base_path / 'with_flat_number' / '3.high_85_90' / 'data.json',
        base_path / 'with_flat_number' / '4.good_80_85' / 'data.json',
        base_path / 'with_flat_number' / '5.medium_high_75_80' / 'data.json',
        base_path / 'with_flat_number' / '6.medium_70_75' / 'data.json',
        base_path / 'with_flat_number' / '7.acceptable_65_70' / 'data.json',
        base_path / 'with_flat_number' / '8.low_below_65' / 'data.json',
    ]
    
    total_moved = 0
    
    print("\n🔄 Processing confidence level files...")
    for filepath in with_flat_dirs:
        if not filepath.exists():
            continue
        
        relative_path = filepath.relative_to(base_path.parent.parent.parent.parent.parent)
        print(f"\n📄 Processing: {relative_path.name}")
        
        data = load_json(filepath)
        if not data:
            continue
        
        # Separate records with and without flat numbers
        records_with_flat = []
        records_without_flat = []
        
        for record in data:
            flat_number = record.get('components', {}).get('flat_number', '')
            if not flat_number or flat_number.strip() == '':
                records_without_flat.append(record)
            else:
                records_with_flat.append(record)
        
        moved_count = len(records_without_flat)
        total_moved += moved_count
        
        if moved_count > 0:
            # Add to no_flat_number
            no_flat_data.extend(records_without_flat)
            print(f"   ✓ Moved {moved_count:,} records to no_flat_number")
            print(f"   ✓ Kept {len(records_with_flat):,} records with flat numbers")
            
            # Save updated file
            save_json(filepath, records_with_flat)
        else:
            print(f"   ✓ No empty flat numbers found")
    
    # Save updated no_flat_number file
    print(f"\n💾 Saving no_flat_number file...")
    save_json(no_flat_path, no_flat_data)
    print(f"   ✓ Saved {len(no_flat_data):,} total records")
    
    print()
    print("=" * 80)
    print("MOVEMENT COMPLETE")
    print("=" * 80)
    print()
    print(f"Total Records Moved:     {total_moved:,}")
    print(f"Total in no_flat_number: {len(no_flat_data):,}")
    print()


# ============================================================================
# COMMAND: UPDATE SUMMARY (Regenerate split_summary.json)
# ============================================================================

def cmd_update_summary(base_dir: str = None):
    """Update split_summary.json based on current data"""
    if base_dir is None:
        base_dir = 'data/json/processing/flat'
    
    base_path = Path(base_dir)
    
    print("=" * 80)
    print("UPDATING SPLIT SUMMARY")
    print("=" * 80)
    print()
    
    # Load all data files
    categories = {
        '1.excellent_95_100': base_path / 'with_flat_number' / '1.excellent_95_100' / 'data.json',
        '2.very_high_90_95': base_path / 'with_flat_number' / '2.very_high_90_95' / 'data.json',
        '3.high_85_90': base_path / 'with_flat_number' / '3.high_85_90' / 'data.json',
        '4.good_80_85': base_path / 'with_flat_number' / '4.good_80_85' / 'data.json',
        '5.medium_high_75_80': base_path / 'with_flat_number' / '5.medium_high_75_80' / 'data.json',
        '6.medium_70_75': base_path / 'with_flat_number' / '6.medium_70_75' / 'data.json',
        '7.acceptable_65_70': base_path / 'with_flat_number' / '7.acceptable_65_70' / 'data.json',
        '8.low_below_65': base_path / 'with_flat_number' / '8.low_below_65' / 'data.json',
        'no_flat_number': base_path / 'no_flat_number' / 'data.json',
    }
    
    print("📂 Loading data files...")
    category_counts = {}
    total_with_flat = 0
    total_without_flat = 0
    
    for cat_name, filepath in categories.items():
        data = load_json(filepath)
        count = len(data)
        category_counts[cat_name] = count
        
        if cat_name != 'no_flat_number':
            total_with_flat += count
            print(f"   ✓ {cat_name}: {count:,} records")
        else:
            total_without_flat = count
            print(f"   ✓ {cat_name}: {count:,} records")
    
    total_records = total_with_flat + total_without_flat
    
    # Generate summary
    summary = [{
        "statistics": {
            "total_records": total_records,
            "with_flat_number": total_with_flat,
            "without_flat_number": total_without_flat,
            "coverage_percentage": round((total_with_flat / total_records * 100) if total_records > 0 else 0, 2),
            "confidence_breakdown": {
                cat_name: count for cat_name, count in category_counts.items() 
                if cat_name != 'no_flat_number'
            }
        },
        "last_updated": "2025-12-19",
        "description": "Summary of flat number extraction results split by confidence levels"
    }]
    
    # Save summary
    summary_path = base_path / 'split_summary.json'
    save_json(summary_path, summary)
    
    print()
    print("=" * 80)
    print("SUMMARY UPDATED")
    print("=" * 80)
    print()
    print(f"Total Records:         {total_records:,}")
    print(f"With Flat Number:      {total_with_flat:,} ({total_with_flat/total_records*100:.1f}%)")
    print(f"Without Flat Number:   {total_without_flat:,} ({total_without_flat/total_records*100:.1f}%)")
    print()
    print("Confidence Breakdown:")
    for cat_name, count in sorted(category_counts.items()):
        if cat_name != 'no_flat_number':
            percentage = (count / total_records * 100) if total_records > 0 else 0
            print(f"  {cat_name:30} {count:>6,} records ({percentage:>5.1f}%)")
    print()
    print(f"💾 Summary saved to: {summary_path.relative_to(base_path.parent.parent.parent.parent.parent)}")
    print()


# ============================================================================
# COMMAND: FIX FALSE POSITIVES (Remove house numbers incorrectly identified as flat numbers)
# ============================================================================

def cmd_fix_false_positives(base_dir: str = None):
    """Fix false positives (remove house numbers incorrectly identified as flat numbers)"""
    if base_dir is None:
        base_dir = 'data/json/processing/flat'
    
    base_path = Path(base_dir)
    
    print("=" * 80)
    print("FIXING FALSE POSITIVES")
    print("=" * 80)
    print()
    
    extractor = AdvancedFlatNumberExtractor()
    
    # Find all JSON files
    json_files = []
    for json_file in base_path.rglob('*.json'):
        if json_file.name not in ['split_summary.json', 'pattern_discovery_report.json', 
                                   'reprocessing_analysis_report.json']:
            json_files.append(json_file)
    
    print(f"📂 Found {len(json_files)} JSON files")
    print("\n🔄 Processing files...")
    
    total_fixed = 0
    
    for json_file in sorted(json_files):
        relative_path = json_file.relative_to(base_path.parent.parent.parent.parent.parent)
        print(f"\n📄 Processing: {relative_path}")
        
        data = load_json(json_file)
        if not data:
            continue
        
        fixed = 0
        
        for record in data:
            address = record.get('address', '')
            if 'components' not in record:
                record['components'] = {}
            
            flat_number = record['components'].get('flat_number', '')
            
            if flat_number:
                # Re-extract to get updated result
                result = extractor.extract(address)
                
                # If new extraction is empty but old had value, it was likely a false positive
                if not result.flat_number and flat_number:
                    record['components']['flat_number'] = ""
                    fixed += 1
                # If new extraction differs, use the new one (algorithm improved)
                elif result.flat_number != flat_number:
                    record['components']['flat_number'] = result.flat_number
                    fixed += 1
        
        if fixed > 0:
            save_json(json_file, data)
            print(f"   ✓ Fixed {fixed:,} false positives")
            total_fixed += fixed
        else:
            print(f"   ✓ No false positives found")
    
    print()
    print("=" * 80)
    print("FIXING COMPLETE")
    print("=" * 80)
    print()
    print(f"Total False Positives Fixed: {total_fixed:,}")
    print()


# ============================================================================
# MAIN CLI
# ============================================================================

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Complete Flat Number Processor - All-in-One Solution',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Extract from single address:
    python3 flat_number_processor.py extract "Flat No: 5A, House No: 24, Diamond Tower"
  
  Process entire dataset:
    python3 flat_number_processor.py process --confidence 0.70
  
  Split dataset by confidence:
    python3 flat_number_processor.py split
  
  Re-process specific level:
    python3 flat_number_processor.py reprocess 2.very_high_90_95
  
  Re-process all levels:
    python3 flat_number_processor.py reprocess-all
  
  Sync main dataset:
    python3 flat_number_processor.py sync 2.very_high_90_95
  
  Move empty flat numbers:
    python3 flat_number_processor.py move-empty
  
  Update split summary:
    python3 flat_number_processor.py update-summary
  
  Fix false positives:
    python3 flat_number_processor.py fix-false-positives
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract flat number from address')
    extract_parser.add_argument('address', help='Address string')
    extract_parser.add_argument('--details', action='store_true', help='Show detailed information', dest='details')
    
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
    
    # Reprocess all command
    reprocess_all_parser = subparsers.add_parser('reprocess-all', help='Re-process all confidence levels')
    reprocess_all_parser.add_argument('--base-dir', help='Base split directory')
    
    # Sync command
    sync_parser = subparsers.add_parser('sync', help='Sync main dataset from split')
    sync_parser.add_argument('level', help='Confidence level folder name')
    sync_parser.add_argument('--main-file', help='Main dataset file')
    sync_parser.add_argument('--split-dir', help='Split directory')
    
    # Move empty command
    move_empty_parser = subparsers.add_parser('move-empty', help='Move empty flat numbers to no_flat_number')
    move_empty_parser.add_argument('--base-dir', help='Base split directory')
    
    # Update summary command
    update_summary_parser = subparsers.add_parser('update-summary', help='Update split_summary.json')
    update_summary_parser.add_argument('--base-dir', help='Base split directory')
    
    # Fix false positives command
    fix_fp_parser = subparsers.add_parser('fix-false-positives', help='Fix false positives (remove house numbers)')
    fix_fp_parser.add_argument('--base-dir', help='Base split directory')
    
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
    elif args.command == 'reprocess-all':
        cmd_reprocess_all(args.base_dir)
    elif args.command == 'sync':
        cmd_sync(args.level, args.main_file, args.split_dir)
    elif args.command == 'move-empty':
        cmd_move_empty(getattr(args, 'base_dir', None))
    elif args.command == 'update-summary':
        cmd_update_summary(getattr(args, 'base_dir', None))
    elif args.command == 'fix-false-positives':
        cmd_fix_false_positives(getattr(args, 'base_dir', None))


if __name__ == "__main__":
    main()
