"""
Trouble Falling Asleep Ruleset

Scores focus areas based on difficulty initiating sleep.

Evidence:
- Sleep onset difficulty: Associated with stress-axis dysregulation, cognitive impairment
- Protective effect: Good sleep initiation supports stress resilience and cognitive function

Modifiers:
- Shift work: Adds STR +0.10 (circadian mismatch)
- Daily alcohol: Adds STR +0.05 (disrupts sleep architecture)
- Current smoking: Adds STR +0.10 (nicotine stimulant effect)

Author: Aether AI Engine
Date: 2025-11-19
"""

from typing import Dict, Tuple, Optional
from .constants import FOCUS_AREAS


class TroubleFallingAsleepRuleset:
    """Ruleset for sleep onset difficulty scoring."""
    
    TOP_N_CONTRIBUTORS = 1
    
    def get_trouble_falling_asleep_weights(
        self,
        trouble_falling_asleep: Optional[bool],
        shift_work: bool = False,
        alcohol_frequency: Optional[str] = None,
        currently_smoking: bool = False
    ) -> Tuple[Dict[str, float], str]:
        """
        Calculate focus area weights based on sleep onset difficulty.
        
        Args:
            trouble_falling_asleep: True if has difficulty falling asleep, False otherwise
            shift_work: Whether user does shift work (circadian mismatch)
            alcohol_frequency: Alcohol consumption frequency (e.g., "daily", "weekly")
            currently_smoking: Whether user currently smokes tobacco
            
        Returns:
            Tuple of (scores dict, description string for reasons file)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        
        # If no data provided, return zeros
        if trouble_falling_asleep is None:
            return (scores, "")
        
        # Base scoring
        if not trouble_falling_asleep:
            # No trouble falling asleep (protective)
            scores["STR"] = -0.05
            scores["COG"] = -0.05
            description = "No"
        else:
            # Has trouble falling asleep
            scores["STR"] = 0.25
            scores["COG"] = 0.15
            scores["MITO"] = 0.05
            scores["IMM"] = 0.05
            scores["CM"] = 0.05
            description = "Yes"
        
        # Modifiers (only apply if has trouble falling asleep)
        modifiers = []
        
        if shift_work:
            scores["STR"] += 0.10
            
        
        if alcohol_frequency and alcohol_frequency.lower() == "daily":
            scores["STR"] += 0.05
            
        
        if currently_smoking:
            scores["STR"] += 0.10
            
    
        
        return (scores, description)

