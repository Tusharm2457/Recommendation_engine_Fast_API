"""
Test suite for Air Filter ruleset (Field 37).
"""

from src.aether_2.tools.rulesets_phase3.air_filter_ruleset import AirFilterRuleset


def approx_equal(a, b, tol=0.01):
    """Check if two floats are approximately equal within tolerance."""
    return abs(a - b) < tol


def test_1_empty_input():
    """Test 1: Empty input / No choice"""
    ruleset = AirFilterRuleset()
    weights, flags = ruleset.get_air_filter_weights("", "")
    assert weights == {}, f"Expected empty dict, got {weights}"
    assert flags == [], f"Expected empty list, got {flags}"
    print("✅ Test 1 passed: Empty input")


def test_2_no_filter_no_context():
    """Test 2: No filter without environmental context"""
    ruleset = AirFilterRuleset()
    weights, flags = ruleset.get_air_filter_weights("No", "")
    assert weights == {}, f"Expected empty dict, got {weights}"
    assert flags == [], f"Expected empty list, got {flags}"
    print("✅ Test 2 passed: No filter without context")


def test_3_no_filter_with_mold():
    """Test 3: No filter with mold/dampness"""
    ruleset = AirFilterRuleset()
    weights, flags = ruleset.get_air_filter_weights(
        "No", "",
        has_mold_dampness=True
    )
    
    # No filter + mold/dampness
    assert approx_equal(weights["IMM"], 0.30), f"Expected IMM=0.30, got {weights['IMM']}"
    assert approx_equal(weights["DTX"], 0.20), f"Expected DTX=0.20, got {weights['DTX']}"
    assert approx_equal(weights["GA"], 0.20), f"Expected GA=0.20, got {weights['GA']}"
    
    print("✅ Test 3 passed: No filter with mold/dampness")


def test_4_no_filter_with_poor_ventilation():
    """Test 4: No filter with poor ventilation"""
    ruleset = AirFilterRuleset()
    weights, flags = ruleset.get_air_filter_weights(
        "No", "",
        has_poor_ventilation=True
    )
    
    # No filter + poor ventilation
    assert approx_equal(weights["DTX"], 0.10), f"Expected DTX=0.10, got {weights['DTX']}"
    
    print("✅ Test 4 passed: No filter with poor ventilation")


def test_5_no_filter_with_gas_stove():
    """Test 5: No filter with gas stove"""
    ruleset = AirFilterRuleset()
    weights, flags = ruleset.get_air_filter_weights(
        "No", "",
        has_gas_stove=True
    )
    
    # No filter + gas stove
    assert approx_equal(weights["IMM"], 0.10), f"Expected IMM=0.10, got {weights['IMM']}"
    
    print("✅ Test 5 passed: No filter with gas stove")


def test_6_no_filter_all_contexts():
    """Test 6: No filter with all environmental contexts"""
    ruleset = AirFilterRuleset()
    weights, flags = ruleset.get_air_filter_weights(
        "No", "",
        has_mold_dampness=True,
        has_poor_ventilation=True,
        has_gas_stove=True
    )
    
    # No filter + all contexts
    # IMM: 0.30 (mold) + 0.10 (gas stove) = 0.40
    # DTX: 0.20 (mold) + 0.10 (poor vent) = 0.30
    # GA: 0.20 (mold)
    assert approx_equal(weights["IMM"], 0.40), f"Expected IMM=0.40, got {weights['IMM']}"
    assert approx_equal(weights["DTX"], 0.30), f"Expected DTX=0.30, got {weights['DTX']}"
    assert approx_equal(weights["GA"], 0.20), f"Expected GA=0.20, got {weights['GA']}"
    
    print("✅ Test 6 passed: No filter with all contexts")


def test_7_yes_hepa_only():
    """Test 7: Yes with HEPA only (unverifiable brand)"""
    ruleset = AirFilterRuleset()
    weights, flags = ruleset.get_air_filter_weights(
        "Yes",
        "True HEPA filter"
    )

    # HEPA only (unverifiable brand)
    # IMM: -0.15 (HEPA) + 0.10 (undersized/unverifiable) = -0.05
    # DTX: -0.10 (HEPA)
    assert approx_equal(weights["IMM"], -0.05), f"Expected IMM=-0.05, got {weights['IMM']}"
    assert approx_equal(weights["DTX"], -0.10), f"Expected DTX=-0.10, got {weights['DTX']}"

    print("✅ Test 7 passed: Yes with HEPA only (unverifiable brand)")


def test_8_yes_hepa_carbon():
    """Test 8: Yes with HEPA + activated carbon"""
    ruleset = AirFilterRuleset()
    weights, flags = ruleset.get_air_filter_weights(
        "Yes",
        "Coway Airmega 400S True HEPA with activated carbon"
    )
    
    # HEPA + carbon + quality brand (adequate CADR)
    # IMM: -0.15 (HEPA) - 0.10 (CADR) = -0.25
    # DTX: -0.10 (HEPA) - 0.10 (carbon) - 0.10 (CADR) = -0.30
    # GA: -0.10 (HEPA + carbon)
    assert approx_equal(weights["IMM"], -0.25), f"Expected IMM=-0.25, got {weights['IMM']}"
    assert approx_equal(weights["DTX"], -0.30), f"Expected DTX=-0.30, got {weights['DTX']}"
    assert approx_equal(weights["GA"], -0.10), f"Expected GA=-0.10, got {weights['GA']}"
    
    print("✅ Test 8 passed: Yes with HEPA + carbon")


def test_9_yes_ionizer_no_cert():
    """Test 9: Yes with ionizer without certification"""
    ruleset = AirFilterRuleset()
    weights, flags = ruleset.get_air_filter_weights(
        "Yes",
        "Ionizer air purifier"
    )

    # Ionizer without UL2998/CARB + unverifiable brand
    # IMM: +0.20 (ozone risk) + 0.10 (undersized) = 0.30
    # DTX: +0.20 (ozone risk)
    assert approx_equal(weights["IMM"], 0.30), f"Expected IMM=0.30, got {weights['IMM']}"
    assert approx_equal(weights["DTX"], 0.20), f"Expected DTX=0.20, got {weights['DTX']}"

    print("✅ Test 9 passed: Yes with ionizer without certification")


def test_10_yes_ionizer_with_cert():
    """Test 10: Yes with ionizer with UL 2998 certification"""
    ruleset = AirFilterRuleset()
    weights, flags = ruleset.get_air_filter_weights(
        "Yes",
        "Ionizer air purifier UL 2998 certified"
    )

    # Ionizer with UL2998 + unverifiable brand
    # IMM: -0.05 (cert) + 0.10 (undersized) = 0.05
    # DTX: -0.05 (cert)
    assert approx_equal(weights["IMM"], 0.05), f"Expected IMM=0.05, got {weights['IMM']}"
    assert approx_equal(weights["DTX"], -0.05), f"Expected DTX=-0.05, got {weights['DTX']}"

    print("✅ Test 10 passed: Yes with ionizer with UL 2998")


def test_11_yes_diy_filter():
    """Test 11: Yes with DIY Corsi-Rosenthal box"""
    ruleset = AirFilterRuleset()
    weights, flags = ruleset.get_air_filter_weights(
        "Yes",
        "DIY Corsi-Rosenthal box fan with MERV 13 filters"
    )

    # DIY filter + HEPA detection (MERV 13 triggers HEPA)
    # IMM: -0.15 (HEPA) - 0.10 (DIY) = -0.25
    # DTX: -0.10 (HEPA) - 0.10 (DIY) = -0.20
    assert approx_equal(weights["IMM"], -0.25), f"Expected IMM=-0.25, got {weights['IMM']}"
    assert approx_equal(weights["DTX"], -0.20), f"Expected DTX=-0.20, got {weights['DTX']}"

    print("✅ Test 11 passed: Yes with DIY filter")


def test_12_yes_poor_maintenance():
    """Test 12: Yes with poor maintenance"""
    ruleset = AirFilterRuleset()
    weights, flags = ruleset.get_air_filter_weights(
        "Yes",
        "HEPA filter but haven't changed in 12 months"
    )

    # HEPA + unverifiable brand + poor maintenance
    # IMM: -0.15 (HEPA) + 0.10 (undersized) + 0.10 (poor maint) = 0.05
    # DTX: -0.10 (HEPA) + 0.10 (poor maint) = 0.00 → removed
    assert approx_equal(weights["IMM"], 0.05), f"Expected IMM=0.05, got {weights['IMM']}"
    assert "DTX" not in weights, f"Expected DTX to be removed, got {weights}"

    print("✅ Test 12 passed: Yes with poor maintenance")


def test_13_yes_mold_with_hepa():
    """Test 13: Yes with mold context + HEPA"""
    ruleset = AirFilterRuleset()
    weights, flags = ruleset.get_air_filter_weights(
        "Yes",
        "True HEPA filter",
        has_mold_dampness=True
    )

    # HEPA + unverifiable brand + mold context
    # IMM: -0.15 (HEPA) + 0.10 (undersized) - 0.10 (mold + HEPA) = -0.15
    # DTX: -0.10 (HEPA)
    # GA: -0.05 (mold + HEPA)
    assert approx_equal(weights["IMM"], -0.15), f"Expected IMM=-0.15, got {weights['IMM']}"
    assert approx_equal(weights["DTX"], -0.10), f"Expected DTX=-0.10, got {weights['DTX']}"
    assert approx_equal(weights["GA"], -0.05), f"Expected GA=-0.05, got {weights['GA']}"

    print("✅ Test 13 passed: Yes with mold + HEPA")


def test_14_yes_wildfire_no_hepa():
    """Test 14: Yes with wildfire smoke but no HEPA"""
    ruleset = AirFilterRuleset()
    weights, flags = ruleset.get_air_filter_weights(
        "Yes",
        "Basic air filter",
        has_wildfire_smoke=True
    )

    # Wildfire smoke + no HEPA + undersized
    # IMM: +0.10 (undersized) + 0.10 (wildfire) = 0.20
    # DTX: +0.20 (wildfire)
    assert approx_equal(weights["IMM"], 0.20), f"Expected IMM=0.20, got {weights['IMM']}"
    assert approx_equal(weights["DTX"], 0.20), f"Expected DTX=0.20, got {weights['DTX']}"

    print("✅ Test 14 passed: Yes with wildfire smoke but no HEPA")


def test_15_complex_case():
    """Test 15: Complex case (HEPA + carbon + quality brand + mold context)"""
    ruleset = AirFilterRuleset()
    weights, flags = ruleset.get_air_filter_weights(
        "Yes",
        "Coway Airmega 400S True HEPA with activated carbon",
        has_mold_dampness=True,
        has_gas_stove=True
    )

    # HEPA + carbon + quality brand + mold context
    # IMM: -0.15 (HEPA) - 0.10 (CADR) - 0.10 (mold + HEPA) = -0.35
    # DTX: -0.10 (HEPA) - 0.10 (carbon) - 0.10 (CADR) = -0.30
    # GA: -0.10 (HEPA + carbon) - 0.05 (mold + HEPA) = -0.15
    assert approx_equal(weights["IMM"], -0.35), f"Expected IMM=-0.35, got {weights['IMM']}"
    assert approx_equal(weights["DTX"], -0.30), f"Expected DTX=-0.30, got {weights['DTX']}"
    assert approx_equal(weights["GA"], -0.15), f"Expected GA=-0.15, got {weights['GA']}"

    print("✅ Test 15 passed: Complex case")


if __name__ == "__main__":
    test_1_empty_input()
    test_2_no_filter_no_context()
    test_3_no_filter_with_mold()
    test_4_no_filter_with_poor_ventilation()
    test_5_no_filter_with_gas_stove()
    test_6_no_filter_all_contexts()
    test_7_yes_hepa_only()
    test_8_yes_hepa_carbon()
    test_9_yes_ionizer_no_cert()
    test_10_yes_ionizer_with_cert()
    test_11_yes_diy_filter()
    test_12_yes_poor_maintenance()
    test_13_yes_mold_with_hepa()
    test_14_yes_wildfire_no_hepa()
    test_15_complex_case()

    print("\n" + "="*80)
    print("ALL 15 TESTS PASSED! ✅")
    print("="*80)

