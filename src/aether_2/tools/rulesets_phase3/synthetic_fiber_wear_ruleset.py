"""
Ruleset for Field 33: Regular Synthetic Fiber Wear

Multi-select with optional free text for evaluating synthetic fiber exposure.

Decision tree:
- A) Baseline contribution per selection (stacking)
  - Polyester/Nylon/Acrylic/Spandex → DTX +0.05, SKN +0.05
  - Rayon/Acetate → SKN +0.05, DTX +0.03
- B) Heat/Sweat pathway add-ons (from free text)
  - Heavy sweating/hot/humid work/exercise → DTX +0.10, SKN +0.10
  - Plus GA +0.10 if dermatitis/rash detected
- C) Water-repellent/stain-resistant gear (DWR)
  - Water-resistant/stain-repellent/outdoor shell → DTX +0.10, SKN +0.05
- D) Known/suspected textile allergy
  - Disperse dye allergy → SKN +0.20, IMM +0.10
  - Spandex/elastane reactions at elastic bands → SKN +0.10, IMM +0.05
- E) Air/indoor chemical load synergy
  - Fragrance/VOCs/poor ventilation + daily synthetics → DTX +0.05
- F) New & unwashed apparel
  - Wearing new/unwashed items regularly → SKN +0.05, DTX +0.05

Per-field cap: All domains ≤ +1.0
"""

from typing import Dict, List, Tuple, Any
import re


class SyntheticFiberWearRuleset:
    """Ruleset for evaluating synthetic fiber wear exposure."""
    
    # Per-field cap
    MAX_WEIGHT = 1.0
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for pattern matching."""
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def _detect_heavy_sweating(self, text: str) -> bool:
        """Detect heavy sweating or hot/humid work/exercise."""
        patterns = [
            r'\bheavy sweat',
            r'\bsweat heavily',
            r'\bsweat a lot',
            r'\bhot\b.*\bhumid\b',
            r'\bhumid\b.*\bhot\b',
            r'\bworkout',
            r'\bexercise',
            r'\bgym\b',
            r'\brun(ning)?\b',
            r'\bhiking\b',
            r'\bsports?\b',
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _detect_dermatitis_rash(self, text: str) -> bool:
        """Detect dermatitis or rash."""
        patterns = [
            r'\bdermatitis\b',
            r'\brash\b',
            r'\bitch(y|ing)?\b',
            r'\bhives\b',
            r'\beczema\b',
            r'\birrit(ation|ated)\b',
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _detect_water_repellent(self, text: str) -> bool:
        """Detect water-repellent or stain-resistant gear."""
        patterns = [
            r'\bwater[- ]?resistant\b',
            r'\bwater[- ]?repellent\b',
            r'\bstain[- ]?resistant\b',
            r'\bstain[- ]?repellent\b',
            r'\boutdoor shell\b',
            r'\brain jacket\b',
            r'\bDWR\b',
            r'\bhiking jacket\b',
            r'\bski jacket\b',
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _detect_disperse_dye_allergy(self, text: str) -> bool:
        """Detect disperse dye allergy."""
        patterns = [
            r'\bdisperse dye\b',
            r'\bdisperse blue\b',
            r'\bpatch[- ]?test\b.*\ballerg',
            r'\ballerg.*\bpatch[- ]?test\b',
            r'\btextile allerg',
            r'\bfabric allerg',
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _detect_spandex_reaction(self, text: str) -> bool:
        """Detect spandex/elastane reactions at elastic bands."""
        patterns = [
            r'\bspandex\b.*\breaction\b',
            r'\breaction\b.*\bspandex\b',
            r'\belastane\b.*\breaction\b',
            r'\breaction\b.*\belastane\b',
            r'\belastic band',
            r'\bwaistband\b.*\brash\b',
            r'\brash\b.*\bwaistband\b',
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False
    
    def _detect_new_unwashed(self, text: str) -> bool:
        """Detect wearing new/unwashed items regularly."""
        patterns = [
            r'\bnew\b.*\bunwashed\b',
            r'\bunwashed\b.*\bnew\b',
            r'\bwear.*\bnew\b.*\bwithout wash',
            r'\bwithout wash.*\bnew\b',
            r'\bbrand[- ]?new\b',
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return True
        return False

    def get_synthetic_fiber_wear_weights(
        self,
        fiber_selections: Any,
        followup_text: str = "",
        has_fragrance_vocs: bool = False,
        has_poor_ventilation: bool = False
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights for synthetic fiber wear.

        Args:
            fiber_selections: Multi-select input (list or comma-separated string)
            followup_text: Optional free text explanation
            has_fragrance_vocs: Whether fragrance/VOCs detected from other fields
            has_poor_ventilation: Whether poor ventilation detected from other fields

        Returns:
            Tuple of (weights dict, flags list)
        """
        weights = {}
        flags = []

        # Parse fiber selections
        selected_fibers = []
        if isinstance(fiber_selections, list):
            selected_fibers = [str(f).strip() for f in fiber_selections if f]
        elif isinstance(fiber_selections, str) and fiber_selections.strip():
            # Split by comma or semicolon
            selected_fibers = [f.strip() for f in re.split(r'[,;]', fiber_selections) if f.strip()]

        if not selected_fibers:
            return {}, []

        # Normalize text
        followup_norm = self._normalize_text(followup_text)

        # A) Baseline contribution per selection (stacking)
        polyester_nylon_acrylic_spandex = ["polyester", "nylon", "acrylic", "spandex", "lycra", "elastane"]
        rayon_acetate = ["rayon", "acetate"]

        for fiber in selected_fibers:
            fiber_norm = self._normalize_text(fiber)

            # Check if it's a known fiber type
            if any(f in fiber_norm for f in polyester_nylon_acrylic_spandex):
                weights["DTX"] = weights.get("DTX", 0) + 0.05
                weights["SKN"] = weights.get("SKN", 0) + 0.05
                flags.append(f"Synthetic fiber: {fiber} → DTX +0.05, SKN +0.05")
            elif any(f in fiber_norm for f in rayon_acetate):
                weights["SKN"] = weights.get("SKN", 0) + 0.05
                weights["DTX"] = weights.get("DTX", 0) + 0.03
                flags.append(f"Semi-synthetic fiber: {fiber} → SKN +0.05, DTX +0.03")

        # B) Heat/Sweat pathway add-ons
        if self._detect_heavy_sweating(followup_norm):
            weights["DTX"] = weights.get("DTX", 0) + 0.10
            weights["SKN"] = weights.get("SKN", 0) + 0.10
            flags.append("Heat/sweat pathway: Heavy sweating/hot/humid work/exercise → DTX +0.10, SKN +0.10")

            # Check for dermatitis/rash
            if self._detect_dermatitis_rash(followup_norm):
                weights["GA"] = weights.get("GA", 0) + 0.10
                flags.append("Skin-gut axis: Dermatitis/rash + sweating → GA +0.10")

        # C) Water-repellent/stain-resistant gear (DWR)
        if self._detect_water_repellent(followup_norm):
            weights["DTX"] = weights.get("DTX", 0) + 0.10
            weights["SKN"] = weights.get("SKN", 0) + 0.05
            flags.append("PFAS exposure: Water-resistant/stain-repellent gear → DTX +0.10, SKN +0.05")

        # D) Known/suspected textile allergy
        if self._detect_disperse_dye_allergy(followup_norm):
            weights["SKN"] = weights.get("SKN", 0) + 0.20
            weights["IMM"] = weights.get("IMM", 0) + 0.10
            flags.append("Textile allergy: Disperse dye allergy → SKN +0.20, IMM +0.10")

        if self._detect_spandex_reaction(followup_norm):
            weights["SKN"] = weights.get("SKN", 0) + 0.10
            weights["IMM"] = weights.get("IMM", 0) + 0.05
            flags.append("Textile allergy: Spandex/elastane reaction at elastic bands → SKN +0.10, IMM +0.05")

        # E) Air/indoor chemical load synergy
        if (has_fragrance_vocs or has_poor_ventilation) and len(selected_fibers) > 0:
            weights["DTX"] = weights.get("DTX", 0) + 0.05
            flags.append("Air/indoor chemical synergy: Fragrance/VOCs/poor ventilation + daily synthetics → DTX +0.05")

        # F) New & unwashed apparel
        if self._detect_new_unwashed(followup_norm):
            weights["SKN"] = weights.get("SKN", 0) + 0.05
            weights["DTX"] = weights.get("DTX", 0) + 0.05
            flags.append("New/unwashed apparel: Wearing new items without washing → SKN +0.05, DTX +0.05")

        # Apply per-field cap
        for domain in weights:
            if weights[domain] > self.MAX_WEIGHT:
                weights[domain] = self.MAX_WEIGHT

        # Remove zero/negative weights
        weights = {k: v for k, v in weights.items() if v > 0}

        return weights, flags

