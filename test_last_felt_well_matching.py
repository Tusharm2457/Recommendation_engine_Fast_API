"""
Test suite for Last Felt Well ruleset
Tests temporal parsing, chronicity overlay, and trigger detection
"""

from datetime import datetime
from src.aether_2.tools.rulesets_phase3.last_felt_well_ruleset import LastFeltWellRuleset


def test_last_felt_well_matching():
    """Test the Last Felt Well ruleset with various inputs."""
    
    print("Initializing ruleset...")
    ruleset = LastFeltWellRuleset()
    
    # Reference date for testing: January 1, 2024
    test_date = datetime(2024, 1, 1)
    
    # Test cases: (description, input_text, expected_triggers, expected_chronicity, age)
    test_cases = [
        # Temporal parsing tests
        (
            "Absolute date with season (Summer 2022)",
            "Summer 2022",
            [],
            "sub_chronic",  # ~18 months ago
            30
        ),
        (
            "Year only (2020)",
            "2020",
            [],
            "chronic",  # ~42 months ago
            30
        ),
        (
            "Relative time (2 years ago)",
            "2 years ago",
            [],
            "sub_chronic",  # 24 months
            30
        ),
        (
            "Never felt well",
            "never felt well",
            [],
            "chronic",  # 120 months
            30
        ),
        
        # Trigger detection tests
        (
            "GI infection (food poisoning)",
            "after food poisoning in Mexico, Summer 2022",
            ["gi_infection"],
            "sub_chronic",
            30
        ),
        (
            "GI infection + antibiotics (escalation)",
            "food poisoning, took antibiotics, Summer 2022",
            ["gi_infection"],  # antibiotics merged into gi_infection
            "sub_chronic",
            30
        ),
        (
            "Post-viral (COVID)",
            "since COVID in 2021",
            ["post_viral"],
            "sub_chronic",  # 2021 mid-year -> ~31 months from Jan 2024
            30
        ),
        (
            "Post-viral + GI symptoms",
            "since COVID, have bloating and fatigue",
            ["post_viral"],  # Should add GA +0.05
            "sub_chronic",  # No year, uses conservative 24 months
            30
        ),
        (
            "Mold exposure",
            "after moving into water-damaged apartment, 2022",
            ["mold", "life_stressor"],  # "moving" triggers life_stressor
            "sub_chronic",
            30
        ),
        (
            "Life stressor (job change)",
            "before job change, around 2021",
            ["life_stressor"],
            "sub_chronic",  # 2021 mid-year -> ~31 months
            30
        ),
        (
            "Hormonal (postpartum)",
            "after baby was born, 2023",
            ["hormonal"],
            None,  # 2023 mid-year -> ~6 months (recent, no chronicity overlay)
            30
        ),
        
        # Multiple triggers
        (
            "Multiple triggers (mold + stress)",
            "moved to new city with mold, lost job, 2020",
            ["mold", "life_stressor"],
            "chronic",
            30
        ),
        
        # Age check
        (
            "Under 18 (should not score)",
            "Summer 2022",
            [],
            None,  # No chronicity because age < 18
            16
        ),
        
        # Empty input
        (
            "Empty input",
            "",
            [],
            None,
            30
        ),
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, (description, input_text, expected_triggers, expected_chronicity, age) in enumerate(test_cases, 1):
        print(f"\nTest {i}/{total}: {description}")
        print(f"  Input: '{input_text}'")
        print(f"  Age: {age}")
        
        # Get scores
        scores, flags, details = ruleset.get_last_felt_well_weights(input_text, age=age, current_date=test_date)
        
        # Extract triggers and chronicity from details
        actual_triggers = [d["trigger_name"] for d in details if d["type"] == "trigger"]
        actual_chronicity = None
        for d in details:
            if d["type"] == "chronicity":
                actual_chronicity = d["label"]
        
        # Check if expected matches actual
        triggers_match = set(expected_triggers) == set(actual_triggers)
        chronicity_match = expected_chronicity == actual_chronicity
        
        if triggers_match and chronicity_match:
            print(f"  ✅ PASS")
            print(f"     Triggers: {sorted(actual_triggers) if actual_triggers else 'None'}")
            print(f"     Chronicity: {actual_chronicity if actual_chronicity else 'None'}")
            if scores:
                non_zero_scores = {k: v for k, v in scores.items() if v > 0}
                print(f"     Scores: {non_zero_scores}")
            passed += 1
        else:
            print(f"  ❌ FAIL")
            if not triggers_match:
                print(f"     Expected triggers: {sorted(expected_triggers)}")
                print(f"     Got triggers:      {sorted(actual_triggers)}")
            if not chronicity_match:
                print(f"     Expected chronicity: {expected_chronicity}")
                print(f"     Got chronicity:      {actual_chronicity}")
            print(f"     Scores: {scores}")
    
    print(f"\n{'='*60}")
    print(f"SUMMARY: {passed}/{total} tests passed")
    if passed == total:
        print("✅ All tests passed!")
    else:
        print(f"❌ {total - passed} test(s) failed")
    print(f"{'='*60}")


if __name__ == "__main__":
    test_last_felt_well_matching()

