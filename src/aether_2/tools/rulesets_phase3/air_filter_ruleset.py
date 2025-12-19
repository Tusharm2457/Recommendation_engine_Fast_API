"""
Ruleset for Air Filter Usage (Field 37).

Evaluates air filter usage and effectiveness for indoor air quality.
"""

from typing import Dict, List, Tuple
import re


class AirFilterRuleset:
    """
    Ruleset for evaluating air filter usage and effectiveness.
    
    Field format: Radio (Yes | No) with optional free text for brand/model
    Example: "Yes; Coway Airmega 400S HEPA with activated carbon"
    """
    
    # Per-field caps
    MAX_DTX = 0.60
    MAX_IMM = 0.60
    MAX_GA = 0.60
    
    def __init__(self):
        """Initialize the air filter ruleset."""
        pass
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, collapse whitespace."""
        if not text:
            return ""
        # Lowercase
        text = text.lower()
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _detect_hepa(self, text: str) -> bool:
        """Detect HEPA filtration (True HEPA, H13, H14)."""
        keywords = ["hepa", "true hepa", "h13", "h14", "merv"]
        return any(kw in text for kw in keywords)
    
    def _detect_activated_carbon(self, text: str) -> bool:
        """Detect activated carbon/charcoal filtration."""
        keywords = ["activated carbon", "charcoal", "carbon filter", "sorbent", "voc filter"]
        return any(kw in text for kw in keywords)
    
    def _detect_electronic_ozone_risk(self, text: str) -> bool:
        """Detect electronic/ozone-risk technologies without certification."""
        keywords = ["ionizer", "plasma", "peco", "pco", "ozone", "electrostatic"]
        has_risky_tech = any(kw in text for kw in keywords)
        
        # Check for safety certifications
        has_cert = any(cert in text for cert in ["ul 2998", "ul2998", "carb certified", "zero ozone"])
        
        return has_risky_tech and not has_cert
    
    def _detect_ul2998_or_carb(self, text: str) -> bool:
        """Detect UL 2998 or CARB certification."""
        keywords = ["ul 2998", "ul2998", "carb certified", "zero ozone"]
        return any(kw in text for kw in keywords)
    
    def _detect_diy_filter(self, text: str) -> bool:
        """Detect DIY Corsi-Rosenthal box fan filter."""
        keywords = ["diy", "corsi", "rosenthal", "box fan", "merv 13", "merv13"]
        return any(kw in text for kw in keywords)
    
    def _detect_poor_maintenance(self, text: str) -> bool:
        """Detect poor maintenance signals."""
        keywords = [
            "filter light on", "haven't changed", "havent changed",
            "12 months", "1 year", "never changed", "old filter"
        ]
        return any(kw in text for kw in keywords)
    
    def _detect_adequate_cadr(self, text: str) -> bool:
        """
        Detect adequate CADR (Clean Air Delivery Rate).
        
        This is a simplified heuristic - in production, you'd look up
        the actual CADR from AHAM Verifide database and compare to room size.
        For now, we'll use brand reputation as a proxy.
        """
        # High-quality brands known for adequate CADR
        quality_brands = [
            "coway", "blueair", "levoit", "winix", "honeywell",
            "dyson", "iqair", "austin air", "rabbit air", "molekule"
        ]
        return any(brand in text for brand in quality_brands)
    
    def get_air_filter_weights(
        self,
        choice: str,
        brand_model_text: str = "",
        has_mold_dampness: bool = False,
        has_poor_ventilation: bool = False,
        has_gas_stove: bool = False,
        has_wildfire_smoke: bool = False
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights for air filter usage.
        
        Args:
            choice: Radio selection (Yes | No)
            brand_model_text: Optional free text for brand/model
            has_mold_dampness: Whether mold/dampness is flagged (from Field 30)
            has_poor_ventilation: Whether poor ventilation/VOC is flagged (from Field 30)
            has_gas_stove: Whether gas stove is present (from Field 30)
            has_wildfire_smoke: Whether wildfire smoke exposure is present
            
        Returns:
            Tuple of (weights dict, flags list)
        """
        weights: Dict[str, float] = {}
        flags: List[str] = []
        
        # Normalize inputs
        choice_norm = self._normalize_text(choice)
        text_norm = self._normalize_text(brand_model_text)
        
        # Branch 1: No air filter in use
        if not choice_norm or choice_norm == "no":
            # No filter AND mold/dampness
            if has_mold_dampness:
                weights["IMM"] = weights.get("IMM", 0) + 0.30
                weights["DTX"] = weights.get("DTX", 0) + 0.20
                weights["GA"] = weights.get("GA", 0) + 0.20
                flags.append("No air filter with mold/dampness → IMM +0.30, DTX +0.20, GA +0.20")
            
            # No filter AND poor ventilation/VOC
            if has_poor_ventilation:
                weights["DTX"] = weights.get("DTX", 0) + 0.10
                flags.append("No air filter with poor ventilation/VOC → DTX +0.10")
            
            # No filter AND gas stove
            if has_gas_stove:
                weights["IMM"] = weights.get("IMM", 0) + 0.10
                flags.append("No air filter with gas stove → IMM +0.10 (NO₂ exposure)")

            # Apply caps and remove zero/negative weights
            for domain in list(weights.keys()):
                if domain == "DTX":
                    weights[domain] = min(weights[domain], self.MAX_DTX)
                elif domain == "IMM":
                    weights[domain] = min(weights[domain], self.MAX_IMM)
                elif domain == "GA":
                    weights[domain] = min(weights[domain], self.MAX_GA)

                if weights[domain] <= 0:
                    del weights[domain]

            return weights, flags

        # Branch 2: Yes air filter in use
        if choice_norm == "yes":
            flags.append("Air filter in use")

            # Step 2.1 - Technology class & certifications
            has_hepa = self._detect_hepa(text_norm)
            has_carbon = self._detect_activated_carbon(text_norm)
            has_ozone_risk = self._detect_electronic_ozone_risk(text_norm)
            has_cert = self._detect_ul2998_or_carb(text_norm)
            is_diy = self._detect_diy_filter(text_norm)
            has_poor_maint = self._detect_poor_maintenance(text_norm)
            has_adequate_cadr = self._detect_adequate_cadr(text_norm)

            # True HEPA present
            if has_hepa:
                weights["IMM"] = weights.get("IMM", 0) - 0.15
                weights["DTX"] = weights.get("DTX", 0) - 0.10
                flags.append("True HEPA filtration → IMM -0.15, DTX -0.10")

            # Activated carbon present
            if has_carbon:
                weights["DTX"] = weights.get("DTX", 0) - 0.10
                flags.append("Activated carbon filtration → DTX -0.10")

            # UL 2998 or CARB certified (for electronic units)
            if has_cert:
                weights["IMM"] = weights.get("IMM", 0) - 0.05
                weights["DTX"] = weights.get("DTX", 0) - 0.05
                flags.append("UL 2998/CARB certified → IMM -0.05, DTX -0.05")

            # Electronic/ionizer/ozone risk without certification
            if has_ozone_risk:
                weights["IMM"] = weights.get("IMM", 0) + 0.20
                weights["DTX"] = weights.get("DTX", 0) + 0.20
                flags.append("Electronic/ionizer without UL2998/CARB → IMM +0.20, DTX +0.20 (ozone risk)")

            # Step 2.2 - Sizing/effectiveness (CADR)
            if has_adequate_cadr and not has_ozone_risk:
                weights["IMM"] = weights.get("IMM", 0) - 0.10
                weights["DTX"] = weights.get("DTX", 0) - 0.10
                flags.append("Adequate CADR (quality brand) → IMM -0.10, DTX -0.10")
            elif not has_adequate_cadr and not is_diy and text_norm:
                # Only penalize if brand/model provided but not recognized
                weights["IMM"] = weights.get("IMM", 0) + 0.10
                flags.append("Unverifiable/undersized CADR → IMM +0.10")

            # Step 2.3 - Contextual synergies
            # Mold/dampness + HEPA
            if has_mold_dampness and has_hepa:
                weights["IMM"] = weights.get("IMM", 0) - 0.10
                weights["GA"] = weights.get("GA", 0) - 0.05
                flags.append("Mold/dampness + HEPA → IMM -0.10, GA -0.05 (spore reduction)")

            # Wildfire smoke context
            if has_wildfire_smoke:
                if not has_hepa and not is_diy:
                    weights["DTX"] = weights.get("DTX", 0) + 0.20
                    weights["IMM"] = weights.get("IMM", 0) + 0.10
                    flags.append("Wildfire smoke without HEPA → DTX +0.20, IMM +0.10")
                elif has_hepa or is_diy:
                    weights["DTX"] = weights.get("DTX", 0) - 0.10
                    weights["IMM"] = weights.get("IMM", 0) - 0.05
                    flags.append("Wildfire smoke + HEPA/DIY → DTX -0.10, IMM -0.05")

            # DIY Corsi-Rosenthal box
            if is_diy:
                weights["IMM"] = weights.get("IMM", 0) - 0.10
                weights["DTX"] = weights.get("DTX", 0) - 0.10
                flags.append("DIY Corsi-Rosenthal box → IMM -0.10, DTX -0.10")

            # Step 2.4 - Maintenance signals
            if has_poor_maint:
                weights["IMM"] = weights.get("IMM", 0) + 0.10
                weights["DTX"] = weights.get("DTX", 0) + 0.10
                flags.append("Poor maintenance (>12 months/filter light on) → IMM +0.10, DTX +0.10")

            # Step 2.5 - Gut axis hook
            if has_hepa and has_carbon and not has_ozone_risk:
                weights["GA"] = weights.get("GA", 0) - 0.10
                flags.append("HEPA + carbon (adequate device) → GA -0.10 (reduced inhaled irritants)")

            # Damp/mold context + no filter
            if has_mold_dampness and not has_hepa and not is_diy:
                weights["GA"] = weights.get("GA", 0) + 0.20
                flags.append("Mold/dampness without HEPA → GA +0.20")

            # Apply caps and remove zero/negative weights
            for domain in list(weights.keys()):
                if domain == "DTX":
                    weights[domain] = max(min(weights[domain], self.MAX_DTX), -self.MAX_DTX)
                elif domain == "IMM":
                    weights[domain] = max(min(weights[domain], self.MAX_IMM), -self.MAX_IMM)
                elif domain == "GA":
                    weights[domain] = max(min(weights[domain], self.MAX_GA), -self.MAX_GA)

                if weights[domain] == 0:
                    del weights[domain]

            return weights, flags

        # Invalid choice
        return {}, []

