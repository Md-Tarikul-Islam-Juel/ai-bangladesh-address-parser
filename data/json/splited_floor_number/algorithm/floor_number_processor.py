#!/usr/bin/env python3
"""
Complete Floor Number Processor - All-in-One Solution
======================================================

Single comprehensive script for Bangladeshi address floor number extraction,
processing, organization, and management.

Features:
    1. Extract floor numbers from addresses (Core Algorithm)
    2. Process entire dataset with confidence filtering
    3. Split dataset by confidence levels
    4. Re-process specific confidence folders
    5. Sync changes between split and main dataset

Usage:
    # Extract from single address
    python3 floor_number_processor.py extract "3rd floor, Left side lalmatia housing estate"
    
    # Process entire dataset
    python3 floor_number_processor.py process --confidence 0.70
    
    # Split dataset by confidence
    python3 floor_number_processor.py split
    
    # Re-process specific confidence level
    python3 floor_number_processor.py reprocess 2.very_high_90_95
    
    # Update main dataset from split
    python3 floor_number_processor.py sync 2.very_high_90_95

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
    EXPLICIT_FLOOR = "explicit_floor"
    EXPLICIT_LEVEL = "explicit_level"
    EXPLICIT_LIFT = "explicit_lift"
    ORDINAL_FLOOR = "ordinal_floor"
    BANGLA_PATTERN = "bangla_pattern"
    CONTEXTUAL = "contextual"
    POSITIONAL = "positional"
    NOT_FOUND = "not_found"
    NOT_CONFIDENT = "not_confident"
    INSTITUTIONAL = "institutional_skip"


@dataclass
class FloorNumberResult:
    """Result of floor number extraction"""
    floor_number: str
    confidence: float
    method: ExtractionMethod
    original: str = ""
    reason: str = ""
    
    def __str__(self):
        return f"FloorNumber('{self.floor_number}', {self.confidence:.1%}, {self.method.value})"
    
    def to_dict(self) -> Dict:
        return {
            'floor_number': self.floor_number,
            'confidence': self.confidence,
            'method': self.method.value,
            'original': self.original,
            'reason': self.reason
        }


class AdvancedFloorNumberExtractor:
    """Advanced AI-Based Floor Number Extractor for Bangladeshi Addresses"""
    
    def __init__(self, preserve_format: bool = True, confidence_threshold: float = 0.70):
        self.preserve_format = preserve_format
        self.confidence_threshold = confidence_threshold
        self._setup_advanced_patterns()
        self._setup_exclusions()
        self._setup_bangla_mappings()
        
    def _setup_advanced_patterns(self):
        """Setup advanced extraction patterns"""
        
        # EXPLICIT FLOOR PATTERNS (95-100% confidence)
        self.explicit_floor_patterns = [
            # Floor No: 3, Floor No. 3, Floor Number: 3
            (r'(?:floor|flr|fl)[\s]+(?:no\.?|number|:)[\s\-]*([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),
            # Floor-3, Floor - 3, Floor: 3
            (r'(?:floor|flr|fl)[\s\-:]+([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Floor # 3, Floor#3
            (r'(?:floor|flr|fl)[\s]*#[\s]*([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),
        ]
        
        # EXPLICIT LEVEL PATTERNS (95-100% confidence)
        self.explicit_level_patterns = [
            # Level 3, Level-3, Level: 3
            (r'(?:level|lvl)[\s\-:]+([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),
            # Level No: 3, Level No. 3
            (r'(?:level|lvl)[\s]+(?:no\.?|number|:)[\s\-]*([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),
            # Level # 3, Level#3
            (r'(?:level|lvl)[\s]*#[\s]*([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),
        ]
        
        # EXPLICIT LIFT PATTERNS (90-95% confidence)
        # Note: "Lift 12" might refer to lift number, but often indicates floor
        self.explicit_lift_patterns = [
            # Lift 12, Lift-12, Lift: 12
            (r'(?:lift|lft)[\s\-:]+([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.90),
            # Lift No: 12, Lift No. 12
            (r'(?:lift|lft)[\s]+(?:no\.?|number|:)[\s\-]*([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.92),
        ]
        
        # ORDINAL FLOOR PATTERNS (90-100% confidence)
        # 3rd floor, 4th floor, 5th floor, 1st floor, 2nd floor
        self.ordinal_floor_patterns = [
            # 3rd floor, 4th floor, 5th floor (most common) - more flexible lookahead
            (r'([\d০-৯]+)(?:st|nd|rd|th)[\s]+(?:floor|flr|fl)(?=\s*[,\(\)]|\s|,|$)', 1.00),
            # 3rd Floor, 4th Floor (capitalized)
            (r'([\d০-৯]+)(?:st|nd|rd|th)[\s]+Floor(?=\s*[,\(\)]|\s|,|$)', 1.00),
            # 3rd floor flat, 4th floor flat (with flat keyword)
            (r'([\d০-৯]+)(?:st|nd|rd|th)[\s]+(?:floor|flr|fl)[\s]+(?:flat|flt)(?=\s*[,\(\)]|\s|,|$)', 0.95),
            # Floor 3rd, Floor 4th (less common, reversed)
            (r'(?:floor|flr|fl)[\s]+([\d০-৯]+)(?:st|nd|rd|th)(?=\s*[,\(\)]|\s|,|$)', 0.90),
        ]
        
        # BANGLA PATTERNS (90-100% confidence)
        self.bangla_patterns = [
            # তলা ৩, তলা ৪, তলা ৫
            (r'তলা[\s\-:]+([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),
            # ৩য় তলা, ৪র্থ তলা, ৫ম তলা
            (r'([\d০-৯]+)(?:য়|র্থ|ম|ষ্ঠ|সপ্তম|অষ্টম|নবম|দশম)[\s]+তলা(?=\s*[,\(\)]|\s|$)', 1.00),
            # ৩য় তলায়, ৪র্থ তলায় (with "at" suffix)
            (r'([\d০-৯]+)(?:য়|র্থ|ম|ষ্ঠ|সপ্তম|অষ্টম|নবম|দশম)[\s]+তলায়(?=\s*[,\(\)]|\s|$)', 1.00),
            # লেভেল ৩, লেভেল ৪
            (r'লেভেল[\s\-:]+([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),
            # তলা নং ৩, তলা নম্বর ৩
            (r'তলা[\s]+(?:নং|নম্বর|:)[\s\-]*([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),
        ]
        
        # CONTEXTUAL PATTERNS (80-90% confidence)
        self.contextual_patterns = [
            # Number followed by "floor" without ordinal (e.g., "3 floor", "4 floor")
            (r'([\d০-৯]+)[\s]+(?:floor|flr|fl)(?=\s*[,\(\)]|\s|$)', 0.85),
            # "Floor" followed by number (e.g., "Floor 3", "Floor 4")
            (r'(?:floor|flr|fl)[\s]+([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.85),
            # "Level" followed by number (already covered in explicit_level_patterns, but lower confidence here)
            (r'(?:level|lvl)[\s]+([\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.80),
        ]
        
        # POSITIONAL PATTERNS (70-80% confidence)
        # Floor number at start of address
        self.positional_patterns = [
            # Number at start followed by "floor" or "level"
            (r'^([\d০-৯]+)[\s]+(?:floor|flr|fl|level|lvl)(?=\s*[,\(\)]|\s|$)', 0.75),
        ]
        
    def _setup_exclusions(self):
        """Setup exclusion patterns and keywords"""
        # Invalid patterns (should not be extracted as floor numbers)
        self.invalid_patterns = [
            r'^\d{4,}$',  # 4+ digit numbers (likely postal codes or house numbers)
            r'^\d{1,2}/\d+',  # Slash patterns (likely house/road numbers)
            r'^[A-Za-z]',  # Starting with letter (likely flat numbers or building names)
        ]
        
        # Keywords that indicate this is NOT a floor number
        self.exclusion_keywords = [
            'house', 'home', 'bari', 'basha', 'road', 'rd', 'street', 'st',
            'lane', 'avenue', 'ave', 'building', 'bldg', 'tower', 'flat',
            'apt', 'apartment', 'unit', 'suite', 'postal', 'zip', 'code'
        ]
        
    def _setup_bangla_mappings(self):
        """Setup Bangla numeral to English conversion"""
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
        """Check if address is institutional (skip floor extraction)"""
        address_lower = address.lower()
        institutional_keywords = [
            'bank', 'hospital', 'clinic', 'school', 'college', 'university',
            'mosque', 'masjid', 'temple', 'church', 'office', 'corporate',
            'branch', 'ltd', 'limited', 'plc', 'company', 'corporation'
        ]
        
        institutional_count = sum(1 for kw in institutional_keywords if kw in address_lower)
        
        # If 2+ institutional keywords, likely institutional address
        return institutional_count >= 2
    
    def _is_house_number(self, floor_number: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted number is actually a house number"""
        before_context = address[max(0, match_start-30):match_start].lower()
        after_context = address[match_end:match_end+30].lower()
        full_context = address[max(0, match_start-30):match_end+30].lower()
        
        # If "floor" or "level" is in the context (before or after), it's definitely a floor number
        if any(kw in full_context for kw in ['floor', 'flr', 'fl', 'level', 'lvl', 'lift', 'তলা', 'লেভেল']):
            return False
        
        # Check for house keywords before
        house_keywords = ['house', 'home', 'hous', 'bari', 'basha', 'building', 'bldg', 'plot', 'holding']
        for keyword in house_keywords:
            if keyword in before_context[-20:]:
                # If number is 3+ digits, it's likely house number
                if re.match(r'^\d{3,}', floor_number):
                    return True
        
        return False
    
    def _is_road_number(self, floor_number: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted number is actually a road number"""
        before_context = address[max(0, match_start-30):match_start].lower()
        after_context = address[match_end:match_end+30].lower()
        full_context = address[max(0, match_start-30):match_end+30].lower()
        
        # If "floor" or "level" is in the context (before or after), it's definitely a floor number
        if any(kw in full_context for kw in ['floor', 'flr', 'fl', 'level', 'lvl', 'lift', 'তলা', 'লেভেল']):
            return False
        
        # Check for road keywords
        road_keywords = ['road', 'rd', 'street', 'st', 'lane', 'avenue', 'ave', 'goli', 'রোড', 'লেন']
        for keyword in road_keywords:
            if keyword in after_context[:20]:
                # If number is followed by road keyword, it's likely road number
                return True
        
        return False
    
    def _is_postal_code(self, floor_number: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted number is actually a postal code"""
        # Postal codes are typically 4 digits
        if re.match(r'^\d{4}$', floor_number):
            # If "floor" or "level" is in the context, it's definitely a floor number
            before_context = address[:match_end].lower()
            if any(kw in before_context for kw in ['floor', 'flr', 'fl', 'level', 'lvl', 'lift', 'তলা', 'লেভেল']):
                return False
            
            # Check if it's at the end of address or after city name
            if match_end >= len(address) - 10:
                return True
        
        return False
    
    def _is_flat_number(self, floor_number: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted number is actually a flat number"""
        before_context = address[max(0, match_start-30):match_start].lower()
        after_context = address[match_end:match_end+30].lower()
        full_context = address[max(0, match_start-30):match_end+30].lower()
        
        # If "floor" or "level" is in the context (before or after), it's definitely a floor number
        if any(kw in full_context for kw in ['floor', 'flr', 'fl', 'level', 'lvl', 'lift', 'তলা', 'লেভেল']):
            return False
        
        # Check for flat keywords before
        flat_keywords = ['flat', 'flt', 'apt', 'apartment', 'unit', 'suite', 'ফ্ল্যাট', 'স্যুট']
        if any(kw in before_context[-20:] for kw in flat_keywords):
            # If number has letter suffix (e.g., "3A", "4B"), it's likely a flat number
            if re.match(r'^\d+[A-Za-z]', floor_number):
                return True
        
        return False
    
    def _validate_floor_number(self, number: str) -> bool:
        """Validate extracted floor number"""
        if not number or len(number) > 10:
            return False
        
        # Floor numbers are typically 1-3 digits
        if not re.match(r'^[\d০-৯]{1,3}$', number):
            return False
        
        for pattern in self.invalid_patterns:
            if re.match(pattern, number):
                return False
        return True
        
    def extract(self, address: str) -> FloorNumberResult:
        """Extract floor number from address"""
        if not address:
            return FloorNumberResult("", 0.0, ExtractionMethod.NOT_FOUND, address, "Empty address")
            
        original_address = address
        original_address_for_bangla = address
        address = self._bangla_to_english_number(address)
        
        # Skip institutional addresses
        if self._is_institutional(address):
            return FloorNumberResult("", 0.0, ExtractionMethod.INSTITUTIONAL, original_address, "Institutional address")
        
        # Try patterns in order of confidence
        all_patterns = [
            (self.explicit_floor_patterns, ExtractionMethod.EXPLICIT_FLOOR),
            (self.explicit_level_patterns, ExtractionMethod.EXPLICIT_LEVEL),
            (self.explicit_lift_patterns, ExtractionMethod.EXPLICIT_LIFT),
            (self.ordinal_floor_patterns, ExtractionMethod.ORDINAL_FLOOR),
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
                    floor_number = match.group(1).strip()
                    
                    # Clean up - remove trailing punctuation
                    floor_number = floor_number.rstrip(',.')
                    
                    # For Bangla patterns, preserve original format but convert numbers
                    if method == ExtractionMethod.BANGLA_PATTERN:
                        # Convert Bangla numerals to English for consistency
                        floor_number = self._bangla_to_english_number(floor_number)
                    
                    # Validate floor number
                    if not self._validate_floor_number(floor_number):
                        continue
                    
                    # Get match positions
                    match_start_pos = match.start(1)
                    match_end_pos = match.end(1)
                    
                    # Check exclusions
                    if self._is_postal_code(floor_number, address, match_start_pos, match_end_pos):
                        continue
                    
                    if self._is_house_number(floor_number, address, match_start_pos, match_end_pos):
                        continue
                    
                    if self._is_road_number(floor_number, address, match_start_pos, match_end_pos):
                        continue
                    
                    if self._is_flat_number(floor_number, address, match_start_pos, match_end_pos):
                        continue
                    
                    # Store match for later prioritization
                    all_matches.append({
                        'floor_number': floor_number,
                        'confidence': confidence,
                        'method': method,
                        'pattern': pattern,
                        'match_start': match.start(),
                        'match_end': match.end(),
                    })
        
        if not all_matches:
            return FloorNumberResult("", 0.0, ExtractionMethod.NOT_FOUND, original_address, "No pattern matched")
        
        # Prioritize matches: prefer explicit patterns, higher confidence, earlier position
        def get_priority(match):
            priority = 0
            
            # Explicit patterns get highest priority
            if match['method'] in [ExtractionMethod.EXPLICIT_FLOOR, ExtractionMethod.EXPLICIT_LEVEL]:
                priority += 10000
            elif match['method'] == ExtractionMethod.EXPLICIT_LIFT:
                priority += 8000
            elif match['method'] == ExtractionMethod.ORDINAL_FLOOR:
                priority += 7000
            elif match['method'] == ExtractionMethod.BANGLA_PATTERN:
                priority += 6000
            elif match['method'] == ExtractionMethod.CONTEXTUAL:
                priority += 3000
            elif match['method'] == ExtractionMethod.POSITIONAL:
                priority += 1000
            
            # Add confidence as secondary priority
            priority += match['confidence'] * 100
            
            # Add position bonus (earlier in address is better for floor numbers)
            position_bonus = (1 - match['match_start'] / len(address)) * 100
            priority += position_bonus
            
            return priority
        
        # Sort by priority (highest first)
        all_matches.sort(key=get_priority, reverse=True)
        
        # Return the best match
        best_match = all_matches[0]
        return FloorNumberResult(
            floor_number=best_match['floor_number'],
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
    """Extract floor number from single address"""
    print("=" * 80)
    print("FLOOR NUMBER EXTRACTION")
    print("=" * 80)
    print()
    print(f"Address: {address}")
    print()
    
    extractor = AdvancedFloorNumberExtractor()
    result = extractor.extract(address)
    
    print(f"Floor Number:  {result.floor_number or '(not found)'}")
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
        input_file = 'src/app/shared/utils/address-parser/data/json/real-customer-address-dataset.json'
    if output_file is None:
        output_file = 'src/app/shared/utils/address-parser/data/json/real-customer-address-dataset-processed.json'
    
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
    
    extractor = AdvancedFloorNumberExtractor(confidence_threshold=confidence)
    
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
            record['components']['floor_number'] = result.floor_number
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
            record['components']['floor_number'] = ""
    
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
        input_file = 'src/app/shared/utils/address-parser/data/json/real-customer-address-dataset.json'
    if output_dir is None:
        output_dir = 'src/app/shared/utils/address-parser/data/json/splited_floor_number'
    
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
    
    extractor = AdvancedFloorNumberExtractor()
    
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
    split_data['no_floor_number'] = []
    
    print("🔄 Categorizing records...")
    for i, record in enumerate(data, 1):
        if i % 100 == 0:
            print(f"   Processed {i}/{len(data)} records...")
        
        address = record.get('address', '')
        result = extractor.extract(address)
        
        # Create new record with only floor_number in components
        new_record = {
            'id': record.get('id'),
            'address': address,
            'components': {
                'floor_number': result.floor_number if result.confidence >= 0.65 and result.floor_number else ''
            }
        }
        
        if result.floor_number and result.confidence >= 0.65:
            # Find appropriate category
            for cat_name, (min_conf, max_conf) in categories.items():
                if min_conf <= result.confidence < max_conf:
                    split_data[cat_name].append(new_record)
                    break
        else:
            split_data['no_floor_number'].append(new_record)
    
    print()
    print("💾 Saving split datasets...")
    
    # Save each category
    for cat_name, records in split_data.items():
        if cat_name == 'no_floor_number':
            cat_path = output_path / cat_name / 'data.json'
        else:
            cat_path = output_path / 'with_floor_number' / cat_name / 'data.json'
        
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
        input_file = 'src/app/shared/utils/address-parser/data/json/real-customer-address-dataset.json'
    if output_dir is None:
        output_dir = 'src/app/shared/utils/address-parser/data/json/splited_floor_number'
    
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
        base_dir = 'src/app/shared/utils/address-parser/data/json/splited_floor_number'
    
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
        cat_path = base_path / 'with_floor_number' / cat / 'data.json'
        if cat_path.exists():
            data = load_json(cat_path)
            category_counts[cat] = len(data)
            print(f"   ✓ {cat}: {len(data)} records")
        else:
            category_counts[cat] = 0
            print(f"   ✓ {cat}: 0 records")
    
    no_floor_path = base_path / 'no_floor_number' / 'data.json'
    if no_floor_path.exists():
        no_floor_data = load_json(no_floor_path)
        no_floor_count = len(no_floor_data)
        print(f"   ✓ no_floor_number: {no_floor_count} records")
    else:
        no_floor_count = 0
        print(f"   ✓ no_floor_number: 0 records")
    
    total_records = sum(category_counts.values()) + no_floor_count
    with_floor = sum(category_counts.values())
    
    # Format to match splited_district_division format
    summary = [{
        'statistics': {
            'total_records': total_records,
            'with_floor_number': with_floor,
            'without_floor_number': no_floor_count,
            'coverage_percentage': round(with_floor / total_records * 100, 1) if total_records > 0 else 0,
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
    print(f"With Floor Number:     {stats['with_floor_number']:,} ({stats['coverage_percentage']:.1f}%)")
    print(f"Without Floor Number:  {stats['without_floor_number']:,} ({100 - stats['coverage_percentage']:.1f}%)")
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
    parser = argparse.ArgumentParser(description='Floor Number Processor')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract floor number from single address')
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

