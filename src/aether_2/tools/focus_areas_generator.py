from crewai.tools import BaseTool
from typing import Type, Dict, ClassVar, Union
from pydantic import BaseModel, Field
import json


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
            height_ft = demographics.get("height_feet")
            height_in = demographics.get("height_inches")
            weight = demographics.get("weight_lbs")

            # total height in inches
            total_height_in = None
            if height_ft is not None and height_in is not None:
                total_height_in = int(height_ft) * 12 + int(height_in)

            bmi = None
            if total_height_in and weight:
                bmi = (weight / (total_height_in**2)) * 703

            # Apply rules
            age_scores = self._get_age_weights(age)
            bmi_scores = self._get_bmi_weights(bmi)
            height_scores = self._get_height_weights(total_height_in)

            scores = self._combine_scores(age_scores, bmi_scores, height_scores)

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
