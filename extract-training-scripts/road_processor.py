#!/usr/bin/env python3
"""
Complete Road Number Processor - All-in-One Solution
=====================================================

Single comprehensive script for Bangladeshi address road number extraction,
processing, organization, and management.

Features:
    1. Extract road numbers from addresses (Core Algorithm)
    2. Process entire dataset with confidence filtering
    3. Split dataset by confidence levels
    4. Re-process specific confidence folders
    5. Sync changes between split and main dataset

Usage:
    # Extract from single address
    python3 road_processor.py extract "Road No: 2, House No: 24, Diamond Tower"
    
    # Process entire dataset
    python3 road_processor.py process --confidence 0.70
    
    # Split dataset by confidence
    python3 road_processor.py split
    
    # Re-process specific confidence level
    python3 road_processor.py reprocess 2.very_high_90_95
    
    # Update main dataset from split
    python3 road_processor.py sync 2.very_high_90_95

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

# Import house number extractor for validation
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from house_number_processor import \
      AdvancedHouseNumberExtractor as HouseNumberExtractor
    HOUSE_EXTRACTOR_AVAILABLE = True
except ImportError:
    HOUSE_EXTRACTOR_AVAILABLE = False

# Import AI Pattern Learner
try:
    from ai_road_pattern_learner import (AdvancedAIPatternMatcher,
                                         AIPatternLearner)
    AI_ENABLED = True
except ImportError:
    AI_ENABLED = False
    print("Warning: AI Pattern Learner not available. Using standard patterns only.")

# ============================================================================
# CORE EXTRACTION ALGORITHM
# ============================================================================

class ExtractionMethod(Enum):
    """Methods used for extraction"""
    EXPLICIT_ROAD = "explicit_road"
    BANGLA_PATTERN = "bangla_pattern"
    ENGLISH_PATTERN = "english_pattern"
    CONTEXTUAL = "contextual"
    POSITIONAL = "positional"
    MIXED_LANGUAGE = "mixed_language"
    SLASH_FORMAT = "slash_format"
    SEMANTIC_AI = "semantic_ai"  # AI-based semantic matching
    FUZZY_AI = "fuzzy_ai"  # AI-based fuzzy pattern matching
    CONTEXT_AI = "context_ai"  # AI-based context understanding
    PATTERN_LEARNED = "pattern_learned"  # Learned from examples
    NOT_FOUND = "not_found"
    NOT_CONFIDENT = "not_confident"
    INSTITUTIONAL = "institutional_skip"


@dataclass
class RoadNumberResult:
    """Result of road number extraction"""
    road: str
    confidence: float
    method: ExtractionMethod
    original: str = ""
    reason: str = ""
    
    def __str__(self):
        return f"RoadNumber('{self.road}', {self.confidence:.1%}, {self.method.value})"
    
    def to_dict(self) -> Dict:
        return {
            'road': self.road,
            'confidence': self.confidence,
            'method': self.method.value,
            'original': self.original,
            'reason': self.reason
        }


class AdvancedRoadNumberExtractor:
    """Advanced AI-Based Road Number Extractor for Bangladeshi Addresses"""
    
    def __init__(self, preserve_format: bool = True, confidence_threshold: float = 0.70, enable_ai: bool = True):
        self.preserve_format = preserve_format
        self.confidence_threshold = confidence_threshold
        self.enable_ai = enable_ai and AI_ENABLED
        self._setup_advanced_patterns()
        self._setup_exclusions()
        self._setup_bangla_mappings()
        
        # Initialize house number extractor for validation
        if HOUSE_EXTRACTOR_AVAILABLE:
            try:
                self.house_extractor = HouseNumberExtractor(confidence_threshold=0.70)
            except Exception as e:
                self.house_extractor = None
        else:
            self.house_extractor = None
        
        # Initialize AI components if available
        if self.enable_ai:
            try:
                self.ai_matcher = AdvancedAIPatternMatcher()
                self.ai_learner = AIPatternLearner()
                print("🤖 AI Pattern Recognition enabled")
            except Exception as e:
                print(f"Warning: Could not initialize AI components: {e}")
                self.enable_ai = False
        else:
            self.ai_matcher = None
            self.ai_learner = None
        
    def _setup_advanced_patterns(self):
        """Setup advanced extraction patterns"""
        
        # EXPLICIT ROAD PATTERNS (96-100% confidence)
        # CRITICAL: Most specific patterns FIRST, simple patterns LAST
        # HIGHEST PRIORITY: 100% clear road patterns
        self.explicit_road_patterns = [
            # Line patterns - 100% CLEAR ROAD PATTERNS (highest priority)
            (r'((?:line|Line|LINE)[\s]*#[\s]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),  # Line #16 - 100% clear
            (r'((?:line|Line|LINE)[\s-]+[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),  # Line-16, Line 16 - 100% clear
            # Lane with ordinal - 100% CLEAR ROAD PATTERN
            (r'([\d]+(?:st|nd|rd|th)[\s]+(?:lane|Lane|LANE))(?=\s*[,\(\)]|\s|$)', 1.00),  # 2nd Lane, 1st Lane - 100% clear
            # Avenue patterns - 100% CLEAR ROAD PATTERNS
            # Named Avenue (Person/Institution + Avenue) - e.g., "Kazi Nazrul Islam Avenue", "Rani Avenue"
            (r'([A-Z][a-zA-Z\s]{3,}(?:Avenue|AVENUE))(?=\s*[,\(\)]|\s|$)', 1.00),  # Named Avenue - 100% clear (reduced from 5 to 3 chars)
            (r'((?:avenue|Avenue|AVENUE)[\s]+[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),  # Avenue 2, Avenue 5 - 100% clear
            (r'((?:avenue|Avenue|AVENUE)[\s-]+[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),  # Avenue-2, Avenue-5 - 100% clear
            # Lane patterns - e.g., "Lane 10", "Lane-5", "Lane No 3" - capture full
            (r'((?:lane|Lane|LANE)[\s]+(?:no\.?|number|#)?[\s]*[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            (r'((?:lane|Lane|LANE)[\s-]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Named roads with Lane - e.g., "Kazi Office Lane", "Narinda Lane" - 100% clear
            (r'([A-Z][a-zA-Z\s]{2,}(?:Lane|LANE))(?=\s*[,\(\)]|\s|$)', 1.00),  # Named road + Lane - 100% clear
            # Lane with colon - e.g., "Lane:12", "Lane no: 05" - 100% clear
            (r'((?:lane|Lane|LANE)[\s]*(?:no\.?|number)?[\s]*:[\s]*[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 1.00),  # Lane:12, Lane no: 05 - 100% clear
            # Line at end of road name - e.g., "Purana Paltan Line"
            (r'([A-Z][a-zA-Z\s]{3,}[\s]+(?:line|Line|LINE))(?=\s*[,\(\)]|\s|$)', 0.95),  # Named road + Line
            # Goli patterns (Banglish word for road/lane) - e.g., "Baitul Aman Moshjid er goli", "Sopno Outlet er Goli"
            (r'([A-Z][a-zA-Z\s]{3,}[\s]+(?:er|এর)?[\s]*goli)(?=\s*[,\(\)\.]|\s|$)', 0.95),  # Named road + goli (allow period at end)
            # Numbered road with "No." - e.g., "3 No. Road", "5 No Road" - capture full
            (r'([\d০-৯]+[\s]+(?:no\.?|No\.?|NO\.?)[\s]+(?:road|rd|Road|Rd|ROAD|RD))(?=\s*[,\(\)]|\s|$)', 0.98),
            # Named roads (Person/Institution + Road) - e.g., "Jakir Hossain Road", "Nur Mosque Road", "Tiposultan Road", "Diyabari Model High School Road"
            # Match road names, but we'll clean single-letter prefixes in post-processing
            # Allow longer named roads (10+ characters before Road)
            # Include / and ( in the pattern to match "Road/ Kalamia Market" and "Road (beside...)"
            (r'([A-Z][a-zA-Z\s]{10,}(?:Road|Rd|ROAD|RD))(?=\s*[/,(]|\s|$)', 0.95),  # Long named roads first (e.g., "Diyabari Model High School Road")
            (r'([A-Z][a-zA-Z\s]{2,}(?:Road|Rd|ROAD|RD))(?=\s*[,\(\)]|\s|$)', 0.95),  # Shorter named roads
            # Abbreviation + Road - e.g., "D.T Road", "A.B Road" - 100% clear
            (r'([A-Z]\.[A-Z][\s]+(?:Road|Rd|ROAD|RD))(?=\s*[,\(\)]|\s|$)', 1.00),  # Abbreviation + Road - 100% clear
            # Street patterns - e.g., "Mridha Bari Madrasa Street", "Raja Srinath Street Lane" - 100% clear
            (r'([A-Z][a-zA-Z\s]{5,}(?:Street|STREET))(?=\s*[,\(\)]|\s|$)', 1.00),  # Named road + Street - 100% clear
            (r'([A-Z][a-zA-Z\s]{5,}(?:Street|STREET)[\s]+(?:Lane|LANE))(?=\s*[,\(\)]|\s|$)', 1.00),  # Named road + Street Lane - 100% clear
            # Descriptive roads - e.g., "North Road", "South Road", "Crescent Road", "60 Feet"
            (r'((?:North|South|East|West|Central|Main|Crescent|Ulon|Green|New|Old)[\s]+(?:Road|Rd|ROAD|RD))(?=\s*[,\(\)]|\s|$)', 0.96),
            (r'([\d০-৯]+[\s]+(?:Feet|feet|FEET))(?=\s*[,\(\)]|\s|$)', 0.95),
            # Road No # pattern with space - e.g., "Road No #2", "Road No # 2", "Road# 18" - capture full
            (r'((?:road|rd|Road|Rd|ROAD|RD)[\s]+(?:no\.?|number|#)[\s]*#[\s]*[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Road# pattern (no space) - e.g., "Road#18", "Road# 18" - capture full
            (r'((?:road|rd|Road|Rd|ROAD|RD)[\s]*#[\s]*[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Road No: pattern (with colon) - e.g., "Road No: 2", "Road No: 05", "Road No: 14/1", "road:3" - capture full
            (r'((?:road|rd|Road|Rd|ROAD|RD)[\s]+(?:no\.?|number|#)[\s:]*[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Road: pattern (direct colon) - e.g., "road:3", "Road: 5" - capture full
            (r'((?:road|rd|Road|Rd|ROAD|RD)[\s:]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Road No. pattern (with period) - e.g., "Road No. 2", "Road No. 5" - capture full
            (r'((?:road|rd|Road|Rd|ROAD|RD)[\s]+(?:no\.?|number|#)[\s-]*[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Road No - pattern (with dash) - e.g., "Road No - 14/1", "Road No - 2" - capture full
            (r'((?:road|rd|Road|Rd|ROAD|RD)[\s]+(?:no\.?|number|#)[\s-]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Road Number- pattern - e.g., "Road Number-3", "Road Number- 5" - capture full
            (r'((?:road|rd|Road|Rd|ROAD|RD)[\s]+(?:number|Number|NUMBER)[\s-]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Road- pattern with letter suffix - e.g., "Road-4A", "Road-10/A", "Road-13", "Road-N05" - capture full
            (r'((?:road|rd|Road|Rd|ROAD|RD)[\s-]+[Nn]?[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # Road-N05, Road-4A
            # Road # pattern - e.g., "Road #2", "Road #S06" - capture full
            (r'((?:road|rd|Road|Rd|ROAD|RD)[\s]*#[\s]*[\d০-৯A-Z]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Rd. pattern - e.g., "Rd. 5", "Rd. 12" - capture full
            (r'\b((?:rd|Rd|RD)\.?[\s]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Rd- pattern - e.g., "Rd-5", "Rd-12" - capture full
            (r'\b((?:rd|Rd|RD)[\s-]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # R- pattern - e.g., "R-03", "R-2/2", "R-6" - capture full (case insensitive)
            (r'\b([rR][\s-]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # R: pattern - e.g., "R:18", "R:2" - capture full
            (r'\b(r:[\s]*[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # R # pattern - e.g., "R # 9", "R#21", "R#08", "R# 2" - capture full (allow leading zeros and spaces)
            (r'\b([rR]\s*#\s*0?[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),  # R#21, R#08, R# 2
            # R pattern (space) - e.g., "R 6", "R 12" - capture full (case insensitive)
            (r'\b([rR][\s]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
            # Road with letter+number - e.g., "Road E2", "Road 5", "Road 3", "Road 10" - capture full
            (r'((?:road|rd|Road|Rd|ROAD|RD)[\s]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
        ]
        
        # SLASH FORMAT PATTERNS (90-95% confidence)
        self.slash_patterns = [
            # Road with slash pattern - e.g., "Road 14/1", "Road 2/2", "Road 3/C", "Road-10/A"
            (r'(?:road|rd|Road|Rd|ROAD|RD)[\s-]+([\d০-৯]+[/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.93),
            # R with slash pattern - e.g., "R 2/2", "R-2/2" - capture group 1 is the full match
            (r'\b((?:r|R)[\s-]+[\d০-৯]+[/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.93),
            # Standalone slash pattern after road context - e.g., "Road 14/1"
            (r'(?:road|rd|Road|Rd|ROAD|RD)[\s]+([\d০-৯]+[/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.93),
        ]
        
        # CONTEXTUAL PATTERNS (85-95% confidence)
        self.contextual_patterns = [
            # Number after "Road" keyword (contextual) - e.g., "Main Road 5", "Road 3", "Road 10"
            (r'(?:road|rd|Road|Rd|ROAD|RD)[\s]+([\d০-৯]{1,3}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.90),
            # Number before "Road" keyword - e.g., "5 Road", "2 Road"
            (r'([\d০-৯]{1,3}[a-zA-Z]?)[\s]+(?:road|rd|Road|Rd|ROAD|RD)(?=\s*[,\(\)]|\s|$)', 0.90),
            # Number after "Rd" keyword - e.g., "Rd 5", "Rd 12"
            (r'\b(?:rd|Rd|RD)[\s]+([\d০-৯]{1,3}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.90),
        ]
        
        # BANGLA PATTERNS (90-100% confidence)
        self.bangla_patterns = [
            # Bangla named roads with রোড (road) - e.g., "সাতারকুল রোড", "তোপখানা রোড" - 100% clear
            # Capture road name + রোড, but exclude leading numbers
            (r'([\u0980-\u09FF\s]{3,}রোড)(?=\s*[,\(\)]|\s|$)', 1.00),  # Named road + রোড - 100% clear
            # Bangla named lanes with লেন (lane) - e.g., "মদন পাল লেন", "পিসি ব্যানার্জি লেন", "হাজী আবদুর রহমান লেন" - 100% clear
            # Capture lane name + লেন, but exclude leading numbers
            (r'([\u0980-\u09FF\s]{3,}লেন)(?=\s*[,\(\)]|\s|$)', 1.00),  # Named lane + লেন - 100% clear
            # English/Banglish lane with "len" - e.g., "2nd len" - 100% clear
            (r'([\d]+(?:st|nd|rd|th)[\s]+len)(?=\s*[,\(\)]|\s|$)', 1.00),  # 2nd len - 100% clear
            # Bangla named roads with গলি (goli) - e.g., "ডিপটি গলি" - 100% clear
            # Capture road name + গলি (more flexible pattern)
            (r'([\u0980-\u09FF]+[\s]+গলি)(?=\s*[,\(\)]|\s|$)', 1.00),  # Named road + গলি - 100% clear
            # Bangla road with নং - e.g., "রোড নং ২", "রোড নং ১৪", "রোড নং ১০/এ" - capture full phrase - 100% clear
            (r'(রোড[\s]+নং[\s]*[\d০-৯]+[/\-]?[\d০-৯]*[\u0980-\u09FFa-zA-Z]?)(?=\s*\(|\s*[,]|\s|$|[\u0980-\u09FF])', 1.00),  # রোড নং ১৪, রোড নং ১০/এ - 100% clear
            # Bangla road with নাম্বার - e.g., "রোড নাম্বার ৪" - 100% clear
            (r'(রোড[\s]+নাম্বার[\s]*[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,]|\s|$)', 1.00),  # রোড নাম্বার ৪ - 100% clear
            # Bangla road with নম্বর - e.g., "রোড নম্বর ১৮" - 100% clear
            (r'(রোড[\s]+নম্বর[\s]*[\d০-৯]+[/\-]?[\d০-৯]*[\u0980-\u09FFa-zA-Z]?)(?=\s*[,]|\s|$)', 1.00),  # রোড নম্বর ১৮ - 100% clear
            # Bangla number + রোড - e.g., "৬ রোড" - 100% clear
            (r'([\d০-৯]+[\s]+রোড)(?=\s*[,]|\s|$)', 1.00),  # ৬ রোড - 100% clear
            # Bangla রোড with number - e.g., "রোড ৩" - 100% clear
            (r'(রোড[\s]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,]|\s|$)', 1.00),  # রোড ৩ - 100% clear
            # Bangla লেন with colon - e.g., "লেইন : ০২" - 100% clear
            (r'((?:লেন|লেইন)[\s]*:[\s]*[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,]|\s|$)', 1.00),  # লেইন : ০২ - 100% clear
            # Bangla লেন with dash - e.g., "লেন-৩" - 100% clear
            (r'((?:লেন|লেইন)[\s-]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,]|\s|$)', 1.00),  # লেন-৩ - 100% clear
            # Bangla road with number - e.g., "রোড ২", "রোড ১৪"
            (r'(?:রোড|রোড)[\s]+([\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.95),
            # Bangla road with dash - e.g., "রোড-২", "রোড-১৪"
            (r'(?:রোড|রোড)[\s-]+([\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.95),
        ]
        
        # POSITIONAL PATTERNS (70-95% confidence)
        self.positional_patterns = [
            # Standalone number at start before "Road" - e.g., "2 Road"
            (r'^([\d০-৯]{1,3}[a-zA-Z]?)[\s]+(?:road|rd|Road|Rd|ROAD|RD)(?=\s*[,\(\)]|\s|$)', 0.90),
            # Number after comma and before Road - e.g., ", 5 Road"
            (r',[\s]+([\d০-৯]{1,3}[a-zA-Z]?)[\s]+(?:road|rd|Road|Rd|ROAD|RD)(?=\s*[,\(\)]|\s|$)', 0.85),
        ]
        
        # ADDITIONAL PATTERNS (80-95% confidence)
        self.additional_patterns = [
            # Road with leading zero - e.g., "Road 05", "Road 02"
            (r'(?:road|rd|Road|Rd|ROAD|RD)[\s]+(0[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.92),
            # Road with letter suffix after number - e.g., "Road 4A", "Road 3/C"
            (r'(?:road|rd|Road|Rd|ROAD|RD)[\s-]+([\d০-৯]+[a-zA-Z/]+)(?=\s*[,\(\)]|\s|$)', 0.92),
            # Named roads with common patterns - e.g., "School Road", "Mosque Road", "College Road"
            (r'((?:School|Mosque|Masjid|College|University|Hospital|Market|Bazar)[\s]+(?:Road|Rd|ROAD|RD))(?=\s*[,\(\)]|\s|$)', 0.90),
            # Person name + Road (2-4 words before Road) - e.g., "Jakir Hossain Road"
            (r'([A-Z][a-z]+[\s]+[A-Z][a-z]+[\s]+(?:Road|Rd|ROAD|RD))(?=\s*[,\(\)]|\s|$)', 0.88),
            # Complex named roads (3+ words) - e.g., "Diyabari Model High School Road"
            (r'([A-Z][a-zA-Z\s]{10,}(?:Road|Rd|ROAD|RD))(?=\s*[,\(\)]|\s|$)', 0.85),
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
            # Exclude partial words (false positives from city names)
            # BUT: Exclude road keywords from this check - they're valid roads (including "r", "R")
            r'^(?!(?:road|rd|r|lane|line|avenue|street|goli|রোড|লেন)[\s-])[a-z]{1,4}[-]?\d+$',  # rpur-1, haka-1206, robi-1, moli-4 (partial words, but not roads)
            r'^(?!(?:road|rd|r|lane|line|avenue|street|goli|রোড|লেন)\s)[a-z]{1,4}\s+\d+$',  # rpur 1, haka 1207 (partial words with space, but not roads, not "R 6")
            # Exclude city name + postal code patterns
            r'^(?!(?:road|rd|lane|line|avenue|goli|রোড|লেন)[\s-])[A-Z][a-z]+[-]?\d{4}$',  # Dhaka-1215, Dhaka-1219, Mirpur-2 (city + postal code, but not roads)
            # Exclude flat patterns
            r'^flat\s+',  # Flat 7/C, Flat No. 5
            r'^no:\s*\d+$',  # No: 10 (gate numbers)
            # Exclude postal code patterns
            r'^[a-z]{1,4}[-]?\d{4}$',  # haka-1206, haka-1219 (postal codes)
            r'^[a-z]{1,4}\s+\d{4}$',  # haka 1207 (postal codes)
            # Exclude single digits (likely floor numbers)
            r'^\d$',  # 5 (from "5th Floor")
            # Exclude block patterns without road context
            r'^[A-Z]-\d+$',  # B-15 (block numbers)
            r'^[A-Z]-\d+/[A-Z]$',  # F-5/A (block/flat numbers)
            # Exclude apartment/lift/gate numbers
            r'^-\d+$',  # -304 (apartment number)
            r'^(gate|lift)[\s:]*\d+$',  # Gate No. 3, Lift: 2
            # Exclude dag/plot numbers
            r'^dag\s+no\.?\s*\d+$',  # Dag No. 1091
            # Exclude partial words with "No"
            r'^[a-z]{1,4}ter\s+no\.?\s*\d+$',  # rter No. 2 (partial word)
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
        
    def _validate_road_number(self, number: str) -> bool:
        """Validate extracted road number"""
        if not number:
            return False
        # Allow longer named roads (e.g., "Diyabari Model High School Road" is 31 characters)
        if len(number) > 50:
            return False
        
        number = number.strip()
        number_lower = number.lower()
        
        # Check against invalid patterns
        # BUT: Skip invalid pattern check if it starts with road keywords (like "R 6", "R-03")
        if not re.match(r'^(r|road|rd|lane|line|avenue|street|goli|রোড|লেন)[\s-]', number_lower, re.IGNORECASE):
            for pattern in self.invalid_patterns:
                if re.match(pattern, number_lower, re.IGNORECASE):
                    return False
        
        # Exclude partial words (false positives from city names)
        # Patterns like "rpur-1", "haka-1206", "robi-1", "moli-4"
        # BUT: If it starts with road keywords (including "r", "R"), it's definitely a road, not a partial word
        if not re.match(r'^(road|rd|r|lane|line|avenue|street|goli|রোড|লেন)[\s-]', number_lower, re.IGNORECASE):
            if re.match(r'^[a-z]{1,4}[-]?\d+$', number_lower):
                # But allow if it contains road keywords or is a single letter (like "R 6", "R-03")
                if not any(kw in number_lower for kw in ['road', 'rd', 'lane', 'line', 'avenue', 'street', 'goli']) and not re.match(r'^[rR][\s-]', number_lower):
                    return False
        
        # Exclude flat patterns
        if number_lower.startswith('flat'):
            return False
        
        # Exclude gate numbers
        if re.match(r'^(no|gate)[\s:]*\d+$', number_lower):
            return False
        
        # Exclude postal code patterns (partial city name + postal code)
        if re.match(r'^[a-z]{1,4}[-]?\d{4}$', number_lower):
            return False
        
        # Exclude city name + postal code (full city names)
        if re.match(r'^[a-z]{3,}[-]?\d{4}$', number_lower):
            # Common city names in Bangladesh
            city_names = ['dhaka', 'chittagong', 'chattogram', 'sylhet', 'rajshahi', 'khulna', 'barisal', 'mirpur']
            for city in city_names:
                if number_lower.startswith(city):
                    return False
        
        # Exclude apartment/lift/gate numbers
        if re.match(r'^-\d+$', number_lower) or re.match(r'^(gate|lift)[\s:]*\d+$', number_lower):
            return False
        
        # Exclude dag/plot numbers
        if re.match(r'^dag\s+no\.?\s*\d+$', number_lower):
            return False
        
        # Exclude partial words with "No"
        if re.match(r'^[a-z]{1,4}ter\s+no\.?\s*\d+$', number_lower):
            return False
        
        # Exclude single digits (likely floor numbers)
        if re.match(r'^\d$', number_lower):
            return False
        
        # Exclude block patterns without road context
        # BUT: Allow "R-03", "R-6" etc. (road patterns)
        if re.match(r'^[a-z]-\d+$', number_lower) and not re.match(r'^r-\d+', number_lower, re.IGNORECASE):
            return False
        
        # Exclude city names with postal codes (full city names)
        # BUT: If it starts with road keywords, it's definitely a road, not a city
        if not re.match(r'^(road|rd|lane|line|avenue|goli|রোড|লেন)[\s-]', number_lower):
            city_postal_pattern = r'^[a-z]{3,}[-]?\d+$'
            if re.match(city_postal_pattern, number_lower):
                # Common city names in Bangladesh
                city_names = ['dhaka', 'chittagong', 'chattogram', 'sylhet', 'rajshahi', 'khulna', 'barisal', 'mirpur', 'uttara', 'gulshan', 'banani', 'dhanmondi']
                for city in city_names:
                    if number_lower.startswith(city):
                        return False
        
        # Exclude gate/lift patterns (case insensitive)
        if re.match(r'^(gate|lift)[\s:]*no\.?\s*\d+$', number_lower) or re.match(r'^(gate|lift)[\s:]*\d+$', number_lower):
            return False
        
        # Exclude building/complex names that aren't roads
        # Patterns like "Lackcity Concord", "Staff Road Quarter" - these are building names, not roads
        # If it contains common building/complex keywords, exclude it
        # BUT: If it starts with "Road", "Rd", "Lane", "Avenue", etc., it's definitely a road, not a building
        # BUT: If it ends with "Road", "Rd", "Lane", "Avenue", it's definitely a road (e.g., "Diyabari Model High School Road")
        if not re.match(r'^(road|rd|lane|line|avenue|goli|রোড|লেন)[\s-]', number_lower) and not re.match(r'^[\d]+\s+(feet|Feet|FEET)', number_lower):
            # Only check building keywords if it doesn't start with road keywords
            # Also skip if it ends with road keywords (e.g., "School Road", "High School Road")
            if not re.search(r'\b(road|rd|lane|line|avenue|goli|রোড|লেন)\b$', number_lower):
                building_keywords = ['concord', 'quarter', 'tower', 'plaza', 'complex', 'building', 'apartment', 'residence', 'garden', 'villa', 'house', 'mansion']
                for keyword in building_keywords:
                    if keyword in number_lower:
                        # But allow if it's clearly a road (e.g., "Staff Road" is valid)
                        if not re.search(r'\b(road|rd|lane|line|avenue|goli|রোড|লেন)\b', number_lower):
                            return False
        
        # Exclude city names or location names that start with city names
        # e.g., "Narayanganj dewvog pakkaroad" - "Narayanganj" is a city name
        city_names_list = ['dhaka', 'chittagong', 'chattogram', 'sylhet', 'rajshahi', 'khulna', 'barisal', 'mirpur', 'uttara', 'gulshan', 'banani', 'dhanmondi', 'narayanganj', 'comilla', 'cox', 'rangpur', 'mymensingh']
        for city in city_names_list:
            if number_lower.startswith(city):
                # Check if it's actually a road (e.g., "Dhaka Road" is valid)
                if not re.search(r'\b(road|rd|lane|line|avenue|goli|রোড|লেন)\b', number_lower):
                    return False
        
        return True
        
    def _is_postal_code(self, road_number: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted number is actually a postal code"""
        # Check if it's a 4-digit number (typical postal code)
        if re.match(r'^\d{4}$', road_number):
            # Check if it appears after location name or at end of address
            remaining = address[match_end:].strip()
            before_match = address[:match_start].lower()
            
            # If "road" keyword appears before, it's definitely a road number, not postal code
            if 'road' in before_match[-30:] or 'rd' in before_match[-30:] or 'রোড' in before_match[-30:]:
                return False  # It's a road number
            
            # Location keywords that typically precede postal codes
            location_keywords = [
                'dhaka', 'chittagong', 'sylhet', 'rajshahi', 'khulna', 'barisal', 
                'rangpur', 'mymensingh', 'comilla', 'cox', 'bazar', 'sadar', 'chattogram'
            ]
            
            # Check if location name appears before the number
            for loc in location_keywords:
                if loc in before_match[-30:]:  # Last 30 chars before match
                    # But check if there's a road keyword between location and match
                    loc_pos = before_match.rfind(loc)
                    if loc_pos != -1:
                        text_between = before_match[loc_pos:match_start]
                        # If road keyword appears, it's a road number
                        if 'road' in text_between or 'rd' in text_between:
                            return False
                    return True  # Likely postal code
            
            # Check if at end of address (last 15% of address) and no road context
            if match_end > len(address) * 0.85:
                # Check if there's any road context nearby
                context = address[max(0, match_start-50):match_end+20].lower()
                if 'road' in context or 'rd' in context:
                    return False
                return True  # Likely postal code
        
        return False
    
    def _is_sector_number(self, road_number: str, address: str, match_start: int) -> bool:
        """Check if extracted number is actually a sector number (not road)"""
        # If the road_number itself contains road keywords, it's definitely a road, not sector
        road_number_lower = road_number.lower()
        if any(kw in road_number_lower for kw in ['road', 'rd', 'lane', 'রোড']):
            return False  # It's a road, not sector
        
        before_match = address[:match_start].lower()
        
        # Check if "sector" appears immediately before the number (within last 15 chars)
        # This ensures we only exclude numbers that are directly after "Sector"
        if 'sector' in before_match[-15:]:  # Last 15 chars before match
            # Check if there's a road keyword between sector and the match
            sector_pos = before_match.rfind('sector')
            if sector_pos != -1:
                text_between = before_match[sector_pos:match_start]
                # If road keyword appears after sector, it's a road, not sector
                if any(kw in text_between for kw in ['road', 'rd', 'lane']):
                    return False
            return True  # It's a sector number, not road
        
        # Check if "Sector" (capitalized) appears
        before_match_original = address[:match_start]
        if re.search(r'\b[Ss]ector\s+', before_match_original[-20:]):
            # Check if road keyword appears after sector
            sector_match = re.search(r'\b[Ss]ector\s+', before_match_original[-30:])
            if sector_match:
                sector_pos = sector_match.end()
                text_between = before_match_original[sector_pos:match_start].lower()
                if any(kw in text_between for kw in ['road', 'rd', 'lane']):
                    return False
            return True
        
        return False
    
    def _is_floor_number(self, road_number: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted number is actually a floor description (not road)"""
        # Check if it matches floor patterns like "3rd", "4th", "10th", etc.
        if re.match(r'^\d+[rdthndst]+$', road_number.lower()):
            # Check context around the match
            context_before = address[:match_start].lower()
            context_after = address[match_end:match_end+20].lower()
            
            # If "floor" appears after, it's a floor number
            if 'floor' in context_after[:15]:
                return True
            
            # If "floor" appears before, it's also likely a floor
            if 'floor' in context_before[-15:]:
                return True
            
            # Check for patterns like "3rd Floor", "4th Floor"
            full_context = address[max(0, match_start-10):match_end+20].lower()
            if re.search(r'\d+[rdthndst]+\s+floor', full_context):
                return True
        
        return False
    
    def _is_flat_number(self, road_number: str, address: str, match_start: int, match_end: int) -> bool:
        """Check if extracted number is actually a flat number (not road)"""
        # If the road_number itself contains road keywords, it's definitely a road
        road_number_lower = road_number.lower()
        road_keywords = ['road', 'rd', 'রোড', 'r-', 'r:', 'r #', 'lane']
        if any(keyword in road_number_lower for keyword in road_keywords):
            return False  # It's a road, not flat
        
        before_match = address[:match_start].lower()
        context_around = address[max(0, match_start-30):match_end+5].lower()
        
        # Check if "flat" appears before the match
        if 'flat' in before_match[-30:] or 'apartment' in before_match[-30:]:
            # Check for patterns like "Flat C10" where "10" is extracted
            # Look for "Flat" followed by letter + number pattern
            flat_patterns = [
                r'flat\s+[a-z]\d+',  # Flat C10, Flat A8
                r'flat\s+(?:no\.?|number|#|:|-)?[\s]*[\d০-৯]+',  # Flat 904, Flat No 5
                r'flat[\s-]+[\d০-৯]+',  # Flat-904
            ]
            for pattern in flat_patterns:
                flat_match = re.search(pattern, context_around, re.IGNORECASE)
                if flat_match:
                    # Extract the number from the flat pattern
                    flat_text = flat_match.group(0)
                    # Check if the extracted road number is part of this flat pattern
                    if road_number in flat_text or re.search(r'[\d০-৯]+', flat_text).group(0) == road_number:
                        return True
            
            # Short slash patterns: 7/C, 8/A, 4-B, 10-C (100% flat when after "flat")
            if re.match(r'^\d{1,2}[/\-][A-Z]$', road_number, re.IGNORECASE) or re.match(r'^\d{1,2}[-][A-Z]$', road_number, re.IGNORECASE):
                return True
            # Letter + number patterns: G2, A8 (100% flat when after "flat")
            elif re.match(r'^[A-Z]\d+$', road_number, re.IGNORECASE):
                return True
            # Number-letter patterns: 4-B (100% flat when after "flat")
            elif re.match(r'^\d+[-][A-Z]$', road_number, re.IGNORECASE):
                return True
            # Standard flat pattern with "flat" keyword
            elif re.search(r'flat[\s]+(?:no\.?|number|#|:|-|:)', context_around, re.IGNORECASE):
                return True
            # Flat number patterns like "Flat 904", "Flat No 5"
            elif re.search(r'flat[\s]+(?:no\.?|number|#|:|-)?[\s]*[\d০-৯]+', before_match[-30:], re.IGNORECASE):
                return True
        
        # Check for Bangla flat patterns (ফ্ল্যাট)
        if 'ফ্ল্যাট' in address[:match_start]:
            return True
        
        return False
    
    def _is_house_number(self, road_number: str, address: str, match_start: int, match_end: int = None) -> bool:
        """Check if extracted number is actually a house number (not road) - comprehensive patterns from house_number_processor.py"""
        # If the road_number itself contains road keywords, it's definitely a road
        road_number_lower = road_number.lower()
        road_keywords = ['road', 'rd', 'রোড', 'r-', 'r:', 'r #', 'r ', 'r#', 'lane', 'line', 'avenue', 'street', 'goli', 'feet', 'লেন', 'লেইন']
        if any(keyword in road_number_lower for keyword in road_keywords):
            return False  # It's a road, not house
        
        # Check context before and around the match
        before_match = address[:match_start]
        before_match_lower = before_match.lower()
        context_around = address[max(0, match_start-40):match_end+5] if match_end else address[max(0, match_start-40):match_start+20]
        context_around_lower = context_around.lower()
        
        # If explicit road keywords appear before the match, it's definitely a road, not house
        road_keywords_before = ['road', 'rd', 'রোড', 'lane', 'street', 'avenue']
        for keyword in road_keywords_before:
            if keyword in before_match_lower[-25:]:  # Last 25 chars before match
                return False  # It's a road, not house
        
        # COMPREHENSIVE HOUSE NUMBER PATTERNS from house_number_processor.py
        # Check last 40 chars before match for house patterns
        
        # 1. H# patterns (H hash) - e.g., "H# CB 11/12", "H#19"
        if re.search(r'\bh#[\s]*[A-Z]{0,3}[\s]*[\d০-৯]+', before_match[-20:], re.IGNORECASE):
            return True
        
        # 2. House# patterns - e.g., "House#F25", "House# 18"
        if re.search(r'(?:house|home)[#][\s]*[A-Za-z]?[\d০-৯]+', before_match[-25:], re.IGNORECASE):
            return True
        
        # 3. H: patterns (H colon) - e.g., "H:51, R:18"
        if re.search(r'\bh:[\s]*[\d০-৯]+', before_match[-15:], re.IGNORECASE):
            return True
        
        # 4. H # patterns (H space hash) - e.g., "H # 1"
        if re.search(r'\bh\s+#\s*[\d০-৯]+', before_match[-15:], re.IGNORECASE):
            return True
        
        # 5. Letter hash patterns - e.g., "U#19"
        if re.search(r'\b[A-Z]#[\d০-৯]+', before_match[-15:], re.IGNORECASE):
            return True
        
        # 6. H- patterns (H dash) - e.g., "H-07", "H-7", "H-04"
        if re.search(r'\bh[\s-]+[\d০-৯]+', before_match[-15:], re.IGNORECASE):
            # But check if road keyword appears after H
            h_match = re.search(r'\bh[\s-]+[\d০-৯]+', before_match[-20:], re.IGNORECASE)
            if h_match:
                h_pos = match_start - (20 - h_match.start())
                text_after_h = before_match[h_pos:match_start].lower()
                if not any(rk in text_after_h for rk in road_keywords_before):
                    return True  # It's a house number (H-07 pattern)
        
        # 7. H space number/slash - e.g., "H 30/B"
        if re.search(r'\bh\s+[\d০-৯]+[/\-][a-zA-Z\d]+', before_match[-20:], re.IGNORECASE):
            return True
        
        # 8. H with number (no dash) - e.g., "H3"
        if re.search(r'\bh[\s]*[\d০-৯]+', before_match[-10:], re.IGNORECASE):
            # Check if it's not part of a road pattern
            if not re.search(r'\b(?:road|rd|lane)[\s]*[\d০-৯]+', context_around_lower, re.IGNORECASE):
                return True
        
        # 9. Banglish patterns - e.g., "Kha/50", "JA-10/1/A", "CHO 55/A", "Kh-72/8"
        banglish_patterns = [
            r'(?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]*[-/]?[\s]*[\d০-৯]+[/\-][\d০-৯]+[/\-][a-zA-Z\d]+',  # JA-10/1/A
            r'(?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]+[\d০-৯]+[/\-][a-zA-Z\d]+',  # CHO 55/A
            r'(?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]+[\d০-৯]+[/\-][\d০-৯]+',  # Kha 72/8
            r'(?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]*[-/][\s]*[\d০-৯]+[/\-][\d০-৯]+',  # Kha/50, Kh-72/8
            r'(?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]*[/][\s]*[\d০-৯]+',  # Kha/50
            r'(?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]*[-/]?[\s]*[\d০-৯]+',  # Simple Banglish
        ]
        for pattern in banglish_patterns:
            if re.search(pattern, before_match[-25:], re.IGNORECASE):
                return True
        
        # 10. Building patterns - e.g., "Building No 376", "Building 9", "Building-03"
        # BUT: If the extracted road contains road keywords (like "60 Feet"), it's a road, not a building number
        if not any(kw in road_number.lower() for kw in ['road', 'rd', 'lane', 'line', 'avenue', 'goli', 'feet', 'রোড', 'লেন']):
            if re.search(r'(?:building|bldg)[\s]+(?:no\.?|number|#)[\s\-:]*[\d০-৯]+', before_match[-30:], re.IGNORECASE):
                return True
            if re.search(r'(?:building|bldg)[\s]+[\d০-৯]+', before_match[-25:], re.IGNORECASE):
                return True
            if re.search(r'(?:building|bldg)[\s-]+[\d০-৯]+', before_match[-25:], re.IGNORECASE):
                return True
        
        # 11. Plot patterns - e.g., "Plot #24/2", "Plot No. 8", "Plot-6"
        if re.search(r'plot[\s]+(?:no\.?|number|#|:)[\s-]*[\d০-৯]+', before_match[-30:], re.IGNORECASE):
            return True
        if re.search(r'plot[\s]+[\d০-৯]+', before_match[-25:], re.IGNORECASE):
            return True
        if re.search(r'plot[\s-]+[\d০-৯]+', before_match[-25:], re.IGNORECASE):
            return True
        
        # 12. Holding patterns - e.g., "Holding no-1924", "Holding No: 228/B/3/A"
        if re.search(r'holding[\s]+(?:no\.?|number|#)[\s:]*[\s-]*[\d০-৯]+', before_match[-30:], re.IGNORECASE):
            return True
        if re.search(r'holding[\s]+no-[\d০-৯]+', before_match[-25:], re.IGNORECASE):
            return True
        
        # 13. House/Home patterns - comprehensive from house_number_processor.py
        house_patterns = [
            r'(?:house|home|hous|bari|basha)[\s]+(?:no\.?|number)[\s]*#[\s]*[\d০-৯]+',  # House No #17
            r'(?:house|home|hous|bari|basha)[\s]+(?:no\.?|number|#)[\s-]*[\d০-৯]+',  # House No. 16
            r'(?:house|home|hous|bari|basha)[\s]+(?:no\.?|number|#)[\s:]*[\d০-৯]+',  # House No: 01
            r'(?:house|home|hous|bari|basha)[\s]+(?:no\.?|number|#)[\s-]*[A-Za-z][/\-][\d০-৯]+',  # House No. F/30
            r'(?:house|home|hous|bari|basha)[\s]+(?:no\.?|number|#)[\s-]*[A-Za-z][\d০-৯]+',  # House No. B40
            r'(?:house|home|hous|bari|basha)[\s-]+[\d০-৯]+',  # House-303, House-09
            r'(?:house|home|hous|bari|basha)[\s]+-[\s]*[\d০-৯]+',  # House - 8
            r'(?:house|home|hous|bari|basha)[\s]*:[\s]*[\d০-৯]+',  # House: 81/A, House: 1
            r'(?:house|home|hous|bari|basha)[\s]+[A-Za-z][/\-][\d০-৯]+',  # House A/10
            r'(?:house|home|hous|bari|basha)[\s]+[A-Za-z][\d০-৯]+',  # House J57
            r'(?:house|home|hous|bari|basha)[\s]+[\d০-৯]+[/\-][\d০-৯]+',  # House 4/4, House 12/6
            r'(?:house|home|hous|bari|basha)[\s]+[\d০-৯]+',  # House 20, House 1
            r'(?:home)[\s-]+[\d০-৯]+',  # Home-1342
            r'(?:basa|basha)[\s]+(?:no\.?|number|#)[\s-]*[\d০-৯]+',  # Basa no.753
        ]
        for pattern in house_patterns:
            if re.search(pattern, before_match[-35:], re.IGNORECASE):
                # But check if there's a road keyword between house and the match
                house_match = re.search(pattern, before_match[-40:], re.IGNORECASE)
                if house_match:
                    house_pos = match_start - (40 - house_match.end())
                    text_between = before_match[house_pos:match_start].lower()
                    # If road keyword appears after house keyword, it's a road
                    if not any(rk in text_between for rk in road_keywords_before):
                        return True  # Likely house number, not road
        
        # 14. Bangla house patterns - e.g., "বাড়ি#২৩৫", "হোল্ডিং ১৩"
        bangla_house_patterns = [
            r'(?:বাড়ি|বাসা|বাড়ী)[\s]*(?:#|নং|নাম্বার|নম্বর|:)?[\s]*[\d০-৯]+',
            r'(?:বাড়ি|বাসা)[\s]*[\d০-৯]+[/\-][\d০-৯]+',
            r'হোল্ডিং[\s]*(?:নং|নাম্বার|নম্বর)?[\s]*[\d০-৯]+',
            r'বিল্ডিং[\s]*(?:নম্বর|নং)?[\s]*[\d০-৯]+',
        ]
        for pattern in bangla_house_patterns:
            if re.search(pattern, before_match[-30:], re.IGNORECASE):
                return True
        
        # 15. Shop patterns - e.g., "Shop no-165", "Shop-165", "Shop No. 123"
        shop_patterns = [
            r'shop\s+(?:no\.?|number|#|:)[\s-]*[\d০-৯]+',
            r'shop[\s-]+[\d০-৯]+',
        ]
        for pattern in shop_patterns:
            if re.search(pattern, context_around_lower, re.IGNORECASE):
                return True
        
        # 16. Tola patterns (floor numbers) - e.g., "6 tola", "3 tola"
        if re.search(r'[\d০-৯]+\s+tola', context_around_lower, re.IGNORECASE):
            return True
        if re.search(r'tola', context_around_lower, re.IGNORECASE) and re.search(r'[\d০-৯]+', road_number):
            return True
        
        # 17. Apartment abbreviations - e.g., "1215 Apar", "Apar", "Apt"
        if re.search(r'[\d০-৯]+\s+apar', context_around_lower, re.IGNORECASE):
            return True
        if re.search(r'\bapar\b', context_around_lower, re.IGNORECASE):
            return True
        if re.search(r'\bapt\b', context_around_lower, re.IGNORECASE):
            return True
        
        # 18. City names with postal codes - e.g., "ganj -1500", "dhaka-1215", "munshiganj -1500"
        city_postal_patterns = [
            r'[a-z]{3,}\s*-?\s*[\d০-৯]{4}',  # ganj -1500, dhaka-1215
        ]
        for pattern in city_postal_patterns:
            if re.search(pattern, context_around_lower, re.IGNORECASE):
                # Check if it's actually a city name pattern (not a road)
                city_match = re.search(pattern, context_around_lower, re.IGNORECASE)
                if city_match:
                    # If the extracted road number contains city name or postal code pattern, exclude it
                    if re.search(r'[a-z]{3,}\s*-?\s*[\d০-৯]{4}', road_number.lower()):
                        return True
        
        return False
    
    def _is_house_number_using_extractor(self, road_number: str, address: str, match_start: int, match_end: int) -> bool:
        """Use house_number_processor.py to definitively check if extracted number is a house number"""
        if not self.house_extractor:
            return False  # Fallback to pattern-based check if extractor not available
        
        # Extract house number from the address
        house_result = self.house_extractor.extract(address)
        
        # If house extractor found a house number
        if house_result.house_number and house_result.house_number.strip():
            house_num = house_result.house_number.strip()
            road_num = road_number.strip()
            
            # Check if the extracted road number matches or overlaps with the house number
            # Case 1: Exact match
            if house_num.lower() == road_num.lower():
                return True
            
            # Case 2: Road number is part of house number (e.g., house="H-07" and road="07")
            if road_num.lower() in house_num.lower():
                # But exclude if road number contains road keywords (including "r ", "r-")
                if not any(kw in road_num.lower() for kw in ['road', 'rd', 'lane', 'street', 'avenue', 'r ', 'r-', 'রোড']):
                    return True
            
            # Case 3: Check if the match position overlaps with house number position
            # Get the position of house number in address
            house_pos = address.lower().find(house_num.lower())
            if house_pos != -1:
                house_end = house_pos + len(house_num)
                # If road match overlaps with house number position, it's likely a house number
                if match_start < house_end and match_end > house_pos:
                    # But exclude if road number contains explicit road keywords (including "r ", "r-")
                    if not any(kw in road_num.lower() for kw in ['road', 'rd', 'lane', 'street', 'avenue', 'r ', 'r-', 'রোড']):
                        return True
            
            # Case 4: If house number confidence is high and road number doesn't have road keywords
            if house_result.confidence >= 0.85:
                # Check if road number is just a number that could be house number
                if re.match(r'^[\d০-৯]+[a-zA-Z]?$', road_num) and not any(kw in road_num.lower() for kw in ['road', 'rd', 'lane', 'রোড']):
                    # Check context - if house number appears before road number in address
                    if house_pos < match_start:
                        return True
        
        return False
        
    def extract(self, address: str) -> RoadNumberResult:
        """Extract road number from address"""
        if not address:
            return RoadNumberResult("", 0.0, ExtractionMethod.NOT_FOUND, address, "Empty address")
            
        original_address = address
        # Store original for Bangla pattern preservation
        original_address_for_bangla = address
        address = self._bangla_to_english_number(address)
        
        # Skip institutional addresses ONLY if they don't contain clear road patterns
        # Many addresses mention institutions but still have valid road numbers
        if self._is_institutional(address):
            # Check if there are clear road patterns - if yes, still process
            clear_road_patterns = [
                r'\b(?:road|rd|r|lane|line|avenue|street)[\s-]+[\d০-৯]+',
                r'\b[\d০-৯]+\s+(?:road|rd|lane|line|avenue|street)',
                r'রোড[\s]+নং',
                r'রোড[\s]+[\d০-৯]+',
                r'[A-Z][a-zA-Z\s]{5,}(?:Road|Rd|Lane|Street|Avenue)',  # Named roads like "Matuail High School Road"
            ]
            has_clear_road = any(re.search(pattern, address, re.IGNORECASE) for pattern in clear_road_patterns)
            if not has_clear_road:
                return RoadNumberResult("", 0.0, ExtractionMethod.INSTITUTIONAL, original_address, "Institutional address")
        
        all_matches = []
        
        # Try AI-based extraction first if enabled
        if self.enable_ai and self.ai_matcher:
            ai_result = self.ai_matcher.extract_with_ai(address)
            if ai_result:
                road_number, confidence, method_name = ai_result
                # Map method name to ExtractionMethod
                method_map = {
                    'semantic_ai': ExtractionMethod.SEMANTIC_AI,
                    'fuzzy_ai': ExtractionMethod.FUZZY_AI,
                    'context_ai': ExtractionMethod.CONTEXT_AI
                }
                method = method_map.get(method_name, ExtractionMethod.SEMANTIC_AI)
                
                # Validate and add to matches
                if self._validate_road_number(road_number):
                    match_start = address.lower().find(road_number.lower())
                    match_end = match_start + len(road_number) if match_start != -1 else len(address)
                    
                    if not self._is_postal_code(road_number, address, match_start, match_end):
                        if not self._is_sector_number(road_number, address, match_start):
                            if not self._is_floor_number(road_number, address, match_start, match_end):
                                if not self._is_flat_number(road_number, address, match_start, match_end):
                                    if not self._is_house_number(road_number, address, match_start, match_end):
                                        # FINAL CHECK: Use house_number_processor.py to definitively exclude house numbers
                                        if not self._is_house_number_using_extractor(road_number, address, match_start, match_end):
                                            all_matches.append({
                                                'road': road_number,
                                                'confidence': confidence,
                                                'method': method,
                                                'pattern': f'AI_{method_name}',
                                                'match_start': match_start,
                                                'match_end': match_end,
                                            })
                                            
                                            # Learn from successful extraction
                                            if self.ai_learner and confidence >= 0.85:
                                                self.ai_learner.learn_from_success(address, road_number, confidence)
        
        # Try patterns in order of confidence
        all_patterns = [
            (self.positional_patterns, ExtractionMethod.POSITIONAL),
            (self.explicit_road_patterns, ExtractionMethod.EXPLICIT_ROAD),
            (self.additional_patterns, ExtractionMethod.EXPLICIT_ROAD),  # Use explicit road method for additional patterns
            (self.slash_patterns, ExtractionMethod.SLASH_FORMAT),
            (self.contextual_patterns, ExtractionMethod.CONTEXTUAL),
            (self.bangla_patterns, ExtractionMethod.BANGLA_PATTERN),
        ]
        
        for patterns, method in all_patterns:
            for pattern, confidence in patterns:
                # For Bangla patterns, match against original address
                search_text = original_address_for_bangla if method == ExtractionMethod.BANGLA_PATTERN else address
                match = re.search(pattern, search_text, re.IGNORECASE)
                if match:
                    road_number = match.group(1).strip()
                    
                    # Clean up single-letter prefixes (e.g., "A Tiposultan Road" -> "Tiposultan Road")
                    # Check if road starts with single letter + space
                    road_cleanup_pattern = r'^([A-Z])\s+([A-Z][a-z]{2,}.*)$'
                    cleanup_match = re.match(road_cleanup_pattern, road_number)
                    if cleanup_match:
                        single_letter = cleanup_match.group(1)
                        rest_of_road = cleanup_match.group(2)
                        # Check if this single letter appears after a slash or number in the address
                        match_start = match.start()
                        # Get context including the single letter position
                        context_start = max(0, match_start - 15)
                        context = address[context_start:match_start + 1]  # Include position where single letter would be
                        # If there's a pattern like "24/A" or "16/B" or "/A" before the road name, remove the single letter
                        # The pattern should match something like "/A" or "24/A" or "16/B" followed by space
                        if re.search(r'[\d/]+' + re.escape(single_letter) + r'(?:\s|$)', context, re.IGNORECASE):
                            road_number = rest_of_road
                    
                    # Clean up
                    road_number = road_number.rstrip(',.')
                    
                    # For Bangla patterns, preserve original format and clean up
                    if method == ExtractionMethod.BANGLA_PATTERN:
                        original_match = re.search(pattern, original_address_for_bangla, re.IGNORECASE)
                        if original_match:
                            road_number = original_match.group(1).strip()
                            road_number = road_number.rstrip(',.')
                            
                            # Remove leading numbers from named roads
                            # BUT: Don't remove if it's a pattern like "৬ রোড" (number + রোড) - that's a valid road pattern
                            # e.g., "১৪ মদন পাল লেন" -> "মদন পাল লেন", "৪৫ তোপখানা রোড" -> "তোপখানা রোড"
                            # BUT keep "৬ রোড" as is
                            if re.match(r'^[\d০-৯]+\s+', road_number) and not re.search(r'রোড$', road_number):
                                road_number = re.sub(r'^[\d০-৯]+\s+', '', road_number)
                    
                    # Validate road number
                    if not self._validate_road_number(road_number):
                        continue
                    
                    # Get match positions
                    match_start_pos = match.start()
                    match_end_pos = match.end()
                    
                    # STRICT POSTAL CODE VALIDATION
                    if self._is_postal_code(road_number, address, match_start_pos, match_end_pos):
                        continue  # Skip postal codes
                    
                    # Check if this is actually a sector number (not road)
                    if self._is_sector_number(road_number, address, match_start_pos):
                        continue  # Skip sector numbers
                    
                    # Check if this is actually a floor number (not road)
                    if self._is_floor_number(road_number, address, match_start_pos, match_end_pos):
                        continue  # Skip floor numbers
                    
                    # Check if this is actually a flat number (not road)
                    if self._is_flat_number(road_number, address, match_start_pos, match_end_pos):
                        continue  # Skip flat numbers
                    
                    # Check if this is actually a house number (not road)
                    if self._is_house_number(road_number, address, match_start_pos, match_end_pos):
                        continue  # Skip house numbers
                    
                    # FINAL CHECK: Use house_number_processor.py to definitively exclude house numbers
                    if self._is_house_number_using_extractor(road_number, address, match_start_pos, match_end_pos):
                        continue  # Skip house numbers
                    
                    # Store match for later prioritization
                    all_matches.append({
                        'road': road_number,
                        'confidence': confidence,
                        'method': method,
                        'pattern': pattern,
                        'match_start': match.start(),
                        'match_end': match.end(),
                    })
        
        if not all_matches:
            return RoadNumberResult("", 0.0, ExtractionMethod.NOT_FOUND, original_address, "No pattern matched")
        
        # Prioritize matches: prefer explicit road patterns
        def get_priority(match):
            priority = 0
            road_lower = match['road'].lower()
            
            # HIGHEST PRIORITY: 100% clear road patterns (Line #, Line-, 2nd Lane, Avenue, Bangla patterns)
            if re.search(r'line\s*#', road_lower) or re.search(r'line\s*-', road_lower):
                priority += 10000  # Line #16, Line-16 - 100% clear, highest priority
            elif re.search(r'\d+(?:st|nd|rd|th)\s+lane', road_lower) or re.search(r'\d+(?:st|nd|rd|th)\s+len', road_lower):
                priority += 10000  # 2nd Lane, 2nd len - 100% clear, highest priority
            elif re.search(r'avenue\s+[\d০-৯]+', road_lower) or re.search(r'avenue\s*-[\d০-৯]+', road_lower):
                priority += 10000  # Avenue 2, Avenue-2 - 100% clear, highest priority
            
            # Check Bangla patterns (need to check original road, not lowercased)
            road_original = match['road']
            if re.search(r'রোড', road_original) or re.search(r'লেন', road_original) or re.search(r'গলি', road_original):
                priority += 10000  # Bangla road patterns (রোড, লেন, গলি) - 100% clear, highest priority
            
            # HIGH PRIORITY: Lane patterns (should come before named roads)
            elif 'lane' in road_lower:
                priority += 5000
            # HIGH PRIORITY: Explicit road patterns
            elif match['method'] == ExtractionMethod.EXPLICIT_ROAD:
                priority += 3000
            elif match['method'] == ExtractionMethod.SLASH_FORMAT:
                priority += 2000
            elif match['method'] == ExtractionMethod.CONTEXTUAL:
                priority += 1500
            elif match['method'] == ExtractionMethod.BANGLA_PATTERN:
                priority += 1800
            elif match['method'] == ExtractionMethod.POSITIONAL:
                priority += 1000
            
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
        return RoadNumberResult(
            road=best_match['road'],
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
    """Extract road number from single address"""
    print("=" * 80)
    print("ROAD NUMBER EXTRACTION")
    print("=" * 80)
    print()
    print(f"Address: {address}")
    print()
    
    extractor = AdvancedRoadNumberExtractor()
    result = extractor.extract(address)
    
    print(f"Road Number:  {result.road or '(not found)'}")
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
    
    extractor = AdvancedRoadNumberExtractor(confidence_threshold=confidence)
    
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
            record['components']['road'] = result.road
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
            record['components']['road'] = ""
    
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
        output_dir = 'data/json/processing/road'
    
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
    
    extractor = AdvancedRoadNumberExtractor()
    
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
    split_data['no_road_number'] = []
    
    print("🔄 Categorizing records...")
    for i, record in enumerate(data, 1):
        if i % 100 == 0:
            print(f"   Processed {i}/{len(data)} records...")
        
        address = record.get('address', '')
        result = extractor.extract(address)
        
        if result.road and result.confidence >= 0.65:
            # Find appropriate category
            for cat_name, (min_conf, max_conf) in categories.items():
                if min_conf <= result.confidence < max_conf:
                    # Keep only road in components
                    new_record = {
                        'id': record.get('id', i),
                        'address': record.get('address', ''),
                        'components': {
                            'road': result.road
                        }
                    }
                    split_data[cat_name].append(new_record)
                    break
        else:
            # Keep only road in components (empty)
            new_record = {
                'id': record.get('id', i),
                'address': record.get('address', ''),
                'components': {
                    'road': ""
                }
            }
            split_data['no_road_number'].append(new_record)
    
    print()
    print("💾 Saving split datasets...")
    
    # Save each category
    for cat_name, records in split_data.items():
        if cat_name == 'no_road_number':
            cat_path = output_path / cat_name / 'data.json'
        else:
            cat_path = output_path / 'with_road_number' / cat_name / 'data.json'
        
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
        base_dir = 'data/json/processing/road'
    
    data_path = Path(base_dir) / 'with_road_number' / confidence_level / 'data.json'
    
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
    
    extractor = AdvancedRoadNumberExtractor(confidence_threshold=threshold)
    
    print("🔄 Re-processing...")
    updated = 0
    
    for i, record in enumerate(data, 1):
        address = record.get('address', '')
        old_road = record['components'].get('road', '')
        
        result = extractor.extract(address)
        
        if result.confidence >= threshold and result.road != old_road:
            record['components']['road'] = result.road
            updated += 1
            if updated <= 10:
                print(f"   ✓ {old_road} → {result.road}")
    
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
        split_dir = 'data/json/processing/road'
    
    main_path = Path(main_file)
    split_path = Path(split_dir) / 'with_road_number' / confidence_level / 'data.json'
    
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
        road = record['components'].get('road', '')
        if road:
            split_map[address] = road
    
    print("🔄 Updating main dataset...")
    updated = 0
    
    for record in main_data:
        address = record['address']
        if address in split_map:
            old_road = record['components'].get('road', '')
            new_road = split_map[address]
            if old_road != new_road:
                record['components']['road'] = new_road
                updated += 1
                if updated <= 10:
                    print(f"   ✓ {old_road} → {new_road}")
    
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
# COMMAND: TRAIN AI PATTERNS
# ============================================================================

def cmd_train_ai(input_file: str = None):
    """Train AI patterns from dataset"""
    if input_file is None:
        input_file = 'data/json/processing/road/with_road_number/1.excellent_95_100/data.json'
    
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"❌ Error: {input_path} not found")
        return
    
    print("=" * 80)
    print("TRAINING AI PATTERNS")
    print("=" * 80)
    print()
    
    if not AI_ENABLED:
        print("❌ Error: AI Pattern Learner not available")
        print("   Make sure ai_road_pattern_learner.py is in the same directory")
        return
    
    try:
        from ai_road_pattern_learner import AIPatternLearner
        
        learner = AIPatternLearner()
        count = learner.generate_patterns_from_data(input_path)
        
        print()
        print("=" * 80)
        print("TRAINING COMPLETE")
        print("=" * 80)
        print()
        print(f"Generated: {count} new patterns")
        print(f"Patterns saved to: learned_road_patterns.json")
        print()
    except Exception as e:
        print(f"❌ Error during training: {e}")
        import traceback
        traceback.print_exc()


# ============================================================================
# MAIN CLI
# ============================================================================

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description='Complete Road Number Processor - All-in-One Solution',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Extract from single address:
    python3 road_processor.py extract "Road No: 2, House No: 24, Diamond Tower"
  
  Process entire dataset:
    python3 road_processor.py process --confidence 0.70
  
  Split dataset by confidence:
    python3 road_processor.py split
  
  Re-process specific level:
    python3 road_processor.py reprocess 2.very_high_90_95
  
  Sync main dataset:
    python3 road_processor.py sync 2.very_high_90_95
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract road number from address')
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
    
    # Train AI command
    train_parser = subparsers.add_parser('train-ai', help='Train AI patterns from dataset')
    train_parser.add_argument('--input', help='Input file with road number examples')
    
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
    elif args.command == 'train-ai':
        cmd_train_ai(args.input)


if __name__ == "__main__":
    main()

