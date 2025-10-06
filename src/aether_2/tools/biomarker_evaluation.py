from crewai.tools import BaseTool
from typing import Type, Tuple, ClassVar, Dict, Any, Union
from pydantic import BaseModel, Field
import json
import re

class BiomarkerEvaluationInput(BaseModel):
    """
    Expects: Json structure in this format {
        "patient_form": { ... your patient JSON structure ... },
        "blood_report": { ... the new blood report JSON structure ... }
    }
    """
    patient_and_blood_data: Union[str, dict] = Field(
        ..., 
        description="JSON string OR dict with keys: patient_form, blood_report"
    )
class BiomarkerEvaluationTool(BaseTool):
    name: str = "biomarker_evaluator"
    description: str = (
        "Evaluates biomarker values against functional / optimal / risk ranges."
    )
    args_schema: Type[BaseModel] = BiomarkerEvaluationInput

    # Keep all your existing SEVERITY_ORDER, biomarker_ranges, and units dictionaries
    SEVERITY_ORDER: ClassVar[Dict[str, int]] = {
        # ... (your entire existing SEVERITY_ORDER dictionary remains the same)
         # ───────── 0  —  Ideal / very low-risk ───────── #
        "optimal": 0,
        "very_good": 0,  # TC:HDL ratio < 3.5
        "desirable": 0,  # Trig:HDL ratio < 1
        "insulin_sensitive": 0,  # HOMA-IR < 1
        "hrt_optimal": 0,  # TRT / HRT targets
        "excellent":0,

        # ───────── 1  —  Normal / physiologic range ─── #
        "normal": 1,
        "functional": 1,
        "lab": 1,
        "lab_range": 1,
        "healthy": 1,
        "sufficient": 1,
        "low_risk": 1,
        # physiologic female hormone phases
        "follicular": 1,
        "mid_cycle": 1,
        "luteal": 1,
        "postmeno": 1,
        # age brackets (handled internally but mapped here for completeness)
        "age_20_49": 1,
        "age_40_60": 1,
        "age_60_plus": 1,
        "borderline": 1,

        # ───────── 2  —  Early deviation / mild concern ─ #
        
        
        
        "prediabetes": 2,
        "low":2,
        "high": 2,

        # ───────── 3  —  Clinically high / clear risk ─── #
        
        
        
        "insulin_resistant": 3,
        "very_low": 3,
        "very_high": 3,
        "diabetes": 3,

        # ───────── 4  —  Critical / danger zone ───────── #
        "critical": 4,  #high category
        "severe": 4,    #low category
        
        
    }

    biomarker_ranges: ClassVar[Dict[str, Dict[str, Any]]] = {
        # ... (your entire existing biomarker_ranges dictionary remains the same)
        "Apolipoprotein A1 (APOA1)": {
        "male": {
            "low": (None, 115),
            "normal": (110, 180),
            "optimal": (115, None)
        },
        "female": {
            "low": (None, 125),
            "normal": (110, 205),
            "optimal": (125, None)
        }
        },

        "Apolipoprotein B (APOB)": {
            "male":{
            "low": (None, 66),
            "optimal": (66, 133),
            "high": (100, 120),
            "very_high": (120, None)
            },
            "female": {
            "low": (None, 60),
            "optimal": (60, 117),
            "high": (100, 120),
            "very_high": (120, None)
        }
        },

        "Alkaline Phosphatase (ALP)": {
            "male": {
                "very_low": (None, 25),
                "low": (25, 39),
                "optimal": (40, 116),
                "high": (117, 150),
                "very_high": (151, None)
            },
            "female": {
                "very_low": (None, 20),
                "low": (20, 34),
                "optimal": (35, 104),
                "high": (105, 140),
                "very_high": (141, None)
            }
        },

        "ApoB:ApoA1 Ratio": {
            "male": {
            "optimal": ( None,0.70)
        },
        "female": {
            "optimal": (None,0.60)
        }
        },  # to add

        # ---------------- Adrenal / steroid hormones -------------------- #
        '''
        "Cortisol (AM)": {"optimal": (10, 17)},  # 6 – 8 a.m.
        "Cortisol (PM)": {"optimal": (4, 10)},  # ~4 p.m.
        '''
        "Cortisol": {
            "very_low": (None, 8),
            "low": (8, 13),
            "optimal": (14, 17),
            "high": (18, 25),
            "very_high": (26, None)
        },
        "Dehydroepiandrosterone Sulfate (DHEA-S)": {
            "male": {"severe":(None,100),"normal":(100, 150),
            "optimal": (150, 250),
            "functional": (250, 290),
            "critical":(290,None)},  # adult functional
            "female": {"severe":(None,100),
            "normal":(100, 150),
            "optimal": (150, 200),
            "critical":(290,None)}
            # focus on functional ranges, so only those are kept.
        },
        "EAG (Calc.)":{
            "optimal": (85, 107),
            "prediabetes":(108,137),
            "diabetes":(138,None)

        },
        "C-peptide": {
        "male": {
            "very_low": (None, 0.7),
            "low": (0.7, 1.0),
            "optimal": (1.1, 4.4),
            "high": (4.5, 6.0),
            "very_high": (6.1, None)
        },
        "female": {
            "very_low": (None, 0.7),
            "low": (0.7, 1.0),
            "optimal": (1.1, 4.4),
            "high": (4.5, 6.0),
            "very_high": (6.1, None)
        }
        },

        "Estradiol": {
            "female": {
                "follicular": (10, 180),
                "mid_cycle": (100, 300),
                "luteal": (40, 200),
                "postmeno": (None, 10),
                "critical":(400,None)
            },
            "male": {
                "severe":(None,10),
                "very_low":(11,23),
                "optimal": (24, 39),
                "critical":(40,None)}
        },

        # ---------------- Insulin / glucose control --------------------- #
        "Fasting Insulin": {
            "low": (None, 1.9),
            "optimal": (1.9, 8),
            "functional": (3, 5),  # tighter preventive window
            "high": (8, 23),
            "very_high": (23, None)
        },

        "HbA1c": {
            "optimal": (4, 5),
            "normal": (5.1, 5.6),
            "prediabetes": (5.7, 6.4),
            "diabetes": (6.5, 8.9),
            "critical": (9.0, None)
        },

        "Fasting Glucose": {
            "optimal": (None, 90),
            "prediabetes": (90, 125),
            "diabetes": (126, None)
        },

        "HOMA-IR": {
            "insulin_sensitive": (None, 1.0),
            "borderline": (1.5, 2.9),
            "insulin_resistant": (2.9, None)
        },

        # ---------------- Iron & storage -------------------------------- #
        "Ferritin": {
            "male": {"optimal": (12, 300), "functional": (40, 80)},
            "female": {"normal": (12, 150), "functional": (40, 80)}
        },

        "Iron": {"male": {
            "optimal": (60, 120),
            "very_high":(120, None)
        },
        "female": {
            "optimal": (45, 80)
        }},
        "Iron Saturation": {
            "very_low": (None, 15),
            "low": (15, 21),
            "normal": (22, 55),
            "high": (56, 70),
            "very_high": (71, None)
        },

        # ---------------- Pituitary / reproductive ---------------------- #
        "FSH": {
            "female": {
                "follicular": (2, 9),
                "mid_cycle": (4, 22),
                "luteal": (2, 9),
                "postmeno": (30, None)
            },
            "male": {"normal": (1, 7)}
        },

        "Testosterone, Total (Males)": {
            "age_20_49": (3.0, 10.8),  # ng/mL
            "age_40_60": (3.0, 8.9),
            "age_60_plus": (3.0, 7.2),
            "hrt_optimal": (700, 1000)  # convert units if necessary
        },

        "Testosterone, Total (Females)": {
            "hrt_optimal": (35, 45)  # ng/dL equivalent
        },

        "Free Testosterone": {
            "male": {"normal": (0.047, 0.244)}  # ng/mL
        },

        # ---------------- Thyroid --------------------------------------- #
        "TSH": {
            "very_low": (None, 0.5),
            "low": (0.5, 1),
            "optimal": (1, 2.5),
            "high": (2.5, 5),
            "very_high": (5, None)
        },

        # ---------------- Lipid profile -------------------------------- #
        "HDL Cholesterol": {
            "male":{
            "very_low": (None, 23),
            "low": (24, 40),
            "excellent": (41, 80),
            "high": (81, 100),
            "very_high": (101, None)},
            "female":{
            "very_low": (None, 23),
            "low": (24, 49),
            "excellent": (50, 80),
            "high": (81, 100),
            "very_high": (101, None)}
        },

        "LDL Cholesterol": {
            "optimal": (40, 100),
            "borderline": (101, 130),
            "high": (131, 160),
            "very_high": (161, 190),
            "critical": (191, None)
        },

        "Calculated Total Cholesterol": {
            "very_low": (None, 125),
            "low": (125, 160),
            "optimal": (160, 200),
            "high": (200, 240),
            "critical": (240, None)
        },
        "LDL:HDL Ratio (Calc.)":{
            "optimal": (None, 2),
            "very_high": (2, None)
        },

        "Total Cholesterol:HDL Ratio": {
            "optimal": (None, 3.5),
            "low_risk": (3.6, 4.5),
            "high": (4.5, 6),
            "very_high": (6, None)
        },

        "Triglycerides": {
            "low": (None, 69),
            "optimal": (70, 100),
            "normal": (100, 150),
            "borderline_high": (150, 199),
            "high": (200, 499),
            "very_high": (500, None)
        },

        "Triglyceride:HDL Ratio": {
            "desirable": (None, 1.0),
            "high": (1.0, 3.5),
            "very_high": (3.5, None)
        },

        "Lp(a)": {
            "optimal": (None, 14),
            "borderline": (14, 30),
            "very_high": (31, 50),
            "critical": (50, None)
        },

        # --------- Inflammation & cardiovascular risk markers ---------- #
        "High-Sensitivity CRP": {
            "optimal": (None, 1.0),
            "borderline": (1.0, 1.5),
            "high": (1.5, 10),
            "very_high": (10, 50),
            "critical": (50, None)
        },

        "Homocysteine": {
            "low": (None, 3),
            "optimal": (4, 8),
            "normal": (9, 15),
            "high": (16, 30),
            "very_high": (31, 100),
            "critical": (100, None)
        },

        # ---------------- Vitamin / mineral status --------------------- #
        "25-(OH) Vitamin D": {
            "very_low": (None, 25),
            "low": (25, 40),
            "sufficient": (40, 70),
            "optimal": (80,None)
        },

        "Vitamin B12": {
            "very_low": (None, 200),
            "low": (200, 400),
            "normal": (400, 749),
            "optimal": (750, 1000),
            "high": (1001, 1500),
            "very_high": (1501, None)
        },
        "Folate": {
            "very_low": (None, 5),
            "low": (5, 10),
            "normal": (10, 19),
            "optimal": (20, None)
        },
        "Magnesium RBC": {
            "very_low": (None, 4.0),
            "low": (4.0, 5.4),
            "optimal": (5.5, 6.5),
            "high": (6.6, 7.5),
            "very_high": (7.6, None)
        },

        # ---------------- Basic metabolic panel ------------------------ #
        "Albumin": {
            "very_low": (None, 3.0),
            "low": (3.0, 3.8),
            "optimal": (3.9, 4.9),
            "high": (5.0, 5.5),
            "very_high": (5.6, None)
        },
        "Blood Urea Nitrogen": {"optimal": (8, 20), "lab_range": (21, 25)},
        "Creatinine": {
            "male": {"normal": (None, 0.69), "optimal": (0.70, 1.30)},
            "female": {"optimal": (None, 0.49), "optimal": (0.50, 1.10)}
        },
        "eGFR": {
            "severe": (None, 15),
            "very_low": (15, 29),
            "low": (30, 44),
            "normal": (45, 59),
            "optimal": (60, 120),
            "high": (121, None)
        },
        "Total Protein": {
            "very_low": (None, 5.5),
            "low": (5.5, 6.8),
            "optimal": (6.9, 7.4),
            "high": (7.5, 8.5),
            "very_high": (8.6, None)
        },
        "Sodium": {
            "very_low": (None, 130),
            "low": (130, 139),
            "optimal": (140, 145),
            "high": (146, 150),
            "very_high": (151, None)
        },
        "Potassium": {
            "very_low": (None, 3.0),
            "low": (3.0, 3.9),
            "optimal": (4.0, 5.0),
            "high": (5.1, 6.0),
            "very_high": (6.1, None)
        },
        "CO2": {
            "very_low": (None, 18),
            "low": (18, 24),
            "optimal": (25, 25),
            "high": (26, 32),
            "very_high": (33, None)
        },
        "Calcium": {
            "very_low": (None, 7.5),
            "low": (7.5, 8.7),
            "optimal": (8.8, 9.5),
            "high": (9.6, 10.5),
            "very_high": (10.6, None)
        },
        "Alanine Aminotransferase": {"optimal": (None, 30), "lab": (31, 39), "critical":(40,None)},  # ALT
        "Aspartate Aminotransferase": {"optimal": (None, 30), "lab": (31, 39), "critical":(40,None)},  # AST
        "GGT": {"optimal": (None, 15)},
        "SBHG": {
            "male":{
                "very_low": (None, 10),
                "low": (10, 19),
                "optimal": (20, 30),
                "high": (31, 50),
                "very_high": (51, None)
            },
            "female":{
                "very_low": (None, 10),
                "low": (10, 19),
                "optimal": (20, 30),
                "high": (31, 50),
                "very_high": (51, None)
            }
        },
        "Bilirubin": {
            "normal": (0.3, 1.0),
            "critical": (2.5, None)
        },
        "Testosterone:Cortisol Ratio": {
        "male": {
            "optimal": (0.05, 30)
        },
        "female": {
            "optimal": (0.015, 0.03)
        }
        },

        # ---------------- Complete blood count ------------------------- #
        "WBC": {
            "very_low": (None, 3.0),
            "low": (3.0, 4.9),
            "optimal": (5, 7),
            "high": (7.1, 10),
            "very_high": (10.1, None)
        },
        "RBC": {
            "very_low": (None, 3.0),
            "low": (3.0, 3.9),
            "optimal": (4, 5),
            "high": (5.1, 6.0),
            "very_high": (6.1, None)
        },
        "Hemoglobin": {
            "very_low": (None, 10),
            "low": (10, 12),
            "optimal": (13, 15),
            "high": (16, 18),
            "very_high": (19, None)
        },
        "Hematocrit": {
            "very_low": (None, 30),
            "low": (30, 39),
            "optimal": (40, 45),
            "high": (46, 55),
            "very_high": (56, None)
        },
        "MCV": {
            "very_low": (None, 75),
            "low": (75, 89),
            "optimal": (90, 90),
            "high": (91, 105),
            "very_high": (106, None)
        },
        "MCH": {
            "very_low": (None, 25),
            "low": (25, 29),
            "optimal": (30, 30),
            "high": (31, 35),
            "very_high": (36, None)
        },
        "MCHC": {
            "very_low": (None, 28),
            "low": (28, 31),
            "optimal": (32, 32),
            "high": (33, 36),
            "very_high": (37, None)
        },
        "RDW": {
            "very_low": (None, 10),
            "low": (10, 12.2),
            "optimal": (12.3, 14.5),
            "high": (14.6, 17),
            "very_high": (17.1, None)
        },
        "Platelets": {
            "very_low": (None, 50),
            "low": (50, 74),
            "optimal": (75, 250),
            "high": (251, 400),
            "very_high": (401, None)
        },
        "Neutro:Lymph Ratio": {
            "very_low": (None, 1.0),
            "low": (1.0, 1.9),
            "optimal": (2, 2),
            "high": (2.1, 4.0),
            "very_high": (4.1, None)
        },
        "Monocytes %": {"optimal": (None, 7)},
        "Eosinophils %": {"optimal": (None, 2)},
        "Basophils %": {"optimal": (0, 0)},
        "VLDL (Calculated)": {
        "male": {
            "optimal": (0, 15),
            "high": (16, 25),
            "very_high": (26, None)
        },
        "female": {
            "optimal": (0, 15),
            "high": (16, 25),
            "very_high": (26, None)
        }}

    }

    units: ClassVar[Dict[str, str]] = {
        
        # ... (your entire existing units dictionary remains the same)
        "Testosterone, Total (Males)": "ng/mL",
        "Ferritin": "ng/mL",
        "25-(OH) Vitamin D": "ng/mL",
        
        "Alanine Aminotransferase": "U/L",  # ALT
        "Aspartate Aminotransferase": "U/L",  # AST
        "Alkaline Phosphatase (ALP)": "IU/L",
        "Bilirubin": "mg/dL",
        "GGT": "U/L",
        
        "Albumin": "g/dL",
        "Blood Urea Nitrogen": "mg/dL",
        "Calcium": "mg/dL",
        "Creatinine": "mg/dL",
        "eGFR": "mL/min/1.73m²",
        "Total Protein": "g/dL",
        "Sodium": "mmol/L",
        "Potassium": "mmol/L",
        "CO2": "mmol/L",
        
        "Apolipoprotein A1 (APOA1)": "mg/dL",
        "Apolipoprotein B (APOB)": "mg/dL",
        "ApoB:ApoA1 Ratio": "ratio",
        "HDL Cholesterol": "mg/dL",
        "LDL Cholesterol": "mg/dL",
        "LDL:HDL Ratio (Calc.)": "ratio",
        "Calculated Total Cholesterol": "mg/dL",
        "Total Cholesterol:HDL Ratio": "ratio",
        "Triglycerides": "mg/dL",
        "Triglyceride:HDL Ratio": "ratio",
        "Lp(a)": "mg/dL",
        "VLDL (Calculated)": "mg/dL",
        
        "Cortisol": "mcg/dL",
        "Dehydroepiandrosterone Sulfate (DHEA-S)": "mcg/dL",
        "SBHG": "nmol/L",  # SHBG
        "Testosterone:Cortisol Ratio": "ratio",
        
        "Estradiol": "pg/mL",
        "Testosterone, Total (Females)": "ng/dL",
        "Free Testosterone": "ng/mL",
        "FSH": "mIU/mL",
        "LH": "mIU/mL",
        
        "TSH": "uIU/mL",
        
        
        "EAG (Calc.)": "mg/dL",
        "C-peptide": "ng/mL",
        "Fasting Insulin": "uIU/mL",
        "HbA1c": "%",
        "Fasting Glucose": "mg/dL",
        "HOMA-IR": "index",
        
        
        "Iron": "mcg/dL",
        "Iron Saturation": "%",
        "Unsaturated Iron Binding Capacity (UIBC)": "mcg/dL",
        
        
        "High-Sensitivity CRP": "mg/L",
        "Homocysteine": "umol/L",
        
        
        "Vitamin B12": "pg/mL",
        "Folate": "ng/mL",
        "Magnesium RBC": "mg/dL",
        
        
        "WBC": "K/uL",
        "RBC": "M/uL",
        "Hemoglobin": "g/dL",
        "Hematocrit": "%",
        "MCV": "fL",
        "MCH": "pg",
        "MCHC": "g/dL",
        "RDW": "%",
        "Platelets": "K/uL",
        "Neutro:Lymph Ratio": "ratio",
        "Monocytes %": "%",
        "Eosinophils %": "%",
        "Basophils %": "%"
    }

    def _extract_numeric_value(self, value_str: str) -> float:
        """
        Extract numeric value from strings like "190.98 mg/dL"
        """
        if isinstance(value_str, (int, float)):
            return float(value_str)
        
        # Remove non-numeric characters except decimal points and negative signs
        numeric_match = re.search(r'[-+]?\d*\.?\d+', str(value_str))
        if numeric_match:
            return float(numeric_match.group())
        else:
            raise ValueError(f"Cannot extract numeric value from: {value_str}")

    def _categorize_marker_direction(self, category: str, severity: int) -> str:
        """
        Categorize biomarker as healthy, low, or high based on category name and severity
        """
        # Severity 0-1 are always healthy
        if severity <= 1:
            return "healthy"
        
        # Define keyword mappings for low and high categories
        low_keywords = {"low", "very_low", "severe", "deficiency", "insufficient"}
        high_keywords = {"high", "very_high", "critical", "excess", "elevated"}
        
        # Special cases that imply direction
        special_cases = {
            "prediabetes": "high",
            "diabetes": "high", 
            "insulin_resistant": "high",
            "insulin_sensitive": "healthy"  # This is actually good
        }
        
        # Check special cases first
        if category in special_cases:
            return special_cases[category]
        
        # Check for low keywords
        if any(keyword in category.lower() for keyword in low_keywords):
            return "low"
        
        # Check for high keywords
        if any(keyword in category.lower() for keyword in high_keywords):
            return "high"
        
        # Default to healthy for anything else
        return "healthy"
    
    def _extract_biomarkers_from_blood_report(self, blood_report_data: dict) -> Dict[str, float]:
        """
        Extract biomarkers from the new blood report format
        """
        biomarkers_dict = {}
        
        # Skip metadata fields
        metadata_fields = ["Kit Type", "Total Biomarkers", "Order ID", "Test Date", "Gender"]
        
        for key, value in blood_report_data.items():
            if key in metadata_fields:
                continue
                
            if value is not None and value != "":
                try:
                    numeric_value = self._extract_numeric_value(value)
                    biomarkers_dict[key] = numeric_value
                except (ValueError, TypeError) as e:
                    print(f"Warning: Could not parse biomarker {key}: {value} - {e}")
                    continue
        
        return biomarkers_dict

    def _extract_patient_demographics(self, patient_form: dict) -> Dict[str, Any]:
        """
        Extract age and sex from patient form
        """
        demographics = patient_form["patient_data"]["phase1_basic_intake"]["demographics"]
        #demographics = patient_form["phase1_basic_intake"]["demographics"]
        
        return {
            "age": demographics["age"],
            "sex_assigned_at_birth": demographics["biological_sex"]
        }
    '''
    def _run(self, patient_and_blood_data: str) -> str:
        """
        Main entry point that accepts your format
        """
        try:
            print("=== DEBUG: Raw input received by tool ===")
            print(f"Input type: {type(patient_and_blood_data)}")
            print(f"Input content: {patient_and_blood_data[:500]}...")  # First 500 chars
            print("=== END DEBUG ===")
            
            data = json.loads(patient_and_blood_data)
            
            # More debugging
            print("=== DEBUG: Parsed JSON structure ===")
            print(f"Top level keys: {list(data.keys())}")
            print("=== END DEBUG ===")
            
            # Rest of your code...
            
        except Exception as e:
            print(f"=== DEBUG: JSON parsing failed: {e} ===")
            return json.dumps({
                "error": f"Tool execution failed: {str(e)}",
                "biomarkers": {},
                "flagged_biomarkers": []
            }, indent=2)
        '''
    def _normalize_biomarker_names(self, biomarkers_dict: Dict[str, float]) -> Dict[str, float]:
        """
        Map blood report biomarker names to the tool's expected names
        """
        name_mapping = {
            "Apolipoprotein A1 (APOA1)": "Apolipoprotein A1 (APOA1)",
            "Apolipoprotein B (APOB)": "Apolipoprotein B (APOB)",
            "Dehydroepiandrosterone Sulfate (DHEA-S)": "Dehydroepiandrosterone Sulfate (DHEA-S)",
            "HDL Cholesterol": "HDL Cholesterol",
            "% Hemoglobin A1C": "HbA1c",
            "High-Sensitivity CRP": "High-Sensitivity CRP",
            "Iron": "Iron",
            "Calcium": "Calcium",
            "C-Peptide": "C-peptide",
            "LDL Cholesterol": "LDL Cholesterol",
            "Testosterone, Total (Males)": "Testosterone, Total (Males)",
            "Testosterone, Free (calc)": "Free Testosterone",
            "Ferritin": "Ferritin",
            "Triglycerides": "Triglycerides",
            "Triglycerides:HDL Ratio": "Triglyceride:HDL Ratio",
            "Total Cholesterol": "Calculated Total Cholesterol",
            "25-(OH) Vitamin D": "25-(OH) Vitamin D",
            "Total Cholesterol:HDL Ratio": "Total Cholesterol:HDL Ratio",
            "Thyroid Stimulating Hormone (TSH)": "TSH",
            "Total Protein": "Total Protein",
            "Unsaturated iron-binding capacity test (UIBC)": "Unsaturated Iron Binding Capacity (UIBC)",
            "Sex Hormone-Binding Globulin (SHBG)": "SBHG",
            "Albumin": "Albumin",
            "Alanine Aminotransferase (ALT)": "Alanine Aminotransferase",
            "Aspartate Aminotransferase (AST)": "Aspartate Aminotransferase",
            "eGFR": "eGFR",
            "Creatinine": "Creatinine",
            "Lipoprotein (a)": "Lp(a)",
            "Blood Urea Nitrogen (BUN)": "Blood Urea Nitrogen",
            "Total Bilirubin": "Bilirubin",
            "Direct Bilirubin": "Bilirubin",  # Map to same as total bilirubin for now
            "BUN:Creatinine Ratio": "BUN:Creatinine Ratio",
            "% Free Testosterone": "Free Testosterone",  # Map to free testosterone
            "Estim. Avg Glu (eAG)": "EAG (Calc.)",
            "LDL-C:HDL-C Ratio": "LDL:HDL Ratio (Calc.)",
            "Calculated Cholesterol, Total": "Calculated Total Cholesterol",
            "ApoB:ApoA1 Ratio": "ApoB:ApoA1 Ratio",
            "VLDL Cholesterol (Calc)": "VLDL (Calculated)",
            "AST:ALT Ratio": "AST:ALT Ratio",
            "LDL-C:ApoB Ratio": "LDL-C:ApoB Ratio"
        }
        
        normalized = {}
        for name, value in biomarkers_dict.items():
            normalized_name = name_mapping.get(name)
            if normalized_name:
                normalized[normalized_name] = value
            else:
                # If no mapping found, use original name
                normalized[name] = value
                print(f"Warning: No mapping found for biomarker: {name}")
        
        return normalized

    def _select_age_bracket(self, marker: str, age: int, ranges: dict) -> dict:
        if marker == "Testosterone, Total (Males)":
            if age < 50:
                return {"optimal": ranges["age_20_49"]}
            elif age < 60:
                return {"optimal": ranges["age_40_60"]}
            else:
                return {"optimal": ranges["age_60_plus"]}
        return ranges

    def _classify_value(self, value: float, ranges: dict) -> Any:
        for label, bounds in ranges.items():
            if not isinstance(bounds, tuple):
                continue
            lo, hi = bounds
            if (lo is None or value >= lo) and (hi is None or value <= hi):
                return label, self.SEVERITY_ORDER[label], bounds
        return "unclassified", 1, (None, None)

    def evaluate_biomarkers(self, demographics: dict, biomarkers_dict: dict) -> dict:
        """
        Core evaluation logic (same as your original)
        """
        sex = demographics.get("sex_assigned_at_birth", "").lower()
        age = demographics.get("age")
        
        biomarkers_out = {}
        flagged_summary = []

        for name, value in biomarkers_dict.items():
            spec = self.biomarker_ranges.get(name)
            if not spec:
                biomarkers_out[name] = {
                    "value": value,
                    "unit": self.units.get(name, "unknown"),
                    "status": "no_reference_data",
                    "category": "unknown",
                    "severity": 1,
                    "flagged": False
                }
                continue

            use_ranges = spec.get(sex, spec)
            if isinstance(use_ranges, dict):
                use_ranges = self._select_age_bracket(name, age, use_ranges)

            category, sev, rng = self._classify_value(value, use_ranges)
            flagged = sev >= 2

            biomarkers_out[name] = {
                "value": value,
                "unit": self.units.get(name, "unknown"),
                "category": category,
                "range_used": list(rng),
                "severity": sev,
                "flagged": flagged
            }

            if flagged:
                flagged_summary.append({
                    "name": name,
                    "value": value,
                    "unit": self.units.get(name, "unknown"),
                    "category": category,
                    "range_used": list(rng),
                    "severity": sev
                })

        # Calculate category counts
        category_counts = {"healthy_markers": 0, "low_markers": 0, "high_markers": 0}

        for biomarker_data in biomarkers_out.values():
            direction = self._categorize_marker_direction(
                biomarker_data["category"], 
                biomarker_data["severity"]
            )
            category_counts[f"{direction}_markers"] += 1

        return {
            
            "flagged_biomarkers": flagged_summary,
            "summary": {
                "total_biomarkers_evaluated": len(biomarkers_dict),
                "total_flagged": len(flagged_summary),
                "high_priority_issues": len([b for b in flagged_summary if b["severity"] >= 3]),
                "category_summary": category_counts  # NEW: Add the category counts
            }
        }

    def _run(self, patient_and_blood_data: Union[str, dict]) -> str:
        """
        Main entry point that accepts either a JSON string or a dict.
        """
        try:
            # If dict is passed, use it directly
            if isinstance(patient_and_blood_data, str):
                patient_and_blood_data = json.loads(patient_and_blood_data)

            # 🔹 FIX: unwrap correctly
            data = patient_and_blood_data

            # Extract from your format
            patient_form = data["patient_form"]
            blood_report = data["blood_report"]

            # Process the data
            demographics = self._extract_patient_demographics(patient_form)
            biomarkers_dict = self._extract_biomarkers_from_blood_report(blood_report)
            normalized_biomarkers = self._normalize_biomarker_names(biomarkers_dict)

            # Run evaluation
            evaluated = self.evaluate_biomarkers(demographics, normalized_biomarkers)

            return json.dumps(evaluated, indent=2)

        except Exception as e:
            return json.dumps({
                "error": f"Tool execution failed: {str(e)}",
                "biomarkers": {},
                "flagged_biomarkers": []
            }, indent=2)
