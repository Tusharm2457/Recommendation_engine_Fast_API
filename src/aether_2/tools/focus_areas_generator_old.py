from crewai.tools import BaseTool
from typing import Type, Dict, ClassVar, Union, List, Any
from pydantic import BaseModel, Field
import json
import logging
from datetime import datetime
from .rulesets import AncestryRuleset, MedicalConditionsRuleset, AllergiesRuleset, SupplementsRuleset, FamilyHistoryRuleset, SmokingRuleset, AlcoholRuleset, WorkStressRuleset, ExerciseRuleset, SleepRuleset, SkinHealthRuleset, ChronicPainRuleset, HeadacheRuleset, MaleSexualHealthRuleset, FemaleReproductiveHealthRuleset, DigestiveSymptomsRuleset, PetAnimalsRuleset, MoldExposureRuleset, ChemicalExposureRuleset, OralHygieneRuleset, MercuryFillingRemovalRuleset, DentalWorkRuleset, ChildhoodDevelopmentRuleset, CSectionBirthRuleset, EatingOutFrequencyRuleset, SunlightExposureRuleset, SnoringApneaRuleset, WakeRefreshedRuleset, TroubleStayingAsleepRuleset, TroubleFallingAsleepRuleset, DietStyleRuleset


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
        if not hasattr(self, '_smoking_ruleset'):
            self._smoking_ruleset = SmokingRuleset()
        if not hasattr(self, '_alcohol_ruleset'):
            self._alcohol_ruleset = AlcoholRuleset()
        if not hasattr(self, '_work_stress_ruleset'):
            self._work_stress_ruleset = WorkStressRuleset()
        if not hasattr(self, '_exercise_ruleset'):
            self._exercise_ruleset = ExerciseRuleset()
        if not hasattr(self, '_sleep_ruleset'):
            self._sleep_ruleset = SleepRuleset()
        if not hasattr(self, '_skin_health_ruleset'):
            self._skin_health_ruleset = SkinHealthRuleset()
        if not hasattr(self, '_chronic_pain_ruleset'):
            self._chronic_pain_ruleset = ChronicPainRuleset()
        if not hasattr(self, '_headache_ruleset'):
            self._headache_ruleset = HeadacheRuleset()
        if not hasattr(self, '_male_sexual_health_ruleset'):
            self._male_sexual_health_ruleset = MaleSexualHealthRuleset()
        if not hasattr(self, '_female_reproductive_health_ruleset'):
            self._female_reproductive_health_ruleset = FemaleReproductiveHealthRuleset()
        if not hasattr(self, '_digestive_symptoms_ruleset'):
            self._digestive_symptoms_ruleset = DigestiveSymptomsRuleset()
        if not hasattr(self, '_pet_animals_ruleset'):
            self._pet_animals_ruleset = PetAnimalsRuleset()
        if not hasattr(self, '_mold_exposure_ruleset'):
            self._mold_exposure_ruleset = MoldExposureRuleset()
        if not hasattr(self, '_chemical_exposure_ruleset'):
            self._chemical_exposure_ruleset = ChemicalExposureRuleset()
        if not hasattr(self, '_oral_hygiene_ruleset'):
            self._oral_hygiene_ruleset = OralHygieneRuleset()
        if not hasattr(self, '_mercury_filling_removal_ruleset'):
            self._mercury_filling_removal_ruleset = MercuryFillingRemovalRuleset()
        if not hasattr(self, '_dental_work_ruleset'):
            self._dental_work_ruleset = DentalWorkRuleset()
        if not hasattr(self, '_childhood_development_ruleset'):
            self._childhood_development_ruleset = ChildhoodDevelopmentRuleset()
        if not hasattr(self, '_c_section_birth_ruleset'):
            self._c_section_birth_ruleset = CSectionBirthRuleset()
        if not hasattr(self, '_eating_out_frequency_ruleset'):
            self._eating_out_frequency_ruleset = EatingOutFrequencyRuleset()
        if not hasattr(self, '_sunlight_exposure_ruleset'):
            self._sunlight_exposure_ruleset = SunlightExposureRuleset()
        if not hasattr(self, '_snoring_apnea_ruleset'):
            self._snoring_apnea_ruleset = SnoringApneaRuleset()
        if not hasattr(self, '_wake_refreshed_ruleset'):
            self._wake_refreshed_ruleset = WakeRefreshedRuleset()
        if not hasattr(self, '_trouble_staying_asleep_ruleset'):
            self._trouble_staying_asleep_ruleset = TroubleStayingAsleepRuleset()
        if not hasattr(self, '_trouble_falling_asleep_ruleset'):
            self._trouble_falling_asleep_ruleset = TroubleFallingAsleepRuleset()
        if not hasattr(self, '_diet_style_ruleset'):
            self._diet_style_ruleset = DietStyleRuleset()

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
                                   supplements_data: List[Dict], family_history_data: Dict, tobacco_data: Dict, alcohol_data: Dict, occupation_data: Dict, physical_activity_data: Dict, skin_health_data: Dict, chronic_pain_data: Dict, headache_data: Dict, male_sexual_concerns: bool, female_reproductive_concerns: bool, digestive_symptoms_data: str, pets_animals_data: Dict, mold_exposure_data: Any, chemical_exposures_data: Any, oral_hygiene_data: Any, mercury_filling_data: Any, dental_work_data: Any, childhood_development_data: Any, c_section_birth_data: Any, eating_out_frequency_data: Any, sunlight_exposure_data: Any, snoring_apnea_data: Any, wake_refreshed_data: Any, trouble_staying_asleep_data: Any, trouble_falling_asleep_data: Any, diet_style_data: Any, age_scores: Dict[str, float], sex_scores: Dict[str, float],
                                   ancestry_scores: Dict[str, float], bmi_scores: Dict[str, float],
                                   height_scores: Dict[str, float], condition_scores: Dict[str, float],
                                   recency_modifier: Dict[str, float], therapy_toxicity_modifier: Dict[str, float],
                                   allergy_scores: Dict[str, float], allergy_integrative_addons: Dict[str, float],
                                   supplement_scores: Dict[str, float], family_history_scores: Dict[str, float], smoking_scores: Dict[str, float], alcohol_scores: Dict[str, float], work_stress_scores: Dict[str, float], exercise_scores: Dict[str, float], sleep_scores: Dict[str, float], skin_health_scores: Dict[str, float], chronic_pain_scores: Dict[str, float], headache_scores: Dict[str, float], male_sexual_health_scores: Dict[str, float], female_reproductive_health_scores: Dict[str, float], digestive_symptoms_scores: Dict[str, float], pet_animals_scores: Dict[str, float], mold_exposure_scores: Dict[str, float], chemical_exposure_scores: Dict[str, float], oral_hygiene_scores: Dict[str, float], mercury_filling_scores: Dict[str, float], dental_work_scores: Dict[str, float], childhood_development_scores: Dict[str, float], c_section_birth_scores: Dict[str, float], eating_out_frequency_scores: Dict[str, float], sunlight_exposure_scores: Dict[str, float], snoring_apnea_scores: Dict[str, float], wake_refreshed_scores: Dict[str, float], trouble_staying_asleep_scores: Dict[str, float], trouble_falling_asleep_scores: Dict[str, float], diet_style_scores: Dict[str, float], final_scores: Dict[str, float]) -> str:
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
            f"  Smoking Data: {tobacco_data}",
            f"  Alcohol Data: {alcohol_data}",
            f"  Work Stress Data: {occupation_data}",
            f"  Exercise Data: {physical_activity_data}",
            f"  Skin Health Data: {skin_health_data}",
            f"  Chronic Pain Data: {chronic_pain_data}",
            f"  Headache Data: {headache_data}",
            f"  Male Sexual Concerns: {male_sexual_concerns}",
            f"  Female Reproductive Concerns: {female_reproductive_concerns}",
            f"  Digestive Symptoms: {digestive_symptoms_data}",
            f"  Pets/Animals: {pets_animals_data}",
            f"  Mold Exposure: {mold_exposure_data}",
            f"  Chemical Exposures: {chemical_exposures_data}",
            f"  Oral Hygiene: {oral_hygiene_data}",
            f"  Mercury Filling Removal: {mercury_filling_data}",
            f"  Dental Work: {dental_work_data}",
            f"  Childhood Development: {childhood_development_data}",
            f"  C-Section Birth: {c_section_birth_data}",
            f"  Eating Out Frequency: {eating_out_frequency_data}",
            f"  Sunlight Exposure: {sunlight_exposure_data}",
            f"  Snoring/Sleep Apnea: {snoring_apnea_data}",
            f"  Wake Feeling Refreshed: {wake_refreshed_data}",
            f"  Trouble Staying Asleep: {trouble_staying_asleep_data}",
            f"  Trouble Falling Asleep: {trouble_falling_asleep_data}",
            f"  Diet Style: {diet_style_data}",
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
        
        # Smoking ruleset
        log_lines.extend([
            "10. SMOKING RULESET:",
            "   Smoking Status Weights:",
            self._format_scores_table(smoking_scores),
            ""
        ])
        
        # Alcohol ruleset
        log_lines.extend([
            "11. ALCOHOL RULESET:",
            "   Alcohol Consumption Weights:",
            self._format_scores_table(alcohol_scores),
            ""
        ])
        
        # Work stress ruleset
        log_lines.extend([
            "12. WORK STRESS RULESET:",
            "   Work Stress & Shift Work Weights:",
            self._format_scores_table(work_stress_scores),
            ""
        ])
        
        # Exercise ruleset
        log_lines.extend([
            "13. EXERCISE RULESET:",
            "   Exercise Frequency Weights:",
            self._format_scores_table(exercise_scores),
            ""
        ])
        
        # Sleep ruleset
        log_lines.extend([
            "14. SLEEP RULESET:",
            "   Sleep Duration & Quality Weights:",
            self._format_scores_table(sleep_scores),
            ""
        ])

        # Skin health ruleset
        log_lines.extend([
            "15. SKIN HEALTH RULESET:",
            "   Skin Condition Weights:",
            self._format_scores_table(skin_health_scores),
            ""
        ])

        # Chronic pain ruleset
        log_lines.extend([
            "16. CHRONIC PAIN RULESET:",
            "   Chronic Pain Weights:",
            self._format_scores_table(chronic_pain_scores),
            ""
        ])

        # Headache ruleset
        log_lines.extend([
            "17. HEADACHE RULESET:",
            "   Headache/Migraine Weights:",
            self._format_scores_table(headache_scores),
            ""
        ])

        # Male sexual health ruleset
        log_lines.extend([
            "18. MALE SEXUAL HEALTH RULESET:",
            "   Male Sexual Health Weights:",
            self._format_scores_table(male_sexual_health_scores),
            ""
        ])

        # Female reproductive health ruleset
        log_lines.extend([
            "19. FEMALE REPRODUCTIVE HEALTH RULESET:",
            "   Female Reproductive Health Weights:",
            self._format_scores_table(female_reproductive_health_scores),
            ""
        ])

        # Digestive symptoms ruleset
        log_lines.extend([
            "20. DIGESTIVE SYMPTOMS RULESET:",
            "   Digestive Symptoms Weights:",
            self._format_scores_table(digestive_symptoms_scores),
            ""
        ])

        # Pet animals ruleset
        log_lines.extend([
            "21. PET ANIMALS RULESET:",
            "   Pet Animals Weights:",
            self._format_scores_table(pet_animals_scores),
            ""
        ])

        # Mold exposure ruleset
        log_lines.extend([
            "22. MOLD EXPOSURE RULESET:",
            "   Mold Exposure Weights:",
            self._format_scores_table(mold_exposure_scores),
            ""
        ])

        # Chemical exposure ruleset
        log_lines.extend([
            "23. CHEMICAL EXPOSURE RULESET:",
            "   Chemical Exposure Weights:",
            self._format_scores_table(chemical_exposure_scores),
            ""
        ])

        # Oral hygiene ruleset
        log_lines.extend([
            "24. ORAL HYGIENE RULESET:",
            "   Oral Hygiene Weights:",
            self._format_scores_table(oral_hygiene_scores),
            ""
        ])

        # Mercury filling removal ruleset
        log_lines.extend([
            "25. MERCURY FILLING REMOVAL RULESET:",
            "   Mercury Filling Removal Weights:",
            self._format_scores_table(mercury_filling_scores),
            ""
        ])

        # Dental work ruleset
        log_lines.extend([
            "26. DENTAL WORK RULESET:",
            "   Dental Work Weights:",
            self._format_scores_table(dental_work_scores),
            ""
        ])

        # Childhood development ruleset
        log_lines.extend([
            "27. CHILDHOOD DEVELOPMENT RULESET:",
            "   Childhood Development Weights:",
            self._format_scores_table(childhood_development_scores),
            ""
        ])

        # C-section birth ruleset
        log_lines.extend([
            "28. C-SECTION BIRTH RULESET:",
            "   C-Section Birth Weights:",
            self._format_scores_table(c_section_birth_scores),
            ""
        ])

        # Eating out frequency ruleset
        log_lines.extend([
            "29. EATING OUT FREQUENCY RULESET:",
            "   Eating Out Frequency Weights:",
            self._format_scores_table(eating_out_frequency_scores),
            ""
        ])

        # Sunlight exposure ruleset
        log_lines.extend([
            "30. SUNLIGHT EXPOSURE RULESET:",
            "   Sunlight Exposure Weights:",
            self._format_scores_table(sunlight_exposure_scores),
            ""
        ])

        # Snoring/sleep apnea ruleset
        log_lines.extend([
            "31. SNORING/SLEEP APNEA RULESET:",
            "   Snoring/Sleep Apnea Weights:",
            self._format_scores_table(snoring_apnea_scores),
            ""
        ])

        # Wake feeling refreshed ruleset
        log_lines.extend([
            "32. WAKE FEELING REFRESHED RULESET:",
            "   Wake Feeling Refreshed Weights:",
            self._format_scores_table(wake_refreshed_scores),
            ""
        ])

        # Trouble staying asleep ruleset
        log_lines.extend([
            "33. TROUBLE STAYING ASLEEP RULESET:",
            "   Trouble Staying Asleep Weights:",
            self._format_scores_table(trouble_staying_asleep_scores),
            ""
        ])

        # Trouble falling asleep ruleset
        log_lines.extend([
            "34. TROUBLE FALLING ASLEEP RULESET:",
            "   Trouble Falling Asleep Weights:",
            self._format_scores_table(trouble_falling_asleep_scores),
            ""
        ])

        # Diet style ruleset
        log_lines.extend([
            "35. DIET STYLE RULESET:",
            "   Diet Style Weights:",
            self._format_scores_table(diet_style_scores),
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
            
            # Smoking data
            lifestyle_factors = phase2_data.get("lifestyle_factors", {})
            tobacco_data = lifestyle_factors.get("tobacco", {})
            
            # Alcohol data
            alcohol_data = lifestyle_factors.get("alcohol", {})
            
            # Work stress data
            occupation_data = phase2_data.get("occupation_wellness", {})
            sleep_data = phase2_data.get("sleep_patterns", {})
            
            # Exercise data
            physical_activity_data = phase2_data.get("physical_activity", {})

            # Skin health data
            pain_and_skin_health = phase2_data.get("pain_and_skin_health", {})
            skin_health_data = pain_and_skin_health.get("skin_health", {})

            # Chronic pain data
            chronic_pain_data = pain_and_skin_health.get("chronic_pain", {})

            # Headache data
            headache_data = pain_and_skin_health.get("headaches", {})

            # Reproductive/hormonal health
            reproductive_health = phase2_data.get("reproductive_hormonal_health", {})
            male_specific = reproductive_health.get("male_specific", {}) if reproductive_health else {}
            male_sexual_concerns = male_specific.get("has_concerns", False) if male_specific else False

            female_specific = reproductive_health.get("female_specific", {}) if reproductive_health else {}
            female_reproductive_concerns = False
            female_concern_details = ""
            if female_specific:
                menstrual_concerns = female_specific.get("menstrual_concerns", "no")
                if menstrual_concerns and menstrual_concerns.lower() in ["yes", "y", "true"]:
                    female_reproductive_concerns = True
                    female_concern_details = female_specific.get("concern_details", "")

            # Systems review (for digestive symptoms)
            systems_review = phase2_data.get("systems_review", {})
            digestive_symptoms = systems_review.get("digestive_symptoms", "")

            # Dietary habits
            dietary_habits = phase2_data.get("dietary_habits", {})

            # Dental health
            dental_health = phase2_data.get("dental_health", {})
            daily_brush_floss = dental_health.get("daily_brush_floss", "")
            mercury_fillings_removed = dental_health.get("mercury_fillings_removed", False)
            removal_timeframe = dental_health.get("removal_timeframe", None)
            dental_work = dental_health.get("dental_work", {})

            # Childhood development
            childhood_development = phase2_data.get("childhood_development", {})
            high_sugar_childhood_diet = childhood_development.get("high_sugar_childhood_diet", "")
            born_via_c_section = childhood_development.get("born_via_c_section", "")

            # Environmental exposures
            environmental_exposures = phase2_data.get("environmental_exposures", {})

            # Pets and animals
            pets_animals_data = phase2_data.get("pets_animals", {})

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
            if not tobacco_data:
                tobacco_data = patient_form.get("tobacco", {})
            if not alcohol_data:
                alcohol_data = patient_form.get("alcohol", {})
            if not occupation_data:
                occupation_data = patient_form.get("occupation_wellness", {})
            if not sleep_data:
                sleep_data = patient_form.get("sleep_patterns", {})
            if not physical_activity_data:
                physical_activity_data = patient_form.get("physical_activity", {})

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
            
            # Smoking ruleset
            smoking_scores = self._smoking_ruleset.get_smoking_weights(tobacco_data)
            
            # Alcohol ruleset
            alcohol_scores = self._alcohol_ruleset.get_alcohol_weights(alcohol_data, sex)
            
            # Work stress ruleset
            work_stress_scores = self._work_stress_ruleset.get_work_stress_weights(occupation_data, sleep_data)
            
            # Exercise ruleset
            exercise_scores = self._exercise_ruleset.get_exercise_weights(physical_activity_data)
            
            # Sleep ruleset (needs cross-field data for comprehensive scoring)
            shift_work_flag = self._work_stress_ruleset._detect_shift_work(occupation_data.get("job_title", ""))
            
            # Determine heavy alcohol consumption
            alcohol_frequency = alcohol_data.get("frequency", "").lower()
            heavy_alcohol = alcohol_frequency in ["daily", "sometimes"]  # Simplified check
            
            systems_review = phase2_data.get("systems_review", {})
            
            sleep_scores = self._sleep_ruleset.get_sleep_weights(
                sleep_data, age, shift_work_flag, heavy_alcohol, medical_conditions, systems_review
            )

            # Skin health ruleset
            skin_health_scores = self._skin_health_ruleset.get_skin_health_weights(
                age, skin_health_data, medical_conditions, current_meds, current_supplements,
                digestive_symptoms, dietary_habits, environmental_exposures, alcohol_data
            )

            # Chronic pain ruleset
            biomarkers = patient_form.get("biomarkers", {})
            chronic_pain_scores = self._chronic_pain_ruleset.get_chronic_pain_weights(
                age, chronic_pain_data, medical_conditions, current_meds, current_supplements,
                digestive_symptoms, sleep_data, dietary_habits, physical_activity_data, biomarkers
            )

            # Headache ruleset
            headache_scores = self._headache_ruleset.get_headache_weights(
                age, headache_data, sex, medical_conditions, current_meds, current_supplements,
                digestive_symptoms, sleep_data, dietary_habits, alcohol_data,
                environmental_exposures, reproductive_health
            )

            # Male sexual health ruleset
            male_sexual_health_scores = self._male_sexual_health_ruleset.get_male_sexual_health_weights(
                age, sex, male_sexual_concerns, medical_conditions, current_meds,
                bmi, environmental_exposures, lifestyle_factors
            )

            # Female reproductive health ruleset
            surgeries = patient_form.get("surgeries_procedures", [])
            female_reproductive_health_scores = self._female_reproductive_health_ruleset.get_female_reproductive_health_weights(
                age, sex, female_reproductive_concerns, female_concern_details,
                medical_conditions, current_meds, surgeries, digestive_symptoms, female_specific
            )

            # Digestive symptoms ruleset
            symptom_details = systems_review.get("symptom_details", "") if systems_review else ""
            digestive_symptoms_scores = self._digestive_symptoms_ruleset.get_digestive_symptoms_weights(
                digestive_symptoms, current_meds, surgeries, dietary_habits, symptom_details
            )

            # Pet animals ruleset
            pet_animals_scores = self._pet_animals_ruleset.get_pet_animals_weights(
                pets_animals_data, known_allergies, medical_conditions
            )

            # Mold exposure ruleset
            mold_exposure = environmental_exposures.get("mold_exposure", False)
            mold_exposure_scores = self._mold_exposure_ruleset.get_mold_exposure_weights(
                mold_exposure, environmental_exposures, medical_conditions, digestive_symptoms, known_allergies
            )

            # Chemical exposure ruleset
            chemical_exposures = environmental_exposures.get("chemical_exposures", [])
            chemical_exposure_other = environmental_exposures.get("chemical_exposure_other", "")
            chemical_exposure_scores = self._chemical_exposure_ruleset.get_chemical_exposure_weights(
                chemical_exposures, chemical_exposure_other, digestive_symptoms, medical_conditions
            )

            # Oral hygiene ruleset
            oral_hygiene_scores = self._oral_hygiene_ruleset.get_oral_hygiene_weights(
                daily_brush_floss, medical_conditions, medications, digestive_symptoms, dietary_habits
            )

            # Mercury filling removal ruleset
            mercury_filling_scores = self._mercury_filling_removal_ruleset.get_mercury_filling_removal_weights(
                mercury_fillings_removed, removal_timeframe, dental_work, digestive_symptoms
            )

            # Dental work ruleset
            dental_work_scores = self._dental_work_ruleset.get_dental_work_weights(
                dental_work, medical_conditions, ""
            )

            # Childhood development ruleset
            childhood_development_scores = self._childhood_development_ruleset.get_childhood_development_weights(
                high_sugar_childhood_diet, born_via_c_section, medical_conditions, family_history_data, dietary_habits, bmi
            )

            # C-section birth ruleset
            c_section_birth_scores = self._c_section_birth_ruleset.get_c_section_birth_weights(
                born_via_c_section, medical_conditions, known_allergies, digestive_symptoms
            )

            # Eating out frequency ruleset
            eating_out_frequency = dietary_habits.get("eating_out_frequency", "")
            eating_out_frequency_scores = self._eating_out_frequency_ruleset.get_eating_out_frequency_weights(
                eating_out_frequency, age, medical_conditions
            )

            # Sunlight exposure ruleset
            sunlight_exposure = phase2_data.get("sunlight_exposure", {})
            sunlight_exposure_scores = self._sunlight_exposure_ruleset.get_sunlight_exposure_weights(
                sunlight_exposure, age, medical_conditions, medications, occupation_data, None
            )

            # Snoring/sleep apnea ruleset
            sleep_patterns = phase2_data.get("sleep_patterns", {})
            snoring_sleep_apnea = sleep_patterns.get("snoring_sleep_apnea", "")
            snoring_apnea_scores = self._snoring_apnea_ruleset.get_snoring_apnea_weights(
                snoring_sleep_apnea, sleep_patterns, medical_conditions, bmi, age, sex, alcohol_data, tobacco_data, occupation_data
            )

            # Wake feeling refreshed ruleset
            wake_feeling_refreshed = sleep_patterns.get("wake_feeling_refreshed", None)
            # Determine if OSA is suspected from snoring/apnea answer
            osa_suspected = str(snoring_sleep_apnea).lower().strip() in ["yes", "y", "true"]
            wake_refreshed_scores = self._wake_refreshed_ruleset.get_wake_refreshed_weights(
                wake_feeling_refreshed, sleep_patterns, medical_conditions, digestive_symptoms, alcohol_data, occupation_data, osa_suspected
            )

            # Trouble staying asleep ruleset
            trouble_staying_asleep = sleep_patterns.get("trouble_staying_asleep", None)
            night_wake_frequency = sleep_patterns.get("night_wake_frequency", None)
            trouble_staying_asleep_scores = self._trouble_staying_asleep_ruleset.get_trouble_staying_asleep_weights(
                trouble_staying_asleep, night_wake_frequency, medical_conditions, digestive_symptoms, sex, alcohol_data, tobacco_data, occupation_data
            )

            # Trouble falling asleep ruleset
            trouble_falling_asleep = sleep_patterns.get("trouble_falling_asleep", None)
            trouble_falling_asleep_scores = self._trouble_falling_asleep_ruleset.get_trouble_falling_asleep_weights(
                trouble_falling_asleep, medical_conditions, digestive_symptoms, alcohol_data, tobacco_data, occupation_data
            )

            # Diet style ruleset
            dietary_habits = phase2_data.get("dietary_habits", {})
            diet_style = dietary_habits.get("diet_style", None)
            diet_style_scores = self._diet_style_ruleset.get_diet_style_weights(
                diet_style, age, medical_conditions, digestive_symptoms, supplements_data
            )

            scores = self._combine_scores(
                age_scores, sex_scores, ancestry_scores, bmi_scores, height_scores,
                condition_scores, recency_modifier, therapy_toxicity_modifier,
                allergy_scores, allergy_integrative_addons, supplement_scores, family_history_scores, smoking_scores, alcohol_scores, work_stress_scores, exercise_scores, sleep_scores, skin_health_scores, chronic_pain_scores, headache_scores, male_sexual_health_scores, female_reproductive_health_scores, digestive_symptoms_scores, pet_animals_scores, mold_exposure_scores, chemical_exposure_scores, oral_hygiene_scores, mercury_filling_scores, dental_work_scores, childhood_development_scores, c_section_birth_scores, eating_out_frequency_scores, sunlight_exposure_scores, snoring_apnea_scores, wake_refreshed_scores, trouble_staying_asleep_scores, trouble_falling_asleep_scores, diet_style_scores
            )

            # Create comprehensive weight breakdown log
            log_content = self._create_weight_breakdown_log(
                age, sex, ancestry, bmi, total_height_in,
                medical_conditions, medications, allergies_data, supplements_data, family_history_data, tobacco_data, alcohol_data, occupation_data, physical_activity_data, skin_health_data, chronic_pain_data, headache_data, male_sexual_concerns, female_reproductive_concerns, digestive_symptoms, pets_animals_data, mold_exposure, chemical_exposures, daily_brush_floss, mercury_fillings_removed, dental_work, high_sugar_childhood_diet, born_via_c_section, eating_out_frequency, sunlight_exposure, snoring_sleep_apnea, wake_feeling_refreshed, trouble_staying_asleep, trouble_falling_asleep, diet_style,
                age_scores, sex_scores, ancestry_scores, bmi_scores, height_scores,
                condition_scores, recency_modifier, therapy_toxicity_modifier,
                allergy_scores, allergy_integrative_addons, supplement_scores, family_history_scores, smoking_scores, alcohol_scores, work_stress_scores, exercise_scores, sleep_scores, skin_health_scores, chronic_pain_scores, headache_scores, male_sexual_health_scores, female_reproductive_health_scores, digestive_symptoms_scores, pet_animals_scores, mold_exposure_scores, chemical_exposure_scores, oral_hygiene_scores, mercury_filling_scores, dental_work_scores, childhood_development_scores, c_section_birth_scores, eating_out_frequency_scores, sunlight_exposure_scores, snoring_apnea_scores, wake_refreshed_scores, trouble_staying_asleep_scores, trouble_falling_asleep_scores, diet_style_scores, scores
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
