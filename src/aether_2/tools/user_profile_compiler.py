from crewai.tools import BaseTool
from typing import Type, Union
from pydantic import BaseModel, Field
import json


class UserProfileCompilerInput(BaseModel):
    patient_and_blood_data: Union[str, dict] = Field(
        ..., description="JSON string OR dict containing patient details from patient_details.json"
    )
    flagged_biomarkers: Union[str, dict] = Field(
        ..., description="JSON string OR dict containing flagged biomarkers from biomarker evaluation"
    )


class UserProfileCompilerTool(BaseTool):
    name: str = "compile_user_profile"
    description: str = (
        "Combines patient data and flagged biomarkers into a single JSON structure without any transformation."
    )
    args_schema: Type[BaseModel] = UserProfileCompilerInput

    def _run(self, patient_and_blood_data: Union[str, dict], flagged_biomarkers: Union[str, dict]) -> str:
        """Simple JSON combiner - no transformation, just merge the two structures."""
        try:
            # Parse inputs
            if isinstance(patient_and_blood_data, str):
                patient_data_parsed = json.loads(patient_and_blood_data)
            else:
                patient_data_parsed = patient_and_blood_data
                
            if isinstance(flagged_biomarkers, str):
                flagged_biomarkers_parsed = json.loads(flagged_biomarkers)
            else:
                flagged_biomarkers_parsed = flagged_biomarkers
            
            # DEBUG: Print variables to see what we're working with
            print(f"🔍 DEBUG - patient_data_parsed keys: {list(patient_data_parsed.keys()) if isinstance(patient_data_parsed, dict) else 'Not a dict'}")
            print(f"🔍 DEBUG - patient_data_parsed: {patient_data_parsed}")
            
            # Extract only patient_data from the combined input, exclude blood_report
            patient_data_only = patient_data_parsed.get("patient_form", {})
            patient_data_subset = patient_data_only.get("patient_data", {})
            
            print(f"🔍 DEBUG - patient_data_only: {patient_data_subset}")
            
            # Simple combination - no transformation
            combined_profile = {
                "patient_data": patient_data_subset,
                "flagged_biomarkers": flagged_biomarkers_parsed.get("flagged_biomarkers", []),
                "summary": flagged_biomarkers_parsed.get("summary", {})
            }
            
            return json.dumps(combined_profile, indent=2)
            
        except Exception as e:
            return json.dumps({
                "error": f"Profile combination failed: {str(e)}",
                "patient_data": {},
                "flagged_biomarkers": [],
                "summary": {}
            }, indent=2)
