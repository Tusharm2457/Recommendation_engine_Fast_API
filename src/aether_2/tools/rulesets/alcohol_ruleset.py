"""
Alcohol Use Ruleset

Parses free-text alcohol consumption and calculates focus area scores based on:
1. Weekly drink count (WDC) - normalized to standard drinks (14g ethanol)
2. Binge drinking patterns (≥4 drinks for women, ≥5 for men in ~2h)
3. Sex-aware thresholds (NIAAA guidelines)

Standard drink = 14g ethanol:
- 12 oz beer (5% ABV)
- 5 oz wine (12% ABV)
- 1.5 oz spirits (40% ABV)

Exposure Categories (sex-aware):
- Low: WDC 1-6/wk, no binge
- Moderate: WDC ≥7/wk (or NIAAA: ≥8/wk women, ≥15/wk men) and no weekly binge
- Heavy: WDC ≥14/wk or NIAAA heavy or weekly binging
- Extreme: WDC ≥28/wk or ≥2 binges/wk

Base Exposure Scores:
- Low: DTX +0.05, CM +0.05, GA +0.05, IMM +0.05, MITO +0.05, STR +0.05
- Moderate: DTX +0.30, CM +0.10, GA +0.30, IMM +0.10, MITO +0.10, SKN +0.05, STR +0.05, COG +0.05
- Heavy: DTX +1.00, CM +0.80, GA +0.70, IMM +0.20, MITO +0.20, SKN +0.10, STR +0.10, COG +0.10
- Extreme: DTX +1.00, CM +0.80, GA +0.70, IMM +0.40, MITO +0.30, SKN +0.20, STR +0.20, COG +0.15

Binge Add-ons (stack on base):
- Monthly: DTX +0.10, CM +0.05, STR +0.05, GA +0.05
- Weekly: DTX +0.20, CM +0.10, STR +0.10, GA +0.10
- ≥2×/wk: DTX +0.30, CM +0.15, STR +0.15, GA +0.15
"""

from typing import Dict, Tuple, Optional
import re
from .constants import FOCUS_AREAS


class AlcoholRuleset:
    """Ruleset for alcohol consumption scoring with text parsing and sex-aware thresholds."""
    
    # Base exposure scores by category
    BASE_SCORES = {
        "low": {
            "DTX": 0.10, "CM": 0.05, "GA": 0.05, "IMM": 0.05,
            "MITO": 0.05, "STR": 0.05
        },
        "moderate": {
            "DTX": 0.30, "CM": 0.10, "GA": 0.30, "IMM": 0.10,
            "MITO": 0.10, "SKN": 0.05, "STR": 0.05, "COG": 0.05
        },
        "heavy": {
            "DTX": 1.00, "CM": 0.80, "GA": 0.70, "IMM": 0.20,
            "MITO": 0.20, "SKN": 0.10, "STR": 0.10, "COG": 0.10
        },
        "extreme": {
            "DTX": 1.00, "CM": 0.80, "GA": 0.70, "IMM": 0.40,
            "MITO": 0.30, "SKN": 0.20, "STR": 0.20, "COG": 0.15
        }
    }
    
    # Binge add-ons by frequency
    BINGE_ADDONS = {
        "monthly": {"DTX": 0.10, "CM": 0.05, "STR": 0.05, "GA": 0.05},
        "weekly": {"DTX": 0.20, "CM": 0.10, "STR": 0.10, "GA": 0.10},
        "multiple_weekly": {"DTX": 0.30, "CM": 0.15, "STR": 0.15, "GA": 0.15}
    }
    
    def get_alcohol_weights(
        self,
        frequency: Optional[str],
        typical_amount: Optional[str],
        sex: Optional[str]
    ) -> Tuple[Dict[str, float], str]:
        """
        Calculate focus area weights based on alcohol consumption.
        
        Args:
            frequency: Frequency category ("rarely", "monthly", "sometimes", "daily")
            typical_amount: Free-text description of typical consumption
            sex: "Male" or "Female" for sex-aware thresholds
            
        Returns:
            Tuple of (scores dict, description string for reasons file)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # If no frequency or frequency is empty/None, return zeros
        if not frequency:
            return (scores, "")
        
        # Parse weekly drink count (WDC) and binge frequency
        wdc, binge_freq = self._parse_alcohol_consumption(frequency, typical_amount)
        
        # If WDC is 0, return zeros
        if wdc == 0:
            return (scores, "")
        
        # Determine exposure category
        exposure_category = self._determine_exposure_category(wdc, binge_freq, sex)
        
        # Apply base exposure scores
        if exposure_category in self.BASE_SCORES:
            for focus_area, weight in self.BASE_SCORES[exposure_category].items():
                scores[focus_area] = weight
        
        # Apply binge add-ons
        if binge_freq and binge_freq in self.BINGE_ADDONS:
            for focus_area, addon in self.BINGE_ADDONS[binge_freq].items():
                scores[focus_area] += addon
        
        # Create description for reasons file
        description = self._create_description(exposure_category, binge_freq)

        return (scores, description)

    def _parse_alcohol_consumption(
        self,
        frequency: str,
        typical_amount: Optional[str]
    ) -> Tuple[float, Optional[str]]:
        """
        Parse frequency and typical_amount to extract weekly drink count (WDC) and binge frequency.
        
        Returns:
            Tuple of (weekly_drink_count, binge_frequency)
            binge_frequency can be: None, "monthly", "weekly", "multiple_weekly"
        """
        wdc = 0.0
        binge_freq = None
        
        # Default WDC by frequency category (if text is vague)
        frequency_defaults = {
            "rarely": 0.5,      # 0-1/wk
            "monthly": 0.5,     # 1-3/mo → ~0.5/wk
            "sometimes": 3.0,   # 1-6/wk
            "daily": 7.0        # ≥7/wk
        }
        
        # Start with frequency default
        freq_lower = frequency.lower() if frequency else ""
        wdc = frequency_defaults.get(freq_lower, 0.0)
        
        # Parse typical_amount text to override default if clearer number found
        if typical_amount:
            parsed_wdc, parsed_binge = self._parse_amount_text(typical_amount)
            if parsed_wdc is not None:
                wdc = parsed_wdc
            if parsed_binge:
                binge_freq = parsed_binge
        
        return (wdc, binge_freq)

    def _parse_amount_text(self, text: str) -> Tuple[Optional[float], Optional[str]]:
        """
        Parse free-text typical_amount to extract weekly drink count and binge patterns.

        Returns:
            Tuple of (weekly_drink_count, binge_frequency)
        """
        if not text:
            return (None, None)

        text_lower = text.lower()
        wdc = None
        binge_freq = None

        # Extract numbers from text
        numbers = re.findall(r'\d+(?:\.\d+)?', text)

        # Common drink types and their standard drink equivalents
        # beer/can/bottle → 1 drink, wine glass → 1 drink, shot/spirit → 1 drink

        # Detect time period
        per_day = any(word in text_lower for word in ['day', 'daily', 'per day', '/day'])
        per_week = any(word in text_lower for word in ['week', 'weekly', 'per week', '/week', '/wk'])
        per_month = any(word in text_lower for word in ['month', 'monthly', 'per month', '/month', '/mo'])

        # Extract drink count
        if numbers:
            count = float(numbers[0])

            # Convert to weekly
            if per_day:
                wdc = count * 7
            elif per_week:
                wdc = count
            elif per_month:
                wdc = count / 4.0  # ~4 weeks per month
            else:
                # Default to per week if no period specified
                wdc = count

        # Detect binge patterns
        # Binge = ≥4 drinks for women, ≥5 for men in ~2h
        # Look for keywords like "binge", "heavy drinking session", etc.
        if any(word in text_lower for word in ['binge', 'heavy session', 'party', 'weekend']):
            # Try to determine frequency
            if any(word in text_lower for word in ['daily', 'every day']):
                binge_freq = "multiple_weekly"  # ≥2×/wk
            elif any(word in text_lower for word in ['week', 'weekly', 'weekend']):
                binge_freq = "weekly"
            elif any(word in text_lower for word in ['month', 'monthly']):
                binge_freq = "monthly"

        # Infer binge from high single-occasion counts
        # e.g., "6 beers on Saturday" suggests binge
        if wdc and wdc >= 4 and any(word in text_lower for word in ['saturday', 'friday', 'occasion', 'night out']):
            if per_week or 'week' in text_lower:
                binge_freq = "weekly"
            elif per_month or 'month' in text_lower:
                binge_freq = "monthly"

        return (wdc, binge_freq)

    def _determine_exposure_category(
        self,
        wdc: float,
        binge_freq: Optional[str],
        sex: Optional[str]
    ) -> str:
        """
        Determine exposure category based on WDC, binge frequency, and sex.

        Categories:
        - Low: WDC 1-6/wk, no binge
        - Moderate: WDC ≥7/wk (or NIAAA: ≥8/wk women, ≥15/wk men) and no weekly binge
        - Heavy: WDC ≥14/wk or NIAAA heavy or weekly binging
        - Extreme: WDC ≥28/wk or ≥2 binges/wk
        """
        # Extreme: ≥28/wk or ≥2 binges/wk
        if wdc >= 28 or binge_freq == "multiple_weekly":
            return "extreme"

        # NIAAA heavy drinking thresholds (sex-aware)
        niaaa_heavy = False
        if sex and sex.lower() in ["female", "f", "woman"]:
            niaaa_heavy = wdc >= 8
        elif sex and sex.lower() in ["male", "m", "man"]:
            niaaa_heavy = wdc >= 15

        # Heavy: WDC ≥14/wk or NIAAA heavy or weekly binging
        if wdc >= 14 or niaaa_heavy or binge_freq in ["weekly", "multiple_weekly"]:
            return "heavy"

        # Moderate: WDC ≥7/wk and no weekly binge
        if wdc >= 7:
            return "moderate"

        # Low: WDC 1-6/wk, no binge
        if wdc >= 1:
            return "low"

        # Default to low if WDC > 0
        return "low"

    def _create_description(
        self,
        exposure_category: str,
        binge_freq: Optional[str]
    ) -> str:
        """Create human-readable description for reasons file."""
        # Base description - just show category
        description = f"Consumption ({exposure_category})"

        # Add binge info
        if binge_freq == "monthly":
            description += ", monthly binge"
        elif binge_freq == "weekly":
            description += ", weekly binge"
        elif binge_freq == "multiple_weekly":
            description += ", ≥2 binges/wk"

        return description

