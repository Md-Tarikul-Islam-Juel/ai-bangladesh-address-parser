"""Stage 2: Canonical Normalization"""

import re
from collections import defaultdict
from typing import Dict


class CanonicalNormalizer:
    """Comprehensive address normalization"""
    
    def __init__(self):
        # Bangla numerals → English
        self.bn_numerals = {
            '০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4',
            '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'
        }
        
        # Bangla places → English (comprehensive)
        self.bn_places = {
            'ঢাকা': 'Dhaka', 'চট্টগ্রাম': 'Chattogram', 'চিটাগাং': 'Chattogram',
            'সিলেট': 'Sylhet', 'রাজশাহী': 'Rajshahi', 'খুলনা': 'Khulna',
            'বরিশাল': 'Barisal', 'রংপুর': 'Rangpur', 'ময়মনসিংহ': 'Mymensingh',
            'বনানী': 'Banani', 'গুলশান': 'Gulshan', 'ধানমন্ডি': 'Dhanmondi',
            'উত্তরা': 'Uttara', 'মিরপুর': 'Mirpur', 'হালিশহর': 'Halishahar',
            'আগ্রাবাদ': 'Agrabad', 'বশুন্ধরা': 'Bashundhara',
        }
        
        # Bangla keywords → English
        self.bn_keywords = {
            'রোড': 'Road', 'বাড়ি': 'House', 'বাসা': 'House', 'বাড়ী': 'House',
            'ফ্ল্যাট': 'Flat', 'তলা': 'Floor', 'ব্লক': 'Block',
            'লেন': 'Lane', 'গলি': 'Lane', 'নং': 'No', 'নাম্বার': 'No',
        }
        
        # Spelling corrections (learned from data)
        self.corrections = {
            'chittagong': 'Chattogram', 'chittagang': 'Chattogram',
            'ctg': 'Chattogram', 'daka': 'Dhaka', 'dhakka': 'Dhaka',
            'raod': 'Road', 'hose': 'House', 'hause': 'House',
        }
        
        self.stats = defaultdict(int)
    
    def normalize(self, address: str) -> str:
        """Comprehensive normalization"""
        if not address:
            return ""
        
        # Convert Bangla numerals
        for bn, en in self.bn_numerals.items():
            address = address.replace(bn, en)
        
        # Transliterate Bangla
        for bn, en in self.bn_places.items():
            address = address.replace(bn, en)
        for bn, en in self.bn_keywords.items():
            address = address.replace(bn, en)
        
        # Remove quotes
        address = address.replace('"', '').replace("'", "")
        
        # Spelling corrections
        for wrong, right in self.corrections.items():
            address = re.sub(r'\b' + wrong + r'\b', right, address, flags=re.IGNORECASE)
        
        # Normalize special characters
        address = address.replace('#', ' No ')
        address = address.replace(':', ' ')
        
        # Clean whitespace
        address = re.sub(r'\s+', ' ', address).strip()
        address = re.sub(r'\s*,\s*', ', ', address)
        
        self.stats['normalized'] += 1
        return address
