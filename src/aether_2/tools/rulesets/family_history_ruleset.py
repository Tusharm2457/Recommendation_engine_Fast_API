"""
Family Medical History Ruleset for Focus Area Scoring.

Scores based on first-degree relative (FDR) family medical history.
"""

import json
import re
from typing import Dict, List, Tuple
from .constants import FOCUS_AREAS


class FamilyHistoryRuleset:
    """Ruleset for family medical history-based focus area scoring."""
    
    def get_family_history_weights(
        self,
        has_family_history: bool,
        family_conditions_detail: str,
        family_other_conditions: str,
        patient_sex: str
    ) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
        """
        Calculate focus area weights based on family medical history.
        
        Args:
            has_family_history: Whether patient has family history
            family_conditions_detail: JSON string of conditions and relations
            family_other_conditions: Free-text other conditions
            patient_sex: Patient's biological sex for sex-based modifiers
            
        Returns:
            Tuple of (cumulative_scores, per_condition_breakdown)
        """
        # Early exit if no family history
        if not has_family_history:
            return ({code: 0.0 for code in FOCUS_AREAS}, {})
        
        cumulative_scores = {code: 0.0 for code in FOCUS_AREAS}
        per_condition_breakdown = {}
        
        # Parse conditions_detail (JSON string)
        conditions_dict = self._parse_conditions_detail(family_conditions_detail)
        
        # Process each condition
        for condition_name in conditions_dict.keys():
            # Normalize condition name (lowercase with underscores)
            normalized_name = self._normalize_condition_name(condition_name)
            
            # Score the condition
            condition_scores = self._score_single_condition(normalized_name, patient_sex)
            
            if any(score != 0 for score in condition_scores.values()):
                # Add to cumulative
                for code in FOCUS_AREAS:
                    cumulative_scores[code] += condition_scores[code]
                
                # Store breakdown (use original condition name for display)
                display_name = condition_name.replace('_', ' ').title()
                per_condition_breakdown[display_name] = condition_scores.copy()
        
        # Process other_conditions_text
        if family_other_conditions:
            other_scores = self._parse_other_conditions(family_other_conditions, patient_sex)
            
            for condition_name, condition_scores in other_scores.items():
                # Add to cumulative
                for code in FOCUS_AREAS:
                    cumulative_scores[code] += condition_scores[code]
                
                # Store breakdown
                per_condition_breakdown[condition_name] = condition_scores.copy()
        
        # Clamp each focus area at [0.0, 1.0]
        for code in FOCUS_AREAS:
            cumulative_scores[code] = max(0.0, min(cumulative_scores[code], 1.0))
        
        return (cumulative_scores, per_condition_breakdown)
    
    def _parse_conditions_detail(self, conditions_detail: str) -> Dict:
        """Parse the conditions_detail JSON string."""
        if not conditions_detail:
            return {}
        
        # Handle both string (JSON) and dict formats
        if isinstance(conditions_detail, str):
            try:
                return json.loads(conditions_detail)
            except (json.JSONDecodeError, ValueError):
                return {}
        elif isinstance(conditions_detail, dict):
            return conditions_detail
        
        return {}
    
    def _normalize_condition_name(self, condition_name: str) -> str:
        """Normalize condition name to lowercase with underscores."""
        # Replace spaces and hyphens with underscores
        normalized = condition_name.lower().replace(' ', '_').replace('-', '_')
        # Remove multiple consecutive underscores
        normalized = re.sub(r'_+', '_', normalized)
        return normalized.strip('_')
    
    def _score_single_condition(self, condition_name: str, patient_sex: str) -> Dict[str, float]:
        """Score a single family history condition."""
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # Anxiety Disorder
        if condition_name == "anxiety_disorder":
            scores["STR"] += 0.10
            scores["COG"] += 0.05
        
        # Arthritis (default to OA)
        elif condition_name == "arthritis":
            scores["MITO"] += 0.05
        
        # Asthma
        elif condition_name == "asthma":
            scores["IMM"] += 0.20
        
        # Bleeding Disorder
        elif condition_name == "bleeding_disorder":
            scores["IMM"] += 0.10
            scores["DTX"] += 0.05
        
        # Blood Clots (DVT)
        elif condition_name == "blood_clots" or condition_name == "dvt":
            scores["CM"] += 0.20
        
        # Cancer (unspecified)
        elif condition_name == "cancer":
            scores["DTX"] += 0.10
            scores["IMM"] += 0.10
        
        # Coronary Artery Disease
        elif condition_name == "coronary_artery_disease" or condition_name == "cad":
            scores["CM"] += 0.25
        
        # Claustrophobic
        elif condition_name == "claustrophobic":
            scores["STR"] += 0.05
            scores["COG"] += 0.05
        
        # Diabetes - Insulin (T1D)
        elif condition_name == "diabetes_insulin":
            scores["IMM"] += 0.15
            scores["CM"] += 0.15
        
        # Diabetes - Non-Insulin (T2D)
        elif condition_name == "diabetes_non_insulin" or condition_name == "diabetes":
            scores["CM"] += 0.25

        # Dialysis (CKD proxy)
        elif condition_name == "dialysis":
            scores["CM"] += 0.15
            scores["DTX"] += 0.10

        # Diverticulitis
        elif condition_name == "diverticulitis":
            scores["GA"] += 0.10

        # Fibromyalgia
        elif condition_name == "fibromyalgia":
            scores["STR"] += 0.10
            scores["COG"] += 0.05
            scores["MITO"] += 0.05

        # Gout
        elif condition_name == "gout":
            base_cm = 0.15
            base_dtx = 0.05
            base_ga = 0.05

            # +10% if male patient
            if patient_sex and patient_sex.lower() == "male":
                scores["CM"] += base_cm * 1.10
                scores["DTX"] += base_dtx * 1.10
                scores["GA"] += base_ga * 1.10
            else:
                scores["CM"] += base_cm
                scores["DTX"] += base_dtx
                scores["GA"] += base_ga

        # Has Pacemaker (arrhythmia)
        elif condition_name == "has_pacemaker" or condition_name == "pacemaker":
            scores["CM"] += 0.20

        # Heart Attack
        elif condition_name == "heart_attack":
            scores["CM"] += 0.25

        # Heart Murmur (valvular)
        elif condition_name == "heart_murmur":
            scores["CM"] += 0.15

        # Hiatal Hernia or Reflux Disease
        elif condition_name == "hiatal_hernia" or condition_name == "reflux_disease":
            scores["GA"] += 0.15

        # HIV or AIDS (record only)
        elif condition_name == "hiv" or condition_name == "aids" or condition_name == "hiv_or_aids":
            pass  # Record only, no scoring

        # High Cholesterol
        elif condition_name == "high_cholesterol":
            scores["CM"] += 0.25

        # High Blood Pressure
        elif condition_name == "high_blood_pressure":
            scores["CM"] += 0.15

        # Overactive Thyroid (Graves proxy)
        elif condition_name == "overactive_thyroid":
            base_imm = 0.15
            base_hrm = 0.20

            # +10% if female patient
            if patient_sex and patient_sex.lower() == "female":
                scores["IMM"] += base_imm * 1.10
                scores["HRM"] += base_hrm * 1.10
            else:
                scores["IMM"] += base_imm
                scores["HRM"] += base_hrm

        # Kidney Disease
        elif condition_name == "kidney_disease":
            scores["CM"] += 0.15
            scores["DTX"] += 0.10

        # Kidney Stones
        elif condition_name == "kidney_stones":
            base_ga = 0.15

            # +5% if male patient
            if patient_sex and patient_sex.lower() == "male":
                scores["GA"] += base_ga * 1.05
            else:
                scores["GA"] += base_ga

        # Leg/Foot Ulcers
        elif condition_name == "leg_foot_ulcers" or condition_name == "foot_ulcers":
            scores["SKN"] += 0.10
            scores["CM"] += 0.10

        # Liver Disease
        elif condition_name == "liver_disease":
            scores["DTX"] += 0.20
            scores["CM"] += 0.10

        # Osteoporosis (parental hip fracture)
        elif condition_name == "osteoporosis":
            base_hrm = 0.20

            # +10% if female patient
            if patient_sex and patient_sex.lower() == "female":
                scores["HRM"] += base_hrm * 1.10
            else:
                scores["HRM"] += base_hrm

        # Polio (record only)
        elif condition_name == "polio":
            pass  # Record only, no scoring

        # Pulmonary Embolism
        elif condition_name == "pulmonary_embolism":
            scores["CM"] += 0.20

        # Reflux or Ulcers
        elif condition_name == "reflux_or_ulcers" or condition_name == "reflux" or condition_name == "ulcers":
            scores["GA"] += 0.15

        # Stroke
        elif condition_name == "stroke":
            scores["COG"] += 0.20
            scores["CM"] += 0.10

        # Tuberculosis (record only)
        elif condition_name == "tuberculosis":
            pass  # Record only, no scoring

        return scores

    def _parse_other_conditions(self, other_text: str, patient_sex: str) -> Dict[str, Dict[str, float]]:
        """
        Parse other_conditions_text and map to known conditions.

        Returns:
            Dict mapping condition names to their scores
        """
        if not other_text:
            return {}

        other_text_lower = other_text.lower()
        parsed_conditions = {}

        # Celiac Disease
        if any(keyword in other_text_lower for keyword in ["celiac", "coeliac"]):
            parsed_conditions["Celiac Disease"] = {
                "GA": 0.20,
                "IMM": 0.05,
                **{code: 0.0 for code in FOCUS_AREAS if code not in ["GA", "IMM"]}
            }

        # IBD (Crohn's, Ulcerative Colitis)
        if any(keyword in other_text_lower for keyword in ["ibd", "crohn", "ulcerative colitis", "inflammatory bowel"]):
            parsed_conditions["IBD"] = {
                "GA": 0.20,
                "IMM": 0.10,
                **{code: 0.0 for code in FOCUS_AREAS if code not in ["GA", "IMM"]}
            }

        # Polyps
        if "polyp" in other_text_lower:
            parsed_conditions["Polyps"] = {
                "GA": 0.10,
                **{code: 0.0 for code in FOCUS_AREAS if code != "GA"}
            }

        # Barrett's Esophagus
        if "barrett" in other_text_lower:
            parsed_conditions["Barrett's Esophagus"] = {
                "GA": 0.15,
                **{code: 0.0 for code in FOCUS_AREAS if code != "GA"}
            }

        # Rheumatoid Arthritis (RA)
        if any(keyword in other_text_lower for keyword in ["rheumatoid", "ra ", " ra"]):
            parsed_conditions["Rheumatoid Arthritis"] = {
                "IMM": 0.20,
                **{code: 0.0 for code in FOCUS_AREAS if code != "IMM"}
            }

        # Psoriatic Arthritis
        if "psoriatic" in other_text_lower:
            parsed_conditions["Psoriatic Arthritis"] = {
                "IMM": 0.20,
                **{code: 0.0 for code in FOCUS_AREAS if code != "IMM"}
            }

        # Lupus
        if "lupus" in other_text_lower:
            parsed_conditions["Lupus"] = {
                "IMM": 0.20,
                **{code: 0.0 for code in FOCUS_AREAS if code != "IMM"}
            }

        # Multiple Sclerosis
        if any(keyword in other_text_lower for keyword in ["multiple sclerosis", "ms ", " ms"]):
            parsed_conditions["Multiple Sclerosis"] = {
                "IMM": 0.20,
                "COG": 0.10,
                **{code: 0.0 for code in FOCUS_AREAS if code not in ["IMM", "COG"]}
            }

        # Alzheimer's / Dementia
        if any(keyword in other_text_lower for keyword in ["alzheimer", "dementia"]):
            parsed_conditions["Alzheimer's/Dementia"] = {
                "COG": 0.25,
                **{code: 0.0 for code in FOCUS_AREAS if code != "COG"}
            }

        # Parkinson's
        if "parkinson" in other_text_lower:
            parsed_conditions["Parkinson's"] = {
                "COG": 0.20,
                "MITO": 0.10,
                **{code: 0.0 for code in FOCUS_AREAS if code not in ["COG", "MITO"]}
            }

        # Depression
        if "depression" in other_text_lower or "depressive" in other_text_lower:
            parsed_conditions["Depression"] = {
                "COG": 0.10,
                "STR": 0.10,
                **{code: 0.0 for code in FOCUS_AREAS if code not in ["COG", "STR"]}
            }

        # Bipolar
        if "bipolar" in other_text_lower:
            parsed_conditions["Bipolar Disorder"] = {
                "COG": 0.15,
                "STR": 0.10,
                **{code: 0.0 for code in FOCUS_AREAS if code not in ["COG", "STR"]}
            }

        # Schizophrenia
        if "schizophrenia" in other_text_lower:
            parsed_conditions["Schizophrenia"] = {
                "COG": 0.20,
                **{code: 0.0 for code in FOCUS_AREAS if code != "COG"}
            }

        # Eczema / Psoriasis
        if "eczema" in other_text_lower or "psoriasis" in other_text_lower:
            parsed_conditions["Eczema/Psoriasis"] = {
                "SKN": 0.15,
                "IMM": 0.10,
                **{code: 0.0 for code in FOCUS_AREAS if code not in ["SKN", "IMM"]}
            }

        # Melanoma
        if "melanoma" in other_text_lower:
            parsed_conditions["Melanoma"] = {
                "SKN": 0.20,
                "DTX": 0.10,
                **{code: 0.0 for code in FOCUS_AREAS if code not in ["SKN", "DTX"]}
            }

        # PCOS
        if "pcos" in other_text_lower or "polycystic ovary" in other_text_lower:
            parsed_conditions["PCOS"] = {
                "HRM": 0.20,
                "CM": 0.10,
                **{code: 0.0 for code in FOCUS_AREAS if code not in ["HRM", "CM"]}
            }

        # Endometriosis
        if "endometriosis" in other_text_lower:
            parsed_conditions["Endometriosis"] = {
                "HRM": 0.15,
                "IMM": 0.10,
                **{code: 0.0 for code in FOCUS_AREAS if code not in ["HRM", "IMM"]}
            }

        return parsed_conditions

