from crewai.tools import BaseTool
from typing import Type, Dict, Union, List, Any
from pydantic import BaseModel, Field
import json
import pandas as pd
import os
import re
from datetime import datetime

from .rulesets_phase3 import (
    HealthGoalsRuleset,
    LifestyleWillingnessRuleset,
    PatientReasoningRuleset,
    LastFeltWellRuleset,
    TriggerEventRuleset,
    SymptomAggravatorsRuleset,
    PartOfDayRuleset,
    WhereSymptomsWorseRuleset
)
from .rulesets_phase3.sunlight_exposure_ruleset import SunlightExposureRuleset
from .rulesets_phase3.sleep_aids_ruleset import SleepAidsRuleset
from .rulesets_phase3.consistent_sleep_schedule_ruleset import ConsistentSleepScheduleRuleset
from .rulesets_phase3.consistent_wake_time_ruleset import ConsistentWakeTimeRuleset
from .rulesets_phase3.typical_meals_ruleset import TypicalMealsRuleset
from .rulesets_phase3.food_avoidance_ruleset import FoodAvoidanceRuleset
from .rulesets_phase3.food_cravings_ruleset import FoodCravingsRuleset
from .rulesets_phase3.mood_ruleset import MoodRuleset
from .rulesets_phase3.current_stress_ruleset import CurrentStressRuleset
from .rulesets_phase3.stress_sources_ruleset import StressSourcesRuleset
from .rulesets_phase3.relaxation_techniques_ruleset import RelaxationTechniquesRuleset
from .rulesets_phase3.support_sources_ruleset import SupportSourcesRuleset
from .rulesets_phase3.trauma_ruleset import TraumaRuleset
from .rulesets_phase3.childhood_illnesses_ruleset import ChildhoodIllnessesRuleset
from .rulesets_phase3.childhood_home_security_ruleset import ChildhoodHomeSecurityRuleset
from .rulesets_phase3.breastfeeding_ruleset import BreastfeedingRuleset
from .rulesets_phase3.early_environmental_exposures_ruleset import EarlyEnvironmentalExposuresRuleset
from .rulesets_phase3.tooth_sensitivity_ruleset import ToothSensitivityRuleset
from .rulesets_phase3.current_environmental_exposures_ruleset import CurrentEnvironmentalExposuresRuleset
from .rulesets_phase3.chemical_sensitivity_ruleset import ChemicalSensitivityRuleset
from .rulesets_phase3.caffeine_reaction_ruleset import CaffeineReactionRuleset
from .rulesets_phase3.alcohol_flushing_ruleset import AlcoholFlushingRuleset
from .rulesets_phase3.synthetic_fiber_wear_ruleset import SyntheticFiberWearRuleset
from .rulesets_phase3.seasonal_allergies_ruleset import SeasonalAllergiesRuleset
from .rulesets_phase3.air_filter_ruleset import AirFilterRuleset
from .rulesets.constants import FOCUS_AREAS, FOCUS_AREA_NAMES, add_top_contributors
from .rulesets_phase3.constants import PHASE3_FIELD_CONTEXT
from .rulesets.data_extractor import extract_phase1_phase2_data

class EvaluateFocusAreasPhase3Input(BaseModel):
    patient_and_blood_data: Union[str, dict] = Field(
        ..., description="JSON string OR dict with keys: patient_form, blood_report"
    )


class EvaluateFocusAreasPhase3Tool(BaseTool):
    name: str = "evaluate_user_focus_areas_phase3"
    description: str = (
        "Evaluates user's phase3 detailed intake data and returns focus area scores "
        "using rule-based scoring on textual responses."
    )
    args_schema: Type[BaseModel] = EvaluateFocusAreasPhase3Input

    # Configuration: Number of top contributors to track per ruleset
    TOP_N_CONTRIBUTORS: int = 1

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def _initialize_scores(self) -> Dict[str, float]:
        """Initialize all focus area scores to 0.0."""
        return {code: 0.0 for code in FOCUS_AREAS}

    def _initialize_reasons(self) -> Dict[str, List[str]]:
        """Initialize reasons tracking dictionary."""
        return {code: [] for code in FOCUS_AREAS}

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
        lines = [f"\n--- {ruleset_name.upper()} ---"]
        if input_data is not None:
            # Truncate long input data for readability
            input_str = str(input_data)
            if len(input_str) > 200:
                input_str = input_str[:200] + "..."
            lines.append(f"Input: {input_str}")
        lines.append("Scores:")
        for code, score in scores.items():
            if score != 0.0:
                sign = "+" if score >= 0 else ""
                lines.append(f"  {code}: {sign}{score:.3f}")
        if all(score == 0.0 for score in scores.values()):
            lines.append("  (No contribution)")
        return "\n".join(lines)

    def _save_log_file(self, log_content: str, patient_id: str = "unknown", suffix: str = "phase3") -> str:
        """Save log content to a file."""
        output_dir = f"outputs/{patient_id}"
        os.makedirs(output_dir, exist_ok=True)

        log_file_path = f"{output_dir}/focus_areas_weight_breakdown_{suffix}.log"
        with open(log_file_path, 'w') as f:
            f.write(log_content)

        return log_file_path

    def _save_reasons_file(self, reasons: Dict[str, List[str]], patient_id: str = "unknown", suffix: str = "phase3") -> str:
        """Save reasons to a JSON file."""
        output_dir = f"outputs/{patient_id}"
        os.makedirs(output_dir, exist_ok=True)

        reasons_file_path = f"{output_dir}/focus_areas_reasons_{suffix}.json"
        with open(reasons_file_path, 'w') as f:
            json.dump(reasons, f, indent=2)

        return reasons_file_path

    def _extract_phase3_to_dataframe(self, phase3_dict: Dict[str, Any]) -> pd.DataFrame:
        """Convert phase3_detailed_intake dict to DataFrame for position-based access."""
        if not phase3_dict:
            return pd.DataFrame(columns=['question', 'answer', 'position'])
        
        items = list(phase3_dict.items())
        df = pd.DataFrame(items, columns=['question', 'answer'])
        df['position'] = df.index
        return df

    def _get_field_by_position(self, df: pd.DataFrame, position: int, default: str = "") -> str:
        """Extract field value by position index."""
        if position < len(df):
            return str(df.iloc[position]['answer']).strip()
        return default
    
    def _get_field_by_position_raw(self, df: pd.DataFrame, position: int, default: Any = None) -> Any:
        """Extract field value by position index, preserving original type (for nested structures)."""
        if position < len(df):
            return df.iloc[position]['answer']
        return default

    def _combine_scores(self, *rulesets) -> Dict[str, float]:
        """Combine multiple ruleset scores."""
        combined = {code: 0.0 for code in FOCUS_AREAS}
        for rules in rulesets:
            for code, score in rules.items():
                combined[code] += score
        return combined

    def _run(self, patient_and_blood_data: Union[str, dict]) -> str:
        try:
            if isinstance(patient_and_blood_data, str):
                data = json.loads(patient_and_blood_data)
            else:
                data = patient_and_blood_data

            if "patient_and_blood_data" in data:
                data = data["patient_and_blood_data"]

            patient_form = data.get("patient_form", {})
            phase3_data = patient_form.get("patient_data", {}).get("phase3_detailed_intake", {})

            if not phase3_data:
                return "Focus Areas Ranking:\n(No phase3 data available)"

            # Extract Phase 1/2 context using shared extractor (no duplication!)
            phase1_phase2_context = extract_phase1_phase2_data(data)

            # Extract commonly used fields
            age = phase1_phase2_context.get("age")
            sex = phase1_phase2_context.get("biological_sex")
            patient_id = str(age) if age else "unknown"
            occupation_data = {"job_title": phase1_phase2_context.get("job_title"),
                             "work_stress_level": phase1_phase2_context.get("work_stress_level")}
            environmental_exposures = {"mold_exposure": phase1_phase2_context.get("mold_exposure"),
                                      "chemical_exposures": phase1_phase2_context.get("chemical_exposures")}

            # Convert to DataFrame for position-based access
            phase3_df = self._extract_phase3_to_dataframe(phase3_data)

            # Extract all 13 fields by position
            field_0 = self._get_field_by_position(phase3_df, 0)  # Top health goals
            field_1 = self._get_field_by_position(phase3_df, 1)  # Patient reasoning
            field_2 = self._get_field_by_position(phase3_df, 2)  # Lifestyle willingness
            field_3 = self._get_field_by_position(phase3_df, 3)  # Last felt well
            field_4 = self._get_field_by_position(phase3_df, 4)  # What started/worsened
            field_5 = self._get_field_by_position(phase3_df, 5)  # What makes worse
            field_6_raw = self._get_field_by_position_raw(phase3_df, 6)  # Time of day worse (nested structure)
            field_7_raw = self._get_field_by_position_raw(phase3_df, 7)  # Where gets worse (nested structure)
            field_8 = self._get_field_by_position(phase3_df, 8)  # Food/drink triggers
            field_9 = self._get_field_by_position(phase3_df, 9)  # What helps
            field_10 = self._get_field_by_position(phase3_df, 10)  # Antibiotics/meds history
            field_11 = self._get_field_by_position(phase3_df, 11)  # Activity intensity
            field_12 = self._get_field_by_position(phase3_df, 12)  # Sunlight exposure ranking
            field_13 = self._get_field_by_position(phase3_df, 13)  # Sleep aids
            field_14 = self._get_field_by_position(phase3_df, 14)  # Consistent sleep schedule
            field_15 = self._get_field_by_position(phase3_df, 15)  # Consistent wake time
            field_16 = self._get_field_by_position(phase3_df, 16)  # Typical meals and snacks
            field_17 = self._get_field_by_position(phase3_df, 17)  # Foods avoided due to symptoms
            field_18 = self._get_field_by_position(phase3_df, 18)  # Food cravings
            field_19 = self._get_field_by_position(phase3_df, 19)  # Mood description
            field_20 = self._get_field_by_position(phase3_df, 20)  # Current stress level (1-10)
            field_21 = self._get_field_by_position(phase3_df, 21)  # Biggest sources of stress (free text)
            field_22 = self._get_field_by_position(phase3_df, 22)  # Relaxation techniques (multi-select)
            field_23 = self._get_field_by_position(phase3_df, 23)  # Support sources (multi-select)
            field_24 = self._get_field_by_position(phase3_df, 24)  # Trauma/abuse history (radio + free text)
            field_25 = self._get_field_by_position(phase3_df, 25)  # Childhood illnesses (radio + free text)
            field_26 = self._get_field_by_position(phase3_df, 26)  # Childhood home security (radio + free text)
            field_27 = self._get_field_by_position(phase3_df, 27)  # Breastfeeding history (radio + free text)
            field_28 = self._get_field_by_position(phase3_df, 28)  # Early environmental/toxic exposures (radio + free text)
            field_29 = self._get_field_by_position(phase3_df, 29)  # Tooth sensitivity (radio + free text)
            field_30 = self._get_field_by_position(phase3_df, 30)  # Current environmental exposures (multi-select + free text)
            field_31 = self._get_field_by_position(phase3_df, 31)  # Chemical sensitivity (radio + optional free text)
            field_32 = self._get_field_by_position(phase3_df, 32)  # Caffeine reaction (radio)
            field_33 = self._get_field_by_position(phase3_df, 33)  # Alcohol flushing (radio + optional free text)
            field_34 = self._get_field_by_position(phase3_df, 34)  # Synthetic fiber wear (multi-select + optional free text)
            field_35 = self._get_field_by_position(phase3_df, 35)  # Seasonal allergies (radio + optional free text)
            field_37 = self._get_field_by_position(phase3_df, 37)  # Air filter usage (radio + optional brand/model)

            # TEMPORARY: Print extracted fields for verification
            print("\n🔍 Phase3 Data Extraction Debug:")
            print(f"  Total fields extracted: {len(phase3_df)}")
            print(f"  Field 0 (Top health goals): '{field_0[:100] if field_0 else 'EMPTY'}...'")
            print(f"  Field 1 (Patient reasoning): '{field_1[:100] if field_1 else 'EMPTY'}...'")
            print(f"  Field 2 (Lifestyle willingness): '{field_2[:100] if field_2 else 'EMPTY'}...'")
            print(f"  Field 3 (Last felt well): '{field_3[:100] if field_3 else 'EMPTY'}...'")
            print(f"  Field 4 (What started/worsened): '{field_4[:100] if field_4 else 'EMPTY'}...'")
            print(f"  Field 5 (What makes worse): '{field_5[:100] if field_5 else 'EMPTY'}...'")
            # Handle nested structure for field 6
            if isinstance(field_6_raw, dict):
                field_6_display = f"radio: {field_6_raw.get('radio', '')}, text: {field_6_raw.get('text', '')}"
            else:
                field_6_display = str(field_6_raw)[:100] if field_6_raw else 'EMPTY'
            print(f"  Field 6 (Time of day worse): '{field_6_display}...'")
            # Handle nested structure for field 7
            if isinstance(field_7_raw, dict):
                field_7_display = f"radio: {field_7_raw.get('radio', '')}, text: {field_7_raw.get('text', '')}"
            else:
                field_7_display = str(field_7_raw)[:100] if field_7_raw else 'EMPTY'
            print(f"  Field 7 (Where gets worse): '{field_7_display}...'")
            print(f"  Field 8 (Food/drink triggers): '{field_8[:100] if field_8 else 'EMPTY'}...'")
            print(f"  Field 9 (What helps): '{field_9[:100] if field_9 else 'EMPTY'}...'")
            print(f"  Field 10 (Antibiotics/meds history): '{field_10[:100] if field_10 else 'EMPTY'}...'")
            print(f"  Field 11 (Activity intensity): '{field_11[:100] if field_11 else 'EMPTY'}...'")
            print(f"  Field 12 (Sunlight exposure ranking): '{field_12[:100] if field_12 else 'EMPTY'}...'")
            print(f"  Field 13 (Sleep aids): '{field_13[:100] if field_13 else 'EMPTY'}...'")
            print(f"  Field 14 (Consistent sleep schedule): '{field_14[:100] if field_14 else 'EMPTY'}...'")
            print(f"  Field 15 (Consistent wake time): '{field_15[:100] if field_15 else 'EMPTY'}...'")
            print(f"  Field 16 (Typical meals): '{field_16[:100] if field_16 else 'EMPTY'}...'")
            print(f"  Field 17 (Food avoidance): '{field_17[:100] if field_17 else 'EMPTY'}...'")
            print(f"  Field 18 (Food cravings): '{field_18[:100] if field_18 else 'EMPTY'}...'")
            print(f"  Field 19 (Mood): '{field_19[:100] if field_19 else 'EMPTY'}...'")
            print(f"  Field 20 (Current stress): '{field_20[:100] if field_20 else 'EMPTY'}...'")
            print(f"  Field 21 (Stress sources): '{field_21[:100] if field_21 else 'EMPTY'}...'")
            print(f"  Field 22 (Relaxation techniques): '{field_22[:100] if field_22 else 'EMPTY'}...'")
            print(f"  Field 23 (Support sources): '{field_23[:100] if field_23 else 'EMPTY'}...'")
            print(f"  Field 24 (Trauma/abuse): '{field_24[:100] if field_24 else 'EMPTY'}...'")
            print(f"  Field 25 (Childhood illnesses): '{field_25[:100] if field_25 else 'EMPTY'}...'")
            print(f"  Field 26 (Childhood home security): '{field_26[:100] if field_26 else 'EMPTY'}...'")
            print(f"  Field 27 (Breastfeeding): '{field_27[:100] if field_27 else 'EMPTY'}...'")
            print(f"  Field 28 (Early environmental exposures): '{field_28[:100] if field_28 else 'EMPTY'}...'")
            print(f"  Field 29 (Tooth sensitivity): '{field_29[:100] if field_29 else 'EMPTY'}...'")
            print(f"  Field 30 (Current environmental exposures): '{field_30[:100] if field_30 else 'EMPTY'}...'")
            print(f"  Field 31 (Chemical sensitivity): '{field_31[:100] if field_31 else 'EMPTY'}...'")
            print(f"  Field 32 (Caffeine reaction): '{field_32[:100] if field_32 else 'EMPTY'}...'")
            print(f"  Field 33 (Alcohol flushing): '{field_33[:100] if field_33 else 'EMPTY'}...'")
            print(f"  Field 34 (Synthetic fiber wear): '{field_34[:100] if field_34 else 'EMPTY'}...'")
            print(f"  Field 35 (Seasonal allergies): '{field_35[:100] if field_35 else 'EMPTY'}...'")
            print(f"  Field 37 (Air filter): '{field_37[:100] if field_37 else 'EMPTY'}...'")
            print("")

            # Initialize scores, reasons, and log
            all_scores = self._initialize_scores()
            all_reasons = self._initialize_reasons()
            log_entries = []

            # Safety flags tracking
            safety_flags = {"crisis": False, "urgent_care": False, "red_flag": False}

            # Adherence Multiplier (will be set by Field 2)
            adherence_multiplier = None

            # Initialize rulesets
            health_goals_ruleset = HealthGoalsRuleset()
            lifestyle_willingness_ruleset = LifestyleWillingnessRuleset()
            patient_reasoning_ruleset = PatientReasoningRuleset()
            last_felt_well_ruleset = LastFeltWellRuleset()
            trigger_event_ruleset = TriggerEventRuleset()
            symptom_aggravators_ruleset = SymptomAggravatorsRuleset()
            part_of_day_ruleset = PartOfDayRuleset()
            where_symptoms_worse_ruleset = WhereSymptomsWorseRuleset()
            sunlight_exposure_ruleset = SunlightExposureRuleset()
            sleep_aids_ruleset = SleepAidsRuleset()
            consistent_sleep_schedule_ruleset = ConsistentSleepScheduleRuleset()
            consistent_wake_time_ruleset = ConsistentWakeTimeRuleset()
            typical_meals_ruleset = TypicalMealsRuleset()
            food_avoidance_ruleset = FoodAvoidanceRuleset()
            food_cravings_ruleset = FoodCravingsRuleset()
            mood_ruleset = MoodRuleset()
            current_stress_ruleset = CurrentStressRuleset()
            stress_sources_ruleset = StressSourcesRuleset()
            relaxation_techniques_ruleset = RelaxationTechniquesRuleset()
            support_sources_ruleset = SupportSourcesRuleset()
            trauma_ruleset = TraumaRuleset()
            childhood_illnesses_ruleset = ChildhoodIllnessesRuleset()
            childhood_home_security_ruleset = ChildhoodHomeSecurityRuleset()
            breastfeeding_ruleset = BreastfeedingRuleset()
            early_environmental_exposures_ruleset = EarlyEnvironmentalExposuresRuleset()
            tooth_sensitivity_ruleset = ToothSensitivityRuleset()
            current_environmental_exposures_ruleset = CurrentEnvironmentalExposuresRuleset()
            chemical_sensitivity_ruleset = ChemicalSensitivityRuleset()
            caffeine_reaction_ruleset = CaffeineReactionRuleset()
            alcohol_flushing_ruleset = AlcoholFlushingRuleset()
            synthetic_fiber_wear_ruleset = SyntheticFiberWearRuleset()
            seasonal_allergies_ruleset = SeasonalAllergiesRuleset()
            air_filter_ruleset = AirFilterRuleset()

            log_entries.append("="*80)
            log_entries.append(f"PHASE 3 FOCUS AREA EVALUATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            log_entries.append("="*80)
            log_entries.append(f"\nPATIENT DATA SUMMARY:")
            log_entries.append(f"  Age: {age}")
            log_entries.append(f"\nRULESET CONTRIBUTIONS:\n")

            # Field 0: Top health goals
            field_0_scores, field_0_flags, goal_details = health_goals_ruleset.get_health_goals_weights(
                field_0, age=age
            )

            # Track reasons - INDIVIDUAL GOAL LEVEL (most important field!)
            field_context = PHASE3_FIELD_CONTEXT[0]

            # Track each goal separately with its rank and contribution
            for goal_detail in goal_details:
                rank = goal_detail["rank"]
                goal_text = goal_detail["goal_text"]
                goal_scores = goal_detail["scores"]

                # Format: "TopHealthGoals[Rank1]:lose weight"
                goal_context = f"{field_context}[Rank{rank}]"

                add_top_contributors(
                    all_reasons,
                    goal_scores,
                    goal_context,
                    goal_text,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log
            log_entries.append(self._create_log_entry(f"Field 0 - {field_context}", field_0_scores, field_0[:100] if field_0 else None))

            all_scores = self._combine_scores(all_scores, field_0_scores)

            # Update safety flags
            if field_0_flags.get("crisis"):
                safety_flags["crisis"] = True
            if field_0_flags.get("urgent_care"):
                safety_flags["urgent_care"] = True

            # Field 1: Patient reasoning
            field_1_scores, field_1_flags, causal_group_details = patient_reasoning_ruleset.get_patient_reasoning_weights(
                field_1, age=age
            )

            # Track reasons - INDIVIDUAL CAUSAL GROUP LEVEL (important for clinical context!)
            field_context = PHASE3_FIELD_CONTEXT[1]

            # Track each causal group separately with its matched text
            for group_detail in causal_group_details:
                group_name = group_detail["group_name"]
                matched_text = group_detail["matched_text"]
                group_scores = group_detail["scores"]

                # Format: "PatientReasoning[poor_diet]:junk food"
                group_context = f"{field_context}[{group_name}]"

                add_top_contributors(
                    all_reasons,
                    group_scores,
                    group_context,
                    matched_text,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log
            log_entries.append(self._create_log_entry(f"Field 1 - {field_context}", field_1_scores, field_1[:100] if field_1 else None))

            all_scores = self._combine_scores(all_scores, field_1_scores)

            # Update safety flags
            if field_1_flags.get("red_flag"):
                safety_flags["red_flag"] = True

            # Field 2: Lifestyle willingness (returns AM - Adherence Multiplier)
            adherence_multiplier = lifestyle_willingness_ruleset.get_lifestyle_willingness_am(
                field_2, age=age, top_goals_text=field_0, occupation_data=occupation_data
            )

            # Log AM (not a score, so special handling)
            field_context = PHASE3_FIELD_CONTEXT[2]
            log_entries.append(f"\n--- FIELD 2 - {field_context.upper()} ---")
            log_entries.append(f"Input: {field_2[:100] if field_2 else 'none'}")
            log_entries.append(f"Adherence Multiplier (AM): {adherence_multiplier:.4f}")
            log_entries.append("(AM is stored separately, not added to focus area scores)")

            # Field 3: Last felt well (chronicity + triggers)
            field_3_scores, field_3_flags, last_felt_well_details = last_felt_well_ruleset.get_last_felt_well_weights(
                field_3, age=age
            )

            # Track reasons - INDIVIDUAL DETAIL LEVEL (chronicity + triggers)
            field_context = PHASE3_FIELD_CONTEXT[3]

            # Track each detail separately (chronicity and triggers)
            for detail in last_felt_well_details:
                detail_type = detail["type"]
                detail_scores = detail["scores"]

                if detail_type == "chronicity":
                    # Format: "LastFeltWell[chronicity:sub_chronic]"
                    detail_context = f"{field_context}[chronicity:{detail['label']}]"
                    detail_text = f"{detail['months']} months ago"
                elif detail_type == "trigger":
                    # Format: "LastFeltWell[trigger:gi_infection]"
                    detail_context = f"{field_context}[trigger:{detail['trigger_name']}]"
                    detail_text = detail["matched_text"]
                else:
                    continue

                add_top_contributors(
                    all_reasons,
                    detail_scores,
                    detail_context,
                    detail_text,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log
            log_entries.append(self._create_log_entry(f"Field 3 - {field_context}", field_3_scores, field_3[:100] if field_3 else None))

            all_scores = self._combine_scores(all_scores, field_3_scores)

            # Field 4: Trigger Event (what started or worsened wellness)
            field_4_scores, field_4_flags, trigger_event_details = trigger_event_ruleset.get_trigger_event_weights(
                field_4, age=age, sex=sex
            )

            # Track reasons - INDIVIDUAL DETAIL LEVEL (triggers + synergies + allostatic load)
            field_context = PHASE3_FIELD_CONTEXT[4]

            # Track each detail separately (triggers, synergies, allostatic load)
            for detail in trigger_event_details:
                detail_type = detail["type"]
                detail_scores = detail["scores"]

                if detail_type == "trigger":
                    # Format: "WhatStartedWorsened[trigger:post_viral]"
                    detail_context = f"{field_context}[trigger:{detail['trigger_name']}]"
                    detail_text = detail["matched_text"]
                elif detail_type == "synergy":
                    # Format: "WhatStartedWorsened[synergy:gastroenteritis_antibiotics]"
                    detail_context = f"{field_context}[synergy:{detail['synergy_name']}]"
                    detail_text = detail["description"]
                elif detail_type == "allostatic_load":
                    # Format: "WhatStartedWorsened[allostatic_load]"
                    detail_context = f"{field_context}[allostatic_load]"
                    detail_text = detail["description"]
                else:
                    continue

                add_top_contributors(
                    all_reasons,
                    detail_scores,
                    detail_context,
                    detail_text,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log
            log_entries.append(self._create_log_entry(f"Field 4 - {field_context}", field_4_scores, field_4[:100] if field_4 else None))

            all_scores = self._combine_scores(all_scores, field_4_scores)

            # Field 5: Symptom Aggravators (what makes symptoms worse)
            field_5_scores, field_5_flags, symptom_aggravators_details = symptom_aggravators_ruleset.get_symptom_aggravators_weights(
                field_5, age=age
            )

            # Track reasons - INDIVIDUAL DETAIL LEVEL (triggers + synergies)
            field_context = PHASE3_FIELD_CONTEXT[5]

            # Track each detail separately (triggers and synergies)
            for detail in symptom_aggravators_details:
                detail_type = detail["type"]
                detail_scores = detail["scores"]

                if detail_type == "trigger":
                    # Format: "WhatMakesWorse[trigger:dairy]"
                    detail_context = f"{field_context}[trigger:{detail['trigger_name']}]"
                    detail_text = detail["matched_text"]
                elif detail_type == "synergy":
                    # Format: "WhatMakesWorse[synergy:multiple_gi_triggers]"
                    detail_context = f"{field_context}[synergy:{detail['synergy_name']}]"
                    detail_text = detail["description"]
                else:
                    continue

                add_top_contributors(
                    all_reasons,
                    detail_scores,
                    detail_context,
                    detail_text,
                    top_n=self.TOP_N_CONTRIBUTORS
                )

            # Log
            log_entries.append(self._create_log_entry(f"Field 5 - {field_context}", field_5_scores, field_5[:100] if field_5 else None))

            all_scores = self._combine_scores(all_scores, field_5_scores)

            # Update safety flags
            if field_5_flags.get("red_flag"):
                safety_flags["red_flag"] = True

            # Field 6: Part of Day (time of day when symptoms worsen)
            # Combine free text from other fields for context
            # Extract text from field_7_raw if it's nested
            field_7_text = ""
            if isinstance(field_7_raw, dict):
                field_7_text = str(field_7_raw.get("text", "")).strip()
            elif isinstance(field_7_raw, str):
                field_7_text = field_7_raw.strip()
            free_text_context = f"{field_4} {field_5} {field_7_text}".strip()

            field_6_scores = part_of_day_ruleset.get_part_of_day_weights(
                field_6_raw, age=age, occupation_data=occupation_data, free_text_strings=free_text_context
            )

            # Track reasons
            field_context = PHASE3_FIELD_CONTEXT[6]
            field_6_display = str(field_6_raw)[:50] if field_6_raw else "none"
            add_top_contributors(
                all_reasons,
                field_6_scores,
                field_context,
                field_6_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 6 - {field_context}", field_6_scores, str(field_6_raw)[:100] if field_6_raw else None))

            all_scores = self._combine_scores(all_scores, field_6_scores)

            # Field 7: Where symptoms get worse
            field_7_scores = where_symptoms_worse_ruleset.get_where_symptoms_worse_weights(
                field_7_raw, age=age, environmental_exposures=environmental_exposures
            )

            # Track reasons
            field_context = PHASE3_FIELD_CONTEXT[7]
            field_7_display = str(field_7_raw)[:50] if field_7_raw else "none"
            add_top_contributors(
                all_reasons,
                field_7_scores,
                field_context,
                field_7_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 7 - {field_context}", field_7_scores, str(field_7_raw)[:100] if field_7_raw else None))

            all_scores = self._combine_scores(all_scores, field_7_scores)

            # Field 12: Sunlight exposure ranking
            field_12_scores = sunlight_exposure_ruleset.get_sunlight_exposure_weights(
                field_12, age=age
            )

            # Track reasons
            field_context = PHASE3_FIELD_CONTEXT[12]
            field_12_display = str(field_12)[:50] if field_12 else "none"
            add_top_contributors(
                all_reasons,
                field_12_scores,
                field_context,
                field_12_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 12 - {field_context}", field_12_scores, str(field_12)[:100] if field_12 else None))

            all_scores = self._combine_scores(all_scores, field_12_scores)

            # Field 13: Sleep aids
            # Check if patient has reflux (from other fields for cross-field synergy)
            reflux_flag = False
            if field_5:
                reflux_keywords = ["reflux", "heartburn", "gerd", "acid"]
                reflux_flag = any(kw in str(field_5).lower() for kw in reflux_keywords)

            field_13_scores = sleep_aids_ruleset.get_sleep_aids_weights(
                field_13, age=age, reflux_flag=reflux_flag
            )

            # Track reasons
            field_context = PHASE3_FIELD_CONTEXT[13]
            field_13_display = str(field_13)[:50] if field_13 else "none"
            add_top_contributors(
                all_reasons,
                field_13_scores,
                field_context,
                field_13_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 13 - {field_context}", field_13_scores, str(field_13)[:100] if field_13 else None))

            all_scores = self._combine_scores(all_scores, field_13_scores)

            # Field 14: Consistent sleep schedule
            # Extract cross-field data for synergies
            from .rulesets_phase3.constants import detect_shift_work

            shift_work_flag = detect_shift_work(
                phase1_phase2_context.get("job_title", "")
            )

            alcohol_frequency = phase1_phase2_context.get("alcohol_frequency", "")

            # Metabolic flags: check for high stress-glycemia or low activity
            # For now, use simple heuristics (can be refined later)
            metabolic_flags = False
            work_stress = phase1_phase2_context.get("work_stress_level", "")
            exercise_days = phase1_phase2_context.get("exercise_days_per_week")
            if work_stress and "high" in str(work_stress).lower():
                metabolic_flags = True
            if exercise_days is not None and exercise_days < 2:
                metabolic_flags = True

            field_14_scores = consistent_sleep_schedule_ruleset.get_consistent_sleep_schedule_weights(
                field_14,
                age=age,
                shift_work_flag=shift_work_flag,
                alcohol_frequency=alcohol_frequency,
                metabolic_flags=metabolic_flags
            )

            # Track reasons - simple format: "ConsistentSleepSchedule: Yes/No"
            field_context = PHASE3_FIELD_CONTEXT[14]
            field_14_display = str(field_14).strip() if field_14 else "none"
            add_top_contributors(
                all_reasons,
                field_14_scores,
                field_context,
                field_14_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 14 - {field_context}", field_14_scores, str(field_14)[:100] if field_14 else None))

            all_scores = self._combine_scores(all_scores, field_14_scores)

            # Field 15: Consistent wake time
            # Reuse cross-field data from Field 14
            # shift_work_flag, alcohol_frequency already extracted above

            # Social jetlag flag: detect from sunlight exposure or other schedule fields
            # For now, set to False (can be enhanced later with actual detection)
            social_jetlag_flag = False

            # Short sleep flag: check if sleep hours < 6
            short_sleep_flag = False
            sleep_hours_category = phase1_phase2_context.get("sleep_hours_category", "")
            if sleep_hours_category and "less_than_6" in str(sleep_hours_category).lower():
                short_sleep_flag = True

            field_15_scores = consistent_wake_time_ruleset.get_consistent_wake_time_weights(
                field_15,
                age=age,
                shift_work_flag=shift_work_flag,
                alcohol_frequency=alcohol_frequency,
                social_jetlag_flag=social_jetlag_flag,
                short_sleep_flag=short_sleep_flag
            )

            # Track reasons - simple format: "ConsistentWakeTime: Yes/No"
            field_context = PHASE3_FIELD_CONTEXT[15]
            field_15_display = str(field_15).strip() if field_15 else "none"
            add_top_contributors(
                all_reasons,
                field_15_scores,
                field_context,
                field_15_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 15 - {field_context}", field_15_scores, str(field_15)[:100] if field_15 else None))

            all_scores = self._combine_scores(all_scores, field_15_scores)

            # Field 16: Typical meals and snacks (LLM-based dietary pattern analysis)
            # Extract digestive symptoms from Phase 2 for caffeine + reflux synergy
            digestive_symptoms = phase1_phase2_context.get("digestive_symptoms", "")

            # Extract current supplements from Phase 1 for omega-3 double-counting check
            # current_supplements is already a list from data_extractor
            current_supplements = phase1_phase2_context.get("current_supplements", [])
            if not isinstance(current_supplements, list):
                # If it's not a list (e.g., string or None), convert to list
                if current_supplements:
                    current_supplements = [s.strip() for s in str(current_supplements).split(',') if s.strip()]
                else:
                    current_supplements = []

            field_16_scores = typical_meals_ruleset.get_typical_meals_weights(
                field_16,
                age=age,
                digestive_symptoms=digestive_symptoms,
                current_supplements=current_supplements
            )

            # Track reasons - simple format: detected categories
            field_context = PHASE3_FIELD_CONTEXT[16]
            field_16_display = str(field_16)[:50] if field_16 else "none"
            add_top_contributors(
                all_reasons,
                field_16_scores,
                field_context,
                field_16_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 16 - {field_context}", field_16_scores, str(field_16)[:100] if field_16 else None))

            all_scores = self._combine_scores(all_scores, field_16_scores)

            # Field 17: Food avoidance (foods avoided due to symptoms)
            field_17_scores, field_17_flags = food_avoidance_ruleset.get_food_avoidance_weights(
                field_17,
                age=age
            )

            # Track reasons - simple format: detected food categories
            field_context = PHASE3_FIELD_CONTEXT[17]
            field_17_display = str(field_17)[:50] if field_17 else "none"
            add_top_contributors(
                all_reasons,
                field_17_scores,
                field_context,
                field_17_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 17 - {field_context}", field_17_scores, str(field_17)[:100] if field_17 else None))

            all_scores = self._combine_scores(all_scores, field_17_scores)

            # Update safety flags
            if any("SAFETY" in flag for flag in field_17_flags):
                safety_flags["red_flag"] = True

            # Field 18: Food cravings (multi-select with substring matching)
            # Extract cross-field data for special rules

            # Sleep hours: convert category to numeric estimate
            sleep_hours = None
            sleep_hours_category = phase1_phase2_context.get("sleep_hours_category", "")
            if sleep_hours_category:
                if "less_than_6" in str(sleep_hours_category).lower() or "<6" in str(sleep_hours_category):
                    sleep_hours = 5.5
                elif "6-7" in str(sleep_hours_category) or "6_7" in str(sleep_hours_category):
                    sleep_hours = 6.5
                elif "7-8" in str(sleep_hours_category) or "7_8" in str(sleep_hours_category):
                    sleep_hours = 7.5
                elif "8+" in str(sleep_hours_category) or ">8" in str(sleep_hours_category):
                    sleep_hours = 8.5

            # Sleep irregular: from Field 14 (if "No" to consistent sleep schedule)
            sleep_irregular = False
            if field_14 and field_14.lower().strip() in ["no", "n"]:
                sleep_irregular = True

            # Menstrual pattern: from Phase 2 systems review
            menstrual_pattern = phase1_phase2_context.get("menstrual_pattern", "")

            # Other symptoms: from Phase 2 systems review (digestive symptoms already extracted)
            other_symptoms = digestive_symptoms  # Reuse digestive symptoms for post-meal crash detection

            field_18_scores, field_18_flags = food_cravings_ruleset.get_food_cravings_weights(
                field_18,
                sleep_hours=sleep_hours,
                sleep_irregular=sleep_irregular,
                sex=sex,
                menstrual_pattern=menstrual_pattern,
                other_symptoms=other_symptoms
            )

            # Track reasons - simple format: detected cravings
            field_context = PHASE3_FIELD_CONTEXT[18]
            field_18_display = str(field_18)[:50] if field_18 else "none"
            add_top_contributors(
                all_reasons,
                field_18_scores,
                field_context,
                field_18_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 18 - {field_context}", field_18_scores, str(field_18)[:100] if field_18 else None))

            all_scores = self._combine_scores(all_scores, field_18_scores)

            # Field 19: Mood description (NLP-based lexicon matching)
            # Cross-field data already extracted: digestive_symptoms, sleep_hours, sleep_irregular

            # Shift work: from Phase 1/2 job title
            shift_work = False
            job_title = phase1_phase2_context.get("job_title", "")
            if job_title:
                from .rulesets_phase3.constants import detect_shift_work
                shift_work = detect_shift_work(job_title)

            field_19_scores, field_19_flags = mood_ruleset.get_mood_weights(
                field_19,
                digestive_symptoms=digestive_symptoms,
                sleep_hours=sleep_hours,
                sleep_irregular=sleep_irregular,
                shift_work=shift_work
            )

            # Track reasons - simple format: mood description
            field_context = PHASE3_FIELD_CONTEXT[19]
            field_19_display = str(field_19)[:50] if field_19 else "none"
            add_top_contributors(
                all_reasons,
                field_19_scores,
                field_context,
                field_19_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 19 - {field_context}", field_19_scores, str(field_19)[:100] if field_19 else None))

            all_scores = self._combine_scores(all_scores, field_19_scores)

            # Update safety flags
            if any("SAFETY" in flag for flag in field_19_flags):
                safety_flags["red_flag"] = True
                # Log safety concern
                log_entries.append(f"\n⚠️  SAFETY FLAG: {field_19_flags[0]}")

            # Field 20: Current stress level (1-10 scale, linear + piecewise)
            # Cross-field data already extracted: sleep_hours, sleep_irregular, shift_work

            # Work stress level: from Phase 2 systems review
            work_stress_level = None
            work_stress_raw = phase1_phase2_context.get("work_stress_level", "")
            if work_stress_raw:
                try:
                    work_stress_level = int(float(str(work_stress_raw).strip()))
                except (ValueError, TypeError):
                    pass

            field_20_scores, field_20_flags = current_stress_ruleset.get_current_stress_weights(
                field_20,
                age=age,
                sleep_hours=sleep_hours,
                sleep_irregular=sleep_irregular,
                shift_work=shift_work,
                work_stress_level=work_stress_level
            )

            # Track reasons - simple format: stress score
            field_context = PHASE3_FIELD_CONTEXT[20]
            field_20_display = str(field_20) if field_20 else "none"
            add_top_contributors(
                all_reasons,
                field_20_scores,
                field_context,
                field_20_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 20 - {field_context}", field_20_scores, str(field_20) if field_20 else None))

            all_scores = self._combine_scores(all_scores, field_20_scores)

            # Log validation warnings/flags
            if field_20_flags:
                for flag in field_20_flags:
                    log_entries.append(f"  ⚠️  {flag}")

            # Field 21: Biggest sources of stress (NLP-based stressor categorization)
            # Cross-field data: gi_symptoms_present, shift_work, sleep_irregular, age

            # GI symptoms: from Phase 2 systems review (digestive symptoms already extracted)
            gi_symptoms_present = bool(digestive_symptoms and digestive_symptoms.strip())

            field_21_scores, field_21_flags = stress_sources_ruleset.get_stress_sources_weights(
                field_21,
                age=age,
                gi_symptoms_present=gi_symptoms_present,
                shift_work=shift_work,
                sleep_irregular=sleep_irregular
            )

            # Track reasons - simple format: detected stressors
            field_context = PHASE3_FIELD_CONTEXT[21]
            field_21_display = str(field_21)[:100] if field_21 else "none"
            add_top_contributors(
                all_reasons,
                field_21_scores,
                field_context,
                field_21_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 21 - {field_context}", field_21_scores, str(field_21)[:100] if field_21 else None))

            all_scores = self._combine_scores(all_scores, field_21_scores)

            # Log validation warnings/flags
            if field_21_flags:
                for flag in field_21_flags:
                    log_entries.append(f"  ⚠️  {flag}")
                    # Check for safety flags
                    if "SAFETY" in flag:
                        safety_flags["crisis"] = True
                        safety_flags["urgent_care"] = True

            # Field 22: Relaxation techniques (multi-select with substring matching)
            # No cross-field data needed

            field_22_scores, field_22_flags = relaxation_techniques_ruleset.get_relaxation_techniques_weights(
                field_22
            )

            # Track reasons - simple format: selected techniques
            field_context = PHASE3_FIELD_CONTEXT[22]
            field_22_display = str(field_22)[:100] if field_22 else "none"
            add_top_contributors(
                all_reasons,
                field_22_scores,
                field_context,
                field_22_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 22 - {field_context}", field_22_scores, str(field_22)[:100] if field_22 else None))

            all_scores = self._combine_scores(all_scores, field_22_scores)

            # Log validation warnings/flags (if any)
            if field_22_flags:
                for flag in field_22_flags:
                    log_entries.append(f"  ⚠️  {flag}")

            # Field 23: Support sources (multi-select with text mapping)
            # Cross-field data: stress_score (Field 20), sleep_irregular (Fields 14/15), gi_symptoms_present (Phase 2)

            # Extract stress score from Field 20 (already processed)
            stress_score = None
            if field_20:
                try:
                    stress_score = int(field_20)
                except (ValueError, TypeError):
                    pass

            field_23_scores, field_23_flags = support_sources_ruleset.get_support_sources_weights(
                field_23,
                age=age,
                stress_score=stress_score,
                sleep_irregular=sleep_irregular,
                gi_symptoms_present=gi_symptoms_present
            )

            # Track reasons - simple format: selected support sources
            field_context = PHASE3_FIELD_CONTEXT[23]
            field_23_display = str(field_23)[:100] if field_23 else "none"
            add_top_contributors(
                all_reasons,
                field_23_scores,
                field_context,
                field_23_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 23 - {field_context}", field_23_scores, str(field_23)[:100] if field_23 else None))

            all_scores = self._combine_scores(all_scores, field_23_scores)

            # Log validation warnings/flags
            if field_23_flags:
                for flag in field_23_flags:
                    log_entries.append(f"  ⚠️  {flag}")
                    # Check for needs_followup flag
                    if "needs_followup" in flag:
                        safety_flags["needs_followup"] = True

            # Field 24: Trauma/Abuse (radio + free text with NLP-based detection and crisis screening)
            # Cross-field data: sleep_disturbance, stress_score, gi_symptom_count, substance_use_high, supports_count

            # Extract GI symptom count from digestive symptoms
            gi_symptom_count = 0
            if digestive_symptoms:
                # Count symptoms (comma-separated)
                gi_symptom_count = len([s.strip() for s in digestive_symptoms.split(',') if s.strip()])

            # Extract supports count from Field 23
            supports_count = 0
            if field_23:
                # Parse selections
                selections_text = field_23.split(';', 1)[0].strip().lower() if ';' in field_23 else field_23.strip().lower()
                if selections_text and selections_text != "none":
                    # Count comma/semicolon-separated items
                    supports_count = len([s.strip() for s in re.split(r'[,;]', selections_text) if s.strip() and s.strip() != "other"])

            # TODO: Extract substance_use_high from Phase 1/2 data (not yet implemented)
            substance_use_high = False

            field_24_scores, field_24_flags = trauma_ruleset.get_trauma_weights(
                field_24,
                sleep_disturbance=sleep_irregular,
                stress_score=stress_score,
                gi_symptom_count=gi_symptom_count,
                substance_use_high=substance_use_high,
                supports_count=supports_count
            )

            # Track reasons - simple format: radio selection
            field_context = PHASE3_FIELD_CONTEXT[24]
            # Extract radio selection for display
            field_24_radio = field_24.split(';', 1)[0].strip() if field_24 and ';' in field_24 else (field_24 if field_24 else "none")
            field_24_display = field_24_radio[:100]
            add_top_contributors(
                all_reasons,
                field_24_scores,
                field_context,
                field_24_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 24 - {field_context}", field_24_scores, field_24_display))

            all_scores = self._combine_scores(all_scores, field_24_scores)

            # Log validation warnings/flags (CRITICAL: Check for crisis)
            if field_24_flags:
                for flag in field_24_flags:
                    log_entries.append(f"  ⚠️  {flag}")
                    # Check for crisis flags
                    if "CRISIS" in flag:
                        safety_flags["crisis_detected"] = True
                        safety_flags["needs_human_review"] = True
                    if "needs_human_review" in flag:
                        safety_flags["needs_human_review"] = True

            # Field 25: Childhood Illnesses (radio + free text with NLP-based detection and age/frequency multipliers)
            field_25_scores, field_25_flags = childhood_illnesses_ruleset.get_childhood_illnesses_weights(field_25)

            # Track reasons - simple format: radio selection
            field_context = PHASE3_FIELD_CONTEXT[25]
            # Extract radio selection for display
            field_25_radio = field_25.split(';', 1)[0].strip() if field_25 and ';' in field_25 else (field_25 if field_25 else "none")
            field_25_display = field_25_radio[:100]
            add_top_contributors(
                all_reasons,
                field_25_scores,
                field_context,
                field_25_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 25 - {field_context}", field_25_scores, field_25_display))

            all_scores = self._combine_scores(all_scores, field_25_scores)

            # Log validation warnings/flags (Check for clinical review)
            if field_25_flags:
                for flag in field_25_flags:
                    log_entries.append(f"  ⚠️  {flag}")
                    # Check for clinical review flags
                    if "needs_clinical_review" in flag:
                        safety_flags["needs_clinical_review"] = True

            # Field 26: Childhood Home Security (radio + free text with NLP-based severity detection)
            field_26_scores, field_26_flags = childhood_home_security_ruleset.get_childhood_home_security_weights(field_26)

            # Track reasons - simple format: radio selection
            field_context = PHASE3_FIELD_CONTEXT[26]
            # Extract radio selection for display
            field_26_radio = field_26.split(';', 1)[0].strip() if field_26 and ';' in field_26 else (field_26 if field_26 else "none")
            field_26_display = field_26_radio[:100]
            add_top_contributors(
                all_reasons,
                field_26_scores,
                field_context,
                field_26_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 26 - {field_context}", field_26_scores, field_26_display))

            all_scores = self._combine_scores(all_scores, field_26_scores)

            # Log validation warnings/flags
            if field_26_flags:
                for flag in field_26_flags:
                    log_entries.append(f"  ⚠️  {flag}")

            # Field 27: Breastfeeding History (radio + duration with cross-field synergies)
            # Extract cross-field data
            c_section = phase1_phase2_context.get("born_via_c_section", "").lower() == "yes"
            early_antibiotics = phase1_phase2_context.get("took_antibiotics_as_child", False)
            current_skin_disease = phase1_phase2_context.get("has_skin_issues", False)

            field_27_scores, field_27_flags = breastfeeding_ruleset.get_breastfeeding_weights(
                field_27,
                c_section=c_section,
                early_antibiotics=early_antibiotics,
                current_skin_disease=current_skin_disease
            )

            # Track reasons - simple format: radio selection
            field_context = PHASE3_FIELD_CONTEXT[27]
            # Extract radio selection for display
            field_27_radio = field_27.split(';', 1)[0].strip() if field_27 and ';' in field_27 else (field_27 if field_27 else "none")
            field_27_display = field_27_radio[:100]
            add_top_contributors(
                all_reasons,
                field_27_scores,
                field_context,
                field_27_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 27 - {field_context}", field_27_scores, field_27_display))

            all_scores = self._combine_scores(all_scores, field_27_scores)

            # Log validation warnings/flags
            if field_27_flags:
                for flag in field_27_flags:
                    log_entries.append(f"  ⚠️  {flag}")

            # Field 28: Early Environmental/Toxic Exposures (radio + free text with NLP-based exposure detection)
            field_28_scores, field_28_flags = early_environmental_exposures_ruleset.get_early_environmental_exposures_weights(
                field_28
            )

            # Track reasons - simple format: radio selection
            field_context = PHASE3_FIELD_CONTEXT[28]
            # Extract radio selection for display
            field_28_radio = field_28.split(';', 1)[0].strip() if field_28 and ';' in field_28 else (field_28 if field_28 else "none")
            field_28_display = field_28_radio[:100]
            add_top_contributors(
                all_reasons,
                field_28_scores,
                field_context,
                field_28_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 28 - {field_context}", field_28_scores, field_28_display))

            all_scores = self._combine_scores(all_scores, field_28_scores)

            # Log validation warnings/flags
            if field_28_flags:
                for flag in field_28_flags:
                    log_entries.append(f"  ⚠️  {flag}")

            # Field 29: Tooth Sensitivity (radio + free text with NLP-based mechanistic scoring)
            # Extract chronic GERD flag from Phase 2 digestive symptoms
            has_chronic_gerd = False
            if digestive_symptoms:
                gerd_keywords = ["gerd", "reflux", "heartburn", "acid reflux"]
                digestive_lower = digestive_symptoms.lower()
                has_chronic_gerd = any(keyword in digestive_lower for keyword in gerd_keywords)

            field_29_scores, field_29_flags = tooth_sensitivity_ruleset.get_tooth_sensitivity_weights(
                field_29,
                has_chronic_gerd=has_chronic_gerd
            )

            # Track reasons - simple format: radio selection
            field_context = PHASE3_FIELD_CONTEXT[29]
            # Extract radio selection for display
            field_29_radio = field_29.split(';', 1)[0].strip() if field_29 and ';' in field_29 else (field_29 if field_29 else "none")
            field_29_display = field_29_radio[:100]
            add_top_contributors(
                all_reasons,
                field_29_scores,
                field_context,
                field_29_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 29 - {field_context}", field_29_scores, field_29_display))

            all_scores = self._combine_scores(all_scores, field_29_scores)

            # Log validation warnings/flags
            if field_29_flags:
                for flag in field_29_flags:
                    log_entries.append(f"  ⚠️  {flag}")

            # Field 30: Current Home/Workplace Environmental Exposures (multi-select + free text)
            # Extract cross-field data: pets and mold exposure from Phase 2
            has_pets_phase2 = phase1_phase2_context.get("has_pets", False)
            # Convert to boolean if it's a string
            if isinstance(has_pets_phase2, str):
                has_pets_phase2 = has_pets_phase2.lower() in ["yes", "true"]

            has_mold_exposure_phase2 = environmental_exposures.get("mold_exposure", False)
            # Convert to boolean if it's a string
            if isinstance(has_mold_exposure_phase2, str):
                has_mold_exposure_phase2 = has_mold_exposure_phase2.lower() in ["yes", "true"]

            field_30_scores, field_30_flags = current_environmental_exposures_ruleset.get_current_environmental_exposures_weights(
                field_30,
                has_pets_phase2=has_pets_phase2,
                has_mold_exposure_phase2=has_mold_exposure_phase2
            )

            # Track reasons - simple format: selected exposures
            field_context = PHASE3_FIELD_CONTEXT[30]
            field_30_display = str(field_30)[:100] if field_30 else "none"
            add_top_contributors(
                all_reasons,
                field_30_scores,
                field_context,
                field_30_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 30 - {field_context}", field_30_scores, field_30_display))

            all_scores = self._combine_scores(all_scores, field_30_scores)

            # Log validation warnings/flags
            if field_30_flags:
                for flag in field_30_flags:
                    log_entries.append(f"  ⚠️  {flag}")

            # Field 31: Chemical Sensitivity (radio + optional free text)
            # Parse field_31 to extract choice and triggers text
            # Format: "Yes; perfume, cleaning aisle, paint; reactions: migraine, rash"
            field_31_choice = ""
            field_31_triggers = ""
            if field_31:
                field_31_str = str(field_31).strip()
                # Check if there's a semicolon separator
                if ";" in field_31_str:
                    parts = field_31_str.split(";", 1)
                    field_31_choice = parts[0].strip()
                    field_31_triggers = parts[1].strip() if len(parts) > 1 else ""
                else:
                    field_31_choice = field_31_str

            field_31_scores, field_31_flags = chemical_sensitivity_ruleset.get_chemical_sensitivity_weights(
                field_31_choice,
                triggers_text=field_31_triggers
            )

            # Track reasons - simple format: choice
            field_context = PHASE3_FIELD_CONTEXT[31]
            field_31_display = field_31_choice if field_31_choice else "none"
            add_top_contributors(
                all_reasons,
                field_31_scores,
                field_context,
                field_31_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 31 - {field_context}", field_31_scores, field_31_display))

            all_scores = self._combine_scores(all_scores, field_31_scores)

            # Log validation warnings/flags
            if field_31_flags:
                for flag in field_31_flags:
                    log_entries.append(f"  ⚠️  {flag}")

            # Field 32: Caffeine Reaction (radio with context-driven scoring)
            # Extract cross-field data
            # digestive_symptoms already extracted (line 697)
            # current_stress already extracted from Field 20 (stored in field_20)
            current_stress_level = 0
            if field_20:
                try:
                    current_stress_level = int(float(str(field_20).strip()))
                except (ValueError, TypeError):
                    pass

            # Extract diagnoses_other from medical history
            diagnoses_other = phase1_phase2_context.get("diagnoses_other", "")

            # Extract hypertension from diagnoses
            has_hypertension = False
            diagnoses = phase1_phase2_context.get("diagnoses", [])
            if isinstance(diagnoses, list):
                # Check for hypertension variants (with underscores replacing spaces)
                hypertension_variants = ["hypertension", "high_blood_pressure", "high blood pressure"]
                for diagnosis in diagnoses:
                    diagnosis_norm = str(diagnosis).lower().replace("_", " ")
                    if any(variant in diagnosis_norm for variant in hypertension_variants):
                        has_hypertension = True
                        break

            field_32_scores, field_32_flags = caffeine_reaction_ruleset.get_caffeine_reaction_weights(
                field_32,
                digestive_symptoms=digestive_symptoms,
                diagnoses_other=diagnoses_other,
                current_stress=current_stress_level,
                has_hypertension=has_hypertension
            )

            # Track reasons - simple format: caffeine reaction choice
            field_context = PHASE3_FIELD_CONTEXT[32]
            field_32_display = str(field_32)[:100] if field_32 else "none"
            add_top_contributors(
                all_reasons,
                field_32_scores,
                field_context,
                field_32_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 32 - {field_context}", field_32_scores, field_32_display))

            all_scores = self._combine_scores(all_scores, field_32_scores)

            # Log validation warnings/flags
            if field_32_flags:
                for flag in field_32_flags:
                    log_entries.append(f"  ⚠️  {flag}")

            # Field 33: Alcohol Flushing (radio + optional free text with context-driven scoring)
            # Extract cross-field data
            # For Field 33, the input format is: "Yes" or "Yes; red wine causes facial flush and nausea"
            # We need to split the radio choice from the followup text
            field_33_choice = ""
            field_33_followup = ""
            if field_33:
                field_33_str = str(field_33).strip()
                # Check if there's a semicolon separator
                if ";" in field_33_str:
                    parts = field_33_str.split(";", 1)
                    field_33_choice = parts[0].strip()
                    field_33_followup = parts[1].strip() if len(parts) > 1 else ""
                else:
                    field_33_choice = field_33_str

            # Extract ancestry from Phase 1/2 data
            ancestry = phase1_phase2_context.get("ancestry", "")

            # Extract diagnoses and diagnoses_other from medical history
            diagnoses = phase1_phase2_context.get("diagnoses", [])
            diagnoses_other = phase1_phase2_context.get("diagnoses_other", "")

            field_33_scores, field_33_flags = alcohol_flushing_ruleset.get_alcohol_flushing_weights(
                field_33_choice,
                followup_text=field_33_followup,
                ancestry=ancestry,
                diagnoses=diagnoses,
                diagnoses_other=diagnoses_other
            )

            # Track reasons - simple format: alcohol flushing choice
            field_context = PHASE3_FIELD_CONTEXT[33]
            field_33_display = field_33_choice[:100] if field_33_choice else "none"
            add_top_contributors(
                all_reasons,
                field_33_scores,
                field_context,
                field_33_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 33 - {field_context}", field_33_scores, field_33_display))

            all_scores = self._combine_scores(all_scores, field_33_scores)

            # Log validation warnings/flags
            if field_33_flags:
                for flag in field_33_flags:
                    log_entries.append(f"  ⚠️  {flag}")

            # Field 34: Synthetic Fiber Wear (multi-select + optional free text)
            # Extract cross-field data
            # For Field 34, the input format is: "Polyester, Nylon, Spandex; I wear polyester workout clothes daily and sweat heavily"
            # We need to split the fiber selections from the followup text
            field_34_selections = []
            field_34_followup = ""
            if field_34:
                field_34_str = str(field_34).strip()
                # Check if there's a semicolon separator
                if ";" in field_34_str:
                    parts = field_34_str.split(";", 1)
                    field_34_selections = parts[0].strip()
                    field_34_followup = parts[1].strip() if len(parts) > 1 else ""
                else:
                    field_34_selections = field_34_str

            # Extract fragrance/VOCs and poor ventilation from Field 30
            # These are detected if Field 30 contains specific keywords
            has_fragrance_vocs = False
            has_poor_ventilation = False
            if field_30:
                field_30_norm = str(field_30).lower()
                if any(kw in field_30_norm for kw in ["fragrance", "perfume", "scent", "air freshener", "candle", "incense"]):
                    has_fragrance_vocs = True
                if any(kw in field_30_norm for kw in ["poor ventilation", "stale air", "no ventilation"]):
                    has_poor_ventilation = True

            field_34_scores, field_34_flags = synthetic_fiber_wear_ruleset.get_synthetic_fiber_wear_weights(
                field_34_selections,
                followup_text=field_34_followup,
                has_fragrance_vocs=has_fragrance_vocs,
                has_poor_ventilation=has_poor_ventilation
            )

            # Track reasons - simple format: fiber selections
            field_context = PHASE3_FIELD_CONTEXT[34]
            field_34_display = str(field_34_selections)[:100] if field_34_selections else "none"
            add_top_contributors(
                all_reasons,
                field_34_scores,
                field_context,
                field_34_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 34 - {field_context}", field_34_scores, field_34_display))

            all_scores = self._combine_scores(all_scores, field_34_scores)

            # Log validation warnings/flags
            if field_34_flags:
                for flag in field_34_flags:
                    log_entries.append(f"  ⚠️  {flag}")

            # Field 35: Seasonal Allergies (radio + optional free text)
            # Parse field_35 to extract choice and allergen/symptoms text
            # Format: "Yes; birch pollen → sneezing, itchy eyes; oral itch after raw apples"
            field_35_choice = ""
            field_35_allergen_symptoms = ""
            if field_35:
                field_35_str = str(field_35).strip()
                # Check if there's a semicolon separator
                if ";" in field_35_str:
                    parts = field_35_str.split(";", 1)
                    field_35_choice = parts[0].strip()
                    field_35_allergen_symptoms = parts[1].strip() if len(parts) > 1 else ""
                else:
                    field_35_choice = field_35_str

            field_35_scores, field_35_flags = seasonal_allergies_ruleset.get_seasonal_allergies_weights(
                field_35_choice,
                allergen_symptoms_text=field_35_allergen_symptoms
            )

            # Track reasons - simple format: choice
            field_context = PHASE3_FIELD_CONTEXT[35]
            field_35_display = field_35_choice if field_35_choice else "none"
            add_top_contributors(
                all_reasons,
                field_35_scores,
                field_context,
                field_35_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 35 - {field_context}", field_35_scores, field_35_display))

            all_scores = self._combine_scores(all_scores, field_35_scores)

            # Log validation warnings/flags
            if field_35_flags:
                for flag in field_35_flags:
                    log_entries.append(f"  ⚠️  {flag}")

            # Field 37: Air Filter Usage (radio + optional brand/model)
            # Parse field_37 to extract choice and brand/model text
            # Format: "Yes; Coway Airmega 400S HEPA with activated carbon"
            field_37_choice = ""
            field_37_brand_model = ""
            if field_37:
                field_37_str = str(field_37).strip()
                # Check if there's a semicolon separator
                if ";" in field_37_str:
                    parts = field_37_str.split(";", 1)
                    field_37_choice = parts[0].strip()
                    field_37_brand_model = parts[1].strip() if len(parts) > 1 else ""
                else:
                    field_37_choice = field_37_str

            # Extract context flags from Field 30 (Current Environmental Exposures)
            # These were already extracted earlier in the code
            has_mold_dampness_field30 = has_mold_exposure_phase2  # From Phase 2
            has_poor_ventilation_field30 = False
            has_gas_stove_field30 = False

            # Parse Field 30 to detect poor ventilation and gas stove
            if field_30:
                field_30_norm = str(field_30).lower()
                has_poor_ventilation_field30 = any(kw in field_30_norm for kw in [
                    "poor ventilation", "stale air", "no ventilation", "stuffy"
                ])
                has_gas_stove_field30 = any(kw in field_30_norm for kw in [
                    "gas stove", "gas range", "gas cooktop"
                ])

            # For now, we don't have wildfire smoke data - set to False
            has_wildfire_smoke = False

            field_37_scores, field_37_flags = air_filter_ruleset.get_air_filter_weights(
                field_37_choice,
                brand_model_text=field_37_brand_model,
                has_mold_dampness=has_mold_dampness_field30,
                has_poor_ventilation=has_poor_ventilation_field30,
                has_gas_stove=has_gas_stove_field30,
                has_wildfire_smoke=has_wildfire_smoke
            )

            # Track reasons - simple format: choice
            field_context = PHASE3_FIELD_CONTEXT[37]
            field_37_display = field_37_choice if field_37_choice else "none"
            add_top_contributors(
                all_reasons,
                field_37_scores,
                field_context,
                field_37_display,
                top_n=self.TOP_N_CONTRIBUTORS
            )

            # Log
            log_entries.append(self._create_log_entry(f"Field 37 - {field_context}", field_37_scores, field_37_display))

            all_scores = self._combine_scores(all_scores, field_37_scores)

            # Log validation warnings/flags
            if field_37_flags:
                for flag in field_37_flags:
                    log_entries.append(f"  ⚠️  {flag}")

            # Add final scores to log
            log_entries.append("\n" + "="*80)
            log_entries.append("FINAL SCORES (PHASE 3):")
            log_entries.append("="*80 + "\n")

            # Rank focus areas
            ranked_focus_areas = sorted(
                [(FOCUS_AREA_NAMES[code], code, score) for code, score in all_scores.items()],
                key=lambda x: x[2],
                reverse=True,
            )

            for focus_area, code, score in ranked_focus_areas:
                log_entries.append(f"{focus_area} ({code}): {score:.3f}")

            # Save log file
            log_content = "\n".join(log_entries)
            log_file_path = self._save_log_file(log_content, patient_id, suffix="phase3")

            # Save reasons file
            reasons_file_path = self._save_reasons_file(all_reasons, patient_id, suffix="phase3")

            print(f"✅ Phase 3 log file saved to: {log_file_path}")
            print(f"✅ Phase 3 reasons file saved to: {reasons_file_path}")

            # Build markdown output
            result = ["# Focus Area Evaluation Results (Phase 3)\n"]

            # Add safety flags if present
            if safety_flags.get("crisis"):
                result.append("⚠️ **CRISIS FLAG**: Text contains suicidal/self-harm keywords. Route to crisis support immediately.\n")
            if safety_flags.get("urgent_care"):
                result.append("⚠️ **URGENT CARE FLAG**: Text contains urgent care keywords (chest pain, worst headache, blood in stool).\n")
            if safety_flags.get("red_flag"):
                result.append("⚠️ **RED FLAG**: Text contains urgent medical keywords (chest pain, stroke, breathing issues, etc.).\n")

            # Add adherence multiplier
            if adherence_multiplier is not None:
                result.append(f"**Adherence Multiplier (AM)**: {adherence_multiplier:.2f}\n")

            result.append("## Ranked Focus Areas (by weighted score)\n")
            for focus_area, code, score in ranked_focus_areas:
                result.append(f"- **{focus_area} ({code})**: {score:.2f}")

            return "\n".join(result)

        except Exception as e:
            return f"Error evaluating phase3 focus areas: {str(e)}"

