"""
Ruleset for Field 27: Breastfeeding History

Evaluates early-life breastfeeding exposure and its impact on gut microbiome,
immune imprinting, and barrier function.

Radio: Yes | No | Not sure
If Yes: free text for duration (months)

Scoring:
- No breastfeeding → risk factors (GA +0.30, IMM +0.25, SKN +0.10)
- <3 months → limited imprint (GA +0.25, IMM +0.20, SKN +0.10)
- 3-5 months → modest protection (GA -0.05, IMM -0.05)
- 6-11 months → strong protection (GA -0.15, IMM -0.15, SKN -0.05)
- ≥12 months → durable protection (GA -0.20, IMM -0.20, SKN -0.10)
- Not sure → attenuated risk (GA +0.10, IMM +0.05)

Text modifiers:
- "exclusive" ≥3 mo → GA -0.05, IMM -0.05 (extra)
- "formula early" or "early solids <4 mo" → GA +0.10, IMM +0.10

Cross-field synergies:
- C-section + (No or <3 mo) → GA +0.10, IMM +0.10
- Early antibiotics (<2y) → GA +0.10, IMM +0.10
- Current skin disease + (No or <3 mo) → SKN +0.10

Per-field cap: -0.30 ≤ (GA, IMM, SKN) ≤ +0.35
"""

from typing import Dict, Tuple, List, Any, Optional
import re


class BreastfeedingRuleset:
    """Ruleset for evaluating breastfeeding history."""
    
    # Per-field caps
    FIELD_CAP_MIN = -0.30
    FIELD_CAP_MAX = 0.35
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, collapse whitespace."""
        text = text.lower()
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _extract_months(self, text: str) -> Optional[int]:
        """
        Extract breastfeeding duration in months from free text.

        Handles various formats:
        - "6 months", "6 mo", "6m"
        - "1 year", "1.5 years", "2 years"
        - "18 months"
        - "6-12 months" (take midpoint)

        Returns:
            Number of months, or None if not found
        """
        text_lower = text.lower()

        # Pattern 1: Range "X-Y months" (take midpoint) - check this FIRST
        match = re.search(r'(\d+)\s*-\s*(\d+)\s*(?:months?|mo\b)', text_lower)
        if match:
            start = int(match.group(1))
            end = int(match.group(2))
            return (start + end) // 2

        # Pattern 2: X months/mo/m
        match = re.search(r'(\d+(?:\.\d+)?)\s*(?:months?|mo\b|m\b)', text_lower)
        if match:
            return int(float(match.group(1)))

        # Pattern 3: X years/yr/y (convert to months)
        match = re.search(r'(\d+(?:\.\d+)?)\s*(?:years?|yrs?|y\b)', text_lower)
        if match:
            years = float(match.group(1))
            return int(years * 12)

        # Pattern 4: Just a number (assume months if <60)
        match = re.search(r'\b(\d+)\b', text_lower)
        if match:
            num = int(match.group(1))
            if num <= 60:  # Reasonable upper bound for months
                return num

        return None
    
    def _detect_exclusive(self, text: str) -> bool:
        """Detect if text mentions exclusive breastfeeding."""
        text_lower = text.lower()
        keywords = ['exclusive', 'exclusively', 'only breast']
        return any(kw in text_lower for kw in keywords)
    
    def _detect_early_formula_or_solids(self, text: str) -> bool:
        """Detect if text mentions early formula or early solids."""
        text_lower = text.lower()
        
        # Early formula
        if 'formula' in text_lower and any(kw in text_lower for kw in ['early', 'started', 'introduced', 'began']):
            return True
        
        # Early solids (before 4 months)
        if 'solid' in text_lower:
            # Look for age mentions
            match = re.search(r'(\d+)\s*(?:months?|mo\b)', text_lower)
            if match:
                months = int(match.group(1))
                if months < 4:
                    return True
            # Or keywords like "early"
            if 'early' in text_lower:
                return True
        
        return False
    
    def get_breastfeeding_weights(
        self,
        breastfeeding_data: Any,
        c_section: bool = False,
        early_antibiotics: bool = False,
        current_skin_disease: bool = False
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights based on breastfeeding history.
        
        Args:
            breastfeeding_data: Radio selection (Yes/No/Not sure) + optional free text
            c_section: Whether patient was born via C-section
            early_antibiotics: Whether patient had antibiotics before age 2
            current_skin_disease: Whether patient has current skin disease
        
        Returns:
            Tuple of (weights dict, flags list)
        """
        weights = {}
        flags = []
        
        # Parse input
        if not breastfeeding_data:
            return weights, flags
        
        text = str(breastfeeding_data).strip()
        
        # Split radio and free text (semicolon-separated)
        if ';' in text:
            radio, free_text = text.split(';', 1)
            radio = radio.strip()
            free_text = free_text.strip()
        else:
            radio = text
            free_text = ""
        
        # Normalize radio selection
        radio_lower = radio.lower()

        # Validate radio selection
        valid_responses = ['yes', 'no', 'not sure']
        if radio_lower not in valid_responses:
            flags.append(f"⚠️  Invalid radio selection: '{radio}' (expected Yes/No/Not sure)")
            return weights, flags

        # Extract months if free text provided
        bf_months = None
        if free_text:
            bf_months = self._extract_months(free_text)
            if bf_months is not None:
                flags.append(f"Extracted duration: {bf_months} months")

        # A) Primary decision tree
        if radio_lower == 'no':
            # No breastfeeding → risk factors
            weights['GA'] = weights.get('GA', 0) + 0.30
            weights['IMM'] = weights.get('IMM', 0) + 0.25
            weights['SKN'] = weights.get('SKN', 0) + 0.10
            flags.append("Base weights (No breastfeeding): GA +0.30, IMM +0.25, SKN +0.10")

        elif radio_lower == 'not sure':
            # Uncertain → attenuated risk
            weights['GA'] = weights.get('GA', 0) + 0.10
            weights['IMM'] = weights.get('IMM', 0) + 0.05
            flags.append("Base weights (Not sure): GA +0.10, IMM +0.05")

        elif radio_lower == 'yes':
            # Yes → duration-based scoring
            m = bf_months or 0

            if m < 3:
                # <3 months → limited imprint
                weights['GA'] = weights.get('GA', 0) + 0.25
                weights['IMM'] = weights.get('IMM', 0) + 0.20
                weights['SKN'] = weights.get('SKN', 0) + 0.10
                flags.append(f"Base weights (Yes, {m} months <3): GA +0.25, IMM +0.20, SKN +0.10")

            elif 3 <= m <= 5:
                # 3-5 months → modest protection
                weights['GA'] = weights.get('GA', 0) - 0.05
                weights['IMM'] = weights.get('IMM', 0) - 0.05
                flags.append(f"Base weights (Yes, {m} months 3-5): GA -0.05, IMM -0.05 (protective)")

            elif 6 <= m <= 11:
                # 6-11 months → strong protection
                weights['GA'] = weights.get('GA', 0) - 0.15
                weights['IMM'] = weights.get('IMM', 0) - 0.15
                weights['SKN'] = weights.get('SKN', 0) - 0.05
                flags.append(f"Base weights (Yes, {m} months 6-11): GA -0.15, IMM -0.15, SKN -0.05 (protective)")

            else:  # m >= 12
                # ≥12 months → durable protection
                weights['GA'] = weights.get('GA', 0) - 0.20
                weights['IMM'] = weights.get('IMM', 0) - 0.20
                weights['SKN'] = weights.get('SKN', 0) - 0.10
                flags.append(f"Base weights (Yes, {m} months ≥12): GA -0.20, IMM -0.20, SKN -0.10 (protective)")

        # B) Text modifiers
        if free_text:
            # Exclusive breastfeeding ≥3 mo
            if self._detect_exclusive(free_text) and (bf_months or 0) >= 3:
                weights['GA'] = weights.get('GA', 0) - 0.05
                weights['IMM'] = weights.get('IMM', 0) - 0.05
                flags.append("Detected: Exclusive breastfeeding ≥3 mo → GA -0.05, IMM -0.05 (extra protective)")

            # Early formula or early solids
            if self._detect_early_formula_or_solids(free_text):
                weights['GA'] = weights.get('GA', 0) + 0.10
                weights['IMM'] = weights.get('IMM', 0) + 0.10
                flags.append("Detected: Early formula/solids → GA +0.10, IMM +0.10")

        # C) Cross-field synergies
        # C-section + (No or <3 mo)
        if c_section and (radio_lower != 'yes' or (bf_months or 0) < 3):
            weights['GA'] = weights.get('GA', 0) + 0.10
            weights['IMM'] = weights.get('IMM', 0) + 0.10
            flags.append("Synergy: C-section + (No or <3 mo breastfeeding) → GA +0.10, IMM +0.10")

        # Early antibiotics
        if early_antibiotics:
            weights['GA'] = weights.get('GA', 0) + 0.10
            weights['IMM'] = weights.get('IMM', 0) + 0.10
            flags.append("Synergy: Early antibiotics (<2y) → GA +0.10, IMM +0.10")

        # Current skin disease + (No or <3 mo)
        if current_skin_disease and (radio_lower != 'yes' or (bf_months or 0) < 3):
            weights['SKN'] = weights.get('SKN', 0) + 0.10
            flags.append("Synergy: Current skin disease + (No or <3 mo) → SKN +0.10")

        # Apply per-field caps
        for fa in list(weights.keys()):
            if weights[fa] > self.FIELD_CAP_MAX:
                flags.append(f"⚠️  {fa} capped at +{self.FIELD_CAP_MAX:.2f} (was {weights[fa]:+.3f})")
                weights[fa] = self.FIELD_CAP_MAX
            elif weights[fa] < self.FIELD_CAP_MIN:
                flags.append(f"⚠️  {fa} capped at {self.FIELD_CAP_MIN:.2f} (was {weights[fa]:+.3f})")
                weights[fa] = self.FIELD_CAP_MIN

        # Remove zero weights
        weights = {fa: w for fa, w in weights.items() if w != 0}

        return weights, flags

