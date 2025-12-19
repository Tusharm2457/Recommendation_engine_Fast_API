from typing import Dict, Any, List, Set
from .constants import FOCUS_AREAS
from .helpers import parse_yes_no_with_followup


class SleepAidsRuleset:
    """
    Ruleset for evaluating sleep aids and medicines usage.
    
    Analyzes sleep aid usage patterns to assess impacts on:
    - Cognitive function (anticholinergics, sedatives)
    - Stress-axis/sleep quality
    - GI function (anticholinergic effects, opioid-induced constipation)
    - Mitochondrial function (long-term sedative use)
    """
    
    # Per-domain caps for this field
    CAPS = {
        "COG": 0.60,
        "STR": 0.50,
        "GA": 0.50,
        "MITO": 0.30,
        "CM": 0.20,
        "DTX": 0.20,
        "IMM": 0.20,
        "SKN": 0.20,
        "HRM": 0.20
    }
    
    # NLP Lexicon for sleep aid classification
    MELATONIN_KEYWORDS = ["melatonin", "mlt", "circadin"]
    
    OTC_ANTICHOLINERGIC_KEYWORDS = [
        "diphenhydramine", "doxylamine", "hydroxyzine", "promethazine",
        "benadryl", "unisom"
    ]
    
    SEDATIVE_HYPNOTIC_KEYWORDS = [
        "temazepam", "lorazepam", "clonazepam", "alprazolam", "diazepam",
        "zolpidem", "eszopiclone", "zopiclone", "ambien", "lunesta"
    ]
    
    SEDATING_AD_ANTIPSYCHOTIC_KEYWORDS = [
        "trazodone", "mirtazapine", "quetiapine", "doxepin", "seroquel", "remeron"
    ]
    
    OPIOID_KEYWORDS = [
        "codeine", "hydrocodone", "oxycodone", "tramadol", "morphine",
        "oxycontin", "vicodin", "percocet"
    ]
    
    MAGNESIUM_KEYWORDS = [
        "magnesium", "mag citrate", "mag glycinate", "mag oxide",
        "magnesium citrate", "magnesium glycinate", "magnesium oxide"
    ]
    
    HERBAL_KEYWORDS = [
        "valerian", "passionflower", "chamomile", "lavender", "ashwagandha"
    ]
    
    # Effect terms
    POSITIVE_EFFECT_KEYWORDS = ["helps", "better sleep", "improved", "works well", "effective"]
    NEGATIVE_EFFECT_KEYWORDS = ["groggy", "grogginess", "vivid dreams", "nightmares"]
    GI_EFFECT_KEYWORDS = [
        "constipation", "slow bowels", "slow bm", "nocturnal reflux",
        "diarrhea", "loose stools", "loose stool"
    ]
    
    def get_sleep_aids_weights(
        self,
        sleep_aids_data: Any,
        age: int = None,
        reflux_flag: bool = False
    ) -> Dict[str, float]:
        """
        Calculate focus area weights based on sleep aids usage.
        
        Args:
            sleep_aids_data: Yes/No + followup text
                            Format: "Yes; Melatonin 3mg, helps with sleep" or "No"
            age: Patient age (must be >= 18)
            reflux_flag: Whether patient has reflux/heartburn (from other fields)
        
        Returns:
            Dictionary mapping focus area codes to weight adjustments
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # Age check
        if age and age < 18:
            return scores
        
        # Parse yes/no + followup
        is_yes, followup_text = parse_yes_no_with_followup(sleep_aids_data)
        
        if not is_yes or not followup_text:
            # No sleep aids or no details provided
            return scores
        
        # Classify sleep aids from free text
        text_lower = followup_text.lower()
        classes = self._classify_sleep_aids(text_lower)
        effects = self._extract_effects(text_lower)
        
        # Extract usage patterns (duration, frequency)
        duration_months = self._extract_duration_months(text_lower)
        use_days_per_year = self._extract_frequency_days_per_year(text_lower)
        
        # Apply decision rules
        scores = self._apply_melatonin_rules(scores, classes, effects, reflux_flag)
        scores = self._apply_otc_anticholinergic_rules(scores, classes, use_days_per_year)
        scores = self._apply_sedative_hypnotic_rules(scores, classes, duration_months, age)
        scores = self._apply_sedating_ad_rules(scores, classes, effects)
        scores = self._apply_opioid_rules(scores, classes)
        scores = self._apply_magnesium_rules(scores, classes, effects, text_lower)
        scores = self._apply_herbal_rules(scores, classes, effects)
        scores = self._apply_gi_hypomotility_rules(scores, classes, effects)
        
        # Apply caps
        for domain in scores:
            if scores[domain] > 0:
                scores[domain] = min(scores[domain], self.CAPS.get(domain, 1.0))
            else:
                scores[domain] = max(scores[domain], -self.CAPS.get(domain, 1.0))
        
        return scores
    
    def _classify_sleep_aids(self, text: str) -> Set[str]:
        """
        Classify which sleep aid categories are mentioned in the text.
        
        Returns:
            Set of class names: {"melatonin", "otc_anticholinergic", ...}
        """
        classes = set()
        
        if any(kw in text for kw in self.MELATONIN_KEYWORDS):
            classes.add("melatonin")
        
        if any(kw in text for kw in self.OTC_ANTICHOLINERGIC_KEYWORDS):
            classes.add("otc_anticholinergic")
        
        if any(kw in text for kw in self.SEDATIVE_HYPNOTIC_KEYWORDS):
            classes.add("sedative_hypnotic")
        
        if any(kw in text for kw in self.SEDATING_AD_ANTIPSYCHOTIC_KEYWORDS):
            classes.add("sedating_ad_or_antipsychotic")
        
        if any(kw in text for kw in self.OPIOID_KEYWORDS):
            classes.add("opioid")
        
        if any(kw in text for kw in self.MAGNESIUM_KEYWORDS):
            classes.add("magnesium")
        
        if any(kw in text for kw in self.HERBAL_KEYWORDS):
            classes.add("herbal")
        
        return classes

    def _extract_effects(self, text: str) -> Set[str]:
        """Extract effect terms from text."""
        effects = set()

        if any(kw in text for kw in self.POSITIVE_EFFECT_KEYWORDS):
            effects.add("helps")

        if any(kw in text for kw in self.NEGATIVE_EFFECT_KEYWORDS):
            effects.add("groggy")

        if "constipation" in text or "slow bowel" in text or "slow bm" in text:
            effects.add("constipation")

        if "nocturnal reflux" in text or "night reflux" in text:
            effects.add("nocturnal_reflux")

        if "diarrhea" in text or "loose stool" in text:
            effects.add("diarrhea")

        return effects

    def _extract_duration_months(self, text: str) -> int:
        """
        Extract duration in months from text.

        Looks for patterns like:
        - "6 months", "6mo", "6 mos"
        - "1 year", "2 years" (convert to months)
        - "nightly for 6 months"
        """
        import re

        # Look for "X months" or "X mo"
        month_match = re.search(r'(\d+)\s*(month|months|mo|mos)', text)
        if month_match:
            return int(month_match.group(1))

        # Look for "X years"
        year_match = re.search(r'(\d+)\s*(year|years|yr|yrs)', text)
        if year_match:
            return int(year_match.group(1)) * 12

        # Default: assume regular use if mentioned
        if "nightly" in text or "every night" in text or "daily" in text:
            return 6  # Assume 6 months if nightly use mentioned

        return 0

    def _extract_frequency_days_per_year(self, text: str) -> int:
        """
        Extract frequency in days per year.

        Looks for patterns like:
        - "nightly", "every night" → 365 days
        - "3-4 nights/week" → ~200 days
        - "occasionally" → ~50 days
        """
        if "nightly" in text or "every night" in text or "daily" in text:
            return 365

        if "most nights" in text or "almost every night" in text:
            return 300

        if "3-4 nights" in text or "3 to 4 nights" in text or "several nights" in text:
            return 200

        if "occasionally" in text or "sometimes" in text or "as needed" in text:
            return 50

        # Default: assume regular use if specific medication mentioned
        return 180  # Assume ~half the year

    def _apply_melatonin_rules(
        self,
        scores: Dict[str, float],
        classes: Set[str],
        effects: Set[str],
        reflux_flag: bool
    ) -> Dict[str, float]:
        """
        A) Melatonin rules.

        Regular use with reported benefit → STR -0.10, GA -0.10
        Reflux + melatonin → extra GA -0.05
        """
        if "melatonin" not in classes:
            return scores

        # Only apply benefit if user reports positive effects
        if "helps" in effects:
            scores["STR"] -= 0.10
            scores["GA"] -= 0.10

            # Extra benefit for reflux
            if reflux_flag:
                scores["GA"] -= 0.05

        return scores

    def _apply_otc_anticholinergic_rules(
        self,
        scores: Dict[str, float],
        classes: Set[str],
        use_days_per_year: int
    ) -> Dict[str, float]:
        """
        B) OTC anticholinergic antihistamines.

        Nightly/near-nightly use (≥90 days/yr) → COG +0.25, STR +0.05, GA +0.10
        If >180 days/yr → COG +0.35
        """
        if "otc_anticholinergic" not in classes:
            return scores

        if use_days_per_year >= 180:
            scores["COG"] += 0.35
            scores["STR"] += 0.05
            scores["GA"] += 0.10
        elif use_days_per_year >= 90:
            scores["COG"] += 0.25
            scores["STR"] += 0.05
            scores["GA"] += 0.10

        return scores

    def _apply_sedative_hypnotic_rules(
        self,
        scores: Dict[str, float],
        classes: Set[str],
        duration_months: int,
        age: int
    ) -> Dict[str, float]:
        """
        C) Prescription sedative-hypnotics.

        Any regular/nightly use → COG +0.30, STR +0.10, MITO +0.10
        If ≥6 months → COG +0.40
        If age > 60 → extra COG +0.10
        """
        if "sedative_hypnotic" not in classes:
            return scores

        # Base scores for any regular use
        if duration_months >= 6:
            scores["COG"] += 0.40
        else:
            scores["COG"] += 0.30

        scores["STR"] += 0.10
        scores["MITO"] += 0.10

        # Cross-field: age > 60
        if age and age > 60:
            scores["COG"] += 0.10

        return scores

    def _apply_sedating_ad_rules(
        self,
        scores: Dict[str, float],
        classes: Set[str],
        effects: Set[str]
    ) -> Dict[str, float]:
        """
        D) Sedating antidepressants/antipsychotics.

        Nightly use → COG +0.10
        If constipation reported → GA +0.10
        """
        if "sedating_ad_or_antipsychotic" not in classes:
            return scores

        scores["COG"] += 0.10

        if "constipation" in effects:
            scores["GA"] += 0.10

        return scores

    def _apply_opioid_rules(
        self,
        scores: Dict[str, float],
        classes: Set[str]
    ) -> Dict[str, float]:
        """
        E) Opioids taken at night.

        Any chronic use → GA +0.40, STR +0.10
        """
        if "opioid" not in classes:
            return scores

        scores["GA"] += 0.40
        scores["STR"] += 0.10

        return scores

    def _apply_magnesium_rules(
        self,
        scores: Dict[str, float],
        classes: Set[str],
        effects: Set[str],
        text: str
    ) -> Dict[str, float]:
        """
        F) Magnesium at bedtime.

        Citrate/glycinate with benefit → STR -0.05, GA -0.05
        Oxide with loose stools → GA +0.10
        """
        if "magnesium" not in classes:
            return scores

        # Check for magnesium oxide specifically
        if "mag oxide" in text or "magnesium oxide" in text:
            if "diarrhea" in effects:
                scores["GA"] += 0.10
        else:
            # Citrate/glycinate with benefit
            if "helps" in effects:
                scores["STR"] -= 0.05
                scores["GA"] -= 0.05

        return scores

    def _apply_herbal_rules(
        self,
        scores: Dict[str, float],
        classes: Set[str],
        effects: Set[str]
    ) -> Dict[str, float]:
        """
        G) Herbal sleep aids.

        Clear benefit, no adverse effects → STR -0.05
        """
        if "herbal" not in classes:
            return scores

        # Only apply benefit if user reports positive effects and no negative effects
        if "helps" in effects and "groggy" not in effects:
            scores["STR"] -= 0.05

        return scores

    def _apply_gi_hypomotility_rules(
        self,
        scores: Dict[str, float],
        classes: Set[str],
        effects: Set[str]
    ) -> Dict[str, float]:
        """
        H) Sedative use + constipation/slow BMs/reflux.

        If sedative + GI symptoms → GA +0.20
        """
        # Check if using sedatives that can cause GI issues
        has_gi_affecting_sedative = (
            "sedative_hypnotic" in classes or
            "otc_anticholinergic" in classes or
            "opioid" in classes
        )

        # Check if GI symptoms present
        has_gi_symptoms = (
            "constipation" in effects or
            "nocturnal_reflux" in effects
        )

        if has_gi_affecting_sedative and has_gi_symptoms:
            scores["GA"] += 0.20

        return scores

