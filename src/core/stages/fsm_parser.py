"""Stage 3: FSM Parser"""

import re
from typing import Dict


class SimpleFSMParser:
    """
    Simplified FSM parser that extracts components
    Uses regex patterns for tokenization
    """
    
    def parse(self, address: str) -> Dict:
        """Parse address and extract components"""
        components = {
            'house_number': None,
            'road': None,
            'area': None,
            'district': None,
            'postal_code': None,
            'flat_number': None,
            'floor_number': None,
            'block_number': None,
        }
        
        # House patterns
        house_patterns = [
            r'House\s+No\s+(\d+[A-Za-z]?)',
            r'House\s+No\s+(\d+/[A-Za-z])',
            r'House\s+(\d+)',
            r'H\s+(\d+)',
        ]
        for pattern in house_patterns:
            match = re.search(pattern, address, re.IGNORECASE)
            if match and not components['house_number']:
                components['house_number'] = match.group(1)
                break
        
        # Road patterns
        road_patterns = [
            r'Road\s+No\s+(\d+[A-Za-z]?)',
            r'Road\s+No\s+(\d+/[A-Za-z]?)',
            r'Road\s+(\d+)',
            r'R\s+(\d+)',
        ]
        for pattern in road_patterns:
            match = re.search(pattern, address, re.IGNORECASE)
            if match and not components['road']:
                components['road'] = match.group(1)
                break
        
        # Postal code (4 digits at end typically)
        postal_match = re.search(r'\b(\d{4})\b', address)
        if postal_match:
            postal = postal_match.group(1)
            # Check if near end of address
            if postal_match.end() > len(address) * 0.5:
                components['postal_code'] = postal
        
        # Flat/Floor/Block
        flat_match = re.search(r'Flat\s+(\w+)', address, re.IGNORECASE)
        if flat_match:
            components['flat_number'] = flat_match.group(1)
        
        floor_match = re.search(r'Floor\s+(\d+)', address, re.IGNORECASE)
        if floor_match:
            components['floor_number'] = floor_match.group(1)
        
        block_match = re.search(r'Block\s+([A-Z0-9]+)', address, re.IGNORECASE)
        if block_match:
            components['block_number'] = block_match.group(1)
        
        confidence = 0.75 if any(v for v in components.values()) else 0.0
        
        return {'components': components, 'confidence': confidence}
