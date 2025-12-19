"""
Phase 3 Ruleset: Trigger Event (Field 4)
"Did anything specific start or worsen your wellness?"

Analyzes free-text responses about trigger events that started or worsened health issues.
Detects 7 trigger categories with NLP-based matching, recency multipliers, and synergy rules.
"""

from typing import Dict, Tuple, List, Any
import re
from datetime import datetime

from .constants import (
    FOCUS_AREAS,
    get_spacy_model,
    preprocess_lexicons,
    lemmatize_text,
    match_keyword_fuzzy,
    RAPIDFUZZ_AVAILABLE
)


class TriggerEventRuleset:
    """
    Ruleset for scoring trigger events that started or worsened wellness.
    
    Detects 7 trigger categories:
    1. Post-infectious (viral/bacterial)
    2. Accident/surgery
    3. Medications (antibiotics, PPI, NSAIDs, metformin, opioids)
    4. Hormonal life events (postpartum, perimenopause)
    5. Environmental/biotoxin exposures (mold, chemicals)
    6. Psychosocial/circadian triggers (stress, job loss, shift work)
    7. Dietary/routine shifts
    
    Features:
    - NLP-based keyword matching with lemmatization + fuzzy matching
    - Negation detection ("not from antibiotics")
    - Uncertainty detection ("maybe after...")
    - Recency multipliers (very recent: 1.2, recent: 1.0, remote: 0.7)
    - Synergy rules (e.g., gastroenteritis + antibiotics)
    - Per-domain caps (GA ≤ 0.40, IMM ≤ 0.35, STR ≤ 0.30, etc.)
    """
    
    # Per-domain caps for this field
    DOMAIN_CAPS = {
        "GA": 0.40,
        "IMM": 0.35,
        "STR": 0.30,
        "HRM": 0.30,
        "MITO": 0.25,
        "DTX": 0.25,
        "COG": 0.20,
        "SKN": 0.10,
        "CM": 0.30  # Not specified in spec, using conservative value
    }
    
    # Uncertainty keywords
    UNCERTAINTY_KEYWORDS = [
        "maybe", "might", "possibly", "perhaps", "could be",
        "not sure", "uncertain", "think", "guess"
    ]
    
    # Negation patterns
    NEGATION_PATTERNS = [
        r'\bnot\s+(?:from|after|due to|because of)\b',
        r'\bno\s+(?:history|evidence)\b',
        r'\bnever\s+(?:had|took|used)\b',
        r'\bwithout\b'
    ]
    
    def __init__(self):
        """Initialize NLP model and preprocess lexicons."""
        self.nlp = get_spacy_model()
        
        # Initialize trigger lexicons (will be defined in next section)
        self.TRIGGER_LEXICONS = self._build_trigger_lexicons()
        
        # Preprocess all lexicons for faster matching
        self.preprocessed_lexicons = {}
        if self.nlp:
            for trigger_name, trigger_config in self.TRIGGER_LEXICONS.items():
                keywords = trigger_config["keywords"]
                self.preprocessed_lexicons[trigger_name] = preprocess_lexicons(
                    {trigger_name: keywords}, self.nlp
                ).get(trigger_name, set())
    
    def _build_trigger_lexicons(self) -> Dict[str, Dict[str, Any]]:
        """
        Build trigger lexicons with keywords and base weights.
        
        Returns:
            Dict mapping trigger names to config dicts with "keywords" and "weights"
        """
        return {
            # 1. Post-infectious (viral)
            "post_viral": {
                "keywords": [
                    "covid", "covid-19", "coronavirus", "sars-cov-2",
                    "flu", "influenza", "mono", "mononucleosis", "ebv", "epstein-barr",
                    "viral infection", "virus", "viral illness"
                ],
                "weights": {"IMM": 0.25, "MITO": 0.15}  # COG +0.10 if brain fog terms present
            },
            
            # 1. Post-infectious (bacterial/GI)
            "gastroenteritis": {
                "keywords": [
                    "food poisoning", "gastroenteritis", "stomach bug", "norovirus",
                    "campylobacter", "salmonella", "traveler's diarrhea", "traveller's diarrhea",
                    "delhi belly", "montezuma", "travelers diarrhea", "travellers diarrhea",
                    "acute diarrhea", "gi infection"
                ],
                "weights": {"GA": 0.30, "IMM": 0.10, "DTX": 0.05}
            },
            
            # 2. Accident/surgery
            "surgery": {
                "keywords": [
                    "surgery", "operation", "surgical", "anesthesia", "anaesthesia",
                    "accident", "trauma", "injury", "cholecystectomy", "appendectomy",
                    "c-section", "cesarean", "caesarean", "laparoscopic", "laparotomy"
                ],
                "weights": {"STR": 0.20, "MITO": 0.05, "IMM": 0.05}
            },

            # 3. Medications - Antibiotics
            "antibiotics": {
                "keywords": [
                    "antibiotic", "antibiotics", "amoxicillin", "azithromycin", "ciprofloxacin",
                    "cipro", "doxycycline", "metronidazole", "flagyl", "clindamycin",
                    "cephalexin", "keflex", "augmentin", "z-pack", "zpack"
                ],
                "weights": {"GA": 0.20, "IMM": 0.10, "DTX": 0.05}
            },

            # 3. Medications - PPI
            "ppi": {
                "keywords": [
                    "ppi", "proton pump inhibitor", "omeprazole", "prilosec",
                    "esomeprazole", "nexium", "pantoprazole", "protonix",
                    "lansoprazole", "prevacid", "rabeprazole", "aciphex"
                ],
                "weights": {"GA": 0.25, "DTX": 0.10, "IMM": 0.05}
            },

            # 3. Medications - NSAIDs
            "nsaids": {
                "keywords": [
                    "nsaid", "nsaids", "ibuprofen", "advil", "motrin",
                    "naproxen", "aleve", "diclofenac", "voltaren",
                    "indomethacin", "indocin", "celecoxib", "celebrex"
                ],
                "weights": {"GA": 0.15, "DTX": 0.10}
            },

            # 3. Medications - Metformin
            "metformin": {
                "keywords": [
                    "metformin", "glucophage", "metformin xr", "metformin er"
                ],
                "weights": {"GA": 0.20}
            },

            # 3. Medications - Opioids
            "opioids": {
                "keywords": [
                    "opioid", "opioids", "codeine", "hydrocodone", "vicodin",
                    "oxycodone", "oxycontin", "percocet", "morphine",
                    "tramadol", "fentanyl", "narcotic", "narcotics"
                ],
                "weights": {"GA": 0.25, "STR": 0.10}
            },

            # 4. Hormonal life events
            "postpartum": {
                "keywords": [
                    "postpartum", "post-partum", "after delivery", "after birth",
                    "after baby", "after pregnancy", "childbirth", "gave birth",
                    "baby was born", "baby born", "had baby", "new baby"
                ],
                "weights": {"HRM": 0.25, "STR": 0.05}  # COG +0.05 if brain fog terms
            },

            "perimenopause": {
                "keywords": [
                    "perimenopause", "peri-menopause", "menopause transition",
                    "menopause", "menopausal", "hot flashes", "hot flushes"
                ],
                "weights": {"HRM": 0.25, "STR": 0.05}  # COG +0.05 if brain fog terms
            },

            # 5. Environmental - Mold
            "mold": {
                "keywords": [
                    "mold", "mould", "mildew", "water damage", "water-damaged",
                    "damp", "mycotoxin", "mycotoxins", "moldy", "mouldy"
                ],
                "weights": {"IMM": 0.20, "DTX": 0.20, "GA": 0.10, "COG": 0.05}
            },

            # 5. Environmental - Chemicals
            "chemicals": {
                "keywords": [
                    "chemical", "chemicals", "solvent", "solvents", "pesticide", "pesticides",
                    "herbicide", "herbicides", "mercury", "lead", "cadmium",
                    "heavy metal", "heavy metals", "toxin", "toxins", "xenobiotic"
                ],
                "weights": {"DTX": 0.20, "IMM": 0.10, "MITO": 0.10, "GA": 0.10, "COG": 0.05}
            },

            # 6. Psychosocial/circadian
            "psychosocial_stress": {
                "keywords": [
                    "shift work", "shift-work", "job loss", "lost job", "fired",
                    "caregiving", "caregiver", "bereavement", "grief", "death",
                    "divorce", "separation", "major stress", "high stress",
                    "work stress", "financial stress", "moved", "relocation"
                ],
                "weights": {"STR": 0.25, "COG": 0.10, "CM": 0.05}
            },

            # 7. Dietary shifts (only when clearly tied to onset)
            "low_fiber_diet": {
                "keywords": [
                    "keto", "ketogenic", "carnivore", "carnivore diet",
                    "low fiber", "low-fiber", "eliminated fiber", "no fiber"
                ],
                "weights": {"GA": 0.10}  # CM -0.05 to 0 (neutral in risk scoring)
            },

            "high_fodmap_diet": {
                "keywords": [
                    "high fodmap", "ultra-processed", "processed food",
                    "junk food", "fast food"
                ],
                "weights": {"GA": 0.10, "IMM": 0.05}
            }
        }

    def _parse_recency(self, text: str, current_date: datetime = None) -> float:
        """
        Parse temporal information and return recency multiplier.

        Recency classes:
        - Very recent (<6 months): 1.2
        - Recent (6-24 months): 1.0
        - Remote (>5 years): 0.7
        - Default (no time info): 1.0

        Args:
            text: Input text
            current_date: Current date for calculations (default: now)

        Returns:
            Recency multiplier (0.7, 1.0, or 1.2)
        """
        if current_date is None:
            current_date = datetime.now()

        text_lower = text.lower()

        # Try to extract relative time (e.g., "2 months ago", "6 weeks ago")
        relative_match = re.search(r'(\d+)\s*(month|week|year|mo|wk|yr)s?\s*ago', text_lower)
        if relative_match:
            number = int(relative_match.group(1))
            unit = relative_match.group(2)

            if unit in ['week', 'wk']:
                months = number / 4.0
            elif unit in ['month', 'mo']:
                months = number
            else:  # year, yr
                months = number * 12

            if months < 6:
                return 1.2  # Very recent
            elif months <= 24:
                return 1.0  # Recent
            else:
                return 0.7  # Remote

        # Try to extract year (e.g., "in 2023", "since 2020")
        year_match = re.search(r'\b(20\d{2})\b', text_lower)
        if year_match:
            year = int(year_match.group(1))
            current_year = current_date.year
            years_ago = current_year - year
            months = years_ago * 12

            if months < 6:
                return 1.2
            elif months <= 24:
                return 1.0
            elif years_ago > 5:
                return 0.7
            else:
                return 1.0

        # Check for recent phrases
        recent_phrases = ["recently", "just", "lately", "last week", "last month"]
        if any(phrase in text_lower for phrase in recent_phrases):
            return 1.2

        # Default: no time info
        return 1.0

    def _detect_uncertainty(self, text: str) -> bool:
        """
        Detect uncertainty markers in text.

        Args:
            text: Input text

        Returns:
            True if uncertainty detected, False otherwise
        """
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.UNCERTAINTY_KEYWORDS)

    def _detect_negation(self, text: str, trigger_keyword: str) -> bool:
        """
        Detect if a trigger is negated in the text.

        Args:
            text: Input text
            trigger_keyword: The trigger keyword to check

        Returns:
            True if negated, False otherwise
        """
        text_lower = text.lower()
        keyword_lower = trigger_keyword.lower()

        # Find position of keyword
        keyword_pos = text_lower.find(keyword_lower)
        if keyword_pos == -1:
            return False

        # Check for negation patterns in the 50 characters before the keyword
        context_start = max(0, keyword_pos - 50)
        context = text_lower[context_start:keyword_pos + len(keyword_lower)]

        for pattern in self.NEGATION_PATTERNS:
            if re.search(pattern, context):
                return True

        return False

    def _detect_triggers(self, text: str) -> Dict[str, Dict[str, Any]]:
        """
        Detect trigger events in the text using NLP-based matching.

        Args:
            text: Input text

        Returns:
            Dict mapping trigger names to trigger details:
            {
                "trigger_name": {
                    "matched_text": "keyword that matched",
                    "scores": {"GA": 0.30, ...},
                    "negated": False,
                    "uncertain": False
                }
            }
        """
        triggers_found = {}
        text_lemmatized = lemmatize_text(text, self.nlp).lower() if self.nlp else text.lower()

        for trigger_name, trigger_config in self.TRIGGER_LEXICONS.items():
            matched_keywords = []

            # Get preprocessed lemmatized keywords
            lemmatized_keywords = self.preprocessed_lexicons.get(trigger_name, set())

            # Try exact match on lemmatized text (with word boundaries)
            for lemma_keyword in lemmatized_keywords:
                # Use word boundaries to avoid substring matches (e.g., "flu" in "reflux")
                pattern = r'\b' + re.escape(lemma_keyword) + r'\b'
                if re.search(pattern, text_lemmatized):
                    # Find original keyword
                    for orig_keyword in trigger_config["keywords"]:
                        if lemmatize_text(orig_keyword, self.nlp).lower() == lemma_keyword:
                            matched_keywords.append(orig_keyword)
                            break

            # If no exact match, try fuzzy matching
            if not matched_keywords and RAPIDFUZZ_AVAILABLE:
                for keyword in trigger_config["keywords"]:
                    if match_keyword_fuzzy(keyword, text, threshold=85):
                        matched_keywords.append(keyword)

            if matched_keywords:
                matched_keyword = matched_keywords[0]

                # Check for negation
                is_negated = self._detect_negation(text, matched_keyword)

                if not is_negated:
                    triggers_found[trigger_name] = {
                        "matched_text": matched_keyword,
                        "scores": trigger_config["weights"].copy(),
                        "negated": False,
                        "uncertain": False  # Will be set globally later
                    }

        return triggers_found

    def _detect_brain_fog_terms(self, text: str) -> bool:
        """Detect brain fog / cognitive terms in text."""
        brain_fog_terms = [
            "brain fog", "brainfog", "memory", "concentration", "focus",
            "cognitive", "mental clarity", "confusion", "forgetful"
        ]
        text_lower = text.lower()
        return any(term in text_lower for term in brain_fog_terms)

    def _detect_gi_symptoms(self, text: str) -> bool:
        """Detect GI symptom terms in text."""
        gi_terms = [
            "constipation", "reflux", "heartburn", "gerd", "ibs",
            "bloating", "diarrhea", "gas", "nausea"
        ]
        text_lower = text.lower()
        return any(term in text_lower for term in gi_terms)

    def get_trigger_event_weights(
        self,
        text: str,
        age: int = None,
        sex: str = None,
        current_date: datetime = None
    ) -> Tuple[Dict[str, float], Dict[str, bool], List[Dict[str, Any]]]:
        """
        Calculate focus area weights from trigger event text.

        Args:
            text: Free-text response about trigger events
            age: Patient age (required, must be >= 18)
            sex: Patient sex ("Male"/"Female", optional, reserved for future use)
            current_date: Current date for recency calculations (default: now)

        Returns:
            Tuple of (scores_dict, flags_dict, detail_list)
            - scores_dict: Focus area scores
            - flags_dict: {"urgent_care": bool} for red flag detection
            - detail_list: List of dicts with breakdown for reason tracking
              [{"type": "trigger", "trigger_name": "post_viral", "matched_text": "COVID",
                "recency_multiplier": 1.2, "uncertainty_multiplier": 1.0, "scores": {...}}]
        """
        # Initialize scores
        scores = {code: 0.0 for code in FOCUS_AREAS}
        flags = {"urgent_care": False}
        details = []

        # Age check: Only score if age >= 18
        if age is None or age < 18:
            return scores, flags, details

        # Empty text check
        if not text or not text.strip():
            return scores, flags, details

        # Detect global uncertainty
        has_uncertainty = self._detect_uncertainty(text)
        uncertainty_multiplier = 0.7 if has_uncertainty else 1.0

        # Parse recency
        recency_multiplier = self._parse_recency(text, current_date)

        # Detect triggers
        triggers_found = self._detect_triggers(text)

        # Apply uncertainty flag to all triggers
        for trigger_name in triggers_found:
            triggers_found[trigger_name]["uncertain"] = has_uncertainty

        # Conditional additions based on context
        has_brain_fog = self._detect_brain_fog_terms(text)
        has_gi_symptoms = self._detect_gi_symptoms(text)

        # Apply base weights with multipliers
        for trigger_name, trigger_info in triggers_found.items():
            base_scores = trigger_info["scores"].copy()

            # Apply conditional additions
            if trigger_name == "post_viral" and has_brain_fog:
                base_scores["COG"] = base_scores.get("COG", 0.0) + 0.10

            if trigger_name in ["postpartum", "perimenopause"] and has_brain_fog:
                base_scores["COG"] = base_scores.get("COG", 0.0) + 0.05

            if trigger_name == "postpartum" and has_gi_symptoms:
                base_scores["GA"] = base_scores.get("GA", 0.0) + 0.15

            if trigger_name == "psychosocial_stress" and has_gi_symptoms:
                base_scores["GA"] = base_scores.get("GA", 0.0) + 0.10

            # Apply multipliers
            final_scores = {}
            for domain, score in base_scores.items():
                final_scores[domain] = score * uncertainty_multiplier * recency_multiplier

            # Add to total scores
            for domain, score in final_scores.items():
                scores[domain] += score

            # Track detail
            details.append({
                "type": "trigger",
                "trigger_name": trigger_name,
                "matched_text": trigger_info["matched_text"],
                "recency_multiplier": recency_multiplier,
                "uncertainty_multiplier": uncertainty_multiplier,
                "scores": final_scores
            })

        # Apply synergy rules
        synergy_applied = []

        # Synergy 1: Gastroenteritis + Antibiotics → extra GA +0.10
        if "gastroenteritis" in triggers_found and "antibiotics" in triggers_found:
            synergy_score = 0.10 * uncertainty_multiplier * recency_multiplier
            scores["GA"] += synergy_score
            synergy_applied.append({
                "type": "synergy",
                "synergy_name": "gastroenteritis_antibiotics",
                "description": "GI infection + antibiotics",
                "scores": {"GA": synergy_score}
            })

        # Synergy 2: Antibiotics + PPI → extra GA +0.05
        if "antibiotics" in triggers_found and "ppi" in triggers_found:
            synergy_score = 0.05 * uncertainty_multiplier * recency_multiplier
            scores["GA"] += synergy_score
            synergy_applied.append({
                "type": "synergy",
                "synergy_name": "antibiotics_ppi",
                "description": "Antibiotics + PPI",
                "scores": {"GA": synergy_score}
            })

        # Add synergies to details
        details.extend(synergy_applied)

        # Global allostatic load: If >= 3 distinct triggers, add STR +0.05
        if len(triggers_found) >= 3:
            allostatic_score = 0.05 * uncertainty_multiplier * recency_multiplier
            scores["STR"] += allostatic_score
            details.append({
                "type": "allostatic_load",
                "trigger_count": len(triggers_found),
                "description": f"{len(triggers_found)} triggers detected",
                "scores": {"STR": allostatic_score}
            })

        # Apply per-domain caps
        for domain in FOCUS_AREAS:
            if domain in self.DOMAIN_CAPS:
                scores[domain] = min(scores[domain], self.DOMAIN_CAPS[domain])

        return scores, flags, details

