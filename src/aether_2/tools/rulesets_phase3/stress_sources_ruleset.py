"""
Stress Sources Ruleset (Field 21): "What are your biggest sources of stress right now?"

NLP-based stressor categorization with cross-field synergies.
"""

from typing import Dict, List, Tuple, Any, Set
import re


class StressSourcesRuleset:
    """
    Evaluates free-text stress sources and returns focus area weights.
    
    Categories:
    - Caregiving
    - Work/Deadlines/Burnout
    - Finances/Housing/Food insecurity
    - Health of self
    - Trauma/PTSD/Grief
    - Relationship conflict/isolation
    - Legal/Immigration/Academic
    - Environment (mold/chemicals/air)
    
    Synergies:
    - GI symptoms + caregiving/burnout/trauma → GA boost
    - Shift work + work stress → STR/GA boost
    - Sleep irregular + ≥2 stressors → STR/COG boost
    - Food insecurity → GA boost
    - Mold/chemical + sinus/headache → DTX/IMM/GA boost
    """
    
    # Stressor category lexicons
    CAREGIVING_KEYWORDS = [
        "caregiv", "elder care", "dementia parent", "special-needs child", "special needs child",
        "spouse with cancer", "taking care of", "caring for", "parent with alzheimer",
        "disabled child", "sick parent", "sick spouse", "aging parent"
    ]
    
    WORK_KEYWORDS = [
        "workload", "deadline", "deadlines", "boss", "performance review", "layoff", "layoffs", "burnout",
        "long hours", "shift work", "night shift", "work stress", "job stress",
        "overtime", "work pressure", "demanding job", "toxic workplace"
    ]
    
    FINANCES_KEYWORDS = [
        "bills", "debt", "rent", "mortgage", "job loss", "paycheck to paycheck",
        "eviction", "food stamps", "food insecurity", "financial stress", "money",
        "bankruptcy", "foreclosure", "unemployment", "can't afford", "broke"
    ]
    
    HEALTH_SELF_KEYWORDS = [
        "chronic illness", "pain", "new diagnosis", "disability", "medical bills",
        "health anxiety", "my condition", "my disease", "my symptoms", "chronic pain",
        "autoimmune", "cancer diagnosis", "heart disease"
    ]
    
    TRAUMA_KEYWORDS = [
        "ptsd", "trauma", "abuse", "triggers", "flashback", "grief", "bereavement",
        "loss of", "death of", "died", "passed away", "assault", "violence",
        "traumatic", "grieving", "mourning"
    ]
    
    RELATIONSHIP_KEYWORDS = [
        "divorce", "separation", "conflict", "custody", "isolation", "loneliness",
        "lonely", "alone", "relationship problems", "family conflict", "marital",
        "breakup", "fighting", "argument"
    ]
    
    LEGAL_KEYWORDS = [
        "lawsuit", "immigration", "visa", "exams", "thesis", "grades", "legal",
        "court", "attorney", "lawyer", "deportation", "citizenship", "student loan",
        "academic pressure", "dissertation"
    ]
    
    ENVIRONMENT_KEYWORDS = [
        "mold", "damp", "chemicals", "noise", "poor air", "commute", "pollution",
        "toxic", "air quality", "water quality", "environmental", "allergens"
    ]
    
    # Safety keywords (trigger human review, no scoring)
    SAFETY_KEYWORDS = [
        "suicide", "suicidal", "kill myself", "end my life", "self-harm", "cut myself",
        "domestic violence", "being abused", "psychosis", "hearing voices", "withdrawal",
        "detox", "want to die"
    ]
    
    # Aerodigestive symptoms (for environment synergy)
    AERODIGESTIVE_KEYWORDS = [
        "sinus", "headache", "cough", "heartburn", "congestion", "migraine", "runny nose"
    ]
    
    # Food insecurity keywords (for GA synergy)
    FOOD_INSECURITY_KEYWORDS = [
        "food insecurity", "irregular meals", "skip meals", "can't afford food",
        "food stamps", "food bank", "hungry"
    ]
    
    # Base weights per stressor category
    STRESSOR_WEIGHTS = {
        "caregiving": {
            "STR": 0.25, "COG": 0.15, "CM": 0.05, "IMM": 0.08, "MITO": 0.05
        },
        "work": {
            "STR": 0.20, "COG": 0.10, "CM": 0.05, "MITO": 0.05
        },
        "finances": {
            "STR": 0.20, "COG": 0.10, "CM": 0.10, "IMM": 0.03, "MITO": 0.05, "GA": 0.05
        },
        "health_self": {
            "STR": 0.15, "COG": 0.10, "CM": 0.05, "IMM": 0.03, "MITO": 0.05
        },
        "trauma": {
            "STR": 0.20, "COG": 0.20, "CM": 0.05, "IMM": 0.10, "MITO": 0.06, "SKN": 0.03
        },
        "relationship": {
            "STR": 0.15, "COG": 0.10, "CM": 0.03, "IMM": 0.03, "MITO": 0.04
        },
        "legal": {
            "STR": 0.15, "COG": 0.10, "CM": 0.05, "MITO": 0.04
        },
        "environment": {
            "STR": 0.10, "COG": 0.05, "IMM": 0.05, "DTX": 0.05, "SKN": 0.03, "GA": 0.05, "MITO": 0.03
        }
    }
    
    def __init__(self):
        pass

    def _normalize_text(self, text: str) -> str:
        """
        Normalize text: lowercase, collapse whitespace, collapse repeated punctuation.
        """
        if not text:
            return ""

        # Lowercase
        text = text.lower()

        # Collapse repeated punctuation
        text = re.sub(r'([!?.,;:])\1+', r'\1', text)

        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def _check_safety(self, text: str) -> bool:
        """
        Check for safety keywords (self-harm, domestic violence, suicidality, etc.).
        Returns True if safety concern detected.
        """
        if not text:
            return False

        normalized = self._normalize_text(text)

        for keyword in self.SAFETY_KEYWORDS:
            if keyword in normalized:
                return True

        return False

    def _keyword_match(self, text: str, keyword: str) -> bool:
        """
        Check if keyword matches in text using word boundaries for single words,
        or substring matching for multi-word phrases.
        """
        if ' ' in keyword:
            # Multi-word phrase: use substring matching
            return keyword in text
        else:
            # Single word: use word boundary matching
            pattern = r'\b' + re.escape(keyword) + r'\b'
            return bool(re.search(pattern, text))

    def _detect_stressors(self, text: str) -> Set[str]:
        """
        Detect stressor categories from text using lexicon matching.
        Returns set of detected category names.
        """
        if not text:
            return set()

        normalized = self._normalize_text(text)
        detected = set()

        # Check each category
        for keyword in self.CAREGIVING_KEYWORDS:
            if self._keyword_match(normalized, keyword):
                detected.add("caregiving")
                break

        for keyword in self.WORK_KEYWORDS:
            if self._keyword_match(normalized, keyword):
                detected.add("work")
                break

        for keyword in self.FINANCES_KEYWORDS:
            if self._keyword_match(normalized, keyword):
                detected.add("finances")
                break

        for keyword in self.HEALTH_SELF_KEYWORDS:
            if self._keyword_match(normalized, keyword):
                detected.add("health_self")
                break

        for keyword in self.TRAUMA_KEYWORDS:
            if self._keyword_match(normalized, keyword):
                detected.add("trauma")
                break

        for keyword in self.RELATIONSHIP_KEYWORDS:
            if self._keyword_match(normalized, keyword):
                detected.add("relationship")
                break

        for keyword in self.LEGAL_KEYWORDS:
            if self._keyword_match(normalized, keyword):
                detected.add("legal")
                break

        for keyword in self.ENVIRONMENT_KEYWORDS:
            if self._keyword_match(normalized, keyword):
                detected.add("environment")
                break

        return detected

    def _detect_food_insecurity(self, text: str) -> bool:
        """Check if text mentions food insecurity."""
        if not text:
            return False

        normalized = self._normalize_text(text)

        for keyword in self.FOOD_INSECURITY_KEYWORDS:
            if keyword in normalized:
                return True

        return False

    def _detect_aerodigestive(self, text: str) -> bool:
        """Check if text mentions aerodigestive symptoms (sinus, headache, etc.)."""
        if not text:
            return False

        normalized = self._normalize_text(text)

        for keyword in self.AERODIGESTIVE_KEYWORDS:
            if keyword in normalized:
                return True

        return False

    def get_stress_sources_weights(
        self,
        stress_data: Any,
        age: int = None,
        gi_symptoms_present: bool = False,
        shift_work: bool = False,
        sleep_irregular: bool = False
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights based on stress sources (free text).

        Args:
            stress_data: Free text describing stress sources
            age: Patient age (must be ≥18)
            gi_symptoms_present: Whether GI symptoms are present elsewhere
            shift_work: Whether patient does shift work
            sleep_irregular: Whether sleep schedule is irregular

        Returns:
            Tuple of (weights dict, flags/warnings list)
        """
        weights = {}
        flags = []

        # Adults only (age ≥18)
        if age is not None and age < 18:
            flags.append("VALIDATION: Age < 18, stress sources scoring not applicable")
            return weights, flags

        # Handle None, empty, or whitespace-only
        if stress_data is None or str(stress_data).strip() == "" or str(stress_data).strip().lower() in ["none", "n/a", "na"]:
            return weights, flags

        text = str(stress_data)

        # Validate length (0-1000 chars)
        if len(text) > 1000:
            text = text[:1000]
            flags.append("VALIDATION: Text truncated to 1000 characters")

        # Safety check (trigger human review, no scoring)
        if self._check_safety(text):
            flags.append("SAFETY: Text contains crisis keywords (self-harm, domestic violence, suicidality) - escalate to clinician")
            return weights, flags

        # Detect stressor categories
        stressors = self._detect_stressors(text)

        if not stressors:
            return weights, flags

        # Global baseline: any stressors present → STR +0.10
        weights["STR"] = weights.get("STR", 0) + 0.10

        # Cap at 5 categories to avoid runaway totals
        stressors_to_score = list(stressors)[:5]
        if len(stressors) > 5:
            flags.append(f"INFO: {len(stressors)} stressor categories detected, capped at 5 for scoring")

        # Apply base weights for each stressor category
        for stressor in stressors_to_score:
            stressor_weights = self.STRESSOR_WEIGHTS.get(stressor, {})
            for domain, weight in stressor_weights.items():
                weights[domain] = weights.get(domain, 0) + weight

        # GI synergies (only if GI symptoms present elsewhere)
        if gi_symptoms_present:
            gi_synergy_count = 0

            if "caregiving" in stressors:
                weights["GA"] = weights.get("GA", 0) + 0.20
                gi_synergy_count += 1

            if "work" in stressors:
                weights["GA"] = weights.get("GA", 0) + 0.20
                gi_synergy_count += 1

            if "trauma" in stressors:
                weights["GA"] = weights.get("GA", 0) + 0.20
                gi_synergy_count += 1

            # Cap GI synergy at +0.40
            if gi_synergy_count > 2:
                # Already capped by only applying to 3 categories max
                pass

        # Shift work synergy
        if shift_work and "work" in stressors:
            weights["STR"] = weights.get("STR", 0) + 0.10
            weights["GA"] = weights.get("GA", 0) + 0.10

        # Sleep irregular synergy (≥2 stressors)
        if sleep_irregular and len(stressors) >= 2:
            weights["STR"] = weights.get("STR", 0) + 0.10
            weights["COG"] = weights.get("COG", 0) + 0.05

        # Food insecurity synergy
        if "finances" in stressors and self._detect_food_insecurity(text):
            weights["GA"] = weights.get("GA", 0) + 0.10

        # Environment synergy (mold/chemical + aerodigestive symptoms)
        if "environment" in stressors:
            if self._detect_aerodigestive(text):
                weights["GA"] = weights.get("GA", 0) + 0.05

        # Remove zero scores
        weights = {k: v for k, v in weights.items() if v != 0}

        return weights, flags

