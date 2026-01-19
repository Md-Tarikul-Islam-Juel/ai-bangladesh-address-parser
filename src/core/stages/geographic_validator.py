"""Stage 7: Geographic Intelligence & Validation"""

import logging
from typing import Dict, Optional, List
from pathlib import Path

from ..utils.constants import OFFLINE_GEO_AVAILABLE

logger = logging.getLogger(__name__)

if OFFLINE_GEO_AVAILABLE:
    from src.geo.bangladesh_geo_offline import BangladeshOfflineGeo


class GeographicValidator:
    """
    Dedicated Geographic Intelligence Stage
    
    Uses offline geographic data (data/geographic/division) to:
    1. Validate geographic consistency (area-district-division)
    2. Auto-fill missing components from hierarchy
    3. Predict postal codes from any level
    4. Provide full location hierarchy
    5. Detect and correct geographic conflicts
    """
    
    def __init__(self):
        self.offline_geo = None
        if OFFLINE_GEO_AVAILABLE:
            try:
                geo_data_path = str(Path(__file__).parent.parent.parent.parent / "data" / "geographic" / "division")
                self.offline_geo = BangladeshOfflineGeo(division_data_path=geo_data_path)
                logger.info("✓ Geographic Intelligence enabled")
            except Exception as e:
                logger.warning(f"⚠ Could not load geographic data: {e}")
    
    def validate_and_enhance(self, components: Dict) -> Dict:
        """
        Validate and enhance components using geographic intelligence
        
        Args:
            components: Dictionary with extracted components (area, district, division, postal_code)
        
        Returns:
            Enhanced components with:
            - Geographic validation results
            - Auto-filled missing components
            - Postal code predictions
            - Full location hierarchy
            - Conflict detection
        """
        if not self.offline_geo:
            return {}
        
        result = {}
        area = components.get('area')
        district = components.get('district')
        division = components.get('division')
        postal_code = components.get('postal_code')
        
        # 1. Geographic Consistency Validation
        if area or district or division:
            validation = self.offline_geo.validate_location(
                area=area,
                district=district,
                division=division,
                postal_code=postal_code
            )
            
            if validation.get('valid'):
                result['geographic_valid'] = True
            else:
                result['geographic_valid'] = False
                result['geographic_conflicts'] = validation.get('conflicts', [])
                result['geographic_suggestions'] = validation.get('suggestions', {})
        
        # 2. Auto-fill Missing Components from Hierarchy
        if area and not district:
            # Try to infer district from area (upazila/union lookup)
            area_lower = area.lower()
            if area_lower in self.offline_geo.upazilas:
                upazila_data = self.offline_geo.upazilas[area_lower]
                if not district:
                    result['district'] = {
                        'value': upazila_data.get('district'),
                        'confidence': 0.95,
                        'source': 'geographic_inferred_from_area'
                    }
                if not division:
                    result['division'] = {
                        'value': upazila_data.get('division'),
                        'confidence': 0.95,
                        'source': 'geographic_inferred_from_area'
                    }
            elif area_lower in self.offline_geo.unions:
                union_data = self.offline_geo.unions[area_lower]
                if not district:
                    result['district'] = {
                        'value': union_data.get('district'),
                        'confidence': 0.90,
                        'source': 'geographic_inferred_from_union'
                    }
                if not division:
                    result['division'] = {
                        'value': union_data.get('division'),
                        'confidence': 0.90,
                        'source': 'geographic_inferred_from_union'
                    }
        
        if district and not division:
            # Infer division from district
            district_lower = district.lower()
            if district_lower in self.offline_geo.districts:
                district_data = self.offline_geo.districts[district_lower]
                if district_data.get('division'):
                    result['division'] = {
                        'value': district_data['division'],
                        'confidence': 0.98,
                        'source': 'geographic_inferred_from_district'
                    }
        
        # 3. Postal Code Prediction (if not already present)
        if not postal_code:
            geo_result = self.offline_geo.predict_postal_code(
                area=area or result.get('area', {}).get('value'),
                district=district or result.get('district', {}).get('value'),
                division=division or result.get('division', {}).get('value')
            )
            
            if geo_result and geo_result.get('confidence', 0) >= 0.80:
                result['postal_code'] = {
                    'value': geo_result['postal_code'],
                    'confidence': geo_result['confidence'],
                    'source': f"geographic_{geo_result['source']}"
                }
                if 'full_location' in geo_result:
                    result['full_location_hierarchy'] = geo_result['full_location']
        
        # 4. Full Location Hierarchy (if postal code exists)
        if postal_code:
            hierarchy = self.offline_geo.get_full_hierarchy(postal_code)
            if hierarchy:
                result['location_hierarchy'] = hierarchy
        
        # 5. Area Name Validation (check if area exists in geographic data)
        if area:
            area_lower = area.lower()
            area_found = False
            area_type = None
            
            if area_lower in self.offline_geo.upazilas:
                area_found = True
                area_type = 'upazila'
            elif area_lower in self.offline_geo.unions:
                area_found = True
                area_type = 'union'
            elif area_lower in self.offline_geo.villages:
                area_found = True
                area_type = 'village'
            
            if area_found:
                result['area_validated'] = {
                    'value': area,
                    'type': area_type,
                    'confidence': 0.95,
                    'source': 'geographic_validated'
                }
        
        return result
    
    def extract_from_address(self, address: str, extracted_components: Dict) -> Dict:
        """
        Extract geographic components directly from address using geographic data
        
        This is a proactive extraction that searches the address for
        upazilas, unions, villages that might not be in the main gazetteer
        """
        if not self.offline_geo:
            return {}
        
        result = {}
        address_lower = address.lower()
        
        # Search for upazilas in address
        for upazila_name, upazila_data in self.offline_geo.upazilas.items():
            if upazila_name.lower() in address_lower:
                # Check if already extracted
                current_area = extracted_components.get('area', {}).get('value') if isinstance(extracted_components.get('area'), dict) else extracted_components.get('area')
                if not current_area or upazila_name.lower() not in str(current_area).lower():
                    result['area'] = {
                        'value': upazila_name,
                        'confidence': 0.90,
                        'source': 'geographic_upazila_extraction'
                    }
                    # Auto-fill district and division
                    if not extracted_components.get('district'):
                        result['district'] = {
                            'value': upazila_data.get('district'),
                            'confidence': 0.95,
                            'source': 'geographic_inferred_from_upazila'
                        }
                    if not extracted_components.get('division'):
                        result['division'] = {
                            'value': upazila_data.get('division'),
                            'confidence': 0.95,
                            'source': 'geographic_inferred_from_upazila'
                        }
                    break
        
        # Search for unions if no upazila found
        if 'area' not in result:
            for union_name, union_data in self.offline_geo.unions.items():
                if union_name.lower() in address_lower:
                    current_area = extracted_components.get('area', {}).get('value') if isinstance(extracted_components.get('area'), dict) else extracted_components.get('area')
                    if not current_area or union_name.lower() not in str(current_area).lower():
                        result['area'] = {
                            'value': union_name,
                            'confidence': 0.85,
                            'source': 'geographic_union_extraction'
                        }
                        if not extracted_components.get('district'):
                            result['district'] = {
                                'value': union_data.get('district'),
                                'confidence': 0.90,
                                'source': 'geographic_inferred_from_union'
                            }
                        break
        
        return result
