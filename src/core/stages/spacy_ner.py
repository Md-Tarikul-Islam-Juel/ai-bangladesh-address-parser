"""Stage 5: spaCy NER (ML-Based Extraction)"""

import logging
from pathlib import Path
from typing import Dict, Optional

from ..utils.constants import SPACY_AVAILABLE

logger = logging.getLogger(__name__)

if SPACY_AVAILABLE:
    import spacy


class SpacyNERExtractor:
    """
    ML-based Named Entity Recognition using spaCy
    
    NOTE: This extractor relies on proper training data.
    For best results, ensure training data has correct entity spans
    for house/road patterns (e.g., "h-107/2, r-7" should have
    separate HOUSE and ROAD entities, not a single ROAD entity).
    
    Use training/enhance_training_data.py to improve training data.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.nlp = None
        self.enabled = False
        
        if not SPACY_AVAILABLE:
            return
        
        # Try to load trained model
        if model_path is None:
            # Go up 2 levels: src/core/stages/ -> src/core/ -> src/ -> root/ -> models/production/
            model_path = str(Path(__file__).parent.parent.parent.parent / "models" / "production" / "address_ner_model")
        
        if Path(model_path).exists():
            try:
                self.nlp = spacy.load(model_path)
                self.enabled = True
                logger.info(f"✓ Loaded trained spaCy NER model from {model_path}")
            except Exception as e:
                logger.warning(f"⚠ Could not load spaCy model: {e}")
        else:
            logger.info("ℹ spaCy NER model not found (optional). Train with: python3 training/train.py")
    
    def extract(self, address: str) -> Dict:
        """
        Extract components using spaCy NER
        
        This method relies on the model being trained with proper entity spans.
        No post-processing validation - the model should be trained correctly.
        
        To improve accuracy on house/road patterns:
        1. Run: python3 training/enhance_training_data.py
        2. Retrain: python3 training/train.py --mode spacy
        """
        results = {}
        
        if not self.enabled or not self.nlp:
            return results
        
        try:
            doc = self.nlp(address)
            
            # Map spaCy entity labels to our component names
            label_mapping = {
                'HOUSE': 'house_number',
                'house': 'house_number',
                'house_number': 'house_number',
                'ROAD': 'road',
                'road': 'road',
                'road_number': 'road',
                'AREA': 'area',
                'area': 'area',
                'DISTRICT': 'district',
                'district': 'district',
                'POSTAL': 'postal_code',
                'postal_code': 'postal_code',
                'FLAT': 'flat_number',
                'flat': 'flat_number',
                'FLOOR': 'floor_number',
                'floor': 'floor_number',
                'BLOCK': 'block_number',
                'block': 'block_number',
            }
            
            for ent in doc.ents:
                label = ent.label_
                component = label_mapping.get(label)
                
                if component and ent.text.strip():
                    value = ent.text.strip()
                    
                    # Only add if not already present (take first occurrence)
                    if component not in results:
                        results[component] = {
                            'value': value,
                            'confidence': 0.85,  # spaCy confidence
                            'source': 'spacy_ner'
                        }
        
        except Exception as e:
            logger.warning(f"spaCy NER extraction failed: {e}")
        
        return results
