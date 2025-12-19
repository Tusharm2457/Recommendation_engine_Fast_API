"""
Focus Areas Generator Tool - Refactored Version
Evaluates patient data and generates weighted scores for 9 health focus areas.
"""

from crewai.tools import BaseTool
from typing import Type, Dict, Union, List, Any
from pydantic import BaseModel, Field
import json
import os
from datetime import datetime

from .rulesets import AgeRuleset, AncestryRuleset, BMIRuleset, SexRuleset, HeightRuleset, AllergiesRuleset, DiagnosisRuleset, SurgeriesRuleset, MedicationsRuleset, SupplementsRuleset, FamilyHistoryRuleset, MedicationSideEffectsRuleset, ChildhoodAntibioticsRuleset, TobaccoRuleset, AlcoholRuleset, RecreationalDrugsRuleset, WorkStressRuleset, PhysicalActivityRuleset, SunlightRuleset, SleepHoursRuleset, TroubleFallingAsleepRuleset, TroubleStayingAsleepRuleset, WakeFeelingRefreshedRuleset, SnoringApneaRuleset, DietaryHabitsRuleset, EatingOutRuleset, CSectionRuleset, HighSugarChildhoodDietRuleset, SkinHealthRuleset, ChronicPainRuleset, DigestiveSymptomRuleset, FemaleHormonalHealthRuleset, MaleHormonalHealthRuleset, HeadacheRuleset, PetsAnimalsRuleset, MoldExposureRuleset
from .rulesets.constants import FOCUS_AREAS, FOCUS_AREA_NAMES, add_top_contributors, detect_shift_work
from .rulesets.data_extractor import extract_phase1_phase2_data


class EvaluateFocusAreasInput(BaseModel):
    patient_and_blood_data: Union[str, dict] = Field(
        ..., description="JSON string OR dict with keys: patient_form, blood_report"
    )


class EvaluateFocusAreasTool(BaseTool):
    name: str = "evaluate_user_focus_areas"
    description: str = (
        "Evaluates user's medical data and returns a ranked list of health focus areas "
        "using rule-based scoring across demographics, medical history, and lifestyle factors."
    )
    args_schema: Type[BaseModel] = EvaluateFocusAreasInput

    # Configuration: Number of top contributors to track per ruleset
    TOP_N_CONTRIBUTORS: int = 1

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def _extract_patient_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract all fields from patient_and_blood_data structure.

        This method now uses the shared data extractor to maintain consistency
        and avoid code duplication with Phase 3.
        """
        return extract_phase1_phase2_data(data)

    def _initialize_scores(self) -> Dict[str, float]:
        """Initialize all focus area scores to 0.0."""
        return {code: 0.0 for code in FOCUS_AREAS}

    def _combine_scores(self, *score_dicts: Dict[str, float]) -> Dict[str, float]:
        """Combine multiple score dictionaries by adding their values."""
        combined = self._initialize_scores()
        for score_dict in score_dicts:
            for code, score in score_dict.items():
                if code in combined:
                    combined[code] += score
        return combined

    def _create_log_entry(self, ruleset_name: str, scores: Dict[str, float],
                         input_data: Any = None) -> str:
        """Create a log entry for a ruleset's contribution."""
        lines = [f"\n--- {ruleset_name.upper()} RULESET ---"]
        if input_data is not None:
            lines.append(f"Input: {input_data}")
        lines.append("Scores:")
        for code, score in scores.items():
            if score != 0.0:
                lines.append(f"  {code}: +{score:.3f}")
        if all(score == 0.0 for score in scores.values()):
            lines.append("  (No contribution)")
        return "\n".join(lines)

    def _save_log_file(self, log_content: str, patient_id: str = "unknown") -> str:
        """Save log content to a file."""
        output_dir = f"outputs/{patient_id}"
        os.makedirs(output_dir, exist_ok=True)

        log_file_path = f"{output_dir}/focus_areas_weight_breakdown_phase2.log"
        with open(log_file_path, 'w') as f:
            f.write(log_content)

        return log_file_path

    def _save_reasons_file(self, reasons: Dict[str, List[str]], patient_id: str = "unknown") -> str:
        """Save reasons dictionary to a JSON file."""
        import json

        output_dir = f"outputs/{patient_id}"
        os.makedirs(output_dir, exist_ok=True)

        reasons_file_path = f"{output_dir}/focus_areas_reasons_phase2.json"
        with open(reasons_file_path, 'w') as f:
            json.dump(reasons, f, indent=2)

        return reasons_file_path

    def _format_markdown_output(self, final_scores: Dict[str, float]) -> str:
        """Format the final scores as markdown output."""
        sorted_areas = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

        lines = [
            "# Focus Area Evaluation Results",
            "",
            "## Ranked Focus Areas (by weighted score)",
            ""
        ]

        for code, score in sorted_areas:
            area_name = FOCUS_AREA_NAMES[code]
            lines.append(f"- **{area_name} ({code})**: {score:.2f}")

        return "\n".join(lines)

    def _run(self, patient_and_blood_data: Union[str, dict]) -> str:
        """Main execution method for the tool."""
        try:
            if isinstance(patient_and_blood_data, str):
                data = json.loads(patient_and_blood_data)
            else:
                data = patient_and_blood_data

            extracted_data = self._extract_patient_data(data)
            final_scores = self._initialize_scores()

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_lines = [
                "="*80,
                f"FOCUS AREA EVALUATION - {timestamp}",
                "="*80,
                "",
                "PATIENT DATA SUMMARY:",
                f"  Age: {extracted_data['age']}",
                f"  Sex: {extracted_data['biological_sex']}",
                f"  BMI: {extracted_data['bmi']:.2f}" if extracted_data['bmi'] else "  BMI: None",
                "",
                "RULESET CONTRIBUTIONS:",
                ""
            ]

            # Initialize rulesets
            age_ruleset = AgeRuleset()
            ancestry_ruleset = AncestryRuleset()
            bmi_ruleset = BMIRuleset()
            sex_ruleset = SexRuleset()
            height_ruleset = HeightRuleset()
            allergies_ruleset = AllergiesRuleset()
            diagnosis_ruleset = DiagnosisRuleset()
            surgeries_ruleset = SurgeriesRuleset()
            medications_ruleset = MedicationsRuleset()
            supplements_ruleset = SupplementsRuleset()
            family_history_ruleset = FamilyHistoryRuleset()
            medication_side_effects_ruleset = MedicationSideEffectsRuleset()
            childhood_antibiotics_ruleset = ChildhoodAntibioticsRuleset()
            tobacco_ruleset = TobaccoRuleset()
            alcohol_ruleset = AlcoholRuleset()
            recreational_drugs_ruleset = RecreationalDrugsRuleset()
            work_stress_ruleset = WorkStressRuleset()
            physical_activity_ruleset = PhysicalActivityRuleset()
            sunlight_ruleset = SunlightRuleset()
            sleep_hours_ruleset = SleepHoursRuleset()
            trouble_falling_asleep_ruleset = TroubleFallingAsleepRuleset()
            trouble_staying_asleep_ruleset = TroubleStayingAsleepRuleset()
            wake_feeling_refreshed_ruleset = WakeFeelingRefreshedRuleset()
            snoring_apnea_ruleset = SnoringApneaRuleset()
            dietary_habits_ruleset = DietaryHabitsRuleset()
            eating_out_ruleset = EatingOutRuleset()
            c_section_ruleset = CSectionRuleset()
            high_sugar_childhood_diet_ruleset = HighSugarChildhoodDietRuleset()
            skin_health_ruleset = SkinHealthRuleset()
            chronic_pain_ruleset = ChronicPainRuleset()
            digestive_symptom_ruleset = DigestiveSymptomRuleset()
            female_hormonal_health_ruleset = FemaleHormonalHealthRuleset()
            male_hormonal_health_ruleset = MaleHormonalHealthRuleset()
            headache_ruleset = HeadacheRuleset()
            pets_animals_ruleset = PetsAnimalsRuleset()
            mold_exposure_ruleset = MoldExposureRuleset()

            # Initialize reasons dictionary
            reasons = {code: [] for code in FOCUS_AREAS}

            # Apply Age Ruleset
            age_scores = age_ruleset.get_age_weights(extracted_data['age'])
            add_top_contributors(reasons, age_scores, "Age", extracted_data['age'], top_n=self.TOP_N_CONTRIBUTORS)
            log_lines.append(self._create_log_entry("Age", age_scores, extracted_data['age']))
            final_scores = self._combine_scores(final_scores, age_scores)

            # Apply Ancestry Ruleset
            ancestry_scores = ancestry_ruleset.get_ancestry_weights(
                extracted_data['ancestry'],
                extracted_data['ancestry_other'],
                extracted_data['alcohol_frequency'],
                extracted_data['digestive_symptoms'],
                extracted_data['diagnoses'],
                extracted_data['family_conditions_detail']
            )
            add_top_contributors(reasons, ancestry_scores, "Ancestry", extracted_data['ancestry'], top_n=self.TOP_N_CONTRIBUTORS)
            ancestry_display = extracted_data['ancestry'] or []
            if extracted_data['ancestry_other']:
                ancestry_display = ancestry_display + [f"Other: {extracted_data['ancestry_other']}"]
            log_lines.append(self._create_log_entry("Ancestry", ancestry_scores, ancestry_display))
            final_scores = self._combine_scores(final_scores, ancestry_scores)

            # Apply BMI Ruleset
            bmi_scores = bmi_ruleset.get_bmi_weights(extracted_data['bmi'])
            add_top_contributors(reasons, bmi_scores, "BMI", extracted_data['bmi'], top_n=self.TOP_N_CONTRIBUTORS)
            log_lines.append(self._create_log_entry("BMI", bmi_scores, extracted_data['bmi']))
            final_scores = self._combine_scores(final_scores, bmi_scores)

            # Apply Sex Ruleset
            sex_scores = sex_ruleset.get_sex_weights(extracted_data['biological_sex'])
            add_top_contributors(reasons, sex_scores, "Sex", extracted_data['biological_sex'], top_n=self.TOP_N_CONTRIBUTORS)
            log_lines.append(self._create_log_entry("Sex", sex_scores, extracted_data['biological_sex']))
            final_scores = self._combine_scores(final_scores, sex_scores)

            # Apply Height Ruleset
            height_scores = height_ruleset.get_height_weights(extracted_data['height_total_inches'])
            add_top_contributors(reasons, height_scores, "Height", extracted_data['height_total_inches'], top_n=self.TOP_N_CONTRIBUTORS)
            log_lines.append(self._create_log_entry("Height", height_scores, extracted_data['height_total_inches']))
            final_scores = self._combine_scores(final_scores, height_scores)

            # Apply Allergies Ruleset
            allergy_scores, per_allergen_breakdown = allergies_ruleset.get_allergies_weights(
                extracted_data['has_allergies'],
                extracted_data['allergen_list'],
                extracted_data['reaction_list']
            )

            # Track reasons per allergen
            for allergen_name, allergen_scores in per_allergen_breakdown.items():
                add_top_contributors(
                    reasons,
                    allergen_scores,
                    "Allergy",
                    allergen_name,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log cumulative allergy scores
            log_lines.append(self._create_log_entry("Allergies", allergy_scores, extracted_data['allergen_list']))
            final_scores = self._combine_scores(final_scores, allergy_scores)

            # Apply Diagnosis Ruleset
            diagnosis_scores, per_diagnosis_breakdown = diagnosis_ruleset.get_diagnosis_weights(
                extracted_data['diagnosis_list'],
                extracted_data['diagnosis_years_list']
            )

            # Track reasons per diagnosis
            for diagnosis_name, diagnosis_scores_single in per_diagnosis_breakdown.items():
                add_top_contributors(
                    reasons,
                    diagnosis_scores_single,
                    "Diagnosis",
                    diagnosis_name,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log cumulative diagnosis scores
            log_lines.append(self._create_log_entry("Diagnoses", diagnosis_scores, extracted_data['diagnosis_list']))
            final_scores = self._combine_scores(final_scores, diagnosis_scores)

            # Apply Surgeries Ruleset
            surgery_scores, per_surgery_breakdown = surgeries_ruleset.get_surgeries_weights(
                surgeries_text=extracted_data['surgeries'],
                digestive_symptoms=extracted_data['digestive_symptoms'],
                alcohol_frequency=extracted_data['alcohol_frequency'],
                current_medications=extracted_data['current_medications']
            )

            # Track reasons per surgery
            for surgery_original_text, surgery_scores_single in per_surgery_breakdown.items():
                add_top_contributors(
                    reasons,
                    surgery_scores_single,
                    "Surgery",
                    surgery_original_text,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log cumulative surgery scores
            surgery_names = list(per_surgery_breakdown.keys())
            log_lines.append(self._create_log_entry("Surgeries", surgery_scores, surgery_names))
            final_scores = self._combine_scores(final_scores, surgery_scores)

            # Apply Medications Ruleset
            med_scores, per_med_breakdown = medications_ruleset.get_medications_weights(
                current_medications=extracted_data['current_medications']
            )

            # Track reasons per medication
            for med_name, med_scores_single in per_med_breakdown.items():
                add_top_contributors(
                    reasons,
                    med_scores_single,
                    "Medication",
                    med_name,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log cumulative medication scores
            med_names = list(per_med_breakdown.keys())
            log_lines.append(self._create_log_entry("Medications", med_scores, med_names))
            final_scores = self._combine_scores(final_scores, med_scores)

            # Apply Supplements Ruleset
            supp_scores, per_supp_breakdown = supplements_ruleset.get_supplements_weights(
                current_supplements=extracted_data['current_supplements'],
                digestive_symptoms=extracted_data['digestive_symptoms']
            )

            # Track reasons per supplement
            for supp_name, supp_scores_single in per_supp_breakdown.items():
                add_top_contributors(
                    reasons,
                    supp_scores_single,
                    "Supplement",
                    supp_name,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log cumulative supplement scores
            supp_names = list(per_supp_breakdown.keys())
            log_lines.append(self._create_log_entry("Supplements", supp_scores, supp_names))
            final_scores = self._combine_scores(final_scores, supp_scores)

            # Apply Family History Ruleset
            fam_hist_scores, per_fam_condition_breakdown = family_history_ruleset.get_family_history_weights(
                has_family_history=extracted_data['has_family_history'],
                family_conditions_detail=extracted_data['family_conditions_detail'],
                family_other_conditions=extracted_data['family_other_conditions'],
                patient_sex=extracted_data['biological_sex']
            )

            # Track reasons per family condition
            for condition_name, condition_scores_single in per_fam_condition_breakdown.items():
                add_top_contributors(
                    reasons,
                    condition_scores_single,
                    "FamilyHistory",
                    condition_name,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log cumulative family history scores
            fam_condition_names = list(per_fam_condition_breakdown.keys())
            log_lines.append(self._create_log_entry("Family History", fam_hist_scores, fam_condition_names))
            final_scores = self._combine_scores(final_scores, fam_hist_scores)

            # Apply Medication Side Effects Ruleset
            med_side_effects_scores, per_pattern_breakdown = medication_side_effects_ruleset.get_medication_side_effects_weights(
                has_adverse_reactions=extracted_data['has_adverse_reactions'],
                reaction_details=extracted_data['reaction_details'],
                current_medications=extracted_data['current_medications'],
                current_supplements=extracted_data['current_supplements']
            )

            # Track reasons using reaction_details text (not pattern names)
            if extracted_data['has_adverse_reactions'] and extracted_data['reaction_details']:
                add_top_contributors(
                    reasons,
                    med_side_effects_scores,
                    "MedSideEffect",
                    extracted_data['reaction_details'],
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log cumulative medication side effects scores
            pattern_names = list(per_pattern_breakdown.keys())
            log_lines.append(self._create_log_entry("Medication Side Effects", med_side_effects_scores, pattern_names))
            final_scores = self._combine_scores(final_scores, med_side_effects_scores)

            # Apply Childhood Antibiotics Ruleset
            childhood_abx_scores = childhood_antibiotics_ruleset.get_childhood_antibiotics_weights(
                took_antibiotics_as_child=extracted_data['took_antibiotics_as_child']
            )

            # Track reasons
            if extracted_data['took_antibiotics_as_child']:
                add_top_contributors(
                    reasons,
                    childhood_abx_scores,
                    "ChildhoodAntibiotics",
                    "Yes",
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log childhood antibiotics scores
            log_lines.append(self._create_log_entry("Childhood Antibiotics", childhood_abx_scores, [extracted_data['took_antibiotics_as_child']]))
            final_scores = self._combine_scores(final_scores, childhood_abx_scores)

            # Apply Tobacco Ruleset
            tobacco_scores, tobacco_description = tobacco_ruleset.get_tobacco_weights(
                use_status=extracted_data['tobacco_use_status'],
                quit_year=extracted_data['tobacco_quit_year'],
                duration_category=extracted_data['tobacco_duration_category']
            )

            # Track reasons with detailed description
            if tobacco_description:
                add_top_contributors(
                    reasons,
                    tobacco_scores,
                    "Tobacco",
                    tobacco_description,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log tobacco scores
            log_lines.append(self._create_log_entry("Tobacco", tobacco_scores, [tobacco_description if tobacco_description else "Never"]))
            final_scores = self._combine_scores(final_scores, tobacco_scores)

            # Apply Alcohol Ruleset
            alcohol_scores, alcohol_description = alcohol_ruleset.get_alcohol_weights(
                frequency=extracted_data['alcohol_frequency'],
                typical_amount=extracted_data['alcohol_typical_amount'],
                sex=extracted_data['biological_sex']
            )

            # Track reasons with detailed description
            if alcohol_description:
                add_top_contributors(
                    reasons,
                    alcohol_scores,
                    "Alcohol",
                    alcohol_description,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log alcohol scores
            log_lines.append(self._create_log_entry("Alcohol", alcohol_scores, [alcohol_description if alcohol_description else "None"]))
            final_scores = self._combine_scores(final_scores, alcohol_scores)

            # Apply Recreational Drugs Ruleset
            rec_drugs_scores, rec_drugs_description = recreational_drugs_ruleset.get_recreational_drugs_weights(
                uses_substances=extracted_data['uses_substances'],
                substance_details=extracted_data['substance_details'],
                digestive_symptoms=extracted_data['digestive_symptoms']
            )

            # Track reasons with detailed description
            if rec_drugs_description:
                add_top_contributors(
                    reasons,
                    rec_drugs_scores,
                    "RecDrugs",
                    rec_drugs_description,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log recreational drugs scores
            log_lines.append(self._create_log_entry("Recreational Drugs", rec_drugs_scores, [rec_drugs_description if rec_drugs_description else "None"]))
            final_scores = self._combine_scores(final_scores, rec_drugs_scores)

            # Detect shift work once (used by multiple rulesets)
            shift_work_flag = detect_shift_work(extracted_data['job_title'])

            # Apply Work Stress Ruleset
            # Determine if user has poor sleep
            has_poor_sleep = (
                extracted_data['trouble_falling_asleep'] or
                extracted_data['trouble_staying_asleep'] or
                not extracted_data['wake_feeling_refreshed']
            )

            # Determine if user has stress-reactive skin conditions
            skin_conditions = ['eczema', 'psoriasis', 'acne', 'dermatitis', 'rosacea']
            has_skin_conditions = any(
                condition in diagnosis.lower()
                for diagnosis in extracted_data['diagnosis_list']
                for condition in skin_conditions
            )

            work_stress_scores, work_stress_description = work_stress_ruleset.get_work_stress_weights(
                work_stress_level=extracted_data['work_stress_level'],
                shift_work=shift_work_flag,
                has_poor_sleep=has_poor_sleep,
                has_skin_conditions=has_skin_conditions
            )

            # Track reasons with detailed description
            if work_stress_description:
                add_top_contributors(
                    reasons,
                    work_stress_scores,
                    "WorkStress",
                    work_stress_description,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log work stress scores
            log_lines.append(self._create_log_entry("Work Stress", work_stress_scores, [work_stress_description if work_stress_description else "None"]))
            final_scores = self._combine_scores(final_scores, work_stress_scores)

            # Apply Physical Activity Ruleset
            activity_scores, activity_description = physical_activity_ruleset.get_physical_activity_weights(
                exercise_days_per_week=extracted_data['exercise_days_per_week'],
                digestive_symptoms=extracted_data['digestive_symptoms']
            )

            # Track reasons with detailed description
            if activity_description:
                add_top_contributors(
                    reasons,
                    activity_scores,
                    "PhysicalActivity",
                    activity_description,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log physical activity scores
            log_lines.append(self._create_log_entry("Physical Activity", activity_scores, [activity_description if activity_description else "None"]))
            final_scores = self._combine_scores(final_scores, activity_scores)

            # Apply Sunlight Ruleset
            sunlight_scores, sunlight_description = sunlight_ruleset.get_sunlight_weights(
                days_per_week=extracted_data['sunlight_days_per_week'],
                avg_minutes_per_day=extracted_data['sunlight_avg_minutes'],
                vitamin_d_optimal=extracted_data['vitamin_d_optimal'],
                shift_work=shift_work_flag,
                current_medications=extracted_data['current_medications']
            )

            # Track reasons with detailed description
            if sunlight_description:
                add_top_contributors(
                    reasons,
                    sunlight_scores,
                    "Sunlight",
                    sunlight_description,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log sunlight scores
            log_lines.append(self._create_log_entry("Sunlight", sunlight_scores, [sunlight_description if sunlight_description else "None"]))
            final_scores = self._combine_scores(final_scores, sunlight_scores)

            # Apply Sleep Hours Ruleset
            # For now, we don't have fatigue detection, so defaulting to False
            has_fatigue = False  # TODO: Add fatigue detection from diagnosis or symptoms

            sleep_hours_scores, sleep_hours_description = sleep_hours_ruleset.get_sleep_hours_weights(
                sleep_hours_category=extracted_data['sleep_hours_category'],
                age=extracted_data['age'],
                shift_work=shift_work_flag,
                has_fatigue=has_fatigue
            )

            # Track reasons with detailed description
            if sleep_hours_description:
                add_top_contributors(
                    reasons,
                    sleep_hours_scores,
                    "SleepHours",
                    sleep_hours_description,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log sleep hours scores
            log_lines.append(self._create_log_entry("Sleep Hours", sleep_hours_scores, [sleep_hours_description if sleep_hours_description else "None"]))
            final_scores = self._combine_scores(final_scores, sleep_hours_scores)

            # Apply Trouble Falling Asleep Ruleset
            # Determine if currently smoking
            currently_smoking = extracted_data['tobacco_use_status'] and extracted_data['tobacco_use_status'].lower() == "yes"

            trouble_asleep_scores, trouble_asleep_description = trouble_falling_asleep_ruleset.get_trouble_falling_asleep_weights(
                trouble_falling_asleep=extracted_data['trouble_falling_asleep'],
                shift_work=shift_work_flag,
                alcohol_frequency=extracted_data['alcohol_frequency'],
                currently_smoking=currently_smoking
            )

            # Track reasons with detailed description
            if trouble_asleep_description:
                add_top_contributors(
                    reasons,
                    trouble_asleep_scores,
                    "TroubleFallingAsleep",
                    trouble_asleep_description,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log trouble falling asleep scores
            log_lines.append(self._create_log_entry("Trouble Falling Asleep", trouble_asleep_scores, [trouble_asleep_description if trouble_asleep_description else "None"]))
            final_scores = self._combine_scores(final_scores, trouble_asleep_scores)

            # Apply Trouble Staying Asleep Ruleset
            trouble_staying_scores, trouble_staying_description = trouble_staying_asleep_ruleset.get_trouble_staying_asleep_weights(
                trouble_staying_asleep=extracted_data['trouble_staying_asleep'],
                night_wake_frequency=extracted_data['night_wake_frequency'],
                night_urination_frequency=extracted_data['night_urination_frequency'],
                digestive_symptoms=extracted_data['digestive_symptoms'],
                biological_sex=extracted_data['biological_sex']
            )

            # Track reasons with detailed description
            if trouble_staying_description:
                add_top_contributors(
                    reasons,
                    trouble_staying_scores,
                    "TroubleStayingAsleep",
                    trouble_staying_description,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log trouble staying asleep scores
            log_lines.append(self._create_log_entry("Trouble Staying Asleep", trouble_staying_scores, [trouble_staying_description if trouble_staying_description else "None"]))
            final_scores = self._combine_scores(final_scores, trouble_staying_scores)

            # Apply Wake Feeling Refreshed Ruleset
            wake_refreshed_scores, wake_refreshed_description = wake_feeling_refreshed_ruleset.get_wake_feeling_refreshed_weights(
                wake_feeling_refreshed=extracted_data['wake_feeling_refreshed'],
                digestive_symptoms=extracted_data['digestive_symptoms'],
                diagnoses=extracted_data['diagnoses_string'],
                shift_work=shift_work_flag,
                alcohol_frequency=extracted_data['alcohol_frequency'],
                sleep_hours_category=extracted_data['sleep_hours_category'],
                trouble_staying_asleep=extracted_data['trouble_staying_asleep']
            )

            # Track reasons with detailed description
            if wake_refreshed_description:
                add_top_contributors(
                    reasons,
                    wake_refreshed_scores,
                    "WakeFeelingRefreshed",
                    wake_refreshed_description,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log wake feeling refreshed scores
            log_lines.append(self._create_log_entry("Wake Feeling Refreshed", wake_refreshed_scores, [wake_refreshed_description if wake_refreshed_description else "None"]))
            final_scores = self._combine_scores(final_scores, wake_refreshed_scores)

            # Apply Snoring/Sleep Apnea Ruleset
            snoring_apnea_scores, snoring_apnea_description = snoring_apnea_ruleset.get_snoring_apnea_weights(
                snoring_sleep_apnea=extracted_data['snoring_sleep_apnea'],
                digestive_symptoms=extracted_data['digestive_symptoms'],
                wake_feeling_refreshed=extracted_data['wake_feeling_refreshed'],
                diagnoses=extracted_data['diagnoses_string'],
                bmi=extracted_data['bmi'],
                age=extracted_data['age'],
                biological_sex=extracted_data['biological_sex'],
                night_wake_frequency=extracted_data['night_wake_frequency'],
                alcohol_frequency=extracted_data['alcohol_frequency'],
                tobacco_use_status=extracted_data['tobacco_use_status'],
                shift_work=shift_work_flag,
                trouble_staying_asleep=extracted_data['trouble_staying_asleep']
            )

            # Track reasons with detailed description
            if snoring_apnea_description:
                add_top_contributors(
                    reasons,
                    snoring_apnea_scores,
                    "SnoringApnea",
                    snoring_apnea_description,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log snoring/sleep apnea scores
            log_lines.append(self._create_log_entry("Snoring/Sleep Apnea", snoring_apnea_scores, [snoring_apnea_description if snoring_apnea_description else "None"]))
            final_scores = self._combine_scores(final_scores, snoring_apnea_scores)

            # Apply Dietary Habits Ruleset
            dietary_scores, dietary_descriptions = dietary_habits_ruleset.get_dietary_habits_weights(
                diet_style=extracted_data['diet_style'],
                diet_style_other=extracted_data['diet_style_other'],
                digestive_symptoms=extracted_data['digestive_symptoms'],
                biological_sex=extracted_data['biological_sex'],
                supplements=extracted_data['supplements_string']
            )

            # Track reasons with detailed descriptions
            if dietary_descriptions:
                for description in dietary_descriptions:
                    add_top_contributors(
                        reasons,
                        dietary_scores,
                        "Diet",
                        description,
                        top_n=self.TOP_N_CONTRIBUTORS
                    )

            # Log dietary habits scores
            log_lines.append(self._create_log_entry("Dietary Habits", dietary_scores, dietary_descriptions if dietary_descriptions else ["None"]))
            final_scores = self._combine_scores(final_scores, dietary_scores)

            # Apply Eating Out Frequency Ruleset
            eating_out_scores, eating_out_description = eating_out_ruleset.get_eating_out_weights(
                eating_out_frequency=extracted_data['eating_out_frequency'],
                diagnoses=extracted_data['diagnoses_string']
            )

            # Track reasons with detailed description
            if eating_out_description:
                add_top_contributors(
                    reasons,
                    eating_out_scores,
                    "EatingOut",
                    eating_out_description,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log eating out scores
            log_lines.append(self._create_log_entry("Eating Out Frequency", eating_out_scores, [eating_out_description if eating_out_description else "None"]))
            final_scores = self._combine_scores(final_scores, eating_out_scores)

            # Apply C-Section Birth Ruleset
            c_section_scores, c_section_description = c_section_ruleset.get_c_section_weights(
                born_via_c_section=extracted_data['born_via_c_section'],
                has_allergies=extracted_data['has_allergies'],
                diagnoses=extracted_data['diagnoses_string'],
                digestive_symptoms=extracted_data['digestive_symptoms'],
                took_antibiotics_as_child=extracted_data['took_antibiotics_as_child']
            )

            # Track reasons with detailed description
            if c_section_description:
                add_top_contributors(
                    reasons,
                    c_section_scores,
                    "Born_via_CSection",
                    c_section_description,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log C-section scores
            log_lines.append(self._create_log_entry("C-Section Birth", c_section_scores, [c_section_description if c_section_description else "None"]))
            final_scores = self._combine_scores(final_scores, c_section_scores)

            # Apply High Sugar Childhood Diet Ruleset
            high_sugar_scores, high_sugar_description = high_sugar_childhood_diet_ruleset.get_high_sugar_childhood_diet_weights(
                high_sugar_childhood_diet=extracted_data['high_sugar_childhood_diet']
            )

            # Track reasons with detailed description
            if high_sugar_description:
                add_top_contributors(
                    reasons,
                    high_sugar_scores,
                    "HighSugarChildhoodDiet",
                    high_sugar_description,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log high sugar childhood diet scores
            log_lines.append(self._create_log_entry("High Sugar Childhood Diet", high_sugar_scores, [high_sugar_description if high_sugar_description else "None"]))
            final_scores = self._combine_scores(final_scores, high_sugar_scores)

            # Apply Skin Health Ruleset
            skin_health_scores, skin_health_descriptions = skin_health_ruleset.get_skin_health_weights(
                has_skin_issues=extracted_data['has_skin_issues'],
                skin_condition_details=extracted_data['skin_condition_details'],
                diagnoses=extracted_data['diagnoses_string'],
                digestive_symptoms=extracted_data['digestive_symptoms'],
                current_medications=extracted_data['current_medications'],
                diet_style=extracted_data['diet_style'],
                chemical_exposures=extracted_data['chemical_exposures'],
                alcohol_frequency=extracted_data['alcohol_frequency']
            )

            # Track reasons with detailed descriptions
            if skin_health_descriptions:
                for description in skin_health_descriptions:
                    add_top_contributors(
                        reasons,
                        skin_health_scores,
                        "SkinHealth",
                        description,
                        top_n=self.TOP_N_CONTRIBUTORS
                    )

            # Log skin health scores
            log_lines.append(self._create_log_entry("Skin Health", skin_health_scores, skin_health_descriptions if skin_health_descriptions else ["None"]))
            final_scores = self._combine_scores(final_scores, skin_health_scores)

            # Apply Chronic Pain Ruleset
            chronic_pain_scores, chronic_pain_descriptions = chronic_pain_ruleset.get_chronic_pain_weights(
                has_chronic_pain=extracted_data['has_chronic_pain'],
                pain_details=extracted_data['pain_details'],
                digestive_symptoms=extracted_data['digestive_symptoms'],
                current_medications=extracted_data['current_medications'],
                sleep_hours=extracted_data['sleep_hours_category'],
                trouble_staying_asleep=extracted_data['trouble_staying_asleep'],
                diagnoses=extracted_data['diagnoses_string'],
                diet_style=extracted_data['diet_style'],
                current_supplements=extracted_data['supplements_string'],
                vitamin_d_level=extracted_data['vitamin_d_level'],
                exercise_days_per_week=extracted_data['exercise_days_per_week']
            )

            # Track reasons with detailed descriptions
            if chronic_pain_descriptions:
                for description in chronic_pain_descriptions:
                    add_top_contributors(
                        reasons,
                        chronic_pain_scores,
                        "ChronicPain",
                        description,
                        top_n=self.TOP_N_CONTRIBUTORS
                    )

            # Log chronic pain scores
            log_lines.append(self._create_log_entry("Chronic Pain", chronic_pain_scores, chronic_pain_descriptions if chronic_pain_descriptions else ["None"]))
            final_scores = self._combine_scores(final_scores, chronic_pain_scores)

            # Apply Digestive Symptom Ruleset
            digestive_scores, per_symptom_breakdown = digestive_symptom_ruleset.get_digestive_symptom_weights(
                digestive_symptoms=extracted_data['digestive_symptoms']
            )

            # Track reasons per symptom
            for symptom_name, symptom_scores in per_symptom_breakdown.items():
                add_top_contributors(
                    reasons,
                    symptom_scores,
                    "DigestiveSymptoms",
                    symptom_name,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log digestive symptom scores
            symptom_list = list(per_symptom_breakdown.keys()) if per_symptom_breakdown else ["None"]
            log_lines.append(self._create_log_entry("Digestive Symptoms", digestive_scores, symptom_list))
            final_scores = self._combine_scores(final_scores, digestive_scores)

            # Apply Female Hormonal Health Ruleset
            female_hormonal_scores, female_hormonal_descriptions = female_hormonal_health_ruleset.get_female_hormonal_health_weights(
                biological_sex=extracted_data['biological_sex'],
                age=extracted_data['age'],
                menstrual_concerns=extracted_data['female_menstrual_concerns'],
                concern_details=extracted_data['female_concern_details'],
                diagnoses=extracted_data['diagnoses_string'],
                digestive_symptoms=extracted_data['digestive_symptoms'],
                surgeries=extracted_data['surgeries'],
                current_medications=extracted_data['current_medications'],
                skin_condition_details=extracted_data['skin_condition_details']
            )

            # Track reasons with detailed descriptions
            if female_hormonal_descriptions:
                for description in female_hormonal_descriptions:
                    add_top_contributors(
                        reasons,
                        female_hormonal_scores,
                        "FemaleHormonalHealth",
                        description,
                        top_n=self.TOP_N_CONTRIBUTORS
                    )

            # Log female hormonal health scores
            log_lines.append(self._create_log_entry("Female Hormonal Health", female_hormonal_scores, female_hormonal_descriptions if female_hormonal_descriptions else ["None"]))
            final_scores = self._combine_scores(final_scores, female_hormonal_scores)

            # Apply Male Hormonal Health Ruleset
            male_hormonal_scores, male_hormonal_descriptions = male_hormonal_health_ruleset.get_male_hormonal_health_weights(
                biological_sex=extracted_data['biological_sex'],
                age=extracted_data['age'],
                hormonal_concerns=extracted_data['male_hormonal_concerns'],
                concern_details=extracted_data['male_concern_details'],
                bmi=extracted_data['bmi'],
                diagnoses=extracted_data['diagnoses_string'],
                snoring_sleep_apnea=extracted_data['snoring_sleep_apnea'],
                current_medications=extracted_data['current_medications'],
                substance_details=extracted_data['substance_details'],
                chemical_exposures=extracted_data['chemical_exposures'],
                surgeries=extracted_data['surgeries']
            )

            # Track reasons with detailed descriptions
            if male_hormonal_descriptions:
                for description in male_hormonal_descriptions:
                    add_top_contributors(
                        reasons,
                        male_hormonal_scores,
                        "MaleHormonalHealth",
                        description,
                        top_n=self.TOP_N_CONTRIBUTORS
                    )

            # Log male hormonal health scores
            log_lines.append(self._create_log_entry("Male Hormonal Health", male_hormonal_scores, male_hormonal_descriptions if male_hormonal_descriptions else ["None"]))
            final_scores = self._combine_scores(final_scores, male_hormonal_scores)

            # Apply Headache Ruleset
            headache_scores, headache_descriptions = headache_ruleset.get_headache_weights(
                frequent_headaches_migraines=extracted_data['frequent_headaches_migraines'],
                headache_details=extracted_data['headache_details'],
                digestive_symptoms=extracted_data['digestive_symptoms'],
                diagnoses=extracted_data['diagnoses_string'],
                sleep_hours_category=extracted_data['sleep_hours_category'],
                trouble_staying_asleep=extracted_data['trouble_staying_asleep'],
                snoring_sleep_apnea=extracted_data['snoring_sleep_apnea'],
                biological_sex=extracted_data['biological_sex'],
                menstrual_concerns=extracted_data['female_menstrual_concerns'],
                alcohol_frequency=extracted_data['alcohol_frequency'],
                substance_details=extracted_data['substance_details'],
                chemical_exposures=extracted_data['chemical_exposures'],
                mold_exposure=extracted_data['mold_exposure']
            )

            # Track reasons with detailed descriptions
            if headache_descriptions:
                for description in headache_descriptions:
                    add_top_contributors(
                        reasons,
                        headache_scores,
                        "Headache",
                        description,
                        top_n=self.TOP_N_CONTRIBUTORS
                    )

            # Log headache scores
            log_lines.append(self._create_log_entry("Headache", headache_scores, headache_descriptions if headache_descriptions else ["None"]))
            final_scores = self._combine_scores(final_scores, headache_scores)

            # Apply Pets/Animals Ruleset
            pets_animals_scores, pets_animals_description = pets_animals_ruleset.get_pets_animals_weights(
                has_pets=extracted_data['has_pets']
            )

            # Track reasons with description
            if pets_animals_description:
                add_top_contributors(
                    reasons,
                    pets_animals_scores,
                    "PetsAnimals",
                    pets_animals_description,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log pets/animals scores
            log_lines.append(self._create_log_entry("Pets/Animals", pets_animals_scores, [pets_animals_description if pets_animals_description else "None"]))
            final_scores = self._combine_scores(final_scores, pets_animals_scores)

            # Apply Mold Exposure Ruleset
            mold_exposure_scores, mold_exposure_descriptions = mold_exposure_ruleset.get_mold_exposure_weights(
                mold_exposure=extracted_data['mold_exposure'],
                diagnoses=extracted_data['diagnoses_string'],
                digestive_symptoms=extracted_data['digestive_symptoms']
            )

            # Track reasons with detailed descriptions
            if mold_exposure_descriptions:
                for description in mold_exposure_descriptions:
                    add_top_contributors(
                        reasons,
                        mold_exposure_scores,
                        "MoldExposure",
                        description,
                        top_n=self.TOP_N_CONTRIBUTORS
                    )

            # Log mold exposure scores
            log_lines.append(self._create_log_entry("Mold Exposure", mold_exposure_scores, mold_exposure_descriptions if mold_exposure_descriptions else ["None"]))
            final_scores = self._combine_scores(final_scores, mold_exposure_scores)

            log_lines.extend([
                "",
                "="*80,
                "FINAL SCORES:",
                "="*80,
                ""
            ])

            sorted_scores = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)
            for code, score in sorted_scores:
                area_name = FOCUS_AREA_NAMES[code]
                log_lines.append(f"{area_name} ({code}): {score:.3f}")

            log_content = "\n".join(log_lines)
            patient_id = extracted_data.get('age', 'unknown')
            log_file_path = self._save_log_file(log_content, str(patient_id))
            print(f"✅ Log file saved to: {log_file_path}")

            # Save reasons dictionary as JSON
            reasons_file_path = self._save_reasons_file(reasons, str(patient_id))
            print(f"✅ Reasons file saved to: {reasons_file_path}")

            markdown_output = self._format_markdown_output(final_scores)
            return markdown_output

        except Exception as e:
            error_msg = f"Error in focus areas evaluation: {str(e)}"
            print(f"❌ {error_msg}")
            raise

