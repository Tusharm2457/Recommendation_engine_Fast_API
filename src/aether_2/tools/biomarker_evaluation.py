from crewai.tools import BaseTool
from typing import Type, ClassVar, Dict, Any, Union
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

    # Simplified SEVERITY_ORDER with only three categories
    SEVERITY_ORDER: ClassVar[Dict[str, int]] = {
        # ───────── 0  —  Optimal / Ideal ───────── #
        "optimal": 0,
        
        # physiologic female hormone phases - these will be handled specially
        "follicular": 0,
        "mid_cycle": 0,
        "luteal": 0,
        "postmeno": 0,
        # age brackets (handled internally but mapped here for completeness)
        "age_20_49": 0,
        "age_40_60": 0,
        "age_60_plus": 0,

        # ───────── 1  —  Low / High (flagged) ─── #
        "low": 1,
        "high": 1,
        
    }

    biomarker_ranges: ClassVar[Dict[str, Dict[str, Any]]] = {
        # ... (your entire existing biomarker_ranges dictionary remains the same)
        "Apolipoprotein A1 (APOA1)": {
        "male": {
            "low": (None, 115),
            "optimal": (115, None)
        },
        "female": {
            "low": (None, 125),
            "optimal": (125, None)
        }
        },

        "Apolipoprotein B (APOB)": {
            "male":{
            "low": (None, 66),
            "optimal": (66, 133),
            "high": (134, None)
            },
            "female": {
            "low": (None, 60),
            "optimal": (60, 117),
            "high": (134, None)
        }
        },

        "Alkaline Phosphatase (ALP)": {
            "male": {
                "low": (None, 40),
                "optimal": (40, 116),
                "high": (117, None)
            },
            "female": {
                "low": (None, 35),
                "optimal": (35, 104),
                "high": (105, None)
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
            "low": (None, 14),
            "optimal": (14, 17),
            "high": (17, None)
        },
        "Dehydroepiandrosterone Sulfate (DHEA-S)": {
            "male": {
            "low": (None, 150),
            "optimal": (150, 250),
            "high": (250, None)
            },
            "female": {
            "low": (None, 150),
            "optimal": (150, 200),
            "high": (200, None)
            }
        },
        "EAG (Calc.)":{
            "low": (None, 85),
            "optimal": (85, 107),
            "high": (107, None)
        },
        "C-peptide": {
        "male": {
            "low": (None, 1.1),
            "optimal": (1.1, 4.4),
            "high": (4.4, None)
        },
        "female": {
            "low": (None, 1.1),
            "optimal": (1.1, 4.4),
            "high": (4.4, None)
        }
        },

        "Estradiol": {
            "female": {
                "low": (None, 10),
                "optimal": (10, 400),
                "high": (400, None)
            },
            "male": {
                "low": (None, 24),
                "optimal": (24, 39),
                "high": (40, None)
            }
        },

        # ---------------- Insulin / glucose control --------------------- #
        "Fasting Insulin": {
            "low": (None, 1.9),
            "optimal": (1.9, 8),
            "high": (8, None)
        },

        "HbA1c": {
            "low": (None, 4),
            "optimal": (4, 5),
            "high": (5, None)
        },

        "Fasting Glucose": {
            
            "optimal": (None, 120),
            "high": (120, None)
        },

        "HOMA-IR": {
            
            "optimal": (None, 1.0),
            "high": (1.0, None)
        },

        # ---------------- Iron & storage -------------------------------- #
        "Ferritin": {
            "male": {"low": (None, 12), "optimal": (12, 300), "high": (300, None)},
            "female": { "low": (None, 12), "optimal": (12, 150), "high": (150, None)}
        },

        "Iron": {"male": {
            "low": (None, 60),
            "optimal": (60, 120),
            "high": (120, None)
        },
        "female": {
            "low": (None, 45),
            "optimal": (45, 80),
            "high": (80, None)
        }},
        "Iron Saturation": {
            "low": (None, 22),
            "optimal": (22, 56),
            "high": (56, None)
        },

        "Unsaturated Iron Binding Capacity (UIBC)": {
            "male": {
                "low": (None, 100),
                "optimal": (100, 300),
                "high": (300, None)
            },
            "female": {
                "low": (None, 100),
                "optimal": (100, 300),
                "high": (300, None)
            }
        },

        # ---------------- Pituitary / reproductive ---------------------- #
        "FSH": {
            "female": {
                "low": (None, 2),
                "optimal": (2, 22),
                "high": (22, None)
            },
            "male": {"low": (None, 1), "optimal": (1, 7), "high": (7, None)}
        },

        "LH": {
            "female": {
                "low": (None, 1.0),
                "optimal": (1.0, 11.4),
                "high": (11.4, None)
            },
            "male": {"low": (None, 1.7), "optimal": (1.7, 8.6), "high": (8.6, None)}
        },

        "Testosterone, Total (Males)": {
            "age_20_49": (3.0, 10.8),  # ng/mL
            "age_40_60": (3.0, 8.9),
            "age_60_plus": (3.0, 7.2),
            "hrt_optimal": (700, 1000)  # convert units if necessary
        },

        "Testosterone, Total (Females)": {
            "low": (None, 35),
            "optimal": (35, 45),
            "high": (45, None)
        },

        "Free Testosterone": {
            "male": {"low": (None, 0.047), "optimal": (0.047, 0.244), "high": (0.244, None)}  # ng/mL
        },

        # ---------------- Thyroid --------------------------------------- #
        "TSH": {
            "low": (None, 1),
            "optimal": (1, 2.5),
            "high": (2.5, None)
        },

        # ---------------- Lipid profile -------------------------------- #
        "HDL Cholesterol": {
            "male":{
            "low": (None, 40),
            "optimal": (40, 80),
            "high": (80, None)},
            "female":{
            "low": (None, 49),
            "optimal": (50, 80),
            "high": (80, None)}
        },

        "LDL Cholesterol": {
            "low": (None, 39),
            "optimal": (40, 100),
            "high": (100, None)
        },

        "Calculated Total Cholesterol": {
            "low": (None, 160),
            "optimal": (160, 200),
            "high": (200, None)
        },
        "LDL:HDL Ratio (Calc.)":{
            
            "optimal": (None, 2),
            "high": (2, None)
        },

        "Total Cholesterol:HDL Ratio": {
            
            "optimal": (None,3.5),
            "high": (3.5, None)
        },

        "Triglycerides": {
            "low": (None, 70),
            "optimal": (70, 100),
            "high": (100, None)
        },

        "Triglyceride:HDL Ratio": {
            
            "optimal": (None, 1.0),
            "high": (1.0, None)
        },

        "Lp(a)": {
            
            "optimal": (None,14),
            "high": (15, None)
        },

        # --------- Inflammation & cardiovascular risk markers ---------- #
        "High-Sensitivity CRP": {
            "low": (None, 1.0),
            "optimal": (1.0, 1.5),
            "high": (1.5, None)
        },

        "Homocysteine": {
            "low": (None, 4),
            "optimal": (4, 9),
            "high": (9, None)
        },

        # ---------------- Vitamin / mineral status --------------------- #
        "25-(OH) Vitamin D": {
            "low": (None, 40),
            "optimal": ( 80,None),
            
        },

        "Vitamin B12": {
            "low": (None, 400),
            "optimal": (400, 1000),
            "high": (1000, None)
        },
        "Folate": {
            "low": (None, 10),
            "optimal": (10, 20),
            "high": (20, None)
        },
        "Magnesium RBC": {
            "low": (None, 5.5),
            "optimal": (5.5, 6.6),
            "high": (6.6, None)
        },

        # ---------------- Basic metabolic panel ------------------------ #
        "Albumin": {
            "low": (None, 3.9),
            "optimal": (3.9, 5.0),
            "high": (5.0, None)
        },
        "Blood Urea Nitrogen": {"low": (None, 8), "optimal": (8, 21), "high": (21, None)},
        "Creatinine": {
            "male": {"low": (None, 0.70), "optimal": (0.70, 1.30), "high": (1.30, None)},
            "female": {"low": (None, 0.50), "optimal": (0.50, 1.10), "high": (1.10, None)}
        },
        "eGFR": {
            "low": (None, 60),
            "optimal": (60, 120),
            "high": (120, None)
        },
        "Total Protein": {
            "low": (None, 6.9),
            "optimal": (6.9, 7.4),
            "high": (7.4, None)
        },
        "Sodium": {
            "low": (None, 140),
            "optimal": (140, 146),
            "high": (146, None)
        },
        "Potassium": {
            "low": (None, 4.0),
            "optimal": (4.0, 5.1),
            "high": (5.1, None)
        },
        "CO2": {
            "low": (None, 25),
            "optimal": (25, 26),
            "high": (26, None)
        },
        "Calcium": {
            "low": (None, 8.8),
            "optimal": (8.8, 9.6),
            "high": (9.6, None)
        },
        "Alanine Aminotransferase": { "optimal": (None, 40), "high": (40, None)},  # ALT
        "Aspartate Aminotransferase": { "optimal": (None, 40), "high": (40, None)},  # AST
        "GGT": { "optimal": (None, 15), "high": (15, None)},
        "SBHG": {
            "male":{
                "low": (None, 20),
                "optimal": (20, 30),
                "high": (30, None)
            },
            "female":{
                "low": (None, 40),
                "optimal": (40, 90),
                "high": (90, None)
            }
        },
        "Bilirubin": {
            "low": (None, 0.3),
            "optimal": (0.3, 2.5),
            "high": (2.5, None)
        },
        "Testosterone:Cortisol Ratio": {
        "male": {
            "optimal": (0.05, None)
        },
        "female": {
            "optimal": (0.015, 0.03)
        }
        },

        # ---------------- Complete blood count ------------------------- #
        "WBC": {
            "low": (None, 5),
            "optimal": (5, 7.1),
            "high": (7.1, None)
        },
        "RBC": {
            "low": (None, 4),
            "optimal": (4, 5.1),
            "high": (5.1, None)
        },
        "Hemoglobin": {
            "low": (None, 13),
            "optimal": (13, 16),
            "high": (16, None)
        },
        "Hematocrit": {
            "low": (None, 40),
            "optimal": (40, 46),
            "high": (46, None)
        },
        "MCV": {
            "low": (None, 90),
            "optimal": (90, 91),
            "high": (91, None)
        },
        "MCH": {
            "low": (None, 30),
            "optimal": (30, 31),
            "high": (31, None)
        },
        "MCHC": {
            "low": (None, 32),
            "optimal": (32, 33),
            "high": (33, None)
        },
        "RDW": {
            "low": (None, 12.3),
            "optimal": (12.3, 14.6),
            "high": (14.6, None)
        },
        "Platelets": {
            "low": (None, 75),
            "optimal": (75, 251),
            "high": (251, None)
        },
        "Neutro:Lymph Ratio": {
            "low": (None, 2),
            "optimal": (2, 2.1),
            "high": (2.1, None)
        },
        "Monocytes %": { "optimal": (None, 7), "high": (7, None)},
        "Eosinophils %": { "optimal": (None, 2), "high": (2, None)},
        "Basophils %": {  "optimal": (0, 0), "high": (0, None)},
        "VLDL (Calculated)": {
        "male": {
            "low": (None, 0),
            "optimal": (0, 15),
            "high": (15, None)
        },
        "female": {
            "low": (None, 0),
            "optimal": (0, 15),
            "high": (15, None)
        }},

        
        "BUN:Creatinine Ratio": {
            "low": (None, 10),
            "optimal": (10, 20),
            "high": (20, None)
        },

        "AST:ALT Ratio": {
            "low": (None, 1.0),
            "optimal": (1.0, 2.0),
            "high": (2.0, None)
            
        },

        "LDL-C:ApoB Ratio": {
            "low": (None, 10),
            "optimal": (10, 20),
            "high": (20, None)
        }

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
        # Severity 0 is optimal/healthy
        if severity == 0:
            return "healthy"
        
        # Severity 1 is flagged (low or high)
        if severity == 1:
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
                    "flagged": False
                }
                continue

            use_ranges = spec.get(sex, spec)
            if isinstance(use_ranges, dict):
                use_ranges = self._select_age_bracket(name, age, use_ranges)

            category, sev, rng = self._classify_value(value, use_ranges)
            flagged = sev >= 1

            biomarkers_out[name] = {
                "value": value,
                "unit": self.units.get(name, "unknown"),
                "category": category,
                "flagged": flagged
            }

            if flagged:
                flagged_summary.append({
                    "name": name,
                    "value": value,
                    "unit": self.units.get(name, "unknown"),
                    "category": category
                })

        # Calculate category counts
        category_counts = {"healthy_markers": 0, "low_markers": 0, "high_markers": 0}

        for biomarker_data in biomarkers_out.values():
            direction = self._categorize_marker_direction(
                biomarker_data["category"], 
                0 if biomarker_data["category"] in ["optimal", "normal", "healthy", "sufficient", "excellent", "very_good", "desirable", "insulin_sensitive", "hrt_optimal", "functional", "lab", "lab_range", "low_risk", "borderline", "follicular", "mid_cycle", "luteal", "postmeno", "age_20_49", "age_40_60", "age_60_plus"] else 1
            )
            category_counts[f"{direction}_markers"] += 1

        return {
            
            "flagged_biomarkers": flagged_summary,
            "summary": {
                "total_biomarkers_evaluated": len(biomarkers_dict),
                "total_flagged": len(flagged_summary),
                "high_priority_issues": len(flagged_summary),
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
