#!/usr/bin/env python3
"""
Test script to compare old (substring) vs new (lemmatization + fuzzy) matching.
"""

import sys
import json
from src.aether_2.tools.rulesets_phase3.health_goals_ruleset import HealthGoalsRuleset

# Test cases covering different scenarios
TEST_CASES = [
    # Word form variations
    {
        "input": "losing weight and reducing stress",
        "expected_domains": ["CM", "STR"],
        "scenario": "Word forms (losing → lose, reducing → reduce)"
    },
    {
        "input": "I have low energies and brain fog",
        "expected_domains": ["MITO", "COG"],
        "scenario": "Plural forms (energies → energy)"
    },
    {
        "input": "stressed out and anxious",
        "expected_domains": ["STR"],
        "scenario": "Verb forms (stressed → stress)"
    },
    
    # Typos
    {
        "input": "loose weight and improve enrgy",
        "expected_domains": ["CM", "MITO"],
        "scenario": "Common typos (loose → lose, enrgy → energy)"
    },
    {
        "input": "reduce bloating and gass",
        "expected_domains": ["GA"],
        "scenario": "Typo (gass → gas)"
    },
    
    # Exact matches (should still work)
    {
        "input": "lose weight; reduce stress; improve energy",
        "expected_domains": ["CM", "STR", "MITO"],
        "scenario": "Exact matches (baseline)"
    },
    {
        "input": "brain fog and fatigue",
        "expected_domains": ["COG", "MITO"],
        "scenario": "Exact matches"
    },
    
    # Cross-mapping
    {
        "input": "reduce chronic pain",
        "expected_domains": ["STR", "IMM", "MITO"],
        "scenario": "Pain cross-mapping"
    },
    {
        "input": "migraines affecting my focus",
        "expected_domains": ["STR", "IMM", "MITO", "COG"],
        "scenario": "Migraine + focus → adds COG"
    },
    {
        "input": "healthy aging and longevity",
        "expected_domains": ["CM", "MITO", "IMM"],
        "scenario": "Longevity cross-mapping"
    },
    
    # Sleep special handling
    {
        "input": "improve sleep quality",
        "expected_domains": ["STR", "COG"],
        "scenario": "Sleep → STR + COG"
    },
    
    # Complex real-world examples
    {
        "input": "I'm trying to lose weight, improve my energy levels, and reduce bloating",
        "expected_domains": ["CM", "MITO", "GA"],
        "scenario": "Complex multi-goal"
    },
    {
        "input": "clear my skin and reduce inflammation",
        "expected_domains": ["SKN", "IMM"],
        "scenario": "Skin + inflammation"
    },
]


def test_matching():
    """Test the new matching logic."""
    print("=" * 80)
    print("HEALTH GOALS RULESET - MATCHING TEST")
    print("=" * 80)
    print()
    
    # Initialize ruleset
    print("Initializing ruleset...")
    ruleset = HealthGoalsRuleset()
    print()
    
    # Run tests
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(TEST_CASES, 1):
        input_text = test_case["input"]
        expected = set(test_case["expected_domains"])
        scenario = test_case["scenario"]
        
        print(f"Test {i}/{len(TEST_CASES)}: {scenario}")
        print(f"  Input: '{input_text}'")
        
        # Get scores (now returns 3 values: scores, flags, goal_details)
        scores, flags, goal_details = ruleset.get_health_goals_weights(input_text, age=30)
        
        # Get matched domains (non-zero scores)
        matched = {domain for domain, score in scores.items() if score > 0}
        
        # Check if expected domains are matched
        if expected.issubset(matched):
            print(f"  ✅ PASS - Matched: {sorted(matched)}")
            passed += 1
        else:
            print(f"  ❌ FAIL - Expected: {sorted(expected)}, Got: {sorted(matched)}")
            missing = expected - matched
            extra = matched - expected
            if missing:
                print(f"     Missing: {sorted(missing)}")
            if extra:
                print(f"     Extra: {sorted(extra)}")
            failed += 1
        
        # Show scores
        non_zero_scores = {k: v for k, v in scores.items() if v > 0}
        if non_zero_scores:
            print(f"  Scores: {json.dumps(non_zero_scores, indent=4)}")
        
        print()
    
    # Summary
    print("=" * 80)
    print(f"SUMMARY: {passed}/{len(TEST_CASES)} tests passed")
    if failed > 0:
        print(f"⚠️  {failed} tests failed")
    else:
        print("✅ All tests passed!")
    print("=" * 80)
    
    return failed == 0


if __name__ == "__main__":
    success = test_matching()
    sys.exit(0 if success else 1)

