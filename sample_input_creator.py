import json
import os

# This is just for creating test input, not part of the crew pipeline
'''
sample_patient = {
    "age": 28,
    "sex_assigned_at_birth": "female",
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
        "Triglycerides": 180,
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
'''


# Patient input data (not part of main pipeline, just for testing)
# Patient input data (not part of main pipeline, just for testing)
sample_patient = {
    "age": 34,
    "sex_assigned_at_birth": "male",
    "height": "5'10\"",
    "weight": "235 lb",
    "BMI": 33.7,
    "alcohol": "Occasional",
    "activity": "Low",
    "rx": [],
    "supplements": [],
    "lifestyle_notes": ["Central adiposity"],
    "biomarkers": {
        "ALT": "55 U/L",
        "AST": "45 U/L",
        "Triglycerides": "250 mg/dL",
        "HDL": "38 mg/dL",
        "LDL": "145 mg/dL",
        "TG:HDL": 6.58,
        "Glucose": "112 mg/dL",
        "Fasting Insulin": "18 µIU/mL",
        "HOMA-IR": 4.98,
        "HbA1c": "6.2 %",
        "hs-CRP": "4.0 mg/L",
        "Vitamin D (25-OH)": "18 ng/mL",
        "Ferritin": "310 ng/mL"
    },
    "metrics": {
        "BMI": 33.7,
        "TG:HDL": 6.58,
        "TC:HDL": 6.18,
        "HOMA-IR": 4.98
    }
}


# Wrap in a list so it works with multi-patient loader
patients = [sample_patient]

os.makedirs("inputs", exist_ok=True)
with open("inputs/patients.json", "w") as f:
    json.dump(patients, f, indent=2)

print("✅ Created inputs/patients.json")
