"""
Test script for Focus Areas Generator (Phase 2, Phase 3, and Combined).
"""

import json
import sys
import time
from src.aether_2.tools.focus_areas_generator import EvaluateFocusAreasTool
from src.aether_2.tools.focus_areas_phase3_generator import EvaluateFocusAreasPhase3Tool


def load_test_data():
    """Load and prepare test data from combined_data.json."""
    with open("inputs/combined_data.json", "r") as f:
        data = json.load(f)

    user_full_data = data[0]["user_full_data"]

    patient_and_blood_data = {
        "patient_form": {
            "patient_data": user_full_data["patient_data"]
        },
        "blood_report": user_full_data["latest_biomarker_results"]
    }

    return patient_and_blood_data


def test_phase2_only():
    """Test Phase 2 rulesets only."""
    print("\n" + "="*80)
    print("TESTING PHASE 2 FOCUS AREAS GENERATOR")
    print("="*80)

    patient_and_blood_data = load_test_data()

    tool = EvaluateFocusAreasTool()

    print("\nRunning Phase 2 tool...")
    start_time = time.time()
    result = tool._run(patient_and_blood_data=patient_and_blood_data)
    end_time = time.time()

    elapsed_ms = (end_time - start_time) * 1000

    print("\n" + "="*80)
    print("PHASE 2 MARKDOWN OUTPUT:")
    print("="*80)
    print(result)

    print("\n" + "="*80)
    print(f"⏱️  PHASE 2 EXECUTION TIME: {elapsed_ms:.2f} ms ({elapsed_ms/1000:.3f} seconds)")
    print("="*80)
    print("\n✅ Phase 2 test completed successfully!")


def test_phase3_only():
    """Test Phase 3 rulesets only."""
    print("\n" + "="*80)
    print("TESTING PHASE 3 FOCUS AREAS GENERATOR")
    print("="*80)

    patient_and_blood_data = load_test_data()

    tool = EvaluateFocusAreasPhase3Tool()

    print("\nRunning Phase 3 tool...")
    start_time = time.time()
    result = tool._run(patient_and_blood_data=patient_and_blood_data)
    end_time = time.time()

    elapsed_ms = (end_time - start_time) * 1000

    print("\n" + "="*80)
    print("PHASE 3 MARKDOWN OUTPUT:")
    print("="*80)
    print(result)

    print("\n" + "="*80)
    print(f"⏱️  PHASE 3 EXECUTION TIME: {elapsed_ms:.2f} ms ({elapsed_ms/1000:.3f} seconds)")
    print("="*80)
    print("\n✅ Phase 3 test completed successfully!")


def test_combined():
    """Test combined Phase 2 + Phase 3 scoring."""
    print("\n" + "="*80)
    print("TESTING COMBINED (PHASE 2 + PHASE 3) FOCUS AREAS")
    print("="*80)

    patient_and_blood_data = load_test_data()

    # Start overall timer
    overall_start_time = time.time()

    # Run Phase 2
    print("\n[1/2] Running Phase 2 tool...")
    phase2_start_time = time.time()
    phase2_tool = EvaluateFocusAreasTool()
    phase2_result = phase2_tool._run(patient_and_blood_data=patient_and_blood_data)
    phase2_end_time = time.time()
    phase2_elapsed_ms = (phase2_end_time - phase2_start_time) * 1000

    # Run Phase 3
    print("\n[2/2] Running Phase 3 tool...")
    phase3_start_time = time.time()
    phase3_tool = EvaluateFocusAreasPhase3Tool()
    phase3_result = phase3_tool._run(patient_and_blood_data=patient_and_blood_data)
    phase3_end_time = time.time()
    phase3_elapsed_ms = (phase3_end_time - phase3_start_time) * 1000

    overall_end_time = time.time()
    overall_elapsed_ms = (overall_end_time - overall_start_time) * 1000

    # Load scores from reasons files
    import os
    patient_id = str(patient_and_blood_data["patient_form"]["patient_data"]["phase1_basic_intake"]["demographics"].get("age", "unknown"))

    phase2_reasons_path = f"outputs/{patient_id}/focus_areas_reasons_phase2.json"
    phase3_reasons_path = f"outputs/{patient_id}/focus_areas_reasons_phase3.json"

    # Combine scores by reading log files and extracting final scores
    # For simplicity, we'll parse the markdown output
    phase2_scores = {}
    phase3_scores = {}

    # Parse Phase 2 scores from markdown
    for line in phase2_result.split('\n'):
        if '**' in line and '(' in line and ')' in line and ':' in line:
            try:
                # Format: "- **Focus Area Name (CODE)**: score"
                parts = line.split('**')
                if len(parts) >= 3:
                    name_and_code = parts[1]
                    if '(' in name_and_code and ')' in name_and_code:
                        code = name_and_code.split('(')[1].split(')')[0]
                        score_part = line.split(':')[-1].strip()
                        score = float(score_part)
                        phase2_scores[code] = score
            except:
                pass

    # Parse Phase 3 scores from markdown
    for line in phase3_result.split('\n'):
        if '**' in line and '(' in line and ')' in line and ':' in line:
            try:
                parts = line.split('**')
                if len(parts) >= 3:
                    name_and_code = parts[1]
                    if '(' in name_and_code and ')' in name_and_code:
                        code = name_and_code.split('(')[1].split(')')[0]
                        score_part = line.split(':')[-1].strip()
                        score = float(score_part)
                        phase3_scores[code] = score
            except:
                pass

    # Combine scores
    from src.aether_2.tools.rulesets.constants import FOCUS_AREAS, FOCUS_AREA_NAMES
    combined_scores = {code: 0.0 for code in FOCUS_AREAS}

    for code in FOCUS_AREAS:
        combined_scores[code] = phase2_scores.get(code, 0.0) + phase3_scores.get(code, 0.0)

    # Rank combined scores
    ranked_combined = sorted(
        [(FOCUS_AREA_NAMES[code], code, score) for code, score in combined_scores.items()],
        key=lambda x: x[2],
        reverse=True
    )

    # Combine reasons files
    combined_reasons = {code: [] for code in FOCUS_AREAS}

    if os.path.exists(phase2_reasons_path):
        with open(phase2_reasons_path, 'r') as f:
            phase2_reasons = json.load(f)
            for code in FOCUS_AREAS:
                combined_reasons[code].extend(phase2_reasons.get(code, []))

    if os.path.exists(phase3_reasons_path):
        with open(phase3_reasons_path, 'r') as f:
            phase3_reasons = json.load(f)
            for code in FOCUS_AREAS:
                combined_reasons[code].extend(phase3_reasons.get(code, []))

    # Save combined files
    output_dir = f"outputs/{patient_id}"
    os.makedirs(output_dir, exist_ok=True)

    # Save combined log (just final scores)
    combined_log_path = f"{output_dir}/focus_areas_weight_breakdown_combined.log"
    with open(combined_log_path, 'w') as f:
        from datetime import datetime
        f.write("="*80 + "\n")
        f.write(f"COMBINED FOCUS AREA EVALUATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("="*80 + "\n\n")
        f.write("FINAL COMBINED SCORES (Phase 2 + Phase 3):\n")
        f.write("="*80 + "\n\n")
        for focus_area, code, score in ranked_combined:
            f.write(f"{focus_area} ({code}): {score:.3f}\n")

    # Save combined reasons
    combined_reasons_path = f"{output_dir}/focus_areas_reasons_combined.json"
    with open(combined_reasons_path, 'w') as f:
        json.dump(combined_reasons, f, indent=2)

    print(f"\n✅ Combined log file saved to: {combined_log_path}")
    print(f"✅ Combined reasons file saved to: {combined_reasons_path}")

    # Print combined output
    print("\n" + "="*80)
    print("COMBINED MARKDOWN OUTPUT:")
    print("="*80)
    print("\n# Focus Area Evaluation Results (Combined: Phase 2 + Phase 3)\n")
    print("## Ranked Focus Areas (by weighted score)\n")
    for focus_area, code, score in ranked_combined:
        print(f"- **{focus_area} ({code})**: {score:.2f}")

    # Print timing information
    print("\n" + "="*80)
    print("⏱️  EXECUTION TIME BREAKDOWN:")
    print("="*80)
    print(f"Phase 2 Time:    {phase2_elapsed_ms:>8.2f} ms ({phase2_elapsed_ms/1000:.3f} seconds)")
    print(f"Phase 3 Time:    {phase3_elapsed_ms:>8.2f} ms ({phase3_elapsed_ms/1000:.3f} seconds)")
    print(f"{'─'*80}")
    print(f"Total Time:      {overall_elapsed_ms:>8.2f} ms ({overall_elapsed_ms/1000:.3f} seconds)")
    print("="*80)

    print("\n✅ Combined test completed successfully!")


def print_usage():
    """Print usage instructions."""
    print("\nUsage: python test_focus_areas.py [mode]")
    print("\nModes:")
    print("  phase2    - Test Phase 2 rulesets only")
    print("  phase3    - Test Phase 3 rulesets only")
    print("  combined  - Test combined Phase 2 + Phase 3 scoring (default)")
    print("  all       - Run all three tests sequentially")
    print("\nExamples:")
    print("  python test_focus_areas.py phase2")
    print("  python test_focus_areas.py combined")
    print("  python test_focus_areas.py all")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "combined"

    if mode == "phase2":
        test_phase2_only()
    elif mode == "phase3":
        test_phase3_only()
    elif mode == "combined":
        test_combined()
    elif mode == "all":
        test_phase2_only()
        test_phase3_only()
        test_combined()
    else:
        print(f"\n❌ Unknown mode: {mode}")
        print_usage()
        sys.exit(1)
