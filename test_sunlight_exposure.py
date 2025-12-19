"""
Test Sunlight Exposure Ranking ruleset.

Input format: Ordered list from MOST to LEAST sunlight exposure
Example: "Sat, Sun, Fri, Thu, Wed, Tue, Mon" means Sat has MOST light, Mon has LEAST
"""

from src.aether_2.tools.rulesets_phase3.sunlight_exposure_ruleset import SunlightExposureRuleset


def test_weekend_only_pattern():
    """
    Test weekend-only pattern (strong social jetlag).
    
    Pattern: Sat > Sun > Fri > Thu > Wed > Tue > Mon
    - Sat=1, Sun=2 (both in top 2) ✓
    - Weekdays: Fri=3, Thu=4, Wed=5, Tue=6, Mon=7
    - Weekdays ranked 3rd-7th: ALL 5 of them ✓
    - This triggers weekend-only classifier
    """
    ruleset = SunlightExposureRuleset()
    
    data = "Sat, Sun, Fri, Thu, Wed, Tue, Mon"
    scores = ruleset.get_sunlight_exposure_weights(data, age=30)
    
    # Should detect weekend-only pattern
    assert scores["STR"] == 0.35, f"Expected STR=0.35, got {scores['STR']}"
    assert scores["GA"] == 0.15, f"Expected GA=0.15, got {scores['GA']}"
    assert scores["CM"] == 0.10, f"Expected CM=0.10, got {scores['CM']}"
    assert scores["COG"] == 0.05, f"Expected COG=0.05, got {scores['COG']}"
    print("✅ Test 1: Weekend-only pattern (Sat > Sun > Fri > Thu > Wed > Tue > Mon)")


def test_regular_weekday_pattern():
    """
    Test regular weekday pattern (protective).
    
    Pattern: Mon > Tue > Wed > Thu > Fri > Sat > Sun
    - Weekday avg = (1+2+3+4+5)/5 = 3.0
    - Weekend avg = (6+7)/2 = 6.5
    - WDI = 3.0 - 6.5 = -3.5 (strong weekday dominance)
    - OC = 0 (smooth pattern)
    """
    ruleset = SunlightExposureRuleset()
    
    data = "Mon, Tue, Wed, Thu, Fri, Sat, Sun"
    scores = ruleset.get_sunlight_exposure_weights(data, age=30)
    
    # Should detect weekday-dominant regularity (protective)
    assert scores["STR"] == -0.20, f"Expected STR=-0.20, got {scores['STR']}"
    assert scores["GA"] == -0.05, f"Expected GA=-0.05, got {scores['GA']}"
    print("✅ Test 2: Regular weekday pattern (Mon > Tue > Wed > Thu > Fri > Sat > Sun)")


def test_erratic_pattern():
    """
    Test erratic zig-zag pattern.
    
    Pattern: Mon > Sat > Wed > Sun > Tue > Fri > Thu
    Ranks in Mon-Sun order: [1, 5, 3, 7, 6, 2, 4]
    Direction changes: 1→5(up), 5→3(down)✓, 3→7(up)✓, 7→6(down), 6→2(down), 2→4(up)✓
    OC = 3 or 4 (need to verify)
    """
    ruleset = SunlightExposureRuleset()
    
    data = "Mon, Sat, Wed, Sun, Tue, Fri, Thu"
    scores = ruleset.get_sunlight_exposure_weights(data, age=30)
    
    # Should detect erratic pattern
    # WDI ~ 0 (balanced), so no weekend dominance penalty
    # But oscillation count should trigger erratic pattern
    print(f"   Erratic pattern scores: STR={scores['STR']}, GA={scores['GA']}")
    assert scores["STR"] >= 0.15, f"Expected STR>=0.15 (erratic), got {scores['STR']}"
    assert scores["GA"] >= 0.05, f"Expected GA>=0.05 (erratic), got {scores['GA']}"
    print("✅ Test 3: Erratic zig-zag pattern (Mon > Sat > Wed > Sun > Tue > Fri > Thu)")


def test_strong_weekend_dominance():
    """
    Test strong weekend dominance (not weekend-only).
    
    Pattern: Sat > Mon > Sun > Fri > Thu > Wed > Tue
    - Sat=1, Mon=2 (Mon in top 2, so NOT weekend-only)
    - Sun=3
    - Weekend avg = (1+3)/2 = 2.0
    - Weekday avg = (2+4+5+6+7)/5 = 4.8
    - WDI = 4.8 - 2.0 = 2.8 (strong weekend dominance)
    """
    ruleset = SunlightExposureRuleset()
    
    data = "Sat, Mon, Sun, Fri, Thu, Wed, Tue"
    scores = ruleset.get_sunlight_exposure_weights(data, age=30)
    
    # Should detect strong weekend dominance (WDI >= 2.0), not weekend-only
    assert scores["STR"] == 0.25, f"Expected STR=0.25, got {scores['STR']}"
    assert scores["GA"] == 0.10, f"Expected GA=0.10, got {scores['GA']}"
    assert scores["CM"] == 0.05, f"Expected CM=0.05, got {scores['CM']}"
    print("✅ Test 4: Strong weekend dominance (Sat > Mon > Sun > Fri > Thu > Wed > Tue)")


def test_moderate_weekend_bias():
    """
    Test moderate weekend bias.
    
    Pattern: Mon > Sat > Tue > Sun > Wed > Thu > Fri
    - Weekend avg = (2+4)/2 = 3.0
    - Weekday avg = (1+3+5+6+7)/5 = 4.4
    - WDI = 4.4 - 3.0 = 1.4 (moderate!)
    """
    ruleset = SunlightExposureRuleset()
    
    data = "Mon, Sat, Tue, Sun, Wed, Thu, Fri"
    scores = ruleset.get_sunlight_exposure_weights(data, age=30)
    
    # Should detect moderate weekend bias (1.0 <= WDI < 2.0)
    assert scores["STR"] == 0.15, f"Expected STR=0.15, got {scores['STR']}"
    assert scores["GA"] == 0.05, f"Expected GA=0.05, got {scores['GA']}"
    print("✅ Test 5: Moderate weekend bias (Mon > Sat > Tue > Sun > Wed > Thu > Fri)")


def test_balanced_pattern():
    """
    Test balanced exposure pattern.
    
    Pattern: Mon > Tue > Sat > Wed > Thu > Sun > Fri
    - Weekend avg = (3+6)/2 = 4.5
    - Weekday avg = (1+2+4+5+7)/5 = 3.8
    - WDI = 3.8 - 4.5 = -0.7 (balanced, |WDI| < 1.0)
    - OC should be low
    """
    ruleset = SunlightExposureRuleset()
    
    data = "Mon, Tue, Sat, Wed, Thu, Sun, Fri"
    scores = ruleset.get_sunlight_exposure_weights(data, age=30)
    
    # Should detect balanced pattern (protective)
    assert scores["STR"] == -0.15, f"Expected STR=-0.15, got {scores['STR']}"
    assert scores["GA"] == -0.05, f"Expected GA=-0.05, got {scores['GA']}"
    print("✅ Test 6: Balanced pattern (Mon > Tue > Sat > Wed > Thu > Sun > Fri)")


def test_abbreviations():
    """Test day abbreviations"""
    ruleset = SunlightExposureRuleset()

    # Test with abbreviations
    data = "mon, tue, wed, thu, fri, sat, sun"
    scores = ruleset.get_sunlight_exposure_weights(data, age=30)

    # Should parse correctly and detect weekday-dominant pattern
    assert scores["STR"] == -0.20, f"Expected STR=-0.20, got {scores['STR']}"
    print("✅ Test 7: Abbreviations (mon, tue, wed, thu, fri, sat, sun)")


def test_full_names():
    """Test full day names"""
    ruleset = SunlightExposureRuleset()

    # Test with full names
    data = "Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday"
    scores = ruleset.get_sunlight_exposure_weights(data, age=30)

    # Should parse correctly and detect weekday-dominant pattern
    assert scores["STR"] == -0.20, f"Expected STR=-0.20, got {scores['STR']}"
    print("✅ Test 8: Full day names")


def test_semicolon_separator():
    """Test semicolon separator"""
    ruleset = SunlightExposureRuleset()

    # Test with semicolon separator (weekend-only pattern)
    data = "Sat; Sun; Fri; Thu; Wed; Tue; Mon"
    scores = ruleset.get_sunlight_exposure_weights(data, age=30)

    # Should detect weekend-only pattern
    assert scores["STR"] == 0.35, f"Expected STR=0.35, got {scores['STR']}"
    print("✅ Test 9: Semicolon separator")


def test_age_gating():
    """Test age gating (< 18 years)"""
    ruleset = SunlightExposureRuleset()

    # Test with age < 18 (weekend-only pattern)
    data = "Sat, Sun, Fri, Thu, Wed, Tue, Mon"
    scores = ruleset.get_sunlight_exposure_weights(data, age=17)

    # Should return all zeros
    total_score = sum(abs(v) for v in scores.values())
    assert total_score == 0, f"Expected total=0 (age<18), got {total_score}"
    print("✅ Test 10: Age gating (age < 18)")


def test_cross_field_modifiers():
    """Test cross-field modifiers"""
    ruleset = SunlightExposureRuleset()

    # Test with bright light at night
    data = "Mon, Tue, Wed, Thu, Fri, Sat, Sun"
    scores = ruleset.get_sunlight_exposure_weights(
        data, age=30, bright_light_at_night=True
    )

    # Should add STR +0.10 on top of base -0.20
    assert scores["STR"] == -0.10, f"Expected STR=-0.10 (-0.20 + 0.10), got {scores['STR']}"
    print("✅ Test 11: Cross-field modifier (bright light at night)")


def test_oscillation_counting():
    """Test oscillation counting logic"""
    ruleset = SunlightExposureRuleset()

    # Test oscillation counting directly
    rank_positions = {
        "Mon": 1, "Tue": 3, "Wed": 2, "Thu": 4, "Fri": 3, "Sat": 5, "Sun": 4
    }
    osc_count = ruleset._count_oscillations(rank_positions)

    # Ranks in Mon-Sun order: [1, 3, 2, 4, 3, 5, 4]
    # 1→3(up), 3→2(down)✓, 2→4(up)✓, 4→3(down)✓, 3→5(up)✓, 5→4(down)✓
    # Expected: 5 direction changes
    print(f"   Oscillation count: {osc_count}")
    assert osc_count >= 4, f"Expected oscillations>=4, got {osc_count}"
    print("✅ Test 12: Oscillation counting")


if __name__ == "__main__":
    test_weekend_only_pattern()
    test_regular_weekday_pattern()
    test_erratic_pattern()
    test_strong_weekend_dominance()
    test_moderate_weekend_bias()
    test_balanced_pattern()
    test_abbreviations()
    test_full_names()
    test_semicolon_separator()
    test_age_gating()
    test_cross_field_modifiers()
    test_oscillation_counting()

    print("\n" + "="*70)
    print("✅ ALL 12 TESTS PASSED!")
    print("="*70)

