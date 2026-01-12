#!/usr/bin/env python3
"""Check ML/spaCy Status"""

print("Checking ML Status...")
print("=" * 80)

# Check spaCy installation
try:
    import spacy
    print("✅ spaCy is installed:", spacy.__version__)
    spacy_installed = True
except ImportError:
    print("❌ spaCy is NOT installed")
    print("   Install: pip3 install spacy")
    spacy_installed = False

# Check model
from pathlib import Path
model_path = Path(__file__).parent / "models" / "address_ner_model"
if model_path.exists():
    print(f"✅ ML model exists at: {model_path}")
    
    if spacy_installed:
        try:
            nlp = spacy.load(str(model_path))
            print(f"✅ ML model loaded successfully!")
            print(f"   Model has {len(nlp.pipe_names)} pipeline components")
            print(f"   Components: {nlp.pipe_names}")
            
            # Test extraction
            test_text = "Flat A-3, Building 7, Bashundhara R/A, Dhaka"
            doc = nlp(test_text)
            if doc.ents:
                print(f"\n✅ ML is WORKING! Found {len(doc.ents)} entities in test:")
                for ent in doc.ents:
                    print(f"   - {ent.text:20} → {ent.label_}")
            else:
                print("\n⚠️  ML loaded but found no entities in test")
                
        except Exception as e:
            print(f"❌ Could not load ML model: {e}")
else:
    print(f"❌ ML model does NOT exist at: {model_path}")
    print("   Train it: python3 train_spacy_model.py")

print("\n" + "=" * 80)
print("Testing Production System...")
print("=" * 80)

try:
    from production_address_extractor import ProductionAddressExtractor
    
    extractor = ProductionAddressExtractor(
        data_path="../main/Processed data/merged_addresses.json"
    )
    
    if hasattr(extractor, 'spacy_ner') and extractor.spacy_ner.enabled:
        print("✅ Production system has ML ENABLED!")
    else:
        print("❌ Production system has ML DISABLED")
        print("   The SpacyNERExtractor might have failed to initialize")
        
except Exception as e:
    print(f"❌ Error loading production system: {e}")

print("=" * 80)
