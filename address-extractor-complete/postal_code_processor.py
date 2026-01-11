#!/usr/bin/env python3
"""
Complete Postal Code Processor - All-in-One Solution
=====================================================

Single comprehensive script for Bangladeshi address postal code extraction,
processing, organization, and management.

Features:
    1. Extract postal codes from addresses (Core Algorithm)
    2. Process entire dataset with confidence filtering
    3. Split dataset by confidence levels
    4. Re-process specific confidence folders
    5. Sync changes between split and main dataset

Usage:
    # Extract from single address
    python3 postal_code_processor.py extract "House-825, Road-4A, Baitul Aman Housing Society, Adabor, Mohammadpur, Dhaka-1207"
    
    # Process entire dataset
    python3 postal_code_processor.py process --confidence 0.70
    
    # Split dataset by confidence
    python3 postal_code_processor.py split
    
    # Re-process specific confidence level
    python3 postal_code_processor.py reprocess 2.very_high_90_95
    
    # Re-process all levels
    python3 postal_code_processor.py reprocess-all
    
    # Update main dataset from split
    python3 postal_code_processor.py sync 2.very_high_90_95

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
    EXPLICIT_POST = "explicit_post"
    EXPLICIT_POSTAL = "explicit_postal"
    EXPLICIT_ZIP = "explicit_zip"
    CITY_DASH = "city_dash"
    BANGLA_CITY_DASH = "bangla_city_dash"
    AREA_POSTAL_CODE = "area_postal_code"
    BANGLA_AREA_POSTAL_CODE = "bangla_area_postal_code"
    POST_OFFICE = "post_office"
    STANDALONE_END = "standalone_end"
    CONTEXTUAL = "contextual"
    BANGLA_NUMERALS = "bangla_numerals"
    NOT_FOUND = "not_found"
    NOT_CONFIDENT = "not_confident"


@dataclass
class PostalCodeResult:
    """Result of postal code extraction"""
    postal_code: str
    confidence: float
    method: ExtractionMethod
    original: str = ""
    reason: str = ""
    
    def __str__(self):
        return f"PostalCode('{self.postal_code}', {self.confidence:.1%}, {self.method.value})"
    
    def to_dict(self) -> Dict:
        return {
            'postal_code': self.postal_code,
            'confidence': self.confidence,
            'method': self.method.value,
            'original': self.original,
            'reason': self.reason
        }


class AdvancedPostalCodeExtractor:
    """Advanced Postal Code Extractor for Bangladeshi Addresses"""
    
    def __init__(self, confidence_threshold: float = 0.65):
        self.confidence_threshold = confidence_threshold
        self._setup_patterns()
        self._setup_exclusions()
        self._setup_bangla_mappings()
        self._load_postal_codes()
    
    def _load_postal_codes(self):
        """Load valid postal codes from dataset"""
        postal_codes_file = Path(__file__).parent.parent.parent / 'division' / 'bd-postal-codes.json'
        self.valid_postal_codes = set()
        
        if postal_codes_file.exists():
            try:
                with open(postal_codes_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'postal_codes' in data:
                        for entry in data['postal_codes']:
                            code = str(entry.get('code', ''))
                            if code and len(code) == 4:
                                self.valid_postal_codes.add(code)
            except Exception as e:
                print(f"Warning: Could not load postal codes: {e}")
                self.valid_postal_codes = set()
        else:
            self.valid_postal_codes = set()
    
    def _setup_patterns(self):
        """Setup extraction patterns - Enhanced with internet research patterns"""
        # EXPLICIT POST PATTERNS (95-100% confidence) - Based on research
        self.explicit_post_patterns = [
            # Post: G.P.O #### pattern - e.g., "Post: G.P.O 6000", "Post: GPO 6000" (specific pattern first)
            (r'(?:Post|POST|পোস্ট)[\s:]+G\.?P\.?O\.?[\s]+([\d০-৯]{4})', 1.00),
            # Post: pattern - e.g., "Post: 1216", "Post: 4000"
            (r'(?:Post|POST|পোস্ট)[\s:]+([\d০-৯]{4})', 1.00),
            # Post Office: pattern - e.g., "Post Office: 1216", "Post Office: G.P.O 6000"
            (r'(?:Post\s+Office|Post\s+office|POST\s+OFFICE|পোস্ট\s+অফিস)[\s:]+(?:G\.?P\.?O\.?[\s]+)?([\d০-৯]{4})', 1.00),
            # P.O: pattern - e.g., "P.O: 1216", "P.O. 1216", "P.O: G.P.O 6000"
            (r'P\.?O\.?[\s:]+(?:G\.?P\.?O\.?[\s]+)?([\d০-৯]{4})', 1.00),
            # Postal Code: pattern - e.g., "Postal Code: 1216"
            (r'(?:Postal\s+Code|Postal\s+code|POSTAL\s+CODE|পোস্টাল\s+কোড)[\s:]+([\d০-৯]{4})', 1.00),
            # Zip: pattern - e.g., "Zip: 1216", "ZIP: 1216"
            (r'(?:Zip|ZIP|zip|জিপ)[\s:]+([\d০-৯]{4})', 0.98),
            # Pin Code: pattern - e.g., "Pin Code: 1216"
            (r'(?:Pin\s+Code|PIN\s+CODE|pin\s+code)[\s:]+([\d০-৯]{4})', 0.98),
        ]
        
        # CITY-DASH PATTERNS (90-100% confidence) - Enhanced with more cities
        # Major cities and common locations
        english_cities = r'(?:Dhaka|Mirpur|Uttara|Gulshan|Banani|Dhanmondi|Chittagong|Chattogram|Sylhet|Rajshahi|Khulna|Barisal|Rangpur|Mymensingh|Comilla|Gazipur|Narayanganj|Savar|Tongi|Narsingdi|Manikganj|Munshiganj|Kishoreganj|Tangail|Jamalpur|Sherpur|Netrokona|Bogura|Joypurhat|Naogaon|Natore|Chapainawabganj|Pabna|Sirajganj|Jessore|Jhenaidah|Magura|Narail|Kushtia|Meherpur|Chuadanga|Bagerhat|Pirojpur|Barguna|Patuakhali|Jhalokathi|Bandarban|Brahmanbaria|Chandpur|Feni|Khagrachhari|Lakshmipur|Noakhali|Rangamati|Cox|Coxs|Bazar)'
        
        bangla_cities = r'(?:ঢাকা|মিরপুর|উত্তরা|গুলশান|বনানী|ধানমন্ডি|চট্টগ্রাম|সিলেট|রাজশাহী|খুলনা|বরিশাল|রংপুর|ময়মনসিংহ|কুমিল্লা|গাজীপুর|নারায়ণগঞ্জ|সাভার|টঙ্গী|নরসিংদী|মানিকগঞ্জ|মুন্সিগঞ্জ|কিশোরগঞ্জ|টাঙ্গাইল|জামালপুর|শেরপুর|নেত্রকোণা|বগুড়া|জয়পুরহাট|নওগাঁ|নাটোর|চাঁপাইনবাবগঞ্জ|পাবনা|সিরাজগঞ্জ|যশোর|ঝিনাইদহ|মাগুরা|নড়াইল|কুষ্টিয়া|মেহেরপুর|চুয়াডাঙ্গা|বাগেরহাট|পিরোজপুর|বরগুনা|পটুয়াখালী|ঝালকাঠি|বান্দরবান|ব্রাহ্মণবাড়িয়া|চাঁদপুর|ফেনী|খাগড়াছড়ি|লক্ষ্মীপুর|নোয়াখালী|রাঙ্গামাটি|কক্স|কক্সবাজার)'
        
        # Common area names in Dhaka and other cities
        english_areas = r'(?:Shyamoli|Shamoli|Shymoli|Mohammadpur|Dhanmondi|Gulshan|Banani|Uttara|Mirpur|Rampura|Khilgaon|Motijheel|Farmgate|Tejgaon|Lalbagh|Wari|Shantinagar|Malibagh|Moghbazar|Shahbagh|Panthapath|Green\s+Road|Elephant\s+Road|Nilkhet|Azimpur|Bashabo|Sabujbag|Jatrabari|Demra|Shyampur|Hazaribagh|Cantonment|Kafrul|Pallabi|Badda|Khilkhet|Baridhara|Nikunja|Bashundhara|Adabor|Agargaon|Airport|Bangshal|Begunbari|Bijoy\s+Sarani|Dilkusha|Fakirapool|Fulbaria|Gandaria|Gopibagh|Goran|Hatirjheel|Indira\s+Road|Jigatola|Kakrail|Kamalapur|Kamlapur|Katabon|Kathalbagan|Kuril|Lalmatia|Magbazar|Manik\s+Mia\s+Avenue|Mohakhali|Mouchak|Nakhalpara|New\s+Market|Paltan|Ramna|Russell\s+Square|Sadarghat|Siddheswari|Sutrapur|Tejgaon\s+Industrial\s+Area|Tongi|Turagh|Wasa|Narinda|Vashantek|Shahjadpur|Kataban|Shewrapara|Kochukhet|Kalabagan|Lake\s+Circus|Bottola|Hathirpool|Matuail|Tilpapara|Dakshinkhan|Balughat|Jheelpar|Ibrahimpur|Banasree|Diyabari|Tolarbag|Zigatola|Shahalibag|Kazipara|Bonosri|Kalshi|Ring\s+Road|Nakhalpara|Jhulonbari|Tantibazar|Kunjbon|Aftabnagar|Sector\s+\d+|Sec\s*[-:]?\s*\d+)'
        
        bangla_areas = r'(?:শ্যামলী|শামলী|মোহাম্মদপুর|ধানমন্ডি|গুলশান|বনানী|উত্তরা|মিরপুর|রামপুরা|খিলগাঁও|মতিঝিল|তেজগাঁও|লালবাগ|ওয়ারী|শান্তিনগর|মালিবাগ|মগবাজার|শাহবাগ|পান্থপথ|নীলক্ষেত|আজিমপুর|বাসাবো|সাবুজবাগ|যাত্রাবাড়ী|হাজারীবাগ|ক্যান্টনমেন্ট|বাড্ডা|খিলক্ষেত|বারিধারা|বসুন্ধরা|আদাবর|মোহাখালী|পুরানা\s+পল্টন|তোপখানা)'
        
        # Combined lookahead pattern for end of postal code (handles both English and Bengali punctuation)
        # Includes: comma, Bengali full stop (।), period, parenthesis, end of string, whitespace
        end_pattern = r'(?=\s*[,।]|\s|$|\)|\.)'
        
        self.city_dash_patterns = [
            # City-#### pattern with word boundary - e.g., "Dhaka-1216", "Mirpur-1216", "Dhaka-1000"
            (rf'\b{english_cities}[\s-]+\s*([\d০-৯]{{4}}){end_pattern}', 0.98),
            # City #### pattern (space, no dash) with word boundary - e.g., "Dhaka 1209", "Dhaka 1211"
            (rf'\b{english_cities}[\s]+([\d০-৯]{{4}}){end_pattern}', 0.98),
            # Bangla city names with dash (handles both "ঢাকা- ১২১৬" and "ঢাকা-১০০০") - e.g., "ঢাকা-১২১৬", "ঢাকা- ১২১৬", "ঢাকা-১০০০"
            (rf'{bangla_cities}[\s]*[-][\s]*([\d০-৯]{{4}}){end_pattern}', 0.98),
            # Bangla city names with space (no dash) - e.g., "ঢাকা ১২১৬"
            (rf'{bangla_cities}[\s]+([\d০-৯]{{4}}){end_pattern}', 0.98),
            # Generic city name pattern (3+ letters) - e.g., "Savar-1340"
            (rf'\b([A-Z][a-z]{{2,}})[\s-]+\s*([\d০-৯]{{4}}){end_pattern}', 0.90),
        ]
        
        # AREA-POSTAL CODE PATTERNS (85-95% confidence) - Area names followed by postal codes
        self.area_postal_patterns = [
            # English area name followed by postal code - e.g., "Shyamoli 1207", "Mohammadpur 1207"
            (rf'\b{english_areas}[\s]+([\d০-৯]{{4}}){end_pattern}', 0.95),
            # English area name with dash followed by postal code - e.g., "Shyamoli-1207"
            (rf'\b{english_areas}[\s]*[-][\s]*([\d০-৯]{{4}}){end_pattern}', 0.95),
            # Bangla area name followed by postal code - e.g., "শ্যামলী ১২১৬"
            (rf'{bangla_areas}[\s]+([\d০-৯]{{4}}){end_pattern}', 0.95),
            # Bangla area name with dash followed by postal code - e.g., "শ্যামলী- ১২১৬"
            (rf'{bangla_areas}[\s]*[-][\s]*([\d০-৯]{{4}}){end_pattern}', 0.95),
            # Generic area name pattern (capitalized word, 3+ letters) followed by postal code - e.g., "Shyamoli 1207"
            (rf'\b([A-Z][a-z]{{3,}})[\s]+([\d০-৯]{{4}}){end_pattern}', 0.85),
        ]
        
        # STANDALONE PATTERNS (70-95% confidence) - Enhanced with word boundaries
        self.standalone_patterns = [
            # 4-digit number at end of address with word boundary - e.g., "..., Dhaka 1216"
            (r'\b([\d০-৯]{4})\b(?=\s*$)', 0.85),
            # 4-digit number after comma and location - e.g., ", Dhaka, 1216"
            (r',[\s]+\b([\d০-৯]{4})\b(?=\s*[,]|\s|$|\)|\.)', 0.80),
            # 4-digit number with space before location keywords
            (r'\b([\d০-৯]{4})\b(?=\s+(?:Dhaka|Mirpur|Uttara|Gulshan|Banani|Dhanmondi|Chittagong|Chattogram|Sylhet|Rajshahi|Khulna|Barisal|Rangpur|Mymensingh|Comilla|Gazipur|Narayanganj|Bangladesh|বাংলাদেশ))', 0.75),
            # Standalone 4-digit number with word boundaries (research pattern: \b\d{4}\b)
            (r'\b([\d০-৯]{4})\b', 0.70),
        ]
        
        # BANGLA NUMERAL PATTERNS (90-100% confidence) - Enhanced
        self.bangla_patterns = [
            # Bangla numerals with word boundary - e.g., "১২১৬", "১০০০" (research pattern: [০-৯]{৪})
            (r'\b([০-৯]{4})\b', 0.90),
            # Bangla numerals in context - e.g., "..., ১২১৬"
            (r'([০-৯]{4})(?=\s*[,]|\s|$|\)|\.)', 0.85),
        ]
    
    def _setup_exclusions(self):
        """Setup exclusion patterns"""
        # Common city names in Bangladesh
        self.city_names = [
            'dhaka', 'chittagong', 'chattogram', 'sylhet', 'rajshahi', 'khulna', 
            'barisal', 'rangpur', 'mymensingh', 'comilla', 'cox', 'mirpur', 
            'uttara', 'gulshan', 'banani', 'dhanmondi', 'gazipur', 'narayanganj',
            'savar', 'tongi', 'narsingdi', 'manikganj', 'munshiganj', 'kishoreganj',
            'tangail', 'jamalpur', 'sherpur', 'netrokona', 'bogura', 'joypurhat',
            'naogaon', 'natore', 'chapainawabganj', 'pabna', 'sirajganj', 'jessore',
            'jhenaidah', 'magura', 'narail', 'kushtia', 'meherpur', 'chuadanga',
            'bagerhat', 'pirojpur', 'barguna', 'patuakhali', 'barisal', 'jhalokathi',
            'bandarban', 'brahmanbaria', 'chandpur', 'chittagong', 'comilla', 'cox',
            'feni', 'khagrachhari', 'lakshmipur', 'noakhali', 'rangamati'
        ]
        
        # Invalid patterns (not postal codes)
        self.invalid_patterns = [
            r'^\d{1,3}$',  # Too few digits (likely house/road number)
            r'^\d{5,}$',   # Too many digits (likely phone number or ID)
            r'^0{4}$',     # All zeros
            # Note: Removed r'^[1-9]0{3}$' because 1000 is a valid postal code (Dhaka GPO)
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
    
    def _validate_postal_code(self, code: str) -> bool:
        """Validate extracted postal code"""
        if not code:
            return False
        
        # Convert Bangla numerals to English
        code = self._bangla_to_english_number(code.strip())
        
        # Must be exactly 4 digits
        if not re.match(r'^\d{4}$', code):
            return False
        
        # Check against invalid patterns
        for pattern in self.invalid_patterns:
            if re.match(pattern, code):
                return False
        
        # Check if it's a valid postal code (if we have the dataset)
        if self.valid_postal_codes:
            if code not in self.valid_postal_codes:
                # Still allow it but with lower confidence (might be valid but not in dataset)
                pass
        
        # Must be between 1000 and 9999 (valid range for Bangladesh)
        try:
            code_int = int(code)
            if code_int < 1000 or code_int > 9999:
                return False
        except ValueError:
            return False
        
        return True
    
    def _is_area_name_before(self, before_context: str) -> bool:
        """Check if there's an area name immediately before the match"""
        # Common area names that indicate postal code context
        area_names = [
            'shyamoli', 'shamoli', 'shymoli', 'mohammadpur', 'dhanmondi', 'gulshan', 
            'banani', 'uttara', 'mirpur', 'rampura', 'khilgaon', 'motijheel', 
            'farmgate', 'tejgaon', 'lalbagh', 'wari', 'shantinagar', 'malibagh',
            'moghbazar', 'shahbagh', 'panthapath', 'nilkhet', 'azimpur', 'bashabo',
            'jatrabari', 'badda', 'baridhara', 'bashundhara', 'adabor', 'agargaon'
        ]
        # Check last 20 characters for area names
        for area in area_names:
            if area in before_context[-20:]:
                # Check if area name is immediately before (within 1-2 words)
                area_pos = before_context.rfind(area)
                if area_pos != -1:
                    text_after_area = before_context[area_pos + len(area):].strip()
                    # If area name is immediately before (just space), it's likely a postal code
                    if len(text_after_area) <= 3:  # Allow for small separators
                        return True
        return False
    
    def _is_house_number(self, postal_code: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted number is actually a house number"""
        # Check context before and after the match
        before_context = address[max(0, match_start-50):match_start]
        before_context_lower = before_context.lower()
        after_context = address[match_end:match_end+50].lower()
        full_context = before_context_lower + after_context
        
        # FIRST: Check if there's an explicit postal code keyword - if so, it's definitely a postal code
        postal_code_keywords = ['post:', 'post office:', 'p.o:', 'p.o.', 'postal code:', 'zip:', 'pin code:', 'g.p.o', 'gpo']
        for pc_kw in postal_code_keywords:
            if pc_kw in before_context_lower[-30:]:  # Last 30 chars before match
                return False  # It's a postal code, not a house number
        
        # SECOND: Check if there's a Bengali city name immediately before (like ঢাকা- or ঢাকা )
        bangla_cities_in_context = ['ঢাকা', 'মিরপুর', 'উত্তরা', 'গুলশান', 'ধানমন্ডি']
        for city in bangla_cities_in_context:
            if city in before_context[-20:]:  # Last 20 chars before match (keep original case for Bengali)
                city_pos = before_context.rfind(city)
                if city_pos != -1:
                    text_after_city = before_context[city_pos + len(city):]
                    # If city name is immediately before with dash or space, it's postal code
                    if len(text_after_city.strip()) <= 3:  # Allow for dash, space, and small separators
                        return False  # It's a postal code, not a house number
        
        # THIRD: Check if there's an area name immediately before - if so, it's likely a postal code
        if self._is_area_name_before(before_context_lower):
            return False  # It's a postal code, not a house number
        
        # If number appears at the very start of address (first 20 chars), it's likely a house number
        if match_start < 20:
            # Check if it's followed by house/road/block keywords
            if any(kw in after_context[:30] for kw in ['road', 'rd', 'block', 'floor', 'level', 'lane', 'goli', 'para', 'area', 'chowdhury', 'model', 'town']):
                return True  # It's a house number
            # Check if it has a slash pattern (house number format like "1359/A" or "1421/1/A")
            if '/' in after_context[:10]:
                return True  # It's a house number
        
        # If there's an English city name right before, it's definitely a postal code, not a house number
        city_names = ['dhaka', 'mirpur', 'uttara', 'gulshan', 'banani', 'dhanmondi', 'chittagong', 'chattogram', 
                     'sylhet', 'rajshahi', 'khulna', 'barisal', 'rangpur', 'mymensingh', 'comilla', 'gazipur', 'narayanganj']
        for city in city_names:
            if city in before_context_lower[-15:]:  # Last 15 chars before match
                # Check if there's a road/house keyword between city and postal code
                city_pos = before_context_lower.rfind(city)
                if city_pos != -1:
                    text_after_city = before_context_lower[city_pos + len(city):]
                    # If there's a road/house keyword, it might be a house number
                    if any(kw in text_after_city for kw in ['road', 'rd', 'lane', 'house', 'building']):
                        continue  # Might be house number, check further
                    # If city name is immediately before (with space or dash), it's postal code
                    if len(text_after_city.strip()) <= 2:  # Just space/dash
                        return False  # It's a postal code
        
        # House number keywords - expanded list
        house_keywords = [
            'house', 'home', 'hous', 'building', 'bldg', 'plot', 'holding',
            'flat', 'apt', 'apartment', 'unit', 'room', 'floor', 'level',
            'gate', 'lift', 'shop', 'store', 'office', 'no.', 'number',
            'block', 'para', 'area', 'chowdhury', 'model', 'town', 'road',
            'rd', 'lane', 'goli', 'street', 'avenue'
        ]
        
        # Check if number is followed by house-related keywords
        if any(kw in after_context[:30] for kw in ['road', 'rd', 'block', 'floor', 'level', 'lane', 'goli', 'para', 'area', 'chowdhury', 'model', 'town', 'street', 'avenue', 'no.', 'number']):
            # But exclude if there's a city name between number and keyword
            if not any(city in after_context[:30] for city in city_names):
                return True  # It's a house number
        
        # Check if number is followed by directional/location keywords (e.g., "1201 East Monipur")
        directional_keywords = ['east', 'west', 'north', 'south', 'central', 'purbo', 'paschim', 'uttor', 'dakshin']
        if any(kw in after_context[:20] for kw in directional_keywords):
            # If followed by a location name (not a city), it's likely a house/block number
            location_indicators = ['monipur', 'kazipara', 'hazipara', 'badda', 'rampura', 'khilgaon', 'dhanmondi', 'gulshan', 'banani']
            if any(loc in after_context[:40] for loc in location_indicators):
                return True  # It's a house/block number
        
        # Check if number is preceded by house-related keywords
        if any(kw in before_context[-30:] for kw in ['no.', 'number', 'house', 'building', 'plot', 'holding']):
            # But exclude if there's a city name or postal code keyword
            if not any(city in before_context[-30:] for city in city_names):
                if not any(pc_kw in before_context[-30:] for pc_kw in ['post', 'postal', 'zip', 'p.o']):
                    return True  # It's a house number
        
        # If house keywords appear before, it's likely a house number
        for keyword in house_keywords:
            if keyword in before_context:
                # But check if there's a postal code keyword or city name between house and number
                keyword_pos = before_context.rfind(keyword)
                if keyword_pos != -1:
                    text_between = before_context[keyword_pos:]
                    if any(pc_kw in text_between for pc_kw in ['post', 'postal', 'zip', 'p.o']):
                        return False  # It's a postal code
                    # Check if there's a city name between house keyword and postal code
                    if any(city in text_between for city in city_names):
                        return False  # It's a postal code
                    return True  # It's a house number
        
        return False
    
    def _is_road_number(self, postal_code: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted number is actually a road number"""
        # Check context before the match
        before_context = address[max(0, match_start-30):match_start]
        before_context_lower = before_context.lower()
        
        # FIRST: Check if there's a Bengali city name immediately before (like ঢাকা- or ঢাকা )
        bangla_cities_in_context = ['ঢাকা', 'মিরপুর', 'উত্তরা', 'গুলশান', 'ধানমন্ডি']
        for city in bangla_cities_in_context:
            if city in before_context[-20:]:  # Last 20 chars before match (keep original case for Bengali)
                city_pos = before_context.rfind(city)
                if city_pos != -1:
                    text_after_city = before_context[city_pos + len(city):]
                    # If city name is immediately before with dash or space, it's postal code
                    if len(text_after_city.strip()) <= 3:  # Allow for dash, space, and small separators
                        return False  # It's a postal code, not a road number
        
        # If there's an English city name right before, it's definitely a postal code, not a road number
        city_names = ['dhaka', 'mirpur', 'uttara', 'gulshan', 'banani', 'dhanmondi', 'chittagong', 'chattogram', 
                     'sylhet', 'rajshahi', 'khulna', 'barisal', 'rangpur', 'mymensingh', 'comilla', 'gazipur', 'narayanganj']
        for city in city_names:
            if city in before_context_lower[-15:]:  # Last 15 chars before match
                # Check if there's a road keyword between city and postal code
                city_pos = before_context_lower.rfind(city)
                if city_pos != -1:
                    text_after_city = before_context_lower[city_pos + len(city):]
                    # If city name is immediately before (with space or dash), it's postal code
                    if len(text_after_city.strip()) <= 2:  # Just space/dash
                        return False  # It's a postal code
        
        # If there's an area name immediately before, it's likely a postal code, not a road number
        if self._is_area_name_before(before_context_lower):
            return False  # It's a postal code, not a road number
        
        # Road number keywords
        road_keywords = [
            'road', 'rd', 'lane', 'line', 'avenue', 'street', 'goli',
            'রোড', 'লেন', 'r ', 'r-', 'r#', 'r:'
        ]
        
        # If road keywords appear before, it's likely a road number
        for keyword in road_keywords:
            if keyword in before_context:
                # But check if there's a postal code keyword or city name between road and number
                keyword_pos = before_context.rfind(keyword)
                if keyword_pos != -1:
                    text_between = before_context[keyword_pos:]
                    if any(pc_kw in text_between for pc_kw in ['post', 'postal', 'zip', 'p.o']):
                        return False  # It's a postal code
                    # Check if there's a city name between road keyword and postal code
                    if any(city in text_between for city in city_names):
                        return False  # It's a postal code
                    return True  # It's a road number
        
        return False
    
    def _is_phone_number(self, postal_code: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted number is actually a phone number"""
        # Phone numbers in Bangladesh are typically 11 digits (01XXXXXXXXX)
        # But we're only matching 4 digits, so check context
        
        # Check if there are more digits nearby (phone numbers often have multiple groups)
        after_context = address[match_end:match_end+20].lower()
        before_context = address[max(0, match_start-20):match_start].lower()
        
        # Phone number keywords
        phone_keywords = ['phone', 'mobile', 'cell', 'tel', 'contact', 'call']
        
        for keyword in phone_keywords:
            if keyword in before_context or keyword in after_context:
                return True
        
        # Check if there are more digits nearby (likely phone number)
        if re.search(r'\d{5,}', before_context + after_context):
            return True
        
        return False
    
    def extract(self, address: str) -> PostalCodeResult:
        """Extract postal code from address"""
        if not address:
            return PostalCodeResult(
                postal_code="",
                confidence=0.0,
                method=ExtractionMethod.NOT_FOUND,
                original=address,
                reason="Empty address"
            )
        
        original_address = address
        all_matches = []
        
        # Try explicit post patterns first (highest confidence)
        for pattern, confidence in self.explicit_post_patterns:
            match = re.search(pattern, address, re.IGNORECASE)
            if match:
                postal_code = match.group(1)
                postal_code = self._bangla_to_english_number(postal_code)
                
                if self._validate_postal_code(postal_code):
                    match_start = match.start()
                    match_end = match.end()
                    
                    # Check exclusions
                    if not self._is_house_number(postal_code, address, match_start, match_end) and \
                       not self._is_road_number(postal_code, address, match_start, match_end) and \
                       not self._is_phone_number(postal_code, address, match_start, match_end):
                        
                        all_matches.append({
                            'postal_code': postal_code,
                            'confidence': confidence,
                            'method': ExtractionMethod.EXPLICIT_POST if 'Post' in pattern or 'P.O' in pattern else ExtractionMethod.EXPLICIT_POSTAL,
                            'match_start': match_start,
                            'match_end': match_end,
                            'pattern': pattern
                        })
        
        # Try city-dash patterns
        for pattern_idx, (pattern, confidence) in enumerate(self.city_dash_patterns):
            # Don't use IGNORECASE for Bangla patterns (indices 2 and 3 are Bengali patterns)
            # Pattern index 2: Bangla city with dash, index 3: Bangla city with space
            is_bangla_pattern = pattern_idx >= 2 and pattern_idx <= 3
            flags = 0 if is_bangla_pattern else re.IGNORECASE
            match = re.search(pattern, address, flags)
            if match:
                # Handle both group(1) and group(2) cases
                if match.lastindex >= 2:
                    postal_code = match.group(2)  # Generic city pattern has 2 groups
                else:
                    postal_code = match.group(1)  # Specific city patterns have 1 group
                postal_code = self._bangla_to_english_number(postal_code)
                
                if self._validate_postal_code(postal_code):
                    match_start = match.start()
                    match_end = match.end()
                    
                    # Check exclusions
                    is_house = self._is_house_number(postal_code, address, match_start, match_end)
                    is_road = self._is_road_number(postal_code, address, match_start, match_end)
                    is_phone = self._is_phone_number(postal_code, address, match_start, match_end)
                    
                    if not is_house and not is_road and not is_phone:
                        # Determine method based on pattern type
                        if is_bangla_pattern:
                            method = ExtractionMethod.BANGLA_CITY_DASH
                        elif pattern_idx == 1:  # City with space (no dash)
                            method = ExtractionMethod.CITY_DASH
                        else:
                            method = ExtractionMethod.CITY_DASH
                        all_matches.append({
                            'postal_code': postal_code,
                            'confidence': confidence,
                            'method': method,
                            'match_start': match_start,
                            'match_end': match_end,
                            'pattern': pattern
                        })
        
        # Try area-postal code patterns
        for pattern_idx, (pattern, confidence) in enumerate(self.area_postal_patterns):
            # Don't use IGNORECASE for Bangla patterns (indices 2 and 3)
            flags = 0 if pattern_idx >= 2 and ('শ্যামলী' in pattern or 'পুরানা' in pattern) else re.IGNORECASE
            match = re.search(pattern, address, flags)
            if match:
                # Handle both group(1) and group(2) cases
                if match.lastindex >= 2:
                    postal_code = match.group(2)  # Generic area pattern has 2 groups
                else:
                    postal_code = match.group(1)  # Specific area patterns have 1 group
                postal_code = self._bangla_to_english_number(postal_code)
                
                if self._validate_postal_code(postal_code):
                    match_start = match.start()
                    match_end = match.end()
                    
                    # Check exclusions
                    is_house = self._is_house_number(postal_code, address, match_start, match_end)
                    is_road = self._is_road_number(postal_code, address, match_start, match_end)
                    is_phone = self._is_phone_number(postal_code, address, match_start, match_end)
                    
                    if not is_house and not is_road and not is_phone:
                        # Determine method based on pattern type
                        if pattern_idx >= 2:  # Bangla area patterns
                            method = ExtractionMethod.BANGLA_AREA_POSTAL_CODE
                        else:  # English area patterns
                            method = ExtractionMethod.AREA_POSTAL_CODE
                        all_matches.append({
                            'postal_code': postal_code,
                            'confidence': confidence,
                            'method': method,
                            'match_start': match_start,
                            'match_end': match_end,
                            'pattern': pattern
                        })
        
        # Try standalone patterns (lower confidence)
        for pattern, confidence in self.standalone_patterns:
            match = re.search(pattern, address, re.IGNORECASE)
            if match:
                postal_code = match.group(1)
                postal_code = self._bangla_to_english_number(postal_code)
                
                if self._validate_postal_code(postal_code):
                    match_start = match.start()
                    match_end = match.end()
                    
                    # Check exclusions
                    if not self._is_house_number(postal_code, address, match_start, match_end) and \
                       not self._is_road_number(postal_code, address, match_start, match_end) and \
                       not self._is_phone_number(postal_code, address, match_start, match_end):
                        
                        all_matches.append({
                            'postal_code': postal_code,
                            'confidence': confidence,
                            'method': ExtractionMethod.STANDALONE_END,
                            'match_start': match_start,
                            'match_end': match_end,
                            'pattern': pattern
                        })
        
        # Try Bangla numeral patterns
        for pattern, confidence in self.bangla_patterns:
            match = re.search(pattern, address)
            if match:
                postal_code = match.group(1)
                postal_code = self._bangla_to_english_number(postal_code)
                
                if self._validate_postal_code(postal_code):
                    match_start = match.start()
                    match_end = match.end()
                    
                    # Check exclusions
                    if not self._is_house_number(postal_code, address, match_start, match_end) and \
                       not self._is_road_number(postal_code, address, match_start, match_end) and \
                       not self._is_phone_number(postal_code, address, match_start, match_end):
                        
                        all_matches.append({
                            'postal_code': postal_code,
                            'confidence': confidence,
                            'method': ExtractionMethod.BANGLA_NUMERALS,
                            'match_start': match_start,
                            'match_end': match_end,
                            'pattern': pattern
                        })
        
        if not all_matches:
            return PostalCodeResult(
                postal_code="",
                confidence=0.0,
                method=ExtractionMethod.NOT_FOUND,
                original=original_address,
                reason="No pattern matched"
            )
        
        # Prioritize matches: prefer explicit patterns
        def get_priority(match):
            priority = 0
            
            # Explicit patterns get highest priority
            if match['method'] == ExtractionMethod.EXPLICIT_POST or \
               match['method'] == ExtractionMethod.EXPLICIT_POSTAL or \
               match['method'] == ExtractionMethod.EXPLICIT_ZIP:
                priority += 10000
            elif match['method'] == ExtractionMethod.CITY_DASH or \
                 match['method'] == ExtractionMethod.BANGLA_CITY_DASH:
                priority += 5000
            elif match['method'] == ExtractionMethod.AREA_POSTAL_CODE or \
                 match['method'] == ExtractionMethod.BANGLA_AREA_POSTAL_CODE:
                priority += 4500  # Slightly lower than city-dash but higher than standalone
            elif match['method'] == ExtractionMethod.STANDALONE_END:
                priority += 1000
            
            # Add confidence as secondary priority
            priority += match['confidence'] * 100
            
            # Add position bonus (later in address is better for postal codes)
            position_bonus = (match['match_start'] / len(address)) * 100
            priority += position_bonus
            
            return priority
        
        # Sort by priority (highest first)
        all_matches.sort(key=get_priority, reverse=True)
        
        # Return the best match
        best_match = all_matches[0]
        return PostalCodeResult(
            postal_code=best_match['postal_code'],
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
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading {filepath}: {e}")
        return []


def save_json(filepath: Path, data: List[Dict]):
    """Save JSON file"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============================================================================
# COMMAND: EXTRACT (Single Address)
# ============================================================================

def cmd_extract(address: str, details: bool = False):
    """Extract postal code from single address"""
    extractor = AdvancedPostalCodeExtractor()
    result = extractor.extract(address)
    
    print("=" * 80)
    print("POSTAL CODE EXTRACTION")
    print("=" * 80)
    print()
    print(f"Address:  {address}")
    print()
    print(f"Postal Code:  {result.postal_code if result.postal_code else '(not found)'}")
    print(f"Confidence:   {result.confidence:.1%}")
    print(f"Method:       {result.method.value}")
    
    if details:
        print(f"Reason:        {result.reason}")
    
    print()


# ============================================================================
# COMMAND: PROCESS (Entire Dataset)
# ============================================================================

def cmd_process(confidence: float = 0.70, input_file: str = None, output_file: str = None):
    """Process entire dataset"""
    if input_file is None:
        input_file = 'data/json/real-customer-address-dataset.json'
    if output_file is None:
        output_file = input_file
    
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    print("=" * 80)
    print("PROCESSING DATASET")
    print("=" * 80)
    print()
    
    print(f"📂 Loading dataset...")
    data = load_json(input_path)
    print(f"   ✓ Loaded {len(data)} records")
    print()
    
    extractor = AdvancedPostalCodeExtractor(confidence_threshold=confidence)
    
    print("🔄 Extracting postal codes...")
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
            record['components']['postal_code'] = result.postal_code
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
            record['components']['postal_code'] = ""
    
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
        output_dir = 'data/json/processing/postal_code'
    
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
    
    extractor = AdvancedPostalCodeExtractor()
    
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
    split_data['no_postal_code'] = []
    
    print("🔄 Categorizing records...")
    for i, record in enumerate(data, 1):
        if i % 100 == 0:
            print(f"   Processed {i}/{len(data)} records...")
        
        address = record.get('address', '')
        result = extractor.extract(address)
        
        if result.postal_code and result.confidence >= 0.65:
            # Find appropriate category
            for cat_name, (min_conf, max_conf) in categories.items():
                if min_conf <= result.confidence < max_conf:
                    # Keep only postal_code in components
                    new_record = {
                        'id': record.get('id', i),
                        'address': record.get('address', ''),
                        'components': {
                            'postal_code': result.postal_code
                        }
                    }
                    split_data[cat_name].append(new_record)
                    break
        else:
            # Keep only postal_code in components (empty)
            new_record = {
                'id': record.get('id', i),
                'address': record.get('address', ''),
                'components': {
                    'postal_code': ""
                }
            }
            split_data['no_postal_code'].append(new_record)
    
    print()
    print("💾 Saving split datasets...")
    
    # Save each category
    for cat_name, records in split_data.items():
        if cat_name == 'no_postal_code':
            cat_path = output_path / cat_name / 'data.json'
        else:
            cat_path = output_path / 'with_postal_code' / cat_name / 'data.json'
        
        save_json(cat_path, records)
        print(f"   ✓ {cat_name}: {len(records)} records")
    
    # Generate summary
    total_records = len(data)
    with_postal_code = sum(len(records) for cat_name, records in split_data.items() if cat_name != 'no_postal_code')
    without_postal_code = len(split_data['no_postal_code'])
    
    summary = {
        "statistics": {
            "total_records": total_records,
            "with_postal_code": with_postal_code,
            "without_postal_code": without_postal_code,
            "coverage_percentage": round((with_postal_code / total_records * 100) if total_records > 0 else 0, 2),
            "confidence_breakdown": {
                cat_name: len(records) for cat_name, records in split_data.items() if cat_name != 'no_postal_code'
            }
        }
    }
    
    summary_path = output_path / 'split_summary.json'
    save_json(summary_path, [summary])  # Save as list for consistency
    print()
    print(f"   ✓ Summary saved to: {summary_path}")
    print()
    print("=" * 80)
    print("SPLIT COMPLETE")
    print("=" * 80)
    print()
    print(f"Total Records:         {total_records}")
    print(f"With Postal Code:      {with_postal_code} ({with_postal_code/total_records*100:.1f}%)")
    print(f"Without Postal Code:   {without_postal_code}")
    print()


# ============================================================================
# COMMAND: REPROCESS (Specific Confidence Level)
# ============================================================================

def cmd_reprocess(confidence_level: str, base_dir: str = None):
    """Re-process specific confidence level"""
    if base_dir is None:
        base_dir = 'data/json/processing/postal_code'
    
    data_path = Path(base_dir) / 'with_postal_code' / confidence_level / 'data.json'
    
    if not data_path.exists():
        print(f"❌ Error: {data_path} not found")
        return
    
    # Confidence thresholds
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
    
    extractor = AdvancedPostalCodeExtractor(confidence_threshold=threshold)
    
    print("🔄 Re-processing...")
    updated = 0
    
    for i, record in enumerate(data, 1):
        address = record.get('address', '')
        old_postal_code = record['components'].get('postal_code', '')
        
        result = extractor.extract(address)
        
        if result.confidence >= threshold and result.postal_code != old_postal_code:
            record['components']['postal_code'] = result.postal_code
            updated += 1
            if updated <= 10:
                print(f"   ✓ {old_postal_code} → {result.postal_code}")
    
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
        base_dir = 'data/json/processing/postal_code'
    
    input_file = 'data/json/real-customer-address-dataset.json'
    
    print("=" * 80)
    print("RE-PROCESSING ALL LEVELS")
    print("=" * 80)
    print()
    
    # Just run split again to reprocess everything
    cmd_split(input_file, base_dir)


# ============================================================================
# COMMAND: SYNC (Update Main Dataset from Split)
# ============================================================================

def cmd_sync(confidence_level: str, main_file: str = None, split_dir: str = None):
    """Sync main dataset from split data"""
    if main_file is None:
        main_file = 'data/json/real-customer-address-dataset.json'
    if split_dir is None:
        split_dir = 'data/json/processing/postal_code'
    
    main_path = Path(main_file)
    split_path = Path(split_dir) / 'with_postal_code' / confidence_level / 'data.json'
    
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
        postal_code = record['components'].get('postal_code', '')
        if postal_code:
            split_map[address] = postal_code
    
    print("🔄 Syncing...")
    updated = 0
    
    for record in main_data:
        address = record.get('address', '')
        if address in split_map:
            if 'components' not in record:
                record['components'] = {}
            old_postal_code = record['components'].get('postal_code', '')
            new_postal_code = split_map[address]
            if old_postal_code != new_postal_code:
                record['components']['postal_code'] = new_postal_code
                updated += 1
                if updated <= 10:
                    print(f"   ✓ {old_postal_code} → {new_postal_code}")
    
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
        description='Complete Postal Code Processor - All-in-One Solution',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Extract from single address:
    python3 postal_code_processor.py extract "House-825, Road-4A, Baitul Aman Housing Society, Adabor, Mohammadpur, Dhaka-1207"
  
  Process entire dataset:
    python3 postal_code_processor.py process --confidence 0.70
  
  Split dataset by confidence:
    python3 postal_code_processor.py split
  
  Re-process specific level:
    python3 postal_code_processor.py reprocess 2.very_high_90_95
  
  Re-process all levels:
    python3 postal_code_processor.py reprocess-all
  
  Sync main dataset:
    python3 postal_code_processor.py sync 2.very_high_90_95
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract postal code from address')
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
    
    # Reprocess all command
    reprocess_all_parser = subparsers.add_parser('reprocess-all', help='Re-process all confidence levels')
    reprocess_all_parser.add_argument('--base-dir', help='Base split directory')
    
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
    elif args.command == 'reprocess-all':
        cmd_reprocess_all(args.base_dir)
    elif args.command == 'sync':
        cmd_sync(args.level, args.main_file, args.split_dir)


if __name__ == "__main__":
    main()

