"""
Tobacco Use Ruleset

Decision tree for tobacco use and cessation.

1) If "never" → Skip (return zeros)

2) If "quit" → Calculate years since quit (YSQ) and apply residual multipliers
   - First compute "as-if current" base weights from duration class at last use
   - Then apply residual multipliers by domain based on YSQ

3) If "yes" (current smoker) → Apply base weights by duration class

Base weights for current smokers (by Duration Class):
- <1 yr: CM +0.20, IMM +0.10, MITO +0.10, SKN +0.05, DTX +0.05, GA +0.30, STR +0.05
- 2-5 yrs: CM +0.40, IMM +0.25, MITO +0.20, SKN +0.15, DTX +0.10, GA +0.30, STR +0.10
- >5 yrs: CM +0.60, IMM +0.40, MITO +0.35, SKN +0.30, DTX +0.20, GA +0.30, STR +0.10

Residual multipliers for quitters (applied to base weights):
- CM: YSQ <1: ×0.70; 1-5: ×0.40; 5-15: ×0.20; ≥15: ×0.05
- Cancer proxy (DTX/SKN/IMM): YSQ <5: ×0.80; 5-10: ×0.60; 10-15: ×0.40; ≥15: ×0.20
- GA: YSQ <1: ×0.50; 1-5: ×0.20; ≥5: ×0.00
- IMM: YSQ <1: ×0.50; 1-5: ×0.30; 5-10: ×0.20; ≥10: ×0.10
- MITO: YSQ <1: ×0.50; 1-5: ×0.30; 5-10: ×0.20; ≥10: ×0.10
- SKN: YSQ <5: ×0.30; 5-10: ×0.20; ≥10: ×0.10
"""

from typing import Dict, Tuple, Optional
from datetime import datetime
from .constants import FOCUS_AREAS


class TobaccoRuleset:
    """Ruleset for tobacco use and cessation scoring."""
    
    # Base weights for current smokers by duration class
    BASE_WEIGHTS = {
        "less_than_year": {
            "CM": 0.20, "IMM": 0.10, "MITO": 0.10, "SKN": 0.05,
            "DTX": 0.05, "GA": 0.30, "STR": 0.05
        },
        "2_5_years": {
            "CM": 0.40, "IMM": 0.25, "MITO": 0.20, "SKN": 0.15,
            "DTX": 0.10, "GA": 0.30, "STR": 0.10
        },
        "more_than_5_years": {
            "CM": 0.60, "IMM": 0.40, "MITO": 0.35, "SKN": 0.30,
            "DTX": 0.20, "GA": 0.30, "STR": 0.10
        }
    }
    
    def get_tobacco_weights(
        self,
        use_status: str,
        quit_year: Optional[str],
        duration_category: Optional[str]
    ) -> Tuple[Dict[str, float], str]:
        """
        Calculate focus area weights based on tobacco use status.
        
        Args:
            use_status: "never", "quit", or "yes"
            quit_year: Year quit (for "quit" status)
            duration_category: Duration of use ("less_than_year", "2_5_years", "more_than_5_years")
            
        Returns:
            Tuple of (scores dict, description string for reasons file)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # If never smoked, return zeros
        if not use_status or use_status.lower() == "never":
            return (scores, "")
        
        # If quit, calculate years since quit and apply residual multipliers
        if use_status.lower() == "quit":
            return self._calculate_quit_scores(quit_year, duration_category)
        
        # If current smoker, apply base weights
        if use_status.lower() == "yes":
            return self._calculate_current_smoker_scores(duration_category)
        
        return (scores, "")
    
    def _calculate_current_smoker_scores(
        self,
        duration_category: Optional[str]
    ) -> Tuple[Dict[str, float], str]:
        """Calculate scores for current smokers."""
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # Default to >5 years if unknown
        if not duration_category:
            duration_category = "more_than_5_years"
        
        # Get base weights for duration class
        if duration_category in self.BASE_WEIGHTS:
            base_weights = self.BASE_WEIGHTS[duration_category]
            for code, weight in base_weights.items():
                scores[code] = weight
        
        # Create description for reasons file
        duration_display = {
            "less_than_year": "<1 year",
            "2_5_years": "2-5 years",
            "more_than_5_years": ">5 years"
        }.get(duration_category, duration_category)
        
        description = f"Current smoker ({duration_display})"
        
        return (scores, description)
    
    def _calculate_quit_scores(
        self,
        quit_year: Optional[str],
        duration_category: Optional[str]
    ) -> Tuple[Dict[str, float], str]:
        """Calculate scores for former smokers with residual multipliers."""
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # Calculate years since quit
        if not quit_year:
            # If quit year unknown, assume recent quit (conservative)
            years_since_quit = 0
        else:
            try:
                current_year = datetime.now().year
                quit_year_int = int(quit_year)
                years_since_quit = current_year - quit_year_int
                # Clamp to non-negative
                years_since_quit = max(0, years_since_quit)
            except (ValueError, TypeError):
                years_since_quit = 0
        
        # Default to >5 years duration if unknown (conservative residuals)
        if not duration_category:
            duration_category = "more_than_5_years"
        
        # Get base weights (as-if current smoker)
        if duration_category in self.BASE_WEIGHTS:
            base_weights = self.BASE_WEIGHTS[duration_category]
        else:
            base_weights = self.BASE_WEIGHTS["more_than_5_years"]
        
        # Apply residual multipliers by domain
        multipliers = self._get_residual_multipliers(years_since_quit)
        
        for code in FOCUS_AREAS:
            if code in base_weights and code in multipliers:
                scores[code] = base_weights[code] * multipliers[code]
        
        # Create description for reasons file
        description = f"Quit {years_since_quit} years ago"

        return (scores, description)

    def _get_residual_multipliers(self, years_since_quit: int) -> Dict[str, float]:
        """
        Get residual multipliers based on years since quit.

        Evidence-based decline after cessation by domain.
        """
        multipliers = {code: 0.0 for code in FOCUS_AREAS}

        # CM (heart/vascular): Risk drops quickly after quitting
        # YSQ <1: ×0.70; 1-5: ×0.40; 5-15: ×0.20; ≥15: ×0.05
        if years_since_quit < 1:
            multipliers["CM"] = 0.70
        elif years_since_quit < 5:
            multipliers["CM"] = 0.40
        elif years_since_quit < 15:
            multipliers["CM"] = 0.20
        else:
            multipliers["CM"] = 0.05

        # Cancer proxy (DTX/SKN components): Falls more slowly
        # YSQ <5: ×0.80; 5-10: ×0.60; 10-15: ×0.40; ≥15: ×0.20
        cancer_multiplier = 0.80
        if years_since_quit < 5:
            cancer_multiplier = 0.80
        elif years_since_quit < 10:
            cancer_multiplier = 0.60
        elif years_since_quit < 15:
            cancer_multiplier = 0.40
        else:
            cancer_multiplier = 0.20

        multipliers["DTX"] = cancer_multiplier

        # GA (reflux/Crohn's): Improves quickly with cessation
        # YSQ <1: ×0.50; 1-5: ×0.20; ≥5: ×0.00
        if years_since_quit < 1:
            multipliers["GA"] = 0.50
        elif years_since_quit < 5:
            multipliers["GA"] = 0.20
        else:
            multipliers["GA"] = 0.00

        # IMM: Innate effects fade quickly; adaptive/epigenetic marks persist
        # YSQ <1: ×0.50; 1-5: ×0.30; 5-10: ×0.20; ≥10: ×0.10
        if years_since_quit < 1:
            multipliers["IMM"] = 0.50
        elif years_since_quit < 5:
            multipliers["IMM"] = 0.30
        elif years_since_quit < 10:
            multipliers["IMM"] = 0.20
        else:
            multipliers["IMM"] = 0.10

        # MITO: Mitochondrial dysfunction improves but may persist
        # YSQ <1: ×0.50; 1-5: ×0.30; 5-10: ×0.20; ≥10: ×0.10
        if years_since_quit < 1:
            multipliers["MITO"] = 0.50
        elif years_since_quit < 5:
            multipliers["MITO"] = 0.30
        elif years_since_quit < 10:
            multipliers["MITO"] = 0.20
        else:
            multipliers["MITO"] = 0.10

        # SKN: Vascularity recovers; photo-/smoke-aging partly permanent
        # YSQ <5: ×0.30; 5-10: ×0.20; ≥10: ×0.10
        if years_since_quit < 5:
            multipliers["SKN"] = 0.30
        elif years_since_quit < 10:
            multipliers["SKN"] = 0.20
        else:
            multipliers["SKN"] = 0.10

        # STR: Not specified in rules, assume similar to MITO
        if years_since_quit < 1:
            multipliers["STR"] = 0.50
        elif years_since_quit < 5:
            multipliers["STR"] = 0.30
        elif years_since_quit < 10:
            multipliers["STR"] = 0.20
        else:
            multipliers["STR"] = 0.10

        # COG, HRM: Not affected by tobacco in the rules
        multipliers["COG"] = 0.0
        multipliers["HRM"] = 0.0

        return multipliers

