"""
Diagnosis-based focus area scoring ruleset.
"""

from typing import Dict, List, Tuple
from .constants import FOCUS_AREAS


class DiagnosisRuleset:
    """Ruleset for diagnosis-based focus area scoring."""
    
    def get_diagnosis_weights(
        self,
        diagnosis_list: List[str],
        diagnosis_years_list: List[str]
    ) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
        """
        Calculate focus area weights based on diagnoses.
        
        Args:
            diagnosis_list: List of diagnosis names
            diagnosis_years_list: List of corresponding diagnosis years
            
        Returns:
            Tuple of:
                - Cumulative scores dict (all diagnoses combined, clamped at 1.0)
                - Per-diagnosis breakdown dict {diagnosis_name: {focus_area: score}}
        """
        # Early exit if no diagnoses
        if not diagnosis_list:
            return ({code: 0.0 for code in FOCUS_AREAS}, {})
        
        cumulative_scores = {code: 0.0 for code in FOCUS_AREAS}
        per_diagnosis_breakdown = {}
        
        # Process each diagnosis
        for diagnosis_name, diagnosis_year in zip(diagnosis_list, diagnosis_years_list):
            diagnosis_scores = self._score_single_diagnosis(diagnosis_name, diagnosis_year)
            
            # Add to cumulative
            for code in FOCUS_AREAS:
                cumulative_scores[code] += diagnosis_scores[code]
            
            # Store per-diagnosis breakdown
            per_diagnosis_breakdown[diagnosis_name] = diagnosis_scores
        
        # Clamp each focus area at 1.0
        for code in FOCUS_AREAS:
            cumulative_scores[code] = min(cumulative_scores[code], 1.0)
        
        return (cumulative_scores, per_diagnosis_breakdown)
    
    def _score_single_diagnosis(self, diagnosis_name: str, diagnosis_year: str) -> Dict[str, float]:
        """Score a single diagnosis."""
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        diagnosis_lower = diagnosis_name.lower()
        
        # Metabolic / Cardiovascular
        if "diabetes" in diagnosis_lower:
            if "insulin" in diagnosis_lower or "type 1" in diagnosis_lower or "t1d" in diagnosis_lower:
                # Type 1 Diabetes
                scores["CM"] += 0.75
                scores["IMM"] += 0.30
                scores["DTX"] += 0.30
            else:
                # Type 2 Diabetes (default)
                scores["CM"] += 0.80
                scores["DTX"] += 0.30
                scores["MITO"] += 0.25
        
        elif "hyperlipidemia" in diagnosis_lower or "high_cholesterol" in diagnosis_lower or "high cholesterol" in diagnosis_lower:
            scores["CM"] += 0.60
        
        elif "hypertension" in diagnosis_lower or "high_blood_pressure" in diagnosis_lower or "high blood pressure" in diagnosis_lower:
            scores["CM"] += 0.60
        
        elif "coronary_artery_disease" in diagnosis_lower or "heart_attack" in diagnosis_lower or "heart attack" in diagnosis_lower or "stent" in diagnosis_lower or " mi " in diagnosis_lower:
            scores["CM"] += 0.85
            scores["MITO"] += 0.30
            scores["COG"] += 0.20
        
        elif "arrhythmia" in diagnosis_lower or "has_pacemaker" in diagnosis_lower or "pacemaker" in diagnosis_lower or " af " in diagnosis_lower or "atrial fib" in diagnosis_lower:
            scores["CM"] += 0.60
            scores["COG"] += 0.25
        
        elif "stroke" in diagnosis_lower:
            scores["COG"] += 0.80
            scores["CM"] += 0.40
        
        elif "peripheral arterial" in diagnosis_lower or "leg_foot_ulcers" in diagnosis_lower or "leg ulcer" in diagnosis_lower or "foot ulcer" in diagnosis_lower:
            scores["SKN"] += 0.60
            scores["CM"] += 0.30
            scores["IMM"] += 0.20
        
        elif "dvt" in diagnosis_lower or "blood_clots" in diagnosis_lower or "pulmonary_embolism" in diagnosis_lower or "blood clot" in diagnosis_lower:
            scores["CM"] += 0.60
            scores["DTX"] += 0.20
            scores["STR"] += 0.20
        
        # Endocrine / Hormonal
        elif "hashimoto" in diagnosis_lower or ("thyroid" in diagnosis_lower and "auto" in diagnosis_lower):
            scores["HRM"] += 0.60
            scores["IMM"] += 0.40
            scores["COG"] += 0.20
        
        elif "overactive_thyroid" in diagnosis_lower or "hyperthyroid" in diagnosis_lower:
            scores["HRM"] += 0.60
            scores["CM"] += 0.30
            scores["STR"] += 0.20
            scores["COG"] += 0.20
        
        # Respiratory / Immune
        elif "asthma" in diagnosis_lower:
            scores["IMM"] += 0.50
            scores["STR"] += 0.20
        
        elif "hiv" in diagnosis_lower or "aids" in diagnosis_lower:
            scores["IMM"] += 0.60
            scores["DTX"] += 0.40
            scores["CM"] += 0.30
            scores["GA"] += 0.20
        
        elif "tuberculosis" in diagnosis_lower or " tb " in diagnosis_lower:
            scores["IMM"] += 0.60
            scores["DTX"] += 0.20
            scores["GA"] += 0.10
        
        # Renal
        elif "kidney_disease" in diagnosis_lower or "dialysis" in diagnosis_lower or "chronic kidney" in diagnosis_lower or " ckd " in diagnosis_lower:
            scores["DTX"] += 0.60
            scores["CM"] += 0.50
            scores["MITO"] += 0.30
            scores["IMM"] += 0.20
        
        elif "kidney_stones" in diagnosis_lower or "kidney stone" in diagnosis_lower:
            scores["GA"] += 0.30
            scores["DTX"] += 0.20
            scores["CM"] += 0.20

        # Liver / Detox
        elif "liver_disease" in diagnosis_lower or "liver disease" in diagnosis_lower or "hepatitis" in diagnosis_lower or "cirrhosis" in diagnosis_lower:
            scores["DTX"] += 0.70
            scores["GA"] += 0.30
            scores["CM"] += 0.20

        elif "nafld" in diagnosis_lower or "masld" in diagnosis_lower or "fatty liver" in diagnosis_lower:
            scores["DTX"] += 0.60
            scores["CM"] += 0.40
            scores["GA"] += 0.30

        # GI
        elif " ibs " in diagnosis_lower or "irritable bowel" in diagnosis_lower:
            scores["GA"] += 0.70
            scores["STR"] += 0.30
            scores["IMM"] += 0.20

        elif " ibd " in diagnosis_lower or "crohn" in diagnosis_lower or " uc " in diagnosis_lower or "ulcerative colitis" in diagnosis_lower:
            scores["GA"] += 0.80
            scores["IMM"] += 0.60
            scores["DTX"] += 0.30
            scores["MITO"] += 0.20

        elif "celiac" in diagnosis_lower:
            scores["GA"] += 0.80
            scores["IMM"] += 0.50
            scores["HRM"] += 0.20

        elif "gerd" in diagnosis_lower or "reflux" in diagnosis_lower or "hiatal_hernia" in diagnosis_lower or "hiatal hernia" in diagnosis_lower:
            scores["GA"] += 0.50

        elif "diverticulitis" in diagnosis_lower:
            scores["GA"] += 0.50

        elif "pancreatic" in diagnosis_lower and "insufficiency" in diagnosis_lower:
            scores["GA"] += 0.70
            scores["DTX"] += 0.30

        elif "sibo" in diagnosis_lower:
            scores["GA"] += 0.70

        elif "peptic ulcer" in diagnosis_lower or "reflux_ulcers" in diagnosis_lower or "ulcer" in diagnosis_lower:
            scores["GA"] += 0.50
            scores["DTX"] += 0.10

        # Neurologic / Mental health
        elif "depression" in diagnosis_lower:
            scores["COG"] += 0.60
            scores["STR"] += 0.40
            scores["MITO"] += 0.20

        elif "anxiety" in diagnosis_lower or "ptsd" in diagnosis_lower or "claustrophobic" in diagnosis_lower:
            scores["STR"] += 0.60
            scores["COG"] += 0.30
            scores["GA"] += 0.10

        # Musculoskeletal / Pain
        elif "fibromyalgia" in diagnosis_lower or "chronic pain" in diagnosis_lower or "widespread pain" in diagnosis_lower:
            scores["STR"] += 0.50
            scores["COG"] += 0.40
            scores["MITO"] += 0.40

        elif "osteoporosis" in diagnosis_lower:
            scores["HRM"] += 0.50
            scores["CM"] += 0.20
            scores["COG"] += 0.10

        # Hematologic / Coagulation
        elif "bleeding_disorder" in diagnosis_lower or "bleeding disorder" in diagnosis_lower:
            scores["DTX"] += 0.20
            scores["IMM"] += 0.20
            scores["CM"] += 0.20

        # Oncology
        elif "cancer" in diagnosis_lower or "carcinoma" in diagnosis_lower or "lymphoma" in diagnosis_lower or "leukemia" in diagnosis_lower:
            scores["DTX"] += 0.50
            scores["IMM"] += 0.30
            scores["STR"] += 0.40
            scores["COG"] += 0.20

        # Arthritis
        elif "arthritis" in diagnosis_lower:
            # Check if inflammatory (RA/psoriatic) - would need med list check, default to OA
            scores["STR"] += 0.30
            scores["MITO"] += 0.30
            scores["IMM"] += 0.20
            scores["CM"] += 0.10

        # Gout
        elif "gout" in diagnosis_lower:
            scores["CM"] += 0.40
            scores["DTX"] += 0.20
            scores["GA"] += 0.10
            scores["IMM"] += 0.10

        # Heart murmur
        elif "heart_murmur" in diagnosis_lower or "heart murmur" in diagnosis_lower or "valve" in diagnosis_lower:
            scores["CM"] += 0.20

        # Polio
        elif "polio" in diagnosis_lower:
            scores["MITO"] += 0.50
            scores["STR"] += 0.30
            scores["COG"] += 0.20
            scores["CM"] += 0.10

        return scores

