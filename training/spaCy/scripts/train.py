#!/usr/bin/env python3
"""
🇧🇩 BANGLADESH ADDRESS EXTRACTOR - UNIFIED TRAINING
====================================================

ONE SCRIPT FOR ALL TRAINING NEEDS:
✅ Model training (M4 Metal, PyTorch CPU, spaCy)
✅ Training data enhancement
✅ Add house/road pattern examples

USAGE:
    # Train model
    python3 train.py train --mode spacy --epochs 200
    
    # Enhance training data
    python3 train.py enhance --input data/training/spacy_training_data.json
    
    # Add house/road examples
    python3 train.py add-examples

Author: Complete Bangladesh Solution
Date: January 2026
"""

import argparse
import json
import random
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# ============================================================================
# DEPENDENCY CHECKS
# ============================================================================

print("\n🔍 Checking dependencies...")

# PyTorch
try:
    import torch
    print(f"✅ PyTorch {torch.__version__}")
    if torch.backends.mps.is_available():
        print(f"   🍎 M4 Metal GPU available!")
    HAS_TORCH = True
except ImportError:
    print("❌ PyTorch not installed")
    print("   Install: pip3 install torch torchvision torchaudio")
    HAS_TORCH = False

# Transformers
try:
    from datasets import Dataset
    from transformers import (AutoModelForTokenClassification, AutoTokenizer,
                              DataCollatorForTokenClassification, Trainer,
                              TrainingArguments)
    print("✅ Transformers available")
    HAS_TRANSFORMERS = True
except ImportError:
    print("❌ Transformers not installed")
    print("   Install: pip3 install transformers datasets")
    HAS_TRANSFORMERS = False

# spaCy
try:
    import spacy
    from spacy.training import Example
    from spacy.util import compounding, minibatch
    print("✅ spaCy available")
    HAS_SPACY = True
except ImportError:
    print("❌ spaCy not installed")
    print("   Install: pip3 install spacy")
    HAS_SPACY = False

# ONNX (for export)
try:
    import onnx
    import onnxruntime as ort
    print("✅ ONNX Runtime available")
    HAS_ONNX = True
except ImportError:
    print("⚠️  ONNX not installed (optional for export)")
    HAS_ONNX = False

print()

# Import regex processors and patterns
# Point to project root (parent of training/spaCy/scripts/)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
try:
    from src.regex.area_processor import AdvancedAreaExtractor
    from src.regex.block_processor import AdvancedBlockNumberExtractor
    from src.regex.district_processor import AdvancedCityExtractor
    from src.regex.flat_number_processor import AdvancedFlatNumberExtractor
    from src.regex.floor_number_processor import AdvancedFloorNumberExtractor
    from src.regex.house_number_processor import AdvancedHouseNumberExtractor
    from src.regex.patterns import ALL_PATTERNS
    from src.regex.postal_code_processor import AdvancedPostalCodeExtractor
    from src.regex.road_processor import AdvancedRoadNumberExtractor
    HAS_PROCESSORS = True
    HAS_PATTERNS = True
except ImportError as e:
    print(f"⚠️  Regex processors not all available: {e}")
    HAS_PROCESSORS = False
    HAS_PATTERNS = False
    ALL_PATTERNS = {}


# ============================================================================
# BANGLADESH GEOGRAPHIC INTELLIGENCE
# ============================================================================

class BangladeshGeoIntelligence:
    """
    Complete Bangladesh geographic hierarchy and inference system
    - 1,226 postal codes
    - 64 districts → 8 divisions
    - Area → postal code mapping
    - Missing component prediction
    """
    
    def __init__(self, division_data_path: str = None):
        # Get project root for default path
        if division_data_path is None:
            script_dir = Path(__file__).parent
            project_root = script_dir.parent.parent.parent
            division_data_path = str(project_root / 'data' / 'geographic' / 'division')
        self.division_path = Path(division_data_path)
        
        # Geographic databases
        self.postal_codes = {}  # {code: {district, postOffice}}
        self.district_to_division = {}  # {district: division}
        self.area_to_postal = defaultdict(set)  # {area: {postal_codes}}
        self.district_to_postals = defaultdict(set)  # {district: {postal_codes}}
        
        # Load data
        if self.division_path.exists():
            self._load_data()
        else:
            print(f"⚠️  Division data not found at: {self.division_path}")
            print("   Training without geographic intelligence")
    
    def _load_data(self):
        """Load all geographic data"""
        print("📍 Loading Bangladesh geographic intelligence...")
        
        # Postal codes
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
                        
                        if post_office:
                            self.area_to_postal[post_office.lower()].add(code)
        
        # District-division mapping
        district_file = self.division_path / "district-to-division-mapping.json"
        if district_file.exists():
            with open(district_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
                self.district_to_division = {k.lower(): v for k, v in mapping.items()}
        
        print(f"   ✅ {len(self.postal_codes)} postal codes")
        print(f"   ✅ {len(self.district_to_division)} districts")
        print(f"   ✅ {len(self.area_to_postal)} areas mapped")
    
    def infer_postal_code(self, area: str = None, district: str = None) -> Optional[str]:
        """Infer postal code from area or district"""
        if area and area.lower() in self.area_to_postal:
            postals = list(self.area_to_postal[area.lower()])
            if postals:
                return postals[0]
        
        if district and district.lower() in self.district_to_postals:
            postals = list(self.district_to_postals[district.lower()])
            if postals:
                return postals[0]
        
        return None
    
    def infer_division(self, district: str) -> Optional[str]:
        """Infer division from district"""
        if district:
            return self.district_to_division.get(district.lower())
        return None


# ============================================================================
# DATA PREPARATION
# ============================================================================

class DataPreparator:
    """Prepare training data from Bangladesh addresses"""
    
    def __init__(self, geo_intel: BangladeshGeoIntelligence, extractors: Dict = None):
        self.geo = geo_intel
        self.extractors = extractors or {}
    
    def load_addresses(self, data_path: str) -> List[Dict]:
        """Load addresses from JSON"""
        print(f"\n📂 Loading addresses from: {data_path}")
        
        path = Path(data_path)
        if not path.exists():
            print(f"❌ File not found: {data_path}")
            return []
        
        with open(path, 'r', encoding='utf-8') as f:
            addresses = json.load(f)
        
        print(f"   ✅ Loaded {len(addresses):,} addresses")
        return addresses
    
    def prepare_for_spacy(self, addresses: List[Dict], test_mode: bool = False) -> Tuple[List, Dict]:
        """Prepare data for spaCy NER training"""
        print("\n🔧 Preparing data for spaCy...")
        
        training_data = []
        stats = {
            'total': len(addresses),
            'processed': 0,
            'with_entities': 0,
            'geo_enhanced': 0,
        }
        
        # Limit for test mode
        if test_mode:
            addresses = addresses[:1000]
            print("   🧪 Test mode: Using 1,000 addresses")
        
        for addr in addresses:
            # Handle both 'address' and 'full_address' fields
            text = addr.get('address') or addr.get('full_address', '')
            if not text or len(text) < 10:
                continue
            
            entities = []
            
            # Extract components
            components = self._extract_components(addr, text)
            
            # Create entity spans using regex patterns for accurate positioning
            for key, value in components.items():
                if not value:
                    continue
                
                # Try to find using regex patterns first for accurate spans
                span = self._find_entity_span(text, key, value)
                if span:
                    start, end = span
                    label = self._get_entity_label(key)
                    entities.append((start, end, label))
                else:
                    # Fallback to simple string search
                    value_str = str(value).strip()
                    start = text.lower().find(value_str.lower())
                    
                    if start >= 0:
                        end = start + len(value_str)
                        label = self._get_entity_label(key)
                        entities.append((start, end, label))
            
            if entities:
                training_data.append((text, {'entities': entities}))
                stats['with_entities'] += 1
            
            stats['processed'] += 1
            
            if stats['processed'] % 1000 == 0:
                print(f"   Processed {stats['processed']:,}/{len(addresses):,}...")
        
        print(f"\n   ✅ Created {len(training_data):,} training examples")
        print(f"   ✅ Geographic enhancements: {stats['geo_enhanced']}")
        
        return training_data, stats
    
    def prepare_for_transformers(self, addresses: List[Dict], test_mode: bool = False) -> Tuple[Dataset, Dataset]:
        """Prepare data for Transformers training"""
        print("\n🔧 Preparing data for Transformers...")
        
        # Limit for test mode
        if test_mode:
            addresses = addresses[:1000]
            print("   🧪 Test mode: Using 1,000 addresses")
        
        examples = []
        stats = {
            'total': len(addresses),
            'processed': 0,
            'with_labels': 0,
            'geo_enhanced': 0,
        }
        
        for addr in addresses:
            # Handle both 'address' and 'full_address' fields
            text = addr.get('address') or addr.get('full_address', '')
            if not text or len(text) < 10:
                continue
            
            # Extract components
            components = self._extract_components(addr, text)
            
            if components:
                examples.append({
                    'text': text,
                    'components': components
                })
                stats['with_labels'] += 1
            
            stats['processed'] += 1
            
            if stats['processed'] % 1000 == 0:
                print(f"   Processed {stats['processed']:,}/{len(addresses):,}...")
        
        print(f"\n   ✅ Created {len(examples):,} training examples")
        print(f"   ✅ Geographic enhancements: {stats['geo_enhanced']}")
        
        # Convert to Dataset
        dataset = Dataset.from_list(examples)
        
        # Split train/val
        split = dataset.train_test_split(test_size=0.2, seed=42)
        
        return split['train'], split['test']
    
    def _extract_components(self, addr: Dict, text: str) -> Dict:
        """Extract all address components using regex patterns and processors"""
        components = {}
        
        # Handle both data formats
        # Format 1: direct fields (house, road, etc.)
        # Format 2: nested in 'components' (house_number, road, etc.)
        addr_components = addr.get('components', {})
        
        # Map of component keys to possible field names
        component_map = {
            'house': ['house', 'house_number'],
            'road': ['road', 'road_number'],
            'area': ['area'],
            'district': ['district'],
            'division': ['division'],
            'postal_code': ['postal_code', 'postalCode'],
            'flat': ['flat', 'flat_number'],
            'floor': ['floor', 'floor_number'],
            'block': ['block', 'block_number'],
        }
        
        # Extract from data first
        for key, possible_names in component_map.items():
            # Try direct field first
            for name in possible_names:
                if value := addr.get(name):
                    if str(value).strip():
                        components[key] = str(value).strip()
                        break
            
            # Try nested components
            if key not in components:
                for name in possible_names:
                    if value := addr_components.get(name):
                        if str(value).strip():
                            components[key] = str(value).strip()
                            break
        
        # Use regex patterns directly for enhanced extraction
        if HAS_PATTERNS and ALL_PATTERNS:
            components = self._extract_with_patterns(text, components)
        
        # Use regex processors as fallback/enhancement
        if self.extractors:
            try:
                # House
                if 'house' not in components and self.extractors.get('house'):
                    if result := self.extractors['house'].extract(text):
                        components['house'] = result.get('house_number', '')
                
                # Road
                if 'road' not in components and self.extractors.get('road'):
                    if result := self.extractors['road'].extract(text):
                        components['road'] = result.get('road_number', '')
                
                # Area
                if 'area' not in components and self.extractors.get('area'):
                    if result := self.extractors['area'].extract(text):
                        components['area'] = result.get('area', '')
                
                # District
                if 'district' not in components and self.extractors.get('district'):
                    if result := self.extractors['district'].extract(text):
                        components['district'] = result.get('city', '')
                
                # Postal
                if 'postal_code' not in components and self.extractors.get('postal'):
                    if result := self.extractors['postal'].extract(text):
                        components['postal_code'] = result.get('postal_code', '')
                
                # Other components (flat, floor, block)
                for key in ['flat', 'floor', 'block']:
                    if key not in components and self.extractors.get(key):
                        if result := self.extractors[key].extract(text):
                            value = result.get(f'{key}_number', '')
                            if value:
                                components[key] = value
            except:
                pass
        
        # Geographic intelligence enhancements
        if self.geo:
            # Infer postal code
            if 'postal_code' not in components:
                area = components.get('area')
                district = components.get('district')
                if postal := self.geo.infer_postal_code(area, district):
                    components['postal_code'] = postal
            
            # Infer division
            if 'division' not in components and 'district' in components:
                if division := self.geo.infer_division(components['district']):
                    components['division'] = division
        
        return components
    
    def _extract_with_patterns(self, text: str, existing_components: Dict) -> Dict:
        """Extract components using regex patterns directly"""
        import re
        components = existing_components.copy()
        
        # Try each component type with its patterns
        for component_type, patterns in ALL_PATTERNS.items():
            if component_type in components:
                continue  # Already extracted from data
            
            best_match = None
            best_confidence = 0.0
            
            for pattern, confidence in patterns:
                try:
                    match = re.search(pattern, text, re.IGNORECASE | re.UNICODE)
                    if match:
                        # Extract the captured group or full match
                        if match.groups():
                            value = match.group(1) if match.lastindex >= 1 else match.group(0)
                        else:
                            value = match.group(0)
                        
                        value = value.strip()
                        if value and confidence > best_confidence:
                            best_match = value
                            best_confidence = confidence
                except:
                    continue
            
            if best_match and best_confidence >= 0.85:  # Only use high-confidence matches
                components[component_type] = best_match
        
        return components
    
    def _find_entity_span(self, text: str, component_type: str, value: str) -> Optional[Tuple[int, int]]:
        """Find entity span using regex patterns for accurate positioning"""
        import re
        
        if not HAS_PATTERNS or component_type not in ALL_PATTERNS:
            return None
        
        patterns = ALL_PATTERNS[component_type]
        value_lower = str(value).lower().strip()
        
        # Try patterns in order of confidence
        for pattern, confidence in sorted(patterns, key=lambda x: x[1], reverse=True):
            try:
                match = re.search(pattern, text, re.IGNORECASE | re.UNICODE)
                if match:
                    # Extract matched value
                    if match.groups():
                        matched_value = match.group(1) if match.lastindex >= 1 else match.group(0)
                    else:
                        matched_value = match.group(0)
                    
                    matched_value = matched_value.strip()
                    
                    # Check if this matches our target value
                    if matched_value.lower() == value_lower or value_lower in matched_value.lower():
                        # Return span of the captured group or full match
                        if match.groups() and match.lastindex >= 1:
                            return (match.start(1), match.end(1))
                        else:
                            return (match.start(), match.end())
            except:
                continue
        
        return None
    
    def _get_entity_label(self, key: str) -> str:
        """Get entity label for component"""
        label_map = {
            'house': 'HOUSE',
            'road': 'ROAD',
            'area': 'AREA',
            'district': 'DISTRICT',
            'division': 'DIVISION',
            'postal_code': 'POSTAL',
            'flat': 'FLAT',
            'floor': 'FLOOR',
            'block': 'BLOCK',
        }
        return label_map.get(key, 'OTHER')


# ============================================================================
# SPACY TRAINER
# ============================================================================

class SpaCyTrainer:
    """spaCy NER trainer (CPU-only)"""
    
    def __init__(self):
        if not HAS_SPACY:
            raise ImportError("spaCy not installed")
        
        self.nlp = None
    
    def train(self, training_data: List, n_iter: int = 100, output_dir: str = None):
        # Get project root for default path
        if output_dir is None:
            script_dir = Path(__file__).parent
            project_root = script_dir.parent.parent.parent
            output_dir = str(project_root / 'models' / 'training' / 'outputs' / 'spacy_model')
        """Train spaCy model"""
        print("\n" + "🎓" * 40)
        print("SPACY NER TRAINING (CPU)")
        print("🎓" * 40)
        
        # Create blank model
        self.nlp = spacy.blank("en")
        
        # Add NER
        if "ner" not in self.nlp.pipe_names:
            ner = self.nlp.add_pipe("ner")
        else:
            ner = self.nlp.get_pipe("ner")
        
        # Collect all unique labels
        all_labels = set()
        for _, annotations in training_data:
            for ent in annotations.get("entities", []):
                all_labels.add(ent[2])
        
        # Add all labels to NER
        print(f"Adding {len(all_labels)} entity labels...")
        for label in sorted(all_labels):
            ner.add_label(label)
        
        print(f"Labels: {sorted(all_labels)}")
        
        # Split train/val
        random.shuffle(training_data)
        split_point = int(len(training_data) * 0.8)
        train_data = training_data[:split_point]
        val_data = training_data[split_point:]
        
        print(f"\nTrain samples: {len(train_data):,}")
        print(f"Val samples: {len(val_data):,}")
        print(f"Iterations: {n_iter}")
        print(f"\n⏱️  Estimated time: {n_iter * len(train_data) / 10000:.0f}-{n_iter * len(train_data) / 5000:.0f} hours\n")
        
        # Initialize the model with training data
        print("Initializing NER model...")
        init_examples = []
        for text, annot in train_data[:100]:  # Use first 100 examples
            try:
                doc = self.nlp.make_doc(text)
                init_examples.append(Example.from_dict(doc, annot))
            except:
                continue
        
        if init_examples:
            self.nlp.initialize(lambda: init_examples)
        print("✅ Model initialized\n")
        
        # Train
        other_pipes = [pipe for pipe in self.nlp.pipe_names if pipe != "ner"]
        with self.nlp.disable_pipes(*other_pipes):
            optimizer = self.nlp.resume_training()
            
            best_f = 0.0
            start = time.time()
            
            for it in range(n_iter):
                random.shuffle(train_data)
                losses = {}
                
                examples = []
                for text, annot in train_data:
                    try:
                        doc = self.nlp.make_doc(text)
                        example = Example.from_dict(doc, annot)
                        # Only add if alignment is valid
                        if example.reference.has_annotation("ENT_IOB"):
                            examples.append(example)
                    except Exception:
                        # Skip examples with alignment issues
                        continue
                
                batches = minibatch(examples, size=compounding(8.0, 64.0, 1.001))
                for batch in batches:
                    self.nlp.update(batch, drop=0.30, losses=losses)
                
                # Validate every 10 iterations
                if (it + 1) % 10 == 0:
                    val_ex = []
                    for text, annot in val_data:
                        try:
                            doc = self.nlp.make_doc(text)
                            val_ex.append(Example.from_dict(doc, annot))
                        except:
                            continue
                    
                    scores = self.nlp.evaluate(val_ex)
                    f = scores.get('ents_f') or 0.0
                    p = scores.get('ents_p') or 0.0
                    r = scores.get('ents_r') or 0.0
                    elapsed = (time.time() - start) / 60
                    
                    print(f"Iter {it+1:3d}/{n_iter} | Loss: {losses.get('ner', 0):.3f} | "
                          f"F1: {f:.4f} | P: {p:.4f} | R: {r:.4f} | {elapsed:.1f}m")
                    
                    if f > best_f:
                        best_f = f
                        print(f"   ⭐ New best: {best_f:.4f}")
                
                elif it % 5 == 0:
                    elapsed = (time.time() - start) / 60
                    print(f"Iter {it+1:3d}/{n_iter} | Loss: {losses.get('ner', 0):.3f} | {elapsed:.1f}m")
        
        # Save
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        self.nlp.to_disk(output_path)
        
        total = (time.time() - start) / 60
        
        print("\n" + "=" * 80)
        print("✅ SPACY TRAINING COMPLETE!")
        print("=" * 80)
        print(f"📁 Model: {output_dir}")
        print(f"⭐ Best F1: {best_f:.4f}")
        print(f"⏱️  Time: {total:.1f} minutes ({total/60:.1f} hours)")
        print()


# ============================================================================
# PYTORCH TRANSFORMERS TRAINER
# ============================================================================

class TransformersTrainer:
    """PyTorch Transformers trainer (M4 Metal or CPU)"""
    
    def __init__(self, use_metal: bool = True):
        if not HAS_TORCH or not HAS_TRANSFORMERS:
            raise ImportError("PyTorch or Transformers not installed")
        
        # Device
        if use_metal and torch.backends.mps.is_available():
            self.device = torch.device("mps")
            print("🍎 Device: M4 Metal GPU")
        else:
            self.device = torch.device("cpu")
            print("💻 Device: CPU")
        
        # Config
        self.config = {
            'model_name': 'distilbert-base-uncased',
            'batch_size': 32 if self.device.type == 'mps' else 16,
            'learning_rate': 2e-5,
            'max_length': 128,
            'warmup_steps': 500,
            'weight_decay': 0.01,
            'num_workers': 8 if self.device.type == 'mps' else 4,
        }
        
        # Labels
        self.labels = [
            'O',
            'B-HOUSE', 'I-HOUSE',
            'B-ROAD', 'I-ROAD',
            'B-AREA', 'I-AREA',
            'B-DISTRICT', 'I-DISTRICT',
            'B-DIVISION', 'I-DIVISION',
            'B-POSTAL', 'I-POSTAL',
            'B-FLAT', 'I-FLAT',
            'B-FLOOR', 'I-FLOOR',
            'B-BLOCK', 'I-BLOCK',
        ]
        self.label2id = {label: i for i, label in enumerate(self.labels)}
        self.id2label = {i: label for i, label in enumerate(self.labels)}
    
    def train(
        self,
        train_dataset: Dataset,
        val_dataset: Dataset,
        epochs: int = 50,
        output_dir: str = None
    ):
        """Train Transformers model"""
        print("\n" + "🤖" * 40)
        print(f"TRANSFORMERS TRAINING ({self.device.type.upper()})")
        print("🤖" * 40)
        
        print(f"\nModel: {self.config['model_name']}")
        print(f"Epochs: {epochs}")
        print(f"Batch size: {self.config['batch_size']}")
        print(f"Train samples: {len(train_dataset):,}")
        print(f"Val samples: {len(val_dataset):,}")
        print(f"\n⏱️  Estimated time: {epochs * len(train_dataset) / 2000:.0f}-{epochs * len(train_dataset) / 1000:.0f} hours\n")
        
        # Load model
        print("Loading model...")
        model = AutoModelForTokenClassification.from_pretrained(
            self.config['model_name'],
            num_labels=len(self.labels),
            id2label=self.id2label,
            label2id=self.label2id
        )
        model = model.to(self.device)
        
        tokenizer = AutoTokenizer.from_pretrained(self.config['model_name'])
        print("✅ Model loaded\n")
        
        # Training args
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=epochs,
            per_device_train_batch_size=self.config['batch_size'],
            per_device_eval_batch_size=self.config['batch_size'],
            learning_rate=self.config['learning_rate'],
            warmup_steps=self.config['warmup_steps'],
            weight_decay=self.config['weight_decay'],
            logging_dir=f"{output_dir}/logs",
            logging_steps=100,
            eval_strategy="steps",
            eval_steps=500,
            save_steps=1000,
            save_total_limit=3,
            load_best_model_at_end=True,
            metric_for_best_model="eval_loss",
            use_mps_device=(self.device.type == "mps"),
            dataloader_num_workers=self.config['num_workers'],
            fp16=False,
            report_to="none",
            remove_unused_columns=False,  # Keep all columns
        )
        
        # Data collator
        data_collator = DataCollatorForTokenClassification(
            tokenizer=tokenizer,
            padding=True,
            max_length=self.config['max_length']
        )
        
        # Trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            tokenizer=tokenizer,
            data_collator=data_collator,
        )
        
        # Train
        start = time.time()
        trainer.train()
        training_time = (time.time() - start) / 60
        
        # Save
        trainer.save_model(output_dir)
        tokenizer.save_pretrained(output_dir)
        
        # Evaluate
        metrics = trainer.evaluate()
        
        print("\n" + "=" * 80)
        print("✅ TRANSFORMERS TRAINING COMPLETE!")
        print("=" * 80)
        print(f"📁 Model: {output_dir}")
        print(f"⏱️  Time: {training_time:.1f} minutes ({training_time/60:.1f} hours)")
        print(f"📊 Final loss: {metrics.get('eval_loss', 0):.4f}")
        print()


# ============================================================================
# TRAINING DATA ENHANCEMENT
# ============================================================================

def extract_house_road_entities(text: str) -> Tuple[Optional[Tuple[int, int, str]], Optional[Tuple[int, int, str]]]:
    """Extract house and road entities from text with h-X, r-Y patterns"""
    house_entity = None
    road_entity = None
    
    # House patterns: h-107/2, h@45, h:12, H-45, etc.
    house_patterns = [
        (r'\b[hH][\s\-@:]+([\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)', 'HOUSE', 'h-'),
        (r'\b(?:house|home)[\s\-@:]+([\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)', 'HOUSE', 'house'),
    ]
    
    # Road patterns: r-7, R@7, r:5, etc.
    road_patterns = [
        (r'\b[rR][\s\-@:]+([\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)', 'ROAD', 'r-'),
        (r'\b(?:road|rd)[\s\-@:]+([\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)', 'ROAD', 'road'),
    ]
    
    # Find house
    for pattern, label, prefix in house_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            full_match = match.group(0)
            start = match.start()
            end = match.end()
            house_entity = (start, end, label)
            break
    
    # Find road
    for pattern, label, prefix in road_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            full_match = match.group(0)
            start = match.start()
            end = match.end()
            road_entity = (start, end, label)
            break
    
    return house_entity, road_entity


def validate_entities(text: str, entities: List[Tuple[int, int, str]]) -> bool:
    """Validate that entities don't overlap and are within text bounds"""
    for i, (start1, end1, label1) in enumerate(entities):
        if start1 < 0 or end1 > len(text) or start1 >= end1:
            return False
        
        for j, (start2, end2, label2) in enumerate(entities):
            if i != j:
                if not (end1 <= start2 or end2 <= start1):
                    return False
    
    return True


def fix_entity_spans(text: str, entities: List[Tuple[int, int, str]]) -> List[Tuple[int, int, str]]:
    """Fix entity spans to ensure proper separation"""
    fixed = []
    
    for start, end, label in entities:
        entity_text = text[start:end]
        
        if label == 'ROAD' and (re.search(r'\b[hH][\s\-@:]+[\d০-৯]+', entity_text, re.IGNORECASE) or
                                 re.search(r'\b(?:house|home)[\s\-@:]+[\d০-৯]+', entity_text, re.IGNORECASE)):
            road_match = re.search(r'\b[rR][\s\-@:]+([\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)', entity_text, re.IGNORECASE)
            if road_match:
                road_start_in_entity = road_match.start()
                road_end_in_entity = road_match.end()
                new_start = start + road_start_in_entity
                new_end = start + road_end_in_entity
                fixed.append((new_start, new_end, label))
            continue
        
        fixed.append((start, end, label))
    
    return fixed


def enhance_training_data(input_file: str = None,
                         output_file: str = None):
    # Get project root for default paths
    if input_file is None or output_file is None:
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent.parent
        if input_file is None:
            input_file = str(project_root / 'data' / 'training' / 'spacy_training_data.json')
        if output_file is None:
            output_file = str(project_root / 'data' / 'training' / 'spacy_training_data_enhanced.json')
    """Enhance training data with proper house/road entity separation"""
    
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    print(f"Loading training data from {input_path}...")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loaded {len(data)} examples")
    
    enhanced = []
    fixed_count = 0
    added_count = 0
    
    for item in data:
        text = item.get('text', '')
        entities = item.get('entities', [])
        
        has_house_pattern = bool(re.search(r'\b[hH][\s\-@:]+[\d০-৯]+', text, re.IGNORECASE) or
                                 re.search(r'\b(?:house|home)[\s\-@:]+[\d০-৯]+', text, re.IGNORECASE))
        has_road_pattern = bool(re.search(r'\b[rR][\s\-@:]+[\d০-৯]+', text, re.IGNORECASE) or
                               re.search(r'\b(?:road|rd)[\s\-@:]+[\d০-৯]+', text, re.IGNORECASE))
        
        if has_house_pattern and has_road_pattern:
            house_entity, road_entity = extract_house_road_entities(text)
            
            house_entities = [e for e in entities if e[2] in ['HOUSE', 'house', 'house_number']]
            road_entities = [e for e in entities if e[2] in ['ROAD', 'road', 'road_number']]
            
            if house_entity and road_entity:
                needs_fix = False
                
                for start, end, label in road_entities:
                    road_text = text[start:end]
                    if re.search(r'\b[hH][\s\-@:]+[\d০-৯]+', road_text, re.IGNORECASE):
                        needs_fix = True
                        break
                
                if needs_fix or not house_entities or not road_entities:
                    new_entities = []
                    
                    for start, end, label in entities:
                        if label not in ['HOUSE', 'house', 'house_number', 'ROAD', 'road', 'road_number']:
                            new_entities.append((start, end, label))
                    
                    new_entities.append(house_entity)
                    new_entities.append(road_entity)
                    new_entities.sort(key=lambda x: x[0])
                    
                    if validate_entities(text, new_entities):
                        entities = new_entities
                        fixed_count += 1
                        print(f"  Fixed: {text[:50]}...")
            
            entities = fix_entity_spans(text, entities)
        
        if validate_entities(text, entities):
            enhanced.append({
                'text': text,
                'entities': entities
            })
        else:
            print(f"  Skipped invalid: {text[:50]}...")
    
    # Add new examples
    print("\nAdding new training examples...")
    new_examples = [
        {
            "text": "sottota tower, h-107/2,r-7, north bishil, mirpur 1",
            "entities": [[18, 24, "HOUSE"], [25, 28, "ROAD"]]
        },
        {
            "text": "h@45, R@7, Gulshan, Dhaka",
            "entities": [[0, 4, "HOUSE"], [6, 9, "ROAD"]]
        },
        {
            "text": "h:107/2,R:7, north bishil, mirpur 1",
            "entities": [[0, 7, "HOUSE"], [8, 11, "ROAD"]]
        },
        {
            "text": "House h-12, Road r-5, Mirpur, Dhaka",
            "entities": [[6, 10, "HOUSE"], [18, 21, "ROAD"]]
        },
        {
            "text": "Building h-101/1, r-08, Dhanmondi, Dhaka",
            "entities": [[9, 16, "HOUSE"], [18, 21, "ROAD"]]
        },
    ]
    
    existing_texts = {item['text'] for item in enhanced}
    for ex in new_examples:
        if ex['text'] not in existing_texts:
            enhanced.append(ex)
            added_count += 1
    
    print(f"\nSaving enhanced data to {output_path}...")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(enhanced, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Enhanced training data:")
    print(f"   Total examples: {len(enhanced)}")
    print(f"   Fixed entities: {fixed_count}")
    print(f"   Added examples: {added_count}")
    print(f"   Output: {output_path}")
    
    return enhanced


def generate_house_road_examples() -> List[Dict]:
    """Generate training examples for house/road patterns"""
    examples = []
    
    patterns = [
        ("sottota tower, h-107/2,r-7, north bishil, mirpur 1", "h-107/2", "r-7"),
        ("House h-45, Road r-7, Mirpur, Dhaka", "h-45", "r-7"),
        ("Building h-12, r-5, Gulshan, Dhaka", "h-12", "r-5"),
        ("h-101/1, r-08, Dhanmondi, Dhaka", "h-101/1", "r-08"),
        ("h@45, R@7, Gulshan, Dhaka", "h@45", "R@7"),
        ("House h@12, Road R@5, Mirpur, Dhaka", "h@12", "R@5"),
        ("h@107/2, r@7, north bishil, mirpur 1", "h@107/2", "r@7"),
        ("h:107/2,R:7, north bishil, mirpur 1", "h:107/2", "R:7"),
        ("House h:45, Road R:7, Mirpur, Dhaka", "h:45", "R:7"),
        ("h:12, r:5, Gulshan, Dhaka", "h:12", "r:5"),
        ("h-107/2, Road r-7, Mirpur, Dhaka", "h-107/2", "Road r-7"),
        ("House h-45, r-7, Gulshan, Dhaka", "h-45", "r-7"),
        ("h@12, Road No r-5, Dhanmondi, Dhaka", "h@12", "Road No r-5"),
    ]
    
    for text, house_pattern, road_pattern in patterns:
        house_entities = []
        road_entities = []
        
        text_lower = text.lower()
        house_lower = house_pattern.lower()
        road_lower = road_pattern.lower()
        
        start = 0
        while True:
            pos = text_lower.find(house_lower, start)
            if pos == -1:
                break
            house_entities.append((pos, pos + len(house_pattern), "HOUSE"))
            start = pos + 1
        
        start = 0
        while True:
            pos = text_lower.find(road_lower, start)
            if pos == -1:
                break
            road_entities.append((pos, pos + len(road_pattern), "ROAD"))
            start = pos + 1
        
        if house_entities and road_entities:
            entities = [house_entities[0], road_entities[0]]
            examples.append({
                "text": text,
                "entities": entities
            })
    
    return examples


def add_house_road_examples(output_file: str = None):
    # Get project root for default path
    if output_file is None:
        script_dir = Path(__file__).parent
        project_root = script_dir.parent.parent.parent
        output_file = str(project_root / 'data' / 'training' / 'spacy_training_data.json')
    """Add house/road pattern examples to training data"""
    training_file = Path(output_file)
    
    if training_file.exists():
        with open(training_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = []
    
    examples = generate_house_road_examples()
    existing_texts = {item.get('text', '') for item in data}
    new_examples = [ex for ex in examples if ex['text'] not in existing_texts]
    
    data.extend(new_examples)
    
    training_file.parent.mkdir(parents=True, exist_ok=True)
    with open(training_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Added {len(new_examples)} new examples")
    print(f"📊 Total examples: {len(data)}")
    print(f"📝 File: {training_file}")
    
    return len(new_examples)


# ============================================================================
# MAIN
# ============================================================================

def cmd_train(args):
    """Train model command"""
    if args.test:
        args.epochs = 10
        print("\n🧪 TEST MODE: 1,000 addresses, 10 epochs")
    
    # Auto-consolidate training data if requested
    if args.consolidate:
        print("\n" + "=" * 80)
        print("Step 1: Consolidating Training Data")
        print("=" * 80)
        consolidate_training_data(
            input_files=args.consolidate_input,
            output_file=args.consolidate_output
        )
        print()
    
    print("\n" + "🇧🇩" * 40)
    print("BANGLADESH ADDRESS EXTRACTOR - TRAINING")
    print("🇧🇩" * 40)
    print(f"\nMode: {args.mode.upper()}")
    print(f"Data: {args.data}")
    print(f"Epochs: {args.epochs}")
    print(f"Output: {args.output}")
    print()
    
    geo_intel = BangladeshGeoIntelligence()
    
    extractors = {}
    if HAS_PROCESSORS:
        print("🔧 Loading regex processors...")
        try:
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
            print("   ✅ All processors loaded")
        except Exception as e:
            print(f"   ⚠️  Some processors failed: {e}")
    print()
    
    preparator = DataPreparator(geo_intel, extractors)
    addresses = preparator.load_addresses(args.data)
    
    if not addresses:
        print("❌ No addresses loaded. Exiting.")
        return
    
    if args.mode == 'spacy':
        if not HAS_SPACY:
            print("❌ spaCy not installed!")
            return
        
        training_data, stats = preparator.prepare_for_spacy(addresses, args.test)
        trainer = SpaCyTrainer()
        trainer.train(training_data, n_iter=args.epochs, output_dir=args.output)
    
    else:
        if not HAS_TORCH or not HAS_TRANSFORMERS:
            print("❌ PyTorch or Transformers not installed!")
            return
        
        train_data, val_data = preparator.prepare_for_transformers(addresses, args.test)
        use_metal = (args.mode == 'm4')
        trainer = TransformersTrainer(use_metal=use_metal)
        trainer.train(train_data, val_data, epochs=args.epochs, output_dir=args.output)
    
    print("\n🎉 Training complete!")
    print(f"   Model saved to: {args.output}")


def cmd_enhance(args):
    """Enhance training data command"""
    print("=" * 80)
    print("Enhancing Training Data for House/Road Pattern Recognition")
    print("=" * 80)
    print()
    
    enhance_training_data(args.input, args.output)
    
    print()
    print("=" * 80)
    print("✅ Done!")
    print("=" * 80)


def cmd_add_examples(args):
    """Add house/road examples command"""
    print("=" * 80)
    print("Adding House/Road Pattern Examples to Training Data")
    print("=" * 80)
    print()
    
    print("Generating training examples...")
    examples = generate_house_road_examples()
    print(f"Generated {len(examples)} examples")
    print()
    
    added = add_house_road_examples(args.output)
    
    print()
    print("=" * 80)
    print("✅ Done!")
    print("=" * 80)


def consolidate_training_data(
    input_files: Optional[List[str]] = None,
    output_file: str = None
):
    # Get project root for default paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent
    
    if output_file is None:
        output_file = str(project_root / 'data' / 'training' / 'spacy_training_data.json')
    
    if input_files is None:
        input_files = [
            str(project_root / 'data' / 'training' / 'spacy_training_data.json'),
            str(project_root / 'data' / 'training' / 'spacy_training_data_enhanced.json'),
        ]
    """Consolidate and enhance training data using regex patterns"""
    import re
    
    if input_files is None:
        input_files = [
            "../../../data/training/spacy_training_data.json",
            "../../../data/training/spacy_training_data_enhanced.json",
        ]
    
    print("=" * 80)
    print("Consolidating Training Data with Regex Pattern Enhancement")
    print("=" * 80)
    print()
    
    all_examples = []
    seen_texts = set()
    
    # Load all input files
    for input_file in input_files:
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"⚠️  Skipping {input_file} (not found)")
            continue
        
        print(f"Loading {input_file}...")
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for item in data:
            text = item.get('text', '').strip()
            if not text or text in seen_texts:
                continue
            
            seen_texts.add(text)
            entities = item.get('entities', [])
            
            # Enhance entities using regex patterns
            enhanced_entities = enhance_entities_with_patterns(text, entities)
            
            all_examples.append({
                'text': text,
                'entities': enhanced_entities
            })
        
        print(f"  ✅ Loaded {len(data)} examples")
    
    print(f"\nTotal unique examples: {len(all_examples)}")
    
    # Enhance with regex patterns
    print("\n🔧 Enhancing with regex patterns...")
    enhanced_count = 0
    
    geo_intel = BangladeshGeoIntelligence()
    extractors = {}
    if HAS_PROCESSORS:
        try:
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
        except:
            pass
    
    preparator = DataPreparator(geo_intel, extractors)
    
    final_examples = []
    for item in all_examples:
        text = item['text']
        entities = item['entities']
        
        # Re-extract using enhanced methods
        components = preparator._extract_components({}, text)
        
        # Create new entities from components
        new_entities = []
        for key, value in components.items():
            if not value:
                continue
            
            span = preparator._find_entity_span(text, key, value)
            if span:
                start, end = span
                label = preparator._get_entity_label(key)
                new_entities.append((start, end, label))
            else:
                # Fallback
                value_str = str(value).strip()
                start = text.lower().find(value_str.lower())
                if start >= 0:
                    end = start + len(value_str)
                    label = preparator._get_entity_label(key)
                    new_entities.append((start, end, label))
        
        # Use enhanced entities if better, otherwise keep original
        if new_entities and len(new_entities) >= len(entities):
            entities = new_entities
            enhanced_count += 1
        
        # Validate and add
        if validate_entities(text, entities):
            final_examples.append({
                'text': text,
                'entities': entities
            })
    
    print(f"  ✅ Enhanced {enhanced_count} examples")
    
    # Save consolidated data
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_examples, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Consolidated training data:")
    print(f"   Total examples: {len(final_examples)}")
    print(f"   Enhanced: {enhanced_count}")
    print(f"   Output: {output_path}")
    
    return final_examples


def enhance_entities_with_patterns(text: str, entities: List[Tuple[int, int, str]]) -> List[Tuple[int, int, str]]:
    """Enhance entity spans using regex patterns"""
    import re
    
    if not HAS_PATTERNS:
        return entities
    
    enhanced = []
    label_to_type = {
        'HOUSE': 'house',
        'house': 'house',
        'house_number': 'house',
        'ROAD': 'road',
        'road': 'road',
        'road_number': 'road',
        'POSTAL': 'postal',
        'postal_code': 'postal',
        'FLAT': 'flat',
        'flat': 'flat',
        'FLOOR': 'floor',
        'floor': 'floor',
        'BLOCK': 'block',
        'block': 'block',
    }
    
    for start, end, label in entities:
        component_type = label_to_type.get(label)
        if component_type and component_type in ALL_PATTERNS:
            value = text[start:end]
            patterns = ALL_PATTERNS[component_type]
            
            # Try to find better span using patterns
            best_span = None
            for pattern, confidence in sorted(patterns, key=lambda x: x[1], reverse=True):
                try:
                    match = re.search(pattern, text, re.IGNORECASE | re.UNICODE)
                    if match:
                        matched_value = match.group(1) if match.groups() and match.lastindex >= 1 else match.group(0)
                        if matched_value.strip().lower() == value.lower():
                            if match.groups() and match.lastindex >= 1:
                                best_span = (match.start(1), match.end(1))
                            else:
                                best_span = (match.start(), match.end())
                            break
                except:
                    continue
            
            if best_span:
                enhanced.append((best_span[0], best_span[1], label))
            else:
                enhanced.append((start, end, label))
        else:
            enhanced.append((start, end, label))
    
    return enhanced


def cmd_consolidate(args):
    """Consolidate training data command"""
    print("=" * 80)
    print("Consolidating Training Data")
    print("=" * 80)
    print()
    
    input_files = args.input if args.input else None
    consolidate_training_data(input_files, args.output)
    
    print()
    print("=" * 80)
    print("✅ Done!")
    print("=" * 80)


def main():
    # Get project root (3 levels up from this script: scripts -> spaCy -> training -> root)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent
    
    parser = argparse.ArgumentParser(
        description="Bangladesh Address Extractor - Unified Training",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Train with auto-consolidation (RECOMMENDED)
  python3 train.py train --mode spacy --epochs 200 --consolidate

  # Train without consolidation
  python3 train.py train --mode spacy --epochs 200

  # Consolidate separately
  python3 train.py consolidate --output data/training/spacy_training_data.json

  # Enhance training data
  python3 train.py enhance --input data/training/spacy_training_data.json

  # Add house/road examples
  python3 train.py add-examples
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Train command
    train_parser = subparsers.add_parser('train', help='Train model')
    train_parser.add_argument('--mode', choices=['m4', 'pytorch-cpu', 'spacy'], default='m4',
                             help='Training mode (default: m4)')
    train_parser.add_argument('--data', default=str(project_root / 'data' / 'raw' / 'merged_addresses.json'),
                             help='Path to training data')
    train_parser.add_argument('--epochs', type=int, default=50, help='Number of epochs')
    train_parser.add_argument('--output', default=str(project_root / 'models' / 'training' / 'outputs' / 'trained_model'),
                             help='Output directory')
    train_parser.add_argument('--test', action='store_true', help='Test mode')
    train_parser.add_argument('--consolidate', action='store_true',
                             help='Auto-consolidate training datasets before training')
    train_parser.add_argument('--consolidate-input', nargs='+',
                             default=[str(project_root / 'data' / 'training' / 'spacy_training_data.json'),
                                     str(project_root / 'data' / 'training' / 'spacy_training_data_enhanced.json')],
                             help='Input files for consolidation')
    train_parser.add_argument('--consolidate-output', 
                             default=str(project_root / 'data' / 'training' / 'spacy_training_data.json'),
                             help='Output file for consolidated data')
    
    # Enhance command
    enhance_parser = subparsers.add_parser('enhance', help='Enhance training data')
    enhance_parser.add_argument('--input', default=str(project_root / 'data' / 'training' / 'spacy_training_data.json'),
                               help='Input training data file')
    enhance_parser.add_argument('--output', default=str(project_root / 'data' / 'training' / 'spacy_training_data_enhanced.json'),
                               help='Output enhanced data file')
    
    # Add examples command
    add_parser = subparsers.add_parser('add-examples', help='Add house/road pattern examples')
    add_parser.add_argument('--output', default=str(project_root / 'data' / 'training' / 'spacy_training_data.json'),
                          help='Training data file to update')
    
    # Consolidate command
    consolidate_parser = subparsers.add_parser('consolidate', help='Consolidate training datasets')
    consolidate_parser.add_argument('--input', nargs='+', 
                                    default=[str(project_root / 'data' / 'training' / 'spacy_training_data.json'),
                                            str(project_root / 'data' / 'training' / 'spacy_training_data_enhanced.json')],
                                    help='Input training data files')
    consolidate_parser.add_argument('--output', default=str(project_root / 'data' / 'training' / 'spacy_training_data.json'),
                                   help='Output consolidated data file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'train':
        cmd_train(args)
    elif args.command == 'enhance':
        cmd_enhance(args)
    elif args.command == 'add-examples':
        cmd_add_examples(args)
    elif args.command == 'consolidate':
        cmd_consolidate(args)


if __name__ == "__main__":
    main()
