"""Component confidence thresholds configuration loader"""

import json
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


def load_component_thresholds(thresholds: Optional[Dict] = None) -> Dict[str, float]:
    """
    Load component confidence thresholds from dict or JSON file
    
    Args:
        thresholds: Dictionary with component thresholds (optional)
    
    Returns:
        Dictionary mapping component names to minimum confidence thresholds
    """
    default_thresholds = {
        'house_number': 0.70,
        'road': 0.70,
        'area': 0.65,
        'district': 0.75,
        'division': 0.80,
        'postal_code': 0.80,
        'flat_number': 0.70,
        'floor_number': 0.70,
        'block_number': 0.70
    }
    
    # If thresholds provided directly, use it
    if thresholds:
        config = default_thresholds.copy()
        config.update(thresholds)
        return config
    
    # Try to load from config file
    # Go up from src/core/config/ -> src/core/ -> src/ -> root/ -> config/
    config_file = Path(__file__).parent.parent.parent.parent / "config" / "component_thresholds.json"
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                # Merge with defaults
                config = default_thresholds.copy()
                for component, threshold in file_config.items():
                    if component in config:
                        # Validate threshold is between 0 and 1
                        threshold_float = float(threshold)
                        if 0.0 <= threshold_float <= 1.0:
                            config[component] = threshold_float
                        else:
                            logger.warning(f"Invalid threshold for {component}: {threshold_float} (must be 0.0-1.0), using default")
                return config
        except Exception as e:
            logger.warning(f"Could not load component thresholds file: {e}, using defaults")
    
    return default_thresholds
