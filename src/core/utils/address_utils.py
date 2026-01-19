"""Advanced Address Utilities - Validation, Formatting, Comparison, etc."""

import re
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher
from collections import Counter


def validate_address(components: Dict, required: Optional[List[str]] = None) -> Dict:
    """
    Validate address completeness and component validity
    
    Args:
        components: Extracted address components
        required: List of required components (default: ['district', 'area'])
    
    Returns:
        {
            'is_valid': bool,
            'completeness': float (0.0-1.0),
            'missing': List[str],
            'invalid': List[str],
            'score': float
        }
    """
    if required is None:
        required = ['district', 'area']  # Minimum required for valid address
    
    missing = []
    invalid = []
    present = []
    
    # Check required components
    for comp in required:
        value = components.get(comp, '').strip()
        if not value:
            missing.append(comp)
        else:
            present.append(comp)
    
    # Validate component formats
    if components.get('postal_code'):
        postal = str(components['postal_code']).strip()
        if not re.match(r'^\d{4}$', postal):
            invalid.append('postal_code')
    
    # Calculate completeness
    all_components = ['house_number', 'road', 'area', 'district', 'division', 
                     'postal_code', 'flat_number', 'floor_number', 'block_number']
    total_components = len([c for c in all_components if components.get(c, '').strip()])
    completeness = total_components / len(all_components)
    
    # Calculate validity score
    required_score = len(present) / len(required) if required else 1.0
    completeness_score = completeness
    validity_score = (required_score * 0.7) + (completeness_score * 0.3)
    
    is_valid = len(missing) == 0 and len(invalid) == 0
    
    return {
        'is_valid': is_valid,
        'completeness': round(completeness, 3),
        'missing': missing,
        'invalid': invalid,
        'score': round(validity_score, 3)
    }


def format_address(components: Dict, style: str = 'full', 
                   separator: str = ', ', include_postal: bool = True) -> str:
    """
    Format address components into a standardized string
    
    Args:
        components: Extracted address components
        style: 'full' | 'short' | 'postal' | 'minimal'
        separator: Separator between components
        include_postal: Whether to include postal code
    
    Returns:
        Formatted address string
    """
    parts = []
    
    if style == 'full':
        # Full format: House, Road, Area, District, Division, Postal
        if components.get('house_number'):
            parts.append(f"House {components['house_number']}")
        if components.get('road'):
            parts.append(f"Road {components['road']}")
        if components.get('flat_number'):
            parts.append(f"Flat {components['flat_number']}")
        if components.get('floor_number'):
            parts.append(f"Floor {components['floor_number']}")
        if components.get('block_number'):
            parts.append(f"Block {components['block_number']}")
        if components.get('area'):
            parts.append(components['area'])
        if components.get('district'):
            parts.append(components['district'])
        if components.get('division') and components.get('division') != components.get('district'):
            parts.append(components['division'])
        if include_postal and components.get('postal_code'):
            parts.append(f"{components['postal_code']}")
    
    elif style == 'short':
        # Short format: Area, District, Postal
        if components.get('area'):
            parts.append(components['area'])
        if components.get('district'):
            parts.append(components['district'])
        if include_postal and components.get('postal_code'):
            parts.append(components['postal_code'])
    
    elif style == 'postal':
        # Postal format: District-Postal
        if components.get('district'):
            postal = f"-{components['postal_code']}" if include_postal and components.get('postal_code') else ""
            parts.append(f"{components['district']}{postal}")
    
    elif style == 'minimal':
        # Minimal: Area, District
        if components.get('area'):
            parts.append(components['area'])
        if components.get('district'):
            parts.append(components['district'])
    
    return separator.join(parts)


def compare_addresses(components1: Dict, components2: Dict) -> Dict:
    """
    Compare two addresses and calculate similarity
    
    Args:
        components1: First address components
        components2: Second address components
    
    Returns:
        {
            'similarity': float (0.0-1.0),
            'match': bool,
            'differences': List[str],
            'common': List[str],
            'score': float
        }
    """
    all_components = ['house_number', 'road', 'area', 'district', 'division', 
                     'postal_code', 'flat_number', 'floor_number', 'block_number']
    
    similarities = {}
    differences = []
    common = []
    
    for comp in all_components:
        val1 = str(components1.get(comp, '')).strip().lower()
        val2 = str(components2.get(comp, '')).strip().lower()
        
        if val1 and val2:
            # Calculate string similarity
            similarity = SequenceMatcher(None, val1, val2).ratio()
            similarities[comp] = similarity
            
            if similarity >= 0.9:
                common.append(comp)
            else:
                differences.append(comp)
        elif val1 or val2:
            differences.append(comp)
    
    # Calculate overall similarity
    if similarities:
        avg_similarity = sum(similarities.values()) / len(similarities)
    else:
        avg_similarity = 0.0
    
    # Weighted score (postal_code and district are more important)
    weights = {
        'postal_code': 0.3,
        'district': 0.25,
        'area': 0.2,
        'house_number': 0.1,
        'road': 0.1,
        'division': 0.05
    }
    
    weighted_score = 0.0
    total_weight = 0.0
    for comp, weight in weights.items():
        if comp in similarities:
            weighted_score += similarities[comp] * weight
            total_weight += weight
    
    final_score = weighted_score / total_weight if total_weight > 0 else avg_similarity
    
    # Consider addresses matching if score > 0.85
    match = final_score >= 0.85
    
    return {
        'similarity': round(avg_similarity, 3),
        'match': match,
        'differences': differences,
        'common': common,
        'score': round(final_score, 3),
        'component_similarities': similarities
    }


def suggest_addresses(query: str, gazetteer, limit: int = 5) -> List[Dict]:
    """
    Suggest addresses based on query (area/district name)
    
    Args:
        query: Search query (area or district name)
        gazetteer: Gazetteer instance
        limit: Maximum number of suggestions
    
    Returns:
        List of suggested addresses with confidence scores
    """
    query_lower = query.lower().strip()
    suggestions = []
    
    # Search in areas
    if hasattr(gazetteer, 'areas') and gazetteer.areas:
        for area_name, area_data in gazetteer.areas.items():
            area_lower = area_name.lower()
            if query_lower in area_lower or area_lower in query_lower:
                # Calculate similarity
                similarity = SequenceMatcher(None, query_lower, area_lower).ratio()
                
                suggestion = {
                    'area': area_name,
                    'district': area_data.get('district'),
                    'division': area_data.get('division'),
                    'postal_code': area_data.get('postal_codes', [None])[0] if area_data.get('postal_codes') else None,
                    'confidence': round(similarity, 3),
                    'source': 'gazetteer'
                }
                suggestions.append(suggestion)
    
    # Search in districts
    if hasattr(gazetteer, 'districts') and gazetteer.districts:
        for district_name, district_data in gazetteer.districts.items():
            district_lower = district_name.lower()
            if query_lower in district_lower or district_lower in query_lower:
                similarity = SequenceMatcher(None, query_lower, district_lower).ratio()
                
                suggestion = {
                    'district': district_name,
                    'division': district_data.get('division'),
                    'confidence': round(similarity, 3),
                    'source': 'gazetteer'
                }
                suggestions.append(suggestion)
    
    # Sort by confidence and return top results
    suggestions.sort(key=lambda x: x['confidence'], reverse=True)
    return suggestions[:limit]


def get_statistics(addresses: List[Dict]) -> Dict:
    """
    Calculate statistics for a list of addresses
    
    Args:
        addresses: List of extracted address results
    
    Returns:
        Statistics dictionary
    """
    if not addresses:
        return {
            'total': 0,
            'completeness': 0.0,
            'distribution': {},
            'common_areas': [],
            'missing_components': {}
        }
    
    total = len(addresses)
    completeness_scores = []
    districts = Counter()
    divisions = Counter()
    areas = Counter()
    missing_components = Counter()
    
    all_components = ['house_number', 'road', 'area', 'district', 'division', 
                     'postal_code', 'flat_number', 'floor_number', 'block_number']
    
    for addr in addresses:
        components = addr.get('components', {})
        
        # Calculate completeness for this address
        present = sum(1 for c in all_components if components.get(c, '').strip())
        completeness_scores.append(present / len(all_components))
        
        # Track distributions
        if components.get('district'):
            districts[components['district']] += 1
        if components.get('division'):
            divisions[components['division']] += 1
        if components.get('area'):
            areas[components['area']] += 1
        
        # Track missing components
        for comp in all_components:
            if not components.get(comp, '').strip():
                missing_components[comp] += 1
    
    avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0.0
    
    return {
        'total': total,
        'completeness': round(avg_completeness, 3),
        'distribution': {
            'districts': dict(districts.most_common(10)),
            'divisions': dict(divisions.most_common(8)),
            'areas': dict(areas.most_common(20))
        },
        'common_areas': [{'area': area, 'count': count} for area, count in areas.most_common(10)],
        'missing_components': dict(missing_components),
        'average_confidence': round(sum(addr.get('overall_confidence', 0) for addr in addresses) / total, 3) if total > 0 else 0.0
    }
