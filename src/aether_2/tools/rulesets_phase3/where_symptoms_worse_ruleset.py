from typing import Dict, Any, List, Tuple
import re
from .constants import FOCUS_AREAS


class WhereSymptomsWorseRuleset:
    """
    Ruleset for evaluating where symptoms get worse (Home/Work/Other).

    Handles radio button selection and free text qualifiers with location-specific logic.
    """
    
    # Per-domain caps for this field
    CAPS = {
        "IMM": 0.70,
        "DTX": 0.60,
        "GA": 0.50,
        "SKN": 0.30,
        "STR": 0.30,
        "COG": 0.20,
        "CM": 0.10,
        "MITO": 0.10,
        "HRM": 0.10
    }
    
    # Keyword groups
    DAMP_MOLD_KEYWORDS = [
        "mold", "mould", "damp", "musty", "water leak", "basement leak",
        "visible mold", "water-damaged", "water damage", "moisture"
    ]
    
    GAS_STOVE_KEYWORDS = [
        "gas stove", "propane stove", "range without hood", "rarely uses hood",
        "no ventilation", "poor ventilation", "cooking fumes"
    ]
    
    RENOVATION_KEYWORDS = [
        "renovation", "paint", "varnish", "new flooring", "glue", "adhesive",
        "strong scents", "cleaners", "vocs", "volatile organic compounds",
        "new carpet", "new furniture"
    ]
    
    CHEMICAL_SOLVENT_KEYWORDS = [
        "solvents", "adhesives", "resins", "voc", "fumes", "printing",
        "coatings", "factory", "lab", "chemical", "industrial"
    ]
    
    HEALTHCARE_KEYWORDS = [
        "hospital", "clinic", "lab", "healthcare", "medical facility",
        "nursing home", "patient care"
    ]
    
    DENTAL_KEYWORDS = [
        "dentist", "dental assistant", "dental hygienist", "amalgam", "mercury",
        "dental x-ray", "dental office"
    ]
    
    SALON_KEYWORDS = [
        "keratin", "brazilian blowout", "formaldehyde", "salon", "beauty work",
        "hair treatment"
    ]
    
    PESTICIDE_KEYWORDS = [
        "pesticides", "herbicides", "glyphosate", "spraying", "turf",
        "groundskeeper", "landscaping", "agriculture", "golf course"
    ]
    
    RESTAURANT_TRAVEL_KEYWORDS = [
        "restaurant", "restaurants", "street food", "travel", "traveler's diarrhea",
        "new country", "traveling", "dining out"
    ]
    
    POOL_KEYWORDS = [
        "chlorine smell", "chloramines", "cough at pool", "lifeguard", "gym pool",
        "indoor pool", "hot tub", "natatorium", "swimming pool"
    ]
    
    def get_where_symptoms_worse_weights(
        self,
        where_data: Any,
        age: int = None,
        environmental_exposures: Dict[str, Any] = None
    ) -> Dict[str, float]:
        """
        Calculate focus area weights based on where symptoms get worse.
        
        Args:
            where_data: Can be string (radio value) or dict with {"radio": "...", "text": "..."}
            age: Patient age (must be >= 18)
            environmental_exposures: Dict with mold_exposure and chemical_exposures from phase2
        
        Returns:
            Dictionary mapping focus area codes to weight adjustments
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # Age check
        if age and age < 18:
            return scores
        
        if not where_data:
            return scores
        
        # Extract radio and text values
        radio_value, text_value = self._extract_radio_and_text(where_data)
        
        # Normalize text
        all_text = text_value.lower().strip() if text_value else ""
        
        # Build flags
        flags = self._build_flags(all_text)
        
        # Apply decision tree based on radio selection
        radio_lower = radio_value.lower() if radio_value else ""
        
        if radio_lower == "home":
            scores = self._apply_home_logic(scores, all_text, flags)
        elif radio_lower == "work":
            scores = self._apply_work_logic(scores, all_text, flags)
        elif radio_lower == "other":
            scores = self._apply_other_logic(scores, all_text, flags)
        
        # Cross-field synergy: If mold_exposure = Yes in phase2
        if environmental_exposures:
            mold_exposure = environmental_exposures.get("mold_exposure", False)
            if mold_exposure in [True, "yes", "Yes", "true", "True"]:
                scores["IMM"] += 0.10
                scores["DTX"] += 0.10
        
        # Apply caps
        for domain in scores:
            scores[domain] = min(scores[domain], self.CAPS.get(domain, 1.0))
        
        return scores
    
    def _extract_radio_and_text(self, data: Any) -> Tuple[str, str]:
        """
        Extract radio button value and text from string format.

        Supports string format: "Home, mold in basement" or "Work; chemical exposure" or "Other, restaurant"

        Important: The text portion is ONLY used if the radio value is "Other".
        For "Home" or "Work", the text is ignored (set to empty string).

        Args:
            data: Input data (string format only - dict format no longer supported)

        Returns:
            Tuple of (radio_value, text_value)
        """
        radio_value = ""
        text_value = ""

        if isinstance(data, str):
            data_str = data.strip()

            # Try to split by semicolon or comma
            if ";" in data_str:
                parts = data_str.split(";", 1)
                radio_value = parts[0].strip()
                text_value = parts[1].strip() if len(parts) > 1 else ""
            elif "," in data_str:
                parts = data_str.split(",", 1)
                radio_value = parts[0].strip()
                text_value = parts[1].strip() if len(parts) > 1 else ""
            else:
                # No separator - treat entire string as radio value
                radio_value = data_str
                text_value = ""

            # IMPORTANT: Only use text if radio is "Other"
            # For "Home" or "Work", ignore the text portion
            if radio_value.lower() not in ["other"]:
                text_value = ""

        return radio_value, text_value
    
    def _build_flags(self, all_text: str) -> Dict[str, bool]:
        """Build flags for decision tree."""
        flags = {
            "damp_mold": False,
            "gas_stove": False,
            "renovation": False,
            "chemical_solvent": False,
            "healthcare": False,
            "dental": False,
            "salon": False,
            "pesticide": False,
            "restaurant_travel": False,
            "pool": False
        }
        
        flags["damp_mold"] = any(term in all_text for term in self.DAMP_MOLD_KEYWORDS)
        flags["gas_stove"] = any(term in all_text for term in self.GAS_STOVE_KEYWORDS)
        flags["renovation"] = any(term in all_text for term in self.RENOVATION_KEYWORDS)
        flags["chemical_solvent"] = any(term in all_text for term in self.CHEMICAL_SOLVENT_KEYWORDS)
        flags["healthcare"] = any(term in all_text for term in self.HEALTHCARE_KEYWORDS)
        flags["dental"] = any(term in all_text for term in self.DENTAL_KEYWORDS)
        flags["salon"] = any(term in all_text for term in self.SALON_KEYWORDS)
        flags["pesticide"] = any(term in all_text for term in self.PESTICIDE_KEYWORDS)
        flags["restaurant_travel"] = any(term in all_text for term in self.RESTAURANT_TRAVEL_KEYWORDS)
        flags["pool"] = any(term in all_text for term in self.POOL_KEYWORDS)
        
        return flags
    
    def _apply_home_logic(self, scores: Dict[str, float], all_text: str, flags: Dict[str, bool]) -> Dict[str, float]:
        """Apply Home decision tree."""
        # A1. Damp/Mold indicators
        if flags["damp_mold"]:
            scores["IMM"] += 0.50
            scores["DTX"] += 0.30
            scores["SKN"] += 0.20
            scores["GA"] += 0.20
        
        # A2. Kitchen gas/propane stove
        if flags["gas_stove"]:
            scores["GA"] += 0.10
            scores["IMM"] += 0.15
        
        # A3. Recent renovation / paints / solvents / fragrances
        if flags["renovation"]:
            scores["DTX"] += 0.40
            scores["IMM"] += 0.20
            # Optional COG if headache/brain fog mentioned
            if any(term in all_text for term in ["headache", "brain fog", "foggy", "cognitive"]):
                scores["COG"] += 0.10
        
        # A4. Home eating / take-out often
        if flags["restaurant_travel"] and "home" in all_text:
            scores["GA"] += 0.15
        
        return scores
    
    def _apply_work_logic(self, scores: Dict[str, float], all_text: str, flags: Dict[str, bool]) -> Dict[str, float]:
        """Apply Work decision tree."""
        # B1. Workplace damp/mold
        if flags["damp_mold"]:
            scores["IMM"] += 0.50
            scores["DTX"] += 0.30
            scores["SKN"] += 0.20
        
        # B2. Chemical/solvent/glue/industrial
        if flags["chemical_solvent"]:
            scores["DTX"] += 0.40
            scores["IMM"] += 0.20
            # Optional COG if headache/brain fog mentioned
            if any(term in all_text for term in ["headache", "brain fog", "foggy", "cognitive"]):
                scores["COG"] += 0.10
        
        # B3. Healthcare setting
        if flags["healthcare"]:
            scores["IMM"] += 0.40
            scores["STR"] += 0.20
        
        # B4. Dental office
        if flags["dental"]:
            scores["DTX"] += 0.30
            scores["IMM"] += 0.10
        
        # B5. Salon/beauty work
        if flags["salon"]:
            scores["DTX"] += 0.40
            scores["IMM"] += 0.20
            scores["SKN"] += 0.10
        
        # B6. Golf course / landscaping / agriculture
        if flags["pesticide"]:
            scores["DTX"] += 0.30
            scores["IMM"] += 0.20
        
        return scores
    
    def _apply_other_logic(self, scores: Dict[str, float], all_text: str, flags: Dict[str, bool]) -> Dict[str, float]:
        """Apply Other decision tree."""
        # C1. Restaurants / travel
        if flags["restaurant_travel"]:
            scores["GA"] += 0.25
        
        # C2. Indoor pool / hot tub
        if flags["pool"]:
            scores["IMM"] += 0.30
            scores["SKN"] += 0.20
            # Optional COG if sleep/airway disturbance mentioned
            if any(term in all_text for term in ["sleep", "airway", "breathing", "cough"]):
                scores["COG"] += 0.10
        
        # C3. Home cooking appliances (gas stove listed under Other)
        if flags["gas_stove"]:
            scores["GA"] += 0.10
            scores["IMM"] += 0.15
        
        # C4. Outdoor hobbies with pesticide contact
        if flags["pesticide"] and any(term in all_text for term in ["golfing", "lawn care", "gardening", "hobby"]):
            scores["DTX"] += 0.20
            scores["IMM"] += 0.10
        
        return scores




