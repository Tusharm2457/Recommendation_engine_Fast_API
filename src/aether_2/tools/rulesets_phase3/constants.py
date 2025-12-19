"""
Phase 3-Specific Constants

This module contains constants specific to Phase 3 rulesets.
Shared constants (FOCUS_AREAS, add_top_contributors, etc.) are imported from Phase 2.
"""

# Import shared constants from Phase 2
from ..rulesets.constants import (
    FOCUS_AREAS,
    FOCUS_AREA_NAMES,
    add_top_contributors,
    SHIFT_WORK_KEYWORDS,
    detect_shift_work
)

# Phase 3 Field Context Mapping
# Maps field position number to human-readable context name for reason tracking
PHASE3_FIELD_CONTEXT = {
    0: "TopHealthGoals",           # Top 3 health goals
    1: "PatientReasoning",         # Patient's causal reasoning about their condition
    2: "LifestyleWillingness",     # Adherence/lifestyle change willingness
    3: "LastFeltWell",             # When they last felt well
    4: "WhatStartedWorsened",      # What started or worsened symptoms
    5: "WhatMakesWorse",           # What makes symptoms worse
    6: "PartOfDay",                # Time of day when symptoms worsen
    7: "WhereSymptomsWorse",       # Location where symptoms get worse
    8: "FoodDrinkTriggers",        # Food/drink triggers
    9: "WhatHelps",                # What helps symptoms
    10: "AntibioticsMedsHistory",  # Antibiotics/medications history
    11: "ActivityIntensity",       # Physical activity intensity
    12: "SunlightExposure",        # Sunlight exposure ranking
    13: "SleepAids",               # Sleep aids and medicines
    14: "ConsistentSleepSchedule", # Consistent sleep schedule
    15: "ConsistentWakeTime",      # Consistent wake time
    16: "TypicalMeals",            # Typical meals and snacks (LLM-based)
    17: "FoodAvoidance",           # Foods avoided due to symptoms (NLP-based)
    18: "FoodCravings",            # Food cravings (multi-select with substring matching)
    19: "Mood",                    # Mood description (NLP-based lexicon matching)
    20: "CurrentStress",           # Current stress level (1-10 scale, linear + piecewise)
    21: "StressSources",           # Biggest sources of stress (NLP-based stressor categorization)
    22: "RelaxationTechniques",    # Relaxation techniques used (multi-select with substring matching)
    23: "SupportSources",          # Who or what do you lean on for support (multi-select with text mapping)
    24: "TraumaAbuse",             # Significant trauma or abuse history (NLP-based with crisis screening)
    25: "ChildhoodIllnesses",      # Significant illnesses during childhood (NLP-based with age/frequency multipliers)
    26: "ChildhoodHomeSecurity",   # Childhood home security and early-life adversity (NLP-based with severity tiers)
    27: "Breastfeeding",           # Breastfeeding history (radio + duration with cross-field synergies)
    28: "EarlyEnvironmentalExposures",  # Early environmental/toxic exposures (NLP-based with duration/intensity multipliers)
    29: "ToothSensitivity",        # Tooth sensitivity (NLP-based with mechanistic scoring)
    30: "CurrentEnvironmentalExposures",  # Current home/workplace environmental exposures (multi-select with NLP-based scoring)
    31: "ChemicalSensitivity",  # Chemical sensitivity (radio with optional free text)
    32: "CaffeineReaction",  # Caffeine reaction (radio with context-driven scoring)
    33: "AlcoholFlushing",  # Alcohol flushing (radio + optional free text with context-driven scoring)
    34: "SyntheticFiberWear",  # Regular synthetic fiber wear (multi-select with optional free text)
    35: "SeasonalAllergies",  # Seasonal allergies (radio with optional free text)
    37: "AirFilter",  # Air filter usage (radio with optional brand/model text)
}

# ============================================================================
# NLP UTILITIES - Shared across Phase 3 rulesets
# ============================================================================

from typing import Dict, Set, Optional
import warnings

# Check for optional NLP libraries
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    warnings.warn(
        "spaCy not available. Install with: pip install spacy && python -m spacy download en_core_web_sm",
        ImportWarning
    )

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    warnings.warn(
        "rapidfuzz not available. Install with: pip install rapidfuzz",
        ImportWarning
    )

# Global spaCy model instance (loaded once, shared across all rulesets)
_SPACY_NLP = None


def get_spacy_model():
    """
    Get or load the shared spaCy model.

    Returns:
        spaCy Language model or None if not available
    """
    global _SPACY_NLP, SPACY_AVAILABLE

    if not SPACY_AVAILABLE:
        return None

    if _SPACY_NLP is None:
        try:
            import spacy
            _SPACY_NLP = spacy.load("en_core_web_sm", disable=["parser", "ner"])
            print("✅ spaCy model loaded successfully (lemmatization enabled)")
        except OSError:
            print("⚠️  spaCy model not found. Run: python -m spacy download en_core_web_sm")
            print("   Falling back to basic substring matching")
            SPACY_AVAILABLE = False
            return None

    return _SPACY_NLP


def preprocess_lexicons(lexicons: Dict[str, list], nlp=None) -> Dict[str, Set[str]]:
    """
    Pre-lemmatize all keywords in lexicons for faster matching.

    Args:
        lexicons: Dict mapping domain codes to lists of keywords
        nlp: Optional spaCy model (will load if not provided)

    Returns:
        Dict mapping domain codes to sets of lemmatized keywords

    Example:
        >>> lexicons = {"CM": ["lose weight", "losing weight"]}
        >>> preprocess_lexicons(lexicons)
        {"CM": {"lose weight"}}  # Both lemmatize to same form
    """
    if nlp is None:
        nlp = get_spacy_model()

    if not nlp:
        return {}

    lemmatized = {}

    for domain, keywords in lexicons.items():
        lemmatized[domain] = set()
        for keyword in keywords:
            # Lemmatize multi-word phrases
            doc = nlp(keyword)
            lemma_phrase = " ".join([token.lemma_ for token in doc])
            lemmatized[domain].add(lemma_phrase)

    return lemmatized


def lemmatize_text(text: str, nlp=None) -> str:
    """
    Convert text to lemmatized form.

    Args:
        text: Input text
        nlp: Optional spaCy model (will load if not provided)

    Returns:
        Lemmatized text

    Examples:
        >>> lemmatize_text("losing weight")
        "lose weight"
        >>> lemmatize_text("stressed out")
        "stress out"
        >>> lemmatize_text("energies")
        "energy"
    """
    if nlp is None:
        nlp = get_spacy_model()

    if not nlp:
        return text

    doc = nlp(text)
    return " ".join([token.lemma_ for token in doc])


def match_keyword_fuzzy(keyword: str, text: str, threshold: int = 85) -> bool:
    """
    Match keyword with fuzzy matching for typos.

    Args:
        keyword: The keyword to search for
        text: The text to search in
        threshold: 0-100, higher = stricter (85 is good default)

    Returns:
        True if fuzzy match found above threshold

    Examples:
        >>> match_keyword_fuzzy("lose weight", "loose weight")
        True  # 91% match
        >>> match_keyword_fuzzy("energy", "enrgy", threshold=80)
        True  # 83% match
    """
    if not RAPIDFUZZ_AVAILABLE:
        return False

    from rapidfuzz import fuzz, process

    words = text.split()
    keyword_word_count = len(keyword.split())

    # Generate n-grams matching keyword length
    phrases = []
    for i in range(len(words) - keyword_word_count + 1):
        phrase = " ".join(words[i:i + keyword_word_count])
        phrases.append(phrase)

    # Find best fuzzy match
    if phrases:
        best_match = process.extractOne(keyword, phrases, scorer=fuzz.ratio)
        if best_match and best_match[1] >= threshold:
            return True

    return False


# ============================================================================
# LLM UTILITIES - For complex NLP tasks
# ============================================================================

def call_vertex_ai_llm(prompt: str, temperature: float = 0.0, model: str = "vertex_ai/gemini-2.5-flash") -> str:
    """
    Make a simple, independent API call to Vertex AI using LiteLLM.

    This is a standalone helper function that doesn't link to CrewAI agents.
    Can be reused across different Phase 3 rulesets that need LLM categorization.

    Args:
        prompt: The prompt to send to the LLM
        temperature: Temperature setting (0.0 = deterministic, 1.0 = creative)
        model: Model identifier (default: vertex_ai/gemini-2.5-flash)

    Returns:
        String response from the LLM

    Example:
        >>> prompt = "Categorize this diet: pizza, soda, candy"
        >>> response = call_vertex_ai_llm(prompt, temperature=0.0)
        >>> print(response)
        "Refined carbs/UPF, Carbonated beverages"
    """
    try:
        from litellm import completion

        # Make API call
        response = completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=1500  # Increased to ensure full category lists are returned
        )

        # Extract text from response
        if response and response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            if content is not None:
                return content.strip()
            else:
                print(f"⚠️  LLM returned None content")
                return ""
        else:
            print(f"⚠️  Empty response from LLM")
            return ""

    except Exception as e:
        print(f"❌ Error calling Vertex AI LLM: {e}")
        return ""


# Export all shared constants plus Phase 3-specific ones
__all__ = [
    # Shared from Phase 2
    "FOCUS_AREAS",
    "FOCUS_AREA_NAMES",
    "add_top_contributors",
    "SHIFT_WORK_KEYWORDS",
    "detect_shift_work",
    # Phase 3-specific
    "PHASE3_FIELD_CONTEXT",
    # NLP utilities
    "SPACY_AVAILABLE",
    "RAPIDFUZZ_AVAILABLE",
    "get_spacy_model",
    "preprocess_lexicons",
    "lemmatize_text",
    "match_keyword_fuzzy",
    # LLM utilities
    "call_vertex_ai_llm",
]

