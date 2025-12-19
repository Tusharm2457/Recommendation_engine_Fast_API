"""
Field 29: Tooth Sensitivity Ruleset

Evaluates tooth sensitivity using NLP-based trigger detection and mechanistic scoring.

Radio: Yes/No
If Yes → free text describing triggers/context

Mechanisms detected:
- Acid/erosion pattern (reflux, acidic foods/drinks)
- Mechanical/occlusal stress (bruxism, grinding, aggressive brushing)
- Periodontal/gum recession (bleeding gums, receding gums)
- Xerostomia/low remineralization (dry mouth, medications)
- Nutrient factors (low calcium, vitamin D deficiency)

Protective factors:
- Night guard, desensitizing toothpaste, fluoride varnish, reflux control

Per-field cap: All domains ≤ +0.8
"""

from typing import Dict, List, Tuple, Any
import re


class ToothSensitivityRuleset:
    """Ruleset for evaluating tooth sensitivity."""
    
    # Per-field cap (all domains)
    MAX_WEIGHT = 0.8
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for keyword matching."""
        text_lower = text.lower()
        # Collapse whitespace
        text_normalized = re.sub(r'\s+', ' ', text_lower).strip()
        return text_normalized
    
    def _detect_acid_erosion(self, text: str) -> bool:
        """Detect acid/erosion pattern keywords."""
        text_lower = text.lower()
        
        keywords = [
            r'\bcold\b', r'\bsour\b', r'\bacidic\b', r'\breflux\b',
            r'\bheartburn\b', r'\bgerd\b', r'\bvomiting\b', r'\bbulimia\b',
            r'\bcitrus\b', r'\blemon\b', r'\borange juice\b',
            r'\bsoda\b', r'\bseltzer\b', r'\bsports drinks?\b',
            r'\benergy drinks?\b', r'\bvinegar\b', r'\bwine\b',
            r'\bacid taste\b', r'\bair hurts\b'
        ]
        
        for keyword in keywords:
            if re.search(keyword, text_lower):
                return True
        return False
    
    def _detect_mechanical_stress(self, text: str) -> bool:
        """Detect mechanical/occlusal stress keywords."""
        text_lower = text.lower()
        
        keywords = [
            r'\bbruxism\b', r'\bgrinding\b', r'\bclenching\b',
            r'\bgrind my teeth\b', r'\bclench my jaw\b',
            r'\bcracked tooth\b', r'\bchipped tooth\b',
            r'\bwhitening\b', r'\bbleaching\b',
            r'\baggressive brushing\b', r'\bhard brushing\b',
            r'\bbiting\b', r'\bpressure\b'
        ]
        
        for keyword in keywords:
            if re.search(keyword, text_lower):
                return True
        return False
    
    def _detect_periodontal(self, text: str) -> bool:
        """Detect periodontal/gum recession keywords."""
        text_lower = text.lower()

        keywords = [
            r'\breceding gums?\b', r'\bgums? recede\b', r'\bgum recession\b',
            r'\bbleeding gums?\b', r'\bgums? bleed\b', r'\bbleed on brushing\b',
            r'\bgingivitis\b', r'\bperiodontitis\b',
            r'\bgum disease\b', r'\bperiodontal\b'
        ]

        for keyword in keywords:
            if re.search(keyword, text_lower):
                return True
        return False
    
    def _detect_xerostomia(self, text: str) -> bool:
        """Detect xerostomia/dry mouth keywords."""
        text_lower = text.lower()
        
        keywords = [
            r'\bdry mouth\b', r'\bxerostomia\b',
            r'\blow saliva\b', r'\bmouth breathing\b',
            r'\bantihistamines?\b', r'\banticholinergics?\b',
            r'\bssris?\b', r'\bantidepressants?\b'
        ]
        
        for keyword in keywords:
            if re.search(keyword, text_lower):
                return True
        return False
    
    def _detect_nutrient_factors(self, text: str) -> bool:
        """Detect nutrient deficiency keywords."""
        text_lower = text.lower()
        
        keywords = [
            r'\blow calcium\b', r'\bvitamin d deficiency\b',
            r'\blow vitamin d\b', r'\blow fluoride\b',
            r'\bwater filter\b', r'\bdefluorinated\b'
        ]
        
        for keyword in keywords:
            if re.search(keyword, text_lower):
                return True
        return False
    
    def _detect_explicit_reflux(self, text: str) -> bool:
        """Detect explicit reflux link to tooth sensitivity."""
        text_lower = text.lower()
        
        # Look for phrases that explicitly link reflux to teeth
        patterns = [
            r'sensitive.*from.*reflux',
            r'reflux.*sensitive',
            r'acid.*at night',
            r'teeth.*reflux',
            r'reflux.*teeth'
        ]
        
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True
        return False
    
    def _detect_protective_factors(self, text: str) -> bool:
        """Detect protective factors (night guard, desensitizing toothpaste, etc.)."""
        text_lower = text.lower()
        
        keywords = [
            r'\bnight guard\b', r'\bmouth guard\b',
            r'\bdesensitizing toothpaste\b', r'\bsensodyne\b',
            r'\bfluoride varnish\b', r'\bfluoride treatment\b',
            r'\breflux under control\b', r'\breflux controlled\b',
            r'\bppi\b', r'\bomeprazole\b', r'\bpantoprazole\b'
        ]
        
        for keyword in keywords:
            if re.search(keyword, text_lower):
                return True
        return False

    def get_tooth_sensitivity_weights(
        self,
        sensitivity_data: Any,
        has_chronic_gerd: bool = False
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights for tooth sensitivity.

        Args:
            sensitivity_data: Radio (Yes/No) + optional free text (semicolon-separated)
            has_chronic_gerd: Whether patient has chronic GERD (from Phase 2 data)

        Returns:
            Tuple of (weights dict, flags list)
        """
        weights: Dict[str, float] = {}
        flags: List[str] = []

        # Handle empty/None input
        if not sensitivity_data or not str(sensitivity_data).strip():
            return weights, flags

        # Parse input: "Radio; free text"
        sensitivity_str = str(sensitivity_data).strip()
        parts = sensitivity_str.split(';', 1)
        radio = parts[0].strip()
        free_text = parts[1].strip() if len(parts) > 1 else ""

        # Validate radio selection
        if radio not in ["Yes", "No"]:
            flags.append(f"Invalid radio selection: '{radio}' (expected Yes/No)")
            return weights, flags

        # If No, return empty weights
        if radio == "No":
            return weights, flags

        # If Yes but no free text, apply minimal base weights
        if not free_text:
            flags.append("Radio is 'Yes' but no free text provided - applying minimal base weights")
            weights["IMM"] = 0.10  # Generic sensitivity
            return weights, flags

        # Normalize text
        text_normalized = self._normalize_text(free_text)

        # Track detected mechanisms
        mechanisms_detected = []

        # B1) Acid/erosion pattern
        if self._detect_acid_erosion(text_normalized):
            mechanisms_detected.append("Acid/erosion")
            flags.append("Detected: Acid/erosion pattern (reflux, acidic foods/drinks)")

            weights["GA"] = weights.get("GA", 0.0) + 0.20  # Aerodigestive link
            weights["IMM"] = weights.get("IMM", 0.0) + 0.10  # Exposed dentin inflammation
            weights["DTX"] = weights.get("DTX", 0.0) + 0.10  # Acidic sodas/energy drinks

            # Extra GA if chronic GERD
            if has_chronic_gerd:
                weights["GA"] = weights.get("GA", 0.0) + 0.10
                flags.append("Cross-field synergy: Chronic GERD → GA +0.10")

        # B2) Mechanical/occlusal stress
        if self._detect_mechanical_stress(text_normalized):
            mechanisms_detected.append("Mechanical stress")
            flags.append("Detected: Mechanical/occlusal stress (bruxism, grinding, whitening)")

            weights["STR"] = weights.get("STR", 0.0) + 0.10  # Sleep-stress/parasomnias
            weights["IMM"] = weights.get("IMM", 0.0) + 0.10  # Dentin/pulp irritation
            weights["COG"] = weights.get("COG", 0.0) + 0.05  # Pain → sleep disruption

        # B3) Periodontal/gum recession
        if self._detect_periodontal(text_normalized):
            mechanisms_detected.append("Periodontal")
            flags.append("Detected: Periodontal/gum recession (bleeding gums, receding gums)")

            weights["IMM"] = weights.get("IMM", 0.0) + 0.15  # Gingival inflammation
            weights["CM"] = weights.get("CM", 0.0) + 0.05  # Systemic CM links
            weights["GA"] = weights.get("GA", 0.0) + 0.10  # Swallowed LPS

        # B4) Xerostomia/low remineralization
        if self._detect_xerostomia(text_normalized):
            mechanisms_detected.append("Xerostomia")
            flags.append("Detected: Xerostomia/dry mouth (medications, mouth breathing)")

            weights["IMM"] = weights.get("IMM", 0.0) + 0.10  # Mucosal vulnerability
            weights["GA"] = weights.get("GA", 0.0) + 0.05  # Swallowing/bolus issues

        # B5) Nutrient factors
        if self._detect_nutrient_factors(text_normalized):
            mechanisms_detected.append("Nutrient deficiency")
            flags.append("Detected: Nutrient factors (low calcium, vitamin D deficiency)")

            weights["HRM"] = weights.get("HRM", 0.0) + 0.05  # Vitamin D/calcium
            weights["IMM"] = weights.get("IMM", 0.0) + 0.05  # Deficiency susceptibility

        # B6) Explicit reflux link
        if self._detect_explicit_reflux(text_normalized):
            mechanisms_detected.append("Explicit reflux link")
            flags.append("Detected: Explicit reflux link to tooth sensitivity")

            weights["GA"] = weights.get("GA", 0.0) + 0.10  # Extra GA (beyond B1)

        # C) Protective factors (subtract)
        if self._detect_protective_factors(text_normalized):
            flags.append("Detected: Protective factors (night guard, desensitizing toothpaste, reflux control)")

            # Subtract small amounts (cap at -0.10 total)
            weights["IMM"] = weights.get("IMM", 0.0) - 0.05
            weights["GA"] = weights.get("GA", 0.0) - 0.05

        # Apply per-field cap (all domains ≤ +0.8)
        for fa in list(weights.keys()):
            if weights[fa] > self.MAX_WEIGHT:
                flags.append(f"{fa} capped at +{self.MAX_WEIGHT} (was +{weights[fa]:.3f})")
                weights[fa] = self.MAX_WEIGHT

        # Remove zero/negative weights that went below zero
        weights = {fa: w for fa, w in weights.items() if w > 1e-6}

        # Summary
        if mechanisms_detected:
            flags.insert(0, f"Mechanisms detected: {', '.join(mechanisms_detected)}")
        else:
            flags.append("No recognized mechanisms detected in free text")

        return weights, flags

