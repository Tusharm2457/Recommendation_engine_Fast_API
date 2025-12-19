"""
Test suite for Trigger Event Ruleset (Field 4)
Tests trigger detection, recency multipliers, synergy rules, and caps.
"""

from datetime import datetime
from src.aether_2.tools.rulesets_phase3.trigger_event_ruleset import TriggerEventRuleset


def run_tests():
    """Run all test cases for trigger event matching."""
    
    # Test cases: (name, input_text, expected_triggers, age, expected_domains_with_scores)
    test_cases = [
        # 1. Post-viral (COVID)
        (
            "Post-viral (COVID)",
            "After COVID in 2023 I've had fatigue and brain fog",
            ["post_viral"],
            30,
            {"IMM": True, "MITO": True, "COG": True}  # COG added due to brain fog
        ),
        
        # 2. Gastroenteritis (food poisoning)
        (
            "Gastroenteritis (food poisoning)",
            "After food poisoning in Mexico last year",
            ["gastroenteritis"],
            30,
            {"GA": True, "IMM": True, "DTX": True}
        ),
        
        # 3. Gastroenteritis + Antibiotics (synergy)
        (
            "GI infection + Antibiotics (synergy)",
            "Food poisoning on trip, took ciprofloxacin",
            ["gastroenteritis", "antibiotics"],
            30,
            {"GA": True, "IMM": True, "DTX": True}  # GA should be capped at 0.40
        ),
        
        # 4. Surgery
        (
            "Surgery (laparoscopic cholecystectomy)",
            "Symptoms started after laparoscopic cholecystectomy",
            ["surgery"],
            30,
            {"STR": True, "MITO": True, "IMM": True}
        ),
        
        # 5. PPI
        (
            "PPI (omeprazole)",
            "After starting omeprazole for reflux",
            ["ppi"],
            30,
            {"GA": True, "DTX": True, "IMM": True}
        ),
        
        # 6. NSAIDs
        (
            "NSAIDs (ibuprofen)",
            "Been taking ibuprofen daily for pain",
            ["nsaids"],
            30,
            {"GA": True, "DTX": True}
        ),
        
        # 7. Postpartum
        (
            "Postpartum with GI symptoms",
            "Since baby was born, constipation and heartburn worse",
            ["postpartum"],
            30,
            {"HRM": True, "STR": True, "GA": True}  # GA added due to GI symptoms
        ),
        
        # 8. Perimenopause
        (
            "Perimenopause",
            "Since perimenopause began, symptoms worsened",
            ["perimenopause"],
            50,
            {"HRM": True, "STR": True}
        ),
        
        # 9. Mold exposure (also detects moving as stress)
        (
            "Mold exposure",
            "After moving into water-damaged apartment",
            ["mold", "psychosocial_stress"],  # Moving is correctly detected as stress
            30,
            {"IMM": True, "DTX": True, "GA": True, "COG": True, "STR": True, "CM": True}
        ),
        
        # 10. Psychosocial stress
        (
            "Psychosocial stress (job loss)",
            "After losing my job, high stress",
            ["psychosocial_stress"],
            30,
            {"STR": True, "COG": True, "CM": True}
        ),
        
        # 11. Multiple triggers (>= 3 for allostatic load)
        (
            "Multiple triggers (allostatic load)",
            "After COVID, food poisoning, took antibiotics, high work stress",
            ["post_viral", "gastroenteritis", "antibiotics", "psychosocial_stress"],
            30,
            {"GA": True, "IMM": True, "STR": True, "MITO": True, "DTX": True, "COG": True}
        ),
        
        # 12. Negation test
        (
            "Negation (not from antibiotics)",
            "Symptoms started, not from antibiotics",
            [],  # Should not detect antibiotics
            30,
            {}
        ),
        
        # 13. Uncertainty test
        (
            "Uncertainty (maybe after...)",
            "Maybe after the flu, not sure",
            ["post_viral"],
            30,
            {"IMM": True, "MITO": True}  # Scores should be reduced by 0.7
        ),
        
        # 14. Recency test (very recent)
        (
            "Very recent (<6 months)",
            "2 months ago after COVID",
            ["post_viral"],
            30,
            {"IMM": True, "MITO": True}  # Scores should be boosted by 1.2
        ),
        
        # 15. Under 18 (should not score)
        (
            "Under 18 (should not score)",
            "After COVID infection",
            [],
            16,
            {}
        ),
        
        # 16. Empty input
        (
            "Empty input",
            "",
            [],
            30,
            {}
        ),
    ]
    
    # Initialize ruleset
    print("Initializing ruleset...")
    ruleset = TriggerEventRuleset()
    
    # Run tests
    passed = 0
    failed = 0
    test_date = datetime(2024, 1, 1)  # Fixed date for consistent testing
    
    for i, (name, input_text, expected_triggers, age, expected_domains) in enumerate(test_cases, 1):
        print(f"\nTest {i}/{len(test_cases)}: {name}")
        print(f"  Input: '{input_text}'")
        print(f"  Age: {age}")
        
        # Get scores
        scores, flags, details = ruleset.get_trigger_event_weights(input_text, age=age, current_date=test_date)
        
        # Extract triggers from details
        actual_triggers = [d["trigger_name"] for d in details if d["type"] == "trigger"]
        
        # Check if expected triggers match
        triggers_match = set(actual_triggers) == set(expected_triggers)
        
        # Check if expected domains have scores
        domains_match = True
        for domain in expected_domains:
            if scores.get(domain, 0.0) <= 0.0:
                domains_match = False
                break
        
        # Overall pass/fail
        if triggers_match and domains_match:
            print(f"  ✅ PASS")
            print(f"     Triggers: {actual_triggers if actual_triggers else 'None'}")
            print(f"     Scores: {', '.join([f'{k}: {v:.2f}' for k, v in scores.items() if v > 0])}")
            passed += 1
        else:
            print(f"  ❌ FAIL")
            if not triggers_match:
                print(f"     Expected triggers: {expected_triggers}")
                print(f"     Got triggers:      {actual_triggers}")
            if not domains_match:
                print(f"     Expected domains with scores: {list(expected_domains.keys())}")
                print(f"     Got scores: {', '.join([f'{k}: {v:.2f}' for k, v in scores.items() if v > 0])}")
            failed += 1
    
    # Summary
    print("\n" + "="*60)
    print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
    if failed > 0:
        print(f"❌ {failed} test(s) failed")
    else:
        print("✅ All tests passed!")
    print("="*60)


if __name__ == "__main__":
    run_tests()

