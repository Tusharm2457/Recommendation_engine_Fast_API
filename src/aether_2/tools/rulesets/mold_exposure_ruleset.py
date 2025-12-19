"""
Mold Exposure Ruleset

Scores focus areas based on mold exposure history.

Evidence:
- Strongest evidence supports inflammatory/respiratory effects
- Remediation focus is moisture control
- GI/mitochondrial/neuro adds are modest and bounded (mechanistic or emerging evidence)
- World Health Organization, National Academies Press

Decision Rules:
- Base weights for mold exposure: IMM +0.25, DTX +0.20, GA +0.20, MITO +0.10, COG +0.10, SKN +0.05
- Asthma/wheeze: IMM +0.10 (Tier A association)
- Fatigue/brain-fog/cognitive complaints: MITO +0.10, COG +0.05
- Histamine-mediated symptoms: GA +0.05

Author: Aether AI Engine
Date: 2025-11-23
"""

from typing import Dict, List, Optional, Tuple
from .constants import FOCUS_AREAS


class MoldExposureRuleset:
    """Ruleset for mold exposure focus area scoring."""
    
    # Keywords for detecting asthma/wheeze
    ASTHMA_KEYWORDS = [
        'asthma', 'wheeze', 'wheezing', 'bronchospasm', 'reactive airway'
    ]
    
    # Keywords for detecting fatigue/brain-fog
    FATIGUE_KEYWORDS = [
        'fatigue', 'chronic fatigue', 'cfs', 'tired', 'exhaustion',
        'brain fog', 'brain-fog', 'brainfog', 'cognitive', 'memory',
        'concentration', 'focus'
    ]
    
    # Keywords for detecting histamine-mediated symptoms
    HISTAMINE_KEYWORDS = [
        'hives', 'urticaria', 'flushing', 'allergic', 'allergy',
        'histamine', 'mast cell', 'mcas'
    ]
    
    def get_mold_exposure_weights(
        self,
        mold_exposure: Optional[bool] = None,
        diagnoses: Optional[str] = None,
        digestive_symptoms: Optional[str] = None
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights based on mold exposure.
        
        Args:
            mold_exposure: Boolean indicating mold exposure
            diagnoses: Comma-separated diagnoses string
            digestive_symptoms: Comma-separated digestive symptoms string
            
        Returns:
            Tuple of (scores dict, descriptions list)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        descriptions = []
        
        # A) If No
        if not mold_exposure:
            return (scores, descriptions)
        
        # B) If Yes - Base weights
        scores["IMM"] += 0.25
        scores["DTX"] += 0.20
        scores["GA"] += 0.20
        scores["MITO"] += 0.10
        scores["COG"] += 0.10
        scores["SKN"] += 0.05
        descriptions.append("Mold exposure (inflammatory/respiratory effects)")
        
        # 4) Severity & context modifiers
        
        # Check for asthma/wheeze in diagnoses
        if diagnoses:
            diagnoses_lower = diagnoses.lower()
            has_asthma = any(keyword in diagnoses_lower for keyword in self.ASTHMA_KEYWORDS)
            if has_asthma:
                scores["IMM"] += 0.10
                descriptions.append("Asthma/wheeze (Tier A association)")
        
        # Check for fatigue/brain-fog in diagnoses
        if diagnoses:
            diagnoses_lower = diagnoses.lower()
            has_fatigue = any(keyword in diagnoses_lower for keyword in self.FATIGUE_KEYWORDS)
            if has_fatigue:
                scores["MITO"] += 0.10
                scores["COG"] += 0.05
                descriptions.append("Fatigue/brain-fog (neuro-inflammatory stress)")
        
        # Check for histamine-mediated symptoms in diagnoses
        if diagnoses:
            diagnoses_lower = diagnoses.lower()
            has_histamine = any(keyword in diagnoses_lower for keyword in self.HISTAMINE_KEYWORDS)
            if has_histamine:
                scores["GA"] += 0.05
                descriptions.append("Histamine-mediated symptoms (barrier/mast-cell activation)")
        
        return (scores, descriptions)

