"""Stage 7: Gazetteer Validation & Enhancement"""

import json
import logging
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional

from ..utils.constants import OFFLINE_GEO_AVAILABLE, TRIE_AVAILABLE

logger = logging.getLogger(__name__)

if TRIE_AVAILABLE:
    import pygtrie

if OFFLINE_GEO_AVAILABLE:
    from src.geo.bangladesh_geo_offline import BangladeshOfflineGeo


class Gazetteer:
    """
    Gazetteer built from merged_addresses.json
    
    OPTIMIZED WITH:
    - Technique #26: Trie Data Structure (10x faster lookups)
    """
    
    def __init__(self, data_path: Optional[str] = None):
        self.areas = {}  # Keep for backward compatibility
        self.districts = {}
        self.divisions = set()
        self.postal_to_area = defaultdict(set)
        
        # Technique #26: Trie data structure for fast prefix matching
        self.area_trie = None
        if TRIE_AVAILABLE:
            self.area_trie = pygtrie.CharTrie()
        
        # Initialize offline geographic intelligence
        self.offline_geo = None
        if OFFLINE_GEO_AVAILABLE:
            try:
                # Calculate correct path: src/core/stages/ -> src/core/ -> src/ -> root/ -> data/geographic/division
                geo_data_path = str(Path(__file__).parent.parent.parent.parent / "data" / "geographic" / "division")
                self.offline_geo = BangladeshOfflineGeo(division_data_path=geo_data_path)
                logger.info("✓ Offline geographic intelligence enabled")
            except Exception as e:
                logger.warning(f"⚠ Could not load offline geo: {e}")
        
        if data_path and Path(data_path).exists():
            self._build_from_data(data_path)
        else:
            self._load_defaults()
        
        logger.info(f"✓ Gazetteer: {len(self.areas)} areas, {len(self.districts)} districts")
    
    def _build_from_data(self, path: str):
        """Build gazetteer from actual data"""
        logger.info(f"Building gazetteer from {path}...")
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Collect statistics
        area_info = defaultdict(lambda: {'districts': [], 'divisions': [], 'postals': []})
        district_info = defaultdict(lambda: {'divisions': []})
        
        for record in data:
            comp = record.get('components', {})
            area = comp.get('area', '').strip()
            district = comp.get('district', '').strip()
            division = comp.get('division', '').strip()
            postal = comp.get('postal_code', '').strip()
            
            if area:
                if district:
                    area_info[area]['districts'].append(district)
                if division:
                    area_info[area]['divisions'].append(division)
                if postal:
                    area_info[area]['postals'].append(postal)
                    self.postal_to_area[postal].add(area)
            
            if district and division:
                district_info[district]['divisions'].append(division)
        
        # Build areas (use most common district/division/postal)
        for area, info in area_info.items():
            if info['districts']:
                district = Counter(info['districts']).most_common(1)[0][0]
            else:
                district = None
            
            if info['divisions']:
                division = Counter(info['divisions']).most_common(1)[0][0]
            else:
                division = None
            
            # Get postal codes sorted by frequency (most common first)
            postal_counts = Counter(info['postals'])
            sorted_postals = [code for code, count in postal_counts.most_common()]
            
            area_data = {
                'district': district,
                'division': division,
                'postal_codes': sorted_postals,  # Most common first
                'postal_code_counts': dict(postal_counts)  # Store frequency
            }
            self.areas[area] = area_data
            
            # Technique #26: Add to Trie for fast lookup
            if self.area_trie is not None:
                self.area_trie[area.lower()] = area_data
        
        # Build districts
        for district, info in district_info.items():
            if info['divisions']:
                division = Counter(info['divisions']).most_common(1)[0][0]
            else:
                division = None
            
            self.districts[district] = {'division': division}
            if division:
                self.divisions.add(division)
        
        logger.info(f"✓ Built: {len(self.areas)} areas, {len(self.districts)} districts, "
                   f"{len(self.divisions)} divisions")
    
    def _load_defaults(self):
        """
        Dynamically load areas from offline geographic data (if available)
        No static/constant values - everything is dynamically detected
        """
        if not self.offline_geo:
            logger.warning("⚠ No data file and no offline geo - gazetteer will be empty")
            return
        
        # Dynamically extract areas from offline geo data
        logger.info("Building gazetteer dynamically from offline geographic data...")
        
        # Extract upazilas as areas (they are administrative divisions that often serve as areas)
        if hasattr(self.offline_geo, 'upazilas'):
            for upazila_name, upazila_data in self.offline_geo.upazilas.items():
                district = upazila_data.get('district', '')
                division = upazila_data.get('division', '')
                postal_codes = upazila_data.get('postal_codes', [])
                
                if upazila_name and district:
                    area_data = {
                        'district': district,
                        'division': division,
                        'postal_codes': postal_codes if postal_codes else [],
                        'postal_code_counts': {pc: 1 for pc in postal_codes} if postal_codes else {}
                    }
                    self.areas[upazila_name] = area_data
                    
                    # Add to Trie
                    if self.area_trie is not None:
                        self.area_trie[upazila_name.lower()] = area_data
                    
                    # Build district mapping
                    if district not in self.districts:
                        self.districts[district] = {'division': division}
                    if division:
                        self.divisions.add(division)
        
        # Extract unions as potential areas (smaller administrative units)
        if hasattr(self.offline_geo, 'unions'):
            for union_name, union_data in self.offline_geo.unions.items():
                district = union_data.get('district', '')
                division = union_data.get('division', '')
                postal_codes = union_data.get('postal_codes', [])
                
                # Only add if not already in areas (upazilas take precedence)
                if union_name and district and union_name not in self.areas:
                    area_data = {
                        'district': district,
                        'division': division,
                        'postal_codes': postal_codes if postal_codes else [],
                        'postal_code_counts': {pc: 1 for pc in postal_codes} if postal_codes else {}
                    }
                    self.areas[union_name] = area_data
                    
                    # Add to Trie
                    if self.area_trie is not None:
                        self.area_trie[union_name.lower()] = area_data
        
        logger.info(f"✓ Dynamically loaded {len(self.areas)} areas from offline geo data")
    
    def extract_area_from_address(self, address: str, road: Optional[str] = None, district: Optional[str] = None) -> Optional[Dict]:
        """
        Extract area name from address using gazetteer data and position-based heuristics
        
        Strategy:
        1. Position-based extraction (between road and district) - HIGHEST PRIORITY
        2. Exact match against gazetteer areas
        3. Fuzzy match against gazetteer areas
        4. Offline geo lookup (upazilas/unions/villages)
        """
        address_lower = address.lower()
        address_normalized = re.sub(r'[^\w\s]', ' ', address_lower)
        words = [w.strip() for w in address_normalized.split() if len(w.strip()) > 2]
        
        best_match = None
        best_score = 0.0
        
        # Strategy 1: Position-based extraction (word between road and district) - HIGHEST PRIORITY
        if road and district:
            road_pos = address_lower.find(road.lower())
            district_pos = address_lower.find(district.lower())
            
            if road_pos != -1 and district_pos != -1 and road_pos < district_pos:
                # Extract text between road and district
                between_text = address[road_pos + len(road):district_pos].strip()
                between_words = [w.strip().rstrip(',.') for w in between_text.split() if len(w.strip()) > 2]
                
                # Check if any word matches gazetteer area (exact or fuzzy)
                for word in between_words:
                    word_lower = word.lower()
                    for area_name in self.areas.keys():
                        area_lower = area_name.lower()
                        
                        # Exact match in position - highest confidence
                        if word_lower == area_lower:
                            score = 0.90
                            if score > best_score:
                                best_score = score
                                best_match = {
                                    'value': area_name,
                                    'confidence': score,
                                    'source': 'gazetteer_position_exact'
                                }
                        # Fuzzy match in position - high confidence
                        elif self._fuzzy_match_area(area_lower, [word_lower]):
                            score = 0.80
                            if score > best_score:
                                best_score = score
                                best_match = {
                                    'value': area_name,
                                    'confidence': score,
                                    'source': 'gazetteer_position_fuzzy'
                                }
        
        # Strategy 2: Exact match anywhere in address
        for area_name in self.areas.keys():
            area_lower = area_name.lower()
            
            if area_lower in address_lower:
                # Calculate position score (areas typically between road and district)
                area_pos = address_lower.find(area_lower)
                position_score = 0.2
                
                # Check if it's between road and district (ideal position)
                if road:
                    road_pos = address_lower.find(road.lower())
                    if road_pos != -1 and area_pos > road_pos:
                        position_score += 0.2
                
                if district:
                    district_pos = address_lower.find(district.lower())
                    if district_pos != -1 and area_pos < district_pos:
                        position_score += 0.2
                
                score = 0.6 + position_score
                if score > best_score:
                    best_score = score
                    best_match = {
                        'value': area_name,
                        'confidence': min(score, 0.95),
                        'source': 'gazetteer_exact_match'
                    }
        
        # Strategy 3: Fuzzy match anywhere in address
        for area_name in self.areas.keys():
            area_lower = area_name.lower()
            
            if self._fuzzy_match_area(area_lower, words):
                # Check position for bonus
                position_bonus = 0.0
                for word in words:
                    if self._fuzzy_match_area(area_lower, [word]):
                        word_pos = address_lower.find(word)
                        if road:
                            road_pos = address_lower.find(road.lower())
                            if road_pos != -1 and word_pos > road_pos:
                                position_bonus += 0.1
                        if district:
                            district_pos = address_lower.find(district.lower())
                            if district_pos != -1 and word_pos < district_pos:
                                position_bonus += 0.1
                        break
                
                score = 0.70 + position_bonus
                if score > best_score:
                    best_score = score
                    best_match = {
                        'value': area_name,
                        'confidence': min(score, 0.90),
                        'source': 'gazetteer_fuzzy_match'
                    }
        
        # Strategy 4: Offline geo lookup (upazilas/unions/villages)
        if not best_match and self.offline_geo:
            for word in words:
                if len(word) > 3:
                    # Check in upazilas
                    for upazila_name, upazila_data in getattr(self.offline_geo, 'upazilas', {}).items():
                        if word in upazila_name.lower() or upazila_name.lower() in word:
                            best_match = {
                                'value': upazila_name,
                                'confidence': 0.75,
                                'source': 'offline_geo_upazila'
                            }
                            break
                    if best_match:
                        break
        
        return best_match
    
    def _fuzzy_match_area(self, area_name: str, words: List[str]) -> bool:
        """Fuzzy match area name against words (handles typos/variations)"""
        area_lower = area_name.lower().strip()
        
        for word in words:
            word_lower = word.lower().strip()
            
            # Exact match
            if word_lower == area_lower:
                return True
            
            # Handle common variations (e.g., "gulisthan" -> "gulshan")
            # Replace common variations
            word_variants = [
                word_lower,
                word_lower.replace('than', 'shan'),
                word_lower.replace('stan', 'shan'),
                word_lower.replace('isthan', 'shan'),
                word_lower.replace('ishan', 'shan'),
            ]
            area_variants = [
                area_lower,
                area_lower.replace('than', 'shan'),
                area_lower.replace('stan', 'shan'),
            ]
            
            # Check if any variant matches
            for word_var in word_variants:
                for area_var in area_variants:
                    if word_var == area_var:
                        return True
            
            # Core substring match (e.g., "gulisthan" contains "gulshan" core)
            if len(word_lower) >= 4 and len(area_lower) >= 4:
                # Extract core (first 4-5 chars) - this handles "gulisthan" vs "gulshan"
                word_core = word_lower[:min(5, len(word_lower))]
                area_core = area_lower[:min(5, len(area_lower))]
                
                # If cores match, it's likely the same area
                if word_core == area_core:
                    return True
                
                # Check if core is contained (e.g., "guli" in "gulshan" or "gul" in both)
                if len(word_core) >= 3 and len(area_core) >= 3:
                    # Check if first 3-4 chars match
                    if word_core[:3] == area_core[:3]:
                        # Calculate character similarity
                        word_chars = set(word_lower)
                        area_chars = set(area_lower)
                        common_chars = len(word_chars & area_chars)
                        total_chars = len(word_chars | area_chars)
                        if total_chars > 0:
                            similarity = common_chars / total_chars
                            if similarity >= 0.70:  # 70% character overlap
                                return True
        
        return False
    
    def validate(self, components: Dict) -> Dict:
        """Validate and enhance components"""
        result = {}
        conflicts = []
        
        area = components.get('area')
        district = components.get('district')
        postal = components.get('postal_code')
        
        # Validate area (Technique #26: Use Trie for fast lookup)
        area_data = None
        if area:
            area_lower = area.lower()
            # Try Trie first (10x faster)
            if self.area_trie is not None:
                area_data = self.area_trie.get(area_lower)
            # Fallback to dict
            if area_data is None and area in self.areas:
                area_data = self.areas[area]
        
        if area_data:
            result['area'] = {
                'value': area,
                'confidence': 0.98,
                'source': 'gazetteer_validated'
            }
            
            # Auto-fill district
            if not district and area_data['district']:
                result['district'] = {
                    'value': area_data['district'],
                    'confidence': 0.95,
                    'source': 'inferred_from_area'
                }
            elif district and district != area_data['district']:
                # Conflict - trust gazetteer
                conflicts.append(f"District mismatch: expected {area_data['district']}, got {district}")
                result['district'] = {
                    'value': area_data['district'],
                    'confidence': 0.90,
                    'source': 'gazetteer_corrected'
                }
            elif district:
                result['district'] = {
                    'value': district,
                    'confidence': 0.98,
                    'source': 'gazetteer_validated'
                }
            
            # Auto-fill division
            if area_data['division']:
                result['division'] = {
                    'value': area_data['division'],
                    'confidence': 0.95,
                    'source': 'inferred_from_area'
                }
            
            # Validate postal (GAZETTEER IS AUTHORITATIVE - 98%+ confidence)
            postal_validated = False
            if postal:
                # Validate postal code format (must be 4 digits)
                is_valid_format = re.match(r'^\d{4}$', str(postal).strip())
                
                if is_valid_format and postal in area_data['postal_codes']:
                    result['postal_code'] = {
                        'value': postal,
                        'confidence': 0.99,
                        'source': 'gazetteer_validated'
                    }
                    postal_validated = True
                elif is_valid_format:
                    # Valid format but not in gazetteer - still accept it
                    result['postal_code'] = {
                        'value': postal,
                        'confidence': 0.75,
                        'source': 'unvalidated'
                    }
                    postal_validated = True
                # If invalid format (e.g., "h-107/2"), don't validate it - fall through to prediction
            
            # Predict postal code if not validated and area has postal codes
            if not postal_validated and area_data['postal_codes']:
                # Infer postal code from area (use MOST COMMON from real data)
                most_common_postal = area_data['postal_codes'][0]  # Already sorted by frequency
                total_samples = sum(area_data.get('postal_code_counts', {}).values())
                most_common_count = area_data.get('postal_code_counts', {}).get(most_common_postal, 1)
                
                # Calculate confidence based on dominance
                if len(area_data['postal_codes']) == 1:
                    confidence = 0.98  # Single postal code - very reliable
                elif total_samples > 0 and most_common_count / total_samples >= 0.8:
                    confidence = 0.98  # Dominant postal (80%+ of samples)
                elif total_samples > 0 and most_common_count / total_samples >= 0.6:
                    confidence = 0.95  # Strong majority (60%+ of samples)
                else:
                    confidence = 0.90  # Multiple postals, use most common
                
                result['postal_code'] = {
                    'value': most_common_postal,
                    'confidence': confidence,
                    'source': f'gazetteer_inferred_{most_common_count}/{total_samples}_samples'
                }
            elif self.offline_geo:
                # FALLBACK: Use offline geographic intelligence
                geo_result = self.offline_geo.predict_postal_code(
                    area=area,
                    district=district or area_data.get('district'),
                    division=area_data.get('division')
                )
                if geo_result and geo_result['confidence'] >= 0.90:
                    result['postal_code'] = {
                        'value': geo_result['postal_code'],
                        'confidence': geo_result['confidence'],
                        'source': f"offline_geo_{geo_result['source']}"
                    }
        
        # Validate district alone
        elif district and district in self.districts:
            district_data = self.districts[district]
            result['district'] = {
                'value': district,
                'confidence': 0.95,
                'source': 'gazetteer_validated'
            }
            
            if district_data['division']:
                result['division'] = {
                    'value': district_data['division'],
                    'confidence': 0.95,
                    'source': 'inferred_from_district'
                }
            
            # Try offline geo for postal code prediction
            if not postal and self.offline_geo:
                geo_result = self.offline_geo.predict_postal_code(
                    area=area,
                    district=district,
                    division=district_data.get('division')
                )
                if geo_result and geo_result['confidence'] >= 0.90:
                    result['postal_code'] = {
                        'value': geo_result['postal_code'],
                        'confidence': geo_result['confidence'],
                        'source': f"offline_geo_{geo_result['source']}"
                    }
        
        # Fallback: Try offline geo even without gazetteer match
        elif self.offline_geo and (area or district):
            geo_result = self.offline_geo.predict_postal_code(
                area=area,
                district=district
            )
            if geo_result and geo_result['confidence'] >= 0.95:
                result['postal_code'] = {
                    'value': geo_result['postal_code'],
                    'confidence': geo_result['confidence'],
                    'source': f"offline_geo_{geo_result['source']}"
                }
                if 'full_location' in geo_result:
                    result['_geo_location'] = geo_result['full_location']
        
        result['_conflicts'] = conflicts
        return result
