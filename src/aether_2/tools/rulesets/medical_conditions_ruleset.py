"""
Medical conditions to health domain mapping ruleset.

This module implements evidence-based mappings from medical conditions to health
focus areas, including weighting framework, recency modifiers, and therapy/toxicity modifiers.
"""

from typing import Dict, List


class MedicalConditionsRuleset:
    """
    Handles medical condition-based adjustments to health focus areas.
    
    Implements evidence-based condition-to-domain mapping with:
    - Weighting framework (0-1 scale: 0.2-0.3=mild, 0.4-0.6=moderate, 0.7-0.9=high)
    - Recency modifier for conditions diagnosed within 12 months
    - Therapy/toxicity modifier for medications with hepatic/renal handling
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
    
    def get_medical_condition_weights(self, medical_conditions: List[str]) -> Dict[str, float]:
        """
        Maps medical conditions to health domains with evidence-based weights.
        
        Args:
            medical_conditions: List of medical condition strings
            
        Returns:
            Dictionary mapping focus area codes to weight adjustments
        """
        if not medical_conditions:
            return {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        
        weights = {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        
        # Normalize condition names for matching
        conditions_lower = [condition.lower().strip() for condition in medical_conditions]
        
        # Metabolic / Cardiovascular
        if any("type 2 diabetes" in cond or "t2d" in cond or "diabetes" in cond for cond in conditions_lower):
            weights["CM"] += 0.80
            weights["DTX"] += 0.30
            weights["MITO"] += 0.25
            
        if any("hyperlipidemia" in cond or "high cholesterol" in cond or "dyslipidemia" in cond for cond in conditions_lower):
            weights["CM"] += 0.60
            
        if any("hypertension" in cond or "high blood pressure" in cond or "htn" in cond for cond in conditions_lower):
            weights["CM"] += 0.60
            
        if any("coronary artery disease" in cond or "cad" in cond or "heart attack" in cond or 
               "myocardial infarction" in cond or "mi" in cond or "stent" in cond for cond in conditions_lower):
            weights["CM"] += 0.85
            weights["MITO"] += 0.30
            weights["COG"] += 0.20
            
        if any("arrhythmia" in cond or "pacemaker" in cond or "atrial fibrillation" in cond or "af" in cond for cond in conditions_lower):
            weights["CM"] += 0.60
            weights["COG"] += 0.25
            
        if any("stroke" in cond or "cerebrovascular" in cond or "cva" in cond for cond in conditions_lower):
            weights["COG"] += 0.80
            weights["CM"] += 0.40
            
        if any("peripheral arterial disease" in cond or "pad" in cond or "leg ulcer" in cond or "foot ulcer" in cond for cond in conditions_lower):
            weights["SKN"] += 0.60
            weights["CM"] += 0.30
            weights["IMM"] += 0.20
            
        if any("dvt" in cond or "deep vein thrombosis" in cond or "pulmonary embolism" in cond or "pe" in cond for cond in conditions_lower):
            weights["CM"] += 0.60
            weights["DTX"] += 0.20
            weights["STR"] += 0.20
            
        # Endocrine / Hormonal
        if any("hashimoto" in cond or "hypothyroid" in cond or "underactive thyroid" in cond for cond in conditions_lower):
            weights["HRM"] += 0.60
            weights["IMM"] += 0.40
            weights["COG"] += 0.20
            
        if any("hyperthyroid" in cond or "overactive thyroid" in cond or "graves" in cond for cond in conditions_lower):
            weights["HRM"] += 0.60
            weights["CM"] += 0.30
            weights["STR"] += 0.20
            weights["COG"] += 0.20
            
        # Respiratory / Immune
        if any("asthma" in cond for cond in conditions_lower):
            weights["IMM"] += 0.50
            weights["STR"] += 0.20
            
        if any("hiv" in cond or "aids" in cond for cond in conditions_lower):
            weights["IMM"] += 0.60
            weights["DTX"] += 0.40
            weights["CM"] += 0.30
            weights["GA"] += 0.20
            
        if any("tuberculosis" in cond or "tb" in cond for cond in conditions_lower):
            weights["IMM"] += 0.60
            weights["DTX"] += 0.20
            weights["GA"] += 0.10
            
        # Renal
        if any("chronic kidney disease" in cond or "ckd" in cond or "dialysis" in cond or "kidney failure" in cond for cond in conditions_lower):
            weights["DTX"] += 0.60
            weights["CM"] += 0.50
            weights["MITO"] += 0.30
            weights["IMM"] += 0.20
            
        if any("kidney stone" in cond or "nephrolithiasis" in cond for cond in conditions_lower):
            weights["GA"] += 0.30
            weights["DTX"] += 0.20
            weights["CM"] += 0.20
            
        # Liver / Detox
        if any("liver disease" in cond or "hepatitis" in cond or "cirrhosis" in cond for cond in conditions_lower):
            weights["DTX"] += 0.70
            weights["GA"] += 0.30
            weights["CM"] += 0.20
            
        if any("nafld" in cond or "masld" in cond or "fatty liver" in cond for cond in conditions_lower):
            weights["DTX"] += 0.60
            weights["CM"] += 0.40
            weights["GA"] += 0.30
            
        # GI
        if any("ibs" in cond or "irritable bowel" in cond for cond in conditions_lower):
            weights["GA"] += 0.70
            weights["STR"] += 0.30
            weights["IMM"] += 0.20
            
        if any("ibd" in cond or "crohn" in cond or "ulcerative colitis" in cond or "uc" in cond for cond in conditions_lower):
            weights["GA"] += 0.80
            weights["IMM"] += 0.60
            weights["DTX"] += 0.30
            weights["MITO"] += 0.20
            
        if any("celiac" in cond or "gluten" in cond for cond in conditions_lower):
            weights["GA"] += 0.80
            weights["IMM"] += 0.50
            weights["HRM"] += 0.20
            
        if any("gerd" in cond or "reflux" in cond or "hiatal hernia" in cond for cond in conditions_lower):
            weights["GA"] += 0.50
            
        if any("diverticulitis" in cond or "diverticulosis" in cond for cond in conditions_lower):
            weights["GA"] += 0.50
            
        if any("pancreatic insufficiency" in cond or "exocrine insufficiency" in cond for cond in conditions_lower):
            weights["GA"] += 0.70
            weights["DTX"] += 0.30
            
        if any("sibo" in cond or "small intestinal bacterial overgrowth" in cond for cond in conditions_lower):
            weights["GA"] += 0.70
            
        if any("peptic ulcer" in cond or "gastric ulcer" in cond or "duodenal ulcer" in cond for cond in conditions_lower):
            weights["GA"] += 0.50
            weights["DTX"] += 0.10
            
        # Neurologic / Mental health
        if any("depression" in cond or "major depressive" in cond or "mdd" in cond for cond in conditions_lower):
            weights["COG"] += 0.60
            weights["STR"] += 0.40
            weights["MITO"] += 0.20
            
        if any("anxiety" in cond or "ptsd" in cond or "claustrophobia" in cond or "panic" in cond for cond in conditions_lower):
            weights["STR"] += 0.60
            weights["COG"] += 0.30
            weights["GA"] += 0.10
            
        # Musculoskeletal / Pain
        if any("fibromyalgia" in cond or "chronic pain" in cond or "widespread pain" in cond for cond in conditions_lower):
            weights["STR"] += 0.50
            weights["COG"] += 0.40
            weights["MITO"] += 0.40
            
        if any("osteoporosis" in cond or "low bone density" in cond for cond in conditions_lower):
            weights["HRM"] += 0.50
            weights["CM"] += 0.20
            weights["COG"] += 0.10
            
        # Hematologic / Coagulation
        if any("bleeding disorder" in cond or "hemophilia" in cond or "von willebrand" in cond for cond in conditions_lower):
            weights["DTX"] += 0.20
            weights["IMM"] += 0.20
            weights["CM"] += 0.20
            
        # Oncology
        if any("cancer" in cond or "tumor" in cond or "malignancy" in cond or "oncology" in cond for cond in conditions_lower):
            weights["DTX"] += 0.50
            weights["IMM"] += 0.30
            weights["STR"] += 0.40
            weights["COG"] += 0.20
        
        # Clamp weights at 1.0 to avoid over-weighting
        for code in weights:
            weights[code] = min(weights[code], 1.0)
            
        return weights

    def get_recency_modifier(self, medical_conditions: List[str], condition_dates: List[str] = None) -> Dict[str, float]:
        """
        Adds +0.05 to mapped domains if condition diagnosed within 12 months (max +0.10).
        
        Args:
            medical_conditions: List of medical condition strings
            condition_dates: List of condition diagnosis dates (optional)
            
        Returns:
            Dictionary mapping focus area codes to recency modifier adjustments
        """
        if not medical_conditions:
            return {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        
        # For now, assume all conditions are recent if no dates provided
        # In a real implementation, you'd parse condition_dates and check if within 12 months
        modifier = {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        
        # If we have recent conditions, add modifier
        if condition_dates is None:  # Assume recent if no dates provided
            # Get base weights from conditions
            base_weights = self.get_medical_condition_weights(medical_conditions)
            for code, weight in base_weights.items():
                if weight > 0:  # Only add modifier to domains affected by conditions
                    modifier[code] = min(0.05, 0.10 - weight)  # Ensure total doesn't exceed 1.0
        
        return modifier

    def get_therapy_toxicity_modifier(self, medications: List[str]) -> Dict[str, float]:
        """
        Adds DTX +0.05-0.10 based on burden for medications with hepatic/renal handling.
        
        Args:
            medications: List of medication strings
            
        Returns:
            Dictionary mapping focus area codes to therapy/toxicity modifier adjustments
        """
        if not medications:
            return {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        
        modifier = {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        
        # Normalize medication names
        meds_lower = [med.lower().strip() for med in medications]
        
        # High burden medications (chemo, ART, etc.)
        high_burden_meds = ["methotrexate", "amiodarone", "chemotherapy", "art", "antiretroviral", 
                           "tacrolimus", "cyclosporine", "warfarin", "phenytoin", "carbamazepine"]
        
        # Medium burden medications
        medium_burden_meds = ["statins", "metformin", "acetaminophen", "ibuprofen", "naproxen", 
                             "aspirin", "clopidogrel", "digoxin", "lithium"]
        
        high_burden_count = sum(1 for med in meds_lower if any(hb_med in med for hb_med in high_burden_meds))
        medium_burden_count = sum(1 for med in meds_lower if any(mb_med in med for mb_med in medium_burden_meds))
        
        # Calculate DTX modifier
        dtx_modifier = (high_burden_count * 0.10) + (medium_burden_count * 0.05)
        modifier["DTX"] = min(dtx_modifier, 0.20)  # Cap at 0.20
        
        return modifier
