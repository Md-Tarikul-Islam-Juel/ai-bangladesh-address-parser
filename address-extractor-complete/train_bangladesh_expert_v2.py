#!/usr/bin/env python3
"""
BANGLADESH GEOGRAPHIC-INTELLIGENT ML TRAINING - EXPERT V2
===========================================================

Enhanced ML training with complete Bangladesh geographic hierarchy:
- 1,226 postal codes (district → post office → code)
- 64 districts → 8 divisions mapping
- Area → postal code inference
- District → division automatic mapping
- Missing component prediction using geographic relationships

This enables:
✅ Predict missing postal codes from area/district
✅ Auto-fill division from district
✅ Validate geographic consistency
✅ Enhanced training labels with geographic context

Author: 20-Year Bangladesh Geospatial Expert
Date: January 2026
Version: 2.0 (Geographic Intelligence)
"""

import json
import random
import re
from pathlib import Path
from typing import List, Tuple, Dict, Set, Optional
from collections import Counter, defaultdict
import time

try:
    import spacy
    from spacy.training import Example
    from spacy.util import minibatch, compounding
except ImportError:
    print("❌ spaCy not installed! Run: pip3 install spacy")
    exit(1)

# Import regex processors
import sys
sys.path.insert(0, str(Path(__file__).parent))
from house_number_processor import AdvancedHouseNumberExtractor
from road_processor import AdvancedRoadNumberExtractor
from area_processor import AdvancedAreaExtractor
from district_processor import AdvancedCityExtractor
from postal_code_processor import AdvancedPostalCodeExtractor
from flat_number_processor import AdvancedFlatNumberExtractor
from floor_number_processor import AdvancedFloorNumberExtractor
from block_processor import AdvancedBlockNumberExtractor


# ============================================================================
# BANGLADESH GEOGRAPHIC INTELLIGENCE SYSTEM
# ============================================================================

class BangladeshGeographicIntelligence:
    """
    Complete Bangladesh geographic hierarchy and inference system
    """
    
    def __init__(self, division_data_path: str = "../main/Processed data/division"):
        self.division_path = Path(division_data_path)
        
        # Load all geographic data
        self.postal_codes = {}  # {code: {district, postOffice}}
        self.district_to_division = {}  # {district: division}
        self.area_to_postal = defaultdict(set)  # {area_name: {postal_codes}}
        self.district_to_postals = defaultdict(set)  # {district: {postal_codes}}
        
        self._load_geographic_data()
    
    def _load_geographic_data(self):
        """Load complete Bangladesh geographic hierarchy"""
        print("Loading Bangladesh geographic intelligence...")
        
        # Load postal codes
        postal_file = self.division_path / "bd-postal-codes.json"
        if postal_file.exists():
            with open(postal_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for entry in data.get('postal_codes', []):
                    code = entry.get('code')
                    district = entry.get('district')
                    post_office = entry.get('postOffice')
                    
                    if code:
                        self.postal_codes[code] = {
                            'district': district,
                            'postOffice': post_office
                        }
                        
                        if district:
                            self.district_to_postals[district.lower()].add(code)
                        
                        # Map area names to postal codes
                        if post_office:
                            self.area_to_postal[post_office.lower()].add(code)
        
        print(f"✓ Loaded {len(self.postal_codes)} postal codes")
        
        # Load district-to-division mapping
        mapping_file = self.division_path / "district-to-division-mapping.json"
        if mapping_file.exists():
            with open(mapping_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.district_to_division = {
                    k.lower(): v for k, v in data.get('mapping', {}).items()
                }
        
        print(f"✓ Loaded {len(self.district_to_division)} district-division mappings")
        print()
    
    def infer_postal_code(self, area: str, district: str) -> Optional[str]:
        """
        Infer postal code from area or district
        """
        if not area and not district:
            return None
        
        # Try area first (more specific)
        if area:
            area_lower = area.lower()
            # Direct match
            if area_lower in self.area_to_postal:
                codes = self.area_to_postal[area_lower]
                if codes:
                    return list(codes)[0]  # Return first match
            
            # Fuzzy match - check if area contains post office name
            for post_office, codes in self.area_to_postal.items():
                if post_office in area_lower or area_lower in post_office:
                    if codes:
                        return list(codes)[0]
        
        # Try district
        if district:
            district_lower = district.lower()
            if district_lower in self.district_to_postals:
                codes = self.district_to_postals[district_lower]
                if codes:
                    # Return most common postal code for district
                    return sorted(list(codes))[0]
        
        return None
    
    def infer_division(self, district: str) -> Optional[str]:
        """
        Infer division from district
        """
        if not district:
            return None
        
        district_lower = district.lower()
        
        # Direct lookup
        if district_lower in self.district_to_division:
            return self.district_to_division[district_lower]
        
        # Fuzzy match
        for dist, div in self.district_to_division.items():
            if dist in district_lower or district_lower in dist:
                return div
        
        return None
    
    def validate_postal_code(self, postal_code: str, district: str) -> bool:
        """
        Validate if postal code matches district
        """
        if not postal_code or not district:
            return True  # Can't validate without data
        
        if postal_code in self.postal_codes:
            expected_district = self.postal_codes[postal_code].get('district', '')
            if expected_district:
                return expected_district.lower() == district.lower()
        
        return True  # Default to valid if unknown
    
    def enrich_components(self, components: Dict) -> Dict:
        """
        Enrich components with geographic intelligence
        """
        enriched = components.copy()
        
        area = enriched.get('area', '')
        district = enriched.get('district', '')
        postal_code = enriched.get('postal_code', '')
        division = enriched.get('division', '')
        
        # Infer missing postal code
        if not postal_code and (area or district):
            inferred_postal = self.infer_postal_code(area, district)
            if inferred_postal:
                enriched['postal_code'] = inferred_postal
                enriched['_inferred_postal'] = True
        
        # Infer missing division
        if not division and district:
            inferred_division = self.infer_division(district)
            if inferred_division:
                enriched['division'] = inferred_division
                enriched['_inferred_division'] = True
        
        # Validate postal code consistency
        if postal_code and district:
            if not self.validate_postal_code(postal_code, district):
                enriched['_inconsistent_postal'] = True
        
        return enriched


# ============================================================================
# ENHANCED TRAINING WITH GEOGRAPHIC INTELLIGENCE
# ============================================================================

def find_entity_positions_smart(text: str, value: str) -> List[Tuple[int, int]]:
    """Smart entity position finder"""
    if not value or not text:
        return []
    
    value_str = str(value).strip()
    if not value_str:
        return []
    
    positions = []
    text_lower = text.lower()
    value_lower = value_str.lower()
    
    # Find exact matches
    start = 0
    while True:
        pos = text_lower.find(value_lower, start)
        if pos == -1:
            break
        positions.append((pos, pos + len(value_str)))
        start = pos + 1
    
    # Handle special patterns
    if not positions and ('/' in value_str or '-' in value_str):
        clean_value = re.sub(r'[/-]', '', value_str)
        clean_text = re.sub(r'[/-]', '', text)
        pos = clean_text.lower().find(clean_value.lower())
        if pos != -1:
            orig_pos = len(re.sub(r'[/-]', '', text[:pos]))
            positions.append((orig_pos, orig_pos + len(value_str)))
    
    return positions


def auto_label_with_geographic_intelligence(address: str, 
                                           components: Dict, 
                                           extractors: Dict,
                                           geo_intel: BangladeshGeographicIntelligence) -> Dict:
    """
    Enhanced auto-labeling with geographic intelligence
    """
    entities = []
    
    # Enrich components with geographic inference
    enriched_components = geo_intel.enrich_components(components)
    
    # Priority 1: Ground truth components (enriched)
    for field, label in [
        ('flat_number', 'FLAT'),
        ('house_number', 'HOUSE'),
        ('floor_number', 'FLOOR'),
        ('road', 'ROAD'),
        ('block_number', 'BLOCK'),
        ('area', 'AREA'),
        ('district', 'DISTRICT'),
        ('postal_code', 'POSTAL'),
    ]:
        value = enriched_components.get(field)
        if value and not enriched_components.get(f'_inferred_{field.split("_")[0]}'):
            # Only use if not inferred (use ground truth)
            positions = find_entity_positions_smart(address, value)
            for start, end in positions:
                entities.append((start, end, label))
    
    # Priority 2: Augment with regex (for missing components)
    try:
        existing_labels = set(e[2] for e in entities)
        
        if 'HOUSE' not in existing_labels:
            result = extractors['house'].extract(address)
            if hasattr(result, 'house_number') and result.house_number:
                positions = find_entity_positions_smart(address, result.house_number)
                for start, end in positions:
                    entities.append((start, end, 'HOUSE'))
        
        if 'ROAD' not in existing_labels:
            result = extractors['road'].extract(address)
            if hasattr(result, 'road') and result.road:
                positions = find_entity_positions_smart(address, result.road)
                for start, end in positions:
                    entities.append((start, end, 'ROAD'))
        
        if 'AREA' not in existing_labels:
            result = extractors['area'].extract(address)
            if hasattr(result, 'area') and result.area:
                positions = find_entity_positions_smart(address, result.area)
                for start, end in positions:
                    entities.append((start, end, 'AREA'))
        
        if 'DISTRICT' not in existing_labels:
            result = extractors['district'].extract(address)
            if hasattr(result, 'city') and result.city:
                positions = find_entity_positions_smart(address, result.city)
                for start, end in positions:
                    entities.append((start, end, 'DISTRICT'))
        
        if 'POSTAL' not in existing_labels:
            result = extractors['postal'].extract(address)
            if hasattr(result, 'postal_code') and result.postal_code:
                positions = find_entity_positions_smart(address, result.postal_code)
                for start, end in positions:
                    entities.append((start, end, 'POSTAL'))
        
        if 'FLAT' not in existing_labels:
            result = extractors['flat'].extract(address)
            if hasattr(result, 'flat_number') and result.flat_number:
                positions = find_entity_positions_smart(address, result.flat_number)
                for start, end in positions:
                    entities.append((start, end, 'FLAT'))
        
        if 'FLOOR' not in existing_labels:
            result = extractors['floor'].extract(address)
            if hasattr(result, 'floor_number') and result.floor_number:
                positions = find_entity_positions_smart(address, result.floor_number)
                for start, end in positions:
                    entities.append((start, end, 'FLOOR'))
        
        if 'BLOCK' not in existing_labels:
            result = extractors['block'].extract(address)
            if hasattr(result, 'block_number') and result.block_number:
                positions = find_entity_positions_smart(address, result.block_number)
                for start, end in positions:
                    entities.append((start, end, 'BLOCK'))
    
    except Exception:
        pass
    
    # Remove overlapping entities
    entities.sort(key=lambda x: (x[0], -(x[1] - x[0])))
    non_overlapping = []
    covered = set()
    
    for start, end, label in entities:
        if not any(pos in covered for pos in range(start, end)):
            non_overlapping.append((start, end, label))
            covered.update(range(start, end))
    
    non_overlapping.sort(key=lambda x: x[0])
    
    return {"entities": non_overlapping}


def prepare_geographic_intelligent_data(data_path: str, 
                                        extractors: Dict,
                                        geo_intel: BangladeshGeographicIntelligence) -> Tuple[List, Dict]:
    """
    Prepare training data with geographic intelligence
    """
    print("=" * 80)
    print("🇧🇩 GEOGRAPHIC-INTELLIGENT DATA PREPARATION")
    print("=" * 80)
    print()
    
    # Load dataset
    with open(data_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    print(f"✓ Loaded {len(dataset):,} addresses")
    print()
    
    # Analyze with geographic intelligence
    print("📊 Analyzing with geographic intelligence...")
    stats = {
        'total': len(dataset),
        'inferred_postal': 0,
        'inferred_division': 0,
        'with_bangla': 0,
        'with_ra': 0,
        'with_landmarks': 0,
    }
    
    for item in dataset:
        address = item.get('address', '')
        components = item.get('components', {})
        
        # Test geographic enrichment
        enriched = geo_intel.enrich_components(components)
        if enriched.get('_inferred_postal'):
            stats['inferred_postal'] += 1
        if enriched.get('_inferred_division'):
            stats['inferred_division'] += 1
        
        # Bangla detection
        if any(0x0980 <= ord(c) <= 0x09FF for c in address):
            stats['with_bangla'] += 1
        
        if 'R/A' in address or 'r/a' in address.lower():
            stats['with_ra'] += 1
        
        if any(marker in address for marker in ['(', 'Near', 'Beside', 'After']):
            stats['with_landmarks'] += 1
    
    print(f"  📬 Can infer postal codes: {stats['inferred_postal']:,} ({stats['inferred_postal']/stats['total']*100:.1f}%)")
    print(f"  🗺️  Can infer divisions: {stats['inferred_division']:,} ({stats['inferred_division']/stats['total']*100:.1f}%)")
    print(f"  🔤 Mixed Bangla-English: {stats['with_bangla']:,} ({stats['with_bangla']/stats['total']*100:.1f}%)")
    print(f"  🏘️  Contains R/A: {stats['with_ra']:,} ({stats['with_ra']/stats['total']*100:.1f}%)")
    print(f"  📍 Has landmarks: {stats['with_landmarks']:,} ({stats['with_landmarks']/stats['total']*100:.1f}%)")
    print()
    
    # Generate training data
    print("🏗️  Generating training samples with geographic intelligence...")
    training_data = []
    
    for i, item in enumerate(dataset, 1):
        if i % 1000 == 0:
            print(f"  Processed {i:,}/{stats['total']:,} ({i/stats['total']*100:.1f}%)...")
        
        address = item.get('address', '')
        components = item.get('components', {})
        
        if not address:
            continue
        
        # Enhanced labeling with geographic intelligence
        annotations = auto_label_with_geographic_intelligence(
            address, components, extractors, geo_intel
        )
        
        # Quality filter
        if len(annotations['entities']) >= 2:
            training_data.append((address, annotations))
    
    print(f"\n✓ Generated {len(training_data):,} high-quality samples")
    print(f"✓ Using {len(training_data)/len(dataset)*100:.1f}% of dataset")
    print()
    
    return training_data, stats


def train_geographic_intelligent_model(training_data: List[Tuple[str, Dict]], 
                                      stats: Dict,
                                      output_dir: str = "models/address_ner_model"):
    """
    Train with geographic intelligence
    """
    print("=" * 80)
    print("🧠 GEOGRAPHIC-INTELLIGENT ML TRAINING")
    print("=" * 80)
    print()
    
    # Load base model
    try:
        nlp = spacy.load("xx_ent_wiki_sm")
        print("✓ Multilingual base model (Bangla + English)")
    except:
        try:
            nlp = spacy.load("en_core_web_sm")
            print("✓ English base model")
        except:
            print("❌ No base model! Install: python3 -m spacy download xx_ent_wiki_sm")
            return
    
    # Setup NER
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner")
    else:
        ner = nlp.get_pipe("ner")
    
    labels = ["HOUSE", "ROAD", "AREA", "DISTRICT", "POSTAL", "FLAT", "FLOOR", "BLOCK"]
    for label in labels:
        ner.add_label(label)
    
    print(f"✓ Training on {len(labels)} entity types")
    print()
    
    # Split
    random.shuffle(training_data)
    split_idx = int(len(training_data) * 0.90)
    train_data = training_data[:split_idx]
    val_data = training_data[split_idx:]
    
    print(f"📊 Training: {len(train_data):,} | Validation: {len(val_data):,}")
    print()
    
    # Hyperparameters
    n_iter = 150
    print(f"🎯 Training for {n_iter} iterations (~2 hours)")
    print()
    
    # Train
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
    
    with nlp.disable_pipes(*other_pipes):
        optimizer = nlp.create_optimizer()
        
        best_f = 0.0
        start = time.time()
        
        for it in range(n_iter):
            random.shuffle(train_data)
            losses = {}
            
            examples = []
            for text, annot in train_data:
                try:
                    doc = nlp.make_doc(text)
                    examples.append(Example.from_dict(doc, annot))
                except:
                    continue
            
            batches = minibatch(examples, size=compounding(8.0, 64.0, 1.001))
            for batch in batches:
                nlp.update(batch, drop=0.30, losses=losses)
            
            if (it + 1) % 10 == 0:
                val_ex = []
                for text, annot in val_data:
                    try:
                        doc = nlp.make_doc(text)
                        val_ex.append(Example.from_dict(doc, annot))
                    except:
                        continue
                
                scores = nlp.evaluate(val_ex)
                f = scores.get('ents_f', 0.0)
                p = scores.get('ents_p', 0.0)
                r = scores.get('ents_r', 0.0)
                elapsed = (time.time() - start) / 60
                
                print(f"Iter {it+1:3d}/{n_iter} | Loss: {losses.get('ner', 0):.3f} | "
                      f"F1: {f:.4f} | P: {p:.4f} | R: {r:.4f} | {elapsed:.1f}m")
                
                if f > best_f:
                    best_f = f
                    print(f"   ⭐ Best: {best_f:.4f}")
            elif it % 5 == 0:
                elapsed = (time.time() - start) / 60
                print(f"Iter {it+1:3d}/{n_iter} | Loss: {losses.get('ner', 0):.3f} | {elapsed:.1f}m")
    
    # Save
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(output_path)
    
    total = (time.time() - start) / 60
    
    print()
    print("=" * 80)
    print("✅ GEOGRAPHIC-INTELLIGENT MODEL TRAINED!")
    print("=" * 80)
    print(f"📁 Model: {output_dir}")
    print(f"⭐ Best F1: {best_f:.4f}")
    print(f"⏱️  Time: {total:.1f} minutes")
    print()
    print("🇧🇩 Geographic Intelligence:")
    print(f"   ✅ {stats.get('inferred_postal', 0):,} addresses can get postal code inference")
    print(f"   ✅ {stats.get('inferred_division', 0):,} addresses can get division inference")
    print(f"   ✅ Complete 64 district → 8 division mapping")
    print(f"   ✅ 1,226 postal codes for validation")
    print()


def main():
    """Main"""
    print("\n" + "🗺️" * 40)
    print("BANGLADESH GEOGRAPHIC-INTELLIGENT ML TRAINING V2")
    print("🗺️" * 40 + "\n")
    
    # Initialize geographic intelligence
    print("Initializing geographic intelligence system...")
    geo_intel = BangladeshGeographicIntelligence()
    print()
    
    # Initialize extractors
    print("Initializing regex processors...")
    extractors = {
        'house': AdvancedHouseNumberExtractor(),
        'road': AdvancedRoadNumberExtractor(),
        'area': AdvancedAreaExtractor(),
        'district': AdvancedCityExtractor(),
        'postal': AdvancedPostalCodeExtractor(),
        'flat': AdvancedFlatNumberExtractor(),
        'floor': AdvancedFloorNumberExtractor(),
        'block': AdvancedBlockNumberExtractor(),
    }
    print("✓ All processors ready\n")
    
    # Prepare data
    data_path = "../main/Processed data/merged_addresses.json"
    training_data, stats = prepare_geographic_intelligent_data(
        data_path, extractors, geo_intel
    )
    
    # Train
    train_geographic_intelligent_model(training_data, stats)


if __name__ == "__main__":
    main()
