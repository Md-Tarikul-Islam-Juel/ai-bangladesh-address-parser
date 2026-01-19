"""Stage 1: Script & Language Detection"""

from typing import Dict
from ..utils.types import ScriptType


class ScriptDetector:
    """Detect Bangla/English/Mixed scripts"""
    
    def detect(self, address: str) -> Dict:
        """Detect script type and segment address"""
        if not address:
            return {
                'is_mixed': False,
                'primary_script': ScriptType.NEUTRAL,
                'bangla_ratio': 0.0,
                'english_ratio': 0.0
            }
        
        bangla_chars = sum(1 for c in address if '\u0980' <= c <= '\u09FF')
        english_chars = sum(1 for c in address if c.isalpha() and ord(c) < 128)
        total_chars = len(address)
        
        bangla_ratio = bangla_chars / total_chars if total_chars > 0 else 0.0
        english_ratio = english_chars / total_chars if total_chars > 0 else 0.0
        
        if bangla_ratio > 0.3 and english_ratio > 0.3:
            primary = ScriptType.MIXED
        elif bangla_ratio > english_ratio:
            primary = ScriptType.BANGLA
        else:
            primary = ScriptType.ENGLISH
        
        return {
            'is_mixed': primary == ScriptType.MIXED,
            'primary_script': primary,
            'bangla_ratio': bangla_ratio,
            'english_ratio': english_ratio
        }
