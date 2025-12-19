"""
Ruleset for Field 28: Early Environmental/Toxic Exposures (Childhood)

Radio: Yes/No → if Yes, free-text details (what/where/when/how long)

Scoring logic:
- Detects 5 exposure categories using NLP keyword matching
- Applies duration multipliers (optional, if mentioned)
- Applies intensity multipliers (continuous vs intermittent)
- Applies early-life multipliers (if age <5 mentioned)
- Per-field caps: DTX/IMM/MITO/COG/CM/SKN ≤ +1.5, GA ≤ +1.0
- Safety check: Flags ongoing unsafe living conditions
"""

import re
from typing import Dict, List, Tuple, Any, Optional


class EarlyEnvironmentalExposuresRuleset:
    """NLP-based keyword detection for early environmental/toxic exposures."""
    
    # Per-field caps
    MAX_WEIGHT_GENERAL = 1.5  # DTX, IMM, MITO, COG, CM, SKN
    MAX_WEIGHT_GA = 1.0       # GA has lower cap
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, collapse whitespace."""
        if not text:
            return ""
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _extract_duration_months(self, text: str) -> Optional[int]:
        """
        Extract exposure duration in months from free text.
        
        Handles:
        - "5 years", "5 yrs", "5y"
        - "6 months", "6 mo"
        - "3 weeks", "3 wk"
        
        Returns:
            Number of months, or None if not found
        """
        text_lower = text.lower()
        
        # Pattern 1: X years/yrs/y (convert to months)
        match = re.search(r'(\d+(?:\.\d+)?)\s*(?:years?|yrs?|y\b)', text_lower)
        if match:
            years = float(match.group(1))
            return int(years * 12)
        
        # Pattern 2: X months/mo
        match = re.search(r'(\d+(?:\.\d+)?)\s*(?:months?|mo\b)', text_lower)
        if match:
            return int(float(match.group(1)))
        
        # Pattern 3: X weeks/wk (convert to months, ~4.3 weeks/month)
        match = re.search(r'(\d+(?:\.\d+)?)\s*(?:weeks?|wks?|wk\b)', text_lower)
        if match:
            weeks = float(match.group(1))
            return max(1, int(weeks / 4.3))  # At least 1 month
        
        return None
    
    def _get_duration_multiplier(self, duration_months: Optional[int]) -> float:
        """
        Get duration multiplier based on exposure length.
        
        Returns:
            0.8 (<3 mo), 1.0 (3-24 mo), 1.2 (2-5 y), 1.4 (>5 y)
        """
        if duration_months is None:
            return 1.0  # Default if not mentioned
        
        if duration_months < 3:
            return 0.8
        elif duration_months <= 24:
            return 1.0
        elif duration_months <= 60:  # 5 years
            return 1.2
        else:
            return 1.4
    
    def _detect_intensity(self, text: str) -> float:
        """
        Detect exposure intensity from text.
        
        Returns:
            1.3 (continuous/"lived in"), 1.0 (intermittent/occasional)
        """
        text_lower = text.lower()
        
        # Continuous exposure keywords
        continuous_keywords = [
            r'\blived in\b', r'\bdaily\b', r'\bevery day\b',
            r'\bschool near\b', r'\bhome near\b', r'\bgrew up\b',
            r'\bchildhood home\b', r'\bconstant\b', r'\balways\b'
        ]
        
        for keyword in continuous_keywords:
            if re.search(keyword, text_lower):
                return 1.3
        
        # Intermittent exposure keywords
        intermittent_keywords = [
            r'\boccasionally\b', r'\bsometimes\b', r'\bvisits?\b',
            r'\bfew times\b', r'\bonce in a while\b'
        ]
        
        for keyword in intermittent_keywords:
            if re.search(keyword, text_lower):
                return 1.0
        
        # Default: assume continuous if not specified
        return 1.3
    
    def _detect_early_life(self, text: str) -> float:
        """
        Detect if exposure occurred in early life (age <5).
        
        Returns:
            1.2 (early life), 1.0 (otherwise)
        """
        text_lower = text.lower()
        
        # Early life keywords
        early_life_keywords = [
            r'\binfant\b', r'\bbaby\b', r'\btoddler\b',
            r'\bpreschool\b', r'\belementary\b',
            r'\bbefore age [1-5]\b', r'\bunder [1-5]\b',
            r'\bwhen i was [1-5]\b', r'\bas a child\b'
        ]
        
        for keyword in early_life_keywords:
            if re.search(keyword, text_lower):
                return 1.2

        return 1.0

    def _detect_heavy_metals(self, text: str) -> bool:
        """Detect heavy metal exposure keywords."""
        text_lower = text.lower()

        keywords = [
            r'\blead\b', r'\blead paint\b', r'\bmercury\b', r'\bamalgam\b',
            r'\bcadmium\b', r'\barsenic\b', r'\buranium\b',
            r'\bmine\b', r'\bsmelter\b'
        ]

        for keyword in keywords:
            if re.search(keyword, text_lower):
                return True
        return False

    def _detect_lead_specific(self, text: str) -> bool:
        """Detect lead-specific exposure (higher COG impact)."""
        text_lower = text.lower()
        return bool(re.search(r'\blead\b', text_lower))

    def _detect_smoke(self, text: str) -> bool:
        """Detect secondhand smoke exposure keywords."""
        text_lower = text.lower()

        keywords = [
            r'\bsecondhand smoke\b', r'\bsmoking at home\b', r'\bsmoke\b',
            r'\bwood stove\b', r'\bcoal stove\b', r'\bparents smoked\b',
            r'\bcigarette\b', r'\btobacco\b'
        ]

        for keyword in keywords:
            if re.search(keyword, text_lower):
                return True
        return False

    def _detect_pesticides(self, text: str) -> bool:
        """Detect pesticide/herbicide exposure keywords."""
        text_lower = text.lower()

        keywords = [
            r'\borganophosphate\b', r'\bchlorpyrifos\b', r'\bmalathion\b',
            r'\bddt\b', r'\bglyphosate\b', r'\bweed killer\b',
            r'\bfarm spray\b', r'\bpesticide\b', r'\bherbicide\b',
            r'\binsecticide\b', r'\bfarm\b'
        ]

        for keyword in keywords:
            if re.search(keyword, text_lower):
                return True
        return False

    def _detect_mold(self, text: str) -> bool:
        """Detect mold/water damage exposure keywords."""
        text_lower = text.lower()

        keywords = [
            r'\bmold\b', r'\bmildew\b', r'\bdamp\b', r'\bmusty\b',
            r'\bwater.?damaged\b', r'\bwater damage\b', r'\bleak\b',
            r'\bflooding\b'
        ]

        for keyword in keywords:
            if re.search(keyword, text_lower):
                return True
        return False

    def _detect_solvents(self, text: str) -> bool:
        """Detect solvent/VOC exposure keywords."""
        text_lower = text.lower()

        keywords = [
            r'\bsolvents?\b', r'\bthinners?\b', r'\bbenzene\b', r'\btoluene\b',
            r'\bglue\b', r'\bpaint fumes\b', r'\bvoc\b',
            r'\bchemicals?\b', r'\bfumes\b'
        ]

        for keyword in keywords:
            if re.search(keyword, text_lower):
                return True
        return False

    def _detect_ongoing_unsafe(self, text: str) -> bool:
        """Detect ongoing unsafe living conditions."""
        text_lower = text.lower()

        keywords = [
            r'\bcurrently\b', r'\bstill living\b', r'\bright now\b',
            r'\btoday\b', r'\bpresent\b'
        ]

        for keyword in keywords:
            if re.search(keyword, text_lower):
                return True
        return False

    def get_early_environmental_exposures_weights(
        self,
        exposure_data: Any
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights for early environmental/toxic exposures.

        Args:
            exposure_data: Radio (Yes/No) + optional free text (semicolon-separated)

        Returns:
            Tuple of (weights dict, flags list)
        """
        weights: Dict[str, float] = {}
        flags: List[str] = []

        # Handle empty/None input
        if not exposure_data or not str(exposure_data).strip():
            return weights, flags

        # Parse input: "Radio; free text"
        exposure_str = str(exposure_data).strip()
        parts = exposure_str.split(';', 1)
        radio = parts[0].strip()
        free_text = parts[1].strip() if len(parts) > 1 else ""

        # Validate radio selection
        if radio not in ["Yes", "No"]:
            flags.append(f"Invalid radio selection: '{radio}' (expected Yes/No)")
            return weights, flags

        # If No, return empty weights
        if radio == "No":
            return weights, flags

        # If Yes but no free text, flag it
        if not free_text:
            flags.append("Radio is 'Yes' but no free text provided")
            return weights, flags

        # Validate free text length (max 1000 chars)
        if len(free_text) > 1000:
            flags.append(f"Free text truncated from {len(free_text)} to 1000 chars")
            free_text = free_text[:1000]

        # Normalize text
        text_normalized = self._normalize_text(free_text)

        # Extract multipliers
        duration_months = self._extract_duration_months(text_normalized)
        duration_mul = self._get_duration_multiplier(duration_months)
        intensity_mul = self._detect_intensity(text_normalized)
        early_life_mul = self._detect_early_life(text_normalized)

        # Log extracted multipliers
        if duration_months:
            flags.append(f"Extracted duration: {duration_months} months (multiplier: {duration_mul})")
        flags.append(f"Intensity multiplier: {intensity_mul} ({'continuous' if intensity_mul > 1.0 else 'intermittent'})")
        flags.append(f"Early life multiplier: {early_life_mul} ({'age <5' if early_life_mul > 1.0 else 'not specified'})")

        # Detect exposures and apply base weights
        exposures_detected = []

        # B1) Heavy metals
        if self._detect_heavy_metals(text_normalized):
            exposures_detected.append("Heavy metals")

            # Lead-specific: higher COG impact
            if self._detect_lead_specific(text_normalized):
                base_weights = {
                    "DTX": 0.45,
                    "IMM": 0.30,
                    "GA": 0.30,
                    "MITO": 0.25,
                    "COG": 0.35,  # Higher for lead
                    "CM": 0.15,
                    "SKN": 0.10
                }
                flags.append("Detected: Lead exposure (higher COG impact)")
            else:
                base_weights = {
                    "DTX": 0.45,
                    "IMM": 0.30,
                    "GA": 0.30,
                    "MITO": 0.25,
                    "COG": 0.25,
                    "CM": 0.15,
                    "SKN": 0.10
                }
                flags.append("Detected: Heavy metals (mercury/cadmium/arsenic/uranium)")

            # Apply multipliers
            for fa, base in base_weights.items():
                contribution = base * duration_mul * intensity_mul * early_life_mul
                weights[fa] = weights.get(fa, 0.0) + contribution

            # GA minimum: +0.20 even if duration_mul < 1.0
            if weights.get("GA", 0.0) < 0.20:
                weights["GA"] = 0.20
                flags.append("GA minimum applied: +0.20 (metals → dysbiosis/permeability)")

        # B2) Secondhand smoke
        if self._detect_smoke(text_normalized):
            exposures_detected.append("Secondhand smoke")
            flags.append("Detected: Secondhand smoke / early smoke exposure")

            base_weights = {
                "IMM": 0.30,
                "CM": 0.30,
                "DTX": 0.25,
                "GA": 0.20,
                "MITO": 0.15,
                "COG": 0.10
            }

            # Apply multipliers
            for fa, base in base_weights.items():
                contribution = base * duration_mul * intensity_mul * early_life_mul
                weights[fa] = weights.get(fa, 0.0) + contribution

        # B3) Pesticides/herbicides
        if self._detect_pesticides(text_normalized):
            exposures_detected.append("Pesticides/herbicides")
            flags.append("Detected: Pesticides/herbicides exposure")

            base_weights = {
                "DTX": 0.40,
                "IMM": 0.30,
                "COG": 0.30,
                "MITO": 0.30,
                "GA": 0.30
            }

            # Apply multipliers
            for fa, base in base_weights.items():
                contribution = base * duration_mul * intensity_mul * early_life_mul
                weights[fa] = weights.get(fa, 0.0) + contribution

        # B4) Mold/water damage
        if self._detect_mold(text_normalized):
            exposures_detected.append("Mold/water damage")
            flags.append("Detected: Mold/water-damaged buildings")

            base_weights = {
                "IMM": 0.45,
                "DTX": 0.35,
                "GA": 0.35,
                "SKN": 0.30,
                "MITO": 0.20,
                "COG": 0.20
            }

            # Apply multipliers
            for fa, base in base_weights.items():
                contribution = base * duration_mul * intensity_mul * early_life_mul
                weights[fa] = weights.get(fa, 0.0) + contribution

        # B5) Solvents/VOCs
        if self._detect_solvents(text_normalized):
            exposures_detected.append("Solvents/VOCs")
            flags.append("Detected: Solvents/VOCs exposure")

            base_weights = {
                "DTX": 0.35,
                "IMM": 0.25,
                "MITO": 0.25,
                "COG": 0.20,
                "GA": 0.20
            }

            # Apply multipliers
            for fa, base in base_weights.items():
                contribution = base * duration_mul * intensity_mul * early_life_mul
                weights[fa] = weights.get(fa, 0.0) + contribution

        # Safety check: ongoing unsafe living conditions
        if self._detect_ongoing_unsafe(text_normalized):
            flags.append("⚠️ SAFETY: Ongoing unsafe living conditions detected → consider environmental remediation")

        # Apply per-field caps
        for fa in weights:
            if fa == "GA":
                if weights[fa] > self.MAX_WEIGHT_GA:
                    flags.append(f"GA capped at +{self.MAX_WEIGHT_GA} (was +{weights[fa]:.3f})")
                    weights[fa] = self.MAX_WEIGHT_GA
            else:
                if weights[fa] > self.MAX_WEIGHT_GENERAL:
                    flags.append(f"{fa} capped at +{self.MAX_WEIGHT_GENERAL} (was +{weights[fa]:.3f})")
                    weights[fa] = self.MAX_WEIGHT_GENERAL

        # Remove zero weights
        weights = {fa: w for fa, w in weights.items() if abs(w) > 1e-6}

        # Summary
        if exposures_detected:
            flags.insert(0, f"Exposures detected: {', '.join(exposures_detected)}")
        else:
            flags.append("No recognized exposures detected in free text")

        return weights, flags

