"""
Test suite for Consistent Wake Time Ruleset
"""

from src.aether_2.tools.rulesets_phase3.consistent_wake_time_ruleset import ConsistentWakeTimeRuleset


def test_consistent_yes():
    """Test consistent wake time (Yes)"""
    ruleset = ConsistentWakeTimeRuleset()
    scores = ruleset.get_consistent_wake_time_weights(
        "Yes",
        age=30
    )
    
    assert scores["STR"] == -0.15, f"Expected STR -0.15, got {scores['STR']}"
    assert scores["COG"] == -0.05, f"Expected COG -0.05, got {scores['COG']}"
    assert scores["GA"] == -0.05, f"Expected GA -0.05, got {scores['GA']}"
    assert scores["CM"] == 0.0, f"Expected CM 0.0, got {scores['CM']}"
    print("✅ test_consistent_yes passed")


def test_irregular_no():
    """Test irregular wake time (No)"""
    ruleset = ConsistentWakeTimeRuleset()
    scores = ruleset.get_consistent_wake_time_weights(
        "No",
        age=30
    )
    
    assert scores["STR"] == 0.30, f"Expected STR 0.30, got {scores['STR']}"
    assert scores["COG"] == 0.15, f"Expected COG 0.15, got {scores['COG']}"
    assert scores["GA"] == 0.20, f"Expected GA 0.20, got {scores['GA']}"
    assert scores["CM"] == 0.0, f"Expected CM 0.0, got {scores['CM']}"
    print("✅ test_irregular_no passed")


def test_irregular_with_shift_work():
    """Test irregular wake time with shift work (should cap STR at 0.40)"""
    ruleset = ConsistentWakeTimeRuleset()
    scores = ruleset.get_consistent_wake_time_weights(
        "No",
        age=30,
        shift_work_flag=True
    )
    
    # Base: STR 0.30, GA 0.20, CM 0.0
    # + Shift work: STR +0.10 (capped at 0.40), GA +0.05, CM +0.10
    assert scores["STR"] == 0.40, f"Expected STR 0.40 (capped), got {scores['STR']}"
    assert scores["GA"] == 0.25, f"Expected GA 0.25, got {scores['GA']}"
    assert scores["CM"] == 0.10, f"Expected CM 0.10, got {scores['CM']}"
    print("✅ test_irregular_with_shift_work passed")


def test_irregular_with_alcohol():
    """Test irregular wake time with daily alcohol"""
    ruleset = ConsistentWakeTimeRuleset()
    scores = ruleset.get_consistent_wake_time_weights(
        "No",
        age=30,
        alcohol_frequency="daily"
    )
    
    # Base: GA 0.20
    # + Alcohol: GA +0.10 = 0.30 (capped)
    assert scores["GA"] == 0.30, f"Expected GA 0.30 (capped), got {scores['GA']}"
    print("✅ test_irregular_with_alcohol passed")


def test_irregular_with_social_jetlag():
    """Test irregular wake time with social jetlag"""
    ruleset = ConsistentWakeTimeRuleset()
    scores = ruleset.get_consistent_wake_time_weights(
        "No",
        age=30,
        social_jetlag_flag=True
    )
    
    # Base: STR 0.30
    # + Social jetlag: STR +0.05 = 0.35
    assert scores["STR"] == 0.35, f"Expected STR 0.35, got {scores['STR']}"
    print("✅ test_irregular_with_social_jetlag passed")


def test_irregular_with_short_sleep():
    """Test irregular wake time with short sleep (<6h)"""
    ruleset = ConsistentWakeTimeRuleset()
    scores = ruleset.get_consistent_wake_time_weights(
        "No",
        age=30,
        short_sleep_flag=True
    )
    
    # Base: STR 0.30, CM 0.0
    # + Short sleep: STR +0.05 = 0.35, CM +0.05
    assert scores["STR"] == 0.35, f"Expected STR 0.35, got {scores['STR']}"
    assert scores["CM"] == 0.05, f"Expected CM 0.05, got {scores['CM']}"
    print("✅ test_irregular_with_short_sleep passed")


def test_irregular_all_escalators():
    """Test irregular wake time with all escalators (capping test)"""
    ruleset = ConsistentWakeTimeRuleset()
    scores = ruleset.get_consistent_wake_time_weights(
        "No",
        age=30,
        shift_work_flag=True,
        alcohol_frequency="weekly",
        social_jetlag_flag=True,
        short_sleep_flag=True
    )
    
    # Base: STR 0.30, COG 0.15, GA 0.20, CM 0.0
    # + Shift work: STR +0.10, GA +0.05, CM +0.10
    # + Alcohol: GA +0.10
    # + Social jetlag: STR +0.05
    # + Short sleep: STR +0.05, CM +0.05
    # Total: STR 0.50 → capped at 0.40, GA 0.35 → capped at 0.30, CM 0.15
    assert abs(scores["STR"] - 0.40) < 0.001, f"Expected STR 0.40 (capped), got {scores['STR']}"
    assert abs(scores["COG"] - 0.15) < 0.001, f"Expected COG 0.15, got {scores['COG']}"
    assert abs(scores["GA"] - 0.30) < 0.001, f"Expected GA 0.30 (capped), got {scores['GA']}"
    assert abs(scores["CM"] - 0.15) < 0.001, f"Expected CM 0.15, got {scores['CM']}"
    print("✅ test_irregular_all_escalators passed")


def test_age_gating():
    """Test age gating (< 18 years)"""
    ruleset = ConsistentWakeTimeRuleset()
    scores = ruleset.get_consistent_wake_time_weights(
        "No",
        age=16
    )
    
    assert all(v == 0.0 for v in scores.values()), "Expected all zeros for age < 18"
    print("✅ test_age_gating passed")


if __name__ == "__main__":
    test_consistent_yes()
    test_irregular_no()
    test_irregular_with_shift_work()
    test_irregular_with_alcohol()
    test_irregular_with_social_jetlag()
    test_irregular_with_short_sleep()
    test_irregular_all_escalators()
    test_age_gating()
    print("\n✅ All tests passed!")

