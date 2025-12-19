"""
Shared constants for all rulesets.
"""

from typing import Dict, List, Any, Optional

FOCUS_AREAS = ["CM", "COG", "DTX", "IMM", "MITO", "SKN", "STR", "HRM", "GA"]

FOCUS_AREA_NAMES = {
    "CM": "Cardiometabolic & Metabolic Health",
    "COG": "Cognitive & Mental Health",
    "DTX": "Detoxification & Biotransformation",
    "IMM": "Immune Function & Inflammation",
    "MITO": "Mitochondrial & Energy Metabolism",
    "SKN": "Skin & Barrier Function",
    "STR": "Stress-Axis & Nervous System Resilience",
    "HRM": "Hormonal Health (Transport)",
    "GA": "Gut Health and Assimilation"
}

# Shift work occupation keywords
SHIFT_WORK_KEYWORDS = [
    # Healthcare
    'nurse', 'physician', 'ed', 'emt', 'resident', 'doctor', 'paramedic',
    # Emergency services
    'security', 'police', 'firefighter', 'fire fighter',
    # Hospitality
    'hospitality', 'hotel', 'restaurant', 'chef', 'bartender', 'server',
    # Industrial
    'factory', 'plant', 'warehouse', 'logistics', 'driver', 'trucker',
    # Aviation
    'airline', 'flight attendant', 'pilot', 'crew',
    # Support
    'customer support', 'call center', 'bpo',
    # Other
    'media', 'maintenance', 'utilities', 'mining', 'oil', 'gas',
    # Shift keywords
    'night', 'rotating', 'graveyard', 'shift'
]


def add_top_contributors(
    reasons_dict: Dict[str, List[str]],
    scores_dict: Dict[str, float],
    ruleset_name: str,
    input_value: Any,
    top_n: int = 1
) -> None:
    """
    Add top N scoring focus areas from a ruleset to the reasons dictionary.

    Args:
        reasons_dict: The cumulative reasons dictionary to update (modified in-place)
        scores_dict: The scores returned by this ruleset
        ruleset_name: Name of the ruleset (e.g., "Age", "Ancestry")
        input_value: The input value used (e.g., 70, "Caucasian", ["Caucasian", "South Asian"])
        top_n: Number of top contributors to track (default: 2)
    """
    # Filter out zero scores (keep both positive and negative)
    non_zero_scores = {k: v for k, v in scores_dict.items() if v != 0}

    if not non_zero_scores:
        return  # No contribution, skip

    # Sort by absolute value descending (to get highest impact regardless of sign)
    sorted_scores = sorted(non_zero_scores.items(), key=lambda x: abs(x[1]), reverse=True)

    # Get top N (or fewer if there aren't N non-zero scores)
    top_scores = sorted_scores[:top_n]

    # Handle ties: if the Nth and (N+1)th scores are equal, include tied ones too
    if len(sorted_scores) > top_n:
        nth_score = top_scores[-1][1]
        for focus_area, score in sorted_scores[top_n:]:
            if score == nth_score:
                top_scores.append((focus_area, score))
            else:
                break

    # Format input value for display
    if isinstance(input_value, list):
        # Handle multi-select fields (e.g., ancestry)
        value_str = ", ".join(str(v) for v in input_value if v)
    else:
        value_str = str(input_value)

    # Add to reasons dictionary as "RulesetName:value"
    for focus_area, _ in top_scores:
        reason_entry = f"{ruleset_name}:{value_str}"
        reasons_dict[focus_area].append(reason_entry)


def detect_shift_work(job_title: Optional[str]) -> bool:
    """
    Detect if job involves shift work based on job title.

    Args:
        job_title: Free-text job title

    Returns:
        True if shift work detected, False otherwise
    """
    if not job_title:
        return False

    job_lower = job_title.lower()

    for keyword in SHIFT_WORK_KEYWORDS:
        if keyword in job_lower:
            return True

    return False

