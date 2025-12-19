"""
Test script for Patient Reasoning Ruleset - NLP Matching Improvements
"""

from src.aether_2.tools.rulesets_phase3.patient_reasoning_ruleset import PatientReasoningRuleset


def test_patient_reasoning_matching():
    """Test the hybrid matching pipeline for patient reasoning."""
    
    print("="*80)
    print("PATIENT REASONING RULESET - MATCHING TEST")
    print("="*80)
    
    print("\nInitializing ruleset...")
    ruleset = PatientReasoningRuleset()
    
    # Test cases: (input_text, expected_groups, description)
    test_cases = [
        # Test 1: Word forms (antibiotics → antibiotic)
        (
            "I took antibiotics last year and my gut has been off since",
            ["antibiotics"],
            "Word forms (antibiotics → antibiotic)"
        ),
        
        # Test 2: Plural forms (stresses → stress)
        (
            "Work stresses and deadlines are killing me",
            ["work_stress"],
            "Plural forms (stresses → stress)"
        ),
        
        # Test 3: Typo (mould → mold)
        (
            "I think the mould in my apartment is making me sick",
            ["mold"],
            "Typo (mould → mold)"
        ),
        
        # Test 4: Exact match (baseline)
        (
            "I have SIBO and leaky gut",
            ["sibo", "leaky_gut"],
            "Exact matches (baseline)"
        ),
        
        # Test 5: Multiple conditions
        (
            "After food poisoning, I developed histamine intolerance",
            ["food_poisoning", "histamine"],
            "Multiple conditions"
        ),
        
        # Test 6: Hormonal variations
        (
            "My thyroid is off and I have PCOS",
            ["hormonal"],
            "Hormonal variations (thyroid, PCOS)"
        ),
        
        # Test 7: Toxin exposure
        (
            "I was exposed to heavy metals at work",
            ["toxins"],
            "Toxin exposure (heavy metals)"
        ),
        
        # Test 8: Sleep issues
        (
            "I work night shifts and barely sleep",
            ["sleep_deprivation"],
            "Sleep issues (night shifts)"
        ),
        
        # Test 9: Diet-related
        (
            "I eat too much junk food and processed stuff",
            ["poor_diet"],
            "Diet-related (junk food, processed)"
        ),
        
        # Test 10: GI-specific
        (
            "I had H pylori infection and took PPIs for months",
            ["h_pylori", "low_stomach_acid"],
            "GI-specific (H pylori, PPIs)"
        ),
        
        # Test 11: Negation handling (check scores instead of matches)
        # Note: Negation is applied during scoring, so matched_groups will still show 'mold'
        # but the scores should be zero
        (
            "I don't have mold exposure",
            ["mold"],  # Will match, but should be negated in scoring
            "Negation handling (matches but should have zero scores)"
        ),
        
        # Test 12: Complex multi-condition
        (
            "I think my issues started with antibiotics, then I got SIBO, and now I have leaky gut and histamine problems",
            ["antibiotics", "sibo", "leaky_gut", "histamine"],
            "Complex multi-condition"
        ),
    ]
    
    passed = 0
    failed = 0
    
    for i, (input_text, expected_groups, description) in enumerate(test_cases, 1):
        print(f"\nTest {i}/{len(test_cases)}: {description}")
        print(f"  Input: '{input_text}'")
        
        # Run the ruleset
        # Get scores (now returns 3 values: scores, flags, causal_group_details)
        scores, safety_flags, causal_group_details = ruleset.get_patient_reasoning_weights(input_text, age=30)
        
        # Get matched groups by checking which groups contributed to scores
        matched_groups_dict = ruleset._match_causal_groups(ruleset._normalize_text(input_text))
        matched_groups = list(matched_groups_dict.keys())
        
        # Check if expected groups match
        expected_set = set(expected_groups)
        matched_set = set(matched_groups)

        # Special handling for negation test (Test 11)
        if "Negation handling" in description:
            # For negation test, check that scores are zero even though groups matched
            non_zero_scores = {k: v for k, v in scores.items() if v > 0}
            if expected_set == matched_set and len(non_zero_scores) == 0:
                print(f"  ✅ PASS - Matched: {sorted(matched_groups)} (but negated, scores=0)")
                passed += 1
            else:
                print(f"  ❌ FAIL")
                print(f"     Expected: {sorted(expected_groups)} with zero scores")
                print(f"     Got:      {sorted(matched_groups)} with scores: {non_zero_scores}")
                failed += 1
        else:
            if expected_set == matched_set:
                print(f"  ✅ PASS - Matched: {sorted(matched_groups)}")
                passed += 1
            else:
                print(f"  ❌ FAIL")
                print(f"     Expected: {sorted(expected_groups)}")
                print(f"     Got:      {sorted(matched_groups)}")
                failed += 1

        # Show scores for matched groups
        non_zero_scores = {k: v for k, v in scores.items() if v > 0}
        if non_zero_scores:
            print(f"  Scores: {non_zero_scores}")
    
    print("\n" + "="*80)
    print(f"SUMMARY: {passed}/{len(test_cases)} tests passed")
    if failed == 0:
        print("✅ All tests passed!")
    else:
        print(f"❌ {failed} test(s) failed")
    print("="*80)
    
    return passed == len(test_cases)


if __name__ == "__main__":
    success = test_patient_reasoning_matching()
    exit(0 if success else 1)

