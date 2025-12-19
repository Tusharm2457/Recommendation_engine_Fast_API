from typing import Dict, Any, List, Tuple
import re
from src.aether_2.utils.text_processing import split_by_delimiters
from .constants import FOCUS_AREAS


class PatientReasoningRuleset:
    """
    Ruleset for evaluating patient reasoning about health issues.

    Extracts causal explanations from free text and maps them to focus areas.
    """
    
    # Per-domain caps for this field
    CAPS = {
        "STR": 0.50,
        "GA": 0.50,
        "DTX": 0.40,
        "IMM": 0.40,
        "CM": 0.35,
        "COG": 0.30,
        "HRM": 0.30,
        "MITO": 0.25,
        "SKN": 0.20
    }
    
    # Safety red flags
    RED_FLAGS = [
        "suicid", "self-harm", "self harm", "harm someone", "kill myself",
        "chest pain now", "stroke", "can't breathe", "cannot breathe",
        "anaphylaxis", "can't swallow", "cannot swallow"
    ]
    
    # Negation patterns
    NEGATION_PATTERNS = [
        r'\bnot\s+',
        r'\bno\s+',
        r'\bwithout\s+',
        r'\bruled\s+out\s+',
        r'\bexcluded\s+',
        r'\bnegative\s+for\s+'
    ]
    
    # Uncertainty/hedge words
    UNCERTAINTY_WORDS = ["maybe", "might", "could be", "possibly", "perhaps", "i guess", "i think", "unsure"]
    
    # Intensity words
    INTENSITY_WORDS = ["definitely", "severe", "major trigger", "very", "extremely", "completely", "totally"]
    
    # Causal lexicon groups (grouped synonyms)
    CAUSAL_LEXICONS = {
        "work_stress": {
            "keywords": [
                "work stress", "burnout", "deadlines", "anxiety from job", "shift work",
                "caregiving stress", "job stress", "workplace stress", "occupational stress"
            ],
            "weights": {"STR": 0.30, "COG": 0.10, "CM": 0.10, "GA": 0.10}  # GA if GI terms co-occur
        },
        "mold": {
            "keywords": [
                "mold", "mould", "damp building", "water-damaged", "musty apartment",
                "water damage", "black mold", "toxic mold"
            ],
            "weights": {"DTX": 0.30, "IMM": 0.25, "MITO": 0.10}  # MITO if fatigue/brain fog co-mentioned
        },
        "antibiotics": {
            "keywords": [
                "antibiotics", "post-antibiotics", "microbiome disrupted", "after antibiotics",
                "antibiotic use", "took antibiotics"
            ],
            "weights": {"GA": 0.25, "IMM": 0.10}
        },
        "food_poisoning": {
            "keywords": [
                "food poisoning", "traveler's diarrhea", "stomach bug", "gi infection",
                "post-infectious", "traveler diarrhea", "gastroenteritis"
            ],
            "weights": {"GA": 0.25, "IMM": 0.05}
        },
        "h_pylori": {
            "keywords": [
                "h pylori", "helicobacter", "gastric infection", "h. pylori", "hpylori"
            ],
            "weights": {"GA": 0.25, "IMM": 0.05}
        },
        "sibo": {
            "keywords": [
                "sibo", "bacterial overgrowth", "small intestinal bacterial overgrowth"
            ],
            "weights": {"GA": 0.25, "MITO": 0.05}
        },
        "candida": {
            "keywords": [
                "candida", "yeast overgrowth", "sifo", "small intestinal fungal overgrowth"
            ],
            "weights": {"GA": 0.10, "IMM": 0.05}
        },
        "bile_gallbladder": {
            "keywords": [
                "bile", "gallbladder problems", "gallbladder removed", "bile acid diarrhea",
                "cholecystectomy", "gallbladder surgery", "bam", "bile acid malabsorption"
            ],
            "weights": {"GA": 0.20, "DTX": 0.05}
        },
        "low_stomach_acid": {
            "keywords": [
                "low acid", "hypochlorhydria", "on ppi", "antacid", "proton pump inhibitor",
                "ppi use", "low stomach acid"
            ],
            "weights": {"GA": 0.15, "IMM": 0.05}
        },
        "leaky_gut": {
            "keywords": [
                "leaky gut", "increased permeability", "zonulin", "intestinal permeability",
                "gut permeability"
            ],
            "weights": {"GA": 0.15, "IMM": 0.05}
        },
        "histamine": {
            "keywords": [
                "histamine intolerance", "histamine", "high histamine"
            ],
            "weights": {"GA": 0.15, "IMM": 0.05}
        },
        "fodmap": {
            "keywords": [
                "fodmap", "fodmaps", "fermentable", "low fodmap"
            ],
            "weights": {"GA": 0.15}
        },
        "poor_diet": {
            "keywords": [
                "poor diet", "junk food", "upfs", "ultra-processed", "too much sugar",
                "high sugar", "seed oils", "processed food", "bad diet"
            ],
            "weights": {"CM": 0.25, "IMM": 0.10, "GA": 0.10}
        },
        "toxins": {
            "keywords": [
                "lead", "mercury", "pesticides", "solvents", "heavy metals", "toxins",
                "chemical exposure", "toxic exposure"
            ],
            "weights": {"DTX": 0.20, "IMM": 0.10, "COG": 0.05}
        },
        "sleep_deprivation": {
            "keywords": [
                "not sleeping", "shift work", "night shifts", "sleep deprivation",
                "circadian disruption", "insomnia", "poor sleep"
            ],
            "weights": {"STR": 0.20, "COG": 0.10, "CM": 0.05}
        },
        "hormonal": {
            "keywords": [
                "thyroid", "menopause", "low t", "hormones off", "hormonal imbalance",
                "testosterone", "estrogen", "pcos", "hypothyroidism"
            ],
            "weights": {"HRM": 0.25, "CM": 0.05}
        },
        "nutrient_deficiency": {
            "keywords": [
                "low iron", "low b12", "vitamin d deficiency", "iron deficiency",
                "b12 deficiency", "vitamin deficiency", "nutrient deficiency"
            ],
            "weights": {"MITO": 0.15, "COG": 0.10}
        }
    }
    
    # GI terms for co-occurrence detection
    GI_TERMS = ["bloat", "gas", "reflux", "constipation", "diarrhea", "ibs", "stomach", "gut", "digestive"]
    
    # Fatigue/brain fog terms for co-occurrence
    FATIGUE_TERMS = ["fatigue", "tired", "exhausted", "brain fog", "foggy", "low energy"]
    
    def get_patient_reasoning_weights(
        self,
        reasoning_text: str,
        age: int = None
    ) -> Tuple[Dict[str, float], Dict[str, bool]]:
        """
        Calculate focus area weights from patient reasoning text.
        
        Args:
            reasoning_text: Free text explaining patient's reasoning
            age: Patient age (must be >= 18)
        
        Returns:
            Tuple of (scores_dict, safety_flags_dict)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        safety_flags = {"red_flag": False}
        
        # Age check
        if age and age < 18:
            return scores, safety_flags
        
        if not reasoning_text or not reasoning_text.strip():
            return scores, safety_flags
        
        # 1) Normalize and validate
        normalized_text = self._normalize_text(reasoning_text)
        
        # 2) Safety check (flag but don't stop scoring)
        safety_flags = self._check_red_flags(normalized_text)
        
        # 3) Remove PII (basic patterns)
        normalized_text = self._remove_pii(normalized_text)
        
        # 4) Match to causal lexicons
        matched_groups = self._match_causal_groups(normalized_text)
        
        if not matched_groups:
            return scores, safety_flags
        
        # 5) Apply compositing logic
        unique_groups = self._dedupe_groups(matched_groups)
        
        # If more than 3 contributing groups, down-weight all by 0.5
        down_weight_factor = 0.5 if len(unique_groups) > 3 else 1.0
        
        for group_name, group_data in unique_groups.items():
            # Check negation
            if self._is_negated(normalized_text, group_data["matched_text"]):
                continue
            
            # Get base weights
            base_weights = group_data["weights"].copy()
            
            # Apply uncertainty modifier (×0.7)
            if self._has_uncertainty(normalized_text, group_data["matched_text"]):
                base_weights = {k: v * 0.7 for k, v in base_weights.items()}
            
            # Apply intensity modifier (+0.05, max +0.10)
            intensity_boost = self._get_intensity_boost(normalized_text, group_data["matched_text"])
            if intensity_boost > 0:
                base_weights = {k: min(v + intensity_boost, v + 0.10) for k, v in base_weights.items()}
            
            # Apply co-occurrence boosts
            base_weights = self._apply_cooccurrence_boosts(normalized_text, group_name, base_weights)
            
            # Apply down-weight if too many groups
            base_weights = {k: v * down_weight_factor for k, v in base_weights.items()}
            
            # Add to scores
            for domain, weight in base_weights.items():
                scores[domain] += weight
        
        # 6) Apply caps
        for domain in scores:
            scores[domain] = min(scores[domain], self.CAPS.get(domain, 1.0))
        
        return scores, safety_flags
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, trim, collapse whitespace, simple lemmatization."""
        if not text:
            return ""
        
        # Limit to 1000 chars
        text = text[:1000]
        
        # Lowercase
        text = text.lower()
        
        # Simple lemmatization (common word endings)
        text = self._simple_lemmatize(text)
        
        # Collapse repeated whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _simple_lemmatize(self, text: str) -> str:
        """Simple lemmatization: normalize common word endings."""
        # Common plural to singular
        replacements = {
            r'\bingestions\b': 'ingestion',
            r'\binfections\b': 'infection',
            r'\bproblems\b': 'problem',
            r'\bissues\b': 'issue',
            r'\bsymptoms\b': 'symptom',
            r'\bmedications\b': 'medication',
            r'\bsupplements\b': 'supplement',
            r'\bconditions\b': 'condition',
            r'\bdisorders\b': 'disorder',
            r'\bdiseases\b': 'disease',
            r'\bexposures\b': 'exposure',
            r'\bstresses\b': 'stress',
            r'\bdeficiencies\b': 'deficiency',
            r'\bovergrowths\b': 'overgrowth',
        }
        
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)
        
        # Remove common verb endings (simple approach)
        text = re.sub(r'\bing\b', '', text)  # Remove standalone "ing"
        text = re.sub(r'\bed\b', '', text)   # Remove standalone "ed"
        
        return text
    
    def _check_red_flags(self, text: str) -> Dict[str, bool]:
        """Check for safety red flags."""
        flags = {"red_flag": False}
        text_lower = text.lower()
        
        for flag in self.RED_FLAGS:
            if flag in text_lower:
                flags["red_flag"] = True
                break
        
        return flags
    
    def _remove_pii(self, text: str) -> str:
        """Remove PII: phone, email, addresses (basic patterns)."""
        # Remove email
        text = re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '[email]', text)
        
        # Remove phone numbers
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[phone]', text)
        
        # Remove addresses (basic pattern)
        text = re.sub(r'\b\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|way|blvd)\b', '[address]', text, flags=re.IGNORECASE)
        
        return text
    
    def _match_causal_groups(self, text: str) -> Dict[str, Dict[str, Any]]:
        """Match text to causal lexicon groups."""
        matched = {}
        text_lower = text.lower()
        
        for group_name, group_data in self.CAUSAL_LEXICONS.items():
            keywords = group_data["keywords"]
            weights = group_data["weights"]
            
            # Check if any keyword matches
            for keyword in keywords:
                if keyword in text_lower:
                    matched[group_name] = {
                        "matched_text": keyword,
                        "weights": weights.copy()
                    }
                    break  # Only match once per group
        
        return matched
    
    def _dedupe_groups(self, matched_groups: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Remove duplicate groups (already handled by matching, but ensure uniqueness)."""
        return matched_groups
    
    def _is_negated(self, text: str, matched_text: str) -> bool:
        """Check if matched text is negated."""
        # Find position of matched text
        text_lower = text.lower()
        match_pos = text_lower.find(matched_text.lower())
        
        if match_pos == -1:
            return False
        
        # Check for negation patterns before the match (within 50 chars)
        context_start = max(0, match_pos - 50)
        context = text_lower[context_start:match_pos]
        
        for pattern in self.NEGATION_PATTERNS:
            if re.search(pattern, context):
                return True
        
        return False
    
    def _has_uncertainty(self, text: str, matched_text: str) -> bool:
        """Check if matched text has uncertainty/hedge words nearby."""
        text_lower = text.lower()
        match_pos = text_lower.find(matched_text.lower())
        
        if match_pos == -1:
            return False
        
        # Check context around match (50 chars before and after)
        context_start = max(0, match_pos - 50)
        context_end = min(len(text_lower), match_pos + len(matched_text) + 50)
        context = text_lower[context_start:context_end]
        
        for uncertainty_word in self.UNCERTAINTY_WORDS:
            if uncertainty_word in context:
                return True
        
        return False
    
    def _get_intensity_boost(self, text: str, matched_text: str) -> float:
        """Get intensity boost amount (0.0 to 0.10)."""
        text_lower = text.lower()
        match_pos = text_lower.find(matched_text.lower())
        
        if match_pos == -1:
            return 0.0
        
        # Check context around match
        context_start = max(0, match_pos - 50)
        context_end = min(len(text_lower), match_pos + len(matched_text) + 50)
        context = text_lower[context_start:context_end]
        
        intensity_count = sum(1 for word in self.INTENSITY_WORDS if word in context)
        
        # +0.05 per intensity word, max +0.10
        return min(intensity_count * 0.05, 0.10)
    
    def _apply_cooccurrence_boosts(self, text: str, group_name: str, base_weights: Dict[str, float]) -> Dict[str, float]:
        """Apply co-occurrence boosts based on additional terms."""
        text_lower = text.lower()
        weights = base_weights.copy()
        
        # Work stress + GI terms → add GA
        if group_name == "work_stress":
            if any(term in text_lower for term in self.GI_TERMS):
                if "GA" not in weights:
                    weights["GA"] = 0.10
                else:
                    weights["GA"] = max(weights["GA"], 0.10)
        
        # Mold + fatigue/brain fog → add MITO
        if group_name == "mold":
            if any(term in text_lower for term in self.FATIGUE_TERMS):
                if "MITO" not in weights:
                    weights["MITO"] = 0.10
                else:
                    weights["MITO"] = max(weights["MITO"], 0.10)
        
        return weights

