"""
Sunlight Exposure Ruleset

Calculates focus area scores based on:
1. Days per week of sun exposure (0-7)
2. Average minutes per day (0-300)
3. Vitamin D status from blood work (≥80 ng/mL = optimal)
4. Shift work status (circadian mismatch)
5. Photoprotection practices
6. Photosensitizing medications

Exposure Categories:
- Very low: <60 weekly minutes OR ≤1 day and <30 min
- Low: 60-149 weekly minutes OR ≤2 days
- Adequate: 150-420 weekly minutes (20-60 min/day × 3-7 days)
- High: 421-840 weekly minutes
- Very high: >840 weekly minutes OR sunburns/tanning beds

Evidence-based scoring from:
- PLOS (vitamin D synthesis, immune function)
- Office of Dietary Supplements (vitamin D and immunity)
- BMJ (circadian entrainment)
- Journal of Clinical Sleep Medicine (daylight and sleep)
- Cancer.gov (UV carcinogenesis)

Key Mechanisms:
- Immune: vitamin D synthesis, mucosal immunity
- Gut: vitamin D and barrier function
- Cardiometabolic: vitamin D and metabolic health
- Stress: circadian entrainment
- Cognitive: daylight and mood/attention
- Skin: UV damage and cancer risk
"""

from typing import Dict, Tuple, Optional
from .constants import FOCUS_AREAS


class SunlightRuleset:
    """Ruleset for sunlight exposure scoring."""
    
    # Photosensitizing medications
    PHOTOSENSITIZING_MEDS = [
        'tetracycline', 'doxycycline', 'minocycline',
        'ciprofloxacin', 'levofloxacin', 'fluoroquinolone',
        'hydrochlorothiazide', 'furosemide', 'diuretic',
        'ibuprofen', 'naproxen', 'nsaid',
        'retinoid', 'isotretinoin', 'tretinoin',
        'sulfamethoxazole', 'trimethoprim'
    ]
    
    def get_sunlight_weights(
        self,
        days_per_week: Optional[int],
        avg_minutes_per_day: Optional[str],
        vitamin_d_optimal: bool = False,
        shift_work: bool = False,
        current_medications: Optional[str] = None
    ) -> Tuple[Dict[str, float], str]:
        """
        Calculate focus area weights based on sunlight exposure.
        
        Args:
            days_per_week: Days of sun exposure per week (0-7)
            avg_minutes_per_day: Average minutes per day (string like "30 minutes")
            vitamin_d_optimal: Whether vitamin D ≥80 ng/mL
            shift_work: Whether user does shift work
            current_medications: Comma-separated medication list
            
        Returns:
            Tuple of (scores dict, description string for reasons file)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # If no data provided, return zeros
        if days_per_week is None or avg_minutes_per_day is None:
            return (scores, "")
        
        # Validate and clamp days to 0-7
        days = max(0, min(7, round(days_per_week)))
        
        # Parse minutes from string and clamp to 0-300
        minutes = self._parse_minutes(avg_minutes_per_day)
        minutes = max(0, min(300, minutes))
        
        # Calculate weekly sun exposure
        weekly_sun = days * minutes
        
        # Detect photosensitizing medications
        has_photosensitizing_meds = self._has_photosensitizing_meds(current_medications)
        
        # Categorize exposure and apply scoring
        if weekly_sun < 60 or (days <= 1 and minutes < 30):
            # A) Very low exposure
            category = "very_low"
            scores["IMM"] = 0.25
            scores["GA"] = 0.15
            scores["CM"] = 0.10
            scores["STR"] = 0.05
            
            # Shift work + very low sunlight → circadian mismatch
            if shift_work:
                scores["STR"] += 0.05
        
        elif weekly_sun < 150 or days <= 2:
            # B) Low exposure
            category = "low"
            scores["IMM"] = 0.15
            scores["GA"] = 0.10
            scores["CM"] = 0.05
            scores["STR"] = 0.05  # Assuming "rarely sees daylight"
            
            # Shift work + low sunlight → circadian mismatch
            if shift_work:
                scores["STR"] += 0.05
        
        elif weekly_sun <= 420:
            # C) Adequate exposure
            category = "adequate"
            scores["STR"] = -0.10
            scores["COG"] = -0.05
            scores["GA"] = -0.05
            
            # Vitamin D optimal → additional GA benefit
            if vitamin_d_optimal:
                scores["GA"] -= 0.05  # Total GA -0.10
        
        elif weekly_sun <= 840:
            # D) High exposure
            category = "high"
            scores["SKN"] = 0.20
            scores["IMM"] = 0.05
            
            # Photosensitizing meds → extra skin risk
            if has_photosensitizing_meds:
                scores["SKN"] += 0.10
        
        else:  # weekly_sun > 840
            # E) Very high / overexposure
            category = "very_high"
            scores["SKN"] = 0.40
            
            # Photosensitizing meds → extra skin risk
            if has_photosensitizing_meds:
                scores["SKN"] += 0.10
        
        # Create description
        description = self._create_description(
            weekly_sun,
            category,
            vitamin_d_optimal,
            shift_work,
            has_photosensitizing_meds
        )

        return (scores, description)

    def _parse_minutes(self, minutes_str: str) -> int:
        """
        Parse minutes from string like "30 minutes" or "1 hour".

        Returns:
            Integer minutes
        """
        if not minutes_str:
            return 0

        minutes_lower = minutes_str.lower()

        # Try to extract number
        try:
            # Look for patterns like "30 minutes", "1.5 hours", "45"
            import re

            # Check for hours
            if 'hour' in minutes_lower:
                match = re.search(r'(\d+\.?\d*)', minutes_lower)
                if match:
                    hours = float(match.group(1))
                    return int(hours * 60)

            # Check for minutes or just a number
            match = re.search(r'(\d+)', minutes_lower)
            if match:
                return int(match.group(1))
        except (ValueError, AttributeError):
            pass

        return 0

    def _has_photosensitizing_meds(self, medications) -> bool:
        """
        Detect photosensitizing medications.

        Args:
            medications: String or list of medications

        Returns:
            True if photosensitizing meds detected, False otherwise
        """
        if not medications:
            return False

        # Handle both string and list inputs
        if isinstance(medications, list):
            meds_text = " ".join(str(m).lower() for m in medications)
        else:
            meds_text = str(medications).lower()

        for med in self.PHOTOSENSITIZING_MEDS:
            if med in meds_text:
                return True

        return False

    def _create_description(
        self,
        weekly_sun: int,
        category: str,
        vitamin_d_optimal: bool,
        shift_work: bool,
        has_photosensitizing_meds: bool
    ) -> str:
        """Create human-readable description for reasons file."""
        # Base description
        category_labels = {
            "very_low": "very low",
            "low": "low",
            "adequate": "adequate",
            "high": "high",
            "very_high": "very high"
        }

        description = f"({category_labels[category]})"

        # Add modifiers
        modifiers = []
        if vitamin_d_optimal and category == "adequate":
            modifiers.append("vit D optimal")
        if shift_work and category in ["very_low", "low"]:
            modifiers.append("shift work")
        if has_photosensitizing_meds and category in ["high", "very_high"]:
            modifiers.append("photosensitizing meds")

        if modifiers:
            description += ", " + ", ".join(modifiers)

        return description

