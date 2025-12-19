"""
Ruleset for Field 31: Caffeine Reaction

Field name: Caffeine Reaction
Assistant prompt: "How do you typically react to caffeine?"
Accepted values: Sensitive | Tolerant | Don't use caffeine

Scoring approach:
- Decision tree based on user's choice (Sensitive, Tolerant, Don't use)
- Context-driven add-ons based on cross-field data
- Additive, monotonic scoring (transparent like clinical scores)

Evidence base:
- Caffeine raises cortisol & sympathetic tone
- GERD symptoms can worsen with coffee (person-specific)
- Coffee can trigger rectosigmoid motor response
- Moderate intake not linked to higher arrhythmia risk overall
- Caffeine impairs sleep onset/quality near bedtime
- Can potentiate hyper-arousal in stressed insomniacs
"""

from typing import Dict, List, Tuple, Any
import re


class CaffeineReactionRuleset:
    """Ruleset for evaluating caffeine reaction (radio selection with context-driven scoring)."""
    
    # Per-field cap (all domains)
    MAX_WEIGHT = 1.0
    
    def __init__(self):
        pass
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text: lowercase, collapse whitespace."""
        if not text:
            return ""
        text = str(text).lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def get_caffeine_reaction_weights(
        self,
        caffeine_reaction: Any,
        digestive_symptoms: str = "",
        diagnoses_other: str = "",
        current_stress: int = 0,
        has_hypertension: bool = False
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights for caffeine reaction.
        
        Args:
            caffeine_reaction: User's caffeine reaction choice (Sensitive | Tolerant | Don't use caffeine)
            digestive_symptoms: Digestive symptoms from Phase 2 (for reflux/heartburn detection)
            diagnoses_other: Other diagnoses from medical history (for IBS-D, palpitations, insomnia detection)
            current_stress: Current stress level (1-10 scale) from Field 20
            has_hypertension: Whether user has hypertension diagnosis
            
        Returns:
            Tuple of (weights dict, flags list)
        """
        weights: Dict[str, float] = {}
        flags: List[str] = []
        
        # Validate input
        if not caffeine_reaction:
            return weights, flags
        
        # Normalize choice
        choice = self._normalize_text(str(caffeine_reaction))
        
        # Validate choice
        valid_choices = ["sensitive", "tolerant", "don't use caffeine", "dont use caffeine"]
        if choice not in valid_choices:
            flags.append(f"Invalid choice: '{caffeine_reaction}' (expected: Sensitive | Tolerant | Don't use caffeine)")
            return weights, flags
        
        # Normalize cross-field data
        digestive_symptoms_norm = self._normalize_text(digestive_symptoms)
        diagnoses_other_norm = self._normalize_text(diagnoses_other)
        
        # A1) Sensitive (jittery/palpitations)
        if choice == "sensitive":
            # Baseline weights
            weights["STR"] = weights.get("STR", 0.0) + 0.30  # Adrenergic arousal
            weights["HRM"] = weights.get("HRM", 0.0) + 0.10  # Catecholamine handling
            weights["COG"] = weights.get("COG", 0.0) + 0.10  # Anxiety/rumination risk
            weights["MITO"] = weights.get("MITO", 0.0) + 0.10  # Heightened sympathetic demand
            
            flags.append("Caffeine sensitivity detected (jittery/palpitations)")
            
            # Context add-ons
            # Reflux/heartburn
            if re.search(r'\b(reflux|heartburn|gerd)\b', digestive_symptoms_norm):
                weights["GA"] = weights.get("GA", 0.0) + 0.20
                flags.append("Cross-field synergy: Reflux/heartburn + caffeine sensitivity → GA +0.20")
            
            # Loose stools/IBS-D/diarrhea
            if re.search(r'\b(diarrhea|ibs-d|ibs d|loose stools?|frequent stools?)\b', diagnoses_other_norm):
                weights["GA"] = weights.get("GA", 0.0) + 0.20
                flags.append("Cross-field synergy: IBS-D/diarrhea + caffeine sensitivity → GA +0.20")
            
            # Palpitations
            if re.search(r'\bpalpitations?\b', diagnoses_other_norm):
                weights["CM"] = weights.get("CM", 0.0) + 0.10
                flags.append("Cross-field synergy: Palpitations + caffeine sensitivity → CM +0.10")
            
            # Sleep loss/insomnia (late dosing)
            # Note: We don't have late dosing data, so we check for insomnia/sleep issues
            if re.search(r'\b(insomnia|sleep loss|poor sleep|sleep disorder)\b', diagnoses_other_norm):
                weights["COG"] = weights.get("COG", 0.0) + 0.10
                weights["STR"] = weights.get("STR", 0.0) + 0.10
                flags.append("Cross-field synergy: Sleep issues + caffeine sensitivity → COG +0.10, STR +0.10")
            
            # Broader chemical sensitivity or alcohol intolerance
            # (Not implemented - would need additional field data)
        
        # A2) Tolerant
        elif choice == "tolerant":
            # No baseline weights
            flags.append("Caffeine tolerance (no baseline weights)")
            
            # Synergy modifiers
            # Very high stress (≥8/10) or insomnia
            has_high_stress = current_stress >= 8
            has_insomnia = re.search(r'\binsomnia\b', diagnoses_other_norm) is not None
            
            if has_high_stress or has_insomnia:
                weights["STR"] = weights.get("STR", 0.0) + 0.10
                weights["COG"] = weights.get("COG", 0.0) + 0.05
                if has_high_stress:
                    flags.append(f"Cross-field synergy: High stress ({current_stress}/10) + caffeine tolerance → STR +0.10, COG +0.05")
                if has_insomnia:
                    flags.append("Cross-field synergy: Insomnia + caffeine tolerance → STR +0.10, COG +0.05")
            
            # GERD worsened by coffee
            if re.search(r'\b(reflux|heartburn|gerd)\b', digestive_symptoms_norm):
                weights["GA"] = weights.get("GA", 0.0) + 0.10
                flags.append("Cross-field synergy: GERD + caffeine tolerance → GA +0.10")
            
            # Hypertension with acute caffeine sensitivity
            # Note: "acute caffeine sensitivity" is not directly available, so we apply if hypertension exists
            if has_hypertension:
                weights["CM"] = weights.get("CM", 0.0) + 0.05
                flags.append("Cross-field synergy: Hypertension + caffeine tolerance → CM +0.05 (watchlist)")
        
        # A3) Don't use caffeine
        elif choice in ["don't use caffeine", "dont use caffeine"]:
            # No change (avoidance by preference)
            flags.append("Caffeine avoidance (no weights applied)")
        
        # Apply per-field cap
        for domain in weights:
            if weights[domain] > self.MAX_WEIGHT:
                flags.append(f"Per-field cap applied: {domain} capped at +{self.MAX_WEIGHT:.2f}")
                weights[domain] = self.MAX_WEIGHT
        
        # Remove zero/negative weights
        weights = {k: v for k, v in weights.items() if v > 0}
        
        return weights, flags

