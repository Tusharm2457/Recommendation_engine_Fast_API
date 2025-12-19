"""
Chronic Pain focus area scoring ruleset.
"""

from typing import Dict, Optional, Tuple, List
from .constants import FOCUS_AREAS


class ChronicPainRuleset:
    """Ruleset for chronic pain focus area scoring."""
    
    # Common NSAID medications
    NSAID_KEYWORDS = [
        'ibuprofen', 'advil', 'motrin', 'naproxen', 'aleve', 'diclofenac',
        'voltaren', 'celecoxib', 'celebrex', 'indomethacin', 'indocin',
        'meloxicam', 'mobic', 'aspirin', 'ketorolac', 'toradol'
    ]
    
    # Common opioid medications
    OPIOID_KEYWORDS = [
        'morphine', 'oxycodone', 'oxycontin', 'percocet', 'hydrocodone',
        'vicodin', 'norco', 'codeine', 'tramadol', 'ultram', 'fentanyl',
        'methadone', 'hydromorphone', 'dilaudid', 'oxymorphone', 'opana'
    ]
    
    def get_chronic_pain_weights(
        self,
        has_chronic_pain: bool,
        pain_details: Optional[str] = None,
        digestive_symptoms: Optional[str] = None,
        current_medications: Optional[List[Dict]] = None,
        sleep_hours: Optional[str] = None,
        trouble_staying_asleep: bool = False,
        diagnoses: Optional[str] = None,
        diet_style: Optional[str] = None,
        current_supplements: Optional[str] = None,
        vitamin_d_level: Optional[float] = None,
        exercise_days_per_week: Optional[int] = None
    ) -> Tuple[Dict[str, float], List[str]]:
        """
        Calculate focus area weights based on chronic pain status.
        
        Args:
            has_chronic_pain: Whether patient has chronic pain
            pain_details: Free text description of pain
            digestive_symptoms: Digestive symptoms string (for GI detection)
            current_medications: List of current medications (for NSAID/opioid detection)
            sleep_hours: Sleep hours category (for <6h detection)
            trouble_staying_asleep: Whether patient has trouble staying asleep
            diagnoses: Comma-separated diagnoses string (for RA/celiac/fibromyalgia)
            diet_style: Diet style string (for gluten-free, pescatarian)
            current_supplements: Comma-separated supplements string (for omega-3)
            vitamin_d_level: Vitamin D level in ng/mL
            exercise_days_per_week: Exercise days per week
            
        Returns:
            Tuple of (scores dict, descriptions list)
        """
        scores = {code: 0.0 for code in FOCUS_AREAS}
        descriptions = []
        
        # A) Base rule
        if not has_chronic_pain:
            return (scores, descriptions)
        
        # Base adds for "Yes"
        scores["MITO"] = 0.20
        scores["IMM"] = 0.15
        scores["STR"] = 0.15
        scores["COG"] = 0.05
        descriptions.append("Has chronic pain")
        
        # B) Gut/medication coupling
        # 1) GI symptoms present
        has_gi_symptoms = False
        if digestive_symptoms:
            symptoms_lower = digestive_symptoms.lower()
            gi_keywords = ['heartburn', 'bloating', 'diarrhea', 'constipation', 'nausea', 'reflux']
            has_gi_symptoms = any(keyword in symptoms_lower for keyword in gi_keywords)
        
        if has_gi_symptoms:
            scores["GA"] += 0.10
            descriptions.append("GI symptoms (brain-gut axis)")
        
        # 2) Regular NSAID use
        has_regular_nsaid = False
        if current_medications:
            for med in current_medications:
                med_name = med.get('name', '').lower()
                frequency = med.get('frequency', '').lower()
                if any(nsaid in med_name for nsaid in self.NSAID_KEYWORDS):
                    # Check for regular use (daily or most days)
                    if 'daily' in frequency or 'day' in frequency:
                        has_regular_nsaid = True
                        break
        
        if has_regular_nsaid:
            scores["GA"] += 0.20
            scores["DTX"] += 0.05
            descriptions.append("Regular NSAID use")
        
        # 3) Regular opioid use
        has_regular_opioid = False
        if current_medications:
            for med in current_medications:
                med_name = med.get('name', '').lower()
                frequency = med.get('frequency', '').lower()
                if any(opioid in med_name for opioid in self.OPIOID_KEYWORDS):
                    # Check for regular use
                    if 'daily' in frequency or 'day' in frequency:
                        has_regular_opioid = True
                        break
        
        if has_regular_opioid:
            scores["GA"] += 0.20
            scores["STR"] += 0.05
            descriptions.append("Regular opioid use")
        
        # C) Sleep & pain loop
        has_short_sleep = sleep_hours and sleep_hours.lower() == "less_than_6"
        if has_short_sleep or trouble_staying_asleep:
            scores["STR"] += 0.10
            scores["MITO"] += 0.05
            descriptions.append("less Sleep multiplier")
        
        # D) Immune/autoimmune & inflammatory clues
        has_inflammatory_arthritis = False
        if diagnoses:
            diagnoses_lower = diagnoses.lower()
            arthritis_keywords = [
                'rheumatoid arthritis', 'ra', 'axial spondyloarthritis',
                'ankylosing spondylitis', 'psoriatic arthritis'
            ]
            has_inflammatory_arthritis = any(keyword in diagnoses_lower for keyword in arthritis_keywords)
        
        if has_inflammatory_arthritis:
            scores["IMM"] += 0.15
            scores["CM"] += 0.05
            descriptions.append("Inflammatory arthritis")
        
        # E) Diet & food-immune signals
        # 1) Celiac disease
        has_celiac = False
        if diagnoses:
            diagnoses_lower = diagnoses.lower()
            has_celiac = 'celiac' in diagnoses_lower or 'coeliac' in diagnoses_lower
        
        if has_celiac:
            scores["GA"] += 0.15
            scores["IMM"] += 0.10
            scores["MITO"] += 0.05
            descriptions.append("Celiac disease")
        
        # 2) Non-celiac gluten sensitivity (NCGS)
        elif not has_celiac:  # Only if not celiac
            has_ncgs = False
            all_text = ""
            if pain_details:
                all_text += pain_details.lower() + " "
            if digestive_symptoms:
                all_text += digestive_symptoms.lower() + " "
            
            ncgs_keywords = ['gluten sensitivity', 'ncgs', 'non-celiac gluten', 'gluten intolerance']
            has_ncgs = any(keyword in all_text for keyword in ncgs_keywords)
            
            if has_ncgs:
                scores["GA"] += 0.05
                scores["IMM"] += 0.05
                descriptions.append("Suspected NCGS")
        
        # 3) Omega-3 benefit (fish-rich diet or omega-3 supplements)
        has_omega3_benefit = False
        if diet_style and 'pescatarian' in diet_style.lower():
            has_omega3_benefit = True
        elif current_supplements:
            supplements_lower = current_supplements.lower()
            omega3_keywords = ['omega-3', 'omega 3', 'fish oil', 'epa', 'dha']
            has_omega3_benefit = any(keyword in supplements_lower for keyword in omega3_keywords)
        
        if has_omega3_benefit:
            scores["IMM"] -= 0.05
            scores["MITO"] -= 0.05
            descriptions.append("Omega-3 benefit")
        
        # F) Central sensitisation & fibromyalgia overlay
        has_fibromyalgia = False
        all_text = ""
        if diagnoses:
            all_text += diagnoses.lower() + " "
        if pain_details:
            all_text += pain_details.lower() + " "

        fibro_keywords = ['fibromyalgia', 'widespread pain', 'allodynia']
        has_fibromyalgia = any(keyword in all_text for keyword in fibro_keywords)

        if has_fibromyalgia:
            scores["STR"] += 0.10
            scores["COG"] += 0.05
            scores["IMM"] += 0.05
            descriptions.append("Fibromyalgia pattern")

        # G) Micronutrients & lifestyle
        # 1) Vitamin D deficiency (<20 ng/mL)
        if vitamin_d_level is not None and vitamin_d_level < 20:
            scores["IMM"] += 0.05
            descriptions.append("Vitamin D deficiency")

        # 2) Physical inactivity vs exercise benefit
        if exercise_days_per_week is not None:
            if exercise_days_per_week < 1:
                scores["MITO"] += 0.05
                scores["STR"] += 0.05
                descriptions.append("Physical inactivity")
            elif exercise_days_per_week >= 3:
                # Check for symptom relief in pain_details
                has_exercise_benefit = False
                if pain_details:
                    pain_lower = pain_details.lower()
                    benefit_keywords = [
                        'better with exercise', 'improves with activity', 'exercise helps',
                        'relief with movement', 'better when active'
                    ]
                    has_exercise_benefit = any(keyword in pain_lower for keyword in benefit_keywords)

                if has_exercise_benefit:
                    scores["MITO"] -= 0.05
                    scores["STR"] -= 0.05
                    descriptions.append("Exercise benefit")

        return (scores, descriptions)

