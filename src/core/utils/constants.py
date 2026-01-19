"""Constants and feature flags"""

# Try to import Trie for optimized gazetteer lookup
try:
    import pygtrie
    TRIE_AVAILABLE = True
except ImportError:
    TRIE_AVAILABLE = False

# Try to import spaCy for ML-based NER
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

# Check if regex processors are available
import sys
from pathlib import Path

REGEX_AVAILABLE = False
try:
    # Go up from src/core/utils/constants.py -> src/core/utils/ -> src/core/ -> src/
    # Then import from src.regex
    src_path = Path(__file__).parent.parent.parent  # src/
    project_root = src_path.parent  # root/
    
    # Add both project root and src to path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    # Import from src.regex (not just regex)
    from src.regex.house_number_processor import AdvancedHouseNumberExtractor
    from src.regex.road_processor import AdvancedRoadNumberExtractor
    from src.regex.area_processor import AdvancedAreaExtractor
    from src.regex.district_processor import AdvancedCityExtractor
    from src.regex.postal_code_processor import AdvancedPostalCodeExtractor
    from src.regex.flat_number_processor import AdvancedFlatNumberExtractor
    from src.regex.floor_number_processor import AdvancedFloorNumberExtractor
    from src.regex.block_processor import AdvancedBlockNumberExtractor
    REGEX_AVAILABLE = True
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.debug(f"Regex processors not available: {e}")
    REGEX_AVAILABLE = False

# Check if offline geo is available
try:
    from src.geo.bangladesh_geo_offline import BangladeshOfflineGeo
    OFFLINE_GEO_AVAILABLE = True
except ImportError:
    OFFLINE_GEO_AVAILABLE = False
