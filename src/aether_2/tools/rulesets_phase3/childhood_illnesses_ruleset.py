"""
Ruleset for Field 25: Childhood Illnesses
Evaluates significant illnesses during childhood (radio + free text).
Uses NLP-based keyword detection with age-of-exposure and frequency multipliers.
"""

from typing import Dict, List, Tuple, Any
import re


class ChildhoodIllnessesRuleset:
    """
    Evaluates childhood illness history and returns focus area weights.
    
    Radio: Yes | No
    If Yes → free text (0-2,000 chars)
    
    Scoring logic:
    - Base weights: +0.1 to +0.6 per rule
    - Frequency multiplier: recurrent/≥3 courses → ×1.2
    - Age-of-exposure multiplier: <3y → ×1.3, 3-7y → ×1.15, >7y → ×1.0
    - Per-field cap: +1.0 from this field
    """
    
    # Red flag keywords (require clinical review)
    RED_FLAG_KEYWORDS = [
        'kawasaki', 'meningitis', 'sepsis', 'failure to thrive', 'ftt',
        'encephalitis', 'osteomyelitis', 'endocarditis'
    ]
    
    # GI infection keywords
    GI_INFECTION_KEYWORDS = [
        'gastroenteritis', 'food poisoning', 'stomach bug', 'stomach flu',
        'campylobacter', 'salmonella', 'shigella', 'rotavirus', 'norovirus',
        'post-infection', 'post infection', 'diarrhea', 'diarrhoea'
    ]
    
    # Antibiotic keywords
    ANTIBIOTIC_KEYWORDS = [
        'antibiotic', 'antibiotics', 'amoxicillin', 'augmentin', 'azithromycin',
        'azithro', 'penicillin', 'cephalosporin', 'cefdinir', 'cefuroxime',
        'iv antibiotics', 'iv abx', 'multiple antibiotics', 'long course',
        'prolonged antibiotic'
    ]
    
    # ENT/respiratory keywords
    ENT_KEYWORDS = [
        'ear infection', 'ear infections', 'otitis media', 'otitis',
        'strep throat', 'tonsillitis', 'sinus infection', 'sinusitis',
        'ear tubes', 'tympanostomy', 'tonsillectomy', 'adenoidectomy',
        'tonsils removed', 'adenoids removed'
    ]
    
    LOWER_RESPIRATORY_KEYWORDS = [
        'pneumonia', 'rsv', 'bronchiolitis', 'bronchitis'
    ]
    
    # Atopy keywords
    ATOPY_KEYWORDS = [
        'asthma', 'eczema', 'allergic rhinitis', 'hay fever',
        'food allergy', 'food allergies', 'hives', 'urticaria'
    ]
    
    # Hospitalization keywords
    HOSPITALIZATION_KEYWORDS = [
        'hospitalized', 'hospitalised', 'hospital', 'iv antibiotics',
        'iv abx', 'appendectomy', 'surgery', 'post-op antibiotics'
    ]
    
    # Procedure keywords (severity markers)
    PROCEDURE_KEYWORDS = [
        'ear tubes', 'tympanostomy', 'tonsillectomy', 'adenoidectomy',
        'tonsils removed', 'adenoids removed'
    ]
    
    # Frequency keywords
    FREQUENCY_KEYWORDS = [
        'recurrent', 'recurring', 'many times', 'multiple times',
        'every few months', 'frequently', 'chronic', 'repeated'
    ]
    
    # Per-field cap
    FIELD_CAP = 1.0
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, collapse whitespace."""
        if not text:
            return ""
        text = text.lower()
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
        
        # Single word: use word boundaries to avoid false positives
        pattern = r'\b' + re.escape(keyword) + r'\b'
        return bool(re.search(pattern, text))
    
    def _detect_red_flags(self, text: str) -> List[str]:
        """Detect red flag keywords requiring clinical review."""
        flags = []
        for keyword in self.RED_FLAG_KEYWORDS:
            if self._keyword_match(text, keyword):
                flags.append(f"🚨 RED FLAG: '{keyword}' detected - requires clinical review")
        return flags
    
    def _extract_age_of_exposure(self, text: str) -> float:
        """
        Extract age of exposure multiplier from text.
        Returns: 1.3 (<3y), 1.15 (3-7y), 1.0 (>7y or unknown)
        """
        # Patterns: "before age 2", "as a toddler", "age 5", "when I was 3"
        patterns = [
            r'before age (\d+)',
            r'age (\d+)',
            r'when (?:i was|he was|she was) (\d+)',
            r'at (\d+) years',
            r'(\d+) years old'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                age = int(match.group(1))
                if age < 3:
                    return 1.3
                elif 3 <= age <= 7:
                    return 1.15
                else:
                    return 1.0
        
        # Check for age-related keywords
        if any(kw in text for kw in ['toddler', 'infant', 'baby']):
            return 1.3
        if any(kw in text for kw in ['preschool', 'kindergarten']):
            return 1.15
        
        return 1.0  # Unknown age

    def _detect_frequency_boost(self, text: str) -> float:
        """
        Detect frequency boost from text.
        Returns: 1.2 if recurrent/≥3 courses, else 1.0
        """
        # Check for frequency keywords
        for keyword in self.FREQUENCY_KEYWORDS:
            if self._keyword_match(text, keyword):
                return 1.2

        # Check for "≥3 courses" patterns
        patterns = [
            r'(\d+)\s*courses',
            r'(\d+)\s*times',
            r'(\d+)\s*episodes'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                count = int(match.group(1))
                if count >= 3:
                    return 1.2

        return 1.0

    def _extract_antibiotic_course_count(self, text: str) -> int:
        """Extract antibiotic course count from text."""
        patterns = [
            r'(\d+)\s*courses?\s*(?:of\s*)?antibiotic',
            r'(\d+)\s*rounds?\s*(?:of\s*)?antibiotic',
            r'(\d+)\s*times?\s*(?:on\s*)?antibiotic'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))

        return 0

    def get_childhood_illnesses_weights(
        self,
        childhood_illnesses_data: Any
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights based on childhood illness history.

        Args:
            childhood_illnesses_data: Radio selection (Yes/No) + optional free text

        Returns:
            Tuple of (weights dict, flags list)
        """
        weights = {}
        flags = []

        # Parse input
        if not childhood_illnesses_data:
            return weights, flags

        text = str(childhood_illnesses_data).strip()

        # Split radio and free text (semicolon-separated)
        if ';' in text:
            radio, free_text = text.split(';', 1)
            radio = radio.strip()
            free_text = free_text.strip()
        else:
            radio = text
            free_text = ""

        # Branch on radio selection
        if radio.lower() == "no":
            return weights, flags

        if radio.lower() != "yes":
            flags.append(f"⚠️  Invalid radio selection: '{radio}' (expected Yes/No)")
            return weights, flags

        # Validate free text length
        if not free_text:
            flags.append("⚠️  Radio 'Yes' but no free text provided")
            return weights, flags

        if len(free_text) > 2000:
            flags.append(f"⚠️  Free text truncated from {len(free_text)} to 2000 chars")
            free_text = free_text[:2000]

        # Normalize text
        normalized_text = self._normalize_text(free_text)

        # Check for red flags (HIGHEST PRIORITY)
        red_flags = self._detect_red_flags(normalized_text)
        if red_flags:
            flags.extend(red_flags)
            flags.append("🚨 CLINICAL REVIEW REQUIRED - Surface clinical review banner")
            flags.append("⚠️  needs_clinical_review=true")

        # Extract multipliers
        age_mult = self._extract_age_of_exposure(normalized_text)
        freq_boost = self._detect_frequency_boost(normalized_text)
        antibiotic_courses = self._extract_antibiotic_course_count(normalized_text)

        # Log multipliers if detected
        if age_mult > 1.0:
            if age_mult == 1.3:
                flags.append("Detected: Early exposure (<3 years) → age multiplier ×1.3")
            elif age_mult == 1.15:
                flags.append("Detected: Childhood exposure (3-7 years) → age multiplier ×1.15")

        if freq_boost > 1.0:
            flags.append("Detected: Recurrent/frequent episodes → frequency multiplier ×1.2")

        if antibiotic_courses >= 3:
            flags.append(f"Detected: {antibiotic_courses} antibiotic courses → frequency multiplier ×1.2")
            freq_boost = 1.2  # Override if explicit count found

        # Rule B: GI infections in childhood
        gi_infection_detected = False
        for keyword in self.GI_INFECTION_KEYWORDS:
            if self._keyword_match(normalized_text, keyword):
                gi_infection_detected = True
                break

        if gi_infection_detected:
            weights['GA'] = weights.get('GA', 0) + 0.6
            weights['IMM'] = weights.get('IMM', 0) + 0.2
            weights['STR'] = weights.get('STR', 0) + 0.1
            weights['COG'] = weights.get('COG', 0) + 0.1
            flags.append("Detected: GI infection in childhood → GA +0.6, IMM +0.2, STR +0.1, COG +0.1")

        # Rule C: Early-life antibiotic exposure
        antibiotic_detected = False
        for keyword in self.ANTIBIOTIC_KEYWORDS:
            if self._keyword_match(normalized_text, keyword):
                antibiotic_detected = True
                break

        if antibiotic_detected:
            imm_weight = 0.3 * age_mult * freq_boost
            ga_weight = 0.3 * age_mult * freq_boost
            dtx_weight = 0.2 * age_mult * freq_boost

            weights['IMM'] = weights.get('IMM', 0) + imm_weight
            weights['GA'] = weights.get('GA', 0) + ga_weight
            weights['DTX'] = weights.get('DTX', 0) + dtx_weight

            flags.append(f"Detected: Antibiotic exposure → IMM +{imm_weight:.3f}, GA +{ga_weight:.3f}, DTX +{dtx_weight:.3f}")

        # Rule D1: Recurrent ENT/respiratory illnesses
        ent_detected = False
        for keyword in self.ENT_KEYWORDS:
            if self._keyword_match(normalized_text, keyword):
                ent_detected = True
                break

        if ent_detected:
            imm_weight = 0.3 * age_mult
            ga_weight = 0.2 * age_mult

            weights['IMM'] = weights.get('IMM', 0) + imm_weight
            weights['GA'] = weights.get('GA', 0) + ga_weight

            flags.append(f"Detected: Recurrent ENT infections → IMM +{imm_weight:.3f}, GA +{ga_weight:.3f}")

            # Check for procedures (severity marker)
            procedure_detected = False
            for keyword in self.PROCEDURE_KEYWORDS:
                if self._keyword_match(normalized_text, keyword):
                    procedure_detected = True
                    break

            if procedure_detected:
                weights['IMM'] = weights.get('IMM', 0) + 0.1
                flags.append("Detected: ENT procedure (ear tubes/tonsillectomy) → IMM +0.1 (severity marker)")

        # Rule D2: Lower respiratory infections
        lower_resp_detected = False
        for keyword in self.LOWER_RESPIRATORY_KEYWORDS:
            if self._keyword_match(normalized_text, keyword):
                lower_resp_detected = True
                break

        if lower_resp_detected:
            imm_weight = 0.4 * age_mult
            mito_weight = 0.2 * age_mult

            weights['IMM'] = weights.get('IMM', 0) + imm_weight
            weights['MITO'] = weights.get('MITO', 0) + mito_weight

            flags.append(f"Detected: Lower respiratory infection → IMM +{imm_weight:.3f}, MITO +{mito_weight:.3f}")

        # Rule E: Childhood atopy/allergic disease
        atopy_detected = False
        for keyword in self.ATOPY_KEYWORDS:
            if self._keyword_match(normalized_text, keyword):
                atopy_detected = True
                break

        if atopy_detected:
            weights['IMM'] = weights.get('IMM', 0) + 0.5
            weights['SKN'] = weights.get('SKN', 0) + 0.3
            weights['GA'] = weights.get('GA', 0) + 0.2
            flags.append("Detected: Atopic history (asthma/eczema/allergies) → IMM +0.5, SKN +0.3, GA +0.2")

        # Rule F: Hospitalization/surgery with antimicrobials
        hospitalization_detected = False
        for keyword in self.HOSPITALIZATION_KEYWORDS:
            if self._keyword_match(normalized_text, keyword):
                hospitalization_detected = True
                break

        if hospitalization_detected:
            weights['DTX'] = weights.get('DTX', 0) + 0.2
            weights['IMM'] = weights.get('IMM', 0) + 0.2
            weights['GA'] = weights.get('GA', 0) + 0.1
            flags.append("Detected: Hospitalization with antimicrobials → DTX +0.2, IMM +0.2, GA +0.1")

        # Apply per-field cap (+1.0)
        for fa in list(weights.keys()):
            if weights[fa] > self.FIELD_CAP:
                flags.append(f"⚠️  {fa} capped at +{self.FIELD_CAP:.1f} (was +{weights[fa]:.3f})")
                weights[fa] = self.FIELD_CAP

        # Remove zero weights
        weights = {fa: w for fa, w in weights.items() if w != 0}

        return weights, flags

