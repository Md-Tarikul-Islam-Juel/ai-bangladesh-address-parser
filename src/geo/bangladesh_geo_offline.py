#!/usr/bin/env python3
"""
BANGLADESH COMPLETE OFFLINE GEOGRAPHIC INTELLIGENCE
====================================================

Complete offline geographic hierarchy system for Bangladesh:
- Division > District > Upazila > Union > Village
- All 8 divisions with complete data
- Postal code prediction at any level
- 100% offline operation

Author: Bangladesh Geospatial Expert
Date: January 2026
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from collections import defaultdict


class BangladeshOfflineGeo:
    """
    Complete offline Bangladesh geographic intelligence system
    
    Hierarchy: Division > District > Upazila > Union > Village
    
    Data sources:
    - 8 division files (bd-dhaka-division.json, etc.)
    - bd-postal-codes.json (1,226 postal codes)
    - district-to-division-mapping.json (64 districts)
    """
    
    def __init__(self, division_data_path: str = "../../data/division"):
        self.division_path = Path(division_data_path)
        
        # Complete hierarchy storage
        self.divisions = {}  # {division_name: data}
        self.districts = {}  # {district_name: {division, upazilas, postal_codes}}
        self.upazilas = {}   # {upazila_name: {district, division, postal_code, unions}}
        self.unions = {}     # {union_name: {upazila, district, division}}
        self.villages = {}   # {village_name: {union, upazila, district, division}}
        
        # Postal code mappings
        self.postal_to_upazila = {}  # {postal_code: upazila_name}
        self.postal_to_district = {}  # {postal_code: district_name}
        self.upazila_to_postal = {}  # {upazila_name: postal_code}
        self.district_to_postals = defaultdict(set)  # {district: {postal_codes}}
        
        # Area name to location mapping
        self.area_to_location = defaultdict(list)  # {area_name: [{hierarchy_info}]}
        
        # Load all data
        self._load_complete_hierarchy()
        self._load_postal_codes()
        self._build_search_indices()
    
    def _load_complete_hierarchy(self):
        """Load all 8 division files with complete hierarchy"""
        print("Loading complete Bangladesh geographic hierarchy...")
        
        division_files = [
            'bd-dhaka-division.json',
            'bd-chittagong-division.json',
            'bd-rajshahi-division.json',
            'bd-khulna-division.json',
            'bd-sylhet-division.json',
            'bd-barisal-division.json',
            'bd-rangpur-division.json',
            'bd-mymensingh-division.json',
        ]
        
        total_upazilas = 0
        total_unions = 0
        total_villages = 0
        
        for div_file in division_files:
            file_path = self.division_path / div_file
            if not file_path.exists():
                continue
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle two different JSON formats
            if isinstance(data, dict):
                # Format 1: {division: "Dhaka", districts: [...]}
                division_name = data.get('division')
                districts = data.get('districts', [])
            elif isinstance(data, list):
                # Format 2: [{name: "District", division: "Dhaka", ...}]
                # Extract division from first district
                division_name = data[0].get('division') if data else None
                districts = data
            else:
                continue
            
            if not division_name:
                continue
            
            self.divisions[division_name] = data
            
            # Process districts in this division
            for district in districts:
                district_name = district.get('name')
                
                self.districts[district_name.lower()] = {
                    'division': division_name,
                    'upazilas': [],
                    'postal_codes': set()
                }
                
                # Process upazilas
                for upazila in district.get('upazilas', []):
                    upazila_name = upazila.get('name')
                    postal_code = upazila.get('postalCode', '')
                    
                    total_upazilas += 1
                    
                    # Store upazila
                    self.upazilas[upazila_name.lower()] = {
                        'district': district_name,
                        'division': division_name,
                        'postal_code': postal_code,
                        'unions': []
                    }
                    
                    self.districts[district_name.lower()]['upazilas'].append(upazila_name)
                    
                    # Map postal code
                    if postal_code:
                        self.postal_to_upazila[postal_code] = upazila_name
                        self.postal_to_district[postal_code] = district_name
                        self.upazila_to_postal[upazila_name.lower()] = postal_code
                        self.districts[district_name.lower()]['postal_codes'].add(postal_code)
                    
                    # Process unions
                    for union in upazila.get('unions', []):
                        union_name = union.get('name')
                        total_unions += 1
                        
                        self.unions[union_name.lower()] = {
                            'upazila': upazila_name,
                            'district': district_name,
                            'division': division_name,
                            'postal_code': postal_code
                        }
                        
                        self.upazilas[upazila_name.lower()]['unions'].append(union_name)
                        
                        # Process villages
                        for village in union.get('villages', []):
                            if isinstance(village, dict):
                                village_name = village.get('name', '')
                            else:
                                village_name = str(village)
                            
                            if village_name:
                                total_villages += 1
                                self.villages[village_name.lower()] = {
                                    'union': union_name,
                                    'upazila': upazila_name,
                                    'district': district_name,
                                    'division': division_name,
                                    'postal_code': postal_code
                                }
        
        print(f"✓ Loaded {len(self.divisions)} divisions")
        print(f"✓ Loaded {len(self.districts)} districts")
        print(f"✓ Loaded {total_upazilas} upazilas with postal codes")
        print(f"✓ Loaded {total_unions} unions")
        print(f"✓ Loaded {total_villages} villages")
        print()
    
    def _load_postal_codes(self):
        """Load additional postal codes database"""
        postal_file = self.division_path / "bd-postal-codes.json"
        if not postal_file.exists():
            return
        
        with open(postal_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for entry in data.get('postal_codes', []):
            code = entry.get('code')
            district = entry.get('district', '').lower()
            post_office = entry.get('postOffice', '')
            
            if code and district:
                self.district_to_postals[district].add(code)
                
                # Store post office as area
                if post_office:
                    self.area_to_location[post_office.lower()].append({
                        'type': 'post_office',
                        'district': district,
                        'postal_code': code
                    })
        
        print(f"✓ Loaded {len(data.get('postal_codes', []))} postal code mappings")
        print()
    
    def _build_search_indices(self):
        """Build search indices for fast lookups"""
        # Index all location names for area search
        for upazila_name in self.upazilas.keys():
            self.area_to_location[upazila_name].append({
                'type': 'upazila',
                **self.upazilas[upazila_name]
            })
        
        for union_name in self.unions.keys():
            self.area_to_location[union_name].append({
                'type': 'union',
                **self.unions[union_name]
            })
        
        print(f"✓ Built search indices for {len(self.area_to_location)} locations")
        print()
    
    def predict_postal_code(self, 
                           area: Optional[str] = None,
                           district: Optional[str] = None,
                           division: Optional[str] = None) -> Optional[Dict]:
        """
        Predict postal code from any level of hierarchy
        
        IMPORTANT: When district is provided, only return matches from that district
        for geographic consistency and accuracy
        
        Returns: {
            'postal_code': str,
            'confidence': float,
            'source': str,  # 'upazila', 'district', 'area', etc.
            'full_location': str
        }
        """
        area_lower = area.lower() if area else None
        district_lower = district.lower() if district else None
        
        # Priority 1: Exact upazila match (highest confidence)
        # BUT validate district if provided
        if area_lower and area_lower in self.upazilas:
            upazila_data = self.upazilas[area_lower]
            
            # CRITICAL: Validate district consistency
            if district_lower and upazila_data['district'].lower() != district_lower:
                # Wrong district - skip this match
                pass
            elif upazila_data['postal_code']:
                return {
                    'postal_code': upazila_data['postal_code'],
                    'confidence': 0.95,
                    'source': 'upazila_match',
                    'full_location': f"{area} (Upazila), {upazila_data['district']}, {upazila_data['division']}"
                }
        
        # Priority 2: Exact union match
        # Validate district if provided
        if area_lower and area_lower in self.unions:
            union_data = self.unions[area_lower]
            
            # CRITICAL: Validate district consistency
            if district_lower and union_data['district'].lower() != district_lower:
                # Wrong district - skip
                pass
            elif union_data['postal_code']:
                return {
                    'postal_code': union_data['postal_code'],
                    'confidence': 0.90,
                    'source': 'union_match',
                    'full_location': f"{area} (Union), {union_data['upazila']}, {union_data['district']}"
                }
        
        # Priority 3: Village match
        # Validate district if provided
        if area_lower and area_lower in self.villages:
            village_data = self.villages[area_lower]
            
            # CRITICAL: Validate district consistency
            if district_lower and village_data['district'].lower() != district_lower:
                # Wrong district - skip
                pass
            elif village_data['postal_code']:
                return {
                    'postal_code': village_data['postal_code'],
                    'confidence': 0.85,
                    'source': 'village_match',
                    'full_location': f"{area} (Village), {village_data['union']}, {village_data['upazila']}"
                }
        
        # Priority 4: Area search (post office, fuzzy match)
        # Validate district if provided
        if area_lower and area_lower in self.area_to_location:
            locations = self.area_to_location[area_lower]
            for loc in locations:
                # Check district consistency
                if district_lower and loc.get('district', '').lower() != district_lower:
                    continue  # Skip wrong district
                
                if 'postal_code' in loc and loc['postal_code']:
                    return {
                        'postal_code': loc['postal_code'],
                        'confidence': 0.80,
                        'source': f"{loc.get('type', 'area')}_match",
                        'full_location': f"{area}, {loc.get('district', 'Unknown')}"
                    }
        
        # Priority 5: Fuzzy area match
        # Validate district if provided
        if area_lower:
            for location_name, location_data in self.area_to_location.items():
                if area_lower in location_name or location_name in area_lower:
                    for loc in location_data:
                        # Check district consistency
                        if district_lower and loc.get('district', '').lower() != district_lower:
                            continue
                        
                        if loc.get('postal_code'):
                            return {
                                'postal_code': loc['postal_code'],
                                'confidence': 0.70,
                                'source': 'fuzzy_area_match',
                                'full_location': f"Near {location_name}"
                            }
        
        # Priority 6: District-level inference (lowest confidence)
        if district_lower and district_lower in self.district_to_postals:
            postal_codes = self.district_to_postals[district_lower]
            if postal_codes:
                return {
                    'postal_code': sorted(list(postal_codes))[0],
                    'confidence': 0.60,
                    'source': 'district_inference',
                    'full_location': f"{district} (District-level)"
                }
        
        return None
    
    def get_full_hierarchy(self, postal_code: str) -> Optional[Dict]:
        """Get complete hierarchy from postal code"""
        if postal_code in self.postal_to_upazila:
            upazila = self.postal_to_upazila[postal_code]
            upazila_data = self.upazilas.get(upazila.lower(), {})
            
            return {
                'postal_code': postal_code,
                'upazila': upazila,
                'district': upazila_data.get('district'),
                'division': upazila_data.get('division'),
                'unions': upazila_data.get('unions', [])
            }
        
        return None
    
    def validate_location(self, 
                         area: Optional[str] = None,
                         district: Optional[str] = None,
                         division: Optional[str] = None,
                         postal_code: Optional[str] = None) -> Dict:
        """
        Validate geographic consistency
        
        Returns: {
            'valid': bool,
            'conflicts': List[str],
            'suggestions': Dict
        }
        """
        conflicts = []
        suggestions = {}
        
        # Check if postal code matches district
        if postal_code and district:
            expected_district = self.postal_to_district.get(postal_code)
            if expected_district and expected_district.lower() != district.lower():
                conflicts.append(f"Postal {postal_code} belongs to {expected_district}, not {district}")
                suggestions['district'] = expected_district
        
        # Check if district matches division
        if district and division:
            district_data = self.districts.get(district.lower())
            if district_data:
                expected_division = district_data['division']
                if expected_division.lower() != division.lower():
                    conflicts.append(f"District {district} belongs to {expected_division}, not {division}")
                    suggestions['division'] = expected_division
        
        return {
            'valid': len(conflicts) == 0,
            'conflicts': conflicts,
            'suggestions': suggestions
        }


# Example usage
if __name__ == "__main__":
    geo = BangladeshOfflineGeo()
    
    # Test postal code prediction
    tests = [
        ("Dhanmondi", "Dhaka", None),
        ("Keraniganj", "Dhaka", None),
        ("Halishahar", "Chattogram", None),
        ("Mirpur", "Dhaka", None),
    ]
    
    print("=" * 80)
    print("TESTING OFFLINE POSTAL CODE PREDICTION")
    print("=" * 80)
    print()
    
    for area, district, division in tests:
        result = geo.predict_postal_code(area, district, division)
        if result:
            print(f"Area: {area}, District: {district}")
            print(f"  → Postal Code: {result['postal_code']}")
            print(f"  → Confidence: {result['confidence']:.1%}")
            print(f"  → Source: {result['source']}")
            print(f"  → Location: {result['full_location']}")
        else:
            print(f"Area: {area}, District: {district}")
            print(f"  → No postal code found")
        print()
