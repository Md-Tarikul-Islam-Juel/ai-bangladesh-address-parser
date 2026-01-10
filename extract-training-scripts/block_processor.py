#!/usr/bin/env python3
"""
Complete Block Number Processor - All-in-One Solution
======================================================

Single comprehensive script for Bangladeshi address block number extraction,
processing, organization, and management.

Features:
    1. Extract block numbers from addresses (Core Algorithm)
    2. Process entire dataset with confidence filtering
    3. Split dataset by confidence levels
    4. Re-process specific confidence folders
    5. Sync changes between split and main dataset

Usage:
    # Extract from single address
    python3 block_processor.py extract "House 48 & 52, Road 05, Block B, Monsurabad R/A"
    
    # Process entire dataset
    python3 block_processor.py process --confidence 0.70
    
    # Split dataset by confidence
    python3 block_processor.py split
    
    # Re-process specific confidence level
    python3 block_processor.py reprocess 2.very_high_90_95
    
    # Update main dataset from split
    python3 block_processor.py sync 2.very_high_90_95

Author: Advanced AI Address Parser System
Date: December 2025
Version: 1.0
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
    EXPLICIT_BLOCK = "explicit_block"
    EXPLICIT_SECTOR = "explicit_sector"
    EXPLICIT_BLK = "explicit_blk"
    BANGLA_PATTERN = "bangla_pattern"
    CONTEXTUAL = "contextual"
    POSITIONAL = "positional"
    NOT_FOUND = "not_found"
    NOT_CONFIDENT = "not_confident"
    INSTITUTIONAL = "institutional_skip"


@dataclass
class BlockNumberResult:
    """Result of block number extraction"""
    block_number: str
    confidence: float
    method: ExtractionMethod
    original: str = ""
    reason: str = ""
    
    def __str__(self):
        return f"BlockNumber('{self.block_number}', {self.confidence:.1%}, {self.method.value})"
    
    def to_dict(self) -> Dict:
        return {
            'block_number': self.block_number,
            'confidence': self.confidence,
            'method': self.method.value,
            'original': self.original,
            'reason': self.reason
        }


class AdvancedBlockNumberExtractor:
    """Advanced AI-Based Block Number Extractor for Bangladeshi Addresses"""
    
    def __init__(self, preserve_format: bool = True, confidence_threshold: float = 0.70):
        self.preserve_format = preserve_format
        self.confidence_threshold = confidence_threshold
        self._setup_advanced_patterns()
        self._setup_exclusions()
        self._setup_bangla_mappings()
        
    def _setup_advanced_patterns(self):
        """Setup advanced extraction patterns"""
        
        # EXPLICIT BLOCK PATTERNS (95-100% confidence)
        # CRITICAL: Patterns with letter BEFORE "Block" must come FIRST
        self.explicit_block_patterns = [
            # H Block, K Block, J Block (letter BEFORE Block - highest priority)
            (r'([A-Za-z])[\s]+(?:block|blk)(?=\s*[,\(\)]|\s|$)', 1.00),
            # Banasree H Block, Halishahar K Block (with area name before)
            (r'([A-Za-z])[\s]+(?:block|blk)(?=\s*[,\(\)]|\s|$)', 1.00),
            # Block - E, Block - A (letter blocks with dash)
            (r'(?:block|blk)[\s\-]+([A-Za-z])(?=\s*[,\(\)]|\s|$)', 1.00),
            # Block A, Block B, Block C (letter blocks)
            (r'(?:block|blk)[\s]+([A-Za-z])(?=\s*[,\(\)]|\s|$)', 1.00),
            # Block-1, Block-2, Block-12 (number blocks with dash)
            (r'(?:block|blk)[\s\-]+([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Block No: A, Block No. B, Block Number: C
            (r'(?:block|blk)[\s]+(?:no\.?|number|:)[\s\-]*([A-Za-z\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),
            # Block # A, Block#B, Block # 1
            (r'(?:block|blk)[\s]*#[\s]*([A-Za-z\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Block: A, Block: 1
            (r'(?:block|blk)[\s]*:[\s]*([A-Za-z\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Block 1, Block 2 (number blocks)
            (r'(?:block|blk)[\s]+([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.95),
        ]
        
        # EXPLICIT SECTOR PATTERNS (90-100% confidence)
        # Note: Sector is sometimes used as block in addresses
        self.explicit_sector_patterns = [
            # Sector 12, Sector-14, Sector # 13
            (r'(?:sector|sct)[\s\-]+([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.95),
            # Sector No: 12, Sector No. 14
            (r'(?:sector|sct)[\s]+(?:no\.?|number|:)[\s\-]*([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Sector # 13, Sector#14
            (r'(?:sector|sct)[\s]*#[\s]*([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.95),
            # Sector: 12, Sector: 14
            (r'(?:sector|sct)[\s]*:[\s]*([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.95),
        ]
        
        # EXPLICIT BLK PATTERNS (90-95% confidence)
        # Abbreviated form
        self.explicit_blk_patterns = [
            # Blk A, Blk-1, Blk # B
            (r'\bblk[\s\-#:]+([A-Za-z\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.90),
        ]
        
        # BANGLA PATTERNS (90-100% confidence)
        self.bangla_patterns = [
            # ব্লক চ, ব্লক - চ (letter blocks)
            (r'ব্লক[\s\-]+([A-Za-z\u0980-\u09FF])(?=\s*[,\(\)]|\s|$)', 1.00),
            # ব্লক ১, ব্লক ২ (number blocks)
            (r'ব্লক[\s\-]+([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),
            # ব্লক নং চ, ব্লক নম্বর ২
            (r'ব্লক[\s]+(?:নং|নম্বর|:)[\s\-]*([A-Za-z\d০-৯\u0980-\u09FF]+)(?=\s*[,\(\)]|\s|$)', 1.00),
            # সেক্টর ১২, সেক্টর - ১৪
            (r'সেক্টর[\s\-]+([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.95),
        ]
        
        # CONTEXTUAL PATTERNS (80-90% confidence)
        self.contextual_patterns = [
            # Letter or number after comma with block context (ONLY if block/sector keyword is present)
            (r'(?:block|blk|sector|sct)[\s]*,[\s]*([A-Za-z\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.85),
        ]
        
        # POSITIONAL PATTERNS (70-80% confidence)
        # REMOVED: This pattern was causing too many false positives (city names, house numbers, etc.)
        self.positional_patterns = []
        
    def _setup_exclusions(self):
        """Setup exclusion patterns and keywords"""
        # Invalid patterns (should not be extracted as block numbers)
        self.invalid_patterns = [
            r'^\d{4,}$',  # 4+ digit numbers (likely postal codes or house numbers)
            r'^\d{1,2}/\d+',  # Slash patterns (likely house/road numbers)
            r'^[a-z]',  # Lowercase single letter (likely not a block)
            r'^\d{2,3}$',  # 2-3 digit numbers without block context (likely house numbers)
        ]
        
        # Common city/district names (should not be extracted as block numbers)
        self.city_names = [
            'dhaka', 'chittagong', 'chattogram', 'ctg', 'comilla', 'cumilla',
            'rajshahi', 'khulna', 'sylhet', 'barisal', 'rangpur', 'mymensingh',
            'narayanganj', 'gazipur', 'noakhali', 'feni', 'coxs bazar', 'cox\'s bazar',
            'jessore', 'jashore', 'bogra', 'bogura', 'dinajpur', 'sirajganj',
            'pabna', 'naogaon', 'jamalpur', 'kishoreganj', 'tangail', 'munshiganj',
            'madaripur', 'faridpur', 'gopalganj', 'shariatpur', 'rajbari',
            'manikganj', 'narsingdi', 'brahmanbaria', 'chandpur', 'lakshmipur',
            'feni', 'noakhali', 'chittagong', 'coxs bazar', 'bandarban', 'rangamati',
            'khagrachhari', 'sylhet', 'moulvibazar', 'habiganj', 'sunamganj',
            'rajshahi', 'chapainawabganj', 'naogaon', 'natore', 'pabna', 'sirajganj',
            'bogra', 'joypurhat', 'rangpur', 'dinajpur', 'thakurgaon', 'panchagarh',
            'nilphamari', 'lalmonirhat', 'kurigram', 'gaibandha', 'khulna',
            'bagerhat', 'satkhira', 'jessore', 'jhenaidah', 'magura', 'narail',
            'kushtia', 'meherpur', 'chuadanga', 'barisal', 'bhola', 'patuakhali',
            'pirojpur', 'barguna', 'jhalokati', 'mymensingh', 'jamalpur', 'sherpur',
            'netrokona', 'tangail', 'kishoreganj', 'manikganj', 'munshiganj',
            'gopalganj', 'faridpur', 'madaripur', 'shariatpur', 'rajbari'
        ]
        
        # Common area names in Dhaka/other cities (should not be extracted as block numbers)
        self.area_names = [
            'uttara', 'dhanmondi', 'gulshan', 'banani', 'rampura', 'khilgaon',
            'mirpur', 'mohammadpur', 'tejgaon', 'motijheel', 'old dhaka', 'purana paltan',
            'farmgate', 'shyamoli', 'adabor', 'mohakhali', 'baridhara', 'banasree',
            'meradia', 'shantinagar', 'wari', 'lalbagh', 'azimpur', 'new market',
            'bashabo', 'jatrabari', 'demra', 'shyampur', 'sutrapur', 'kotwali',
            'lalbagh', 'hazaribagh', 'gandaria', 'narinda', 'wari', 'sutrapur',
            'gopibagh', 'mugda', 'pallabi', 'uttara', 'tongi', 'savar', 'dhamrai',
            'keraniganj', 'dohar', 'nawabganj', 'dohar', 'dhamrai', 'savar',
            'agrabad', 'halishahar', 'panchlaish', 'khulshi', 'bakolia', 'chawkbazar',
            'pahartali', 'patenga', 'bayezid', 'andarkilla', 'katalganj', 'nasirabad',
            'lalkhan bazar', 'chittagong', 'raozan', 'fatickchari', 'sitakunda',
            'sandwip', 'hatiya', 'feni', 'chhagalnaiya', 'daganbhuiyan', 'parshuram',
            'fulgazi', 'sonagazi', 'dagonbhuiyan', 'chhagalnaiya', 'parshuram',
            'ghatarchor', 'matuail', 'khilgaon', 'rampura', 'jatrabari', 'demra',
            'mohakhali', 'banasree', 'meradia', 'adabor', 'shyamoli', 'mohammadpur',
            'vashanteck', 'khilkhet', 'badda', 'baridhara', 'gulshan', 'banani',
            'uttara', 'dhanmondi', 'wari', 'lalbagh', 'azimpur', 'new market',
            'bashabo', 'shantinagar', 'farmgate', 'tejgaon', 'motijheel', 'old dhaka',
            'horogram', 'sompreeti', 'madhobkati', 'jhongkar', 'agrabad', 'sostitola',
            'thonthonia', 'khalishpur', 'kawtkhali', 'zindabazar', 'amberkhana',
            'hapania', 'cikly', 'kasalong', 'ramgonj', 'hirajil', 'jamgora',
            'kandirpar', 'narinda', 'balugat', 'rajerbag', 'hajigonj', 'miyarpol',
            'saidabad', 'bajitpur', 'sodorghat', 'mohamudpur', 'chayaneer', 'lecturer'
        ]
        
        # Keywords that indicate this is NOT a block number
        self.exclusion_keywords = [
            'house', 'home', 'bari', 'basha', 'road', 'rd', 'street', 'st',
            'lane', 'avenue', 'ave', 'building', 'bldg', 'tower', 'flat',
            'apt', 'apartment', 'unit', 'suite', 'postal', 'zip', 'code',
            'floor', 'flr', 'fl', 'level', 'lvl', 'lift'
        ]
        
    def _setup_bangla_mappings(self):
        """Setup Bangla numeral to English conversion"""
        self.bangla_to_english = {
            '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4',
            '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'
        }
        
        # Bangla letter to English single letter mappings
        self.bangla_to_english_letter = {
            'ক': 'K', 'খ': 'Kh', 'গ': 'G', 'ঘ': 'Gh', 'ঙ': 'Ng',
            'চ': 'C', 'ছ': 'Ch', 'জ': 'J', 'ঝ': 'Jh', 'ঞ': 'Ny',
            'ট': 'T', 'ঠ': 'Th', 'ড': 'D', 'ঢ': 'Dh', 'ণ': 'N',
            'ত': 'T', 'থ': 'Th', 'দ': 'D', 'ধ': 'Dh', 'ন': 'N',
            'প': 'P', 'ফ': 'Ph', 'ব': 'B', 'ভ': 'Bh', 'ম': 'M',
            'য': 'Y', 'র': 'R', 'ল': 'L', 'শ': 'Sh', 'ষ': 'Sh',
            'স': 'S', 'হ': 'H', 'ড়': 'R', 'ঢ়': 'Rh', 'য়': 'Y',
            'অ': 'A', 'আ': 'A', 'ই': 'I', 'ঈ': 'I', 'উ': 'U',
            'ঊ': 'U', 'ঋ': 'R', 'এ': 'E', 'ঐ': 'Ai', 'ও': 'O',
            'ঔ': 'Ou'
        }
        
        # Bangla letter to Banglish/Romanized mappings (for block letters)
        # Common block letters in Banglish form
        self.bangla_to_banglish = {
            'চ': 'Cha', 'ক': 'Ka', 'গ': 'Ga', 'জ': 'Ja', 'ড': 'Da',
            'প': 'Pa', 'ব': 'Ba', 'ম': 'Ma', 'র': 'Ra', 'ল': 'La',
            'এ': 'A', 'বি': 'Bi', 'সি': 'Ci', 'ডি': 'Di', 'ই': 'E',
            'এফ': 'F', 'জি': 'Gi', 'এইচ': 'H', 'আই': 'I', 'জে': 'Je',
            'খ': 'Kha', 'ছ': 'Cha', 'ঠ': 'Tha', 'থ': 'Tha', 'ফ': 'Pha',
            'ভ': 'Bha', 'শ': 'Sha', 'স': 'Sa', 'হ': 'Ha'
        }
        
    def _bangla_to_english_number(self, text: str) -> str:
        """Convert Bangla numerals to English"""
        for bangla, english in self.bangla_to_english.items():
            text = text.replace(bangla, english)
        return text
    
    def _bangla_letter_to_banglish(self, text: str) -> str:
        """Convert Bangla letters to Banglish/Romanized form (for block letters)"""
        # Check if text contains any Bangla characters
        if any(char in self.bangla_to_banglish for char in text):
            # Find the first matching Bangla character
            for bangla_char in text:
                if bangla_char in self.bangla_to_banglish:
                    return self.bangla_to_banglish[bangla_char]
            # Fallback: try single letter mapping
            for bangla_char in text:
                if bangla_char in self.bangla_to_english_letter:
                    return self.bangla_to_english_letter[bangla_char]
        return text
    
    def _is_institutional(self, address: str) -> bool:
        """Check if address is institutional (skip block extraction)"""
        address_lower = address.lower()
        institutional_keywords = [
            'bank', 'hospital', 'clinic', 'school', 'college', 'university',
            'mosque', 'masjid', 'temple', 'church', 'office', 'corporate',
            'branch', 'ltd', 'limited', 'plc', 'company', 'corporation'
        ]
        
        institutional_count = sum(1 for kw in institutional_keywords if kw in address_lower)
        
        # If 2+ institutional keywords, likely institutional address
        return institutional_count >= 2
    
    def _is_house_number(self, block_number: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted number is actually a house number"""
        before_context = address[max(0, match_start-30):match_start].lower()
        after_context = address[match_end:match_end+30].lower()
        full_context = address[max(0, match_start-30):match_end+30].lower()
        
        # If "block" or "sector" is in the context, it's definitely a block number
        if any(kw in full_context for kw in ['block', 'blk', 'sector', 'sct', 'ব্লক', 'সেক্টর']):
            return False
        
        # If it's a pure number (1-3 digits) and there's no block context, it's likely a house number
        if re.match(r'^\d{1,3}$', block_number):
            # Check for house keywords before or after
            house_keywords = ['house', 'home', 'hous', 'bari', 'basha', 'building', 'bldg', 'plot', 'holding', 'no', 'number']
            if any(kw in before_context[-20:] for kw in house_keywords):
                return True
            # If it's at the start of address followed by comma, likely house number
            if match_start < 10 and ',' in after_context[:5]:
                return True
            # If followed by road/street keywords, likely house number
            if any(kw in after_context[:15] for kw in ['road', 'rd', 'street', 'st', 'lane', 'goli', 'রোড']):
                return True
        
        return False
    
    def _is_road_number(self, block_number: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted number is actually a road number"""
        before_context = address[max(0, match_start-30):match_start].lower()
        after_context = address[match_end:match_end+30].lower()
        full_context = address[max(0, match_start-30):match_end+30].lower()
        
        # If "block" or "sector" is in the context, it's definitely a block number
        if any(kw in full_context for kw in ['block', 'blk', 'sector', 'sct', 'ব্লক', 'সেক্টর']):
            return False
        
        # Check for road keywords
        road_keywords = ['road', 'rd', 'street', 'st', 'lane', 'avenue', 'ave', 'goli', 'রোড', 'লেন']
        for keyword in road_keywords:
            if keyword in after_context[:20]:
                # If number is followed by road keyword, it's likely road number
                return True
        
        return False
    
    def _is_postal_code(self, block_number: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted number is actually a postal code"""
        # Postal codes are typically 4 digits
        if re.match(r'^\d{4}$', block_number):
            # If "block" or "sector" is in the context, it's definitely a block number
            before_context = address[:match_end].lower()
            if any(kw in before_context for kw in ['block', 'blk', 'sector', 'sct', 'ব্লক', 'সেক্টর']):
                return False
            
            # Check if it's at the end of address or after city name
            if match_end >= len(address) - 10:
                return True
        
        return False
    
    def _is_flat_number(self, block_number: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted number is actually a flat number"""
        before_context = address[max(0, match_start-30):match_start].lower()
        after_context = address[match_end:match_end+30].lower()
        full_context = address[max(0, match_start-30):match_end+30].lower()
        
        # If "block" or "sector" is in the context, it's definitely a block number
        if any(kw in full_context for kw in ['block', 'blk', 'sector', 'sct', 'ব্লক', 'সেক্টর']):
            return False
        
        # Check for flat keywords before
        flat_keywords = ['flat', 'flt', 'apt', 'apartment', 'unit', 'suite', 'ফ্ল্যাট', 'স্যুট']
        if any(kw in before_context[-20:] for kw in flat_keywords):
            # If number has letter suffix (e.g., "3A", "4B") or letter prefix (e.g., "C7", "C33b"), it's likely a flat number
            if re.match(r'^\d+[A-Za-z]', block_number) or re.match(r'^[A-Za-z]\d+[A-Za-z]?', block_number):
                return True
        
        # Patterns like "C7", "C33b", "9A" without block context are likely flat numbers
        if re.match(r'^[A-Za-z]\d+[A-Za-z]?$', block_number) or re.match(r'^\d+[A-Za-z]$', block_number):
            # If no block context nearby, likely flat number
            if not any(kw in full_context for kw in ['block', 'blk', 'sector', 'sct', 'ব্লক', 'সেক্টর']):
                return True
        
        return False
    
    def _is_city_or_area_name(self, block_number: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted text is actually a city or area name"""
        block_lower = block_number.lower().strip()
        
        # Check against known city names
        if block_lower in self.city_names:
            return True
        
        # Check against known area names
        if block_lower in self.area_names:
            return True
        
        # If it's a multi-word capitalized text (like "Green City", "Lake City"), it's likely an area name
        if re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]+)*$', block_number):
            # Check if it's followed by common area indicators
            after_context = address[match_end:match_end+20].lower()
            if any(kw in after_context for kw in ['city', 'area', 'colony', 'housing', 'society', 'estate']):
                return True
        
        return False
    
    def _validate_block_number(self, number: str) -> bool:
        """Validate extracted block number"""
        if not number or len(number) > 10:
            return False
        
        # Block numbers can be:
        # - Single letter (A-Z)
        # - Single digit (1-9)
        # - Multiple digits (12, 13, 14)
        # - Bangla numerals (converted to English)
        # - Banglish forms (Cha, Ka, Ga, etc.)
        
        # Check if it's a valid block format
        if re.match(r'^[A-Za-z]$', number):
            return True  # Single letter block
        
        if re.match(r'^[A-Za-z]{2,}$', number):
            return True  # Banglish form (Cha, Ka, etc.)
        
        if re.match(r'^[\d০-৯]{1,3}$', number):
            return True  # 1-3 digit block
        
        # Invalid patterns
        for pattern in self.invalid_patterns:
            if re.match(pattern, number):
                return False
        return True
        
    def extract(self, address: str) -> BlockNumberResult:
        """Extract block number from address"""
        if not address:
            return BlockNumberResult("", 0.0, ExtractionMethod.NOT_FOUND, address, "Empty address")
            
        original_address = address
        original_address_for_bangla = address
        address = self._bangla_to_english_number(address)
        
        # Skip institutional addresses
        if self._is_institutional(address):
            return BlockNumberResult("", 0.0, ExtractionMethod.INSTITUTIONAL, original_address, "Institutional address")
        
        # Try patterns in order of confidence
        all_patterns = [
            (self.explicit_block_patterns, ExtractionMethod.EXPLICIT_BLOCK),
            (self.explicit_sector_patterns, ExtractionMethod.EXPLICIT_SECTOR),
            (self.explicit_blk_patterns, ExtractionMethod.EXPLICIT_BLK),
            (self.bangla_patterns, ExtractionMethod.BANGLA_PATTERN),
            (self.contextual_patterns, ExtractionMethod.CONTEXTUAL),
            (self.positional_patterns, ExtractionMethod.POSITIONAL),
        ]
        
        all_matches = []
        
        for patterns, method in all_patterns:
            for pattern, confidence in patterns:
                # For Bangla patterns, match against original address
                if method == ExtractionMethod.BANGLA_PATTERN:
                    search_text = original_address_for_bangla
                else:
                    search_text = address
                    
                match = re.search(pattern, search_text, re.IGNORECASE)
                if match:
                    block_number = match.group(1).strip()
                    
                    # Clean up - remove trailing punctuation
                    block_number = block_number.rstrip(',.')
                    
                    # For Bangla patterns, convert to Banglish
                    if method == ExtractionMethod.BANGLA_PATTERN:
                        # Convert Bangla numerals to English
                        block_number = self._bangla_to_english_number(block_number)
                        # Convert Bangla letters to Banglish if needed
                        if any(char in block_number for char in self.bangla_to_banglish.keys()):
                            block_number = self._bangla_letter_to_banglish(block_number)
                    
                    # Normalize to uppercase for single letter blocks only
                    # Keep Banglish forms as-is (e.g., "Cha", "Ka")
                    if re.match(r'^[A-Za-z]$', block_number):
                        block_number = block_number.upper()
                    elif re.match(r'^[A-Za-z]{2,}$', block_number):
                        # Banglish form - capitalize first letter
                        block_number = block_number.capitalize()
                    
                    # Validate block number
                    if not self._validate_block_number(block_number):
                        continue
                    
                    # Get match positions
                    match_start_pos = match.start(1)
                    match_end_pos = match.end(1)
                    
                    # Check exclusions
                    if self._is_postal_code(block_number, address, match_start_pos, match_end_pos):
                        continue
                    
                    if self._is_house_number(block_number, address, match_start_pos, match_end_pos):
                        continue
                    
                    if self._is_road_number(block_number, address, match_start_pos, match_end_pos):
                        continue
                    
                    if self._is_flat_number(block_number, address, match_start_pos, match_end_pos):
                        continue
                    
                    if self._is_city_or_area_name(block_number, address, match_start_pos, match_end_pos):
                        continue
                    
                    # Store match for later prioritization
                    all_matches.append({
                        'block_number': block_number,
                        'confidence': confidence,
                        'method': method,
                        'pattern': pattern,
                        'match_start': match.start(),
                        'match_end': match.end(),
                    })
        
        if not all_matches:
            return BlockNumberResult("", 0.0, ExtractionMethod.NOT_FOUND, original_address, "No pattern matched")
        
        # Prioritize matches: prefer explicit patterns, higher confidence, earlier position
        def get_priority(match):
            priority = 0
            
            # Explicit patterns get highest priority
            if match['method'] in [ExtractionMethod.EXPLICIT_BLOCK, ExtractionMethod.EXPLICIT_SECTOR]:
                priority += 10000
            elif match['method'] == ExtractionMethod.EXPLICIT_BLK:
                priority += 8000
            elif match['method'] == ExtractionMethod.BANGLA_PATTERN:
                priority += 7000
            elif match['method'] == ExtractionMethod.CONTEXTUAL:
                priority += 3000
            elif match['method'] == ExtractionMethod.POSITIONAL:
                priority += 1000
            
            # Add confidence as secondary priority
            priority += match['confidence'] * 100
            
            # Add position bonus (earlier in address is better for block numbers)
            position_bonus = (1 - match['match_start'] / len(address)) * 100
            priority += position_bonus
            
            return priority
        
        # Sort by priority (highest first)
        all_matches.sort(key=get_priority, reverse=True)
        
        # Return the best match
        best_match = all_matches[0]
        return BlockNumberResult(
            block_number=best_match['block_number'],
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
    """Extract block number from single address"""
    print("=" * 80)
    print("BLOCK NUMBER EXTRACTION")
    print("=" * 80)
    print()
    print(f"Address: {address}")
    print()
    
    extractor = AdvancedBlockNumberExtractor()
    result = extractor.extract(address)
    
    print(f"Block Number:  {result.block_number or '(not found)'}")
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
    
    extractor = AdvancedBlockNumberExtractor(confidence_threshold=confidence)
    
    print("🔄 Processing records...")
    extracted_count = 0
    confidence_dist = {'>95': 0, '90-95': 0, '85-90': 0, '80-85': 0, '75-80': 0, '70-75': 0, '<70': 0}
    
    for i, record in enumerate(data, 1):
        if i % 100 == 0:
            print(f"   Processed {i}/{len(data)} records...")
        
        address = record.get('address', '')
        result = extractor.extract(address)
        
        if result.confidence >= confidence:
            if 'components' not in record:
                record['components'] = {}
            record['components']['block_number'] = result.block_number
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
            if 'components' not in record:
                record['components'] = {}
            record['components']['block_number'] = ""
    
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
        output_dir = 'data/json/processing/block'
    
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
    
    extractor = AdvancedBlockNumberExtractor()
    
    # Categories (with numbered prefixes for sorting)
    categories = {
        '1.excellent_95_100': (0.95, 1.01),
        '2.very_high_90_95': (0.90, 0.95),
        '3.high_85_90': (0.85, 0.90),
        '4.good_80_85': (0.80, 0.85),
        '5.medium_high_75_80': (0.75, 0.80),
        '6.medium_70_75': (0.70, 0.75),
        '7.acceptable_65_70': (0.65, 0.70),
        '8.low_below_65': (0.00, 0.65),
    }
    
    split_data = {cat: [] for cat in categories.keys()}
    split_data['no_block_number'] = []
    
    print("🔄 Categorizing records...")
    for i, record in enumerate(data, 1):
        if i % 100 == 0:
            print(f"   Processed {i}/{len(data)} records...")
        
        address = record.get('address', '')
        result = extractor.extract(address)
        
        # Create new record with only block_number in components
        new_record = {
            'id': record.get('id'),
            'address': address,
            'components': {
                'block_number': result.block_number if result.confidence >= 0.65 and result.block_number else ''
            }
        }
        
        if result.block_number and result.confidence >= 0.65:
            # Find appropriate category
            for cat_name, (min_conf, max_conf) in categories.items():
                if min_conf <= result.confidence < max_conf:
                    split_data[cat_name].append(new_record)
                    break
        else:
            split_data['no_block_number'].append(new_record)
    
    print()
    print("💾 Saving split datasets...")
    
    # Save each category
    for cat_name, records in split_data.items():
        if cat_name == 'no_block_number':
            cat_path = output_path / cat_name / 'data.json'
        else:
            cat_path = output_path / 'with_block_number' / cat_name / 'data.json'
        
        save_json(cat_path, records)
        print(f"   ✓ {cat_name}: {len(records)} records")
    
    print()
    print("=" * 80)
    print("SPLIT COMPLETE")
    print("=" * 80)
    print()


# ============================================================================
# COMMAND: REPROCESS ALL
# ============================================================================

def cmd_reprocess_all(input_file: str = None, output_dir: str = None):
    """Re-process all confidence levels"""
    if input_file is None:
        input_file = 'data/json/real-customer-address-dataset.json'
    if output_dir is None:
        output_dir = 'data/json/processing/block'
    
    print("=" * 80)
    print("RE-PROCESSING ALL LEVELS")
    print("=" * 80)
    print()
    
    # Just call split again
    cmd_split(input_file, output_dir)


# ============================================================================
# COMMAND: UPDATE SUMMARY
# ============================================================================

def cmd_update_summary(base_dir: str = None):
    """Update split summary statistics"""
    if base_dir is None:
        base_dir = 'data/json/processing/block'
    
    base_path = Path(base_dir)
    
    print("=" * 80)
    print("UPDATING SPLIT SUMMARY")
    print("=" * 80)
    print()
    
    categories = [
        '1.excellent_95_100', '2.very_high_90_95', '3.high_85_90', '4.good_80_85',
        '5.medium_high_75_80', '6.medium_70_75', '7.acceptable_65_70', '8.low_below_65'
    ]
    
    print("📂 Loading data files...")
    category_counts = {}
    for cat in categories:
        cat_path = base_path / 'with_block_number' / cat / 'data.json'
        if cat_path.exists():
            data = load_json(cat_path)
            category_counts[cat] = len(data)
            print(f"   ✓ {cat}: {len(data)} records")
        else:
            category_counts[cat] = 0
            print(f"   ✓ {cat}: 0 records")
    
    no_block_path = base_path / 'no_block_number' / 'data.json'
    if no_block_path.exists():
        no_block_data = load_json(no_block_path)
        no_block_count = len(no_block_data)
        print(f"   ✓ no_block_number: {no_block_count} records")
    else:
        no_block_count = 0
        print(f"   ✓ no_block_number: 0 records")
    
    total_records = sum(category_counts.values()) + no_block_count
    with_block = sum(category_counts.values())
    
    # Format to match splited_district_division format
    summary = [{
        'statistics': {
            'total_records': total_records,
            'with_block_number': with_block,
            'without_block_number': no_block_count,
            'coverage_percentage': round(with_block / total_records * 100, 1) if total_records > 0 else 0,
            'confidence_breakdown': {
                cat: category_counts[cat]
                for cat in categories
            }
        }
    }]
    
    summary_path = base_path / 'split_summary.json'
    save_json(summary_path, summary)
    
    print()
    print("=" * 80)
    print("SUMMARY UPDATED")
    print("=" * 80)
    print()
    stats = summary[0]['statistics']
    print(f"Total Records:         {stats['total_records']:,}")
    print(f"With Block Number:     {stats['with_block_number']:,} ({stats['coverage_percentage']:.1f}%)")
    print(f"Without Block Number:  {stats['without_block_number']:,} ({100 - stats['coverage_percentage']:.1f}%)")
    print()
    print("Confidence Breakdown:")
    for cat in categories:
        count = stats['confidence_breakdown'][cat]
        pct = round(count / stats['total_records'] * 100, 1) if stats['total_records'] > 0 else 0
        if count > 0:
            print(f"  {cat:<25} {count:>4} records ({pct:>5.1f}%)")
    print()
    print(f"💾 Summary saved to: {summary_path}")
    print()


# ============================================================================
# MAIN CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Block Number Processor')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract block number from single address')
    extract_parser.add_argument('address', help='Address to extract from')
    extract_parser.add_argument('--details', action='store_true', help='Show detailed information')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process entire dataset')
    process_parser.add_argument('--confidence', type=float, default=0.70, help='Confidence threshold (default: 0.70)')
    process_parser.add_argument('--input', type=str, help='Input JSON file path')
    process_parser.add_argument('--output', type=str, help='Output JSON file path')
    
    # Split command
    split_parser = subparsers.add_parser('split', help='Split dataset by confidence levels')
    split_parser.add_argument('--input', type=str, help='Input JSON file path')
    split_parser.add_argument('--output', type=str, help='Output directory path')
    
    # Reprocess all command
    reprocess_parser = subparsers.add_parser('reprocess-all', help='Re-process all confidence levels')
    reprocess_parser.add_argument('--input', type=str, help='Input JSON file path')
    reprocess_parser.add_argument('--output', type=str, help='Output directory path')
    
    # Update summary command
    summary_parser = subparsers.add_parser('update-summary', help='Update split summary statistics')
    summary_parser.add_argument('--base-dir', type=str, help='Base directory path')
    
    args = parser.parse_args()
    
    if args.command == 'extract':
        cmd_extract(args.address, args.details)
    elif args.command == 'process':
        cmd_process(args.confidence, args.input, args.output)
    elif args.command == 'split':
        cmd_split(args.input, args.output)
    elif args.command == 'reprocess-all':
        cmd_reprocess_all(args.input, args.output)
    elif args.command == 'update-summary':
        cmd_update_summary(args.base_dir)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

