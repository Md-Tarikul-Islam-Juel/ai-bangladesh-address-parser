"""Stage 5: Regex Pattern Extraction"""

from typing import Dict
import logging

from ..utils.constants import REGEX_AVAILABLE

logger = logging.getLogger(__name__)

if REGEX_AVAILABLE:
    from src.regex.house_number_processor import AdvancedHouseNumberExtractor
    from src.regex.road_processor import AdvancedRoadNumberExtractor
    from src.regex.area_processor import AdvancedAreaExtractor
    from src.regex.district_processor import AdvancedCityExtractor
    from src.regex.postal_code_processor import AdvancedPostalCodeExtractor
    from src.regex.flat_number_processor import AdvancedFlatNumberExtractor
    from src.regex.floor_number_processor import AdvancedFloorNumberExtractor
    from src.regex.block_processor import AdvancedBlockNumberExtractor


class RegexExtractor:
    """Wrapper for regex processors"""

    def __init__(self):
        if REGEX_AVAILABLE:
            self.house_extractor = AdvancedHouseNumberExtractor()
            self.road_extractor = AdvancedRoadNumberExtractor()
            self.area_extractor = AdvancedAreaExtractor()
            self.district_extractor = AdvancedCityExtractor()
            self.postal_extractor = AdvancedPostalCodeExtractor()
            self.flat_extractor = AdvancedFlatNumberExtractor()
            self.floor_extractor = AdvancedFloorNumberExtractor()
            self.block_extractor = AdvancedBlockNumberExtractor()
            logger.info("✓ ALL 8 regex processors loaded")
        else:
            self.house_extractor = None
            self.road_extractor = None
            self.area_extractor = None
            self.district_extractor = None
            self.postal_extractor = None
            self.flat_extractor = None
            self.floor_extractor = None
            self.block_extractor = None

    def extract(self, address: str) -> Dict:
        """Extract components using regex processors"""
        results = {}
        
        if not REGEX_AVAILABLE:
            return results
        
        # House number
        if self.house_extractor:
            house_result = self.house_extractor.extract(address)
            if house_result.house_number:
                results['house_number'] = {
                    'value': house_result.house_number,
                    'confidence': house_result.confidence,
                    'source': 'regex'
                }
        
        # Road
        if self.road_extractor:
            road_result = self.road_extractor.extract(address)
            if road_result.road:
                results['road'] = {
                    'value': road_result.road,
                    'confidence': road_result.confidence,
                    'source': 'regex'
                }
        
        # Area
        if self.area_extractor:
            area_result = self.area_extractor.extract(address)
            if area_result.area:
                results['area'] = {
                    'value': area_result.area,
                    'confidence': area_result.confidence,
                    'source': 'regex'
                }
        
        # District (returns 'city' attribute)
        if self.district_extractor:
            district_result = self.district_extractor.extract(address)
            if hasattr(district_result, 'city') and district_result.city:
                results['district'] = {
                    'value': district_result.city,
                    'confidence': district_result.confidence,
                    'source': 'regex'
                }
                # Also extract division if available
                if hasattr(district_result, 'division') and district_result.division:
                    results['division'] = {
                        'value': district_result.division,
                        'confidence': district_result.division_confidence if hasattr(district_result, 'division_confidence') else district_result.confidence,
                        'source': 'regex'
                    }
        
        # Postal code
        if self.postal_extractor:
            postal_result = self.postal_extractor.extract(address)
            if postal_result.postal_code:
                results['postal_code'] = {
                    'value': postal_result.postal_code,
                    'confidence': postal_result.confidence,
                    'source': 'regex'
                }
        
        # Flat
        if self.flat_extractor:
            flat_result = self.flat_extractor.extract(address)
            if flat_result.flat_number:
                results['flat_number'] = {
                    'value': flat_result.flat_number,
                    'confidence': flat_result.confidence,
                    'source': 'regex'
                }
        
        # Floor
        if self.floor_extractor:
            floor_result = self.floor_extractor.extract(address)
            if floor_result.floor_number:
                results['floor_number'] = {
                    'value': floor_result.floor_number,
                    'confidence': floor_result.confidence,
                    'source': 'regex'
                }
        
        # Block
        if self.block_extractor:
            block_result = self.block_extractor.extract(address)
            if block_result.block_number:
                results['block_number'] = {
                    'value': block_result.block_number,
                    'confidence': block_result.confidence,
                    'source': 'regex'
                }
        
        return results
