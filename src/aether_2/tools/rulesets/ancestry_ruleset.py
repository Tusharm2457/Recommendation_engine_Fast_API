"""
Ancestry-based health domain adjustment ruleset.

This module implements evidence-based adjustments to health focus areas based on
ancestry/ethnicity, incorporating epidemiological and physiological patterns.
"""

from typing import Dict, List


class AncestryRuleset:
    """
    Handles ancestry-based adjustments to health focus areas.
    
    Based on epidemiological evidence and physiological patterns for different
    ancestral populations, with weights applied to relevant health domains.
    """
    
    FOCUS_AREAS = {
        "CM": "Cardiometabolic & Metabolic Health",
        "COG": "Cognitive & Mental Health", 
        "DTX": "Detoxification & Biotransformation",
        "IMM": "Immune Function & Inflammation",
        "MITO": "Mitochondrial & Energy Metabolism",
        "SKN": "Skin & Barrier Function",
        "STR": "Stress-Axis & Nervous System Resilience",
        "HRM": "Hormonal Health (Transport)",
        "GA": "Gut Health and assimilation",
    }
    
    def get_ancestry_weights(self, ancestry_list: List[str]) -> Dict[str, float]:
        """
        Calculate ancestry-based weights for health focus areas.
        
        Args:
            ancestry_list: List of ancestry/ethnicity strings
            
        Returns:
            Dictionary mapping focus area codes to weight adjustments
        """
        if not ancestry_list:
            return {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        
        # Start with neutral baseline
        weights = {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        
        # Process each ancestry in the list
        for ancestry in ancestry_list:
            ancestry_lower = ancestry.lower()
            
            if "african" in ancestry_lower or "black" in ancestry_lower:
                # Higher MetS/CVD burden in US cohorts
                weights["CM"] += 0.20
                
            elif "east asian" in ancestry_lower or "asian" in ancestry_lower:
                # More visceral fat at given BMI, ALDH2 variants, low lactase persistence
                weights["CM"] += 0.10
                weights["DTX"] += 0.05  # baseline for alcohol metabolism
                weights["GA"] += 0.15   # low lactase persistence
                
            elif "northern european" in ancestry_lower or "caucasian" in ancestry_lower or "white" in ancestry_lower:
                # Celiac vigilance: HLA-DQ2/DQ8 enriched
                weights["GA"] += 0.25
                weights["IMM"] += 0.05
                
            elif "hispanic" in ancestry_lower or "latino" in ancestry_lower:
                # Higher US MetS/MASLD burden, liver fat attention, lower lactase persistence
                weights["CM"] += 0.15
                weights["DTX"] += 0.10
                weights["GA"] += 0.10
                
            elif "native american" in ancestry_lower or "first nations" in ancestry_lower:
                # Very high MetS prevalence, lower lactase persistence
                weights["CM"] += 0.20
                weights["GA"] += 0.125  # average of 0.10-0.15
                
            elif "pacific islander" in ancestry_lower:
                # Very high obesity/diabetes prevalence, fatigue/energy load, steatohepatitis vigilance
                weights["CM"] += 0.25
                weights["MITO"] += 0.10
                weights["DTX"] += 0.05
                
            elif "south asian" in ancestry_lower:
                # Higher visceral adiposity/IR, NAFLD/MASLD vigilance, IBD/celiac signal
                weights["CM"] += 0.20
                weights["DTX"] += 0.15
                weights["GA"] += 0.10
                
            elif "mediterranean" in ancestry_lower:
                # Neutral baseline (no adjustments)
                pass
                
            elif "middle eastern" in ancestry_lower:
                # Lower lactase persistence common
                weights["GA"] += 0.10
                
            elif "ashkenazi" in ancestry_lower or "jewish" in ancestry_lower:
                # IBD/Crohn's enrichment
                weights["GA"] += 0.20
                weights["IMM"] += 0.10
        
        return weights
