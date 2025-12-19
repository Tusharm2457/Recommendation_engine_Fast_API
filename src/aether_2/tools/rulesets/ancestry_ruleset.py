"""
Ancestry-based focus area scoring ruleset.
"""

from typing import Dict, List, Optional
from .constants import FOCUS_AREAS


class AncestryRuleset:
    """Ruleset for ancestry-based focus area scoring."""
    
    def get_ancestry_weights(
        self,
        ancestry: Optional[List[str]],
        ancestry_other: Optional[str],
        alcohol_frequency: Optional[str] = None,
        digestive_symptoms: Optional[str] = None,
        diagnoses: Optional[List[str]] = None,
        family_conditions_detail: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Calculate focus area weights based on ancestry.

        Args:
            ancestry: List of selected ancestries (multi-select)
            ancestry_other: Free-text if "Other" was selected
            alcohol_frequency: Alcohol consumption frequency
            digestive_symptoms: Self-reported digestive symptoms
            diagnoses: Personal medical diagnoses list
            family_conditions_detail: Family medical history conditions

        Returns:
            Dictionary of focus area scores
        """
        if not ancestry:
            return {code: 0.0 for code in FOCUS_AREAS}
        
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # Process each selected ancestry
        for anc in ancestry:
            anc_lower = anc.lower().strip()
            
            if "african" in anc_lower or "african-american" in anc_lower:
                scores["CM"] += 0.20
                
            elif "east asian" in anc_lower:
                scores["CM"] += 0.10
                scores["DTX"] += 0.05
                scores["GA"] += 0.15
                
            elif "northern european" in anc_lower or "caucasian" in anc_lower:
                scores["GA"] += 0.25
                scores["IMM"] += 0.05
                
            elif "hispanic" in anc_lower or "latino" in anc_lower:
                scores["CM"] += 0.15
                scores["DTX"] += 0.10
                scores["GA"] += 0.10
                
            elif "native american" in anc_lower or "first nations" in anc_lower:
                scores["CM"] += 0.20
                scores["GA"] += 0.15
                
            elif "pacific islander" in anc_lower:
                scores["CM"] += 0.25
                scores["MITO"] += 0.10
                scores["DTX"] += 0.05
                
            elif "south asian" in anc_lower:
                scores["CM"] += 0.20
                scores["DTX"] += 0.15
                scores["GA"] += 0.10
                
            elif "mediterranean" in anc_lower:
                pass  # Neutral baseline
                
            elif "middle eastern" in anc_lower:
                scores["GA"] += 0.10
                
            elif "ashkenazi" in anc_lower or "jewish" in anc_lower:
                scores["GA"] += 0.20
                scores["IMM"] += 0.10

        # Additional conditions based on ancestry + other factors

        # 1. Alcohol use + East Asian ancestry (ALDH2-linked flushing)
        if alcohol_frequency and alcohol_frequency.lower() != "never":
            for anc in ancestry:
                if "east asian" in anc.lower():
                    scores["DTX"] += 0.15
                    scores["GA"] += 0.05
                    scores["CM"] += 0.05
                    break  # Only apply once even if multiple East Asian ancestries

        # 2. Self-reported dairy triggers in digestive symptoms
        if digestive_symptoms:
            digestive_lower = digestive_symptoms.lower()
            if "dairy" in digestive_lower or "lactose" in digestive_lower:
                if "bloat" in digestive_lower or "diarrhea" in digestive_lower:
                    scores["GA"] += 0.15

        # 3. Personal or family history of celiac
        has_celiac = False

        # Check personal diagnoses
        if diagnoses:
            for diagnosis in diagnoses:
                if "celiac" in diagnosis.lower():
                    has_celiac = True
                    break

        # Check family history
        if not has_celiac and family_conditions_detail:
            # Handle both dict and string (JSON string) formats
            if isinstance(family_conditions_detail, str):
                import json
                try:
                    family_dict = json.loads(family_conditions_detail)
                    for condition_name in family_dict.keys():
                        if "celiac" in condition_name.lower():
                            has_celiac = True
                            break
                except (json.JSONDecodeError, AttributeError):
                    pass
            elif isinstance(family_conditions_detail, dict):
                for condition_name in family_conditions_detail.keys():
                    if "celiac" in condition_name.lower():
                        has_celiac = True
                        break

        if has_celiac:
            scores["GA"] += 0.20
            scores["IMM"] += 0.05

        return scores

