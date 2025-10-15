from crewai.tools import BaseTool
from typing import Type, Dict, ClassVar, Union, List
from pydantic import BaseModel, Field
import json
import logging
from datetime import datetime
from .rulesets import AncestryRuleset, MedicalConditionsRuleset, AllergiesRuleset, SupplementsRuleset, FamilyHistoryRuleset


class EvaluateFocusAreasInput(BaseModel):
    patient_and_blood_data: Union[str, dict] = Field(
        ..., description="JSON string OR dict with keys: patient_form, blood_report"
    )


class EvaluateFocusAreasTool(BaseTool):
    name: str = "evaluate_user_focus_areas"
    description: str = (
        "Evaluates user's medical data and returns a ranked list of health focus areas "
        "using rule-based scoring (age, BMI, height, etc.)."
    )
    args_schema: Type[BaseModel] = EvaluateFocusAreasInput
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize rulesets as class attributes to avoid Pydantic field issues
        if not hasattr(self, '_ancestry_ruleset'):
            self._ancestry_ruleset = AncestryRuleset()
        if not hasattr(self, '_medical_conditions_ruleset'):
            self._medical_conditions_ruleset = MedicalConditionsRuleset()
        if not hasattr(self, '_allergies_ruleset'):
            self._allergies_ruleset = AllergiesRuleset()
        if not hasattr(self, '_supplements_ruleset'):
            self._supplements_ruleset = SupplementsRuleset()
        if not hasattr(self, '_family_history_ruleset'):
            self._family_history_ruleset = FamilyHistoryRuleset()

    FOCUS_AREAS: ClassVar[Dict[str, str]] = {
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

    # -------------------
    # AGE RULESET (as before)
    # -------------------
    def _get_age_weights(self, age: int) -> Dict[str, float]:
        if age is None:
            return {code: 0.0 for code in self.FOCUS_AREAS.keys()}

        if 18 <= age <= 25:
            return {"CM": 0.30, "COG": 0.50, "DTX": 0.30, "IMM": 0.30,
                    "MITO": 0.30, "SKN": 0.40, "STR": 0.40, "HRM": 0.50, "GA": 0.30}
        elif 26 <= age <= 39:
            return {"CM": 0.40, "COG": 0.30, "DTX": 0.30, "IMM": 0.20,
                    "MITO": 0.30, "SKN": 0.20, "STR": 0.50, "HRM": 0.40, "GA": 0.30}
        elif 40 <= age <= 49:
            return {"CM": 0.50, "COG": 0.30, "DTX": 0.30, "IMM": 0.30,
                    "MITO": 0.40, "SKN": 0.30, "STR": 0.50, "HRM": 0.50, "GA": 0.30}
        elif 50 <= age <= 59:
            return {"CM": 0.60, "COG": 0.40, "DTX": 0.40, "IMM": 0.30,
                    "MITO": 0.50, "SKN": 0.40, "STR": 0.40, "HRM": 0.60, "GA": 0.40}
        elif 60 <= age <= 69:
            return {"CM": 0.70, "COG": 0.60, "DTX": 0.50, "IMM": 0.50,
                    "MITO": 0.60, "SKN": 0.50, "STR": 0.40, "HRM": 0.30, "GA": 0.50}
        elif age >= 70:
            return {"CM": 0.80, "COG": 0.70, "DTX": 0.60, "IMM": 0.60,
                    "MITO": 0.70, "SKN": 0.60, "STR": 0.30, "HRM": 0.20, "GA": 0.60}
        else:
            return {code: 0.0 for code in self.FOCUS_AREAS.keys()}

    # -------------------
    # BMI RULESET (from your table)
    # -------------------
    def _get_bmi_weights(self, bmi: float) -> Dict[str, float]:
        if bmi is None:
            return {code: 0.0 for code in self.FOCUS_AREAS.keys()}

        if bmi < 18.5:  # Underweight
            return {"CM": 0.20, "COG": 0.30, "DTX": 0.30, "IMM": 0.50,
                    "MITO": 0.50, "SKN": 0.30, "STR": 0.30, "HRM": 0.30, "GA": 0.60}
        elif bmi < 25:  # Healthy
            return {"CM": 0.20, "COG": 0.20, "DTX": 0.20, "IMM": 0.20,
                    "MITO": 0.20, "SKN": 0.20, "STR": 0.25, "HRM": 0.20, "GA": 0.20}
        elif bmi < 30:  # Overweight
            return {"CM": 0.50, "COG": 0.30, "DTX": 0.35, "IMM": 0.35,
                    "MITO": 0.40, "SKN": 0.30, "STR": 0.30, "HRM": 0.40, "GA": 0.30}
        elif bmi < 35:  # Obesity I
            return {"CM": 0.60, "COG": 0.40, "DTX": 0.50, "IMM": 0.45,
                    "MITO": 0.50, "SKN": 0.40, "STR": 0.35, "HRM": 0.50, "GA": 0.40}
        elif bmi < 40:  # Obesity II
            return {"CM": 0.70, "COG": 0.45, "DTX": 0.55, "IMM": 0.50,
                    "MITO": 0.60, "SKN": 0.50, "STR": 0.35, "HRM": 0.50, "GA": 0.45}
        else:  # Obesity III
            return {"CM": 0.80, "COG": 0.50, "DTX": 0.60, "IMM": 0.60,
                    "MITO": 0.70, "SKN": 0.60, "STR": 0.35, "HRM": 0.50, "GA": 0.50}

    # -------------------
    # SEX RULESET (physiology-informed priors)
    # -------------------
    def _get_sex_weights(self, sex: str) -> Dict[str, float]:
        if sex is None:
            return {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        
        sex_lower = sex.lower()
        
        if sex_lower == "female":
            # Higher IBS prevalence, stronger HPA reactivity, sex-biased immune patterns, dominant estrogen/progesterone axis
            return {"CM": 0.20, "COG": 0.20, "DTX": 0.20, "IMM": 0.25,
                    "MITO": 0.20, "SKN": 0.20, "STR": 0.25, "HRM": 0.35, "GA": 0.25}
        elif sex_lower == "male":
            # Earlier cardiovascular risk timing, androgen pathway (DHEA-S) generally higher
            return {"CM": 0.25, "COG": 0.20, "DTX": 0.20, "IMM": 0.20,
                    "MITO": 0.20, "SKN": 0.20, "STR": 0.20, "HRM": 0.30, "GA": 0.20}
        else:
            # Other/Intersex/Prefer to self-describe - heterogeneous physiology, minority-stress burden
            return {"CM": 0.22, "COG": 0.22, "DTX": 0.22, "IMM": 0.22,
                    "MITO": 0.22, "SKN": 0.20, "STR": 0.30, "HRM": 0.35, "GA": 0.22}

    # -------------------
    # ANCESTRY RULESET (epidemiology/physiology-based adjustments)
    # -------------------

    # -------------------
    # HEIGHT RULESET (from your table)
    # -------------------
    def _get_height_weights(self, height_in: int) -> Dict[str, float]:
        if height_in is None:
            return {code: 0.0 for code in self.FOCUS_AREAS.keys()}

        if height_in <= 60:  # Very short
            return {"CM": 0.30, "COG": 0.15, "DTX": 0.15, "IMM": 0.15,
                    "MITO": 0.20, "SKN": 0.10, "STR": 0.15, "HRM": 0.15, "GA": 0.15}
        elif 61 <= height_in <= 64:  # Short
            return {"CM": 0.25, "COG": 0.15, "DTX": 0.15, "IMM": 0.15,
                    "MITO": 0.15, "SKN": 0.10, "STR": 0.15, "HRM": 0.15, "GA": 0.10}
        elif 65 <= height_in <= 75:  # Average
            return {"CM": 0.15, "COG": 0.10, "DTX": 0.10, "IMM": 0.10,
                    "MITO": 0.10, "SKN": 0.10, "STR": 0.10, "HRM": 0.10, "GA": 0.10}
        elif 76 <= height_in <= 77:  # Tall
            return {"CM": 0.25, "COG": 0.10, "DTX": 0.10, "IMM": 0.10,
                    "MITO": 0.15, "SKN": 0.10, "STR": 0.10, "HRM": 0.10, "GA": 0.10}
        else:  # Very tall ≥78
            return {"CM": 0.30, "COG": 0.10, "DTX": 0.10, "IMM": 0.10,
                    "MITO": 0.20, "SKN": 0.10, "STR": 0.10, "HRM": 0.10, "GA": 0.10}

    # -------------------
    # MEDICAL CONDITIONS RULESET (evidence-based condition-to-domain mapping)
    # -------------------

    # -------------------
    # ALLERGIES RULESET (allergy-to-domain mapping with severity modifiers)
    # -------------------

    # -------------------
    # Logging System
    # -------------------
    def _create_weight_breakdown_log(self, 
                                   age: int, sex: str, ancestry: List[str], bmi: float, height_in: int,
                                   medical_conditions: List[str], medications: List[str], allergies_data: List[Dict],
                                   supplements_data: List[Dict], family_history_data: Dict, age_scores: Dict[str, float], sex_scores: Dict[str, float], 
                                   ancestry_scores: Dict[str, float], bmi_scores: Dict[str, float], 
                                   height_scores: Dict[str, float], condition_scores: Dict[str, float],
                                   recency_modifier: Dict[str, float], therapy_toxicity_modifier: Dict[str, float],
                                   allergy_scores: Dict[str, float], allergy_integrative_addons: Dict[str, float],
                                   supplement_scores: Dict[str, float], family_history_scores: Dict[str, float], final_scores: Dict[str, float]) -> str:
        """
        Create a comprehensive log of how each ruleset contributed to the final scores.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_lines = [
            "=" * 80,
            f"FOCUS AREA EVALUATION WEIGHT BREAKDOWN - {timestamp}",
            "=" * 80,
            "",
            "PATIENT INPUT DATA:",
            f"  Age: {age}",
            f"  Sex: {sex}",
            f"  Ancestry: {ancestry}",
            f"  BMI: {bmi:.2f}" if bmi else "  BMI: None",
            f"  Height: {height_in} inches" if height_in else "  Height: None",
            f"  Medical Conditions: {medical_conditions}",
            f"  Medications: {medications}",
            f"  Allergies: {allergies_data}",
            f"  Supplements: {supplements_data}",
            f"  Family History: {family_history_data}",
            "",
            "RULESET WEIGHT CONTRIBUTIONS:",
            ""
        ]
        
        # Basic demographic rulesets
        log_lines.extend([
            "1. AGE RULESET:",
            self._format_scores_table(age_scores),
            ""
        ])
        
        log_lines.extend([
            "2. SEX RULESET:",
            self._format_scores_table(sex_scores),
            ""
        ])
        
        log_lines.extend([
            "3. ANCESTRY RULESET:",
            self._format_scores_table(ancestry_scores),
            ""
        ])
        
        log_lines.extend([
            "4. BMI RULESET:",
            self._format_scores_table(bmi_scores),
            ""
        ])
        
        log_lines.extend([
            "5. HEIGHT RULESET:",
            self._format_scores_table(height_scores),
            ""
        ])
        
        # Medical conditions ruleset
        log_lines.extend([
            "6. MEDICAL CONDITIONS RULESET:",
            "   Base Condition Weights:",
            self._format_scores_table(condition_scores),
            "   Recency Modifier:",
            self._format_scores_table(recency_modifier),
            "   Therapy/Toxicity Modifier:",
            self._format_scores_table(therapy_toxicity_modifier),
            ""
        ])
        
        # Allergies ruleset
        log_lines.extend([
            "7. ALLERGIES RULESET:",
            "   Base Allergy Weights:",
            self._format_scores_table(allergy_scores),
            "   Integrative Add-ons:",
            self._format_scores_table(allergy_integrative_addons),
            ""
        ])
        
        # Supplements ruleset
        log_lines.extend([
            "8. SUPPLEMENTS RULESET:",
            "   Medication/Supplement Weights:",
            self._format_scores_table(supplement_scores),
            ""
        ])
        
        # Family history ruleset
        log_lines.extend([
            "9. FAMILY HISTORY RULESET:",
            "   Family Condition Weights:",
            self._format_scores_table(family_history_scores),
            ""
        ])
        
        # Final combined scores
        log_lines.extend([
            "FINAL COMBINED SCORES:",
            self._format_scores_table(final_scores),
            ""
        ])
        
        # Top 3 focus areas
        ranked_areas = sorted(
            [(self.FOCUS_AREAS[code], code, score) for code, score in final_scores.items()],
            key=lambda x: x[2],
            reverse=True
        )
        
        log_lines.extend([
            "TOP 3 FOCUS AREAS:",
            f"  1. {ranked_areas[0][0]} ({ranked_areas[0][1]}): {ranked_areas[0][2]:.3f}",
            f"  2. {ranked_areas[1][0]} ({ranked_areas[1][1]}): {ranked_areas[1][2]:.3f}",
            f"  3. {ranked_areas[2][0]} ({ranked_areas[2][1]}): {ranked_areas[2][2]:.3f}",
            "",
            "=" * 80
        ])
        
        return "\n".join(log_lines)
    
    def _format_scores_table(self, scores: Dict[str, float]) -> str:
        """Format scores dictionary as a readable table."""
        if not any(score > 0 for score in scores.values()):
            return "     (No weights applied)"
        
        lines = []
        for code, score in scores.items():
            if score > 0:
                focus_area = self.FOCUS_AREAS[code]
                lines.append(f"     {focus_area} ({code}): {score:.3f}")
        
        return "\n".join(lines) if lines else "     (No weights applied)"
    
    def _save_log_to_file(self, log_content: str, patient_id: str = "patient_1") -> str:
        """Save the log content to a file."""
        import os
        
        # Create outputs directory if it doesn't exist
        output_dir = f"outputs/{patient_id}"
        os.makedirs(output_dir, exist_ok=True)
        
        # Save log file
        log_file_path = f"{output_dir}/focus_areas_weight_breakdown.log"
        with open(log_file_path, 'w') as f:
            f.write(log_content)
        
        return log_file_path

    # -------------------
    # Combiner
    # -------------------
    def _combine_scores(self, *rulesets) -> Dict[str, float]:
        combined = {code: 0.0 for code in self.FOCUS_AREAS.keys()}
        for rules in rulesets:
            for code, score in rules.items():
                combined[code] += score
        return combined

    # -------------------
    # Main execution
    # -------------------
    def _run(self, patient_and_blood_data: Union[str, dict]) -> str:
        try:
            if isinstance(patient_and_blood_data, str):
                data = json.loads(patient_and_blood_data)
            else:
                data = patient_and_blood_data

            if "patient_and_blood_data" in data:
                data = data["patient_and_blood_data"]

            patient_form = data.get("patient_form", {})
            demographics = (
                patient_form.get("patient_data", {})
                            .get("phase1_basic_intake", {})
                            .get("demographics", {})
            )

            age = demographics.get("age")
            sex = demographics.get("biological_sex")
            ancestry = demographics.get("ancestry", [])
            height_ft = demographics.get("height_feet")
            height_in = demographics.get("height_inches")
            weight = demographics.get("weight_lbs")

            # Extract medical conditions, medications, allergies, supplements, and family history
            medical_conditions = []
            medications = []
            allergies_data = []
            supplements_data = []
            family_history_data = {}
            
            # Extract from the correct paths based on actual data structure
            phase1_data = patient_form.get("patient_data", {}).get("phase1_basic_intake", {})
            phase2_data = patient_form.get("patient_data", {}).get("phase2_detailed_intake", {})
            
            # Medical conditions (diagnoses)
            medical_history = phase1_data.get("medical_history", {})
            medical_conditions = medical_history.get("diagnoses", [])
            
            # Medications
            medications_section = phase1_data.get("medications", {})
            current_meds = medications_section.get("current_medications", [])
            # Extract medication names from the medication objects
            medications = [med.get("name", "") for med in current_meds if med.get("name")]
            
            # Allergies
            allergies_section = phase1_data.get("allergies", {})
            known_allergies = allergies_section.get("known_allergies", [])
            # Convert allergy strings to allergy objects with allergen and reaction
            allergies_data = [{"allergen": allergy, "reaction": "unknown"} for allergy in known_allergies]
            
            # Supplements
            supplements_section = phase1_data.get("supplements", {})
            current_supplements = supplements_section.get("current_supplements", [])
            # Keep full supplement objects for detailed analysis
            supplements_data = current_supplements
            
            # Family history
            family_medical_history = phase2_data.get("family_medical_history", {})
            family_history_data = family_medical_history
            
            # Alternative extraction paths (fallback)
            if not medical_conditions:
                medical_conditions = patient_form.get("medical_conditions", [])
            if not medications:
                medications = patient_form.get("medications", [])
            if not allergies_data:
                allergies_data = patient_form.get("allergies", [])
            if not supplements_data:
                supplements_data = patient_form.get("supplements", [])
            if not family_history_data:
                family_history_data = patient_form.get("family_history", {})

            # total height in inches
            total_height_in = None
            if height_ft is not None and height_in is not None:
                total_height_in = int(height_ft) * 12 + int(height_in)

            bmi = None
            if total_height_in and weight:
                bmi = (weight / (total_height_in**2)) * 703

            # Apply rules
            age_scores = self._get_age_weights(age)
            sex_scores = self._get_sex_weights(sex)
            ancestry_scores = self._ancestry_ruleset.get_ancestry_weights(ancestry)
            bmi_scores = self._get_bmi_weights(bmi)
            height_scores = self._get_height_weights(total_height_in)
            
            # Medical conditions ruleset
            condition_scores = self._medical_conditions_ruleset.get_medical_condition_weights(medical_conditions)
            recency_modifier = self._medical_conditions_ruleset.get_recency_modifier(medical_conditions)
            therapy_toxicity_modifier = self._medical_conditions_ruleset.get_therapy_toxicity_modifier(medications)
            
            # Allergies ruleset
            allergy_scores = self._allergies_ruleset.get_allergy_weights(allergies_data)
            allergy_integrative_addons = self._allergies_ruleset.get_integrative_addons(medications)
            
            # Supplements ruleset
            supplement_scores = self._supplements_ruleset.get_supplement_medication_weights(supplements_data, medications)
            
            # Family history ruleset
            family_history_scores = self._family_history_ruleset.get_family_history_weights(family_history_data, sex)

            scores = self._combine_scores(
                age_scores, sex_scores, ancestry_scores, bmi_scores, height_scores,
                condition_scores, recency_modifier, therapy_toxicity_modifier,
                allergy_scores, allergy_integrative_addons, supplement_scores, family_history_scores
            )

            # Create comprehensive weight breakdown log
            log_content = self._create_weight_breakdown_log(
                age, sex, ancestry, bmi, total_height_in,
                medical_conditions, medications, allergies_data, supplements_data, family_history_data,
                age_scores, sex_scores, ancestry_scores, bmi_scores, height_scores,
                condition_scores, recency_modifier, therapy_toxicity_modifier,
                allergy_scores, allergy_integrative_addons, supplement_scores, family_history_scores, scores
            )
            
            # Save log to file
            log_file_path = self._save_log_to_file(log_content)
            
            # Print log to console for immediate visibility
            print(f"\n{log_content}\n")
            print(f"📊 Detailed weight breakdown saved to: {log_file_path}")

            # Rank
            ranked_focus_areas = sorted(
                [(self.FOCUS_AREAS[code], code, score) for code, score in scores.items()],
                key=lambda x: x[2],
                reverse=True,
            )

            result = ["Focus Areas Ranking:"]
            for focus_area, code, score in ranked_focus_areas:
                result.append(f"{focus_area} ({code}): {score:.2f}")

            return "\n".join(result)

        except Exception as e:
            return f"Error evaluating focus areas: {str(e)}"
