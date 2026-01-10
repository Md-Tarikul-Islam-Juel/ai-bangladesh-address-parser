#!/usr/bin/env python3
"""
Complete City Processor - All-in-One Solution
=============================================

Single comprehensive script for Bangladeshi address city extraction,
processing, organization, and management.

Features:
    1. Extract city names from addresses (Core Algorithm)
    2. Process entire dataset with confidence filtering
    3. Split dataset by confidence levels
    4. Re-process specific confidence folders
    5. Sync changes between split and main dataset

Usage:
    # Extract from single address
    python3 city_processor.py extract "House-825, Road-4A, Baitul Aman Housing Society, Adabor, Mohammadpur, Dhaka-1207"
    
    # Process entire dataset
    python3 city_processor.py process --confidence 0.70
    
    # Split dataset by confidence
    python3 city_processor.py split
    
    # Re-process specific confidence level
    python3 city_processor.py reprocess 2.very_high_90_95
    
    # Re-process all levels
    python3 city_processor.py reprocess-all
    
    # Update main dataset from split
    python3 city_processor.py sync 2.very_high_90_95
    
    # Update summary
    python3 city_processor.py update-summary

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
    EXPLICIT_CITY = "explicit_city"
    CITY_DASH_POSTAL = "city_dash_postal"
    BANGLA_CITY = "bangla_city"
    END_OF_ADDRESS = "end_of_address"
    CONTEXTUAL = "contextual"
    AREA_INFERENCE = "area_inference"
    NOT_FOUND = "not_found"
    NOT_CONFIDENT = "not_confident"


@dataclass
class CityResult:
    """Result of city/district extraction"""
    city: str  # District
    confidence: float
    method: ExtractionMethod
    original: str = ""
    reason: str = ""
    division: str = ""  # Division (inferred from district or extracted directly)
    division_confidence: float = 0.0  # Confidence for division extraction
    country: str = ""  # Country (Bangladesh by default for all addresses)
    country_confidence: float = 0.0  # Confidence for country extraction
    
    def __str__(self):
        return f"City('{self.city}', {self.confidence:.1%}, {self.method.value}, Division: '{self.division}', Country: '{self.country}')"
    
    def to_dict(self) -> Dict:
        return {
            'city': self.city,  # District
            'division': self.division,
            'country': self.country,
            'confidence': self.confidence,
            'division_confidence': self.division_confidence,
            'country_confidence': self.country_confidence,
            'method': self.method.value,
            'original': self.original,
            'reason': self.reason
        }


class AdvancedCityExtractor:
    """Advanced City Extractor for Bangladeshi Addresses"""
    
    def __init__(self, confidence_threshold: float = 0.00):
        self.confidence_threshold = confidence_threshold
        self._load_city_variations()
        self._load_district_to_division_mapping()
        self._setup_patterns()
        self._setup_exclusions()
    
    def _load_city_variations(self):
        """Load city variations from JSON file"""
        city_variations_file = Path(__file__).parent.parent.parent / 'city-variations.json'
        self.city_variations = {}
        self.normalized_cities = {}  # Maps variations to normalized names
        
        if city_variations_file.exists():
            try:
                with open(city_variations_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'city_variations' in data:
                        self.city_variations = data['city_variations']
                        # Create reverse mapping: variation -> normalized
                        for variation, normalized in self.city_variations.items():
                            self.normalized_cities[variation.lower()] = normalized
            except Exception as e:
                print(f"Warning: Could not load city variations: {e}")
                self.city_variations = {}
                self.normalized_cities = {}
        else:
            self.city_variations = {}
            self.normalized_cities = {}
    
    def _load_district_to_division_mapping(self):
        """Load district to division mapping"""
        mapping_file = Path(__file__).parent.parent.parent / 'division' / 'district-to-division-mapping.json'
        self.district_to_division = {}
        
        if mapping_file.exists():
            try:
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'mapping' in data:
                        self.district_to_division = data['mapping']
            except Exception as e:
                print(f"Warning: Could not load district-to-division mapping: {e}")
                self.district_to_division = {}
        else:
            self.district_to_division = {}
    
    def _normalize_city(self, city: str) -> str:
        """Normalize city name using variations"""
        city_lower = city.lower().strip()
        if city_lower in self.normalized_cities:
            return self.normalized_cities[city_lower]
        
        # Handle specific variations
        if city_lower in ['chottogram', 'chattagram', 'chittagong', 'chattagong']:
            return 'Chattogram'
        
        # If not found, return capitalized version
        return city.strip().title()
    
    def _get_division_from_district(self, district: str) -> Tuple[str, float]:
        """Get division from district using mapping"""
        if not district:
            return "", 0.0
        
        # Normalize district name
        district_normalized = self._normalize_city(district)
        
        # Check mapping
        division = self.district_to_division.get(district_normalized, "")
        
        if division:
            # High confidence when inferred from district (95%)
            return division, 0.95
        return "", 0.0
    
    def _extract_country(self, address: str) -> Tuple[str, float]:
        """Extract country from address (explicit mentions or default to Bangladesh)"""
        if not address:
            return "Bangladesh", 0.95  # Default to Bangladesh with high confidence
        
        address_lower = address.lower()
        
        # Country names and variations
        country_patterns = {
            'Bangladesh': ['bangladesh', 'bangladesh', 'bd', 'b.d.', 'b.d', 'bdesh', 'বাংলাদেশ'],
            'India': ['india', 'ind', 'ভারত'],
            'Pakistan': ['pakistan', 'pak', 'পাকিস্তান'],
            'Myanmar': ['myanmar', 'burma', 'মিয়ানমার'],
            'Nepal': ['nepal', 'নেপাল'],
            'Bhutan': ['bhutan', 'ভুটান'],
            'Sri Lanka': ['sri lanka', 'srilanka', 'ceylon', 'শ্রীলঙ্কা']
        }
        
        # Pattern 1: Explicit mentions like "Bangladesh", "BD", "বাংলাদেশ"
        for country, variations in country_patterns.items():
            for variation in variations:
                # Check for standalone country mentions
                pattern = rf'\b{re.escape(variation)}\b'
                if re.search(pattern, address_lower, re.IGNORECASE):
                    # Check if it's at the end of address (high confidence)
                    if address_lower.endswith(variation.lower()) or address_lower.endswith(variation.lower() + '.'):
                        return country, 1.00
                    # Check if it's in the last few words
                    words = address.split(',')
                    if len(words) > 0 and variation.lower() in words[-1].lower():
                        return country, 0.98
                    # Otherwise, medium confidence
                    return country, 0.90
        
        # Default: Since all addresses are from Bangladesh, return Bangladesh with high confidence
        return "Bangladesh", 0.95
    
    def _extract_division_directly(self, address: str) -> Tuple[str, float]:
        """Extract division directly from address (explicit mentions)"""
        if not address:
            return "", 0.0
        
        # All 8 divisions of Bangladesh
        divisions = {
            'Dhaka': ['dhaka', 'ঢাকা'],
            'Chattogram': ['chattogram', 'chittagong', 'chottogram', 'chattagram', 'ctg', 'চট্টগ্রাম'],
            'Sylhet': ['sylhet', 'silhet', 'সিলেট'],
            'Rajshahi': ['rajshahi', 'রাজশাহী'],
            'Khulna': ['khulna', 'খুলনা'],
            'Barisal': ['barisal', 'barishal', 'বরিশাল'],
            'Rangpur': ['rangpur', 'রংপুর'],
            'Mymensingh': ['mymensingh', 'mymensing', 'ময়মনসিংহ']
        }
        
        # Bangla division names
        bangla_divisions = {
            'ঢাকা': 'Dhaka',
            'চট্টগ্রাম': 'Chattogram',
            'সিলেট': 'Sylhet',
            'রাজশাহী': 'Rajshahi',
            'খুলনা': 'Khulna',
            'বরিশাল': 'Barisal',
            'রংপুর': 'Rangpur',
            'ময়মনসিংহ': 'Mymensingh'
        }
        
        address_lower = address.lower()
        
        # Pattern 1: "Division: Dhaka", "বিভাগ: ঢাকা", "Dhaka Division", "ঢাকা বিভাগ"
        explicit_patterns = [
            (r'(?:division|বিভাগ)[\s]*:[\s]*([A-Za-z\u0980-\u09FF]+)', 1.00),  # "Division: Dhaka" or "বিভাগ: ঢাকা"
            (r'(?:division|বিভাগ)[\s]+([A-Za-z\u0980-\u09FF]+)', 1.00),  # "Division Dhaka" or "বিভাগ ঢাকা"
            (r'([A-Za-z\u0980-\u09FF]+)[\s]+(?:division|বিভাগ)', 0.98),  # "Dhaka Division" or "ঢাকা বিভাগ"
        ]
        
        for pattern, conf in explicit_patterns:
            match = re.search(pattern, address, re.IGNORECASE)
            if match:
                div_name = match.group(1).strip()
                
                # Check if it's Bangla
                if re.search(r'[\u0980-\u09FF]', div_name):
                    division = bangla_divisions.get(div_name, "")
                    if division:
                        return division, conf
                else:
                    # Check English divisions
                    div_lower = div_name.lower()
                    for div, variations in divisions.items():
                        if div_lower in variations:
                            return div, conf
        
        # Pattern 2: Standalone division mentions at end of address
        words = address.split(',')
        if len(words) > 0:
            last_word = words[-1].strip()
            last_word_clean = re.sub(r'[.,;:!?।]+$', '', last_word).strip()
            
            # Check Bangla divisions
            for bangla_div, eng_div in bangla_divisions.items():
                if bangla_div in last_word_clean:
                    return eng_div, 0.95
            
            # Check English divisions
            last_word_lower = last_word_clean.lower()
            for div, variations in divisions.items():
                if last_word_lower in variations:
                    return div, 0.95
        
        return "", 0.0
    
    def _setup_patterns(self):
        """Setup extraction patterns"""
        
        # ALL 64 DISTRICTS OF BANGLADESH (English) - Comprehensive list
        self.english_cities = [
            # Divisional Cities (Major)
            'Dhaka', 'Dacca', 'Dakha', 'Dhakha', 'Daka', 'Dhka', 'Dhaka City', 'Dhaka District',
            'Chittagong', 'Chattogram', 'Chattagong', 'Chottogram', 'Chattagram', 'Ctg', 'Ctg.', 'Chattogram City', 'Chittagong City',
            'Sylhet', 'Silhet', 'Sylet', 'Silet', 'Sylhet City',
            'Rajshahi', 'Rajshai', 'Rajshahi City',
            'Khulna', 'Khulna City',
            'Barisal', 'Barishal', 'Borishal', 'Barisal City',
            'Mymensingh', 'Mymensing', 'Moymonsingh', 'Moymonshingh', 'Mymensingh City',
            'Rangpur', 'Rangpur City',
            
            # All Districts (Complete List)
            'Bagerhat', 'Bandarban', 'Barguna', 'Bhola', 'Bogra', 'Bogura', 'Brahmanbaria',
            'Chandpur', 'ChapaiNawabganj', 'Chapainawabganj', 'Nawabganj', 'Chuadanga',
            'Comilla', 'Cumilla', 'CoxsBazar', 'Coxs', "Cox's Bazar", 'Cox Bazar', 'Coxsbazar', 'Coxs Bazaar', 'Cox Bazaar',
            'Dinajpur', 'Faridpur', 'Feni', 'Gaibandha', 'Gazipur', 'Gopalganj',
            'Habiganj', 'Jamalpur', 'Jashore', 'Jessore', 'Jessor', 'Jhalokathi', 'Jhenaidah',
            'Joypurhat', 'Khagrachari', 'Kishoreganj', 'Kurigram', 'Kushtia',
            'Lakshmipur', 'Lalmonirhat', 'Madaripur', 'Magura', 'Manikganj', 'Meherpur',
            'Moulvibazar', 'Munshiganj', 'Naogaon', 'Narail', 'Narayanganj', 'Narsingdi',
            'Natore', 'Netrokona', 'Noakhali', 'Pabna', 'Panchagarh', 'Patuakhali',
            'Pirojpur', 'Rajbari', 'Rangamati', 'Satkhira', 'Shariatpur', 'Sherpur',
            'Sirajganj', 'Sunamganj', 'Tangail', 'Thakurgaon',
            
            # Common abbreviations and variations
            'CTG', 'CTg', 'ctg', 'DHA', 'Dha', 'SYL', 'Syl', 'RAJ', 'Raj', 'KHU', 'Khu',
            'BAR', 'Bar', 'RAN', 'Ran', 'MYM', 'Mym', 'COX', 'Cox'
        ]
        
        # ALL DISTRICTS IN BANGLA - Complete mapping
        self.bangla_cities = [
            # Divisional Cities
            'ঢাকা', 'ঢাক', 'চট্টগ্রাম', 'সিলেট', 'রাজশাহী', 'খুলনা', 'বরিশাল', 'রংপুর', 'ময়মনসিংহ',
            
            # All Districts (Bangla)
            'বাগেরহাট', 'বান্দরবান', 'বরগুনা', 'ভোলা', 'বগুড়া', 'ব্রাহ্মণবাড়িয়া', 'চাঁদপুর',
            'চাঁপাইনবাবগঞ্জ', 'চুয়াডাঙ্গা', 'কুমিল্লা', 'কক্সবাজার', 'কক্স', 'দিনাজপুর',
            'ফরিদপুর', 'ফেনী', 'গাইবান্ধা', 'গাজীপুর', 'গোপালগঞ্জ', 'হবিগঞ্জ', 'জামালপুর',
            'যশোর', 'ঝালকাঠি', 'ঝিনাইদহ', 'জয়পুরহাট', 'খাগড়াছড়ি', 'কিশোরগঞ্জ', 'কুড়িগ্রাম',
            'কুষ্টিয়া', 'লক্ষ্মীপুর', 'লালমনিরহাট', 'মাদারীপুর', 'মাগুরা', 'মানিকগঞ্জ',
            'মেহেরপুর', 'মৌলভীবাজার', 'মুন্সিগঞ্জ', 'নওগাঁ', 'নড়াইল', 'নারায়ণগঞ্জ', 'নরসিংদী',
            'নাটোর', 'নেত্রকোণা', 'নোয়াখালী', 'পাবনা', 'পঞ্চগড়', 'পটুয়াখালী', 'পিরোজপুর',
            'রাজবাড়ী', 'রাঙ্গামাটি', 'শরীয়তপুর', 'শেরপুর', 'সিরাজগঞ্জ', 'সুনামগঞ্জ', 'টাঙ্গাইল',
            'ঠাকুরগাঁও', 'সাতক্ষীরা', 'সাভার', 'টঙ্গী'
        ]
        
        # Complete Bangla-to-English mapping for all districts
        self.bangla_to_english_map = {
            'ঢাকা': 'Dhaka',
            'ঢাক': 'Dhaka',  # Handle incomplete "ঢাক" (typo for "ঢাকা")
            'চট্টগ্রাম': 'Chattogram',
            'সিলেট': 'Sylhet',
            'রাজশাহী': 'Rajshahi',
            'খুলনা': 'Khulna',
            'বরিশাল': 'Barisal',
            'রংপুর': 'Rangpur',
            'ময়মনসিংহ': 'Mymensingh',
            'বাগেরহাট': 'Bagerhat',
            'বান্দরবান': 'Bandarban',
            'বরগুনা': 'Barguna',
            'ভোলা': 'Bhola',
            'বগুড়া': 'Bogra',
            'ব্রাহ্মণবাড়িয়া': 'Brahmanbaria',
            'চাঁদপুর': 'Chandpur',
            'চাঁপাইনবাবগঞ্জ': 'ChapaiNawabganj',
            'চুয়াডাঙ্গা': 'Chuadanga',
            'কুমিল্লা': 'Comilla',
            'কক্সবাজার': 'CoxsBazar',
            'কক্স': 'CoxsBazar',
            'দিনাজপুর': 'Dinajpur',
            'ফরিদপুর': 'Faridpur',
            'ফেনী': 'Feni',
            'গাইবান্ধা': 'Gaibandha',
            'গাজীপুর': 'Gazipur',
            'গোপালগঞ্জ': 'Gopalganj',
            'হবিগঞ্জ': 'Habiganj',
            'জামালপুর': 'Jamalpur',
            'যশোর': 'Jashore',
            'ঝালকাঠি': 'Jhalokathi',
            'ঝিনাইদহ': 'Jhenaidah',
            'জয়পুরহাট': 'Joypurhat',
            'খাগড়াছড়ি': 'Khagrachari',
            'কিশোরগঞ্জ': 'Kishoreganj',
            'কুড়িগ্রাম': 'Kurigram',
            'কুষ্টিয়া': 'Kushtia',
            'লক্ষ্মীপুর': 'Lakshmipur',
            'লালমনিরহাট': 'Lalmonirhat',
            'মাদারীপুর': 'Madaripur',
            'মাগুরা': 'Magura',
            'মানিকগঞ্জ': 'Manikganj',
            'মেহেরপুর': 'Meherpur',
            'মৌলভীবাজার': 'Moulvibazar',
            'মুন্সিগঞ্জ': 'Munshiganj',
            'নওগাঁ': 'Naogaon',
            'নড়াইল': 'Narail',
            'নারায়ণগঞ্জ': 'Narayanganj',
            'নরসিংদী': 'Narsingdi',
            'নাটোর': 'Natore',
            'নেত্রকোণা': 'Netrokona',
            'নোয়াখালী': 'Noakhali',
            'পাবনা': 'Pabna',
            'পঞ্চগড়': 'Panchagarh',
            'পটুয়াখালী': 'Patuakhali',
            'পিরোজপুর': 'Pirojpur',
            'রাজবাড়ী': 'Rajbari',
            'রাঙ্গামাটি': 'Rangamati',
            'শরীয়তপুর': 'Shariatpur',
            'শেরপুর': 'Sherpur',
            'সিরাজগঞ্জ': 'Sirajganj',
            'সুনামগঞ্জ': 'Sunamganj',
            'টাঙ্গাইল': 'Tangail',
            'ঠাকুরগাঁও': 'Thakurgaon',
            'সাতক্ষীরা': 'Satkhira',
            'সাভার': 'Savar',
            'টঙ্গী': 'Tongi'
        }
        
        # Common areas that are NOT cities (exclude these) - Comprehensive list from area-mappings.json
        self.area_names = [
            # Dhaka Areas
            'Mirpur', 'Uttara', 'Gulshan', 'Banani', 'Dhanmondi', 'Mohammadpur',
            'Shyamoli', 'Shamoli', 'Shymoli', 'Rampura', 'Khilgaon', 'Motijheel',
            'Farmgate', 'Tejgaon', 'Lalbagh', 'Wari', 'Shantinagar', 'Malibagh',
            'Moghbazar', 'Shahbagh', 'Panthapath', 'Green Road', 'Elephant Road',
            'Nilkhet', 'Azimpur', 'Bashabo', 'Sabujbag', 'Jatrabari', 'Demra',
            'Shyampur', 'Hazaribagh', 'Cantonment', 'Kafrul', 'Pallabi', 'Badda',
            'Khilkhet', 'Baridhara', 'Nikunja', 'Bashundhara', 'Adabor', 'Agargaon',
            'Airport', 'Bangshal', 'Begunbari', 'Bijoy Sarani', 'Dilkusha', 'Fakirapool',
            'Fulbaria', 'Gandaria', 'Gopibagh', 'Goran', 'Hatirjheel', 'Indira Road',
            'Jigatola', 'Kakrail', 'Kamalapur', 'Kamlapur', 'Katabon', 'Kathalbagan',
            'Kuril', 'Lalmatia', 'Magbazar', 'Manik Mia Avenue', 'Mohakhali', 'Mouchak',
            'Nakhalpara', 'New Market', 'Paltan', 'Ramna', 'Russell Square', 'Sadarghat',
            'Siddheswari', 'Sutrapur', 'Tejgaon Industrial Area', 'Tongi', 'Turagh',
            'Wasa', 'Narinda', 'Vashantek', 'Shahjadpur', 'Kataban', 'Shewrapara',
            'Kochukhet', 'Kalabagan', 'Lake Circus', 'Bottola', 'Hathirpool', 'Matuail',
            'Tilpapara', 'Dakshinkhan', 'Balughat', 'Jheelpar', 'Ibrahimpur', 'Banasree',
            'Diyabari', 'Tolarbag', 'Zigatola', 'Shahalibag', 'Kazipara', 'Bonosri',
            'Kalshi', 'Ring Road', 'Jhulonbari', 'Tantibazar', 'Kunjbon', 'Aftabnagar',
            'Uttarkhan', 'Raja Bari', 'Anand Nagar', 'Aftab Nagar', 'Baitul Falah',
            'Baitul Aman', 'Chankharpool', 'Dhanmondi Road', 'Arjatpara', 'Shantipur',
            'West Shewrapara', 'Lalmatia Housing Estate', 'Kochukhet Puran Bazar',
            'Lake Circus Kalabagan', 'Bottola Railgate', 'Hathirpool Pukurpar',
            'South Matuail', 'Lomboritek', 'Middle Badda', 'Gudaraghat Bazar',
            'North Jatrabari', 'Bibir Bagicha', 'Rojonigondha Road', 'North Ibrahimpur',
            'Banasree H Block', 'Zigatola Tannery Mor', 'Chorokghatar Goli',
            'West Kazipara', 'Siddheswari Road', 'Shadhinota Shoroni', 'North Kalshi',
            'Bashundhara R/A', 'Bashundhara Residential Area', 'West Nakhalpara',
            'Abdullahpur', 'Adabor 10', 'Adorshopara', 'Arambag', 'Arifabad Housing Society',
            'Ashulia', 'Avenue 3', 'Avenue-3', 'Badaldi Bazar', 'Bangshal Thana',
            'Baridhara DOHS', 'Baunia', 'Bawnia', 'Block A', 'Block E', 'Block K',
            'Block-B', 'Block-E', 'Block: C', 'Block:K', 'Boishaki Telecom Er Mor',
            'Boubazar', 'Dhaka Bank Goli', 'Dhaka Uddyan', 'East Narsinghpur', 'Faridabad',
            'Fayadabad', 'Ghatarchor', 'Green City', 'Hatirpool', 'Kadamtoli Model Town',
            'Kallyanpur', 'Khilgaon Taltola', 'Laboni Point', 'Lake City', 'Madani Jhil Par',
            'Mirpur 15', 'Mirpur DOHS', 'Mirpur DOHS Link Road', 'Mirpur Original 10',
            'Mirpur-1', 'Mirpur-11', 'Mirpur-12', 'Mirpur-7', 'Mirpur: 1',
            'Moddho Badda Adorsho No Nogor', 'Modinabag Society', 'Mohammadia Housing Society',
            'Molla Para', 'Monsurabad R/A', 'Nababi Mor', 'Nasirabad Housing Society',
            'Nayapaltan', 'Nikunja 2', 'North Badda', 'North Bashabo', 'Purbo Hazipara',
            'Rampura Boubazar', 'Rupnagar Residential Area', 'Sanarpar', 'Savar',
            'Sector 4', 'Sector 9', 'Sector 11', 'Sector-14', 'Sector-18', 'Sher-e-Bangla Nagar',
            'South Bonoshree', 'South Goran', 'South Pallabi', 'Uttar Badda',
            'Uttara Sector -14', 'West Kafrul', 'West Panthapath',
            'Tallabag', 'Nimtola Model Town', 'Merul Badda', 'Kalibari', 'Shamoly Housing',
            'Mogbazar', 'Ekta Housing', 'North Shajahanpur', 'Tejgaon IA', 'Bakshibazar',
            'Rayerbagh', 'Merajnagar', 'Siddeshwari', 'Police Line', 'Niketon', 'Segunbagicha',
            'Dhaka Cantonment', 'East Kazipara', 'Purbo Ahmed Nogor', 'Khilgaon Sipaibag',
            'West Tejturi Bazar', 'Jhigatola', 'Boro Moghbazar Wireless', 'Shakhertak',
            'Kaliyartek', 'Kamarpara', 'South Banossree', 'Water Tank Area', 'Bhashantec',
            'Borobag', 'Chowdhurypara', 'Kollanpur', 'Shonir Akhra Bridge', 'Bosila',
            'West Dhanmondi', 'Shahinbaag', 'Uttar Jatabari', 'Saddam Market', 'Zero Point',
            'Baitul Aman Jame Moshjid', 'Kodomtuli', 'Manikde', 'Uttar Mugdha', 'Jannat Bagh',
            'Jurain', 'Alambag', 'Postogola',
            
            # Chattogram Areas
            'Agrabad', 'Nasirabad', 'Halishahar', 'Pahartali', 'Patenga', 'Bandar', 'EPZ',
            'Chawkbazar', 'Andarkilla', 'Lalkhan Bazar', 'New Market', 'Golpahar', 'Panchlaish',
            'Panchlaish Thana', 'Katalgonj', 'Kunjochaya Avashik', 'North Agrabad',
            'Ramna Residential Area', 'Bakolia', 'Mojaffor Noghor', 'Polytechnic Mood',
            'Rahman Nagar', 'Hill View', 'Khulshi', 'Chandgaon', 'Bayezid', 'Muradpur',
            'Chattogram Sadar', 'Chattogram City', 'Wasa', 'Oxygen', 'Oxygen Mor',
            'Firozshah Colony', 'Sholoshahar', 'Sholoshahar New Area', 'Sholoshahar Old Area',
            'Sholoshahar Railway', 'Sholoshahar Bus Stand', 'Sholoshahar Market',
            'Block - C', 'Mog Pukur Par', 'Mogoltuli Bazarer Mukhe', 'Mozzafar Nagar',
            'P.S: Bakolia', 'Proshanti', 'Sitakunda', 'South Khulsi', 'Subarea',
            'Thana Panchlaish', 'Ameen Centre', 'DC Hill', 'Dewanhat', 'Dhoom Para',
            'East Nasirabad', 'Eidga Boro Pukur Par', 'H Block', 'Jhongkar',
            'Middle Rampur', 'Mohammadpur Residential Area', 'Nazirhat Fatickchari',
            'North Patenga', 'Noyahat', 'Shaheed Minar Goli', 'Shamsi Colony',
            'Thana: Double Mooring', 'West Khulshi', 'Chok Bajar', 'Bitora Mosjidar Ahga',
            'GEC Circle', 'Akbarshah', 'Bagh Ghona', 'Hillside R/A', 'Khulshi Thana',
            'Andorkillah', 'Banijjakiran Market', 'H & I Block',
            
            # Sylhet Areas
            'Shahjalal University', 'Kadamtali', 'Amberkhana', 'Bandar Bazar', 'Zindabazar',
            'Subhanighat', 'Kumarpara', 'Shibganj', 'Sylhet Sadar', 'Sylhet City',
            'Osmani Nagar', 'Shahporan', 'Dargah Gate', 'Taltola', 'Mirabazar', 'Jail Road',
            'Uposhahar', 'Shahjalal Uposhahar', 'Nayasarak', 'Chowhatta', 'Bondor Bazar',
            
            # Rajshahi Areas
            'Sapura', 'Rajshahi University', 'Shah Makhdum', 'Katakhali', 'Padma',
            'Shaheb Bazar', 'Rajshahi Sadar', 'Rajshahi City', 'Kadamtali', 'Upashahar',
            'Shah Makhdum Airport', 'Padma Residential Area', 'Katakhali Bazar', 'Horogram',
            'Kajla', 'Dharampur', 'Kumar Para', 'Kazla', 'Octroi Mor', 'Terikhadiya',
            
            # Gazipur Areas
            'Kaliakair', 'Kapasia', 'Sreepur', 'Kaliganj', 'National University',
            'Open University', 'Gazipur Sadar', 'Gazipur City', 'Joydebpur', 'Kashimpur',
            'Bhawal', 'Rajendrapur', 'Rajendrapur Cantonment', 'Pepsi Gate',
            'Gazipur Cantonment', 'Gazipur Chowrasta', 'Shimultoly',
            
            # Narayanganj Areas
            'Fatullah', 'Siddhirganj', 'Bandar', 'Rupganj', 'Sonargaon', 'Araihazar',
            'Narayanganj Sadar', 'Bandar Upazila', 'Rupganj Upazila', 'Sonargaon Upazila',
            'Chashara', 'Jamtola', 'Jamtola Masjid Goli', 'Masjid Goli', 'Chashara Bazar',
            'Takkar Math', 'Uttor Sehachor', 'Bondor Akrampur', 'Mizmizi Pochimpara',
            'Duspipe Jalkuri',
            
            # Khulna Areas
            'Sonadanga', 'Khulna University', 'Khan Jahan Ali', 'Daulatpur', 'Phultala',
            'Dumuria', 'Khulna Sadar', 'Khulna City', 'Labonchara', 'Royel Mor', 'Gollamari',
            'Boyra', 'Khalishpur', 'Shiromoni', 'Royel Area'
        ]
    
    def _setup_exclusions(self):
        """Setup exclusion patterns"""
        # Words that should not be extracted as cities (English)
        self.excluded_words = [
            'house', 'home', 'building', 'bldg', 'flat', 'apt', 'apartment',
            'road', 'rd', 'street', 'st', 'lane', 'avenue', 'goli', 'moholla',
            'para', 'block', 'sector', 'phase', 'level', 'floor', 'lift',
            'tower', 'market', 'bazar', 'shop', 'store', 'office', 'bank',
            'school', 'college', 'university', 'hospital', 'clinic', 'mosque',
            'masjid', 'temple', 'church', 'park', 'garden', 'society', 'housing',
            'estate', 'complex', 'residence', 'villa', 'mansion', 'plaza',
            'center', 'centre', 'mall', 'supermarket', 'restaurant', 'hotel',
            'cafe', 'station', 'bus', 'train', 'airport', 'port', 'terminal',
            'thana', 'police', 'station', 'post', 'office', 'gpo', 'g.p.o',
            'sadar', 'upazila', 'union', 'ward', 'village', 'gram', 'pur',
            'nagar', 'nagar', 'colony', 'colony', 'area', 'zone', 'region'
        ]
        
        # Bangla words that should not be extracted as cities
        self.bangla_excluded_words = [
            'বাড়ি', 'বাসা', 'বিল্ডিং', 'ফ্ল্যাট', 'রোড', 'সড়ক', 'লেন', 'গলি',
            'মহল্লা', 'পাড়া', 'ব্লক', 'সেক্টর', 'তলা', 'লিফট', 'টাওয়ার',
            'মার্কেট', 'বাজার', 'দোকান', 'অফিস', 'ব্যাংক', 'স্কুল', 'কলেজ',
            'বিশ্ববিদ্যালয়', 'হাসপাতাল', 'ক্লিনিক', 'মসজিদ', 'মন্দির', 'গির্জা',
            'পার্ক', 'বাগান', 'সোসাইটি', 'হাউজিং', 'এস্টেট', 'কমপ্লেক্স', 'বাসভবন',
            'ভিলা', 'প্লাজা', 'সেন্টার', 'মল', 'রেস্তোরাঁ', 'হোটেল', 'ক্যাফে',
            'স্টেশন', 'বাস', 'ট্রেন', 'বিমানবন্দর', 'বন্দর', 'থানা', 'পুলিশ',
            'পোস্ট', 'অফিস', 'সদর', 'উপজেলা', 'ইউনিয়ন', 'ওয়ার্ড', 'গ্রাম',
            'নগর', 'কলোনি', 'এলাকা', 'জোন', 'অঞ্চল', 'মহানগর', 'শহর'
        ]
    
    def _is_excluded(self, word: str) -> bool:
        """Check if word should be excluded"""
        word_lower = word.lower().strip()
        word_original = word.strip()
        
        # Check English excluded words
        if word_lower in self.excluded_words:
            return True
        
        # Check Bangla excluded words
        if any(bangla_word in word_original for bangla_word in self.bangla_excluded_words):
            return True
        
        # Check area names
        if word_lower in [a.lower() for a in self.area_names]:
            return True
        
        return False
    
    def _is_building_name_city(self, city: str, address: str, position: int) -> bool:
        """Check if extracted city is part of a building/area name like 'Lake City', 'Green City', 'Rakeen City', 'Priyanka City', 'Yunusco City Center'"""
        city_lower = city.lower().strip()
        
        # Common building/area name patterns that contain "City" but aren't actual cities
        building_city_patterns = [
            'lake city', 'green city', 'rakeen city', 'model city', 'dream city',
            'royal city', 'golden city', 'silver city', 'new city', 'old city',
            'smart city', 'eco city', 'mega city', 'super city', 'mini city',
            'garden city', 'park city', 'hill city', 'sea city', 'river city',
            'sun city', 'star city', 'moon city', 'diamond city', 'platinum city',
            'emerald city', 'pearl city', 'coral city', 'crystal city', 'gold city',
            'silver city', 'bronze city', 'copper city', 'steel city', 'iron city',
            'priyanka city', 'yunusco city', 'city center', 'city centre'
        ]
        
        # Check if the word appears before "City" in a building name pattern
        context_before = address[max(0, position-50):position].lower()
        context_after = address[position:min(len(address), position+50)].lower()
        
        # Check for "X City" pattern where X is the extracted word
        if re.search(rf'\b{re.escape(city_lower)}\s+city\b', context_after, re.IGNORECASE):
            # Check if it's a known building name pattern
            full_pattern = f"{city_lower} city"
            if full_pattern in building_city_patterns:
                return True
            
            # If the word before "City" is NOT a known city, it's likely a building name
            is_known_city = False
            for eng_city in self.english_cities:
                if city_lower == eng_city.lower():
                    is_known_city = True
                    break
            
            if not is_known_city:
                # STRICT: If word is NOT in the 64 cities list and appears before "City", it's a building name
                # This ensures we ONLY extract from the 64 districts/cities of Bangladesh
                return True
        
        # Check for "X City Center" or "X City Centre" pattern
        if re.search(rf'\b{re.escape(city_lower)}\s+city\s+(?:center|centre)\b', context_after, re.IGNORECASE):
            # STRICT: If the word is NOT a known city (from 64 districts), it's definitely a building name
            is_known_city = False
            for eng_city in self.english_cities:
                if city_lower == eng_city.lower():
                    is_known_city = True
                    break
            
            if not is_known_city:
                return True
        
        # Check for "X City" in parentheses (common building name pattern)
        if re.search(rf'\([^)]*{re.escape(city_lower)}\s+city[^)]*\)', address, re.IGNORECASE):
            # STRICT: If the word is NOT a known city (from 64 districts), it's a building name
            is_known_city = False
            for eng_city in self.english_cities:
                if city_lower == eng_city.lower():
                    is_known_city = True
                    break
            
            if not is_known_city:
                return True
        
        return False
    
    def _is_valid_city(self, city: str, address: str = "", position: int = -1) -> bool:
        """Validate if extracted text is a valid city"""
        if not city or len(city) < 2:
            return False
        
        city_lower = city.lower().strip()
        
        # Check if it's in excluded words
        if self._is_excluded(city):
            return False
        
        # CRITICAL: Check if it's part of a building name like "Lake City", "Green City", "Rakeen City"
        if address and position >= 0:
            if self._is_building_name_city(city, address, position):
                return False
        
        # Check if it's a known city (English or Bangla) - STRICT MATCHING
        for eng_city in self.english_cities:
            # Exact match or the extracted city is the full city name
            if city_lower == eng_city.lower():
                return True
            # Allow partial match only if the extracted city is longer (e.g., "Chattogram" matches "Chattogram")
            if eng_city.lower() in city_lower and len(city_lower) >= len(eng_city.lower()) * 0.8:
                return True
        
        # Check Bangla cities - STRICT MATCHING
        for bangla_city in self.bangla_cities:
            if bangla_city == city or city == bangla_city:
                return True
            # Allow if city contains the full Bangla city name
            if bangla_city in city and len(city) >= len(bangla_city) * 0.8:
                return True
        
        # Check normalized cities
        if city_lower in self.normalized_cities:
            return True
        
        # If it's a very short word (< 3 chars), likely not a city
        if len(city.strip()) < 3:
            return False
        
        # If it contains numbers, likely not a city
        if re.search(r'\d', city):
            return False
        
        # STRICT: If it's a single word and not in our known cities list, reject it
        # This prevents false positives like "Lake", "Green", "Rakeen"
        if len(city.split()) == 1:
            # Must be in known cities list
            is_known = False
            for eng_city in self.english_cities:
                if city_lower == eng_city.lower():
                    is_known = True
                    break
            if not is_known:
                for bangla_city in self.bangla_cities:
                    if bangla_city == city:
                        is_known = True
                        break
            if not is_known:
                return False
        
        return True
    
    def extract(self, address: str) -> CityResult:
        """Extract city from address"""
        if not address:
            return CityResult("", 0.0, ExtractionMethod.NOT_FOUND, address, "Empty address")
        
        original_address = address
        address_lower = address.lower()
        
        # Try patterns in order of confidence
        all_matches = []
        
        # 1. EXPLICIT CITY PATTERNS (95-100% confidence) - HIGHEST PRIORITY
        # Pattern: "City: Dhaka", "City: Chattogram", "শহর: ঢাকা", "জেলা: ঢাকা", "জেলা নোয়াখালী", "District-Tangail", etc.
        explicit_patterns = [
            # Pattern: "জেলা: ঢাকা", "জেলা: ঢাক" (জেলা before city, handle incomplete "ঢাক") - HIGHEST PRIORITY
            (r'জেলা[\s]*:[\s]*([\u0980-\u09FF]+)', 1.00),  # "জেলা: ঢাকা" or "জেলা: ঢাক"
            (r'জেলা[\s]+([\u0980-\u09FF]+)', 1.00),  # "জেলা নোয়াখালী"
            # Pattern: "City: Dhaka", "শহর: ঢাকা", "District-Tangail", "District: Tangail"
            (r'(?:city|শহর|district)[\s]*:[\s]*([A-Za-z\u0980-\u09FF]+)', 1.00),
            (r'(?:city|শহর|district)[\s]+([A-Za-z\u0980-\u09FF]+)', 1.00),
            (r'(?:city|শহর|district)[\s]*-[\s]*([A-Za-z\u0980-\u09FF]+)', 1.00),  # "District-Tangail"
            # Pattern: "Dhaka City", "ঢাকা শহর", "ঢাকা জেলা" - BUT exclude building names like "Lake City"
            (r'([A-Za-z\u0980-\u09FF]+)[\s]+(?:city|শহর|জেলা|district)', 0.98),
        ]
        
        for pattern, conf in explicit_patterns:
            match = re.search(pattern, address, re.IGNORECASE)
            if match:
                city = match.group(1).strip()
                match_start = match.start()
                
                # CRITICAL: Check if this is a building name pattern (e.g., "Lake City", "Green City", "Rakeen City")
                if self._is_building_name_city(city, address, match_start):
                    continue  # Skip building names
                
                if self._is_valid_city(city, address, match_start):
                    # Check if it's Bangla
                    if re.search(r'[\u0980-\u09FF]', city):
                        normalized = self.bangla_to_english_map.get(city, city)
                    else:
                        normalized = self._normalize_city(city)
                    all_matches.append({
                        'city': normalized,
                        'confidence': conf,
                        'method': ExtractionMethod.EXPLICIT_CITY,
                        'position': match_start
                    })
                    break  # Use first match
        
        # 2. CITY-DASH-POSTAL PATTERNS (90-100% confidence)
        # Pattern: "Dhaka-1207", "Chattogram-4000", etc.
        for eng_city in self.english_cities:
            pattern = rf'\b({re.escape(eng_city)})[\s-]+(\d{{4}})'
            match = re.search(pattern, address, re.IGNORECASE)
            if match:
                city = match.group(1).strip()
                postal = match.group(2)
                # Verify it's not part of a longer word
                start = match.start()
                end = match.end()
                if start > 0 and address[start-1].isalnum():
                    continue
                if end < len(address) and address[end].isalnum():
                    continue
                normalized = self._normalize_city(city)
                all_matches.append({
                    'city': normalized,
                    'confidence': 0.98,
                    'method': ExtractionMethod.CITY_DASH_POSTAL,
                    'position': start
                })
        
        # 3. BANGLA CITY PATTERNS (90-100% confidence)
        # Check for Bangla city names with various patterns
        for bangla_city in self.bangla_cities:
            # Pattern 0: "পুরান ঢাকা" (Old Dhaka) - 100% confidence
            if bangla_city == 'ঢাকা':
                pattern = r'পুরান[\s]+ঢাকা'
                match = re.search(pattern, address)
                if match:
                    pos = match.start()
                    normalized = self.bangla_to_english_map.get(bangla_city, bangla_city)
                    all_matches.append({
                        'city': normalized,
                        'confidence': 1.00,
                        'method': ExtractionMethod.BANGLA_CITY,
                        'position': pos
                    })
            
            # Pattern 1: Bangla city with "জেলা" before it (e.g., "জেলা নোয়াখালী") - HIGH PRIORITY
            pattern = rf'জেলা[\s]*:?[\s]+{re.escape(bangla_city)}'
            match = re.search(pattern, address)
            if match:
                pos = match.start()
                normalized = self.bangla_to_english_map.get(bangla_city, bangla_city)
                all_matches.append({
                    'city': normalized,
                    'confidence': 0.99,  # 99% - explicit mention with "জেলা"
                    'method': ExtractionMethod.BANGLA_CITY,
                    'position': pos
                })
            
            # Pattern 2: Bangla city with dash and postal code (e.g., "ঢাকা-১২১৬")
            pattern = rf'({re.escape(bangla_city)})[\s-]+[\d০-৯]{{4}}'
            match = re.search(pattern, address)
            if match:
                pos = match.start()
                normalized = self.bangla_to_english_map.get(bangla_city, bangla_city)
                all_matches.append({
                    'city': normalized,
                    'confidence': 0.98,
                    'method': ExtractionMethod.BANGLA_CITY,
                    'position': pos
                })
            
            # Pattern 3: Bangla city with "জেলা" or "শহর" after it (e.g., "ঢাকা জেলা", "ঢাকা শহর")
            pattern = rf'({re.escape(bangla_city)})[\s]+(?:জেলা|শহর)'
            match = re.search(pattern, address)
            if match:
                pos = match.start()
                normalized = self.bangla_to_english_map.get(bangla_city, bangla_city)
                all_matches.append({
                    'city': normalized,
                    'confidence': 0.97,
                    'method': ExtractionMethod.BANGLA_CITY,
                    'position': pos
                })
            
            # Pattern 4: Standalone Bangla city (explicit mentions) - 95-100% confidence
            if bangla_city in address:
                pos = address.find(bangla_city)
                # Check if it's not part of a longer word
                if pos > 0 and address[pos-1].isalnum():
                    continue
                if pos + len(bangla_city) < len(address) and address[pos + len(bangla_city)].isalnum():
                    continue
                
                # Check if it's a standalone word (comma-separated or at start/end)
                words = address.split(',')
                is_standalone = False
                is_first_word = False
                is_last_word = False
                
                for i, word in enumerate(words):
                    word_clean = word.strip()
                    # Exact match: "নারায়ণগঞ্জ" or "ঢাকা"
                    if word_clean == bangla_city:
                        is_standalone = True
                        if i == 0:
                            is_first_word = True
                        if i == len(words) - 1:
                            is_last_word = True
                        break
                    # Starts with district and followed by comma, space, or parenthesis: "নারায়ণগঞ্জ, ..." or "নারায়ণগঞ্জ (..."
                    if word_clean.startswith(bangla_city):
                        remaining = word_clean[len(bangla_city):].strip()
                        # Allow trailing punctuation like ), (, etc.
                        if not remaining or remaining.startswith(',') or remaining.startswith('(') or remaining.startswith(')') or remaining.startswith(' '):
                            is_standalone = True
                            if i == 0:
                                is_first_word = True
                            if i == len(words) - 1:
                                is_last_word = True
                            break
                
                # Check if it's at the end of address (high confidence) or near the end
                address_remaining = len(address) - (pos + len(bangla_city))
                
                # 100% confidence for explicit cases: first word, last word, or near end as standalone
                if is_standalone and (is_first_word or is_last_word):
                    # Standalone explicit mention at start/end - 100% confidence
                    normalized = self.bangla_to_english_map.get(bangla_city, bangla_city)
                    all_matches.append({
                        'city': normalized,
                        'confidence': 1.00,
                        'method': ExtractionMethod.BANGLA_CITY,
                        'position': pos
                    })
                elif is_standalone and address_remaining < 30:  # Standalone near end (within 30 chars)
                    # Standalone near end - 100% confidence (very explicit)
                    normalized = self.bangla_to_english_map.get(bangla_city, bangla_city)
                    all_matches.append({
                        'city': normalized,
                        'confidence': 1.00,
                        'method': ExtractionMethod.BANGLA_CITY,
                        'position': pos
                    })
                elif is_standalone or address_remaining < 20:  # Near end of address or standalone in middle
                    normalized = self.bangla_to_english_map.get(bangla_city, bangla_city)
                    all_matches.append({
                        'city': normalized,
                        'confidence': 0.95,
                        'method': ExtractionMethod.BANGLA_CITY,
                        'position': pos
                    })
                else:
                    # Middle of address - lower confidence
                    normalized = self.bangla_to_english_map.get(bangla_city, bangla_city)
                    all_matches.append({
                        'city': normalized,
                        'confidence': 0.90,
                        'method': ExtractionMethod.BANGLA_CITY,
                        'position': pos
                    })
        
        # 4. END OF ADDRESS PATTERNS (85-100% confidence)
        # Districts often appear at the end of addresses OR at the start
        # Check last 2-3 words AND first word
        words = address.split(',')
        if len(words) > 0:
            # FIRST: Check if district is at START of address (comma-separated) - 100% confidence
            # Pattern: "Dhaka, ...", "Narayanganj, ...", "Chittagong, ..." - 100% explicit
            if len(words) > 1:  # Only if there's actually a comma
                first_word = words[0].strip()
                first_word_clean = re.sub(r'[\s-]+[\d০-৯]{4}$', '', first_word).strip()
                
                # Check English cities at start (comma-separated)
                for eng_city in self.english_cities:
                    if first_word_clean.lower() == eng_city.lower():
                        pos = address.find(first_word_clean)
                        if not self._is_building_name_city(eng_city, address, pos):
                            normalized = self._normalize_city(eng_city)
                            # District at START of address (comma-separated) = 100% confidence
                            all_matches.append({
                                'city': normalized,
                                'confidence': 1.00,
                                'method': ExtractionMethod.EXPLICIT_CITY,
                                'position': pos
                            })
                            break
                
                # Check Bangla cities at start (comma-separated)
                for bangla_city in self.bangla_cities:
                    if first_word_clean == bangla_city or first_word_clean.startswith(bangla_city):
                        pos = address.find(bangla_city)
                        normalized = self.bangla_to_english_map.get(bangla_city, bangla_city)
                        # District at START of address (comma-separated) = 100% confidence
                        all_matches.append({
                            'city': normalized,
                            'confidence': 1.00,
                            'method': ExtractionMethod.EXPLICIT_CITY,
                            'position': pos
                        })
                        break
            # First, check for standalone district mentions (comma-separated, explicit)
            # Pattern: "..., DistrictName" or "..., DistrictName, ..." - very explicit
            for i in range(len(words) - 1, max(-1, len(words) - 4), -1):  # Check last 3 words
                word = words[i].strip()
                word_clean = re.sub(r'[\s-]+[\d০-৯]{4}$', '', word).strip()
                
                # Check if it's a standalone district mention
                for eng_city in self.english_cities:
                    if word_clean.lower() == eng_city.lower():
                        pos = address.rfind(word_clean)
                        if not self._is_building_name_city(eng_city, address, pos):
                            normalized = self._normalize_city(eng_city)
                            # Standalone district mention gets 100% confidence (very explicit)
                            all_matches.append({
                                'city': normalized,
                                'confidence': 1.00,
                                'method': ExtractionMethod.END_OF_ADDRESS,
                                'position': pos
                            })
                            break
                
                # Check Bangla cities
                for bangla_city in self.bangla_cities:
                    if bangla_city in word_clean:
                        pos = address.rfind(bangla_city)
                        normalized = self.bangla_to_english_map.get(bangla_city, bangla_city)
                        all_matches.append({
                            'city': normalized,
                            'confidence': 0.95,
                            'method': ExtractionMethod.END_OF_ADDRESS,
                            'position': pos
                        })
                        break
            # Check last word
            last_word = words[-1].strip()
            # Remove postal code if present (e.g., "Dhaka-1207" -> "Dhaka")
            # Also remove trailing punctuation like period, comma, etc. (including Bangla punctuation "।")
            last_word_clean = re.sub(r'[\s-]+[\d০-৯]{4}$', '', last_word).strip()
            last_word_clean = re.sub(r'[.,;:!?।]+$', '', last_word_clean).strip()  # Remove trailing punctuation (including Bangla period "।")
            
            # Check if it's a known English city
            for eng_city in self.english_cities:
                if last_word_clean.lower() == eng_city.lower() or last_word_clean.lower() in eng_city.lower():
                    pos = address.rfind(last_word_clean)
                    # CRITICAL: Check if it's a building name
                    if not self._is_building_name_city(eng_city, address, pos):
                        normalized = self._normalize_city(eng_city)
                        # If district is the last word (explicit mention), give 100% confidence
                        # Check if it's a standalone district mention (not part of a longer phrase)
                        is_standalone = (
                            last_word_clean.lower() == eng_city.lower() and
                            (pos == 0 or not address[pos-1].isalnum()) and
                            (pos + len(eng_city) >= len(address) or not address[pos + len(eng_city)].isalnum())
                        )
                        # Standalone district at end = 100% confidence (very explicit)
                        confidence = 1.00 if is_standalone else 0.95
                        all_matches.append({
                            'city': normalized,
                            'confidence': confidence,
                            'method': ExtractionMethod.END_OF_ADDRESS,
                            'position': pos
                        })
                        break
            
            # Check if last word is a Bangla city
            for bangla_city in self.bangla_cities:
                if bangla_city in last_word_clean:
                    pos = address.rfind(bangla_city)
                    normalized = self.bangla_to_english_map.get(bangla_city, bangla_city)
                    # If it's exactly the last word (standalone) or starts the last word, give 100% confidence
                    # This handles cases like "..., ঢাকা" or "..., ঢাকা)" or "..., নারায়ণগঞ্জ"
                    is_exact_last = (
                        last_word_clean.strip() == bangla_city or
                        last_word_clean.strip().startswith(bangla_city) and 
                        (len(last_word_clean.strip()) == len(bangla_city) or 
                         last_word_clean.strip()[len(bangla_city):].strip() in ['', ')', '(', ','])
                    )
                    confidence = 1.00 if is_exact_last else 0.95
                    all_matches.append({
                        'city': normalized,
                        'confidence': confidence,
                        'method': ExtractionMethod.END_OF_ADDRESS,
                        'position': pos
                    })
                    break
            
            # Check second to last word if last word is postal code or other non-city text
            if len(words) > 1:
                second_last = words[-2].strip()
                last_word_lower = words[-1].strip().lower()
                
                # If last word is "Bangladesh" or a postal code, the second to last is likely the district
                # This should get HIGH confidence (95%+) as it's an explicit mention
                is_explicit_district = (
                    last_word_lower == 'bangladesh' or 
                    re.match(r'^[\d০-৯]{4}$', words[-1].strip()) or
                    last_word_lower in ['bd', 'b.d.', 'b.d']
                )
                
                # Check English cities
                for eng_city in self.english_cities:
                    if second_last.lower() == eng_city.lower() or second_last.lower() in eng_city.lower():
                        pos = address.rfind(second_last)
                        # CRITICAL: Check if it's a building name
                        if not self._is_building_name_city(eng_city, address, pos):
                            normalized = self._normalize_city(eng_city)
                            # If it's explicitly mentioned before "Bangladesh" or postal code, give 95%+ confidence
                            confidence = 0.95 if is_explicit_district else 0.88
                            all_matches.append({
                                'city': normalized,
                                'confidence': confidence,
                                'method': ExtractionMethod.END_OF_ADDRESS,
                                'position': pos
                            })
                            break
                
                # Check Bangla cities
                for bangla_city in self.bangla_cities:
                    if bangla_city in second_last:
                        normalized = self.bangla_to_english_map.get(bangla_city, bangla_city)
                        # If it's exactly the second-to-last word (standalone), give 100% confidence
                        # This handles cases like "..., ঢাকা, Bangladesh" or "..., নারায়ণগঞ্জ, 1234"
                        is_exact_second_last = (
                            second_last.strip() == bangla_city or
                            (second_last.strip().startswith(bangla_city) and 
                             len(second_last.strip()) <= len(bangla_city) + 2)  # Allow small trailing chars
                        )
                        confidence = 1.00 if is_exact_second_last else 0.95
                        all_matches.append({
                            'city': normalized,
                            'confidence': confidence,
                            'method': ExtractionMethod.END_OF_ADDRESS,
                            'position': address.rfind(bangla_city)
                        })
                        break
        
        # 5. STANDALONE DISTRICT AT START/END (SPACE-SEPARATED) (100% confidence)
        # Pattern: "Gazipur ...", "Dhaka keranigonj ...", "94/3 ... Dhaka" (space-separated)
        # Check if district appears at the very start OR end of address (first/last word)
        address_words = address.split()
        if len(address_words) > 0:
            # Check FIRST word (space-separated) - skip if already found
            already_found_start = any(m['position'] == 0 or (m['position'] < 20 and m['confidence'] >= 1.0) for m in all_matches)
            if not already_found_start:
                first_word_space = address_words[0].strip()
                first_word_clean_space = re.sub(r'[\s-]+[\d০-৯]{4}$', '', first_word_space).strip()
                
                # Check English cities at start (space-separated)
                for eng_city in self.english_cities:
                    if first_word_clean_space.lower() == eng_city.lower():
                        pos = address.find(first_word_clean_space)
                        if not self._is_building_name_city(eng_city, address, pos):
                            normalized = self._normalize_city(eng_city)
                            # District at START of address (space-separated) = 100% confidence
                            all_matches.append({
                                'city': normalized,
                                'confidence': 1.00,
                                'method': ExtractionMethod.EXPLICIT_CITY,
                                'position': pos
                            })
                            break
            
            # Check LAST word (space-separated) - for addresses like "94/3 Arjatpara Mohakhali Dhaka"
            already_found_end = any(m['position'] > len(address) - 30 and m['confidence'] >= 1.0 for m in all_matches)
            if not already_found_end:
                last_word_space = address_words[-1].strip()
                last_word_clean_space = re.sub(r'[\s-]+[\d০-৯]{4}$', '', last_word_space).strip()
                
                # Check English cities at end (space-separated)
                for eng_city in self.english_cities:
                    if last_word_clean_space.lower() == eng_city.lower():
                        pos = address.rfind(last_word_clean_space)
                        if not self._is_building_name_city(eng_city, address, pos):
                            normalized = self._normalize_city(eng_city)
                            # District at END of address (space-separated) = 100% confidence
                            all_matches.append({
                                'city': normalized,
                                'confidence': 1.00,
                                'method': ExtractionMethod.END_OF_ADDRESS,
                                'position': pos
                            })
                            break
        
        # 6. STANDALONE DISTRICT IN MIDDLE (95-100% confidence)
        # Pattern: "..., DistrictName, ..." or "DistrictName ..." (space-separated, not comma)
        # Check for standalone district mentions that are clearly explicit
        for eng_city in self.english_cities:
            pattern = rf'\b{re.escape(eng_city)}\b'
            matches = list(re.finditer(pattern, address, re.IGNORECASE))
            for match in matches:
                # Skip if already found in higher confidence patterns
                already_found = any(m['position'] == match.start() for m in all_matches)
                if already_found:
                    continue
                
                start = match.start()
                end = match.end()
                
                # CRITICAL: Skip if it's part of a building name like "Lake City", "Green City"
                if self._is_building_name_city(eng_city, address, start):
                    continue
                
                # Check if it's a standalone word (word boundaries on both sides)
                is_standalone_word = (
                    (start == 0 or not address[start-1].isalnum()) and
                    (end >= len(address) or not address[end].isalnum())
                )
                
                # If it's a standalone word and appears early in address or with clear context, give high confidence
                if is_standalone_word:
                    # Check context - if it's followed by upazila/sub-district names, it's still the district
                    context_after = address[end:min(len(address), end+50)].lower()
                    # Common upazila/sub-district indicators that don't change the district
                    upazila_indicators = ['keranigonj', 'sadar', 'cantonment', 'thana', 'upazila', 'upozila']
                    has_upazila_after = any(indicator in context_after[:30] for indicator in upazila_indicators)
                    
                    # If district is standalone and followed by upazila/sub-district, it's 100% confident
                    if has_upazila_after:
                        normalized = self._normalize_city(eng_city)
                        all_matches.append({
                            'city': normalized,
                            'confidence': 1.00,
                            'method': ExtractionMethod.EXPLICIT_CITY,
                            'position': start
                        })
                        continue
                    
                    # If it's at the start (space-separated, not comma), give 100% confidence
                    if start < 50:  # Within first 50 chars
                        normalized = self._normalize_city(eng_city)
                        all_matches.append({
                            'city': normalized,
                            'confidence': 1.00,
                            'method': ExtractionMethod.EXPLICIT_CITY,
                            'position': start
                        })
                        continue
                
                # Check if it's at the END of address (space-separated) - should be 100% confidence
                # Pattern: "... Dhaka", "... Mymensingh.", "... Comilla" (last word)
                address_words_space = address.split()
                if len(address_words_space) > 0:
                    last_word_space = address_words_space[-1].strip()
                    last_word_clean_space = re.sub(r'[.,;:!?।]+$', '', last_word_space).strip()  # Remove trailing punctuation (including Bangla period "।")
                    
                    if last_word_clean_space.lower() == eng_city.lower():
                        pos_end = address.rfind(last_word_clean_space)
                        if not self._is_building_name_city(eng_city, address, pos_end):
                            normalized = self._normalize_city(eng_city)
                            # District at END of address (space-separated) = 100% confidence
                            all_matches.append({
                                'city': normalized,
                                'confidence': 1.00,
                                'method': ExtractionMethod.END_OF_ADDRESS,
                                'position': pos_end
                            })
                            continue
                
                # Otherwise, use contextual pattern (80% confidence)
                context_before = address[max(0, start-30):start].lower()
                context_after = address[end:min(len(address), end+30)].lower()
                
                # Skip if it's part of a building/area name
                exclusion_keywords = ['building', 'tower', 'society', 'housing', 'market', 'bazar',
                                     'বিল্ডিং', 'টাওয়ার', 'সোসাইটি', 'হাউজিং', 'মার্কেট', 'বাজার',
                                     'road', 'street', 'lane', 'রোড', 'সড়ক', 'লেন', 'city']
                if any(keyword in context_before or keyword in context_after for keyword in exclusion_keywords):
                    # But allow if it's a known city and the keyword is far enough away
                    if 'city' in context_after[:10]:  # "City" immediately after might be building name
                        if not any(known_city.lower() == eng_city.lower() for known_city in ['dhaka', 'chattogram', 'sylhet', 'rajshahi', 'khulna', 'barisal']):
                            continue
                
                normalized = self._normalize_city(eng_city)
                all_matches.append({
                    'city': normalized,
                    'confidence': 0.80,
                    'method': ExtractionMethod.CONTEXTUAL,
                    'position': start
                })
        
        # 8. MIXED BANGLA-ENGLISH PATTERNS (85-90% confidence)
        # Pattern: "Dhaka শহর", "ঢাকা City", "Chattogram জেলা", etc.
        mixed_patterns = [
            (r'([A-Za-z]+)[\s]+(?:শহর|জেলা)', 0.88),  # "Dhaka শহর"
            (r'(?:শহর|জেলা)[\s]+([A-Za-z]+)', 0.88),  # "শহর Dhaka"
            (r'([\u0980-\u09FF]+)[\s]+(?:city|district)', 0.88),  # "ঢাকা city"
            (r'(?:city|district)[\s]+([\u0980-\u09FF]+)', 0.88),  # "city ঢাকা"
        ]
        
        for pattern, conf in mixed_patterns:
            match = re.search(pattern, address, re.IGNORECASE)
            if match:
                city = match.group(1).strip()
                match_start = match.start()
                
                # CRITICAL: Check if this is a building name pattern
                if self._is_building_name_city(city, address, match_start):
                    continue  # Skip building names
                
                if self._is_valid_city(city, address, match_start):
                    # Check if it's Bangla
                    if re.search(r'[\u0980-\u09FF]', city):
                        normalized = self.bangla_to_english_map.get(city, city)
                    else:
                        normalized = self._normalize_city(city)
                    
                    all_matches.append({
                        'city': normalized,
                        'confidence': conf,
                        'method': ExtractionMethod.CONTEXTUAL,
                        'position': match_start
                    })
        
        # Filter and prioritize matches
        if not all_matches:
            return CityResult("", 0.0, ExtractionMethod.NOT_FOUND, original_address, "No city pattern matched")
        
        # Remove duplicates (same city, same position)
        unique_matches = []
        seen = set()
        for match in all_matches:
            key = (match['city'].lower(), match['position'])
            if key not in seen:
                seen.add(key)
                unique_matches.append(match)
        
        # Sort by confidence (highest first), then by position (later in address is better for cities)
        unique_matches.sort(key=lambda x: (x['confidence'], -x['position']), reverse=True)
        
        # Return best match
        best_match = unique_matches[0]
        
        # Final validation - STRICT CHECK
        if not self._is_valid_city(best_match['city'], original_address, best_match['position']):
            return CityResult("", 0.0, ExtractionMethod.NOT_FOUND, original_address, "Extracted city failed validation")
        
        # FINAL CHECK: Ensure it's not a building name
        if self._is_building_name_city(best_match['city'], original_address, best_match['position']):
            return CityResult("", 0.0, ExtractionMethod.NOT_FOUND, original_address, "Extracted city is part of building name")
        
        if best_match['confidence'] < self.confidence_threshold:
            return CityResult("", 0.0, ExtractionMethod.NOT_CONFIDENT, original_address, f"Confidence {best_match['confidence']:.1%} below threshold")
        
        # Extract division
        district = best_match['city']
        
        # First try to extract division directly from address
        division, div_conf = self._extract_division_directly(original_address)
        
        # If not found directly, infer from district
        if not division:
            division, div_conf = self._get_division_from_district(district)
        
        # Extract country
        country, country_conf = self._extract_country(original_address)
        
        return CityResult(
            city=district,
            confidence=best_match['confidence'],
            method=best_match['method'],
            original=original_address,
            reason=f"Matched using {best_match['method'].value}",
            division=division,
            division_confidence=div_conf,
            country=country,
            country_confidence=country_conf
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
    """Extract city from single address"""
    print("=" * 80)
    print("CITY EXTRACTION")
    print("=" * 80)
    print()
    print(f"Address: {address}")
    print()
    
    extractor = AdvancedCityExtractor()
    result = extractor.extract(address)
    
    print(f"District:   {result.city or '(not found)'}")
    print(f"Division:   {result.division or '(not found)'}")
    print(f"Country:    {result.country or '(not found)'}")
    print(f"Confidence: {result.confidence:.1%}")
    if result.division:
        print(f"Division Confidence: {result.division_confidence:.1%}")
    if result.country:
        print(f"Country Confidence: {result.country_confidence:.1%}")
    print(f"Method:     {result.method.value}")
    
    if show_details:
        print(f"Reason:     {result.reason}")
    
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
    
    extractor = AdvancedCityExtractor(confidence_threshold=confidence)
    
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
            record['components']['district'] = result.city
            record['components']['division'] = result.division if result.division else ""
            record['components']['country'] = result.country if result.country else "Bangladesh"
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
            record['components']['district'] = ""
            record['components']['division'] = ""
            record['components']['country'] = "Bangladesh"  # Default to Bangladesh
    
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
        output_dir = 'src/app/shared/utils/address-parser/data/json/splited_district_division'
    
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
    
    extractor = AdvancedCityExtractor()
    
    # Categories (with numbered prefixes for sorting)
    categories = {
        '1.excellent_95_100': (0.95, 1.01),  # Include 1.00 (100% confidence)
        '2.very_high_90_95': (0.90, 0.95),
        '3.high_85_90': (0.85, 0.90),
        '4.good_80_85': (0.80, 0.85),
        '5.medium_high_75_80': (0.75, 0.80),
        '6.medium_70_75': (0.70, 0.75),
        '7.acceptable_65_70': (0.65, 0.70),
        '8.low_below_65': (0.00, 0.65),
    }
    
    split_data = {cat: [] for cat in categories.keys()}
    split_data['no_district'] = []
    
    print("🔄 Categorizing records...")
    for i, record in enumerate(data, 1):
        if i % 100 == 0:
            print(f"   Processed {i}/{len(data)} records...")
        
        address = record.get('address', '')
        result = extractor.extract(address)
        
        if result.city and result.confidence >= 0.65:
            # Find appropriate category
            for cat_name, (min_conf, max_conf) in categories.items():
                if min_conf <= result.confidence < max_conf:
                    new_record = {
                        'id': record.get('id', i),
                        'address': record.get('address', ''),
                        'components': {
                            'district': result.city,
                            'division': result.division if result.division else "",
                            'country': result.country if result.country else "Bangladesh"
                        }
                    }
                    split_data[cat_name].append(new_record)
                    break
        else:
            new_record = {
                'id': record.get('id', i),
                'address': record.get('address', ''),
                'components': {
                    'district': "",
                    'division': "",
                    'country': "Bangladesh"  # Default to Bangladesh
                }
            }
            split_data['no_district'].append(new_record)
    
    print()
    print("💾 Saving split datasets...")
    
    # Save each category
    for cat_name, records in split_data.items():
        if cat_name == 'no_district':
            cat_path = output_path / cat_name / 'data.json'
        else:
            cat_path = output_path / 'with_district' / cat_name / 'data.json'
        
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

def cmd_reprocess_all(base_dir: str = None):
    """Re-process all confidence levels"""
    if base_dir is None:
        base_dir = 'src/app/shared/utils/address-parser/data/json/splited_district_division'
    
    input_file = 'src/app/shared/utils/address-parser/data/json/real-customer-address-dataset.json'
    
    print("=" * 80)
    print("RE-PROCESSING ALL LEVELS")
    print("=" * 80)
    print()
    
    # Just run split again to reprocess everything
    cmd_split(input_file, base_dir)


# ============================================================================
# COMMAND: UPDATE SUMMARY
# ============================================================================

def cmd_update_summary(base_dir: str = None):
    """Update split summary"""
    if base_dir is None:
        base_dir = 'src/app/shared/utils/address-parser/data/json/splited_district_division'
    
    base_path = Path(base_dir)
    
    print("=" * 80)
    print("UPDATING SPLIT SUMMARY")
    print("=" * 80)
    print()
    
    print("📂 Loading data files...")
    
    categories = [
        '1.excellent_95_100', '2.very_high_90_95', '3.high_85_90', '4.good_80_85',
        '5.medium_high_75_80', '6.medium_70_75', '7.acceptable_65_70', '8.low_below_65'
    ]
    
    category_counts = {}
    for cat in categories:
        cat_path = base_path / 'with_district' / cat / 'data.json'
        if cat_path.exists():
            data = load_json(cat_path)
            category_counts[cat] = len(data)
            print(f"   ✓ {cat}: {len(data)} records")
        else:
            category_counts[cat] = 0
    
    no_district_path = base_path / 'no_district' / 'data.json'
    if no_district_path.exists():
        no_district_data = load_json(no_district_path)
        no_district_count = len(no_district_data)
        print(f"   ✓ no_district: {no_district_count:,} records")
    else:
        no_district_count = 0
    
    total_with_district = sum(category_counts.values())
    total_records = total_with_district + no_district_count
    
    summary = {
        "statistics": {
            "total_records": total_records,
            "with_district": total_with_district,
            "without_district": no_district_count,
            "coverage_percentage": round((total_with_district / total_records * 100) if total_records > 0 else 0, 2),
            "confidence_breakdown": category_counts
        }
    }
    
    summary_path = base_path / 'split_summary.json'
    save_json(summary_path, [summary])
    
    print()
    print("=" * 80)
    print("SUMMARY UPDATED")
    print("=" * 80)
    print()
    print(f"Total Records:         {total_records:,}")
    print(f"With District:         {total_with_district:,} ({total_with_district/total_records*100:.1f}%)")
    print(f"Without District:      {no_district_count:,} ({no_district_count/total_records*100:.1f}%)")
    print()
    print("Confidence Breakdown:")
    for cat_name, count in category_counts.items():
        if count > 0:
            print(f"  {cat_name:<25} {count:>4} records ({count/total_records*100:>5.1f}%)")
    print()
    print(f"💾 Summary saved to: {summary_path}")
    print()


# ============================================================================
# MAIN CLI
# ============================================================================

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Complete City Processor - All-in-One Solution',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Extract from single address:
    python3 city_processor.py extract "House-825, Road-4A, Baitul Aman Housing Society, Adabor, Mohammadpur, Dhaka-1207"
  
  Process entire dataset:
    python3 city_processor.py process --confidence 0.70
  
  Split dataset by confidence:
    python3 city_processor.py split
  
  Re-process all levels:
    python3 city_processor.py reprocess-all
  
  Update summary:
    python3 city_processor.py update-summary
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract city from address')
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
    
    # Reprocess all command
    reprocess_all_parser = subparsers.add_parser('reprocess-all', help='Re-process all confidence levels')
    reprocess_all_parser.add_argument('--base-dir', help='Base split directory')
    
    # Update summary command
    update_summary_parser = subparsers.add_parser('update-summary', help='Update split summary')
    update_summary_parser.add_argument('--base-dir', help='Base split directory')
    
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
    elif args.command == 'reprocess-all':
        cmd_reprocess_all(args.base_dir)
    elif args.command == 'update-summary':
        cmd_update_summary(args.base_dir)


if __name__ == "__main__":
    main()

