from typing import Dict, Any, List, Tuple
import re
from .constants import FOCUS_AREAS


class PartOfDayRuleset:
    """
    Ruleset for evaluating time of day when symptoms worsen.

    Handles radio button selection (Morning/Afternoon/Evening) and free text qualifiers.
    """
    
    # Per-domain caps for this field
    CAPS = {
        "GA": 0.80,
        "STR": 0.60,
        "CM": 0.50,
        "COG": 0.40,
        "MITO": 0.40,
        "IMM": 0.30,
        "DTX": 0.20,
        "SKN": 0.20,
        "HRM": 0.10
    }
    
    # Text qualifier keywords
    AFTER_BREAKFAST_TERMS = [
        "after breakfast", "first meal", "fatty breakfast", "post breakfast",
        "morning meal", "breakfast"
    ]
    
    AFTER_LUNCH_TERMS = [
        "after lunch", "2-4 h after eating", "2-4 hours after eating",
        "gas builds later", "post lunch", "afternoon meal"
    ]
    
    LARGE_DINNER_TERMS = [
        "large dinner", "big dinner", "heavy dinner", "eat within 2-3 h of bed",
        "eat within 2-3 hours of bed", "close to bedtime", "before bed"
    ]
    
    NOCTURNAL_TERMS = [
        "at night", "nighttime", "night time", "bedtime", "during sleep",
        "wakes from sleep", "nocturnal", "while sleeping"
    ]
    
    HISTAMINE_TERMS = [
        "itch", "hives", "sneezing", "wheezing", "histamine", "allergic reaction"
    ]
    
    HEARTBURN_TERMS = [
        "heartburn", "throat burn", "acid taste", "acid reflux", "gerd"
    ]
    
    def get_part_of_day_weights(
        self,
        time_of_day_data: Any,
        age: int = None,
        occupation_data: Dict[str, Any] = None,
        free_text_strings: str = ""
    ) -> Dict[str, float]:
        """
        Calculate focus area weights based on time of day when symptoms worsen.
        
        Args:
            time_of_day_data: Can be string (radio value) or dict with {"radio": "...", "text": "..."}
            age: Patient age (must be >= 18)
            occupation_data: Dict with work_stress_level and job_title
            free_text_strings: Additional free text from other fields (concatenated)
        
        Returns:
            Dictionary mapping focus area codes to weight adjustments
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # Age check
        if age and age < 18:
            return scores
        
        if not time_of_day_data:
            return scores
        
        # Extract radio and text values
        radio_value, text_value = self._extract_radio_and_text(time_of_day_data)
        
        # Combine all text for analysis
        all_text = f"{text_value} {free_text_strings}".lower().strip()
        
        # Build flags
        flags = self._build_flags(all_text, occupation_data)
        
        # Apply decision tree based on radio selection
        radio_lower = radio_value.lower() if radio_value else ""
        
        if radio_lower == "morning":
            scores = self._apply_morning_logic(scores, all_text, flags)
        elif radio_lower == "afternoon":
            scores = self._apply_afternoon_logic(scores, all_text, flags)
        elif radio_lower == "evening":
            scores = self._apply_evening_logic(scores, all_text, flags)
        
        # Night-time overlays (from any free text)
        if flags["nocturnal_terms"]:
            scores["GA"] += 0.40
            scores["STR"] += 0.20
            
            # Check for histamine/allergy terms
            if any(term in all_text for term in self.HISTAMINE_TERMS):
                scores["IMM"] += 0.20
                scores["SKN"] += 0.10
        
        # Cross-field synergy
        if flags["shift_work"] or flags["high_stress"]:
            scores["STR"] += 0.20
            scores["CM"] += 0.10
            scores["GA"] += 0.20
        
        if flags["late_meal_within_3h"]:
            scores["GA"] += 0.20
        
        # Apply caps
        for domain in scores:
            scores[domain] = min(scores[domain], self.CAPS.get(domain, 1.0))
        
        return scores
    
    def _extract_radio_and_text(self, data: Any) -> Tuple[str, str]:
        """
        Extract radio button value and text from nested structure or string.

        Supports multiple formats:
        1. Dict format (legacy): {"radio": "Morning", "text": "after breakfast"}
        2. String format (new): "Morning; After breakfast" or "Morning, After breakfast"
        3. String format (radio only): "Morning"

        Args:
            data: Input data (dict or string)

        Returns:
            Tuple of (radio_value, text_value)
        """
        radio_value = ""
        text_value = ""

        if isinstance(data, dict):
            # Legacy dict format: {"radio": "Morning", "text": "after breakfast"}
            radio_value = str(data.get("radio", "")).strip()
            text_value = str(data.get("text", "")).strip()
        elif isinstance(data, str):
            # New string format: "Morning; After breakfast" or "Morning, After breakfast"
            data_str = data.strip()

            # Try to split by semicolon or comma
            if ";" in data_str:
                parts = data_str.split(";", 1)
                radio_value = parts[0].strip()
                text_value = parts[1].strip() if len(parts) > 1 else ""
            elif "," in data_str:
                parts = data_str.split(",", 1)
                radio_value = parts[0].strip()
                text_value = parts[1].strip() if len(parts) > 1 else ""
            else:
                # No separator - treat entire string as radio value
                radio_value = data_str
                text_value = ""

        return radio_value, text_value
    
    def _build_flags(self, all_text: str, occupation_data: Dict[str, Any] = None) -> Dict[str, bool]:
        """Build flags for decision tree."""
        flags = {
            "after_breakfast_terms": False,
            "after_lunch_terms": False,
            "large_dinner_terms": False,
            "late_meal_within_3h": False,
            "nocturnal_terms": False,
            "shift_work": False,
            "high_stress": False
        }
        
        # Check text qualifiers
        flags["after_breakfast_terms"] = any(term in all_text for term in self.AFTER_BREAKFAST_TERMS)
        flags["after_lunch_terms"] = any(term in all_text for term in self.AFTER_LUNCH_TERMS)
        flags["large_dinner_terms"] = any(term in all_text for term in self.LARGE_DINNER_TERMS)
        flags["nocturnal_terms"] = any(term in all_text for term in self.NOCTURNAL_TERMS)
        
        # Check for late meal patterns
        if any(term in all_text for term in ["within 2-3", "within 2-3h", "within 2-3 hours", "close to bed", "before bed"]):
            flags["late_meal_within_3h"] = True
        
        # Check occupation data
        if occupation_data:
            job_title = str(occupation_data.get("job_title", "")).lower()
            work_stress_level = occupation_data.get("work_stress_level", 0)
            
            # Shift work detection
            shift_keywords = ["shift", "night", "rotating", "overnight", "night shift"]
            flags["shift_work"] = any(keyword in job_title for keyword in shift_keywords)
            
            # High stress (>= 8)
            try:
                stress_level = int(work_stress_level) if work_stress_level else 0
                flags["high_stress"] = stress_level >= 8
            except (ValueError, TypeError):
                pass
        
        return flags
    
    def _apply_morning_logic(self, scores: Dict[str, float], all_text: str, flags: Dict[str, bool]) -> Dict[str, float]:
        """Apply morning decision tree."""
        # Default morning weights
        scores["STR"] += 0.40
        scores["COG"] += 0.20
        
        # After breakfast terms
        if flags["after_breakfast_terms"]:
            scores["GA"] += 0.20
            scores["DTX"] += 0.10
        
        # Heartburn/throat burn
        if any(term in all_text for term in self.HEARTBURN_TERMS):
            scores["GA"] += 0.20
        
        return scores
    
    def _apply_afternoon_logic(self, scores: Dict[str, float], all_text: str, flags: Dict[str, bool]) -> Dict[str, float]:
        """Apply afternoon decision tree."""
        # Default afternoon weights
        scores["CM"] += 0.40
        scores["COG"] += 0.20
        scores["STR"] += 0.20
        
        # After lunch terms
        if flags["after_lunch_terms"]:
            scores["GA"] += 0.30
        
        return scores
    
    def _apply_evening_logic(self, scores: Dict[str, float], all_text: str, flags: Dict[str, bool]) -> Dict[str, float]:
        """Apply evening decision tree."""
        # Default evening weights
        scores["GA"] += 0.30
        scores["STR"] += 0.30
        scores["MITO"] += 0.30
        scores["CM"] += 0.20
        
        # Large dinner or late meal terms
        if flags["large_dinner_terms"] or flags["late_meal_within_3h"]:
            scores["GA"] += 0.10
        
        return scores




