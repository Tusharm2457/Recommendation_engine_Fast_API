"""
Ruleset for Field 24: Trauma/Abuse
Evaluates trauma history with NLP-based keyword detection and privacy safeguards.
"""

from typing import Dict, List, Tuple, Any, Optional
import re


class TraumaRuleset:
    """Ruleset for evaluating trauma/abuse history."""
    
    # Crisis keywords - immediate danger/ongoing abuse/suicidality
    CRISIS_KEYWORDS = {
        'imminent_danger': ['want to die', 'going to kill', 'end my life', 'suicide plan', 
                           'kill myself', 'hurt myself', 'end it all', 'better off dead'],
        'ongoing_abuse': ['happening now', 'currently being', 'still abusing', 'won\'t stop',
                         'can\'t escape', 'trapped', 'afraid for my life'],
        'homicidal': ['kill them', 'hurt them', 'going to harm', 'make them pay']
    }
    
    # Trauma type keywords (using word boundaries and multi-word phrases)
    CHILDHOOD_KEYWORDS = [
        'childhood', 'child abuse', 'childhood abuse', 'ACE', 'adverse childhood',
        'neglect', 'neglected', 'abandoned', 'foster care', 'orphan',
        'parent abuse', 'parental abuse', 'family violence', 'grew up with abuse'
    ]
    
    IPV_SEXUAL_KEYWORDS = [
        'sexual assault', 'sexual abuse', 'rape', 'raped', 'molest', 'molestation',
        'intimate partner', 'domestic violence', 'domestic abuse', 'partner violence',
        'spousal abuse', 'dating violence', 'abusive relationship', 'sexual trauma'
    ]
    
    COMBAT_KEYWORDS = [
        'combat', 'war', 'deployment', 'deployed', 'veteran', 'military trauma',
        'first responder', 'firefighter', 'paramedic', 'EMT', 'police trauma',
        'witnessed death', 'combat zone', 'active duty'
    ]
    
    ACCIDENT_DISASTER_KEYWORDS = [
        'car accident', 'car crash', 'accident', 'natural disaster', 'hurricane',
        'earthquake', 'flood', 'tornado', 'fire', 'explosion', 'near death'
    ]
    
    MEDICAL_KEYWORDS = [
        'ICU', 'intensive care', 'ventilator', 'intubated', 'surgery trauma',
        'medical trauma', 'birth trauma', 'traumatic birth', 'NICU', 'hospitalization',
        'life support', 'emergency surgery'
    ]
    
    DISCRIMINATION_KEYWORDS = [
        'discrimination', 'discriminated', 'bullying', 'bullied', 'harassment',
        'harassed', 'hate crime', 'racism', 'sexism', 'homophobia', 'transphobia',
        'chronic stress', 'systemic oppression', 'marginalized'
    ]
    
    # Pattern keywords
    REPEATED_CHRONIC_KEYWORDS = [
        'for years', 'repeatedly', 'multiple times', 'ongoing', 'chronic',
        'over and over', 'many times', 'continuous', 'prolonged', 'extended period'
    ]
    
    # PTSD symptom keywords
    PTSD_SYMPTOMS = {
        'nightmares': ['nightmare', 'nightmares', 'bad dreams', 'night terrors'],
        'flashbacks': ['flashback', 'flashbacks', 'reliving', 'intrusive memories', 'intrusive thoughts'],
        'hypervigilance': ['hypervigilant', 'hypervigilance', 'on edge', 'always alert', 'can\'t relax'],
        'startle': ['startle', 'startled', 'jumpy', 'easily scared', 'startle response'],
        'avoidance': ['avoid', 'avoidance', 'avoiding', 'can\'t talk about', 'won\'t discuss']
    }
    
    # Protective factor keywords
    THERAPY_KEYWORDS = [
        'tf-cbt', 'tfcbt', 'trauma focused', 'emdr', 'eye movement',
        'trauma therapy', 'trauma counseling', 'trauma treatment'
    ]
    
    MIND_BODY_KEYWORDS = [
        'mindfulness', 'meditation', 'yoga', 'breathing exercises', 'paced breathing',
        'tai chi', 'qigong', 'body scan', 'progressive relaxation'
    ]
    
    # Per-field caps
    CAPS = {
        'STR': 1.5,
        'COG': 1.0,
        'IMM': 0.7,
        'GA': 0.7,
        'CM': 0.6,
        'MITO': 0.5,
        'SKN': 0.3,
        'DTX': 0.4,
        'HRM': 0.3
    }
    
    def __init__(self):
        """Initialize the trauma ruleset."""
        pass
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching."""
        if not text:
            return ""
        # Lowercase
        text = text.lower()
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text)
        # Strip leading/trailing whitespace
        text = text.strip()
        return text
    
    def _keyword_match(self, text: str, keyword: str) -> bool:
        """
        Match keyword with word boundaries for single words,
        substring matching for multi-word phrases.
        """
        if not text or not keyword:
            return False
        
        # Multi-word phrase -> substring match
        if ' ' in keyword:
            return keyword in text
        
        # Single word -> word boundary match
        pattern = r'\b' + re.escape(keyword) + r'\b'
        return bool(re.search(pattern, text))
    
    def _detect_crisis(self, text: str) -> Tuple[bool, List[str]]:
        """Detect crisis keywords suggesting imminent danger."""
        flags = []
        crisis_detected = False
        
        for category, keywords in self.CRISIS_KEYWORDS.items():
            for keyword in keywords:
                if self._keyword_match(text, keyword):
                    crisis_detected = True
                    flags.append(f"🚨 CRISIS: {category} detected - '{keyword}'")
        
        return crisis_detected, flags

    def _detect_trauma_types(self, text: str) -> Dict[str, bool]:
        """Detect trauma types from text."""
        types = {
            'childhood': False,
            'ipv_sexual': False,
            'combat': False,
            'accident_disaster': False,
            'medical': False,
            'discrimination': False
        }

        # Childhood/early-life adversity
        for keyword in self.CHILDHOOD_KEYWORDS:
            if self._keyword_match(text, keyword):
                types['childhood'] = True
                break

        # Intimate-partner/sexual violence
        for keyword in self.IPV_SEXUAL_KEYWORDS:
            if self._keyword_match(text, keyword):
                types['ipv_sexual'] = True
                break

        # War/combat/first-responder
        for keyword in self.COMBAT_KEYWORDS:
            if self._keyword_match(text, keyword):
                types['combat'] = True
                break

        # Serious accident/natural disaster
        for keyword in self.ACCIDENT_DISASTER_KEYWORDS:
            if self._keyword_match(text, keyword):
                types['accident_disaster'] = True
                break

        # Medical/ICU/birth trauma
        for keyword in self.MEDICAL_KEYWORDS:
            if self._keyword_match(text, keyword):
                types['medical'] = True
                break

        # Chronic discrimination/bullying
        for keyword in self.DISCRIMINATION_KEYWORDS:
            if self._keyword_match(text, keyword):
                types['discrimination'] = True
                break

        return types

    def _detect_repeated_chronic(self, text: str) -> bool:
        """Detect repeated/chronic trauma patterns."""
        for keyword in self.REPEATED_CHRONIC_KEYWORDS:
            if self._keyword_match(text, keyword):
                return True
        return False

    def _detect_ptsd_symptoms(self, text: str) -> Dict[str, bool]:
        """Detect PTSD symptoms from text."""
        symptoms = {
            'nightmares': False,
            'flashbacks': False,
            'hypervigilance': False,
            'startle': False,
            'avoidance': False
        }

        for symptom, keywords in self.PTSD_SYMPTOMS.items():
            for keyword in keywords:
                if self._keyword_match(text, keyword):
                    symptoms[symptom] = True
                    break

        return symptoms

    def _extract_recency(self, text: str) -> Optional[int]:
        """
        Extract recency in months from text.
        Returns None if not found.
        """
        # Look for patterns like "X months ago", "X years ago", "last year", etc.

        # X months ago
        match = re.search(r'(\d+)\s*months?\s+ago', text)
        if match:
            return int(match.group(1))

        # X years ago
        match = re.search(r'(\d+)\s*years?\s+ago', text)
        if match:
            return int(match.group(1)) * 12

        # Last year, this year
        if 'last year' in text or 'past year' in text:
            return 12
        if 'this year' in text or 'recent' in text or 'recently' in text:
            return 6

        # Ongoing/current
        if 'ongoing' in text or 'current' in text or 'still' in text:
            return 0

        return None

    def _detect_therapy(self, text: str) -> bool:
        """Detect trauma-focused therapy."""
        for keyword in self.THERAPY_KEYWORDS:
            if self._keyword_match(text, keyword):
                # Check for session count
                match = re.search(r'(\d+)\s*sessions?', text)
                if match and int(match.group(1)) >= 8:
                    return True
                # Check for "ongoing"
                if 'ongoing' in text or 'currently' in text or 'still in' in text:
                    return True
        return False

    def _detect_mind_body_practice(self, text: str) -> bool:
        """Detect mind-body practice ≥3×/week."""
        for keyword in self.MIND_BODY_KEYWORDS:
            if self._keyword_match(text, keyword):
                # Check for frequency
                if any(freq in text for freq in ['3 times', '3x', 'three times', 'daily', 'every day', 'most days']):
                    return True
        return False

    def get_trauma_weights(
        self,
        trauma_data: Any,
        sleep_disturbance: bool = False,
        stress_score: int = None,
        gi_symptom_count: int = 0,
        substance_use_high: bool = False,
        supports_count: int = 0
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights for trauma/abuse history.

        Args:
            trauma_data: Radio selection + optional free text (e.g., "Yes; childhood abuse, nightmares")
            sleep_disturbance: Whether patient has sleep disturbance
            stress_score: Current stress level (1-10)
            gi_symptom_count: Number of GI symptoms
            substance_use_high: Whether patient has high substance use
            supports_count: Number of support sources

        Returns:
            Tuple of (weights dict, flags list)
        """
        weights = {}
        flags = []

        # Parse input
        if not trauma_data or not isinstance(trauma_data, str):
            return weights, flags

        text = self._normalize_text(trauma_data)

        # Split radio selection and free text
        parts = text.split(';', 1)
        radio = parts[0].strip()
        free_text = parts[1].strip() if len(parts) > 1 else ""

        # Branch on radio selection
        if radio == "no":
            return weights, flags

        if radio == "prefer not to say":
            flags.append("⚠️  Privacy: User preferred not to disclose trauma history")
            return weights, flags

        if radio != "yes":
            # Invalid radio value
            flags.append(f"⚠️  Invalid radio value: '{radio}' (expected Yes/No/Prefer not to say)")
            return weights, flags

        # Validate free text length (1-2000 chars)
        if free_text and len(free_text) > 2000:
            flags.append(f"⚠️  Free text truncated from {len(free_text)} to 2000 chars")
            free_text = free_text[:2000]

        # Crisis screening (HIGHEST PRIORITY)
        crisis_detected, crisis_flags = self._detect_crisis(free_text)
        if crisis_detected:
            flags.extend(crisis_flags)
            flags.append("🚨 CRISIS DETECTED - STOP SCORING - SURFACE CRISIS RESOURCE CARD (988)")
            flags.append("⚠️  needs_human_review=true")
            # Return empty weights - crisis takes precedence
            return weights, flags

        # Step B: Baseline weights (any significant trauma/abuse)
        weights['STR'] = 0.7
        weights['COG'] = 0.4
        weights['IMM'] = 0.3
        weights['CM'] = 0.2
        weights['GA'] = 0.2
        weights['MITO'] = 0.2
        weights['SKN'] = 0.1

        # Step C: Type refinement
        trauma_types = self._detect_trauma_types(free_text)

        if trauma_types['childhood']:
            weights['STR'] = weights.get('STR', 0) + 0.2
            weights['IMM'] = weights.get('IMM', 0) + 0.2
            weights['GA'] = weights.get('GA', 0) + 0.2
            weights['CM'] = weights.get('CM', 0) + 0.1
            flags.append("Detected: Childhood/early-life adversity")

        if trauma_types['ipv_sexual']:
            weights['STR'] = weights.get('STR', 0) + 0.2
            weights['COG'] = weights.get('COG', 0) + 0.2
            weights['IMM'] = weights.get('IMM', 0) + 0.1
            flags.append("Detected: Intimate-partner/sexual violence")

        if trauma_types['combat']:
            weights['COG'] = weights.get('COG', 0) + 0.2
            weights['STR'] = weights.get('STR', 0) + 0.2
            weights['CM'] = weights.get('CM', 0) + 0.1
            flags.append("Detected: War/combat/first-responder trauma")

        if trauma_types['accident_disaster']:
            weights['STR'] = weights.get('STR', 0) + 0.1
            weights['COG'] = weights.get('COG', 0) + 0.1
            flags.append("Detected: Serious accident/natural disaster")

        if trauma_types['medical']:
            weights['STR'] = weights.get('STR', 0) + 0.2
            weights['COG'] = weights.get('COG', 0) + 0.1
            weights['GA'] = weights.get('GA', 0) + 0.1
            flags.append("Detected: Medical/ICU/birth trauma")

        if trauma_types['discrimination']:
            weights['STR'] = weights.get('STR', 0) + 0.1
            weights['COG'] = weights.get('COG', 0) + 0.1
            flags.append("Detected: Chronic discrimination/bullying")

        # Step D: Pattern refinement
        # Complex/repeated
        if self._detect_repeated_chronic(free_text) or sum(trauma_types.values()) > 1:
            weights['STR'] = weights.get('STR', 0) + 0.2
            weights['COG'] = weights.get('COG', 0) + 0.1
            weights['IMM'] = weights.get('IMM', 0) + 0.1
            weights['GA'] = weights.get('GA', 0) + 0.1
            flags.append("Detected: Complex/repeated trauma")

        # Recency
        recency_months = self._extract_recency(free_text)
        if recency_months is not None:
            if recency_months <= 12:
                weights['STR'] = weights.get('STR', 0) + 0.2
                weights['COG'] = weights.get('COG', 0) + 0.1
                flags.append(f"Detected: Recent trauma (≤12 months ago)")
            elif recency_months <= 60:  # 5 years
                weights['STR'] = weights.get('STR', 0) + 0.1
                flags.append(f"Detected: Trauma within 1-5 years")

        # PTSD symptoms
        ptsd_symptoms = self._detect_ptsd_symptoms(free_text)
        ptsd_count = sum(ptsd_symptoms.values())
        if ptsd_count > 0:
            # Add per symptom, but cap at +0.3 per focus
            ptsd_str_increment = min(ptsd_count * 0.1, 0.3)
            ptsd_cog_increment = min(ptsd_count * 0.1, 0.3)
            weights['STR'] = weights.get('STR', 0) + ptsd_str_increment
            weights['COG'] = weights.get('COG', 0) + ptsd_cog_increment
            flags.append(f"Detected: {ptsd_count} PTSD symptom(s) - {', '.join([k for k, v in ptsd_symptoms.items() if v])}")

        # Step E: Cross-field synergies
        # Sleep disturbance
        if sleep_disturbance:
            sleep_str_increment = min(0.1, 0.2)  # Cap at +0.2
            weights['STR'] = weights.get('STR', 0) + sleep_str_increment
            flags.append("Cross-field synergy: Sleep disturbance → STR +0.10")

        # High stress
        if stress_score is not None and stress_score >= 8:
            weights['STR'] = weights.get('STR', 0) + 0.1
            weights['CM'] = weights.get('CM', 0) + 0.1
            flags.append(f"Cross-field synergy: High stress ({stress_score}/10) → STR +0.10, CM +0.10")

        # GI burden
        if gi_symptom_count >= 3 or 'post-infectious' in free_text or 'post infectious' in free_text:
            weights['GA'] = weights.get('GA', 0) + 0.2
            flags.append(f"Cross-field synergy: GI burden ({gi_symptom_count} symptoms) → GA +0.20")

        # Substance use elevation
        if substance_use_high:
            weights['DTX'] = weights.get('DTX', 0) + 0.2
            weights['CM'] = weights.get('CM', 0) + 0.1
            weights['GA'] = weights.get('GA', 0) + 0.1
            flags.append("Cross-field synergy: High substance use → DTX +0.20, CM +0.10, GA +0.10")

        # Step F: Protective modifiers (subtractors)
        # Trauma-focused therapy
        if self._detect_therapy(free_text):
            weights['STR'] = weights.get('STR', 0) - 0.2
            weights['COG'] = weights.get('COG', 0) - 0.1
            flags.append("Protective factor: Trauma-focused therapy (≥8 sessions or ongoing) → STR -0.20, COG -0.10")

        # Mind-body practice
        if self._detect_mind_body_practice(free_text):
            weights['STR'] = weights.get('STR', 0) - 0.1
            weights['GA'] = weights.get('GA', 0) - 0.05
            flags.append("Protective factor: Mind-body practice (≥3×/week) → STR -0.10, GA -0.05")

        # Robust supports
        if supports_count >= 3:
            weights['STR'] = weights.get('STR', 0) - 0.1
            flags.append(f"Protective factor: Robust supports ({supports_count} sources) → STR -0.10")

        # Apply per-field caps
        for domain, cap in self.CAPS.items():
            if domain in weights:
                if weights[domain] > cap:
                    flags.append(f"⚠️  {domain} capped at +{cap:.1f} (was {weights[domain]:.2f})")
                    weights[domain] = cap

        # Remove zero weights
        weights = {k: v for k, v in weights.items() if abs(v) > 0.001}

        return weights, flags

