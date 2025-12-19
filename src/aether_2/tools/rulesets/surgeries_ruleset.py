"""
Surgeries-based focus area scoring ruleset.
"""

from typing import Dict, List, Tuple
from .constants import FOCUS_AREAS


class SurgeriesRuleset:
    """Ruleset for surgeries-based focus area scoring."""
    
    def get_surgeries_weights(
        self,
        surgeries_text: str,
        digestive_symptoms: str,
        alcohol_frequency: str,
        current_medications: List[Dict]
    ) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
        """
        Calculate focus area weights based on surgeries.
        
        Args:
            surgeries_text: Free-text surgeries (e.g., "Appendectomy 2013; Cholecystectomy 2021")
            digestive_symptoms: Digestive symptoms text
            alcohol_frequency: Alcohol use frequency
            current_medications: List of medication objects
            
        Returns:
            Tuple of:
                - Cumulative scores dict (all surgeries combined, clamped at 1.0)
                - Per-surgery breakdown dict {original_text: {focus_area: score}}
        """
        # Parse surgeries
        surgeries_list = self._parse_surgeries_text(surgeries_text)
        
        # Early exit if no surgeries
        if not surgeries_list:
            return ({code: 0.0 for code in FOCUS_AREAS}, {})
        
        cumulative_scores = {code: 0.0 for code in FOCUS_AREAS}
        per_surgery_breakdown = {}
        
        # Process each surgery - apply base weights
        for original_text, procedure_normalized, year in surgeries_list:
            surgery_scores = self._score_single_surgery(procedure_normalized, year)
            
            # Add to cumulative
            for code in FOCUS_AREAS:
                cumulative_scores[code] += surgery_scores[code]
            
            # Store per-surgery breakdown (use original text as key)
            per_surgery_breakdown[original_text] = surgery_scores
        
        # Apply modifiers (A, B, E, G)
        self._apply_modifiers(
            cumulative_scores,
            surgeries_list,
            digestive_symptoms,
            alcohol_frequency,
            current_medications
        )
        
        # Clamp each focus area at 1.0
        for code in FOCUS_AREAS:
            cumulative_scores[code] = min(cumulative_scores[code], 1.0)
        
        return (cumulative_scores, per_surgery_breakdown)
    
    def _parse_surgeries_text(self, surgeries_text: str) -> List[Tuple[str, str, str]]:
        """
        Parse free-text surgeries into structured list.
        
        Args:
            surgeries_text: Free-text surgeries (e.g., "Appendectomy 2013; Cholecystectomy 2021")
            
        Returns:
            List of (original_text, procedure_name_normalized, year) tuples
        """
        # Handle null/empty/NA cases
        if not surgeries_text:
            return []
        
        surgeries_text_lower = surgeries_text.lower().strip()
        if surgeries_text_lower in ["no", "na", "none", "null"]:
            return []
        
        surgeries = []
        
        # Split by semicolon
        entries = surgeries_text.split(';')
        
        for entry in entries:
            original_entry = entry.strip()
            if not original_entry:
                continue
            
            # Split into tokens
            tokens = original_entry.split()
            
            # Check if last token is a year (4 digits)
            if tokens and tokens[-1].isdigit() and len(tokens[-1]) == 4:
                year = tokens[-1]
                procedure_name = ' '.join(tokens[:-1]).lower().strip()
            else:
                year = "unknown"
                procedure_name = original_entry.lower().strip()
            
            if procedure_name:
                surgeries.append((original_entry, procedure_name, year))
        
        return surgeries
    
    def _classify_surgery(self, procedure_name: str) -> str:
        """
        Classify surgery into category using keyword matching.
        
        Returns:
            Surgery type: 'cholecystectomy', 'bariatric', 'appendectomy', 
                          'bowel_resection', 'fundoplication', 'pancreatic',
                          'thyroidectomy', 'oophorectomy', 'hysterectomy',
                          'cardiac', 'unknown'
        """
        proc_lower = procedure_name.lower()
        
        # GI & Hepatobiliary
        if "cholecystectomy" in proc_lower or "gallbladder" in proc_lower:
            return "cholecystectomy"
        
        if any(keyword in proc_lower for keyword in ["bariatric", "gastric bypass", "roux-en-y", "roux en y", "sleeve", "bpd", "gastric sleeve"]):
            return "bariatric"
        
        if "appendectomy" in proc_lower or "appendix" in proc_lower:
            return "appendectomy"
        
        if any(keyword in proc_lower for keyword in ["bowel resection", "colectomy", "ileocecal", "ileal pouch", "ileostomy", "colostomy"]):
            return "bowel_resection"
        
        if "fundoplication" in proc_lower or "hiatal hernia" in proc_lower:
            return "fundoplication"
        
        if "pancreatic" in proc_lower or "pancreas" in proc_lower or "whipple" in proc_lower:
            return "pancreatic"
        
        # Endocrine & Reproductive
        if "thyroidectomy" in proc_lower or "thyroid removal" in proc_lower:
            return "thyroidectomy"
        
        if "oophorectomy" in proc_lower or ("ovar" in proc_lower and "removal" in proc_lower):
            return "oophorectomy"
        
        if "hysterectomy" in proc_lower or ("uterus" in proc_lower and "removal" in proc_lower):
            return "hysterectomy"

        # Cardiac & Vascular
        if any(keyword in proc_lower for keyword in ["bypass", "cabg", "valve", "pacemaker", "icd", "cardiac", "coronary"]):
            return "cardiac"

        return "unknown"

    def _score_single_surgery(self, procedure_name: str, year: str) -> Dict[str, float]:
        """Score a single surgery based on type."""
        scores = {code: 0.0 for code in FOCUS_AREAS}

        surgery_type = self._classify_surgery(procedure_name)

        # Apply base weights by surgery type

        # GI & Hepatobiliary
        if surgery_type == "cholecystectomy":
            scores["GA"] += 0.60

        elif surgery_type == "bariatric":
            scores["GA"] += 0.80
            scores["DTX"] += 0.50
            scores["CM"] += 0.30

        elif surgery_type == "appendectomy":
            scores["GA"] += 0.30

        elif surgery_type == "bowel_resection":
            scores["GA"] += 0.85
            scores["DTX"] += 0.30

        elif surgery_type == "fundoplication":
            scores["GA"] += 0.40

        elif surgery_type == "pancreatic":
            scores["GA"] += 0.70
            scores["DTX"] += 0.20

        # Endocrine & Reproductive
        elif surgery_type == "thyroidectomy":
            scores["HRM"] += 0.60

        elif surgery_type == "oophorectomy":
            scores["HRM"] += 0.60
            scores["CM"] += 0.30

        elif surgery_type == "hysterectomy":
            scores["HRM"] += 0.30

        # Cardiac & Vascular
        elif surgery_type == "cardiac":
            scores["CM"] += 0.70
            scores["MITO"] += 0.30
            scores["COG"] += 0.20

        return scores

    def _apply_modifiers(
        self,
        cumulative_scores: Dict[str, float],
        surgeries_list: List[Tuple[str, str, str]],
        digestive_symptoms: str,
        alcohol_frequency: str,
        current_medications: List[Dict]
    ) -> None:
        """Apply integrative add-ons (A, B, E, G)."""

        # G. Surgery count modifier (apply first)
        surgery_count = len(surgeries_list)
        surgery_count_bonus = min(surgery_count * 0.05, 0.15)
        cumulative_scores["IMM"] += surgery_count_bonus
        cumulative_scores["GA"] += surgery_count_bonus

        # Track specific surgery types
        had_cholecystectomy = False
        had_bariatric = False

        for original_text, procedure_normalized, year in surgeries_list:
            surgery_type = self._classify_surgery(procedure_normalized)

            if surgery_type == "cholecystectomy":
                had_cholecystectomy = True

            if surgery_type == "bariatric":
                had_bariatric = True

            # E. Bowel resection specifics (parse from original text)
            if surgery_type == "bowel_resection":
                original_lower = original_text.lower()

                if "ileocecal" in original_lower:
                    cumulative_scores["GA"] += 0.10

                if any(keyword in original_lower for keyword in ["stoma", "colostomy", "ileostomy"]):
                    cumulative_scores["GA"] += 0.10
                    cumulative_scores["SKN"] += 0.05

                if any(keyword in original_lower for keyword in ["ileal pouch", "j-pouch", "j pouch"]):
                    cumulative_scores["GA"] += 0.10
                    cumulative_scores["SKN"] += 0.05

        # A. Post-cholecystectomy symptoms
        if had_cholecystectomy and digestive_symptoms:
            if "diarrhea" in digestive_symptoms.lower():
                cumulative_scores["GA"] += 0.10

        # B. Bariatric surgery details
        if had_bariatric:
            # Check alcohol use
            if alcohol_frequency and alcohol_frequency.lower() not in ["never", "none", ""]:
                cumulative_scores["DTX"] += 0.10

            # Check for extended-release meds
            if self._has_extended_release_meds(current_medications):
                cumulative_scores["DTX"] += 0.10

            # Check for GI symptoms
            if digestive_symptoms:
                symptoms_lower = digestive_symptoms.lower()
                if any(keyword in symptoms_lower for keyword in ["bloat", "diarrhea", "gas", "foul"]):
                    cumulative_scores["GA"] += 0.10

    def _has_extended_release_meds(self, current_medications: List[Dict]) -> bool:
        """Check if patient has extended-release medications."""
        if not current_medications:
            return False

        for med in current_medications:
            # Handle both dict and string formats
            if isinstance(med, dict):
                # Try both "name" and "medication_name" fields for compatibility
                med_name = med.get("name", med.get("medication_name", "")).lower()
            else:
                med_name = str(med).lower()

            if any(keyword in med_name for keyword in ["xr", "er", "extended", "sustained", "sr", "cr"]):
                return True

        return False

