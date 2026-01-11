#!/usr/bin/env python3
"""
Train spaCy NER Model for Address Components
=============================================

Train a custom spaCy model to recognize Bangladeshi address components.

Author: Advanced AI Address Parser System
Date: January 2026
"""

import json
import random
from pathlib import Path
from typing import List, Tuple, Dict

try:
    import spacy
    from spacy.training import Example
    from spacy.util import minibatch, compounding
    SPACY_AVAILABLE = True
except ImportError:
    print("❌ spaCy not installed!")
    print("   Run: pip install spacy")
    print("   For Bangla support: python -m spacy download xx_ent_wiki_sm")
    exit(1)


def load_training_data(file_path: str) -> List[Tuple[str, Dict]]:
    """Load training data from JSON"""
    with open(file_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    training_data = [
        (item["text"], {"entities": item["entities"]})
        for item in json_data
    ]
    
    return training_data


def train_spacy_model(training_data: List[Tuple[str, Dict]],
                     n_iter: int = 30,
                     output_dir: str = "models/address_ner_model",
                     base_model: str = "xx_ent_wiki_sm"):
    """
    Train spaCy NER model
    
    Args:
        training_data: List of (text, {"entities": [(start, end, label)]})
        n_iter: Number of training iterations
        output_dir: Where to save trained model
        base_model: Base model to use (xx_ent_wiki_sm for multilingual, en_core_web_sm for English)
    """
    print("=" * 80)
    print("TRAINING SPACY NER MODEL")
    print("=" * 80)
    print()
    
    # Load base model
    try:
        nlp = spacy.load(base_model)
        print(f"✓ Loaded base model: {base_model}")
    except:
        try:
            nlp = spacy.load("en_core_web_sm")
            print(f"✓ Loaded English base model")
        except:
            print("❌ No base model found!")
            print("   Run: python -m spacy download xx_ent_wiki_sm")
            print("   Or: python -m spacy download en_core_web_sm")
            return
    
    # Add NER pipe if not present
    if "ner" not in nlp.pipe_names:
        ner = nlp.add_pipe("ner")
        print("✓ Added NER pipe")
    else:
        ner = nlp.get_pipe("ner")
        print("✓ Using existing NER pipe")
    
    # Add labels
    labels = ["HOUSE", "ROAD", "AREA", "DISTRICT", "POSTAL", "FLAT", "FLOOR", "BLOCK"]
    for label in labels:
        ner.add_label(label)
    print(f"✓ Added {len(labels)} labels: {', '.join(labels)}")
    print()
    
    # Split into train/validation (80/20)
    random.shuffle(training_data)
    split_idx = int(len(training_data) * 0.8)
    train_data = training_data[:split_idx]
    val_data = training_data[split_idx:]
    
    print(f"Training samples: {len(train_data)}")
    print(f"Validation samples: {len(val_data)}")
    print()
    
    # Disable other pipes during training
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != "ner"]
    with nlp.disable_pipes(*other_pipes):
        optimizer = nlp.create_optimizer()
        
        print(f"Training for {n_iter} iterations...")
        print()
        
        best_val_loss = float('inf')
        
        for iteration in range(n_iter):
            random.shuffle(train_data)
            losses = {}
            
            # Convert to Examples
            examples = []
            for text, annotations in train_data:
                try:
                    doc = nlp.make_doc(text)
                    example = Example.from_dict(doc, annotations)
                    examples.append(example)
                except:
                    # Skip invalid examples
                    continue
            
            # Update model in batches
            batches = minibatch(examples, size=compounding(4.0, 32.0, 1.001))
            for batch in batches:
                nlp.update(batch, drop=0.5, losses=losses)
            
            # Validate
            val_loss = 0.0
            if val_data and (iteration + 1) % 5 == 0:
                val_examples = []
                for text, annotations in val_data:
                    try:
                        doc = nlp.make_doc(text)
                        example = Example.from_dict(doc, annotations)
                        val_examples.append(example)
                    except:
                        continue
                
                val_scores = nlp.evaluate(val_examples)
                val_loss = val_scores.get('ents_f', 0.0)
                
                print(f"Iteration {iteration + 1:3d}/{n_iter} | "
                      f"Train Loss: {losses.get('ner', 0):.4f} | "
                      f"Val F-score: {val_loss:.4f}")
                
                # Save best model
                if val_loss > best_val_loss:
                    best_val_loss = val_loss
            else:
                print(f"Iteration {iteration + 1:3d}/{n_iter} | "
                      f"Train Loss: {losses.get('ner', 0):.4f}")
    
    # Save model
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    nlp.to_disk(output_path)
    
    print()
    print("=" * 80)
    print("TRAINING COMPLETE")
    print("=" * 80)
    print(f"✓ Model saved to: {output_dir}")
    print(f"✓ Best validation F-score: {best_val_loss:.4f}")
    print()
    print("Next steps:")
    print(f"  1. Test model: python test_hybrid_extractor.py")
    print(f"  2. Use in hybrid extractor: python hybrid_extractor.py")
    print()


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train spaCy NER model')
    parser.add_argument('--input', default='data/spacy_training_data.json',
                       help='Training data path')
    parser.add_argument('--output', default='models/address_ner_model',
                       help='Output model directory')
    parser.add_argument('--iterations', type=int, default=30,
                       help='Number of training iterations')
    parser.add_argument('--base-model', default='xx_ent_wiki_sm',
                       help='Base spaCy model (xx_ent_wiki_sm or en_core_web_sm)')
    
    args = parser.parse_args()
    
    # Load training data
    print(f"Loading training data from {args.input}...")
    training_data = load_training_data(args.input)
    print(f"✓ Loaded {len(training_data)} training examples\n")
    
    # Train model
    train_spacy_model(
        training_data,
        n_iter=args.iterations,
        output_dir=args.output,
        base_model=args.base_model
    )


if __name__ == "__main__":
    main()
