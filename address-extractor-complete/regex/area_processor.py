#!/usr/bin/env python3
"""
Complete Area Processor - All-in-One Solution
=============================================

Single comprehensive script for Bangladeshi address area extraction,
processing, organization, and management.

Features:
    1. Extract area names from addresses (Core Algorithm)
    2. Process entire dataset with confidence filtering
    3. Split dataset by confidence levels
    4. Re-process specific confidence folders
    5. Update summary statistics

Usage:
    # Extract from single address
    python3 area_processor.py extract "House 48, Road 5, Banasree, Dhaka"
    
    # Process entire dataset
    python3 area_processor.py process --confidence 0.70
    
    # Split dataset by confidence
    python3 area_processor.py split
    
    # Re-process all levels
    python3 area_processor.py reprocess-all
    
    # Update summary
    python3 area_processor.py update-summary

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
    EXPLICIT_AREA = "explicit_area"
    BANGLA_PATTERN = "bangla_pattern"
    CONTEXTUAL = "contextual"
    POSITIONAL = "positional"
    NOT_FOUND = "not_found"
    NOT_CONFIDENT = "not_confident"
    INSTITUTIONAL = "institutional_skip"


@dataclass
class AreaResult:
    """Result of area extraction"""
    area: str
    confidence: float
    method: ExtractionMethod
    original: str = ""
    reason: str = ""
    
    def __str__(self):
        return f"Area('{self.area}', {self.confidence:.1%}, {self.method.value})"
    
    def to_dict(self) -> Dict:
        return {
            'area': self.area,
            'confidence': self.confidence,
            'method': self.method.value,
            'original': self.original,
            'reason': self.reason
        }


class AdvancedAreaExtractor:
    """Advanced AI-Based Area Extractor for Bangladeshi Addresses"""
    
    def __init__(self, preserve_format: bool = True, confidence_threshold: float = 0.70):
        self.preserve_format = preserve_format
        self.confidence_threshold = confidence_threshold
        self._load_area_data()
        self._setup_advanced_patterns()
        self._setup_exclusions()
        
    def _load_area_data(self):
        """Load area mappings from JSON file"""
        area_file = Path('data/json/area-mappings.json')
        try:
            with open(area_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.area_mappings = data.get('area_mappings', {})
        except FileNotFoundError:
            self.area_mappings = {}
        
        # Flatten all areas into a single list with variations
        self.all_areas = []
        self.area_variations = {}
        
        for city, areas in self.area_mappings.items():
            for area in areas:
                area_lower = area.lower().strip()
                self.all_areas.append(area_lower)
                # Store variations (with/without numbers, with/without spaces)
                variations = [
                    area_lower,
                    area_lower.replace(' ', ''),
                    area_lower.replace('-', ' '),
                    area_lower.replace('-', ''),
                ]
                for var in variations:
                    if var not in self.area_variations:
                        self.area_variations[var] = area_lower
        
        # Common area patterns
        self.common_areas = [
            'uttara', 'dhanmondi', 'gulshan', 'banani', 'rampura', 'khilgaon',
            'mirpur', 'mohammadpur', 'tejgaon', 'motijheel', 'farmgate', 'shyamoli',
            'adabor', 'mohakhali', 'baridhara', 'banasree', 'meradia', 'shantinagar',
            'wari', 'lalbagh', 'azimpur', 'bashabo', 'jatrabari', 'demra', 'hazaribagh',
            'badda', 'khilkhet', 'bashundhara', 'nikunja', 'agrabad', 'halishahar',
            'panchlaish', 'katalgonj', 'nasirabad', 'chawkbazar', 'lalkhan bazar',
            'amberkhana', 'zindabazar', 'sapura', 'sonadanga', 'fatullah', 'siddhirganj',
            'kochukhet', 'fulbaria', 'sitakunda', 'pahartali', 'laxmipur', 'horogram',
            'lohagara', 'kajla', 'dharampur', 'madaripur', 'satkhira', 'noakhali'
        ]
        
    def _setup_advanced_patterns(self):
        """Setup advanced extraction patterns for area detection"""
        
        # Get all area names from area_mappings for comprehensive pattern matching
        area_names_pattern = '|'.join(self.common_areas)
        
        # EXPLICIT AREA PATTERNS (95-100% confidence)
        self.explicit_area_patterns = [
            # Pattern 1: Directional prefix + Area name (e.g., "North Badda" -> extract "Badda")
            (r'\b(?:north|south|east|west|middle|uttar|dakshin|purbo|paschim|উত্তর|দক্ষিণ|পূর্ব|পশ্চিম)\s+(badda|dhanmondi|goran|pallabi|jatrabari|rampura|agrabad|pirerbag|ahmednagar|nakhalpara|bishil|anand|nagar|khan|খান|ধানমন্ডি|বাড্ডা|যাত্রাবাড়ী|রামপুরা|আগ্রাবাদ|মিরপুর|উত্তরা|গুলশান|বনানী|খিলগাঁও|মোহাম্মদপুর|তেজগাঁও|মতিঝিল|শ্যামলী|আদাবর|মোহাখালী|বারিধারা|বনশ্রী|মেরাদিয়া|শান্তিনগর|ওয়ারী|লালবাগ|আজিমপুর|বাসাবো|সাবুজবাগ|হাজারীবাগ|খিলক্ষেত|বসুন্ধরা|নিকুঞ্জ|হালিশহর|পাঁচলাইশ|কাতলগঞ্জ|নাসিরাবাদ|চকবাজার|আম্বরখানা|জিন্দাবাজার|সাপুরা|সোনাডাঙ্গা|ফতুল্লা|সিদ্ধিরগঞ্জ)\b', 0.95),
            # Pattern 2: Area name with "Sector" keyword (e.g., "Uttara Sector 12" -> extract "Uttara")
            (r'\b(uttara|dhanmondi|gulshan|banani|rampura|khilgaon|mirpur|mohammadpur|tejgaon|motijheel|farmgate|shyamoli|adabor|mohakhali|baridhara|banasree|meradia|shantinagar|wari|lalbagh|azimpur|bashabo|jatrabari|demra|hazaribagh|badda|khilkhet|bashundhara|nikunja|agrabad|halishahar|panchlaish|katalgonj|nasirabad|chawkbazar|amberkhana|zindabazar|sapura|sonadanga|fatullah|siddhirganj)\s+(?:sector|sec)\s+\d+(?=\s*[,\(\)]|\s*$)', 0.98),
            # Pattern 3: Area name with "Block" keyword (e.g., "Banasree H Block" -> extract "Banasree")
            (r'\b(uttara|dhanmondi|gulshan|banani|rampura|khilgaon|mirpur|mohammadpur|tejgaon|motijheel|farmgate|shyamoli|adabor|mohakhali|baridhara|banasree|meradia|shantinagar|wari|lalbagh|azimpur|bashabo|jatrabari|demra|hazaribagh|badda|khilkhet|bashundhara|nikunja|agrabad|halishahar|panchlaish|katalgonj|nasirabad|chawkbazar|amberkhana|zindabazar|sapura|sonadanga|fatullah|siddhirganj)\s+[A-Za-z]\s+(?:block|blk)(?=\s*[,\(\)]|\s*$)', 0.98),
            (r'\b(uttara|dhanmondi|gulshan|banani|rampura|khilgaon|mirpur|mohammadpur|tejgaon|motijheel|farmgate|shyamoli|adabor|mohakhali|baridhara|banasree|meradia|shantinagar|wari|lalbagh|azimpur|bashabo|jatrabari|demra|hazaribagh|badda|khilkhet|bashundhara|nikunja|agrabad|halishahar|panchlaish|katalgonj|nasirabad|chawkbazar|amberkhana|zindabazar|sapura|sonadanga|fatullah|siddhirganj)\s+(?:block|blk)\s+[A-Za-z\d]+(?=\s*[,\(\)]|\s*$)', 0.98),
            # Pattern 4: Area name with number (e.g., "Mirpur 10", "Gulshan 2" -> extract "Mirpur"/"Gulshan")
            (r'\b(uttara|dhanmondi|gulshan|banani|rampura|khilgaon|mirpur|mohammadpur|tejgaon|motijheel|farmgate|shyamoli|adabor|mohakhali|baridhara|banasree|meradia|shantinagar|wari|lalbagh|azimpur|bashabo|jatrabari|demra|hazaribagh|badda|khilkhet|bashundhara|nikunja|agrabad|halishahar|panchlaish|katalgonj|nasirabad|chawkbazar|amberkhana|zindabazar|sapura|sonadanga|fatullah|siddhirganj)[\s\-]+\d+(?=\s*[,\(\)]|\s*$)', 0.95),
            # Pattern 5: Area name followed by comma or end of address (standalone area)
            (r'\b(uttara|dhanmondi|gulshan|banani|rampura|khilgaon|mirpur|mohammadpur|tejgaon|motijheel|farmgate|shyamoli|adabor|mohakhali|baridhara|banasree|meradia|shantinagar|wari|lalbagh|azimpur|bashabo|jatrabari|demra|hazaribagh|badda|khilkhet|bashundhara|nikunja|agrabad|halishahar|panchlaish|katalgonj|nasirabad|chawkbazar|amberkhana|zindabazar|sapura|sonadanga|fatullah|siddhirganj)\b(?=\s*[,\(\)]|\s*$)', 1.00),
        ]
        
        # BANGLA PATTERNS (90-100% confidence)
        self.bangla_patterns = [
            # Pattern 1: Bangla directional prefix + Area name (e.g., "পশ্চিম ধানমন্ডি" -> extract "ধানমন্ডি")
            (r'\b(?:উত্তর|দক্ষিণ|পূর্ব|পশ্চিম|মধ্য)\s+(ধানমন্ডি|বাড্ডা|যাত্রাবাড়ী|রামপুরা|আগ্রাবাদ|মিরপুর|উত্তরা|গুলশান|বনানী|খিলগাঁও|মোহাম্মদপুর|তেজগাঁও|মতিঝিল|শ্যামলী|আদাবর|মোহাখালী|বারিধারা|বনশ্রী|মেরাদিয়া|শান্তিনগর|ওয়ারী|লালবাগ|আজিমপুর|বাসাবো|সাবুজবাগ|হাজারীবাগ|খিলক্ষেত|বসুন্ধরা|নিকুঞ্জ|হালিশহর|পাঁচলাইশ|কাতলগঞ্জ|নাসিরাবাদ|চকবাজার|আম্বরখানা|জিন্দাবাজার|সাপুরা|সোনাডাঙ্গা|ফতুল্লা|সিদ্ধিরগঞ্জ)\b', 0.95),
            # Pattern 2: Bangla area names with numbers (e.g., "মিরপুর ১০" -> extract "মিরপুর")
            (r'(মিরপুর|গুলশান|বনানী|উত্তরা|ধানমন্ডি)\s+[০-৯]+(?=\s*[,\(\)]|\s*$)', 0.98),
            # Pattern 3: Common Bangla area names (standalone)
            (r'(মিরপুর|গুলশান|বনানী|উত্তরা|ধানমন্ডি|মোহাম্মদপুর|রামপুরা|খিলগাঁও|মতিঝিল|তেজগাঁও|লালবাগ|ওয়ারী|শান্তিনগর|মালিবাগ|মগবাজার|শাহবাগ|কাওরান|পান্থপথ|নীলক্ষেত|আজিমপুর|বাসাবো|সাবুজবাগ|যাত্রাবাড়ী|হাজারীবাগ|ক্যান্টনমেন্ট|বাড্ডা|খিলক্ষেত|বারিধারা|বসুন্ধরা|আদাবর|মোহাখালী)(?=\s*[,\(\)]|\s*$)', 1.00),
        ]
        
        # CONTEXTUAL PATTERNS (80-95% confidence)
        # IMPORTANT: These patterns prioritize main area names when they appear after locality names
        self.contextual_patterns = [
            # Pattern 1: "Gram: [area]" or "গ্রাম: [area]" format (e.g., "Gram: Daribishandi" -> extract "Daribishandi")
            # HIGHEST PRIORITY - explicit area mention
            (r'\b(?:gram|গ্রাম)\s*:\s*([A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)*)(?=\s*[,\(\)]|\s*$)', 0.98),
            # Pattern 2: "Thana [area]" format (e.g., "Thana Satkania" -> extract "Satkania")
            (r'\bthana\s+([A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)*)(?=\s*[,\(\)]|\s*$)', 0.95),
            # Pattern 3: "Puran Dhaka" / "Old Dhaka" / "poran Dhaka" variations
            (r'\b(?:puran|poran|old)\s+dhaka\b', 0.98),
            # Pattern 4: Known area after building/market name (e.g., "Aziz Mansion, ... Kochukhet" -> extract "Kochukhet")
            # This pattern uses a more flexible approach - looks for known areas after comma-separated parts
            # We'll use a dynamic pattern that checks against all_areas in the extraction logic
            (r'\b([A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)*(?:\s+[A-Za-z][a-z]+)*)\s*,\s*(?:[A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)*(?:\s*,\s*[A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)*)*\s*,\s*)?([A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)*)(?=\s*[,\(\)]|\s*$)', 0.92),
            # Pattern 4: Main area name after locality (e.g., "..., Badda, Dhaka" or "..., Mirpur, Dhaka")
            # This pattern should have HIGH priority to catch main areas that appear after locality names
            (r'\b(?:[A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)*(?:\s*,\s*[A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)*)*\s*,\s*)?(badda|uttara|mirpur|dhanmondi|gulshan|banani|rampura|khilgaon|mohammadpur|tejgaon|motijheel|farmgate|shyamoli|adabor|mohakhali|baridhara|banasree|meradia|shantinagar|wari|lalbagh|azimpur|bashabo|jatrabari|demra|hazaribagh|khilkhet|bashundhara|nikunja|agrabad|halishahar|panchlaish|katalgonj|nasirabad|chawkbazar|amberkhana|zindabazar|sapura|sonadanga|fatullah|siddhirganj)\s*,\s*(?:dhaka|chittagong|chattogram|sylhet|rajshahi|khulna|barisal|rangpur|mymensingh|comilla|cumilla|narayanganj|gazipur|noakhali|feni|coxs?\s+bazar|jessore|jashore|bogra|bogura|dinajpur|sirajganj|pabna|naogaon|jamalpur|kishoreganj|tangail|munshiganj|madaripur|faridpur|gopalganj|shariatpur|rajbari|manikganj|narsingdi|brahmanbaria|chandpur|lakshmipur|bandarban|rangamati|khagrachhari|moulvibazar|habiganj|sunamganj|chapainawabganj|natore|joypurhat|thakurgaon|panchagarh|nilphamari|lalmonirhat|kurigram|gaibandha|bagerhat|satkhira|jhenaidah|magura|narail|kushtia|meherpur|chuadanga|bhola|patuakhali|pirojpur|barguna|jhalokati|sherpur|netrokona|\d{4})\b', 0.98),
            # Pattern 5: Main area name with number after locality (e.g., "..., Mirpur 2, Dhaka" or "..., Mirpur 60 feet")
            (r'\b(?:[A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)*(?:\s*,\s*[A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)*)*\s*,\s*)?(badda|uttara|mirpur|dhanmondi|gulshan|banani|rampura|khilgaon|mohammadpur|tejgaon|motijheel|farmgate|shyamoli|adabor|mohakhali|baridhara|banasree|meradia|shantinagar|wari|lalbagh|azimpur|bashabo|jatrabari|demra|hazaribagh|khilkhet|bashundhara|nikunja|agrabad|halishahar|panchlaish|katalgonj|nasirabad|chawkbazar|amberkhana|zindabazar|sapura|sonadanga|fatullah|siddhirganj)\s+[\d০-৯]+(?:\s+feet)?(?=\s*[,\(\)]|\s*$)', 0.98),
            # Pattern 6: Locality names before main area (e.g., "South Goran, Shantipur, Khilgaon" -> extract "Khilgaon")
            (r'\b(?:north|south|east|west|purbo|paschim|uttar|dakshin|middle|মধ্য|উত্তর|দক্ষিণ|পূর্ব|পশ্চিম)\s+[A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)*\s*,\s*(uttara|dhanmondi|gulshan|banani|rampura|khilgaon|mirpur|mohammadpur|tejgaon|motijheel|farmgate|shyamoli|adabor|mohakhali|baridhara|banasree|meradia|shantinagar|wari|lalbagh|azimpur|bashabo|jatrabari|demra|hazaribagh|badda|khilkhet|bashundhara|nikunja|agrabad|halishahar|panchlaish|katalgonj|nasirabad|chawkbazar|amberkhana|zindabazar|sapura|sonadanga|fatullah|siddhirganj)\b', 0.90),
            # Pattern 7: Multiple locality names before main area (e.g., "South Goran, Shantipur, Khilgaon" -> extract "Khilgaon")
            (r'\b(?:[A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)*\s*,\s*[A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)*)\s*,\s*(uttara|dhanmondi|gulshan|banani|rampura|khilgaon|mirpur|mohammadpur|tejgaon|motijheel|farmgate|shyamoli|adabor|mohakhali|baridhara|banasree|meradia|shantinagar|wari|lalbagh|azimpur|bashabo|jatrabari|demra|hazaribagh|badda|khilkhet|bashundhara|nikunja|agrabad|halishahar|panchlaish|katalgonj|nasirabad|chawkbazar|amberkhana|zindabazar|sapura|sonadanga|fatullah|siddhirganj)\b', 0.90),
            # Pattern 8: Single locality name before main area (e.g., "Shantipur, Khilgaon" -> extract "Khilgaon")
            (r'\b([A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)*)\s*,\s*(uttara|dhanmondi|gulshan|banani|rampura|khilgaon|mirpur|mohammadpur|tejgaon|motijheel|farmgate|shyamoli|adabor|mohakhali|baridhara|banasree|meradia|shantinagar|wari|lalbagh|azimpur|bashabo|jatrabari|demra|hazaribagh|badda|khilkhet|bashundhara|nikunja|agrabad|halishahar|panchlaish|katalgonj|nasirabad|chawkbazar|amberkhana|zindabazar|sapura|sonadanga|fatullah|siddhirganj)\b', 0.85),
            # Pattern 9: Area name before city/district name
            (r'\b([A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)*)\s+(?:dhaka|chittagong|chattogram|sylhet|rajshahi|khulna|barisal|rangpur|mymensingh|comilla|cumilla|narayanganj|gazipur|noakhali|feni|coxs?\s+bazar|jessore|jashore|bogra|bogura|dinajpur|sirajganj|pabna|naogaon|jamalpur|kishoreganj|tangail|munshiganj|madaripur|faridpur|gopalganj|shariatpur|rajbari|manikganj|narsingdi|brahmanbaria|chandpur|lakshmipur|bandarban|rangamati|khagrachhari|moulvibazar|habiganj|sunamganj|chapainawabganj|natore|joypurhat|thakurgaon|panchagarh|nilphamari|lalmonirhat|kurigram|gaibandha|bagerhat|satkhira|jhenaidah|magura|narail|kushtia|meherpur|chuadanga|bhola|patuakhali|pirojpur|barguna|jhalokati|sherpur|netrokona)\b', 0.85),
        ]
        
        # POSITIONAL PATTERNS (70-80% confidence)
        self.positional_patterns = [
            # Area name at start of address followed by comma
            (r'^([A-Za-z][a-z]+(?:\s+[A-Za-z][a-z]+)*)\s*,(?=\s*[A-Z])', 0.75),
        ]
        
    def _setup_exclusions(self):
        """Setup comprehensive exclusion patterns and keywords from all processors"""
        # Load all 64 districts from bd-districts.json
        districts_file = Path('data/json/division/bd-districts.json')
        self.city_names = []
        try:
            with open(districts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                districts = data.get('districts', [])
                for district in districts:
                    value = district.get('value', '').lower()
                    label = district.get('label', '').lower()
                    normalized = district.get('normalized', '').lower()
                    self.city_names.extend([value, label, normalized])
        except FileNotFoundError:
            pass
        
        # Add common variations
        self.city_names.extend([
            'dhaka', 'dacca', 'dakha', 'chittagong', 'chattogram', 'ctg', 'comilla', 'cumilla',
            'rajshahi', 'khulna', 'sylhet', 'barisal', 'rangpur', 'mymensingh',
            'narayanganj', 'gazipur', 'noakhali', 'feni', 'coxs bazar', 'cox\'s bazar',
            'jessore', 'jashore', 'bogra', 'bogura', 'dinajpur', 'sirajganj',
            'pabna', 'naogaon', 'jamalpur', 'kishoreganj', 'tangail', 'munshiganj',
            'madaripur', 'faridpur', 'gopalganj', 'shariatpur', 'rajbari',
            'manikganj', 'narsingdi', 'brahmanbaria', 'chandpur', 'lakshmipur',
            'bandarban', 'rangamati', 'khagrachhari', 'moulvibazar', 'habiganj',
            'sunamganj', 'chapainawabganj', 'natore', 'joypurhat', 'thakurgaon',
            'panchagarh', 'nilphamari', 'lalmonirhat', 'kurigram', 'gaibandha',
            'bagerhat', 'satkhira', 'jhenaidah', 'magura', 'narail', 'kushtia',
            'meherpur', 'chuadanga', 'bhola', 'patuakhali', 'pirojpur', 'barguna',
            'jhalokati', 'sherpur', 'netrokona'
        ])
        self.city_names = list(set(self.city_names))  # Remove duplicates
        
        # Building/landmark names that should NOT be extracted as areas
        self.building_keywords = [
            'tower', 'building', 'bldg', 'apartment', 'apt', 'complex', 'plaza',
            'mall', 'market', 'bazar', 'bazaar', 'hospital', 'school', 'college',
            'university', 'mosque', 'masjid', 'temple', 'church', 'bank', 'office',
            'residence', 'villa', 'mansion', 'center', 'centre', 'supermarket',
            'restaurant', 'hotel', 'cafe', 'station', 'airport', 'port',
            # Additional building/complex names from analysis
            'kormokorta', 'abashon', 'shapla', 'castle', 'palace', 'textile',
            'laboratory', 'lab', 'colony', 'housing', 'society', 'estate',
            'diagnostic', 'center', 'clinic', 'court', 'tower', 'road',
            'quarter', 'residential', 'area', 'zone', 'gate', 'station',
            'power', 'house', 'para', 'niketon', 'garden', 'park'
        ]
        
        # House number keywords (from house_number_processor)
        self.house_keywords = [
            'house', 'home', 'hous', 'bari', 'basha', 'building', 'bldg',
            'plot', 'holding', 'no', 'number', 'h#', 'h-', 'h:', 'h '
        ]
        
        # Road number keywords (from road_number_processor)
        self.road_keywords = [
            'road', 'rd', 'street', 'st', 'lane', 'avenue', 'ave', 'goli',
            'রোড', 'লেন', 'r#', 'r-', 'r:', 'r '
        ]
        
        # Flat number keywords (from flat_number_processor)
        self.flat_keywords = [
            'flat', 'flt', 'apt', 'apartment', 'unit', 'suite', 'ফ্ল্যাট', 'স্যুট'
        ]
        
        # Block number keywords (from block_processor)
        self.block_keywords = [
            'block', 'blk', 'sector', 'sct', 'ব্লক', 'সেক্টর'
        ]
        
        # Postal code patterns (from postal_code_processor)
        self.postal_code_patterns = [
            r'\b\d{4}\b',  # 4-digit postal codes
            r'post\s*code', r'postal\s*code', r'p\.?o\.?\s*box', r'zip\s*code'
        ]
        
        # Floor number keywords (from floor_number_processor)
        self.floor_keywords = [
            'floor', 'flr', 'fl', 'level', 'lvl', 'তলা'
        ]
        
        # Division names (from district_processor)
        self.division_names = [
            'dhaka', 'chattogram', 'chittagong', 'sylhet', 'rajshahi',
            'khulna', 'barisal', 'rangpur', 'mymensingh',
            'ঢাকা', 'চট্টগ্রাম', 'সিলেট', 'রাজশাহী', 'খুলনা', 'বরিশাল', 'রংপুর', 'ময়মনসিংহ'
        ]
        
        # District/sub-district names that should be excluded (e.g., "Rangpur Sadar", "Dhaka Sadar")
        self.sadar_names = [
            'sadar', 'সদর', 'sodor', 'sodar'
        ]
        
        # Known locality/sub-area names that should be excluded when main area names appear later
        # These are sub-areas within main areas (e.g., "Anand Nagar" is in "Badda", "Pirerbag" is in "Mirpur")
        self.locality_names = [
            # Badda localities
            'anand', 'anand nagar', 'south anand nagar', 'north anand nagar', 'aftab nagar', 'aftabnagar',
            'merul badda', 'middle badda', 'south badda', 'north badda', 'uttar badda', 'tekpara', 
            'sonakatra', 'baithkali', 'dit project',
            # Uttara localities
            'khan', 'dakshin khan', 'uttarkhan', 'raja bari', 'ashkona', 'prem bagan',
            # Mirpur localities
            'pirerbag', 'north pirerbag', 'south pirerbag', 'middle pirerbag', 'east pirerbag', 'west pirerbag',
            'ahmednagar', 'east ahmednagar', 'west ahmednagar', 'north ahmednagar', 'south ahmednagar',
            'pallabi', 'south pallabi', 'north pallabi', 'west pallabi', 'east pallabi',
            'kazipara', 'west kazipara', 'east kazipara', 'shewrapara', 'west shewrapara',
            'kalshi', 'north kalshi', 'south kalshi', 'nakhalpara', 'west nakhalpara',
            'bishil', 'north bishil', 'south bishil', 'goran', 'south goran', 'north goran',
            'shantipur', 'shantinagar', 'shamoli', 'shyamoli', 'adabor',
            # Dhanmondi localities
            'kalabagan', 'zigatola', 'jigatola', 'kataban', 'katabon', 'lalmatia',
            # Gulshan/Banani localities
            'niketan', 'baridhara', 'baridhara dohs', 'khilkhet', 'banasree',
            # Mohammadpur localities
            'shahjadpur', 'shahjadpur bashtola', 'lalmatia housing estate',
            # Other common localities
            'nakhalpara', 'west nakhalpara', 'east nakhalpara', 'north nakhalpara',
            'shantinagar', 'shantipur', 'shamoli', 'shyamoli',
            'goran', 'south goran', 'north goran', 'east goran', 'west goran',
            'bishil', 'north bishil', 'south bishil',
            'anand', 'anand nagar', 'south anand nagar', 'north anand nagar',
            'pirerbag', 'north pirerbag', 'south pirerbag', 'middle pirerbag',
            'ahmednagar', 'east ahmednagar', 'west ahmednagar',
            'khan', 'dakshin khan', 'uttarkhan',
            'kazipara', 'west kazipara', 'east kazipara',
            'shewrapara', 'west shewrapara',
            'kalshi', 'north kalshi', 'south kalshi',
            'pallabi', 'south pallabi', 'north pallabi',
        ]
        
        # Main area names (these should be prioritized over locality names)
        self.main_area_names = [
            'badda', 'uttara', 'mirpur', 'dhanmondi', 'gulshan', 'banani', 'rampura',
            'khilgaon', 'mohammadpur', 'tejgaon', 'motijheel', 'farmgate', 'shyamoli',
            'adabor', 'mohakhali', 'baridhara', 'banasree', 'meradia', 'shantinagar',
            'wari', 'lalbagh', 'azimpur', 'bashabo', 'jatrabari', 'demra', 'hazaribagh',
            'khilkhet', 'bashundhara', 'nikunja', 'agrabad', 'halishahar', 'panchlaish',
            'katalgonj', 'nasirabad', 'chawkbazar', 'amberkhana', 'zindabazar', 'sapura',
            'sonadanga', 'fatullah', 'siddhirganj'
        ]
        
    def _is_institutional(self, address: str) -> bool:
        """Check if address is institutional (skip area extraction)"""
        address_lower = address.lower()
        institutional_keywords = [
            'bank', 'hospital', 'clinic', 'school', 'college', 'university',
            'mosque', 'masjid', 'temple', 'church', 'office', 'corporate',
            'branch', 'ltd', 'limited', 'plc', 'company', 'corporation'
        ]
        
        institutional_count = sum(1 for kw in institutional_keywords if kw in address_lower)
        return institutional_count >= 2
    
    def _is_keyword_not_area(self, area: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted text is a keyword that should not be extracted as area"""
        area_lower = area.lower().strip()
        
        # Keywords that should never be extracted as areas
        excluded_keywords = [
            'district', 'jela', 'জেলা', 'thana', 'থানা', 'post', 'gram', 'গ্রাম',
            'university', 'of', 'faculty', 'college', 'school', 'hospital',
            'office', 'building', 'tower', 'mansion', 'store', 'department',
            'studies', 'business', 'main', 'road', 'foods'
        ]
        
        if area_lower in excluded_keywords:
            return True
        
        # Check if "District" keyword appears before the match
        before_context = address[max(0, match_start-30):match_start].lower()
        after_context = address[match_end:match_end+30].lower()
        full_context = address[max(0, match_start-30):match_end+30].lower()
        
        # If "District" or "Jela" appears in context, don't extract it as area
        if re.search(r'\b(district|jela|জেলা)\s+', full_context, re.IGNORECASE):
            if area_lower in ['district', 'jela', 'জেলা']:
                return True
        
        # If "University of" pattern appears, don't extract "University" or "Of" as area
        if re.search(r'\buniversity\s+of\b', full_context, re.IGNORECASE):
            if area_lower in ['university', 'of', 'university of']:
                return True
        
        # If "Faculty of" pattern appears, don't extract anything as area (institutional address)
        if re.search(r'\bfaculty\s+of\b', full_context, re.IGNORECASE):
            return True
        
        # If "Thana" keyword appears before the match, check if we're extracting "Thana" itself or "Thana: [name]"
        if re.search(r'\bthana\s*:?\s*', before_context[-30:], re.IGNORECASE):
            # Exclude "Thana:" patterns completely
            if 'thana' in area_lower or re.search(r'\bthana\s*:?\s*', full_context, re.IGNORECASE):
                return True
        
        # Exclude patterns like "Thana: Double Mooring", "Thana Panchlaish"
        if re.search(r'\bthana\s*:?\s*', full_context, re.IGNORECASE):
            # If the area appears after "Thana:" or "Thana ", exclude it
            if re.search(r'\bthana\s*:?\s*' + re.escape(area) + r'\b', full_context, re.IGNORECASE):
                return True
        
        return False
    
    def _is_city_name(self, area: str) -> bool:
        """Check if extracted text is actually a city/district name"""
        area_lower = area.lower().strip()
        return area_lower in self.city_names
    
    def _is_building_name(self, area: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted text is actually a building/landmark name"""
        area_lower = area.lower()
        
        # IMPORTANT: If this is a known area (especially main area), it's NOT a building name
        # This prevents excluding valid areas that happen to contain building keywords
        if area_lower in self.main_area_names:
            return False  # Main areas are never building names
        
        if area_lower in self.all_areas:
            # It's a known area - check if it appears after a building name
            # If it does, it's likely the actual area, not a building
            before_context = address[max(0, match_start-50):match_start].lower()
            has_building_before = any(kw in before_context for kw in self.building_keywords)
            
            # If it appears after building and is a known area, it's the area, not a building
            if has_building_before and match_start > 20:
                return False  # This is the area, not a building
        
        # Check if the extracted area itself contains building keywords
        contains_building_keyword = False
        for keyword in self.building_keywords:
            if keyword in area_lower:
                contains_building_keyword = True
                break
        
        if contains_building_keyword:
            # Check if a known area appears AFTER this match
            address_after = address[match_end:].lower()
            
            # Check main area names
            for main_area in self.main_area_names:
                pattern = r'\b' + re.escape(main_area) + r'\b'
                if re.search(pattern, address_after):
                    # Known area found after building name - exclude building
                    return True
            
            # Check all known areas
            for known_area in self.all_areas:
                if len(known_area) > 3:  # Only check substantial area names
                    pattern = r'\b' + re.escape(known_area.lower()) + r'\b'
                    if re.search(pattern, address_after):
                        return True
            
            # If no known area found after, still exclude if it's clearly a building
            # But only if it's at the start of address (common pattern)
            if match_start < 50:  # Near start of address
                return True
        
        before_context = address[max(0, match_start-30):match_start].lower()
        after_context = address[match_end:match_end+30].lower()
        
        # Check for building keywords nearby
        for keyword in self.building_keywords:
            if keyword in before_context[-20:] or keyword in after_context[:20]:
                # If a known area appears after, exclude this
                address_after = address[match_end:].lower()
                for main_area in self.main_area_names:
                    pattern = r'\b' + re.escape(main_area) + r'\b'
                    if re.search(pattern, address_after):
                        return True
                # If near start and no known area after, exclude
                if match_start < 50:
                    return True
        
        return False
    
    def _is_house_number(self, area: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted text is actually a house number (from house_number_processor)"""
        # IMPORTANT: If it's a known area name, it's NOT a house number
        area_lower = area.lower()
        if area_lower in self.all_areas or area_lower in self.main_area_names or area_lower in self.common_areas:
            return False  # Known areas are never house numbers
        
        before_context = address[max(0, match_start-30):match_start].lower()
        after_context = address[match_end:match_end+30].lower()
        full_context = address[max(0, match_start-30):match_end+30].lower()
        
        # Check for house keywords before the match
        for keyword in self.house_keywords:
            if keyword in before_context[-20:]:
                # STRICT: Only if it's actually a number pattern (not a word)
                if re.match(r'^[\d০-৯]+([/\-][\d০-৯]+)?([A-Za-z])?$', area):
                    return True
        
        # Check for patterns like "H#", "H-", "H:" before the area
        # But only if the area itself is a number
        if re.search(r'\b[h]\s*[#:\-]\s*', before_context[-15:], re.IGNORECASE):
            if re.match(r'^[\d০-৯]+([/\-][\d০-৯]+)?([A-Za-z])?$', area):
                return True
        
        return False
    
    def _is_road_number(self, area: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted text is actually a road number (from road_number_processor)"""
        before_context = address[max(0, match_start-30):match_start].lower()
        after_context = address[match_end:match_end+30].lower()
        
        # Check for road keywords after the match
        for keyword in self.road_keywords:
            if keyword in after_context[:20]:
                # If it's a number pattern, likely road number
                if re.match(r'^[\d০-৯]+([/\-][\d০-৯]+)?$', area):
                    return True
        
        # Check for patterns like "R#", "R-", "R:" before the area
        if re.search(r'\b[r]\s*[#:\-]\s*', before_context[-15:], re.IGNORECASE):
            return True
        
        return False
    
    def _is_postal_code(self, area: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted text is actually a postal code (from postal_code_processor)"""
        # Postal codes are typically 4 digits
        if re.match(r'^\d{4}$', area):
            before_context = address[:match_end].lower()
            after_context = address[match_end:match_end+20].lower()
            
            # Check for postal code keywords
            postal_keywords = ['post', 'postal', 'code', 'zip', 'p.o', 'po box']
            for keyword in postal_keywords:
                if keyword in before_context[-30:] or keyword in after_context[:20]:
                    return True
            
            # If it's at the end of address or after city name, likely postal code
            if match_end >= len(address) - 10:
                # Check if city name is before it
                for city in self.city_names[:10]:  # Check major cities
                    if city in before_context[-30:]:
                        return True
        
        return False
    
    def _is_flat_number(self, area: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted text is actually a flat number (from flat_number_processor)"""
        before_context = address[max(0, match_start-30):match_start].lower()
        after_context = address[match_end:match_end+30].lower()
        full_context = address[max(0, match_start-30):match_end+30].lower()
        
        # Check for flat keywords before the match
        for keyword in self.flat_keywords:
            if keyword in before_context[-20:]:
                # If it's a flat number pattern (letter+number, number+letter, etc.)
                if re.match(r'^[A-Za-z]?[\d০-৯]+[A-Za-z]?$', area) or \
                   re.match(r'^[\d০-৯]+[/\-][A-Za-z]$', area) or \
                   re.match(r'^[A-Za-z][/\-][\d০-৯]+$', area):
                    return True
        
        return False
    
    def _is_block_number(self, area: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted text is actually a block number (from block_processor)"""
        area_lower = area.lower().strip()
        
        before_context = address[max(0, match_start-30):match_start].lower()
        after_context = address[match_end:match_end+30].lower()
        full_context = address[max(0, match_start-50):match_end+30].lower()  # Wider context
        
        # STRICT: If "block" or "blk" keyword is in context, check if it's a block pattern
        for keyword in self.block_keywords:
            if keyword in full_context:
                # Pattern: "Block A", "Block B", "Block C", "Block - C", "Block-B" etc.
                if re.search(r'\bblock\s*[-:]?\s*' + re.escape(area) + r'\b', full_context, re.IGNORECASE):
                    # EXCEPTION: Only exclude if it's NOT a known area name (e.g., "Block Road" might be an area)
                    if area_lower not in self.all_areas and area_lower not in self.main_area_names:
                        return True
                # Pattern: "A Block", "B Block", "C Block", "H block" etc. - letter before "block"
                if re.search(r'\b' + re.escape(area) + r'\s+block\b', full_context, re.IGNORECASE):
                    # EXCEPTION: Only exclude if it's NOT a known area name
                    if area_lower not in self.all_areas and area_lower not in self.main_area_names:
                        return True
                # Pattern: "Block - C", "Block-B" (with dash)
                if re.search(r'\bblock\s*[-]\s*' + re.escape(area) + r'\b', full_context, re.IGNORECASE):
                    # EXCEPTION: Only exclude if it's NOT a known area name
                    if area_lower not in self.all_areas and area_lower not in self.main_area_names:
                        return True
                # Single letter (A-Z) or letter with dash (A-B, C-D) is likely a block
                if re.match(r'^[A-Za-z]$', area) or re.match(r'^[A-Za-z]\s*[-]\s*[A-Za-z]$', area):
                    return True  # Always exclude single letters in block context
                # Short numbers (1-2 digits) with block context are likely block numbers
                if re.match(r'^[\d০-৯]{1,2}$', area):
                    return True  # Always exclude short numbers in block context
                # For longer text, only exclude if it's NOT a known area
                if area_lower not in self.all_areas and area_lower not in self.main_area_names and area_lower not in self.common_areas:
                    return True
        
        return False
    
    def _is_division(self, area: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted text is actually a division name (from district_processor)"""
        area_lower = area.lower().strip()
        
        # Check if it's a division name
        if area_lower in self.division_names:
            return True
        
        # Check for division keywords in context
        before_context = address[max(0, match_start-30):match_start].lower()
        after_context = address[match_end:match_end+30].lower()
        full_context = address[max(0, match_start-30):match_end+30].lower()
        
        division_keywords = ['division', 'বিভাগ']
        for keyword in division_keywords:
            if keyword in full_context:
                return True
        
        # Check if it's a "Sadar" pattern (e.g., "Rangpur Sadar", "Dhaka Sadar")
        # These are district/sub-district names, not areas
        for sadar_name in self.sadar_names:
            if sadar_name in area_lower:
                # Check if a city/district name appears before it
                before_text = address[max(0, match_start-50):match_start].lower()
                for city in self.city_names[:30]:
                    if city in before_text:
                        return True  # It's a district/sub-district name like "Rangpur Sadar"
        
        # Also check if the area itself contains a city name + "Sadar" pattern
        # e.g., "Rangpur Sadar" should be excluded
        for city in self.city_names[:30]:
            if city in area_lower:
                for sadar_name in self.sadar_names:
                    if sadar_name in area_lower:
                        return True  # Pattern like "Rangpur Sadar"
        
        return False
    
    def _is_locality_name(self, area: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted text is a locality name and a main area name appears later in the address"""
        area_lower = area.lower().strip()
        
        # Check if it's a known locality name
        is_locality = False
        for locality in self.locality_names:
            if area_lower == locality.lower() or locality.lower() in area_lower or area_lower in locality.lower():
                is_locality = True
                break
        
        if not is_locality:
            return False
        
        # Check if a main area name appears AFTER this match in the address
        address_after_match = address[match_end:].lower()
        
        # Check for main area names after the match
        for main_area in self.main_area_names:
            # Use word boundary to avoid partial matches
            pattern = r'\b' + re.escape(main_area) + r'\b'
            if re.search(pattern, address_after_match):
                # Main area name found after locality - exclude the locality
                return True
        
        return False
    
    def _is_floor_number(self, area: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted text is actually a floor number (from floor_number_processor)"""
        before_context = address[max(0, match_start-30):match_start].lower()
        after_context = address[match_end:match_end+30].lower()
        full_context = address[max(0, match_start-30):match_end+30].lower()
        
        # Check for floor keywords before or after the match
        for keyword in self.floor_keywords:
            if keyword in full_context:
                # If it's a number or ordinal pattern, likely floor number
                if re.match(r'^[\d০-৯]+(?:th|st|nd|rd)?$', area, re.IGNORECASE):
                    return True
        
        return False
    
    def _bangla_to_english_number(self, text: str) -> str:
        """Convert Bangla numerals to English"""
        bangla_to_english = {
            '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4',
            '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'
        }
        for bangla, english in bangla_to_english.items():
            text = text.replace(bangla, english)
        return text
    
    def _normalize_area(self, area: str) -> str:
        """Normalize area name"""
        area = area.strip()
        
        # Convert Bangla numerals to English if present
        area = self._bangla_to_english_number(area)
        
        area_lower = area.lower()
        
        # Check if it's a known area variation
        if area_lower in self.area_variations:
            normalized = self.area_variations[area_lower]
            # Capitalize first letter of each word
            return ' '.join(word.capitalize() for word in normalized.split())
        
        # If it's in the common areas list, capitalize properly
        if area_lower in self.common_areas:
            return ' '.join(word.capitalize() for word in area_lower.split())
        
        # Default: capitalize first letter of each word
        return ' '.join(word.capitalize() for word in area.split())
    
    def _validate_area(self, area: str, allow_bangla: bool = False) -> bool:
        """Validate extracted area"""
        if not area or len(area) < 3 or len(area) > 50:
            return False
        
        # Must start with letter (English or Bangla)
        if allow_bangla:
            if not re.match(r'^[A-Za-z\u0980-\u09FF]', area):
                return False
        else:
            if not re.match(r'^[A-Za-z]', area):
                return False
        
        # Should not be all numbers
        if re.match(r'^[\d০-৯]+$', area):
            return False
        
        return True
        
    def _intelligent_area_extraction(self, address: str) -> List[Dict]:
        """
        AI-Powered Intelligent Area Extraction
        Uses multi-factor scoring instead of simple pattern matching
        """
        address_lower = address.lower()
        candidates = []
        
        # Split address into parts for context analysis
        parts = [p.strip() for p in address.split(',')]
        
        # PHASE 1: Find all potential area candidates from known areas
        for known_area in self.all_areas:
            # Use word boundary matching
            pattern = r'\b' + re.escape(known_area) + r'\b'
            matches = list(re.finditer(pattern, address_lower, re.IGNORECASE))
            
            for match in matches:
                match_start = match.start()
                match_end = match.end()
                area_text = address[match_start:match_end]
                
                # Calculate intelligent score
                # Start with base score for known areas
                score = 0.20  # Base score for any known area
                reasons = []
                
                # Factor 1: Is it a main area name? (HIGH WEIGHT)
                if known_area in self.main_area_names:
                    score += 0.30
                    reasons.append("main_area")
                elif known_area in self.common_areas:
                    score += 0.15  # Bonus for common areas
                    reasons.append("common_area")
                
                # Factor 2: Position in address (areas typically appear in middle-to-end)
                position_ratio = match_start / len(address) if len(address) > 0 else 0
                if 0.2 <= position_ratio <= 0.8:  # Middle section is ideal
                    score += 0.15
                    reasons.append("good_position")
                elif position_ratio > 0.8:  # Near end is also good
                    score += 0.10
                    reasons.append("end_position")
                
                # Factor 3: Context analysis - what appears before/after
                before_context = address[max(0, match_start-50):match_start].lower()
                after_context = address[match_end:match_end+50].lower()
                
                # Check if it appears after building/market keywords (GOOD SIGN)
                # Check in the full before context, not just last 30 chars
                building_before = any(kw in before_context for kw in self.building_keywords)
                if building_before:
                    score += 0.20
                    reasons.append("after_building")
                
                # Check if it appears before city/district name (EXCELLENT SIGN - MASSIVE BOOST)
                # Check immediate context (first 20 chars) for city names
                city_after_immediate = any(city in after_context[:20] for city in self.city_names[:30])
                if city_after_immediate:
                    score += 0.50  # Massive boost for areas before city names
                    reasons.append("before_city_immediate")
                # Also check slightly further (20-50 chars)
                elif any(city in after_context[20:50] for city in self.city_names[:30]):
                    score += 0.30
                    reasons.append("before_city")
                
                # Check if it appears after comma-separated parts (GOOD SIGN)
                part_index = None
                for i, part in enumerate(parts):
                    if known_area in part.lower():
                        part_index = i
                        break
                
                if part_index is not None and part_index > 0:
                    score += 0.10
                    reasons.append("after_comma")
                
                # Factor 4: Check if previous parts are building names
                if part_index is not None and part_index > 0:
                    previous_parts_text = ' '.join(parts[:part_index]).lower()
                    is_after_building = any(kw in previous_parts_text for kw in self.building_keywords)
                    if is_after_building:
                        score += 0.15
                        reasons.append("after_building_name")
                
                # Factor 5: Check if it's part of a known area pattern (e.g., "Mirpur 6", "Uttara Sector 12")
                area_with_number = re.search(r'\b' + re.escape(known_area) + r'\s+[\d০-৯]+', address[match_start:match_start+30], re.IGNORECASE)
                if area_with_number:
                    score += 0.10
                    reasons.append("with_number")
                
                # Factor 6: Check if it appears with directional prefix (e.g., "North Badda", "Purbo Ganeshpur")
                # Check for directional prefix before the area (check wider context)
                directional_before = re.search(r'\b(?:north|south|east|west|middle|uttar|dakshin|purbo|paschim|উত্তর|দক্ষিণ|পূর্ব|পশ্চিম)\s+' + re.escape(known_area) + r'\b', address[max(0, match_start-30):match_end], re.IGNORECASE)
                if directional_before:
                    score += 0.30  # Increased boost for directional prefixes
                    reasons.append("with_direction")
                    # If it appears early in address with directional prefix, it's likely the main area
                    if position_ratio < 0.4:
                        score += 0.25  # Extra boost for early directional area
                        reasons.append("early_directional_area")
                
                # Factor 7: Penalty if it appears at the very start (likely building name)
                if match_start < 30:
                    # Check if it's definitely a building
                    if any(kw in address[:match_end].lower() for kw in self.building_keywords):
                        score -= 0.30  # Heavy penalty
                        reasons.append("penalty_start_building")
                    else:
                        score -= 0.10  # Light penalty
                        reasons.append("penalty_start")
                
                # Factor 8: Bonus if it's in common areas list
                if known_area in self.common_areas:
                    score += 0.10  # Increased bonus for common areas
                    reasons.append("common_area")
                
                # Factor 9: Check surrounding words for area indicators
                context_words = (before_context[-20:] + ' ' + after_context[:20]).lower()
                area_indicators = ['near', 'beside', 'opposite', 'in', 'at', 'area', 'locality', 'sector', 'block']
                if any(indicator in context_words for indicator in area_indicators):
                    score += 0.05
                    reasons.append("area_context")
                
                # Normalize score to 0-1 range (ensure it's never negative)
                score = max(0.0, min(1.0, score))
                
                # ALWAYS add known areas - intelligent ranking will select the best
                # This ensures we don't miss valid areas due to scoring issues
                is_main_area = known_area in self.main_area_names
                is_common_area = known_area in self.common_areas
                
                # Check if area appears after building name
                before_context_full = address[max(0, match_start-50):match_start].lower()
                is_after_building_direct = any(kw in before_context_full for kw in self.building_keywords)
                
                # Boost score for areas after buildings (strong indicator of correct area)
                if is_after_building_direct and match_start > 20:
                    if score < 0.60:
                        score = 0.75  # Significant boost
                    if 'after_building' not in reasons:
                        reasons.append("after_building")
                    reasons.append("known_area_after_building")
                
                # Boost score for main areas
                if is_main_area:
                    if score < 0.50:
                        score = 0.65  # Minimum score for main areas
                elif is_common_area:
                    if score < 0.40:
                        score = 0.55  # Minimum score for common areas
                else:
                    # For other known areas, ensure minimum score
                    if score < 0.30:
                        score = 0.45  # Minimum score for any known area
                
                # Always add known areas - let intelligent ranking decide
                candidates.append({
                    'area': self._normalize_area(known_area),
                    'score': score,
                    'confidence': score,  # Use score as confidence
                    'match_start': match_start,
                    'match_end': match_end,
                    'reasons': reasons,
                    'is_known': True,
                    'method': ExtractionMethod.CONTEXTUAL,
                    'pattern': f'intelligent_extraction: {", ".join(reasons)}'
                })
        
        # PHASE 2: Also check explicit patterns for additional candidates
        all_patterns = [
            (self.contextual_patterns, ExtractionMethod.CONTEXTUAL),
            (self.explicit_area_patterns, ExtractionMethod.EXPLICIT_AREA),
            (self.bangla_patterns, ExtractionMethod.BANGLA_PATTERN),
        ]
        
        for patterns, method in all_patterns:
            for pattern_info in patterns:
                pattern, base_confidence = pattern_info
                flags = re.UNICODE if method == ExtractionMethod.BANGLA_PATTERN else re.IGNORECASE
                match = re.search(pattern, address, flags)
                if match:
                    # Extract area
                    if match.lastindex and match.lastindex >= 1:
                        area = match.group(1).strip()
                        match_start_pos = match.start(1)
                        match_end_pos = match.end(1)
                    else:
                        continue
                    
                    # For contextual patterns, area might be in group 2
                    if method == ExtractionMethod.CONTEXTUAL and len(match.groups()) >= 2:
                        area = match.group(2).strip()
                        match_start_pos = match.start(2)
                        match_end_pos = match.end(2)
                    
                    area = area.rstrip(',.')
                    area = self._normalize_area(area)
                    
                    if not self._validate_area(area, allow_bangla=(method == ExtractionMethod.BANGLA_PATTERN)):
                        continue
                    
                    # Check exclusions - CRITICAL: Block numbers must be excluded first
                    if self._is_block_number(area, address, match_start_pos, match_end_pos):
                        continue
                    if self._is_city_name(area):
                        continue
                    if self._is_building_name(area, address, match_start_pos, match_end_pos):
                        continue
                    if self._is_keyword_not_area(area, address, match_start_pos, match_end_pos):
                        continue
                    
                    area_lower = area.lower()
                    is_known_area = area_lower in self.all_areas or area_lower in self.common_areas
                    
                    # Adjust confidence
                    if not is_known_area and base_confidence > 0.90:
                        base_confidence = 0.80
                    
                    # Check if already in candidates
                    already_exists = any(c['area'].lower() == area_lower for c in candidates)
                    if not already_exists:
                        candidates.append({
                            'area': area,
                            'score': base_confidence,
                            'confidence': base_confidence,
                            'match_start': match_start_pos,
                            'match_end': match_end_pos,
                            'reasons': ['pattern_match'],
                            'is_known': is_known_area,
                            'method': method,
                            'pattern': str(pattern)
                        })
        
        return candidates
    
    def extract(self, address: str) -> AreaResult:
        """Extract area from address using intelligent AI-powered extraction"""
        if not address:
            return AreaResult("", 0.0, ExtractionMethod.NOT_FOUND, address, "Empty address")
            
        original_address = address
        address_lower = address.lower()
        
        # Skip institutional addresses
        if self._is_institutional(address):
            return AreaResult("", 0.0, ExtractionMethod.INSTITUTIONAL, original_address, "Institutional address")
        
        # Use intelligent extraction
        all_matches = self._intelligent_area_extraction(address)
        
        # Additional validation: Remove candidates that fail exclusion checks
        # BUT: Known areas should be protected from most exclusions
        validated_matches = []
        for match in all_matches:
            area = match['area']
            match_start = match['match_start']
            match_end = match['match_end']
            area_lower = area.lower()
            
            # IMPORTANT: Known areas get special protection
            is_known_area = area_lower in self.all_areas or area_lower in self.main_area_names or area_lower in self.common_areas
            
            # Check if this is a known area appearing after building
            is_known_after_building = False
            if is_known_area:
                before_context = address[max(0, match_start-50):match_start].lower()
                has_building_before = any(kw in before_context for kw in self.building_keywords)
                if has_building_before and match_start > 20:
                    is_known_after_building = True
            
            # Apply exclusion checks (but be lenient with known areas)
            if self._is_city_name(area):
                continue
            
            # Known areas are never building names (already checked in _is_building_name)
            if not is_known_area and self._is_building_name(area, address, match_start, match_end):
                continue
            
            # CRITICAL: Block numbers should ALWAYS be excluded, even if they're "known areas"
            # This prevents "Block A", "Block-B", "H block" from being extracted as areas
            if self._is_block_number(area, address, match_start, match_end):
                continue
            
            # Known areas are never house/road/postal/flat/floor numbers
            if not is_known_area:
                if self._is_house_number(area, address, match_start, match_end):
                    continue
                if self._is_road_number(area, address, match_start, match_end):
                    continue
                if self._is_postal_code(area, address, match_start, match_end):
                    continue
                if self._is_flat_number(area, address, match_start, match_end):
                    continue
                if self._is_floor_number(area, address, match_start, match_end):
                    continue
            
            if self._is_division(area, address, match_start, match_end):
                continue
            if self._is_keyword_not_area(area, address, match_start, match_end):
                continue
            if self._is_locality_name(area, address, match_start, match_end):
                continue
            
            validated_matches.append(match)
        
        all_matches = validated_matches
        
        if not all_matches:
            return AreaResult("", 0.0, ExtractionMethod.NOT_FOUND, original_address, "No area candidates found")
        
        # AI-POWERED INTELLIGENT RANKING
        # Use multi-factor scoring instead of simple priority
        def intelligent_score(match):
            """Calculate intelligent score based on multiple factors"""
            area_lower = match['area'].lower()
            base_score = match.get('score', match.get('confidence', 0.5))
            
            # Factor 1: Main area names get massive boost
            if area_lower in self.main_area_names:
                base_score += 0.15
            
            # Factor 2: Known areas get boost
            if match.get('is_known', False):
                base_score += 0.10
            
            # Factor 3: Position analysis (areas typically in middle-to-end)
            position_ratio = match['match_start'] / len(address) if len(address) > 0 else 0
            if 0.3 <= position_ratio <= 0.7:  # Middle section
                base_score += 0.08
            elif position_ratio > 0.7:  # End section
                base_score += 0.05
            
            # Factor 4: Check reasons from intelligent extraction
            reasons = match.get('reasons', [])
            # CRITICAL: Areas appearing immediately before city names get MASSIVE priority
            if 'before_city_immediate' in reasons:
                base_score = max(base_score, 0.95)  # Force to near-maximum if before city
                base_score += 0.30  # Additional massive boost
            if 'after_building' in reasons:
                base_score += 0.12  # Strong indicator
            if 'before_city' in reasons:
                base_score += 0.20  # Very strong indicator (increased)
            if 'after_building_name' in reasons:
                base_score += 0.10
            # CRITICAL: Areas with directional prefixes get high priority
            if 'with_direction' in reasons:
                base_score += 0.25  # Increased boost for directional prefixes
            if 'early_directional_area' in reasons:
                base_score += 0.30  # Extra boost for early directional areas (increased)
            if 'with_number' in reasons:
                base_score += 0.05
            if 'good_position' in reasons:
                base_score += 0.05
            
            # Factor 5: Penalty for start position (unless it's a known area pattern)
            if position_ratio < 0.2 and area_lower not in self.main_area_names:
                base_score -= 0.10
            
            # Factor 6: Method-based adjustments
            if match.get('method') == ExtractionMethod.EXPLICIT_AREA:
                base_score += 0.05
            elif match.get('method') == ExtractionMethod.BANGLA_PATTERN:
                base_score += 0.03
            
            # Factor 7: Check if it appears after comma (good sign)
            if 'after_comma' in reasons:
                base_score += 0.05
            
            # Normalize to 0-1 range
            final_score = max(0.0, min(1.0, base_score))
            
            return final_score
        
        # Score all matches
        for match in all_matches:
            match['intelligent_score'] = intelligent_score(match)
        
        # Sort by intelligent score (highest first)
        all_matches.sort(key=lambda x: x['intelligent_score'], reverse=True)
        
        # Return the best match
        best_match = all_matches[0]
        return AreaResult(
            area=best_match['area'],
            confidence=best_match['intelligent_score'],
            method=best_match.get('method', ExtractionMethod.CONTEXTUAL),
            original=original_address,
            reason=f"Intelligent extraction: {', '.join(best_match.get('reasons', ['pattern_match']))}"
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
    """Extract area from single address"""
    print("=" * 80)
    print("AREA EXTRACTION")
    print("=" * 80)
    print()
    print(f"Address: {address}")
    print()
    
    extractor = AdvancedAreaExtractor()
    result = extractor.extract(address)
    
    print(f"Area:         {result.area or '(not found)'}")
    print(f"Confidence:   {result.confidence:.1%}")
    print(f"Method:       {result.method.value}")
    
    if show_details:
        print(f"Reason:       {result.reason}")
    
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
    
    extractor = AdvancedAreaExtractor()
    
    print("🔄 Processing addresses...")
    processed = 0
    with_area = 0
    
    for record in data:
        address = record.get('address', '')
        result = extractor.extract(address)
        
        if 'components' not in record:
            record['components'] = {}
        
        if result.area and result.confidence >= confidence:
            record['components']['area'] = result.area
            with_area += 1
        else:
            record['components']['area'] = ''
        
        processed += 1
        if processed % 100 == 0:
            print(f"   Processed {processed}/{len(data)} records...")
    
    print()
    print(f"💾 Saving processed dataset to: {output_path}")
    save_json(output_path, data)
    print()
    
    print("=" * 80)
    print("PROCESSING COMPLETE")
    print("=" * 80)
    print()
    print(f"Total Records:     {len(data)}")
    print(f"With Area:         {with_area} ({with_area/len(data)*100:.1f}%)")
    print(f"Without Area:      {len(data)-with_area} ({(len(data)-with_area)/len(data)*100:.1f}%)")
    print()


# ============================================================================
# COMMAND: SPLIT (By Confidence)
# ============================================================================

def cmd_split(input_file: str = None, output_dir: str = None):
    """Split dataset by confidence levels"""
    if input_file is None:
        input_file = 'data/json/real-customer-address-dataset.json'
    if output_dir is None:
        output_dir = 'data/json/processing/area'
    
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
    
    extractor = AdvancedAreaExtractor()
    
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
    split_data['no_area'] = []
    
    print("🔄 Categorizing records...")
    for i, record in enumerate(data, 1):
        if i % 100 == 0:
            print(f"   Processed {i}/{len(data)} records...")
        
        address = record.get('address', '')
        result = extractor.extract(address)
        
        # Create new record with area in components
        new_record = {
            'id': record.get('id'),
            'address': address,
            'components': {
                'area': result.area if result.confidence >= 0.65 and result.area else ''
            }
        }
        
        if result.area and result.confidence >= 0.65:
            # Find appropriate category
            for cat_name, (min_conf, max_conf) in categories.items():
                if min_conf <= result.confidence < max_conf:
                    split_data[cat_name].append(new_record)
                    break
        else:
            split_data['no_area'].append(new_record)
    
    print()
    print("💾 Saving split datasets...")
    
    # Save each category
    for cat_name, records in split_data.items():
        if cat_name == 'no_area':
            cat_path = output_path / cat_name / 'data.json'
        else:
            cat_path = output_path / 'with_area' / cat_name / 'data.json'
        
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
    print("=" * 80)
    print("RE-PROCESSING ALL LEVELS")
    print("=" * 80)
    print()
    
    cmd_split(input_file, output_dir)


# ============================================================================
# COMMAND: UPDATE SUMMARY
# ============================================================================

def cmd_update_summary(base_dir: str = None):
    """Update split summary statistics"""
    if base_dir is None:
        base_dir = 'data/json/processing/area'
    
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
    total_with_area = 0
    
    for cat in categories:
        cat_path = base_path / 'with_area' / cat / 'data.json'
        if cat_path.exists():
            data = load_json(cat_path)
            count = len(data)
            category_counts[cat] = count
            total_with_area += count
            print(f"   ✓ {cat}: {count} records")
        else:
            category_counts[cat] = 0
    
    no_area_path = base_path / 'no_area' / 'data.json'
    if no_area_path.exists():
        no_area_data = load_json(no_area_path)
        no_area_count = len(no_area_data)
        print(f"   ✓ no_area: {no_area_count} records")
    else:
        no_area_count = 0
    
    total_records = total_with_area + no_area_count
    coverage_pct = (total_with_area / total_records * 100) if total_records > 0 else 0
    
    print()
    print("=" * 80)
    print("SUMMARY UPDATED")
    print("=" * 80)
    print()
    print(f"Total Records:         {total_records:,}")
    print(f"With Area:            {total_with_area:,} ({coverage_pct:.1f}%)")
    print(f"Without Area:         {no_area_count:,} ({100-coverage_pct:.1f}%)")
    print()
    print("Confidence Breakdown:")
    for cat in categories:
        count = category_counts.get(cat, 0)
        pct = (count / total_records * 100) if total_records > 0 else 0
        print(f"  {cat:25} {count:>4} records ({pct:>5.1f}%)")
    
    # Create summary in district_division format
    summary = [{
        "statistics": {
            "total_records": total_records,
            "with_area": total_with_area,
            "without_area": no_area_count,
            "coverage_percentage": round(coverage_pct, 1),
            "confidence_breakdown": {
                cat: category_counts.get(cat, 0) for cat in categories
            }
        }
    }]
    
    summary_path = base_path / 'split_summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    
    print()
    print(f"💾 Summary saved to: {summary_path}")
    print()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Area Extraction Processor')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract area from single address')
    extract_parser.add_argument('address', help='Address to extract from')
    extract_parser.add_argument('--details', action='store_true', help='Show detailed information')
    
    # Process command
    process_parser = subparsers.add_parser('process', help='Process entire dataset')
    process_parser.add_argument('--confidence', type=float, default=0.70, help='Confidence threshold')
    process_parser.add_argument('--input', help='Input file path')
    process_parser.add_argument('--output', help='Output file path')
    
    # Split command
    split_parser = subparsers.add_parser('split', help='Split dataset by confidence')
    split_parser.add_argument('--input', help='Input file path')
    split_parser.add_argument('--output', help='Output directory path')
    
    # Reprocess-all command
    reprocess_parser = subparsers.add_parser('reprocess-all', help='Re-process all confidence levels')
    reprocess_parser.add_argument('--input', help='Input file path')
    reprocess_parser.add_argument('--output', help='Output directory path')
    
    # Update-summary command
    summary_parser = subparsers.add_parser('update-summary', help='Update split summary')
    summary_parser.add_argument('--base-dir', help='Base directory path')
    
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

