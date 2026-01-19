#!/usr/bin/env python3
"""
Unified Regex Patterns for Address Extraction
============================================

This file contains all regex patterns used for extracting address components.
Patterns are organized by component type and confidence level.

Used by:
- Training script for enhanced data preparation
- Regex processors for extraction
"""

from typing import List, Tuple

# ============================================================================
# HOUSE NUMBER PATTERNS
# ============================================================================

HOUSE_EXPLICIT_PATTERNS: List[Tuple[str, float]] = [
    # Hash notation with complex patterns
    (r'(h#[\s]*[A-Z]{1,3}[\s]+[\d০-৯]+[a-zA-Z0-9/\-&\s]*?)(?=\s*[,\(]|\s*$)', 0.98),
    (r'(h#[\s]*[A-Z]{0,3}[\s]*[\d০-৯]+[a-zA-Z0-9/\-&\s]*?)(?=\s*[,\(]|\s*$)', 0.98),
    # House# with letter+number
    (r'((?:house|home)[#][\s]*[A-Za-z][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(house#[\s]*[\d০-৯]+[a-zA-Z0-9/\-&\s]*?)(?=\s*[,\(]|\s*$)', 0.98),
    (r'(home#[\s]*[\d০-৯]+[a-zA-Z0-9/\-&]*)', 0.98),
    # H:51 pattern
    (r'\bh:[\s]*([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    # H # 1 pattern
    (r'\b(h\s+#\s*[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    # Letter hash number pattern
    (r'\b([A-Z]#[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    # H@ pattern
    (r'\b[hH]@[\s]*([\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    # H- patterns with slash
    (r'\b[hH][\s-]+([\d০-৯]+[/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'^h[\s-]+([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'\b[hH][\s-]+([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    # H with number (no dash)
    (r'\b[hH][\s]*([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    # H 30/B pattern
    (r'\bh\s+([\d০-৯]+[/\-][a-zA-Z\d]+)(?=\s*[,\(\)]|\s|$)', 0.98),
    # Banglish alphabet patterns
    (r'((?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]*[-/]?[\s]*[\d০-৯]+[/\-][\d০-৯]+[/\-][a-zA-Z\d]+)', 0.98),
    (r'((?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]+[\d০-৯]+[/\-][a-zA-Z\d]+)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]+[\d০-৯]+[/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]*[-/][\s]*[\d০-৯]+[/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]*[/][\s]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[\s]*[-/]?[\s]*[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    # Building number patterns
    (r'(?:building|bldg)[\s]+(?:no\.?|number|#)[\s\-:]*([\d০-৯]{1,5}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:building|bldg)[\s]+([\d০-৯]{1,5}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:building|bldg)[\s-]+([\d০-৯]{1,5}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    # Plot number patterns
    (r'(?:plot)[\s]+(?:no\.?|number|#|:)[\s-]*([\d০-৯]+[\s]*&[\s]*[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:plot)[\s]+(?:no\.?|number|#|:)[\s-]*([\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?[\(]?[a-zA-Z\d]?[\)]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:plot)[\s]+#[\s]*[\d০-৯]+[/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:plot)[\s]+([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:plot)[\s-]+([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    # Holding number patterns
    (r'(?:holding)[\s]+(?:no\.?|number|#)[\s:]*[\s-]*([\d০-৯]+[/\-][a-zA-Z\d]+[/\-][\d০-৯]+[/\-][a-zA-Z\d]+)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:holding)[\s]+(?:no\.?|number|#)[\s:]*[\s-]*([\d০-৯]+[/\-]?[a-zA-Z\d/]+)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:holding)[\s]+(?:no\.?|number|#)[\s:]*[\s-]*([A-Za-z][\s-]*[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:holding)[\s]+no-[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:holding)[\s]+(?:no\.?|number|#)[\s]+new[\s:]*[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    # House with multiple numbers
    (r'(?:house|home|hous|bari|basha)[\s:]*(\d+[\s]*[+&][\s]*\d+)', 0.98),
    (r'(?:house|home|hous|bari|basha)[\s:]*(\d+[\s]*[-][\s]*\d+)', 0.98),
    # House No. patterns
    (r'(?:house|home|hous|bari|basha)[\s]+(?:no\.?|number|#)[\s-]*([\d০-৯]{1,5}[\s]*,[\s]*[\d০-৯]{1,5}[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:house|home|hous|bari|basha)[\s]+(?:no\.?|number|#)[\s-]*([\d০-৯]{1,5}[\s]*,[\s]*[\d০-৯]{1,5})(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:house|home|hous|bari|basha)[\s]+(?:no\.?|number)[\s]*#[\s]*[\d০-৯]{1,5}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:house|home|hous|bari|basha)[\s]+(?:no\.?|number|#)[\s-]*([\d০-৯]{1,5}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:house|home|hous|bari|basha)[\s]+(?:no\.?|number|#)[\s:]*[\d০-৯]{1,5}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:house|home|hous|bari|basha)[\s]+(?:no\.?|number|#)[\s-]*[A-Za-z][/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:house|home|hous|bari|basha)[\s]+(?:no\.?|number|#)[\s-]*[A-Za-z][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:house|home|hous|bari|basha)[\s-]+([\d০-৯]{1,5}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:house|home|hous|bari|basha)[\s]+-[\s]*[\d০-৯]{1,5}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:house|home|hous|bari|basha)[\s]*:[\s]*[\d০-৯]+[/\-]?[A-Za-z]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:house|home|hous|bari|basha)[\s]+[A-Za-z][/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:house|home|hous|bari|basha)[\s]+[A-Za-z][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:house|home|hous|bari|basha)[\s]+([\d০-৯]{1,5}[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:house|home|hous|bari|basha)[\s]+[\d০-৯]+[/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    # House with 3-part slash patterns
    (r'(?:house|home|hous|bari|basha)[\s:]*(\d+/\d+/[a-zA-Z0-9]+)', 0.98),
    (r'(?:house|home|hous|bari|basha)[\s:]*(\d+/\d+)', 0.98),
    (r'(?:house|home|hous|bari|basha)[\s:]*(\d+/[a-zA-Z]+)', 0.98),
    # Basa/Basha patterns
    (r'(?:basa|basha)[\s]*([\d০-৯]+[/\-]\d+(?:[/\-][a-zA-Z0-9]+)?)', 0.98),
    (r'(?:basa|basha)[\s]+(?:no\.?|number|#)[\s-]*([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    # Number before "No House"
    (r'([\d০-৯]+[a-zA-Z]?)[\s]+no\s+house(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'([\d০-৯]+[a-zA-Z]?)[\s]+no\s+basa(?=\s*[,\(\)]|\s|$)', 0.98),
    # Simple house patterns
    (r'(?:house|home|hous|hose|hause)[\s:]*([\d০-৯]{1,5})(?=\s*[,\(\)]|\s|$)', 0.96),
]

HOUSE_SLASH_PATTERNS: List[Tuple[str, float]] = [
    (r'(\d+[/\-]\d+[-]\d+)\s*[,\s]', 0.95),
    (r'(\d+[/\-]\d+[\s]+(?:kha|ka|gh|ja|cho|kh|k|ga|g|cha|ch)[a-z]?)(?=\s*[,\(\)]|\s|$)', 0.95),
    (r'(\d+[/\-]\d+[a-zA-Z]?[\(]?[a-zA-Z\d]?[\)]?)(?=\s*[,\(\)]|\s|$)', 0.93),
    (r'(\d+[/\-][A-Z][/\-]\d+[/\-]\d+)\s*[,\s]', 0.95),
    (r'(\d+[/\-]\d+[/\-][A-Z][/\-]\d+)\s*[,\s]', 0.95),
    (r'(\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?)\s*[,\s]', 0.95),
    (r'(\d+[/\-]\d+[/\-][A-Za-z]+)\s*[,\s]', 0.93),
    (r'(\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?[/\-][A-Z])\s*[,\s]', 0.93),
    (r'(\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?)\s*[,\s]', 0.93),
    (r'(\d+[/\-][A-Za-z][/\-]\d+[a-zA-Z]?)\s*[,\s]', 0.93),
    (r'(\d+[/\-]\d+[/\-][A-Za-z])(?=\s*[,\(\)]|\s|$)', 0.93),
    (r'(\d+[/\-]\d+[/\-][A-Za-z][\s-]*\d+[a-zA-Z]?)(?=\s*[,\s\.]|$)', 0.93),
    (r'(\d+[/\-][A-Za-z][/\-][A-Za-z])\s*[,\s]', 0.93),
    (r'(\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?\s+[A-Z])(?=\s|,|$)', 0.95),
    (r'(\d+[a-zA-Z]?[/\-]\d+[a-zA-Z]?)\s*[,\s]', 0.90),
    (r'(\d+[a-zA-Z]?[/\-][a-zA-Z]+)\s*[,\s]', 0.90),
]

# ============================================================================
# ROAD NUMBER PATTERNS
# ============================================================================

ROAD_EXPLICIT_PATTERNS: List[Tuple[str, float]] = [
    # Line patterns
    (r'((?:line|Line|LINE)[\s]*#[\s]*[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),
    (r'((?:line|Line|LINE)[\s-]+[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),
    # Lane patterns
    (r'([\d]+(?:st|nd|rd|th)[\s]+(?:lane|Lane|LANE))(?=\s*[,\(\)]|\s|$)', 1.00),
    (r'((?:lane|Lane|LANE)[\s]+(?:no\.?|number|#)?[\s]*[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:lane|Lane|LANE)[\s-]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'([A-Z][a-zA-Z\s]{2,}(?:Lane|LANE))(?=\s*[,\(\)]|\s|$)', 1.00),
    (r'((?:lane|Lane|LANE)[\s]*(?:no\.?|number)?[\s]*:[\s]*[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 1.00),
    # Avenue patterns
    (r'([A-Z][a-zA-Z\s]{3,}(?:Avenue|AVENUE))(?=\s*[,\(\)]|\s|$)', 1.00),
    (r'((?:avenue|Avenue|AVENUE)[\s]+[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),
    (r'((?:avenue|Avenue|AVENUE)[\s-]+[\d০-৯]+)(?=\s*[,\(\)]|\s|$)', 1.00),
    # Named roads
    (r'([A-Z][a-zA-Z\s]{10,}(?:Road|Rd|ROAD|RD))(?=\s*[/,(]|\s|$)', 0.95),
    (r'([A-Z][a-zA-Z\s]{2,}(?:Road|Rd|ROAD|RD))(?=\s*[,\(\)]|\s|$)', 0.95),
    (r'([A-Z]\.[A-Z][\s]+(?:Road|Rd|ROAD|RD))(?=\s*[,\(\)]|\s|$)', 1.00),
    # Street patterns
    (r'([A-Z][a-zA-Z\s]{5,}(?:Street|STREET))(?=\s*[,\(\)]|\s|$)', 1.00),
    (r'([A-Z][a-zA-Z\s]{5,}(?:Street|STREET)[\s]+(?:Lane|LANE))(?=\s*[,\(\)]|\s|$)', 1.00),
    # Road No patterns
    (r'((?:road|rd|Road|Rd|ROAD|RD)[\s]+(?:no\.?|number|#)[\s]*#[\s]*[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:road|rd|Road|Rd|ROAD|RD)[\s]*#[\s]*[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:road|rd|Road|Rd|ROAD|RD)[\s]+(?:no\.?|number|#)[\s:]*[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:road|rd|Road|Rd|ROAD|RD)[\s:]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:road|rd|Road|Rd|ROAD|RD)[\s]+(?:no\.?|number|#)[\s-]*[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:road|rd|Road|Rd|ROAD|RD)[\s]+(?:no\.?|number|#)[\s-]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:road|rd|Road|Rd|ROAD|RD)[\s]+(?:number|Number|NUMBER)[\s-]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:road|rd|Road|Rd|ROAD|RD)[\s-]+[Nn]?[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:road|rd|Road|Rd|ROAD|RD)[\s]*#[\s]*[\d০-৯A-Z]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    # R patterns
    (r'\b((?:rd|Rd|RD)\.?[\s]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'\b((?:rd|Rd|RD)[\s-]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'\b[rR]@[\s]*([\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?<!h-)(?<!H-)(?<!h\s)(?<!H\s)\b[rR][\s-]+([\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'\b[rR]:[\s]*([\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'\b[rR]\s*#\s*(0?[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'\b[rR][\s]+([\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    # Road with number
    (r'((?:road|rd|Road|Rd|ROAD|RD)[\s]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
]

ROAD_SLASH_PATTERNS: List[Tuple[str, float]] = [
    (r'(?:road|rd|Road|Rd|ROAD|RD)[\s-]+([\d০-৯]+[/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.93),
    (r'\b((?:r|R)[\s-]+[\d০-৯]+[/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.93),
    (r'(?:road|rd|Road|Rd|ROAD|RD)[\s]+([\d০-৯]+[/\-][\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.93),
]

ROAD_BANGLA_PATTERNS: List[Tuple[str, float]] = [
    (r'([\u0980-\u09FF\s]{3,}রোড)(?=\s*[,\(\)]|\s|$)', 1.00),
    (r'([\u0980-\u09FF\s]{3,}লেন)(?=\s*[,\(\)]|\s|$)', 1.00),
    (r'([\d]+(?:st|nd|rd|th)[\s]+len)(?=\s*[,\(\)]|\s|$)', 1.00),
    (r'([\u0980-\u09FF]+[\s]+গলি)(?=\s*[,\(\)]|\s|$)', 1.00),
    (r'(রোড[\s]+নং[\s]*[\d০-৯]+[/\-]?[\d০-৯]*[\u0980-\u09FFa-zA-Z]?)(?=\s*\(|\s*[,]|\s|$|[\u0980-\u09FF])', 1.00),
    (r'(রোড[\s]+নাম্বার[\s]*[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,]|\s|$)', 1.00),
    (r'(রোড[\s]+নম্বর[\s]*[\d০-৯]+[/\-]?[\d০-৯]*[\u0980-\u09FFa-zA-Z]?)(?=\s*[,]|\s|$)', 1.00),
    (r'([\d০-৯]+[\s]+রোড)(?=\s*[,]|\s|$)', 1.00),
    (r'(রোড[\s]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,]|\s|$)', 1.00),
    (r'((?:লেন|লেইন)[\s]*:[\s]*[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,]|\s|$)', 1.00),
    (r'((?:লেন|লেইন)[\s-]+[\d০-৯]+[/\-]?[\d০-৯]*[a-zA-Z]?)(?=\s*[,]|\s|$)', 1.00),
]

# ============================================================================
# POSTAL CODE PATTERNS
# ============================================================================

POSTAL_EXPLICIT_PATTERNS: List[Tuple[str, float]] = [
    (r'(?:Post|POST|পোস্ট)[\s:]+G\.?P\.?O\.?[\s]+([\d০-৯]{4})', 1.00),
    (r'(?:Post|POST|পোস্ট)[\s:]+([\d০-৯]{4})', 1.00),
    (r'(?:Post\s+Office|Post\s+office|POST\s+OFFICE|পোস্ট\s+অফিস)[\s:]+(?:G\.?P\.?O\.?[\s]+)?([\d০-৯]{4})', 1.00),
    (r'P\.?O\.?[\s:]+(?:G\.?P\.?O\.?[\s]+)?([\d০-৯]{4})', 1.00),
    (r'(?:Postal\s+Code|Postal\s+code|POSTAL\s+CODE|পোস্টাল\s+কোড)[\s:]+([\d০-৯]{4})', 1.00),
    (r'(?:Zip|ZIP|zip|জিপ)[\s:]+([\d০-৯]{4})', 0.98),
    (r'(?:Pin\s+Code|PIN\s+CODE|pin\s+code)[\s:]+([\d০-৯]{4})', 0.98),
]

POSTAL_CITY_DASH_PATTERNS: List[Tuple[str, float]] = [
    # City-dash patterns (e.g., "Dhaka-1216", "Chittagong-4000")
    (r'(?:Dhaka|Mirpur|Uttara|Gulshan|Banani|Dhanmondi|Chittagong|Chattogram|Sylhet|Rajshahi|Khulna|Barisal|Rangpur|Mymensingh|Comilla|Gazipur|Narayanganj|Savar|Tongi|Narsingdi|Manikganj|Munshiganj|Kishoreganj|Tangail|Jamalpur|Sherpur|Netrokona|Bogura|Joypurhat|Naogaon|Natore|Chapainawabganj|Pabna|Sirajganj|Jessore|Jhenaidah|Magura|Narail|Kushtia|Meherpur|Chuadanga|Bagerhat|Pirojpur|Barguna|Patuakhali|Jhalokathi|Bandarban|Brahmanbaria|Chandpur|Feni|Khagrachhari|Lakshmipur|Noakhali|Rangamati|Cox|Coxs|Bazar)[\s-]+([\d০-৯]{4})', 0.95),
]

# ============================================================================
# FLAT NUMBER PATTERNS
# ============================================================================

FLAT_EXPLICIT_PATTERNS: List[Tuple[str, float]] = [
    (r'(?:flat|Flat|FLAT)[\s]+(?:no\.?|number|#)[\s-]*([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:flat|Flat|FLAT)[\s-]+([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:flat|Flat|FLAT)[\s]+([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:flat|Flat|FLAT)[\s]*:[\s]*[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'((?:flat|Flat|FLAT)[\s]*#[\s]*[\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
]

# ============================================================================
# FLOOR NUMBER PATTERNS
# ============================================================================

FLOOR_EXPLICIT_PATTERNS: List[Tuple[str, float]] = [
    (r'(?:floor|Floor|FLOOR)[\s]+(?:no\.?|number|#)[\s-]*([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:floor|Floor|FLOOR)[\s-]+([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:floor|Floor|FLOOR)[\s]+([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:level|Level|LEVEL)[\s]+([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:lift|Lift|LIFT)[\s-]+([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
]

# ============================================================================
# BLOCK NUMBER PATTERNS
# ============================================================================

BLOCK_EXPLICIT_PATTERNS: List[Tuple[str, float]] = [
    (r'(?:block|Block|BLOCK)[\s]+(?:no\.?|number|#)[\s-]*([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:block|Block|BLOCK)[\s-]+([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:block|Block|BLOCK)[\s]+([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:sector|Sector|SECTOR)[\s]+(?:no\.?|number|#)[\s-]*([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:sector|Sector|SECTOR)[\s-]+([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
    (r'(?:blk|Blk|BLK)[\s-]+([\d০-৯]+[a-zA-Z]?)(?=\s*[,\(\)]|\s|$)', 0.98),
]

# ============================================================================
# AREA PATTERNS (Simplified - area extraction is more complex)
# ============================================================================

AREA_EXPLICIT_PATTERNS: List[Tuple[str, float]] = [
    # Area patterns are context-dependent and use geographic data
    # This is a simplified set for training
    (r'(?:area|Area|AREA)[\s]+([A-Za-z\u0980-\u09FF\s]{2,})(?=\s*[,\(\)]|\s|$)', 0.85),
]

# ============================================================================
# ALL PATTERNS BY COMPONENT
# ============================================================================

ALL_PATTERNS = {
    'house': HOUSE_EXPLICIT_PATTERNS + HOUSE_SLASH_PATTERNS,
    'road': ROAD_EXPLICIT_PATTERNS + ROAD_SLASH_PATTERNS + ROAD_BANGLA_PATTERNS,
    'postal': POSTAL_EXPLICIT_PATTERNS + POSTAL_CITY_DASH_PATTERNS,
    'flat': FLAT_EXPLICIT_PATTERNS,
    'floor': FLOOR_EXPLICIT_PATTERNS,
    'block': BLOCK_EXPLICIT_PATTERNS,
    'area': AREA_EXPLICIT_PATTERNS,
}
