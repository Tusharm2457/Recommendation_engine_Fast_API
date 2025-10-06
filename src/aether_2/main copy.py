#!/usr/bin/env python
import sys
import warnings

from datetime import datetime

from aether_2.crew import Aether2

from dotenv import load_dotenv
import os

# Add at the very top of main.py
load_dotenv()

def debug_env_vars():
    print("=== Environment Variables Debug ===")
    print(f"MODEL: {os.getenv('MODEL')}")
    print(f"OPENAI_API_TYPE: {os.getenv('OPENAI_API_TYPE')}")
    print(f"OPENAI_API_KEY: {'Set' if os.getenv('OPENAI_API_KEY') else 'Not Set'}")
    print(f"OPENAI_API_BASE: {os.getenv('OPENAI_API_BASE')}")
    print(f"OPENAI_API_VERSION: {os.getenv('OPENAI_API_VERSION')}")
    print("=====================================")

# Call this before running your crew
debug_env_vars()
warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# This main file is intended to be a way for you to run your
# crew locally, so refrain from adding unnecessary logic into this file.
# Replace with inputs you want to test with, it will automatically
# interpolate any tasks and agents information

def run():
    """
    Run the crew.
    """
    inputs = {
        'medical_data': {
            "age": 24,
            "sex_assigned_at_birth": "male",
            "ancestry": ["Asian"],
            "health_goals": ["reducing bloat", "improving sleep"],
            "causes_to_issues": ["poor diet", "high stress"],
            "what_needs_to_change": ["better sleep routine", "better diet", "stress management"],
            "last_felt_well": "Summer 2013",
            "symptom_triggers": {
                "onset_or_worsening": "Puberty",
                "worsened_by": ["Lack of sleep"],
                "worsens_at_time": "Morning",
                "worsens_at_location": "Home"
            },
            "what_helps": ["Deep breathing", "Exercise"],
            "allergens_and_reactions": ["Dust", "Cold"],
            "childhood_antibiotic_use": True,
            "alcohol_use": "never",
            "recreational_drug_use": False,
            "occupation": {
                "role": "Student",
                "stress_level": 10
            },
            "physical_activity": {
                "days_per_week": 3,
                "type": "running",
                "intensity": "moderate"
            },
            "sunlight_exposure": {
                "days_per_week": 5,
                "average_minutes_per_day": 10,
                "weekly_ranking": [
                    "Monday", "Thursday", "Friday", "Tuesday", "Wednesday", "Sunday", "Saturday"
                ]
            },
            "biomarkers": {
                "Triglycerides": 135,
                "TSH": 2.1,
                "Estradiol": 28,
                "HbA1c": 5.3,
                "FSH": 4.5,
                "Ferritin": 70,
                "Lp(a)": 15,
                "LH": 5.3,
                "Albumin": 4.4,
                "SHBG": 30,
                "Free Testosterone": 18,
                "Alanine Aminotransferase": 28,
                "Aspartate Aminotransferase": 24,
                "Creatinine": 0.9,
                "Blood Urea Nitrogen": 14,
                "Bilirubin": 0.8,
                "C-Peptide": 1.9,
                "EAG": 104,
                "LDL:HDL Ratio": 2.2,
                "VLDL": 22,
                "Iron": 95,
                "Unsaturated Iron Binding Capacity": 180,
                "Calcium": 9.5,
                "Alkaline Phosphatase": 68,
                "Direct Bilirubin": 0.2,
                "25-(OH) Vitamin D": 14,
                "Apolipoprotein A1 (APOA1)": 130,
                "Apolipoprotein B (APOB)": 90,
                "Morning Cortisol": 4.2,
                "Dehydroepiandrosterone Sulfate (DHEA-S)": 320,
                "eGFR": 95,
                "HDL Cholesterol": 55,
                "% Hemoglobin A1C": 5.3,
                "High-Sensitivity CRP": 1.2,
                "Fasting Insulin": 7.5,
                "LDL Cholesterol": 110,
                "Testosterone, Total (Males)": 540,
                "Calculated Total Cholesterol": 185,
                "ApoB:ApoA1 Ratio": 0.69,
                "Total Cholesterol:HDL Ratio": 3.4,
                "Triglycerides:HDL Ratio": 2.45,
                "Testosterone:Cortisol Ratio": 128.57,
                "HOMA-IR": 1.6,
                "HS-CRP": 1.2,
                "Homocysteine": 9.4,
                "Ferritin": 70,
                "Cortisol": 6.1
            }
        }
    }

    try:
        Aether2().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        'medical_data': {
            "age": 24,
            "sex_assigned_at_birth": "male",
            "ancestry": ["Asian"],
            "health_goals": ["reducing bloat", "improving sleep"],
            "causes_to_issues": ["poor diet", "high stress"],
            "what_needs_to_change": ["better sleep routine", "better diet", "stress management"],
            "last_felt_well": "Summer 2013",
            "symptom_triggers": {
                "onset_or_worsening": "Puberty",
                "worsened_by": ["Lack of sleep"],
                "worsens_at_time": "Morning",
                "worsens_at_location": "Home"
            },
            "what_helps": ["Deep breathing", "Exercise"],
            "allergens_and_reactions": ["Dust", "Cold"],
            "childhood_antibiotic_use": True,
            "alcohol_use": "never",
            "recreational_drug_use": False,
            "occupation": {
                "role": "Student",
                "stress_level": 10
            },
            "physical_activity": {
                "days_per_week": 3,
                "type": "running",
                "intensity": "moderate"
            },
            "sunlight_exposure": {
                "days_per_week": 5,
                "average_minutes_per_day": 10,
                "weekly_ranking": [
                    "Monday", "Thursday", "Friday", "Tuesday", "Wednesday", "Sunday", "Saturday"
                ]
            },
            "biomarkers": {
                "Triglycerides": 135,
                "TSH": 2.1,
                "Estradiol": 28,
                "HbA1c": 5.3,
                "FSH": 4.5,
                "Ferritin": 70,
                "Lp(a)": 15,
                "LH": 5.3,
                "Albumin": 4.4,
                "SHBG": 30,
                "Free Testosterone": 18,
                "Alanine Aminotransferase": 28,
                "Aspartate Aminotransferase": 24,
                "Creatinine": 0.9,
                "Blood Urea Nitrogen": 14,
                "Bilirubin": 0.8,
                "C-Peptide": 1.9,
                "EAG": 104,
                "LDL:HDL Ratio": 2.2,
                "VLDL": 22,
                "Iron": 95,
                "Unsaturated Iron Binding Capacity": 180,
                "Calcium": 9.5,
                "Alkaline Phosphatase": 68,
                "Direct Bilirubin": 0.2,
                "25-(OH) Vitamin D": 14,
                "Apolipoprotein A1 (APOA1)": 130,
                "Apolipoprotein B (APOB)": 90,
                "Morning Cortisol": 4.2,
                "Dehydroepiandrosterone Sulfate (DHEA-S)": 320,
                "eGFR": 95,
                "HDL Cholesterol": 55,
                "% Hemoglobin A1C": 5.3,
                "High-Sensitivity CRP": 1.2,
                "Fasting Insulin": 7.5,
                "LDL Cholesterol": 110,
                "Testosterone, Total (Males)": 540,
                "Calculated Total Cholesterol": 185,
                "ApoB:ApoA1 Ratio": 0.69,
                "Total Cholesterol:HDL Ratio": 3.4,
                "Triglycerides:HDL Ratio": 2.45,
                "Testosterone:Cortisol Ratio": 128.57,
                "HOMA-IR": 1.6,
                "HS-CRP": 1.2,
                "Homocysteine": 9.4,
                "Ferritin": 70,
                "Cortisol": 6.1
            }
        },
    }

    try:
        Aether2().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        Aether2().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        'medical_data': {
            "age": 24,
            "sex_assigned_at_birth": "male",
            "ancestry": ["Asian"],
            "health_goals": ["reducing bloat", "improving sleep"],
            "causes_to_issues": ["poor diet", "high stress"],
            "what_needs_to_change": ["better sleep routine", "better diet", "stress management"],
            "last_felt_well": "Summer 2013",
            "symptom_triggers": {
                "onset_or_worsening": "Puberty",
                "worsened_by": ["Lack of sleep"],
                "worsens_at_time": "Morning",
                "worsens_at_location": "Home"
            },
            "what_helps": ["Deep breathing", "Exercise"],
            "allergens_and_reactions": ["Dust", "Cold"],
            "childhood_antibiotic_use": True,
            "alcohol_use": "never",
            "recreational_drug_use": False,
            "occupation": {
                "role": "Student",
                "stress_level": 10
            },
            "physical_activity": {
                "days_per_week": 3,
                "type": "running",
                "intensity": "moderate"
            },
            "sunlight_exposure": {
                "days_per_week": 5,
                "average_minutes_per_day": 10,
                "weekly_ranking": [
                    "Monday", "Thursday", "Friday", "Tuesday", "Wednesday", "Sunday", "Saturday"
                ]
            },
            "biomarkers": {
                "Triglycerides": 135,
                "TSH": 2.1,
                "Estradiol": 28,
                "HbA1c": 5.3,
                "FSH": 4.5,
                "Ferritin": 70,
                "Lp(a)": 15,
                "LH": 5.3,
                "Albumin": 4.4,
                "SHBG": 30,
                "Free Testosterone": 18,
                "Alanine Aminotransferase": 28,
                "Aspartate Aminotransferase": 24,
                "Creatinine": 0.9,
                "Blood Urea Nitrogen": 14,
                "Bilirubin": 0.8,
                "C-Peptide": 1.9,
                "EAG": 104,
                "LDL:HDL Ratio": 2.2,
                "VLDL": 22,
                "Iron": 95,
                "Unsaturated Iron Binding Capacity": 180,
                "Calcium": 9.5,
                "Alkaline Phosphatase": 68,
                "Direct Bilirubin": 0.2,
                "25-(OH) Vitamin D": 14,
                "Apolipoprotein A1 (APOA1)": 130,
                "Apolipoprotein B (APOB)": 90,
                "Morning Cortisol": 4.2,
                "Dehydroepiandrosterone Sulfate (DHEA-S)": 320,
                "eGFR": 95,
                "HDL Cholesterol": 55,
                "% Hemoglobin A1C": 5.3,
                "High-Sensitivity CRP": 1.2,
                "Fasting Insulin": 7.5,
                "LDL Cholesterol": 110,
                "Testosterone, Total (Males)": 540,
                "Calculated Total Cholesterol": 185,
                "ApoB:ApoA1 Ratio": 0.69,
                "Total Cholesterol:HDL Ratio": 3.4,
                "Triglycerides:HDL Ratio": 2.45,
                "Testosterone:Cortisol Ratio": 128.57,
                "HOMA-IR": 1.6,
                "HS-CRP": 1.2,
                "Homocysteine": 9.4,
                "Ferritin": 70,
                "Cortisol": 6.1
            }
        }
    }

    try:
        Aether2().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")