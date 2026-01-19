#!/usr/bin/env python3
"""
Stage Control Script
====================

Control which processing stages are enabled/disabled in the address extraction system.

Usage:
    # Enable/disable specific stages
    python tools/control_stages.py --disable fsm spacy --enable gazetteer
    
    # Use a performance profile
    python scripts/control_stages.py --profile fast
    
    # Show current configuration
    python scripts/control_stages.py --show
    
    # Test with custom config
    python scripts/control_stages.py --test "House 12, Road 5, Mirpur, Dhaka"
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.core import ProductionAddressExtractor

# Stage mapping
STAGE_MAP = {
    'script': 'stage_1_script_detection',
    'fsm': 'stage_3_fsm_parsing',
    'spacy': 'stage_5_spacy_ner',
    'gazetteer': 'stage_6_gazetteer',
    'geographic': 'stage_7_geographic',
    'all': ['stage_1_script_detection', 'stage_3_fsm_parsing', 'stage_5_spacy_ner', 'stage_6_gazetteer', 'stage_7_geographic']
}

# Performance profiles
PROFILES = {
    'fast': {
        'stage_1_script_detection': False,
        'stage_3_fsm_parsing': False,
        'stage_5_spacy_ner': False,
        'stage_6_gazetteer': False,
        'stage_7_geographic': False
    },
    'balanced': {
        'stage_1_script_detection': False,
        'stage_3_fsm_parsing': False,
        'stage_5_spacy_ner': True,
        'stage_6_gazetteer': True,
        'stage_7_geographic': True
    },
    'accurate': {
        'stage_1_script_detection': True,
        'stage_3_fsm_parsing': True,
        'stage_5_spacy_ner': True,
        'stage_6_gazetteer': True,
        'stage_7_geographic': True
    },
    'minimal': {
        'stage_1_script_detection': False,
        'stage_3_fsm_parsing': False,
        'stage_5_spacy_ner': False,
        'stage_6_gazetteer': False,
        'stage_7_geographic': False
    }
}

def load_config_file():
    """Load configuration from JSON file"""
    config_file = project_root / "config" / "stage_config.json"
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Remove metadata if present
            if '_metadata' in data:
                data = {k: v for k, v in data.items() if k != '_metadata'}
            return data
    return None

def save_config_file(config: dict):
    """Save configuration to JSON file (simplified flat format)"""
    config_file = project_root / "config" / "stage_config.json"
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing or create new
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Preserve metadata if present
            metadata = data.get('_metadata', {})
    else:
        data = {}
        metadata = {
            "description": "Stage enable/disable configuration",
            "mandatory_stages": [
                "stage_2_normalization",
                "stage_4_regex_extraction",
                "stage_8_conflict_resolution",
                "stage_9_output"
            ],
            "optional_stages": [
                "stage_1_script_detection",
                "stage_3_fsm_parsing",
                "stage_5_spacy_ner",
                "stage_6_gazetteer",
                "stage_7_geographic"
            ]
        }
    
    # Remove metadata from data before updating
    if '_metadata' in data:
        del data['_metadata']
    
    # Update stage settings (simplified flat format)
    data.update(config)
    
    # Ensure mandatory stages are always enabled
    mandatory_stages = ['stage_2_normalization', 'stage_4_regex_extraction', 
                       'stage_8_conflict_resolution', 'stage_9_output']
    for stage in mandatory_stages:
        data[stage] = True
    
    # Add metadata back
    data['_metadata'] = metadata
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Configuration saved to: {config_file}")

def show_config():
    """Show current configuration"""
    config_file = project_root / "config" / "stage_config.json"
    
    print("=" * 80)
    print("CURRENT STAGE CONFIGURATION")
    print("=" * 80)
    print()
    
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract metadata
        metadata = data.get('_metadata', {})
        mandatory_stages = metadata.get('mandatory_stages', [
            'stage_2_normalization',
            'stage_4_regex_extraction',
            'stage_8_conflict_resolution',
            'stage_9_output'
        ])
        
        # Filter out metadata from config
        config = {k: v for k, v in data.items() if k != '_metadata'}
        
        print("MANDATORY STAGES (always enabled):")
        print("-" * 80)
        for stage_key in sorted(mandatory_stages):
            if stage_key in config:
                enabled = "✓ ENABLED" if config.get(stage_key, True) else "✗ DISABLED"
                print(f"  {stage_key:35s} {enabled:12s} (MANDATORY)")
        print()
        
        print("OPTIONAL STAGES (can be disabled):")
        print("-" * 80)
        optional_stages = [k for k in sorted(config.keys()) if k not in mandatory_stages]
        for stage_key in optional_stages:
            enabled = "✓ ENABLED" if config.get(stage_key, True) else "✗ DISABLED"
            print(f"  {stage_key:35s} {enabled:12s} (OPTIONAL)")
        print()
    else:
        print("No configuration file found. Using defaults (all stages enabled).")
        print()
        print("Default Configuration:")
        print("-" * 80)
        default_stages = {
            'stage_1_script_detection': True,
            'stage_2_normalization': True,
            'stage_3_fsm_parsing': True,
            'stage_4_regex_extraction': True,
            'stage_5_spacy_ner': True,
            'stage_6_gazetteer': True,
            'stage_7_geographic': True,
            'stage_8_conflict_resolution': True,
            'stage_9_output': True
        }
        for stage, enabled in default_stages.items():
            status = "✓ ENABLED" if enabled else "✗ DISABLED"
            print(f"  {stage:30s} {status}")
        print()

def apply_profile(profile_name: str):
    """Apply a performance profile"""
    if profile_name not in PROFILES:
        print(f"❌ Error: Unknown profile '{profile_name}'")
        print(f"Available profiles: {', '.join(PROFILES.keys())}")
        return False
    
    profile = PROFILES[profile_name]
    save_config_file(profile)
    print(f"✓ Applied profile: {profile_name}")
    return True

def enable_stages(stage_names: list):
    """Enable specified stages"""
    config = {}
    for name in stage_names:
        if name == 'all':
            for stage in STAGE_MAP['all']:
                config[stage] = True
        elif name in STAGE_MAP:
            stage_key = STAGE_MAP[name]
            config[stage_key] = True
        else:
            print(f"⚠ Warning: Unknown stage '{name}' (skipping)")
    
    if config:
        save_config_file(config)
        print(f"✓ Enabled stages: {', '.join(stage_names)}")
    return True

def disable_stages(stage_names: list):
    """Disable specified stages"""
    config = {}
    for name in stage_names:
        if name == 'all':
            for stage in STAGE_MAP['all']:
                config[stage] = False
        elif name in STAGE_MAP:
            stage_key = STAGE_MAP[name]
            config[stage_key] = False
        else:
            print(f"⚠ Warning: Unknown stage '{name}' (skipping)")
    
    if config:
        save_config_file(config)
        print(f"✓ Disabled stages: {', '.join(stage_names)}")
    return True

def test_extraction(address: str, config: dict = None):
    """Test extraction with current or custom configuration"""
    print("=" * 80)
    print("TESTING ADDRESS EXTRACTION")
    print("=" * 80)
    print()
    print(f"Address: {address}")
    print()
    
    # Load data path if available
    data_path = project_root / "data" / "merged_addresses.json"
    data_path_str = str(data_path) if data_path.exists() else None
    
    # Create extractor with custom config
    extractor = ProductionAddressExtractor(
        data_path=data_path_str,
        stage_config=config
    )
    
    # Extract
    result = extractor.extract(address, detailed=True)
    
    print("Extracted Components:")
    print("-" * 80)
    for comp, value in result['components'].items():
        if value:
            print(f"  {comp:20s} = {value}")
    print()
    
    print(f"Overall Confidence: {result['overall_confidence']:.1%}")
    print(f"Extraction Time: {result['extraction_time_ms']:.2f}ms")
    
    if 'metadata' in result and 'enabled_stages' in result['metadata']:
        print(f"Enabled Stages: {', '.join(result['metadata']['enabled_stages'])}")
    
    print()

def main():
    parser = argparse.ArgumentParser(
        description='Control which processing stages are enabled/disabled',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show current configuration
  python scripts/control_stages.py --show
  
  # Disable FSM and spaCy NER
  python scripts/control_stages.py --disable fsm spacy
  
  # Enable gazetteer
  python scripts/control_stages.py --enable gazetteer
  
  # Use fast profile
  python scripts/control_stages.py --profile fast
  
  # Test with custom config
  python scripts/control_stages.py --test "House 12, Road 5, Mirpur, Dhaka"
  
  # Custom configuration
  python scripts/control_stages.py --config '{"stage_6_spacy_ner": false}'
        """
    )
    
    parser.add_argument('--show', action='store_true', help='Show current configuration')
    parser.add_argument('--enable', nargs='+', help='Enable stages (script, fsm, spacy, gazetteer, all)')
    parser.add_argument('--disable', nargs='+', help='Disable stages (script, fsm, spacy, gazetteer, all)')
    parser.add_argument('--profile', choices=list(PROFILES.keys()), help='Apply performance profile')
    parser.add_argument('--test', help='Test extraction with address string')
    parser.add_argument('--config', help='Custom JSON configuration')
    
    args = parser.parse_args()
    
    if args.show:
        show_config()
    elif args.profile:
        apply_profile(args.profile)
    elif args.enable:
        enable_stages(args.enable)
    elif args.disable:
        disable_stages(args.disable)
    elif args.test:
        config = None
        if args.config:
            config = json.loads(args.config)
        test_extraction(args.test, config)
    elif args.config:
        config = json.loads(args.config)
        save_config_file(config)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
