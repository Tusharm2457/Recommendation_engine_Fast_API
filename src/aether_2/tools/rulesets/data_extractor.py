"""
Data Extractor for Focus Areas Generator

This module provides shared data extraction logic for Phase 2 (and eventually Phase 3).
Extracts patient data from the nested JSON structure and returns a dictionary with all fields.
"""

from typing import Dict, Any, Optional, List


def extract_phase1_phase2_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract Phase 1 and Phase 2 data from patient_and_blood_data structure.
    
    This function extracts all fields needed by Phase 2 rulesets and returns them
    in a dictionary with the exact same structure as the original _extract_patient_data method.
    
    Args:
        data: The patient_and_blood_data dictionary (or wrapper containing it)
    
    Returns:
        Dictionary with all extracted fields, maintaining exact same keys and structure
        as the original implementation for backward compatibility.
    """
    if "patient_and_blood_data" in data:
        data = data["patient_and_blood_data"]

    patient_form = data.get("patient_form", {})
    patient_data = patient_form.get("patient_data", {})
    phase1_data = patient_data.get("phase1_basic_intake", {})
    phase2_data = patient_data.get("phase2_detailed_intake", {})

    # Blood Results (for vitamin D)
    # Check both possible locations
    latest_biomarkers = data.get("latest_biomarker_results", data.get("blood_report", {}))
    vitamin_d_raw = latest_biomarkers.get("25-(OH) Vitamin D")

    # Parse vitamin D value and determine if optimal (≥80 ng/mL)
    vitamin_d_optimal = False
    vitamin_d_level = None
    if vitamin_d_raw:
        try:
            # Extract numeric value from string like "95.89 ng/mL"
            vitamin_d_level = float(vitamin_d_raw.split()[0])
            vitamin_d_optimal = vitamin_d_level >= 80
        except (ValueError, IndexError):
            pass  # If parsing fails, keep as None

    # Demographics
    demographics = phase1_data.get("demographics", {})
    age = demographics.get("age")
    biological_sex = demographics.get("biological_sex")
    ancestry = demographics.get("ancestry", [])
    ancestry_other = demographics.get("ancestry_other")
    height_feet = demographics.get("height_feet")
    height_inches = demographics.get("height_inches")
    weight_lbs = demographics.get("weight_lbs")
    
    # Calculate total height in inches and BMI
    height_total_inches = None
    bmi = None
    if height_feet is not None and height_inches is not None:
        height_total_inches = (height_feet * 12) + height_inches
    if height_total_inches and weight_lbs:
        bmi = (weight_lbs / (height_total_inches ** 2)) * 703
    
    # Medical History
    medical_history = phase1_data.get("medical_history", {})
    diagnoses = medical_history.get("diagnoses", [])
    diagnoses_years = medical_history.get("diagnoses_years", {})
    diagnoses_other = medical_history.get("diagnoses_other")
    surgeries = medical_history.get("surgeries")

    # Parse diagnosis list - handle "other" field
    diagnosis_list = []
    diagnosis_years_list = []

    if diagnoses:
        for diagnosis in diagnoses:
            diagnosis_clean = diagnosis.lower().strip().rstrip('_')

            # If diagnosis is "other", use diagnoses_other field
            if diagnosis_clean == "other" and diagnoses_other:
                diagnosis_name = diagnoses_other.strip()
            else:
                # Convert underscore format to readable (e.g., "kidney_stones_" -> "kidney_stones")
                diagnosis_name = diagnosis_clean

            if diagnosis_name and diagnosis_name != "none":
                diagnosis_list.append(diagnosis_name)
                # Get year if available
                year = diagnoses_years.get(diagnosis, "unknown")
                diagnosis_years_list.append(year)

    # Create comma-separated string for rulesets that need string format
    diagnoses_string = ",".join(diagnosis_list) if diagnosis_list else None
    
    # Medications
    medications_section = phase1_data.get("medications", {})
    has_medications = medications_section.get("has_medications", False)
    current_medications = medications_section.get("current_medications", [])
    
    # Allergies
    allergies_section = phase1_data.get("allergies", {})
    has_allergies = allergies_section.get("has_allergies", False)
    known_allergies = allergies_section.get("known_allergies", [])

    # Parse allergen names and reactions
    allergen_list = []
    reaction_list = []

    if has_allergies and known_allergies:
        for allergy_item in known_allergies:
            allergen = allergy_item.get("allergen", "").lower().strip()
            reaction = allergy_item.get("reaction", "")

            # If allergen is "other", use allergen_other field
            if allergen == "other":
                allergen_name = allergy_item.get("allergen_other", "").strip()
            else:
                allergen_name = allergen.capitalize()  # Normalize case

            if allergen_name:
                allergen_list.append(allergen_name)
                reaction_list.append(reaction)
    
    # Supplements
    supplements_section = phase1_data.get("supplements", {})
    has_supplements = supplements_section.get("has_supplements", False)
    current_supplements = supplements_section.get("current_supplements", [])

    # Create comma-separated string for rulesets that need string format
    supplements_string = ",".join(current_supplements) if current_supplements else None
    
    # Wearable Devices
    wearable_devices = phase1_data.get("wearable_devices", {})
    has_any_wearables = wearable_devices.get("has_any_wearables", False)
    
    # Complementary Approaches
    complementary_approaches = phase1_data.get("complementary_approaches", {})
    selected_approaches = complementary_approaches.get("selected_approaches", [])

    # ========== PHASE 2: DETAILED INTAKE ==========

    # Lifestyle Factors
    lifestyle_factors = phase2_data.get("lifestyle_factors", {})

    # Tobacco
    tobacco = lifestyle_factors.get("tobacco", {})
    tobacco_use_status = tobacco.get("use_status")
    tobacco_quit_year = tobacco.get("quit_year")
    tobacco_duration_category = tobacco.get("duration_category")

    # Alcohol
    alcohol = lifestyle_factors.get("alcohol", {})
    alcohol_frequency = alcohol.get("frequency")
    alcohol_typical_amount = alcohol.get("typical_amount")

    # Recreational Drugs
    recreational_drugs = lifestyle_factors.get("recreational_drugs", {})
    uses_substances = recreational_drugs.get("uses_substances", False)
    substance_details = recreational_drugs.get("substance_details")

    # Physical Activity
    physical_activity = phase2_data.get("physical_activity", {})
    exercise_days_per_week = physical_activity.get("exercise_days_per_week")

    # Sleep Patterns
    sleep_patterns = phase2_data.get("sleep_patterns", {})
    sleep_hours_category = sleep_patterns.get("hours_category")
    snoring_sleep_apnea = sleep_patterns.get("snoring_sleep_apnea")
    night_wake_frequency = sleep_patterns.get("night_wake_frequency")
    trouble_falling_asleep = sleep_patterns.get("trouble_falling_asleep", False)
    trouble_staying_asleep = sleep_patterns.get("trouble_staying_asleep", False)
    wake_feeling_refreshed = sleep_patterns.get("wake_feeling_refreshed", False)
    night_urination_frequency = sleep_patterns.get("night_urination_frequency")

    # Occupation & Wellness
    occupation_wellness = phase2_data.get("occupation_wellness", {})
    job_title = occupation_wellness.get("job_title")
    work_stress_level = occupation_wellness.get("work_stress_level")

    # Dietary Habits
    dietary_habits = phase2_data.get("dietary_habits", {})
    diet_style = dietary_habits.get("diet_style")
    diet_style_other = dietary_habits.get("diet_style_other")
    eating_out_frequency = dietary_habits.get("eating_out_frequency")

    # Sunlight Exposure
    sunlight_exposure = phase2_data.get("sunlight_exposure", {})
    sunlight_days_per_week = sunlight_exposure.get("days_per_week")
    sunlight_avg_minutes = sunlight_exposure.get("average_minutes_per_day")

    # Pain and Skin Health
    pain_and_skin_health = phase2_data.get("pain_and_skin_health", {})

    # Chronic Pain
    chronic_pain = pain_and_skin_health.get("chronic_pain", {})
    has_chronic_pain = chronic_pain.get("has_chronic_pain", False)
    pain_details = chronic_pain.get("pain_details")

    # Headaches
    headaches = pain_and_skin_health.get("headaches", {})
    frequent_headaches_migraines = headaches.get("frequent_headaches_migraines", False)
    headache_details = headaches.get("headache_details")

    # Skin Health
    skin_health = pain_and_skin_health.get("skin_health", {})
    has_skin_issues = skin_health.get("has_skin_issues", False)
    skin_condition_details = skin_health.get("skin_condition_details")

    # Dental Health
    dental_health = phase2_data.get("dental_health", {})
    daily_brush_floss = dental_health.get("daily_brush_floss")
    mercury_fillings_removed = dental_health.get("mercury_fillings_removed", False)
    removal_timeframe = dental_health.get("removal_timeframe")
    dental_work = dental_health.get("dental_work", {})

    # Systems Review
    systems_review = phase2_data.get("systems_review", {})
    digestive_symptoms = systems_review.get("digestive_symptoms")

    # Family Medical History
    family_medical_history = phase2_data.get("family_medical_history", {})
    has_family_history = family_medical_history.get("has_family_history", False)
    family_conditions_detail = family_medical_history.get("conditions_detail", {})
    family_other_conditions = family_medical_history.get("other_conditions_text")

    # Environmental Exposures
    environmental_exposures = phase2_data.get("environmental_exposures", {})
    mold_exposure = environmental_exposures.get("mold_exposure", False)
    chemical_exposures = environmental_exposures.get("chemical_exposures")
    chemical_exposure_other = environmental_exposures.get("chemical_exposure_other")

    # Pets and Animals
    pets_animals = phase2_data.get("pets_animals", {})
    has_pets = pets_animals.get("has_pets", False)

    # Childhood Development
    childhood_development = phase2_data.get("childhood_development", {})
    born_via_c_section = childhood_development.get("born_via_c_section")
    high_sugar_childhood_diet = childhood_development.get("high_sugar_childhood_diet")

    # Childhood Antibiotics
    childhood_antibiotics = phase2_data.get("childhood_antibiotics", {})
    took_antibiotics_as_child = childhood_antibiotics.get("took_antibiotics_as_child", False)

    # Medication Side Effects
    medication_side_effects = phase2_data.get("medication_side_effects", {})
    has_adverse_reactions = medication_side_effects.get("has_adverse_reactions", False)
    reaction_details = medication_side_effects.get("reaction_details")

    # Reproductive & Hormonal Health
    reproductive_hormonal_health = phase2_data.get("reproductive_hormonal_health", {})
    male_specific = reproductive_hormonal_health.get("male_specific")
    female_specific = reproductive_hormonal_health.get("female_specific", {})

    # Female-specific
    female_menstrual_concerns = None
    female_concern_details = None
    if female_specific:
        female_menstrual_concerns = female_specific.get("menstrual_concerns")
        female_concern_details = female_specific.get("concern_details")

    # Male-specific
    male_hormonal_concerns = None
    male_concern_details = None
    if male_specific:
        male_hormonal_concerns = male_specific.get("hormonal_concerns")
        male_concern_details = male_specific.get("concern_details")

    return {
        # Demographics
        "age": age,
        "biological_sex": biological_sex,
        "ancestry": ancestry,
        "ancestry_other": ancestry_other,
        "height_feet": height_feet,
        "height_inches": height_inches,
        "height_total_inches": height_total_inches,
        "weight_lbs": weight_lbs,
        "bmi": bmi,

        # Medical History
        "diagnoses": diagnoses,
        "diagnoses_years": diagnoses_years,
        "diagnoses_other": diagnoses_other,
        "diagnoses_string": diagnoses_string,
        "surgeries": surgeries,
        "diagnosis_list": diagnosis_list,
        "diagnosis_years_list": diagnosis_years_list,

        # Medications
        "has_medications": has_medications,
        "current_medications": current_medications,

        # Allergies
        "has_allergies": has_allergies,
        "known_allergies": known_allergies,
        "allergen_list": allergen_list,
        "reaction_list": reaction_list,

        # Supplements
        "has_supplements": has_supplements,
        "current_supplements": current_supplements,
        "supplements_string": supplements_string,

        # Wearables & Complementary
        "has_any_wearables": has_any_wearables,
        "selected_approaches": selected_approaches,

        # Tobacco
        "tobacco_use_status": tobacco_use_status,
        "tobacco_quit_year": tobacco_quit_year,
        "tobacco_duration_category": tobacco_duration_category,

        # Alcohol
        "alcohol_frequency": alcohol_frequency,
        "alcohol_typical_amount": alcohol_typical_amount,

        # Recreational Drugs
        "uses_substances": uses_substances,
        "substance_details": substance_details,

        # Physical Activity
        "exercise_days_per_week": exercise_days_per_week,

        # Sleep
        "sleep_hours_category": sleep_hours_category,
        "snoring_sleep_apnea": snoring_sleep_apnea,
        "night_wake_frequency": night_wake_frequency,
        "trouble_falling_asleep": trouble_falling_asleep,
        "trouble_staying_asleep": trouble_staying_asleep,
        "wake_feeling_refreshed": wake_feeling_refreshed,
        "night_urination_frequency": night_urination_frequency,

        # Occupation
        "job_title": job_title,
        "work_stress_level": work_stress_level,

        # Diet
        "diet_style": diet_style,
        "diet_style_other": diet_style_other,
        "eating_out_frequency": eating_out_frequency,

        # Sunlight
        "sunlight_days_per_week": sunlight_days_per_week,
        "sunlight_avg_minutes": sunlight_avg_minutes,
        "vitamin_d_optimal": vitamin_d_optimal,
        "vitamin_d_level": vitamin_d_level,

        # Pain & Skin
        "has_chronic_pain": has_chronic_pain,
        "pain_details": pain_details,
        "frequent_headaches_migraines": frequent_headaches_migraines,
        "headache_details": headache_details,
        "has_skin_issues": has_skin_issues,
        "skin_condition_details": skin_condition_details,

        # Dental
        "daily_brush_floss": daily_brush_floss,
        "mercury_fillings_removed": mercury_fillings_removed,
        "removal_timeframe": removal_timeframe,
        "dental_work": dental_work,

        # Digestive
        "digestive_symptoms": digestive_symptoms,

        # Family History
        "has_family_history": has_family_history,
        "family_conditions_detail": family_conditions_detail,
        "family_other_conditions": family_other_conditions,

        # Environmental
        "mold_exposure": mold_exposure,
        "chemical_exposures": chemical_exposures,
        "chemical_exposure_other": chemical_exposure_other,

        # Pets
        "has_pets": has_pets,

        # Childhood
        "born_via_c_section": born_via_c_section,
        "high_sugar_childhood_diet": high_sugar_childhood_diet,
        "took_antibiotics_as_child": took_antibiotics_as_child,

        # Medication Reactions
        "has_adverse_reactions": has_adverse_reactions,
        "reaction_details": reaction_details,

        # Reproductive Health
        "female_menstrual_concerns": female_menstrual_concerns,
        "female_concern_details": female_concern_details,
        "male_hormonal_concerns": male_hormonal_concerns,
        "male_concern_details": male_concern_details
    }

