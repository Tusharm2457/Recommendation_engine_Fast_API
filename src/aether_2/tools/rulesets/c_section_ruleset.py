"""
C-Section Birth focus area scoring ruleset.
"""

from typing import Dict, Optional, Tuple
from .constants import FOCUS_AREAS


class CSectionRuleset:
    """Ruleset for C-section birth focus area scoring."""
    
    def get_c_section_weights(
        self,
        born_via_c_section: Optional[str],
        has_allergies: bool = False,
        diagnoses: Optional[str] = None,
        digestive_symptoms: Optional[str] = None,
        took_antibiotics_as_child: bool = False
    ) -> Tuple[Dict[str, float], str]:
        """
        Calculate focus area weights based on C-section birth status.
        
        Args:
            born_via_c_section: C-section birth status ("yes", "no", "not_sure")
            has_allergies: Whether patient has allergies
            diagnoses: Comma-separated diagnoses string (for asthma, eczema detection)
            digestive_symptoms: Digestive symptoms string (for IBS/IBD detection)
            took_antibiotics_as_child: Whether patient took antibiotics as a child
            
        Returns:
            Tuple of (scores dict, description string)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        if not born_via_c_section:
            return (scores, "Unknown")
        
        status = born_via_c_section.lower().strip()
        
        # Detect asthma/eczema
        has_asthma_eczema = False
        if diagnoses:
            diagnoses_lower = diagnoses.lower()
            asthma_eczema_keywords = ['asthma', 'eczema', 'atopic dermatitis']
            has_asthma_eczema = any(keyword in diagnoses_lower for keyword in asthma_eczema_keywords)
        
        # Detect IBS/IBD-like symptoms
        has_ibs_ibd = False
        if digestive_symptoms:
            symptoms_lower = digestive_symptoms.lower()
            ibs_ibd_keywords = ['ibs', 'irritable bowel', 'ibd', 'inflammatory bowel', 'crohn', 'colitis', 'diarrhea', 'abdominal pain']
            has_ibs_ibd = any(keyword in symptoms_lower for keyword in ibs_ibd_keywords)
        
        # No - neutral
        if status == "no":
            description = "No"
        
        # Not sure
        elif status == "not_sure":
            scores["IMM"] = 0.10
            scores["GA"] = 0.05
            scores["SKN"] = 0.05
            
            # Overlays
            if has_allergies or has_asthma_eczema:
                scores["IMM"] += 0.05
                scores["SKN"] += 0.05
            
            if has_ibs_ibd:
                scores["GA"] += 0.05
            
            # Cross-field synergies
            if took_antibiotics_as_child:
                scores["IMM"] += 0.10
                scores["GA"] += 0.10
            
            description = "Not sure"
        
        # Yes
        elif status == "yes":
            scores["IMM"] = 0.20
            scores["GA"] = 0.15
            scores["SKN"] = 0.10
            scores["CM"] = 0.05
            
            # Overlays
            if has_allergies or has_asthma_eczema:
                scores["IMM"] += 0.05
                scores["SKN"] += 0.05
            
            if has_ibs_ibd:
                scores["GA"] += 0.05
            
            # Cross-field synergies
            if took_antibiotics_as_child:
                scores["IMM"] += 0.10
                scores["GA"] += 0.10
            
            description = "Yes"
        
        else:
            # Unknown status
            description = "Unknown"
        
        return (scores, description)

