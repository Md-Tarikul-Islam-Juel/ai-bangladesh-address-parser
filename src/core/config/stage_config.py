"""Stage configuration loader"""

import json
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def load_stage_config(stage_config: Optional[Dict] = None) -> Dict:
    """Load stage configuration from dict or JSON file"""
    default_config = {
        'stage_1_script_detection': True,
        'stage_2_normalization': True,  # Always True (essential)
        'stage_3_4_fsm_parsing': True,
        'stage_5_regex_extraction': True,  # Always True (essential)
        'stage_6_spacy_ner': True,
        'stage_7_gazetteer': True,
        'stage_7_5_geographic': True,  # Geographic Intelligence & Validation
        'stage_8_conflict_resolution': True,  # Always True (essential)
        'stage_9_output': True,  # Always True (essential)
    }
    
    # If config provided directly, use it
    if stage_config:
        # Merge with defaults
        config = default_config.copy()
        config.update(stage_config)
        return config
    
    # Try to load from config file
    # Go up from src/core/config/ -> src/core/ -> src/ -> root/ -> config/
    config_file = Path(__file__).parent.parent.parent.parent / "config" / "stage_config.json"
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                # Extract stage settings
                if 'stages' in file_config:
                    config = default_config.copy()
                    for stage_key, stage_data in file_config['stages'].items():
                        if stage_key in config:
                            config[stage_key] = stage_data.get('enabled', True)
                    return config
        except Exception as e:
            logger.warning(f"Could not load config file: {e}, using defaults")
    
    return default_config
