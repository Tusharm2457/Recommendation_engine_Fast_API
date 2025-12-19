"""
Field 30: Current Home/Workplace Environmental Exposures Ruleset

Multi-select with optional "Other" free text.
NLP-based scoring with duration/frequency modifiers and mitigation discounts.
"""

import re
from typing import Dict, List, Tuple, Any


class CurrentEnvironmentalExposuresRuleset:
    """
    Evaluate current home/workplace environmental exposures.
    
    Multi-select options:
    - Water leaks / Dampness
    - Ongoing renovations
    - Fresh paint / VOCs
    - New carpet / Flooring glue
    - Poor ventilation / Stale air
    - Gas stove
    - Wood-burning fireplace
    - Pets indoors
    - Heavy fragrance / Air fresheners
    - High-EMF sources (server room)
    - Other building issues
    
    Scoring approach:
    - Additive, monotonic points model (transparent like clinical scores)
    - Base weights proportional to evidence strength
    - Duration/frequency modifiers
    - Mitigation discounts
    - Synergy with Phase 2 mold exposure
    - Per-field cap: ≤ +2.0 for all domains
    """
    
    # Per-field cap (total indoor environment contribution)
    MAX_WEIGHT = 2.0
    
    def __init__(self):
        """Initialize the ruleset."""
        pass
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for keyword matching."""
        if not text:
            return ""
        # Lowercase, collapse whitespace
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _parse_selections(self, exposure_data: str) -> Tuple[List[str], str]:
        """
        Parse multi-select input.
        
        Format: "option1, option2; other_text" or "option1; option2; other_text"
        
        Returns:
            Tuple of (selected_options, other_text)
        """
        if not exposure_data or not str(exposure_data).strip():
            return [], ""
        
        # Split by comma or semicolon
        parts = re.split(r'[,;]', str(exposure_data))
        parts = [p.strip() for p in parts if p.strip()]
        
        # Map user-friendly text to internal keys
        option_mapping = {
            "water leaks": "water_leaks",
            "dampness": "water_leaks",
            "water leaks / dampness": "water_leaks",
            "ongoing renovations": "renovations",
            "renovations": "renovations",
            "fresh paint": "paint_VOCs",
            "vocs": "paint_VOCs",
            "fresh paint / vocs": "paint_VOCs",
            "new carpet": "new_carpet_glue",
            "flooring glue": "new_carpet_glue",
            "new carpet / flooring glue": "new_carpet_glue",
            "poor ventilation": "poor_ventilation",
            "stale air": "poor_ventilation",
            "poor ventilation / stale air": "poor_ventilation",
            "gas stove": "gas_stove",
            "wood-burning fireplace": "wood_fireplace",
            "wood fireplace": "wood_fireplace",
            "fireplace": "wood_fireplace",
            "pets indoors": "pets_indoors",
            "pets": "pets_indoors",
            "heavy fragrance": "heavy_fragrance",
            "air fresheners": "heavy_fragrance",
            "scented candles": "heavy_fragrance",
            "heavy fragrance / air fresheners": "heavy_fragrance",
            "high-emf sources": "high_EMF_server_room",
            "high emf": "high_EMF_server_room",
            "server room": "high_EMF_server_room",
            "high-emf sources (server room)": "high_EMF_server_room",
            "other building issues": "other",
            "other": "other"
        }
        
        selected_options = []
        other_text = ""
        
        for part in parts:
            part_lower = part.lower()
            
            # Check if it matches a known option
            matched = False
            for key, value in option_mapping.items():
                if key in part_lower:
                    if value not in selected_options:
                        selected_options.append(value)
                    matched = True
                    break
            
            # If not matched and looks like free text (>20 chars or contains spaces), treat as "other" text
            if not matched and (len(part) > 20 or ' ' in part):
                other_text = part
                if "other" not in selected_options:
                    selected_options.append("other")
        
        return selected_options, other_text
    
    def _extract_duration(self, text: str) -> str:
        """
        Extract duration from text.
        
        Returns: "<3mo", "3-12mo", ">12mo", or "unknown"
        """
        if not text:
            return "unknown"
        
        text_lower = text.lower()
        
        # Check for explicit duration patterns
        # >12 months
        if re.search(r'(\d+)\s*(year|yr|y)\b', text_lower):
            match = re.search(r'(\d+)\s*(year|yr|y)\b', text_lower)
            years = int(match.group(1))
            if years >= 1:
                return ">12mo"
        
        # Months
        if re.search(r'(\d+)\s*(month|mo|m)\b', text_lower):
            match = re.search(r'(\d+)\s*(month|mo|m)\b', text_lower)
            months = int(match.group(1))
            if months < 3:
                return "<3mo"
            elif months <= 12:
                return "3-12mo"
            else:
                return ">12mo"
        
        # Keywords
        if any(kw in text_lower for kw in ["recent", "new", "just", "last week", "last month"]):
            return "<3mo"
        
        if any(kw in text_lower for kw in ["ongoing", "chronic", "years", "long time", "always"]):
            return ">12mo"

        return "unknown"

    def _detect_daily_exposure(self, text: str) -> bool:
        """Detect if exposure is daily/overnight."""
        if not text:
            return False

        text_lower = text.lower()
        keywords = [
            "daily", "every day", "overnight", "24/7", "all day",
            "live in", "sleep in", "work in", "constant"
        ]
        return any(kw in text_lower for kw in keywords)

    def _detect_mitigations(self, text: str) -> List[str]:
        """
        Detect mitigation strategies mentioned in text.

        Returns list of detected mitigations:
        - "vented_hood" (range hood used often/always)
        - "hepa_purifier" (air purifier)
        - "dehumidifier" (dehumidifier 40-50% RH)
        - "windows_opened" (windows opened regularly)
        - "low_voc_products" (low-VOC products)
        """
        if not text:
            return []

        text_lower = text.lower()
        mitigations = []

        # Vented range hood
        if any(kw in text_lower for kw in ["range hood", "vent hood", "exhaust fan", "vented"]):
            mitigations.append("vented_hood")

        # HEPA purifier
        if any(kw in text_lower for kw in ["hepa", "air purifier", "air filter", "purifier"]):
            mitigations.append("hepa_purifier")

        # Dehumidifier
        if any(kw in text_lower for kw in ["dehumidifier", "humidity control", "40-50%", "rh"]):
            mitigations.append("dehumidifier")

        # Windows opened
        if any(kw in text_lower for kw in ["windows open", "open windows", "ventilate", "fresh air"]):
            mitigations.append("windows_opened")

        # Low-VOC products
        if any(kw in text_lower for kw in ["low voc", "low-voc", "no voc", "voc-free", "green products"]):
            mitigations.append("low_voc_products")

        return mitigations

    def _classify_other_text(self, other_text: str) -> List[str]:
        """
        Classify "Other" free text into known categories using lexicons.

        Returns list of matched categories (can map to existing options).
        """
        if not other_text:
            return []

        text_lower = other_text.lower()
        matched_categories = []

        # Mold/dampness keywords
        if any(kw in text_lower for kw in ["mold", "musty", "leak", "flood", "condensation", "damp"]):
            matched_categories.append("water_leaks")

        # VOC/chemical keywords
        if any(kw in text_lower for kw in ["formaldehyde", "solvent", "adhesive", "new furniture", "pressed wood"]):
            matched_categories.append("paint_VOCs")

        # Printer/toner/ozone
        if any(kw in text_lower for kw in ["printer", "toner", "ozone", "copier", "office equipment"]):
            matched_categories.append("printer_toner")

        # Radon (log as safety item, no GI weight)
        if "radon" in text_lower:
            matched_categories.append("radon")

        return matched_categories

    def get_current_environmental_exposures_weights(
        self,
        exposure_data: Any,
        has_pets_phase2: bool = False,
        has_mold_exposure_phase2: bool = False
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights for current environmental exposures.

        Args:
            exposure_data: Multi-select options (comma/semicolon separated) + optional "Other" text
            has_pets_phase2: Whether patient has pets (from Phase 2 data)
            has_mold_exposure_phase2: Whether patient has mold exposure (from Phase 2 data)

        Returns:
            Tuple of (weights dict, flags list)
        """
        weights: Dict[str, float] = {}
        flags: List[str] = []

        # Handle empty/None input
        if not exposure_data or not str(exposure_data).strip():
            return weights, flags

        # Parse selections
        selected_options, other_text = self._parse_selections(str(exposure_data))

        if not selected_options:
            flags.append("No recognized environmental exposures detected")
            return weights, flags

        # Validate other_text length (max 300 chars)
        if other_text and len(other_text) > 300:
            flags.append(f"Other text truncated from {len(other_text)} to 300 chars")
            other_text = other_text[:300]

        # Extract metadata from other_text (if present)
        duration = self._extract_duration(other_text) if other_text else "unknown"
        is_daily = self._detect_daily_exposure(other_text) if other_text else False
        mitigations = self._detect_mitigations(other_text) if other_text else []

        # Classify "Other" text into known categories
        if "other" in selected_options and other_text:
            other_categories = self._classify_other_text(other_text)
            # Add matched categories to selected_options (avoid duplicates)
            for cat in other_categories:
                if cat not in selected_options:
                    selected_options.append(cat)
            flags.append(f"Other text classified as: {', '.join(other_categories) if other_categories else 'unrecognized'}")

        # Track detected exposures
        exposures_detected = []

        # Base weights for each exposure type
        # C1) Water leaks / Dampness
        if "water_leaks" in selected_options:
            exposures_detected.append("Water leaks/Dampness")
            flags.append("Detected: Water leaks/Dampness (mold & damp microbiome)")

            weights["GA"] = weights.get("GA", 0.0) + 0.30
            weights["IMM"] = weights.get("IMM", 0.0) + 0.40
            weights["DTX"] = weights.get("DTX", 0.0) + 0.30
            weights["COG"] = weights.get("COG", 0.0) + 0.20
            weights["SKN"] = weights.get("SKN", 0.0) + 0.20

            # Synergy: Water leaks + Phase 2 mold exposure
            if has_mold_exposure_phase2:
                weights["GA"] = weights.get("GA", 0.0) + 0.10
                weights["IMM"] = weights.get("IMM", 0.0) + 0.10
                flags.append("Cross-field synergy: Water leaks + Phase 2 mold exposure → GA +0.10, IMM +0.10")

        # C2) Ongoing renovations
        if "renovations" in selected_options:
            exposures_detected.append("Ongoing renovations")
            flags.append("Detected: Ongoing renovations (demolition, sanding, adhesives)")

            weights["GA"] = weights.get("GA", 0.0) + 0.20
            weights["DTX"] = weights.get("DTX", 0.0) + 0.30
            weights["IMM"] = weights.get("IMM", 0.0) + 0.20
            weights["COG"] = weights.get("COG", 0.0) + 0.10

        # C3) Fresh paint / VOCs
        if "paint_VOCs" in selected_options:
            exposures_detected.append("Fresh paint/VOCs")
            flags.append("Detected: Fresh paint/VOCs (formaldehyde, off-gassing)")

            weights["GA"] = weights.get("GA", 0.0) + 0.20
            weights["DTX"] = weights.get("DTX", 0.0) + 0.30
            weights["IMM"] = weights.get("IMM", 0.0) + 0.10
            weights["COG"] = weights.get("COG", 0.0) + 0.10
            weights["SKN"] = weights.get("SKN", 0.0) + 0.10

        # C4) New carpet / Flooring glue
        if "new_carpet_glue" in selected_options:
            exposures_detected.append("New carpet/Flooring glue")
            flags.append("Detected: New carpet/Flooring glue (VOC sources)")

            weights["GA"] = weights.get("GA", 0.0) + 0.20
            weights["DTX"] = weights.get("DTX", 0.0) + 0.30
            weights["SKN"] = weights.get("SKN", 0.0) + 0.10
            weights["COG"] = weights.get("COG", 0.0) + 0.10

        # C5) Poor ventilation / Stale air
        if "poor_ventilation" in selected_options:
            exposures_detected.append("Poor ventilation/Stale air")
            flags.append("Detected: Poor ventilation/Stale air (concentrated VOCs/CO₂)")

            weights["GA"] = weights.get("GA", 0.0) + 0.10
            weights["COG"] = weights.get("COG", 0.0) + 0.20
            weights["DTX"] = weights.get("DTX", 0.0) + 0.10
            weights["IMM"] = weights.get("IMM", 0.0) + 0.10

        # C6) Gas stove
        if "gas_stove" in selected_options:
            exposures_detected.append("Gas stove")
            flags.append("Detected: Gas stove (NO₂, PM, benzene)")

            weights["GA"] = weights.get("GA", 0.0) + 0.10
            weights["CM"] = weights.get("CM", 0.0) + 0.20
            weights["IMM"] = weights.get("IMM", 0.0) + 0.10
            weights["DTX"] = weights.get("DTX", 0.0) + 0.10

        # C7) Wood-burning fireplace
        if "wood_fireplace" in selected_options:
            exposures_detected.append("Wood-burning fireplace")
            flags.append("Detected: Wood-burning fireplace (PM₂.₅, irritants)")

            weights["GA"] = weights.get("GA", 0.0) + 0.10
            weights["CM"] = weights.get("CM", 0.0) + 0.20
            weights["IMM"] = weights.get("IMM", 0.0) + 0.20
            weights["DTX"] = weights.get("DTX", 0.0) + 0.20
            weights["SKN"] = weights.get("SKN", 0.0) + 0.10

        # C8) Pets indoors (incremental environment load)
        if "pets_indoors" in selected_options:
            exposures_detected.append("Pets indoors")

            if has_pets_phase2:
                # Half weights (avoid double-counting)
                flags.append("Detected: Pets indoors (incremental load; Phase 2 pets already scored)")
                weights["IMM"] = weights.get("IMM", 0.0) + 0.15
                weights["SKN"] = weights.get("SKN", 0.0) + 0.10
                weights["GA"] = weights.get("GA", 0.0) + 0.05
            else:
                # Full weights
                flags.append("Detected: Pets indoors (dander allergen)")
                weights["IMM"] = weights.get("IMM", 0.0) + 0.30
                weights["SKN"] = weights.get("SKN", 0.0) + 0.20
                weights["GA"] = weights.get("GA", 0.0) + 0.10

        # C9) Heavy fragrance / Air fresheners
        if "heavy_fragrance" in selected_options:
            exposures_detected.append("Heavy fragrance/Air fresheners")
            flags.append("Detected: Heavy fragrance/Air fresheners (VOCs, terpenes, phthalates)")

            weights["GA"] = weights.get("GA", 0.0) + 0.10
            weights["DTX"] = weights.get("DTX", 0.0) + 0.20
            weights["IMM"] = weights.get("IMM", 0.0) + 0.10
            weights["SKN"] = weights.get("SKN", 0.0) + 0.20
            weights["COG"] = weights.get("COG", 0.0) + 0.10

        # C10) High-EMF sources (server room)
        if "high_EMF_server_room" in selected_options:
            exposures_detected.append("High-EMF sources")
            flags.append("Detected: High-EMF sources (environmental stress)")

            weights["STR"] = weights.get("STR", 0.0) + 0.10
            weights["COG"] = weights.get("COG", 0.0) + 0.10

        # C11) Printer/toner/ozone (from "Other" text)
        if "printer_toner" in selected_options:
            exposures_detected.append("Printer/toner/ozone")
            flags.append("Detected: Printer/toner/ozone (ultrafine particles)")

            weights["DTX"] = weights.get("DTX", 0.0) + 0.10
            weights["IMM"] = weights.get("IMM", 0.0) + 0.10

        # C12) Radon (from "Other" text) - log as safety item, no GI weight
        if "radon" in selected_options:
            exposures_detected.append("Radon")
            flags.append("⚠️ SAFETY: Radon detected - recommend testing and mitigation")
            # No weights added for radon

        # D) Apply duration/frequency modifiers
        duration_multiplier = 1.0
        if duration == "3-12mo":
            duration_multiplier = 1.15
            flags.append("Duration modifier: 3-12 months → ×1.15")
        elif duration == ">12mo":
            duration_multiplier = 1.30
            flags.append("Duration modifier: >12 months → ×1.30")

        frequency_multiplier = 1.0
        if is_daily:
            frequency_multiplier = 1.15
            flags.append("Frequency modifier: Daily/overnight exposure → ×1.15")

        # Apply modifiers (multiplicative)
        total_multiplier = duration_multiplier * frequency_multiplier
        if total_multiplier > 1.0:
            for fa in list(weights.keys()):
                weights[fa] *= total_multiplier
            flags.append(f"Total modifier applied: ×{total_multiplier:.2f}")

        # E) Apply mitigation discounts
        if mitigations:
            flags.append(f"Mitigations detected: {', '.join(mitigations)}")

            # Each mitigation reduces weights by 10% (multiplicative)
            mitigation_discount = 0.90 ** len(mitigations)
            for fa in list(weights.keys()):
                weights[fa] *= mitigation_discount
            flags.append(f"Mitigation discount applied: ×{mitigation_discount:.2f} ({len(mitigations)} mitigations)")

        # F) Apply per-field cap (≤ +2.0 for all domains)
        for fa in list(weights.keys()):
            if weights[fa] > self.MAX_WEIGHT:
                flags.append(f"{fa} capped at +{self.MAX_WEIGHT} (was +{weights[fa]:.3f})")
                weights[fa] = self.MAX_WEIGHT

        # Remove zero/negative weights
        weights = {fa: w for fa, w in weights.items() if w > 1e-6}

        # Summary
        if exposures_detected:
            flags.insert(0, f"Exposures detected: {', '.join(exposures_detected)}")
        else:
            flags.append("No recognized exposures detected")

        return weights, flags

