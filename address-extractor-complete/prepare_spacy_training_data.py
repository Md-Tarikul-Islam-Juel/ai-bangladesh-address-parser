#!/usr/bin/env python3
"""
Prepare spaCy Training Data from Existing Dataset
==================================================

Convert your existing address dataset into spaCy NER training format.
Uses your regex extractors to auto-label training data.

Author: Advanced AI Address Parser System
Date: January 2026
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Import regex extractors for auto-labeling
import sys
sys.path.insert(0, str(Path(__file__).parent))
try:
    from house_number_processor import AdvancedHouseNumberExtractor
    from road_processor import AdvancedRoadNumberExtractor
    EXTRACTORS_AVAILABLE = True
except ImportError:
    EXTRACTORS_AVAILABLE = False


def find_entity_positions(address: str, entity_value: str) -> List[Tuple[int, int]]:
    """
    Find all positions of entity_value in address
    Returns list of (start, end) tuples
    """
    if not entity_value:
        return []
    
    positions = []
    # Escape special regex characters
    escaped_value = re.escape(entity_value)
    
    # Find all occurrences
    for match in re.finditer(escaped_value, address, re.IGNORECASE):
        positions.append((match.start(), match.end()))
    
    return positions


def auto_label_address(address: str) -> Dict[str, List[Tuple[int, int, str]]]:
    """
    Automatically label an address using regex extractors
    
    Returns:
        {"entities": [(start, end, label), ...]}
    """
    entities = []
    
    if not EXTRACTORS_AVAILABLE:
        return {"entities": []}
    
    # Extract house number
    house_extractor = AdvancedHouseNumberExtractor()
    house_result = house_extractor.extract(address)
    if house_result.house_number and house_result.confidence >= 0.85:
        positions = find_entity_positions(address, house_result.house_number)
        for start, end in positions:
            entities.append((start, end, "HOUSE"))
    
    # Extract road
    road_extractor = AdvancedRoadNumberExtractor()
    road_result = road_extractor.extract(address)
    if road_result.road and road_result.confidence >= 0.85:
        positions = find_entity_positions(address, road_result.road)
        for start, end in positions:
            entities.append((start, end, "ROAD"))
    
    # Extract postal code (simple pattern)
    postal_matches = re.finditer(r'\b(\d{4})\b', address)
    for match in postal_matches:
        # Check if it's at the end (likely postal code)
        if match.end() >= len(address) * 0.7:
            entities.append((match.start(), match.end(), "POSTAL"))
    
    # Extract flat number
    flat_matches = re.finditer(r'(?:flat|apartment)[\s#:]*(?:no\.?)?[\s-]*(\w+)', address, re.IGNORECASE)
    for match in flat_matches:
        entities.append((match.start(1), match.end(1), "FLAT"))
    
    # Extract floor
    floor_matches = re.finditer(r'(\d+)(?:st|nd|rd|th)?[\s]+floor', address, re.IGNORECASE)
    for match in floor_matches:
        entities.append((match.start(1), match.end(1), "FLOOR"))
    
    # Extract block
    block_matches = re.finditer(r'block[\s]+([A-Z]|[\d]+)', address, re.IGNORECASE)
    for match in block_matches:
        entities.append((match.start(1), match.end(1), "BLOCK"))
    
    # Sort by start position and remove overlaps
    entities = sorted(entities, key=lambda x: x[0])
    non_overlapping = []
    last_end = -1
    for start, end, label in entities:
        if start >= last_end:
            non_overlapping.append((start, end, label))
            last_end = end
    
    return {"entities": non_overlapping}


def load_dataset(file_path: str) -> List[Dict]:
    """Load address dataset"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_training_data(dataset: List[Dict], 
                          min_confidence: float = 0.85,
                          max_samples: int = 1000) -> List[Tuple[str, Dict]]:
    """
    Generate spaCy training data from dataset
    
    Args:
        dataset: List of address dictionaries
        min_confidence: Minimum confidence to include sample
        max_samples: Maximum number of samples to generate
    
    Returns:
        List of (text, {"entities": [(start, end, label)]})
    """
    training_data = []
    
    print(f"Generating training data from {len(dataset)} addresses...")
    
    for i, item in enumerate(dataset[:max_samples], 1):
        if i % 100 == 0:
            print(f"  Processed {i}/{min(len(dataset), max_samples)} addresses...")
        
        address = item.get('address', '')
        if not address:
            continue
        
        # Auto-label the address
        annotations = auto_label_address(address)
        
        # Only include if we found at least 2 entities
        if len(annotations['entities']) >= 2:
            training_data.append((address, annotations))
    
    print(f"✓ Generated {len(training_data)} training samples")
    return training_data


def save_training_data(training_data: List[Tuple[str, Dict]], output_path: str):
    """Save training data to JSON"""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to JSON-serializable format
    json_data = [
        {
            "text": text,
            "entities": annotations["entities"]
        }
        for text, annotations in training_data
    ]
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Training data saved to {output_path}")


def load_training_data(file_path: str) -> List[Tuple[str, Dict]]:
    """Load training data from JSON"""
    with open(file_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    training_data = [
        (item["text"], {"entities": item["entities"]})
        for item in json_data
    ]
    
    return training_data


def print_sample_training_data(training_data: List[Tuple[str, Dict]], n: int = 5):
    """Print sample training data for inspection"""
    print("\n" + "=" * 80)
    print("SAMPLE TRAINING DATA")
    print("=" * 80 + "\n")
    
    for i, (text, annotations) in enumerate(training_data[:n], 1):
        print(f"Sample {i}:")
        print(f"  Text: {text}")
        print(f"  Entities:")
        for start, end, label in annotations["entities"]:
            entity_text = text[start:end]
            print(f"    [{start:3d}:{end:3d}] {label:8s} = '{entity_text}'")
        print()


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Prepare spaCy training data')
    parser.add_argument('--input', default='../../data/distilt5_production/train.json',
                       help='Input dataset path')
    parser.add_argument('--output', default='data/spacy_training_data.json',
                       help='Output training data path')
    parser.add_argument('--max-samples', type=int, default=1000,
                       help='Maximum training samples')
    parser.add_argument('--show-samples', type=int, default=5,
                       help='Number of samples to display')
    
    args = parser.parse_args()
    
    # Load dataset
    print(f"Loading dataset from {args.input}...")
    dataset = load_dataset(args.input)
    print(f"✓ Loaded {len(dataset)} addresses\n")
    
    # Generate training data
    training_data = generate_training_data(
        dataset, 
        max_samples=args.max_samples
    )
    
    # Show samples
    if args.show_samples > 0:
        print_sample_training_data(training_data, args.show_samples)
    
    # Save training data
    save_training_data(training_data, args.output)
    
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("\n1. Review the training data:")
    print(f"   less {args.output}")
    print("\n2. Train spaCy model:")
    print("   python train_spacy_model.py")
    print("\n3. Use hybrid extractor:")
    print("   python hybrid_extractor.py")
    print()


if __name__ == "__main__":
    main()
