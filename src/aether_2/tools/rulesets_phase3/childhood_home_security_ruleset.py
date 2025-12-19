"""
Ruleset for Field 26: Childhood Home Security

Evaluates early-life home environment security and adversity.
Radio: Yes (happy/secure) | No (not happy/secure) | Not sure
If No → optional free text for adversity details

Scoring:
- Base weights by radio selection (Yes = protective, No = risk, Not sure = mild risk)
- Free-text amplifiers for severity tiers (Tier A = severe, Tier B = moderate)
- Per-field caps applied

Author: Aether AI Engine
"""

from typing import Dict, List, Tuple, Any
import re


class ChildhoodHomeSecurityRuleset:
    """
    Ruleset for evaluating childhood home security and early-life adversity.
    
    Uses radio selection + optional free text with NLP-based severity detection.
    """
    
    # Tier A: Severe, chronic adversity keywords
    TIER_A_KEYWORDS = [
        # Physical/sexual/emotional abuse
        'physical abuse', 'sexual abuse', 'emotional abuse', 'abuse', 'abused', 'beaten', 'hit',
        'molested', 'raped', 'assaulted', 'violated',
        # Violence
        'violence', 'violent', 'domestic violence', 'witnessed violence',
        # Neglect
        'neglect', 'neglected', 'abandoned', 'abandonment', 'left alone', 'no supervision',
        # Caregiver issues
        'alcoholic parent', 'drug addict parent', 'addiction', 'substance abuse',
        'parent mental illness', 'parent psychosis', 'parent depression severe',
        'parent suicide', 'parent hospitalized',
        # Incarceration
        'parent in prison', 'parent in jail', 'incarcerated', 'imprisoned',
        # Homelessness/foster care
        'homeless', 'homelessness', 'foster care', 'foster home', 'orphanage',
        'removed from home', 'child protective services', 'cps'
    ]
    
    # Tier B: Moderate, persistent stressors keywords
    TIER_B_KEYWORDS = [
        # Instability/moves
        'frequent moves', 'moved a lot', 'moved', 'unstable', 'instability', 'chaotic',
        'no stability', 'constant change',
        # Conflict
        'high conflict', 'constant fighting', 'parents fought', 'yelling', 'screaming',
        'arguments', 'tension', 'hostile', 'angry household',
        # Financial insecurity
        'financial stress', 'financial insecurity', 'poverty', 'poor', 'no money',
        'food insecurity', 'hungry', 'not enough food', 'struggled financially',
        # Bullying
        'bullied', 'bullying', 'picked on', 'teased', 'harassed'
    ]
    
    # Per-field cap
    FIELD_CAP = 1.0
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for keyword matching."""
        if not text:
            return ""
        # Lowercase
        text = text.lower()
        # Collapse multiple spaces
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _keyword_match(self, text: str, keyword: str) -> bool:
        """
        Match keyword in text using word boundaries for single words,
        substring matching for multi-word phrases.
        """
        if not text or not keyword:
            return False
        
        # Multi-word phrase: use substring matching
        if ' ' in keyword:
            return keyword in text
        
        # Single word: use word boundary matching
        pattern = r'\b' + re.escape(keyword) + r'\b'
        return bool(re.search(pattern, text))
    
    def _detect_severity_tier(self, text: str) -> str:
        """
        Detect severity tier from free text.
        
        Returns:
            'tier_a' for severe chronic adversity
            'tier_b' for moderate persistent stressors
            'none' if no keywords detected
        """
        if not text:
            return 'none'
        
        normalized_text = self._normalize_text(text)
        
        # Check Tier A first (highest severity)
        for keyword in self.TIER_A_KEYWORDS:
            if self._keyword_match(normalized_text, keyword):
                return 'tier_a'
        
        # Check Tier B
        for keyword in self.TIER_B_KEYWORDS:
            if self._keyword_match(normalized_text, keyword):
                return 'tier_b'
        
        return 'none'
    
    def get_childhood_home_security_weights(
        self,
        childhood_home_data: Any
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights based on childhood home security.
        
        Args:
            childhood_home_data: Radio selection (Yes/No/Not sure) + optional free text
        
        Returns:
            Tuple of (weights dict, flags list)
        """
        weights = {}
        flags = []
        
        # Parse input
        if not childhood_home_data:
            return weights, flags
        
        text = str(childhood_home_data).strip()
        
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

        # Validate free text length (if provided)
        if free_text and len(free_text) > 2000:
            flags.append(f"⚠️  Free text truncated from {len(free_text)} to 2000 chars")
            free_text = free_text[:2000]

        # Base weights by radio selection
        if radio_lower == 'no':
            # Not happy/secure → risk factors
            weights['STR'] = weights.get('STR', 0) + 0.6
            weights['COG'] = weights.get('COG', 0) + 0.4
            weights['GA'] = weights.get('GA', 0) + 0.3
            weights['IMM'] = weights.get('IMM', 0) + 0.2
            weights['HRM'] = weights.get('HRM', 0) + 0.2
            weights['MITO'] = weights.get('MITO', 0) + 0.2
            weights['SKN'] = weights.get('SKN', 0) + 0.1
            flags.append("Base weights (No - not happy/secure): STR +0.6, COG +0.4, GA +0.3, IMM +0.2, HRM +0.2, MITO +0.2, SKN +0.1")

        elif radio_lower == 'not sure':
            # Uncertain → mild risk factors
            weights['STR'] = weights.get('STR', 0) + 0.3
            weights['COG'] = weights.get('COG', 0) + 0.2
            weights['GA'] = weights.get('GA', 0) + 0.2
            weights['IMM'] = weights.get('IMM', 0) + 0.1
            weights['HRM'] = weights.get('HRM', 0) + 0.1
            weights['MITO'] = weights.get('MITO', 0) + 0.1
            flags.append("Base weights (Not sure): STR +0.3, COG +0.2, GA +0.2, IMM +0.1, HRM +0.1, MITO +0.1")

        elif radio_lower == 'yes':
            # Happy/secure → protective factors (negative weights)
            weights['STR'] = weights.get('STR', 0) - 0.2
            weights['COG'] = weights.get('COG', 0) - 0.1
            weights['GA'] = weights.get('GA', 0) - 0.1
            flags.append("Base weights (Yes - happy/secure): STR -0.2, COG -0.1, GA -0.1 (protective)")

        # Free-text amplifiers (only if free text provided)
        if free_text:
            severity_tier = self._detect_severity_tier(free_text)

            if severity_tier == 'tier_a':
                # Severe, chronic adversity
                weights['STR'] = weights.get('STR', 0) + 0.2
                weights['COG'] = weights.get('COG', 0) + 0.2
                weights['IMM'] = weights.get('IMM', 0) + 0.1
                weights['GA'] = weights.get('GA', 0) + 0.1
                weights['HRM'] = weights.get('HRM', 0) + 0.1
                flags.append("Detected: Tier A (severe chronic adversity) → STR +0.2, COG +0.2, IMM +0.1, GA +0.1, HRM +0.1")

            elif severity_tier == 'tier_b':
                # Moderate, persistent stressors
                weights['STR'] = weights.get('STR', 0) + 0.1
                weights['COG'] = weights.get('COG', 0) + 0.1
                weights['GA'] = weights.get('GA', 0) + 0.1
                flags.append("Detected: Tier B (moderate persistent stressors) → STR +0.1, COG +0.1, GA +0.1")

        # Apply per-field cap (+1.0)
        for fa in list(weights.keys()):
            if weights[fa] > self.FIELD_CAP:
                flags.append(f"⚠️  {fa} capped at +{self.FIELD_CAP:.1f} (was +{weights[fa]:.3f})")
                weights[fa] = self.FIELD_CAP

        # Remove zero weights
        weights = {fa: w for fa, w in weights.items() if w != 0}

        return weights, flags

