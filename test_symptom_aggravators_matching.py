"""
Test suite for Symptom Aggravators Ruleset (Field 5)
Tests trigger detection, intensity modifiers, negation, synergy, and caps.
"""

from src.aether_2.tools.rulesets_phase3.symptom_aggravators_ruleset import SymptomAggravatorsRuleset


def test_dairy_trigger():
    """Test dairy trigger detection."""
    ruleset = SymptomAggravatorsRuleset()
    text = "Dairy products make me bloated"
    scores, flags, details = ruleset.get_symptom_aggravators_weights(text, age=30)
    
    assert scores["GA"] > 0, "Should detect dairy → GA"
    assert scores["IMM"] > 0, "Should detect dairy → IMM"
    assert scores["SKN"] > 0, "Should detect dairy → SKN"
    assert len(details) == 1, "Should detect 1 trigger"
    assert details[0]["trigger_name"] == "dairy"
    print("✅ Test 1 passed: Dairy trigger")


def test_multiple_gi_triggers_synergy():
    """Test synergy bonus for ≥3 GI triggers."""
    ruleset = SymptomAggravatorsRuleset()
    text = "Dairy and onions set me off; worse if I eat late; stress makes it worse."
    scores, flags, details = ruleset.get_symptom_aggravators_weights(text, age=30)
    
    # Should detect: dairy, onions (FODMAP), late-night meals, stress
    # First 3 are GI triggers → synergy bonus
    trigger_names = [d["trigger_name"] for d in details if d["type"] == "trigger"]
    assert "dairy" in trigger_names
    assert "fodmap_onions_garlic" in trigger_names
    assert "late_night_meals" in trigger_names
    assert "stress" in trigger_names
    
    # Check for synergy
    synergy = [d for d in details if d["type"] == "synergy"]
    assert len(synergy) == 1, "Should have synergy bonus"
    assert synergy[0]["synergy_name"] == "multiple_gi_triggers"
    
    print("✅ Test 2 passed: Multiple GI triggers synergy")


def test_coffee_spicy_alcohol():
    """Test coffee, spicy food, alcohol detection."""
    ruleset = SymptomAggravatorsRuleset()
    text = "Coffee, spicy food, alcohol—especially after a big dinner."
    scores, flags, details = ruleset.get_symptom_aggravators_weights(text, age=30)
    
    trigger_names = [d["trigger_name"] for d in details if d["type"] == "trigger"]
    assert "coffee_caffeine" in trigger_names
    assert "spicy" in trigger_names
    assert "alcohol" in trigger_names
    assert "large_meals" in trigger_names
    
    assert scores["GA"] > 0, "Should have GA score"
    assert scores["DTX"] > 0, "Should have DTX score (alcohol)"
    assert scores["STR"] > 0, "Should have STR score (coffee)"
    
    print("✅ Test 3 passed: Coffee, spicy, alcohol")


def test_stress_lack_of_sleep():
    """Test stress and sleep triggers."""
    ruleset = SymptomAggravatorsRuleset()
    text = "Worse with stress and lack of sleep"
    scores, flags, details = ruleset.get_symptom_aggravators_weights(text, age=30)
    
    trigger_names = [d["trigger_name"] for d in details if d["type"] == "trigger"]
    assert "stress" in trigger_names
    assert "lack_of_sleep" in trigger_names
    
    assert scores["STR"] > 0, "Should have STR score"
    assert scores["GA"] > 0, "Should have GA score (stress → GA)"
    assert scores["COG"] > 0, "Should have COG score (sleep → COG)"
    
    print("✅ Test 4 passed: Stress and sleep")


def test_intensity_modifier_high():
    """Test high intensity modifier ('always')."""
    ruleset = SymptomAggravatorsRuleset()
    text = "Dairy always makes me sick"
    scores, flags, details = ruleset.get_symptom_aggravators_weights(text, age=30)
    
    # Should detect intensity modifier
    dairy_detail = [d for d in details if d["type"] == "trigger" and d["trigger_name"] == "dairy"][0]
    assert dairy_detail["intensity_multiplier"] > 1.0, "Should detect 'always' as high intensity"
    
    print("✅ Test 5 passed: High intensity modifier")


def test_intensity_modifier_low():
    """Test low intensity modifier ('sometimes')."""
    ruleset = SymptomAggravatorsRuleset()
    text = "Dairy sometimes bothers me"
    scores, flags, details = ruleset.get_symptom_aggravators_weights(text, age=30)
    
    # Should detect intensity modifier
    dairy_detail = [d for d in details if d["type"] == "trigger" and d["trigger_name"] == "dairy"][0]
    assert dairy_detail["intensity_multiplier"] < 1.0, "Should detect 'sometimes' as low intensity"
    
    print("✅ Test 6 passed: Low intensity modifier")


def test_negation():
    """Test negation detection."""
    ruleset = SymptomAggravatorsRuleset()
    text = "Coffee doesn't bother me, but dairy does"
    scores, flags, details = ruleset.get_symptom_aggravators_weights(text, age=30)
    
    trigger_names = [d["trigger_name"] for d in details if d["type"] == "trigger"]
    assert "coffee_caffeine" not in trigger_names, "Should NOT detect coffee (negated)"
    assert "dairy" in trigger_names, "Should detect dairy"
    
    print("✅ Test 7 passed: Negation")


def test_ga_cap():
    """Test GA cap at 0.45."""
    ruleset = SymptomAggravatorsRuleset()
    # Many GI triggers to exceed cap
    text = "Dairy, gluten, onions, beans, spicy food, coffee, alcohol, large meals, late-night eating"
    scores, flags, details = ruleset.get_symptom_aggravators_weights(text, age=30)
    
    assert scores["GA"] <= 0.45, f"GA should be capped at 0.45, got {scores['GA']}"
    
    print("✅ Test 8 passed: GA cap")


def test_safety_flag():
    """Test safety flag detection."""
    ruleset = SymptomAggravatorsRuleset()
    text = "Bloody stool after eating dairy"
    scores, flags, details = ruleset.get_symptom_aggravators_weights(text, age=30)
    
    assert flags.get("red_flag") == True, "Should detect red flag"
    assert len(scores) == 0, "Should not score when red flag detected"
    
    print("✅ Test 9 passed: Safety flag")


def test_age_gating():
    """Test age gating (<18 years)."""
    ruleset = SymptomAggravatorsRuleset()
    text = "Dairy makes me sick"
    scores, flags, details = ruleset.get_symptom_aggravators_weights(text, age=15)
    
    assert len(scores) == 0, "Should not score for age < 18"
    assert len(details) == 0, "Should not detect triggers for age < 18"
    
    print("✅ Test 10 passed: Age gating")


def test_empty_input():
    """Test empty input handling."""
    ruleset = SymptomAggravatorsRuleset()
    scores, flags, details = ruleset.get_symptom_aggravators_weights("", age=30)
    
    assert len(scores) == 0
    assert len(details) == 0
    
    print("✅ Test 11 passed: Empty input")


def test_morning_flares():
    """Test morning flares detection."""
    ruleset = SymptomAggravatorsRuleset()
    text = "Symptoms worse in the morning"
    scores, flags, details = ruleset.get_symptom_aggravators_weights(text, age=30)
    
    trigger_names = [d["trigger_name"] for d in details if d["type"] == "trigger"]
    assert "morning_flares" in trigger_names
    assert scores["STR"] > 0, "Should have STR score"
    assert scores["HRM"] > 0, "Should have HRM score"
    
    print("✅ Test 12 passed: Morning flares")


if __name__ == "__main__":
    test_dairy_trigger()
    test_multiple_gi_triggers_synergy()
    test_coffee_spicy_alcohol()
    test_stress_lack_of_sleep()
    test_intensity_modifier_high()
    test_intensity_modifier_low()
    test_negation()
    test_ga_cap()
    test_safety_flag()
    test_age_gating()
    test_empty_input()
    test_morning_flares()
    
    print("\n" + "="*50)
    print("✅ ALL 12 TESTS PASSED!")
    print("="*50)

