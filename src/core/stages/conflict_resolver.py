"""Stage 8: Evidence-Weighted Conflict Resolution"""

import re
from collections import defaultdict
from typing import Dict, List


class ConflictResolver:
    """Evidence-weighted conflict resolution"""
    
    def __init__(self):
        # Source reliability weights (calibrated)
        self.weights = {
            'regex': 1.00,               # Your patterns - highest precision
            'gazetteer_validated': 0.95,  # Confirmed existence
            'fsm': 0.90,                 # Deterministic
            'spacy_ner': 0.85,           # ML-based pattern learning
            'gazetteer_corrected': 0.85,  # Corrected conflict
            'inferred_from_area': 0.80,   # Logical inference
            'inferred_from_district': 0.80,
            'unvalidated': 0.60,         # Not confirmed
        }
    
    def resolve(self, evidence_map: Dict[str, List[Dict]]) -> Dict:
        """Resolve conflicts using weighted voting"""
        resolved = {}
        
        for component, evidences in evidence_map.items():
            if not evidences:
                resolved[component] = None
                continue
            
            # Normalize evidences - ensure all are dictionaries
            normalized_evidences = []
            for e in evidences:
                if isinstance(e, dict):
                    # Validate postal codes - must be 4 digits
                    if component == 'postal_code':
                        value = str(e.get('value', '')).strip()
                        if not re.match(r'^\d{4}$', value):
                            # Invalid postal code format - skip it
                            continue
                    normalized_evidences.append(e)
                elif isinstance(e, str):
                    # Validate postal codes - must be 4 digits
                    if component == 'postal_code':
                        if not re.match(r'^\d{4}$', str(e).strip()):
                            # Invalid postal code format - skip it
                            continue
                    # Convert string to dict format
                    normalized_evidences.append({
                        'value': e,
                        'confidence': 0.80,
                        'source': 'unknown'
                    })
                else:
                    continue  # Skip invalid entries
            
            if not normalized_evidences:
                resolved[component] = None
                continue
            
            # Get unique values
            unique_values = set(e['value'] for e in normalized_evidences if e.get('value'))
            
            if len(unique_values) == 0:
                resolved[component] = None
            elif len(unique_values) == 1:
                # All agree - high confidence
                value = list(unique_values)[0]
                avg_conf = sum(e['confidence'] for e in normalized_evidences) / len(normalized_evidences)
                best_source = max(normalized_evidences, key=lambda e: e['confidence'])['source']
                
                resolved[component] = {
                    'value': value,
                    'confidence': min(avg_conf * 1.05, 0.99),  # Consensus bonus
                    'source': best_source,
                    'evidence_count': len(normalized_evidences)
                }
            else:
                # Disagreement - weighted voting
                scores = defaultdict(float)
                for evidence in normalized_evidences:
                    value = evidence['value']
                    weight = self.weights.get(evidence['source'], 0.5)
                    scores[value] += evidence['confidence'] * weight
                
                best_value = max(scores.items(), key=lambda x: x[1])[0]
                best_evidence = max([e for e in normalized_evidences if e['value'] == best_value],
                                  key=lambda e: e['confidence'])
                
                resolved[component] = {
                    'value': best_value,
                    'confidence': best_evidence['confidence'] * 0.90,  # Conflict penalty
                    'source': best_evidence['source'],
                    'evidence_count': len(normalized_evidences),
                    'conflict': True
                }
        
        return resolved
